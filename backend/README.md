# IntelliVest Backend Application Gateway

FastAPI service orchestrating the closed-loop advisory and risk ecosystem:

- `/auth`: registration, login, logout, and current-session APIs. Login uses Argon2id password hashes and a 12-hour opaque HTTP-only cookie session. Unsafe requests require the session CSRF token.

- `/users`: Profile management & risk tolerance classification.
- `/cashflow`: Income/expense tracking & investable surplus calculation.
- `/recommendations`: Affordability-constrained stock sizing engine.
- `/portfolios`: Portfolio holdings & PostgreSQL analytics bridge.
- `/rebalance`: SERIALIZABLE rebalance execution & closed-loop feedback engine.
- `/alerts`: Rebalance alerts and risk breach resolution.

## Running Locally
```bash
cp .env.example .env  # set the local PostgreSQL password placeholder
docker compose up -d
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
API Documentation: `http://localhost:8000/docs`

Apply the numbered migrations once to the matching database before starting the
gateway. The Phase 6 additions are `db/migrations/advisory/004_auth_sessions.sql`
and `db/migrations/risk/004_cvar_analytics.sql`; their matching
`*_rollback.sql` files are manual rollback scripts and are not forward migrations.
The existing migration runner replays prior files, so review `db/README.md` before
using it on a populated database.

New registrations create the same UUID in the advisory identity and risk portfolio
records. Existing profiles have a nullable password hash and are not automatically
claimable. Reconcile a legacy account only after verifying ownership out of band,
then set its Argon2id password hash and confirm any associated risk `user_id` records
through an audited administrative procedure. Do not assign old portfolios based on
an email match alone.

The service rejects non-loopback clients even with authentication enabled. Keep it
local-only; do not expose it through a proxy, tunnel, or public interface. Cookie
sessions and ownership checks are MVP protections, not a public deployment review.
PostgreSQL data remains in named Compose volumes; `docker compose down -v` deletes
those volumes and should not be used for routine shutdown.
