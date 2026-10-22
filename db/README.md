# IntelliVest Database Management

This directory contains SQL migrations, database initialization scripts, and schema definitions for the two PostgreSQL databases:

1. **Advisory Database (`advisory_db`)**:
   - `USER_PROFILE`
   - `INCOME_STREAM`
   - `EXPENSE_ITEM`
   - `SURPLUS_SNAPSHOT`
   - `RECOMMENDATION_LOG`

2. **Portfolio Risk Database (`risk_db`)**:
   - `PORTFOLIO`
   - `SECURITY_MASTER`
   - `HOLDING`
   - `TRANSACTION_LEDGER`
   - `DAILY_MARKET_QUOTE`
   - `REBALANCE_ALERT`
   - `mv_daily_sector_concentration` (Materialized View)

## Directory Structure
- `init-scripts/`: Bootstrap scripts for containerized PostgreSQL environments.
- `migrations/advisory/`: Versioned migration scripts for the Advisory DB.
- `migrations/risk/`: Versioned migration scripts for the Portfolio Risk DB.
