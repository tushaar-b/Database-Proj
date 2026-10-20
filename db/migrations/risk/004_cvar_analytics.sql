-- Historical returns use adjusted_close so splits/dividends are reflected where
-- the quote provider supplies adjustments. Weights remain the current holdings
-- marked at the latest close, exactly as in the existing portfolio convention.
CREATE OR REPLACE VIEW daily_security_returns AS
WITH prices AS (
    SELECT security_id, trade_date,
           COALESCE(adjusted_close, close_price)::double precision AS price,
           LAG(COALESCE(adjusted_close, close_price)::double precision) OVER (
               PARTITION BY security_id ORDER BY trade_date
           ) AS previous_price
    FROM daily_market_quote
), returns AS (
    SELECT security_id, trade_date,
           CASE WHEN previous_price > 0 AND price > 0 THEN price / previous_price - 1.0 END AS daily_return
    FROM prices
), rolling AS (
    SELECT security_id, trade_date, daily_return,
           STDDEV_SAMP(daily_return) OVER (
               PARTITION BY security_id ORDER BY trade_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
           ) AS sample_volatility,
           COUNT(daily_return) OVER (
               PARTITION BY security_id ORDER BY trade_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
           ) AS return_observations_30d
    FROM returns
)
SELECT security_id, trade_date, daily_return,
       CASE WHEN return_observations_30d = 30 THEN sample_volatility END AS rolling_volatility_30d,
       return_observations_30d
FROM rolling;

CREATE OR REPLACE FUNCTION portfolio_risk_summary_v2(
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
    calculation_status text,
    cvar_95 numeric,
    cvar_confidence_level double precision,
    cvar_horizon_trading_days integer,
    cvar_return_basis text,
    cvar_observations integer,
    cvar_window integer,
    cvar_data_timestamp date,
    cvar_status text
) LANGUAGE sql STABLE AS $$
WITH base AS (
    SELECT * FROM portfolio_risk_summary(p_portfolio_id, p_annual_risk_free_rate)
), history AS (
    SELECT r.trade_date, -r.portfolio_return * b.portfolio_valuation AS loss
    FROM daily_portfolio_returns r CROSS JOIN base b
    WHERE r.portfolio_id=p_portfolio_id AND r.portfolio_return IS NOT NULL
    ORDER BY r.trade_date DESC LIMIT 252
), threshold AS (
    SELECT COUNT(*)::integer AS n,
           PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY loss) AS loss_threshold,
           MAX(trade_date) AS latest_date
    FROM history
), tail AS (
    SELECT AVG(h.loss) AS mean_tail_loss
    FROM history h CROSS JOIN threshold t
    WHERE h.loss >= t.loss_threshold
)
SELECT b.portfolio_id,b.portfolio_valuation,b.volatility_30d,b.parametric_var_95,
       b.historical_var_95,b.sharpe_ratio,b.sector_hhi,b.target_hhi_limit,
       b.calculation_date,b.historical_observations,b.calculation_status,
       CASE WHEN t.n=252 THEN GREATEST(COALESCE(b.historical_var_95,0),COALESCE(tail.mean_tail_loss,0)) END,
       0.95::double precision,
       1,
       'current_market_value_weights_adjusted_close_daily_returns'::text,
       t.n,252,t.latest_date,
       CASE WHEN t.n<252 THEN 'insufficient_history_252_required'
            ELSE 'ok_inclusive_ties_at_linear_95th_percentile' END
FROM base b CROSS JOIN threshold t CROSS JOIN tail;
$$;
