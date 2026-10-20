# IntelliVest ETL Pipeline & Market Data Ingestion

This module manages market data ingestion and synchronization for the Portfolio Risk Database (`risk_db`).

---

## 🚀 Features

1. **Nifty 50 Constituent Master (`etl.constituents`)**:
   - Master definition of all 50 constituent stocks with NSE tickers, Yahoo Finance identifiers (`.NS`), standard company names, sector taxonomies, and initial beta metrics.
2. **Historical OHLCV Ingestion (`etl.pipeline`)**:
   - Ingests 5 years of daily OHLCV pricing data via `yfinance`.
   - Cleans price anomalies, formats trade dates, and generates unique quote identifiers.
   - Robust offline Geometric Brownian Motion fallback if network is constrained or external APIs throttle.
3. **Idempotent High-Throughput Batch Upserts (`etl.db`)**:
   - Batch inserts for `SECURITY_MASTER` and `DAILY_MARKET_QUOTE` using PostgreSQL `ON CONFLICT` clauses (`ON CONFLICT (security_id, trade_date)` and `ON CONFLICT (ticker_symbol)`).
   - Compatible with PostgreSQL and SQLite.
4. **Incremental Daily Refresh Job (`etl.run_daily_refresh`)**:
   - Fetches the latest quotes for all active constituents.
   - Triggers automated refresh of `mv_daily_sector_concentration` materialized view.
5. **Temporal Performance Benchmark (`etl.benchmark`)**:
   - Benchmarks 30-day quote retrieval queries against the `idx_quote_temporal` index, validating the `< 10ms` latency requirement.

---

## 🛠 Usage & CLI Commands

### 1. Run Full 5-Year Historical Ingestion
```bash
# Ingest real 5-year Yahoo Finance history for all Nifty 50 stocks into risk_db.
# Set RISK_DB_URL from the local .env before running; no embedded database
# password fallback or synthetic market fallback is used by default.
set -a; source .env; set +a
python -m etl.pipeline

# Synthetic fallback is available only when explicitly requested.
python -m etl.pipeline --allow-synthetic-fallback
```

### 2. Run Daily Incremental Refresh
```bash
# Pull last 5 days of quotes and refresh materialized views
python -m etl.run_daily_refresh --days 5

# Refresh specific symbols only
python -m etl.run_daily_refresh --symbols RELIANCE TCS INFY --days 3
```

### 3. Run Query Performance Benchmark
```bash
python -m pytest tests/etl/test_temporal_query_perf.py -v
```
