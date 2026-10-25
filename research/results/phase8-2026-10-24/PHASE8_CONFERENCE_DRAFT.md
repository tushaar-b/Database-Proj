# Phase 8 conference draft — separate from all earlier paper material

## Motivation

Earlier implementation and historical diagnostics showed that financial affordability constraints could coexist with high cash allocation and nonbinding feedback. We investigated a second-generation research policy without changing the live application or treating reused historical periods as untouched validation.

## Proposed Improvements

We implemented FIFO carry-forward of tier-approved monthly authority, feasibility-aware whole-share construction, controlled holding top-ups and explicit position/sector/risk guards. The principal feedback extension redirected purchases away from every overweight sector. A separate secondary arm investigated capped, cost-bearing corrective sales and recycled-proceeds authorization. Neither intervention placed live trades or modified user portfolios.

## Experimental Design

The same nine synthetic profiles, starting capital, reserve-protected contributions, restricted 40-security adjusted-price dataset, historical ranking/momentum inputs, monthly decisions, daily monitoring and next-session execution were shared. Fees/slippage were 10/5 bp. The primary 2022–2025 window and additional 2022–2023, 2024–2025 and 2026 YTD windows had previously been inspected; the entire study is exploratory. No outcome-driven parameter search or independent holdout claim was used.

## Baseline Comparison

V1 reproduced the frozen original Full policy before comparison. V2 changed approval carry-forward only; V3 changed feasible construction/top-ups with declared guards; V4 combined these mechanisms; V5 added purchase redirection. Corrective selling remained separate. The complete method, authority conservation equation, original monthly-reference overspend and alternative fresh-funding definitions are disclosed in the accompanying reports.

## Results

| metric | V1 | V2 | V3 | V4 | V5 |
| --- | --- | --- | --- | --- | --- |
| authorized_budget_utilization | 0.14523 | 0.57053 | 0.95134 | 0.99958 | 0.99958 |
| feasible_but_unexecuted | 24.22222 | 6.22222 | 0.33333 | 0.22222 | 0.22222 |
| mean_cash_allocation | 0.85621 | 0.69246 | 0.60492 | 0.59136 | 0.59136 |
| purchase_frequency | 0.28009 | 0.46991 | 0.99306 | 0.99537 | 0.99537 |
| mean_hhi | 0.34783 | 0.13570 | 0.10607 | 0.10588 | 0.10588 |
| hhi_breach_frequency | 0.34898 | 0.05582 | 0.02938 | 0.02578 | 0.02578 |
| hhi_breach_sessions | 326.66667 | 54.22222 | 29.00000 | 25.44444 | 25.44444 |
| var95 | 0.00205 | 0.00430 | 0.00565 | 0.00582 | 0.00582 |
| cvar95 | 0.00310 | 0.00666 | 0.00899 | 0.00927 | 0.00927 |
| maximum_drawdown | 0.02882 | 0.07127 | 0.10106 | 0.10483 | 0.10483 |
| annualized_volatility | 0.02107 | 0.04496 | 0.06302 | 0.06492 | 0.06492 |
| annualized_return | 0.02635 | 0.05880 | 0.08614 | 0.09031 | 0.09031 |
| sharpe | -21.80107 | 0.21315 | 0.56771 | 0.61233 | 0.61233 |
| turnover | 0.12506 | 0.34411 | 0.61157 | 0.63332 | 0.63332 |
| transaction_fees | 250.50560 | 352.63017 | 968.47133 | 998.87102 | 998.87102 |
| slippage_cost | 125.19021 | 176.22697 | 483.99367 | 499.18592 | 499.18592 |
| new_position_trades | 22.44444 | 37.55556 | 26.00000 | 26.00000 | 26.00000 |
| topup_trades | 0.00000 | 0.00000 | 109.55556 | 109.33333 | 109.33333 |
| changed_recommendations | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 |
| actual_trade_changed_decisions | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 |
| household_new_draw_violations | 0.00000 | 0.00000 | 0.00000 | 0.00000 | 0.00000 |
| monthly_reference_violation_rate | 0.00000 | 0.03704 | 0.00000 | 0.00463 | 0.00463 |

Investor-level results, including extreme finite Sharpe ratios, are retained. Higher utilization was not treated as proof of better risk-adjusted performance. Feedback state changes, recommendation changes, executed changes, costs and subsequent concentration persistence were separately measured.

## Ablation Analysis

