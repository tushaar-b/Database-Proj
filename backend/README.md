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
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
API Documentation: `http://localhost:8000/docs`

The MVP has no authentication yet. The API binds to loopback and rejects requests
from non-loopback clients. Do not expose it through a proxy, tunnel, or public
interface. Authentication and per-user authorization are required before any
shared or deployed use. PostgreSQL data remains in the named Compose volumes;
`docker compose down -v` deletes that data and should not be used for routine
shutdown.
