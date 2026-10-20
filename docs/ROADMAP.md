# IntelliVest Roadmap & Milestone Plan

| Phase | Title | Focus Area | Status |
|---|---|---|---|
| **Phase 0** | Project Setup | Repo scaffolding, dual PostgreSQL Docker setup, dependencies, base test runner | Completed |
| **Phase 1** | PostgreSQL Schemas & Migrations | Stand up Advisory DB & Risk DB schemas, constraints, indexes, materialized view stub | Completed |
| **Phase 2** | Market Data Ingestion Pipeline | Python ETL for Nifty 50 5-year OHLCV quotes via yfinance, idempotency, daily refresh job | Completed |
| **Phase 3** | In-Engine SQL Financial Analytics | Window functions for volatility, VaR 95%, Historical VaR, Sharpe, HHI; NumPy verification suite | Pending |
| **Phase 4** | Application Gateway & Feedback Loop | FastAPI routers, Sizing Engine, SERIALIZABLE rebalancing transaction flow, drift feedback triggers | Pending |
| **Phase 5** | Dashboard UI & Final Integration | React dashboard (Onboarding, Cash Flow, Recommendations, Risk Meters, Alerts, Ledger) | Pending |
| **Phase 6** | Hardening & Polish | Security audit, structured logging, latency benchmark re-verification (≤10ms / ≤25ms) | Pending |