| policy | authorized_budget_utilization | feasible_but_unexecuted | annualized_return | cvar95 | mean_hhi | topup_trades | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FEAS_ONLY | 0.29831 | 0.11111 | 0.04392 | 0.00515 | 0.13287 | 0.00000 | 0.20733 |
| GUARDS_ONLY | 0.14523 | 24.22222 | 0.02635 | 0.00310 | 0.34783 | 0.00000 | 0.12506 |
| TOPUP_ONLY | 0.35285 | 19.55556 | 0.04548 | 0.00482 | 0.33983 | 42.00000 | 0.30603 |
| V1 | 0.14523 | 24.22222 | 0.02635 | 0.00310 | 0.34783 | 0.00000 | 0.12506 |
| V2 | 0.57053 | 6.22222 | 0.05880 | 0.00666 | 0.13570 | 0.00000 | 0.34411 |
| V3 | 0.95134 | 0.33333 | 0.08614 | 0.00899 | 0.10607 | 109.55556 | 0.61157 |
| V4 | 0.99958 | 0.22222 | 0.09031 | 0.00927 | 0.10588 | 109.33333 | 0.63332 |
| V4_NO_MOMENTUM | 0.99789 | 0.22222 | 0.08897 | 0.00930 | 0.10612 | 110.22222 | 0.63332 |
| V5 | 0.99958 | 0.22222 | 0.09031 | 0.00927 | 0.10588 | 109.33333 | 0.63332 |

## Discussion

- RQ6: Supported in the studied scenarios.
- RQ7: Supported in the studied scenarios.
- RQ8: Partially supported.
- RQ9: Unsupported for incremental principal purchase-redirection actionability.
- RQ10: Inconclusive as an overall superiority claim; measured risk/performance trade-offs available.

## Threats to Validity

Current-universe survivorship, incomplete point-in-time membership and corporate-action certification, synthetic household assumptions, previously examined dates, modeled cash authority and simplified transaction costs constrain external validity. The initial bootstrap and grandfathered drift are explicit guard exceptions. Conditional moving-block intervals are descriptive; correlated sessions and scenario permutations are not independent investor experiments. The ranked integer heuristic is reproducible but does not claim global optimality. No omitted live CVaR constraint or real-world tax model is implied.

## Conclusion

The study measured whether explicit authority, feasibility, top-up and feedback changes affected decisions and investment outcomes. The tables and ablations support only the component-specific classifications above. Results do not establish overall investment superiority, a validated forecast or readiness to apply new trading behavior to real users. Independent prospective evidence would be required before such claims.

## Additional stress interpretation

The following concentrated-start cases had already been examined in previous phases. They are targeted exploratory mechanism probes, not new holdouts. Monthly purchase redirection remains identical to V4 in these cases. Corrective selling is a distinct additional action with explicit costs and recycling; all adverse outcomes remain visible. In the low/conservative stress, observed HHI-breach sessions fell from 988 to 148, while turnover and costs increased; the high/aggressive selling stress had lower return than the buy-only parent. This supports conditional actionability of the separate selling mechanism, not general superiority or a principal-redirection effect.

| scenario | policy | annualized_return | cvar95 | mean_hhi | hhi_breach_sessions | hhi_episodes_resolved | sell_trades | turnover | transaction_fees |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| low_conservative | V4 | 0.10945 | 0.04445 | 0.62293 | 988 | 0 | 0 | 0.21011 | 59.77355 |
| low_conservative | V5 | 0.10945 | 0.04445 | 0.62293 | 988 | 0 | 0 | 0.21011 | 59.77355 |
| low_conservative | V5_SELL | 0.17007 | 0.02734 | 0.19632 | 148 | 8 | 7 | 0.63598 | 195.20570 |
| medium_moderate | V4 | 0.15707 | 0.02847 | 0.22752 | 269 | 1 | 0 | 0.63976 | 479.42419 |
| medium_moderate | V5 | 0.15707 | 0.02847 | 0.22752 | 269 | 1 | 0 | 0.63976 | 479.42419 |
| medium_moderate | V5_SELL | 0.16393 | 0.02264 | 0.15004 | 81 | 1 | 4 | 0.74508 | 568.57868 |
| high_aggressive | V4 | 0.18569 | 0.02025 | 0.10512 | 21 | 1 | 0 | 1.04524 | 3596.17013 |
| high_aggressive | V5 | 0.18569 | 0.02025 | 0.10512 | 21 | 1 | 0 | 1.04524 | 3596.17013 |
| high_aggressive | V5_SELL | 0.18392 | 0.01984 | 0.10268 | 21 | 1 | 1 | 1.05448 | 3628.31174 |

Primary corrective-selling means (separate from V5):

| policy | changed_recommendations | actual_trade_changed_decisions | hhi_breach_sessions | hhi_episodes_resolved | transaction_fees | turnover | annualized_return | cvar95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| V5_SELL | 0.22222 | 0.22222 | 25.44444 | 1.33333 | 1000.42033 | 0.63413 | 0.09042 | 0.00930 |

In the primary nine profiles, V5_SELL executed three sales across two monthly decisions. Its mean breach duration stayed equal to V4/V5 at 25.44444 sessions; resolved HHI-episode totals also stayed equal (12 observed episodes). Thus actual corrective transactions did not establish an incremental primary concentration-duration improvement.

