# IntelliVest Phase 9 final research report

**Classification: 2 — exploratory benchmark research.** All findings are exploratory comparisons of nine synthetic profiles sharing historical market paths. Previously inspected observations, overlapping windows, surviving-security selection and current sector labels prevent independent-validation or population-level claims.

## What was executed

36 exact original V1 replays, followed by 108 V1/V3/V4 frozen-policy reproductions; 495 stock strategy/account/window simulations; 54 executable ETF simulations; 72 selected-profile sensitivity simulations; 432 common-state comparisons across six methods (2,592 allocations); and 450 controlled runtime calls. Validation adds deterministic and future-price-perturbation replays. Counts describe computations, not independent investors. Existing application/data/evidence hashes remain unchanged.

## Main evidence

| policy | regime | authorized_budget_utilization | annualized_return | annualized_volatility | cvar95 | maximum_drawdown | mean_hhi | mean_cash_allocation | median_defined_sharpe |
|---|---|---|---|---|---|---|---|---|---|
| V1 | M | 14.523 | 2.635 | 2.107 | 0.310 | 2.882 | 0.348 | 85.621 | -1.934 |
| GREEDY_M | M | 94.255 | 5.749 | 5.126 | 0.723 | 9.963 | 0.252 | 62.439 | 0.341 |
| V3 | M | 95.134 | 8.614 | 6.302 | 0.899 | 10.106 | 0.106 | 60.492 | 0.729 |
| MILP_M | M | 92.013 | 5.389 | 4.877 | 0.682 | 9.589 | 0.257 | 63.629 | 0.349 |
| EQUAL_M | M | 95.684 | 7.030 | 5.284 | 0.763 | 9.029 | 0.132 | 61.431 | 0.502 |
| SIP_M | M | 94.074 | 9.404 | 7.852 | 1.142 | 12.592 | 0.163 | 60.274 | 0.671 |
| ETF_M | M | 97.085 | 4.792 | 4.496 | 0.620 | 7.195 | unavailable | 61.503 | 0.246 |
| GREEDY_C | C | 99.683 | 6.094 | 5.295 | 0.746 | 10.554 | 0.257 | 60.907 | 0.339 |
| V4 | C | 99.958 | 9.031 | 6.492 | 0.927 | 10.483 | 0.106 | 59.136 | 0.761 |
| MILP_C | C | 99.802 | 5.981 | 5.277 | 0.741 | 10.633 | 0.256 | 60.557 | 0.363 |
| EQUAL_C | C | 99.974 | 7.256 | 5.416 | 0.780 | 9.246 | 0.133 | 60.117 | 0.629 |
| SIP_C | C | 99.882 | 9.756 | 8.165 | 1.191 | 12.973 | 0.159 | 58.618 | 0.679 |
| ETF_C | C | 99.930 | 4.876 | 4.573 | 0.631 | 7.328 | unavailable | 60.851 | 0.261 |
| NEUTRAL_M | M | 94.760 | 9.029 | 7.058 | 1.012 | 12.050 | 0.105 | 60.328 | 0.681 |
| NEUTRAL_C | C | 99.938 | 9.417 | 7.307 | 1.048 | 12.365 | 0.104 | 58.714 | 0.719 |


All rate columns are percent, with HHI and Sharpe unitless. NIFTY TRI is unavailable; ETF is the executable NIFTYBEES proxy. Daily CVaR and drawdown quantify the additional downside that accompanies returns. The observed original-baseline utilization gain survives comparison, but it is not unique to the proposed constructor: equal-weight monthly utilization is 95.68% versus V3 95.13%, and all C strategies approach full approved utilization.

At identical V3 states, score-greedy attains 99.39% of the integer reference's utility versus V3/V4 62.39%. V3/V4 are sector-balanced heuristics rather than global maximizers of that utility. V3's low HHI and different holdings help explain why realized returns do not follow the score-utility ranking. No future return was used in the objective. The reference solves a conservative encoded guard model, so ratios are reference comparisons rather than universal optimality gaps.

