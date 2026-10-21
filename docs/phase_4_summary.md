# Phase 4: FastAPI Gateway and Closed Feedback Loop

## API surface

- `GET /health`: real advisory and risk database connection checks; API docs at `/docs` and `/openapi.json`.
- `/users`: retrieve, update profile, update risk tolerance. Profiles use the authenticated account UUID; PAN data is not collected or returned.
- PAN hash removal preserves existing profile UUIDs and related records. Historical backups or replicas created before migration `005_remove_pan_hash.sql` may retain the old hash until they expire under the existing backup-retention policy.
- `/cashflow`: create/update/delete income and expenses, monthly summary, and persisted surplus evaluation.
- `/recommendations`: generate, list, accept, or reject a batch. Accepting records intent only and does not trade.
- `/portfolios`: create/list, retrieve valuation/cash, list holdings, and evaluate risk through PostgreSQL `portfolio_risk_summary()`.
- `/alerts`: list/filter, evaluate, list by portfolio, and resolve alerts.
- `/rebalance`: propose and execute approved simulated operations.

## Configuration and data rules

- `ADVISORY_DB_URL` defaults to `localhost:5434/advisory_db`; `RISK_DB_URL` defaults to `localhost:5433/risk_db`. Environment variables and `.env` override defaults. The gateway uses bounded thread-safe psycopg2 pools.
- Income is evaluated monthly (`YEARLY / 12`); expenses support `MONTHLY` and `YEARLY`. Other recurrence values are rejected. Surplus is monthly income less mandatory expense; investable buffer is `max(0, surplus - reserve)`.
- Recommendations use latest real quote prices, whole shares, up to three distinct sectors, and equal per-sector budgets. Base capacity is 25%/50%/75% of buffer for conservative/moderate/aggressive users. Only one pending batch per user is permitted. Existing holdings and feedback-blocked sectors are excluded.
- Configured risk thresholds: VaR exceeds 10% of portfolio valuation; daily 30-observation volatility exceeds 3%; HHI exceeds the portfolio's own `target_hhi_limit`. Values can be changed with `RISK_VAR_LIMIT_PERCENT` and `RISK_DAILY_VOLATILITY_LIMIT`.

## Feedback and simulated execution

- Risk evaluation writes duplicate-safe alerts and a risk-database outbox snapshot in one transaction. Advisory delivery records each event ID once and applies policy updates in sequence order. Failed deliveries stay pending with attempt/error details and retry on the next recommendation request or risk evaluation. Recommendations fail closed while undelivered events remain.
- A single VaR or volatility breach halves capacity; both reduce it to 25% of the user's base capacity. HHI breach blocks new recommendations in the most concentrated sector. Recommendation text contains the active reason.
- Rebalance proposals sell at most one share of the largest holding (preferably in the concentrated sector). Execution requires explicit approval and an idempotency UUID; all quote, cash, holding, and ledger writes run in a Risk DB `SERIALIZABLE` transaction with bounded retry. No brokerage is contacted. The advisory and risk databases do not share atomic transactions; feedback uses the outbox.

## Verification

- Additive migrations `advisory/002_phase4_gateway.sql` and `risk/003_phase4_gateway.sql` were applied to the existing databases.
- Full `.venv/bin/python -m pytest -q`: **26 passed**, including live end-to-end tests against both PostgreSQL databases and concurrent rebalance requests. Test users, portfolios, alerts, and feedback rows are removed after the tests; historical market quotes are untouched.
- Uvicorn started locally; `/health` returned 200 with both databases connected, `/docs` returned 200, and `/openapi.json` returned 200.

## Known MVP limits

- User authentication and authorization are not implemented; endpoints accept UUIDs directly.
- Stock selection is deterministic diversification by sector/ticker, not an investment prediction. Tax, fees, market impact, and NSE lot sizes above one share are not modeled.
- Feedback delivery retries when gateway work next processes the outbox; no separate worker is deployed. If Advisory DB is unavailable, risk events remain durable and recommendations fail closed.
- Risk thresholds are simple configurable MVP defaults. Rebalance proposals are single-share risk-reduction suggestions and require user approval; execution is a simulated ledger operation only.
