-- Phase 3: PostgreSQL-native portfolio risk analytics.
-- Returns use close_price and current holdings/market-value weights.

CREATE OR REPLACE VIEW daily_security_returns AS
WITH prices AS (
    SELECT security_id, trade_date, close_price::double precision AS price,
           LAG(close_price::double precision) OVER (
               PARTITION BY security_id ORDER BY trade_date
           ) AS previous_price
    FROM daily_market_quote
), returns AS (
    SELECT security_id, trade_date,
           CASE WHEN previous_price > 0 AND price > 0
                THEN price / previous_price - 1.0 END AS daily_return
    FROM prices
), rolling AS (
    SELECT security_id, trade_date, daily_return,
           STDDEV_SAMP(daily_return) OVER (
               PARTITION BY security_id ORDER BY trade_date
               ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
           ) AS sample_volatility,
           COUNT(daily_return) OVER (
               PARTITION BY security_id ORDER BY trade_date
               ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
           ) AS return_observations_30d
    FROM returns
)
SELECT security_id, trade_date, daily_return,
       CASE WHEN return_observations_30d = 30 THEN sample_volatility END AS rolling_volatility_30d,
       return_observations_30d
FROM rolling;

-- Portfolio history uses current share quantities and latest market-value weights.
-- A date is included only when every positive holding has a return for that date;
-- weighted aggregation therefore retains covariance effects between holdings.
CREATE OR REPLACE VIEW daily_portfolio_returns AS
WITH latest_prices AS (
    SELECT DISTINCT ON (security_id) security_id, close_price::double precision AS price
    FROM daily_market_quote
    ORDER BY security_id, trade_date DESC
), holding_values AS (
    SELECT h.portfolio_id, h.security_id,
           h.quantity::double precision * lp.price AS market_value,
           p.cash_balance::double precision AS cash_balance
    FROM holding h
    JOIN portfolio p ON p.portfolio_id = h.portfolio_id
    JOIN latest_prices lp USING (security_id)
    WHERE h.quantity > 0
), weights AS (
    SELECT portfolio_id, security_id,
           market_value / NULLIF(SUM(market_value) OVER (PARTITION BY portfolio_id)
                                 + MAX(cash_balance) OVER (PARTITION BY portfolio_id), 0) AS weight,
           COUNT(*) OVER (PARTITION BY portfolio_id) AS holding_count
    FROM holding_values
), combined AS (
    SELECT w.portfolio_id, r.trade_date,
           SUM(w.weight * r.daily_return) AS portfolio_return,
           COUNT(*) AS observed_holdings,
           MAX(w.holding_count) AS holding_count
    FROM weights w
    JOIN daily_security_returns r USING (security_id)
    WHERE r.daily_return IS NOT NULL
    GROUP BY w.portfolio_id, r.trade_date
)
SELECT portfolio_id, trade_date,
       CASE WHEN observed_holdings = holding_count THEN portfolio_return END AS portfolio_return
FROM combined;

-- Latest quote value for securities plus cash balance; market value excludes stale
-- PORTFOLIO.total_valuation so an unrefreshed cache cannot misstate risk.
DROP MATERIALIZED VIEW IF EXISTS mv_daily_sector_concentration;
CREATE MATERIALIZED VIEW mv_daily_sector_concentration AS
WITH latest_prices AS (
    SELECT DISTINCT ON (security_id) security_id, close_price::numeric AS price
    FROM daily_market_quote
    ORDER BY security_id, trade_date DESC
), sector_values AS (
    SELECT p.portfolio_id, sm.sector_name,
           SUM(h.quantity::numeric * lp.price)::numeric(14,2) AS sector_valuation,
           COUNT(h.holding_id)::bigint AS asset_count
    FROM portfolio p
    JOIN holding h ON h.portfolio_id = p.portfolio_id
    JOIN security_master sm ON sm.security_id = h.security_id
    JOIN latest_prices lp ON lp.security_id = h.security_id
    WHERE h.quantity > 0
    GROUP BY p.portfolio_id, sm.sector_name
), weighted AS (
    SELECT portfolio_id, sector_name, sector_valuation, asset_count,
           sector_valuation / NULLIF(SUM(sector_valuation) OVER (PARTITION BY portfolio_id), 0) AS sector_weight
    FROM sector_values
)
SELECT portfolio_id, sector_name, sector_valuation, asset_count,
       sector_weight,
       SUM(sector_weight * sector_weight) OVER (PARTITION BY portfolio_id) AS sector_hhi,
       CURRENT_TIMESTAMP AS last_refreshed_at