The neutral-preference and rotating recurring strategies have higher mean primary returns but larger CVaR/drawdown than V3/V4. Existing IntelliVest ranking is not established as return-enhancing. Feasible selection and controlled top-ups jointly explain much of the difference from rank-first; top-ups under feasible selection alone increase utilization by 65.30pp. Carry-forward adds 4.82pp utilization and 0.418pp annualized return while increasing risk. The same-state V3/V4 allocation equality establishes that V4's difference comes from authority, not a distinct allocation algorithm.

## Research questions and hypothesis assessment

| Question | Finding | Assessment |
|---|---|---|
| RQ11 conventional benchmarks | V3/V4 exceed executable ETF and equal-weight mean primary returns but also incur larger CVaR/drawdown; SIP and neutral preferences return more with greater losses | Mixed exploratory evidence; universal superiority unsupported |
| RQ12 allocation efficiency | Large gain over original rank-first; monthly equal-weight slightly exceeds V3 utilization; greedy nearly matches reference utility and exceeds V3 utility | Original-baseline improvement supported; superiority to simple allocation unsupported |
| RQ13 incremental construction | Feasibility and top-ups materially interact; ledger changes authority; score/sizing preferences do not establish better returns | Construction/deployment contribution supported; ranking alpha unsupported |
| RQ14 risk-return | Additional returns accompany additional equity exposure/downside; sector concentration differs materially | Trade-off supported; unqualified risk-adjusted dominance unsupported |
| RQ15 V4 complexity | +4.82pp utilization, +0.418pp return, +0.0278pp daily CVaR, +0.377pp drawdown; same constructor at equal authority | Small deployment gain supported; deployment justification inconclusive |
| RQ16 generalizability | Profile/window/cost/cash/universe sensitivities executed; PIT membership and independent holdout unavailable | Restricted robustness only; external validity inconclusive |

## Data integrity and fairness

Original adjusted equity dataset is unchanged (40 securities, 57,400 observations). Signals use prior/current observed history with next-session close execution. Point-in-time historical index membership remains unresolved: the official workbook ends July 2020. ETF history has six NSE close matches and one independently sourced missing-session repair, separately versioned. NIFTY TRI endpoints were inaccessible. Current sector classification, action reconstruction, ex-date dividend credit, survivorship and provider metadata listing dates remain limitations. The new benchmark is not an independent holdout.

M and C receive identical household contributions and unique approvals. Brokerage cash and approval authority are separately conserved; protected reserves stay outside the account. ETF fund-level exposure is not constrained by single-stock position caps and cannot establish superiority under common stock constraints. All comparisons label the applicable regime. Zero cash yield is primary; 4% is an explicitly frozen-trade overlay. No live database, application policy, account or order was changed.

## Interpretation for publication

A defensible contribution is an audited affordability/authority/execution architecture plus a transparent feasibility-aware sector-priority heuristic and experimental evidence of its effects. A claim of a new general allocation optimization algorithm, reliable alpha, universal risk dominance, statistical generalization to investors or independent external validation is unsupported. Simple greedy and equal-weight methods substantially weaken any claim that high approved-capital utilization is algorithmically unique. V4's small incremental deployment benefit must be weighed against bookkeeping, expiry/revocation burden and additional losses; this experiment does not justify production integration.

## Validation and remaining work

All 28 final focused checks passed. Independent reconciliation covered 281,151 stock-account days and 11,720 guarded purchase batches, plus all 54 ETF accounts and 72 sensitivity ledgers. All 489 previously protected Phase 8 input files are also included in the 854-file unchanged manifest. VALIDATION.json and validation_final.log give the authoritative executed outcomes; no unresolved check failure remains. All earlier research files are hash-protected; protected-source manifests include application files. No frontend/browser/regression suite was run. Detailed report links, CSV schemas, figure captions, exact commands, hashes and source snapshots are in README.md and the run manifests. Real point-in-time membership, independently verified actions, historical ETF look-through exposures, a prospective frozen holdout, score-only ablation and a full-guard exact optimization certificate remain future research, not completed claims.
