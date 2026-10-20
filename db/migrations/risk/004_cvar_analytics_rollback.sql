DROP FUNCTION IF EXISTS portfolio_risk_summary_v2(uuid, double precision);

-- Restore the pre-CVaR close_price return view. This rollback does not touch
-- market data or holdings; all previous risk results are recalculated by SQL.
CREATE OR REPLACE VIEW daily_security_returns AS
WITH prices AS (
    SELECT security_id, trade_date, close_price::double precision AS price,
           LAG(close_price::double precision) OVER (PARTITION BY security_id ORDER BY trade_date) AS previous_price
    FROM daily_market_quote
), returns AS (
    SELECT security_id, trade_date,
           CASE WHEN previous_price > 0 AND price > 0 THEN price / previous_price - 1.0 END AS daily_return
    FROM prices
), rolling AS (
    SELECT security_id, trade_date, daily_return,
           STDDEV_SAMP(daily_return) OVER (PARTITION BY security_id ORDER BY trade_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS sample_volatility,
           COUNT(daily_return) OVER (PARTITION BY security_id ORDER BY trade_date ROWS BETWEEN 29 PRECEDING AND CURRENT ROW) AS return_observations_30d
    FROM returns
)
SELECT security_id, trade_date, daily_return,
       CASE WHEN return_observations_30d = 30 THEN sample_volatility END AS rolling_volatility_30d,
       return_observations_30d
FROM rolling;
