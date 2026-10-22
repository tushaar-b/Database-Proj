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

## Recommendation freshness (migration 007)

`migrations/advisory/007_recommendation_freshness.sql` restores the previously missing migration file. It adds the batch metadata, `SUPERSEDED` enum label, batch indexes, and composite batch/user foreign key needed by the current recommendation router. It does not delete, backfill, supersede, or change existing recommendation records. Legacy batch references and NULL fingerprints are preserved. A newly added foreign key is `NOT VALID`, enforcing new references while leaving legacy validation for a separately approved audit. Existing validated constraints are left unchanged. No uniqueness restriction is placed on fingerprints because the reconsideration interval permits later batches for unchanged inputs.

Read-only inspection of the local databases on 2026-10-22 found all these required structures already present, including the validated composite ownership foreign key and both indexes. `rebalance_alert` exists only in Risk DB. There is no migration ledger, so the provenance of the existing structures cannot establish that a particular 007 script was applied. **No schema or data changes were made during this repair; no local migration is currently required.**

For another installation missing these structures, review its schema and any legacy batch references before applying **only** the prepared file after approval:

```sh
docker compose exec -T advisory_db psql -U postgres -d advisory_db -v ON_ERROR_STOP=1 < db/migrations/advisory/007_recommendation_freshness.sql
```

Do not run the complete migration history to fix this issue. The prepared migration has transaction and lock timeouts; unexpected schema incompatibilities abort rather than replacing tables or repairing records automatically. Older batch tables missing identity/timestamp columns or having incompatible column types require a separate reviewed migration. Do not validate a new foreign key or repair legacy references without first reviewing the affected records.
