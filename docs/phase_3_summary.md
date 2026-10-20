# Phase 3: PostgreSQL Financial Risk Analytics

## Implemented

- `daily_security_returns` calculates close-to-close returns with `LAG()` and 30-observation sample volatility with `STDDEV_SAMP()`.
- `daily_portfolio_returns` aggregates contemporaneous security returns using current market-value weights, preserving cross-security covariance. Cash is included in the portfolio denominator with a zero-return assumption.
- `portfolio_risk_summary(portfolio_id, annual_risk_free_rate)` returns current quote-based holdings value plus cash, 30-observation volatility, 95% parametric VaR, 252-observation historical VaR, annualized Sharpe, sector HHI, target limit, date, observation count, and a status.
- `mv_daily_sector_concentration` uses current quote values and exposes sector weights and HHI. Refresh with `SELECT refresh_daily_sector_concentration();`.
- `tests/db/test_risk_analytics_postgres.py` provides a deterministic PostgreSQL calculation check and empty-portfolio check.

## Verification

- Risk migrations 001 and 002 applied successfully to the local PostgreSQL 16 risk container.
- Transaction-scoped SQL smoke test used 253 alternating prices (100/110), asserted 30-observation sample volatility (~0.097086), parametric VaR (~159.707 on a 1,000 portfolio), historical VaR (~90.909), Sharpe (~0.72808), HHI (1.0), and NULL risk metrics for an empty portfolio. Test rows were rolled back.
- `.venv/bin/python -m pytest -q`: 25 passed. The deterministic PostgreSQL test ran against `risk_db` after the Docker containers became available.
- The advisory schema has five base tables, four foreign keys, and ten indexes. The risk schema has six base tables, six foreign keys, three unique constraints, and sixteen indexes. The analytics materialized view exists.
- `DAILY_MARKET_QUOTE` currently contains zero rows. Another service occupies host port 5432, so the Compose advisory database was started on alternate host port 5434 for migration and schema checks. The default advisory URL still expects port 5432; configure it to port 5434 in this environment before running the app migration runner.

## Assumptions and limits

- Returns use `close_price`; prices and current holding quantities are used to value positions. `PORTFOLIO.total_valuation` is treated as a cache and not as the risk valuation source.
- Portfolio return weights use latest holding market values over holdings plus cash; cash has zero return. Historical portfolio returns use today's holdings and weights, so this is a current-portfolio backtest, not a reconstructed historical holdings series.
- Parametric VaR uses 1.645 times 30-trading-observation sample volatility. Historical VaR and Sharpe require a complete 252 portfolio-return observations; 30-day volatility requires 30. Insufficient metrics remain NULL. Sharpe defaults to an annual 4% risk-free rate (252 trading days) and accepts an override.
- HHI covers invested sectors and excludes cash. Empty portfolios have no sector rows and therefore a NULL HHI.
- The real market-data ingestion path was not run. No synthetic prices were inserted. Both schemas were verified, but usable historical quote coverage remains a blocker until real market data is ingested.
- Phase 6 performance targets and optimization remain deferred.