FROM weighted;

CREATE UNIQUE INDEX idx_mv_sector_conc_pk
    ON mv_daily_sector_concentration (portfolio_id, sector_name);

CREATE OR REPLACE FUNCTION refresh_daily_sector_concentration()
RETURNS void LANGUAGE plpgsql AS $$
BEGIN
    REFRESH MATERIALIZED VIEW mv_daily_sector_concentration;
END;
$$;

-- One row for a known portfolio. Risk-free rate is annualized (default 4%) and
-- converted to a daily rate using 252 trading days. Sharpe and historical VaR
-- require a complete 252-return window; 30-day volatility requires 30 returns.
CREATE OR REPLACE FUNCTION portfolio_risk_summary(
    p_portfolio_id uuid,
    p_annual_risk_free_rate double precision DEFAULT 0.04
)
RETURNS TABLE (
    portfolio_id uuid,
    portfolio_valuation numeric,
    volatility_30d double precision,
    parametric_var_95 numeric,
    historical_var_95 numeric,
    sharpe_ratio double precision,
    sector_hhi double precision,
    target_hhi_limit numeric,
    calculation_date date,
    historical_observations integer,
    calculation_status text
) LANGUAGE sql STABLE AS $$
WITH portfolio AS (
    SELECT p.portfolio_id, p.cash_balance, p.target_hhi_limit
    FROM portfolio p WHERE p.portfolio_id = p_portfolio_id
), latest_prices AS (
    SELECT DISTINCT ON (security_id) security_id, trade_date, close_price::numeric AS price
    FROM daily_market_quote ORDER BY security_id, trade_date DESC
), valuation AS (
    SELECT p.portfolio_id, p.cash_balance + COALESCE(SUM(h.quantity::numeric * lp.price), 0) AS value,
           MAX(lp.trade_date) AS as_of_date
    FROM portfolio p
    LEFT JOIN holding h ON h.portfolio_id = p.portfolio_id AND h.quantity > 0
    LEFT JOIN latest_prices lp ON lp.security_id = h.security_id
    GROUP BY p.portfolio_id, p.cash_balance
), history AS (
    SELECT r.trade_date, r.portfolio_return
    FROM daily_portfolio_returns r
    WHERE r.portfolio_id = p_portfolio_id AND r.portfolio_return IS NOT NULL
    ORDER BY r.trade_date DESC LIMIT 252
), stats AS (
    SELECT COUNT(*)::integer AS n,
           STDDEV_SAMP(portfolio_return) AS sigma,
           AVG(portfolio_return) AS mean_return,
           PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY portfolio_return) AS p05,
           MAX(trade_date) AS latest_date
    FROM history
), latest_vol AS (
    SELECT STDDEV_SAMP(portfolio_return) AS sigma
    FROM (SELECT portfolio_return FROM daily_portfolio_returns
          WHERE portfolio_id = p_portfolio_id AND portfolio_return IS NOT NULL
          ORDER BY trade_date DESC LIMIT 30) last_30
    HAVING COUNT(*) = 30
), concentration AS (
    SELECT MAX(sector_hhi) AS hhi
    FROM mv_daily_sector_concentration WHERE mv_daily_sector_concentration.portfolio_id = p_portfolio_id
)
SELECT p.portfolio_id,
       v.value,
       lv.sigma,
       CASE WHEN lv.sigma IS NOT NULL THEN 1.645 * lv.sigma * v.value END,
       CASE WHEN s.n = 252 THEN GREATEST(0, -s.p05 * v.value) END,
       CASE WHEN s.n = 252 AND s.sigma > 0
            THEN ((s.mean_return - p_annual_risk_free_rate / 252.0) / s.sigma) * SQRT(252.0) END,
       c.hhi,
       p.target_hhi_limit,
       COALESCE(s.latest_date, v.as_of_date, CURRENT_DATE),
       s.n,
       CASE WHEN s.n < 252 THEN 'insufficient_history_252_required'
            WHEN lv.sigma IS NULL THEN 'insufficient_history_30_required'
            WHEN s.sigma = 0 THEN 'zero_return_volatility'
            ELSE 'ok' END
FROM portfolio p
JOIN valuation v USING (portfolio_id)
CROSS JOIN stats s
LEFT JOIN latest_vol lv ON TRUE
LEFT JOIN concentration c ON TRUE;
$$;
