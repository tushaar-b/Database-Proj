# IntelliVest Backend Application Gateway

FastAPI service orchestrating the closed-loop advisory and risk ecosystem:

- `/users`: Profile management & risk tolerance classification.
- `/cashflow`: Income/expense tracking & investable surplus calculation.
- `/recommendations`: Affordability-constrained stock sizing engine.
- `/portfolios`: Portfolio holdings & PostgreSQL analytics bridge.
- `/rebalance`: SERIALIZABLE rebalance execution & closed-loop feedback engine.
- `/alerts`: Rebalance alerts and risk breach resolution.

## Running Locally
```bash
cp .env.example .env  # replace the local PostgreSQL password placeholder
docker compose up -d
.venv/bin/python -m backend
```
API Documentation: `http://127.0.0.1:8000/docs`

The API uses database-backed opaque sessions, Argon2id passwords, CSRF validation,
and per-user ownership checks. It still binds to loopback and rejects non-local
clients. Do not expose it through a public proxy or tunnel. The local Vite `/api`
proxy forwards to `APP_HOST:APP_PORT` from the root `.env`; `.venv/bin/python -m backend` uses those same settings (defaults `127.0.0.1:8000`). Open the frontend
at `http://127.0.0.1:5173` and allow that origin in `ALLOWED_ORIGINS`.

`/auth/me` returns a stable per-session CSRF proof with `Cache-Control: no-store`.
It lazily upgrades existing random-proof sessions without changing their expiry,
identity, or database schema. All state-changing authenticated endpoints retain
CSRF and origin checks; cookie HttpOnly, SameSite and production Secure behavior
are unchanged. Reload browser tabs running an older frontend bundle after updating.

PostgreSQL data remains in the named Compose volumes;
`docker compose down -v` deletes that data and should not be used for routine
shutdown.
