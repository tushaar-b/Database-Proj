# IntelliVest comparative experiment specification

## Question and scope

Evaluate whether linking an affordability limit, portfolio risk limits, and durable risk feedback improves decision consistency against affordability-only, risk-only, and no-feedback baselines. This is an evaluation plan, not evidence that the strategy outperforms another approach.

## Available data and limits

The local risk database currently contains 50 securities and 61,850 daily quotes from 2021-10-19 through 2026-10-19. Returns for the Phase 6 risk metrics use `adjusted_close` where present (the current schema requires it), with current holdings marked at the latest `close_price`. The CVaR and historical VaR window uses the latest 252 complete daily portfolio returns with current market-value weights. Missing security/date observations are not imputed; portfolio observations require aligned returns for all positive holdings.

The current `security_master` is a 50-security snapshot. Historical index membership and delisting coverage are not in the repository, so the present universe cannot support a survivorship-bias-controlled long-horizon comparison. Before a paper result is reported, add point-in-time Nifty 50 membership, delisted securities and source/provenance metadata. Verify quote adjustment methodology and corporate-action history against the upstream source before treating it as audited price history.

Investor cash flows should be synthetic, with a published seed and stated distributions for income, mandatory expenses, discretionary expenses, and reserves. Do not use live investor records as research inputs. Label all generated profiles and resulting measurements as synthetic.

## Shared experimental protocol

- Pin the repository commit, migration versions, Python/Node dependency lockfiles, SQL functions, configuration, data coverage, and the synthetic-profile seed.
- Use the same point-in-time universe, quote cut-off, sector mapping, recommendation ordering, cash endowment, rebalance dates, and transaction assumptions for every method.
- Keep the production MVP’s deterministic sector/ticker ordering fixed for the first comparison. Record it as the ranking method; do not substitute realized returns as a ranking feature.
- Use an expanding historical warm-up of at least 252 aligned daily returns. Evaluate decisions only after each decision timestamp; use no future quote or constituent membership.
- Define execution at the next available close after a recommendation, with a preregistered symmetric transaction cost (default experiment value: 10 basis points) and sensitivity runs at 0 and 25 basis points. Prices are a simulation convention, not actual brokerage fills.
- Use monthly decision dates for comparisons and the same one-day 95% VaR/CVaR horizon. Calculate allocation drift, turnover, and return/drawdown from the same portfolio marks and cash-flow convention.
- Run a separate out-of-sample period after the warm-up; do not select thresholds on those results. Publish all per-period observations, missing-data exclusions, and uncertainty intervals.

## Baseline definitions

| Configuration | Affordability | Risk | Feedback |
| --- | --- | --- | --- |
| A — Affordability only | Cap each allocation and cumulative recommendations to the synthetic investable buffer; enforce whole shares. | Disabled for recommendation eligibility. | Disabled. |
| B — Risk only | Use a fixed, preregistered experiment capital endowment independent of profile surplus; preserve the common execution and share-sizing convention. | Apply the same VaR, volatility, and HHI limits as IntelliVest. | Disabled. |
| C — No feedback | Enforce the current cash-flow buffer and whole-share affordability. | Evaluate risk for initial eligibility using the same limits. | Freeze the advisory policy at its initial state after a breach; do not apply subsequent outbox events to later recommendation batches. |
| IntelliVest | Apply the current cash-flow buffer and whole-share affordability. | Use PostgreSQL portfolio risk outputs. | Apply each durable, duplicate-safe risk event to the next recommendation batch. |

Baseline B intentionally isolates risk from personal affordability; report its budget/constraint violation rate against the synthetic profile separately rather than describing those violations as affordable investments. Keep the universe, recommendation candidate order, quote cut-off, and transaction cost common.

## Measurements

- Unaffordable recommendation rate and total budget violations.
- Risk-limit violations and portfolio VaR/CVaR at 95%, one trading day.
- Sector HHI and allocation drift from target.
- Breach-to-policy-update latency, in seconds and recommendation cycles.
- Portfolio turnover and transaction-cost sensitivity.
- Return, maximum drawdown, and exposure to cash, only after point-in-time prices and execution assumptions are validated.
- Recommendation stability: ticker/weight changes between consecutive batches, including changes attributable to feedback.

Report denominators, dates, missing-data exclusions, and per-profile results. Use paired comparisons over identical profile/date paths and bootstrap confidence intervals by profile path; do not treat repeated dates from one profile as independent investors.

## Implementation readiness

The production APIs can generate real-quote recommendations, SQL risk metrics, alerts, and updated policies. They do not provide a historical backtest runner or switches for the four configurations. No comparative experiment was run in Phase 6. Remaining research work is to add point-in-time constituents, quote-quality checks, a deterministic historical replay runner with the four explicit modes, transaction/cash-flow accounting, and a report exporter that records provenance and exclusions.
