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

## Phase 6 migrations

- Advisory `004_auth_sessions.sql` adds a nullable Argon2id password hash column,
  opaque login sessions, and hashed rate-limit counters. It does not reassign or
  delete any existing profile or financial record.
- Risk `004_cvar_analytics.sql` switches portfolio daily returns to adjusted close
  where available and adds `portfolio_risk_summary_v2`, which extends the existing
  risk row with historical CVaR metadata. It does not rewrite quotes, holdings, or
  ledgers. Historical VaR and volatility are recalculated against adjusted returns.
- The `*_rollback.sql` files are rollback scripts, not forward migrations. Apply a
  rollback together with the matching application version; the risk rollback
  restores the former close-price return basis and removes the v2 function.

Before applying migrations to a populated database, take a normal PostgreSQL
backup and verify it can be restored. The Phase 6 live migrations were additive and
were tested inside rollback transactions before application. No historical quote
or financial record was overwritten. Migration SQL can be applied individually
using the corresponding database URL, for example:

```bash
psql "$ADVISORY_DB_URL" -v ON_ERROR_STOP=1 -f db/migrations/advisory/004_auth_sessions.sql
psql "$RISK_DB_URL" -v ON_ERROR_STOP=1 -f db/migrations/risk/004_cvar_analytics.sql
```

The legacy `db/migrate.py` runner replays the numbered forward files; the risk
analytics migration rebuilds its materialized view as part of that replay. Do not
run it casually against a busy populated system. Rollback files are excluded from
the runner. A migration-history table is still a follow-up improvement before a
production deployment.
