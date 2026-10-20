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
uvicorn backend.main:app --reload --port 8000
```
API Documentation: `http://localhost:8000/docs`
