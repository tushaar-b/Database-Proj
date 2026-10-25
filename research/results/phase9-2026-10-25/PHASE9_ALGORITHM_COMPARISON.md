# Algorithmic comparison

All findings are exploratory comparisons of nine synthetic profiles sharing historical market paths. Previously inspected observations, overlapping windows, surviving-security selection and current sector labels prevent independent-validation or population-level claims.

## Separate path efficiency from common-state quality

The historical policy table uses each method's own evolving holdings and feedback. In addition, 432 original V3 decision states (9 profiles × 48 monthly decisions) are replayed through each allocator with exactly the same cash, authority, prices, pool and covariance. Every output passes the common eligibility/guard/budget check in these states. V1 still excludes held names by design; common-state comparisons therefore do not by themselves isolate top-ups. The guarded rank-with-top-ups arm provides the more tightly controlled selection contrast.

| method | states | mean_budget_fill | mean_objective | valid_fraction | median_seconds | mean_reference_utility_ratio |
|---|---|---|---|---|---|---|
| GREEDY_M | 432.0000 | 98.9059 | 20526.4886 | 100.0000 | 0.0017 | 99.3886 |
| MILP_M | 432.0000 | 99.0884 | 20569.2597 | 100.0000 | 0.0085 | 100.0000 |
| RANK_TOPUP_M | 432.0000 | 60.7700 | 11267.8264 | 100.0000 | 0.0011 | 37.9616 |
| V1 | 432.0000 | 54.6647 | 10307.6119 | 100.0000 | 0.0002 | 30.9428 |
| V3 | 432.0000 | 97.4300 | 13364.8952 | 100.0000 | 0.0013 | 62.3914 |
| V4 | 432.0000 | 97.4300 | 13364.8952 | 100.0000 | 0.0013 | 62.3914 |


Mean state-wise utility/reference utility is **99.39% for greedy** and **62.39% for V3/V4**. All 432 reference objectives are positive. The integer solver certifies its encoded conservative formulation in all 432 states; it is not a full-guard global optimum certificate because linear grandfathering can be more restrictive at fee-induced cap crossings. Mean utility in INR-score units is dominated by larger budgets; the normalized state-wise ratio is the primary descriptive allocation-quality comparison. No realized future returns enter the objective.

V3/V4 are **not superior under this score-only objective**. Greedy nearly matches the integer reference. V3 instead prioritizes sector balance and a three-sector basket. Their common-state quantities are identical when authority is held fixed. Neither score utility nor higher budget fill implies higher subsequent return. Across actual primary paths, MILP M deploys less authority than greedy M/V3 despite higher same-state utility, illustrating feedback, next-session cancellations, and state-path effects.

## Policy-path efficiency

| policy | authorized_budget_utilization | decision_purchase_efficiency | proposed_basket_execution_rate | feasible_but_unexecuted_total |
|---|---|---|---|---|
| V1 | 14.523 | 28.009 | 100.000 | 218.000 |
| GREEDY_M | 94.255 | 97.454 | 97.454 | 11.000 |
| V3 | 95.134 | 99.306 | 99.306 | 3.000 |
| MILP_M | 92.013 | 95.833 | 95.833 | 18.000 |
| EQUAL_M | 95.684 | 98.843 | 98.843 | 5.000 |
| SIP_M | 94.074 | 98.843 | 99.534 | 5.000 |
| ETF_M | 97.085 | 100.000 | 100.000 | 0.000 |
| GREEDY_C | 99.683 | 94.907 | 94.907 | 22.000 |
| V4 | 99.958 | 99.537 | 99.537 | 2.000 |
| MILP_C | 99.802 | 95.602 | 95.602 | 19.000 |
| EQUAL_C | 99.974 | 99.537 | 99.537 | 2.000 |
| SIP_C | 99.882 | 99.537 | 99.768 | 2.000 |
| ETF_C | 99.930 | 100.000 | 100.000 | 0.000 |
| NEUTRAL_M | 94.760 | 99.537 | 99.537 | 2.000 |
| NEUTRAL_C | 99.938 | 100.000 | 100.000 | 0.000 |


Execution feasibility is both the all-decision purchase fraction and the purchase fraction conditional on a nonzero proposal. Feasible-but-unexecuted counts use a compliant one-share witness at the signal date; some failures reflect next-session drift/guard cancellation and cannot all be attributed to signal design. No claim is made that a simultaneous multi-security basket cannot exist when no single-share witness passes.

## Runtime under matched states

| candidate_size | method | median | min | max |
|---|---|---|---|---|
| 10.0000 | GREEDY_M | 0.7828 | 0.4230 | 2.6907 |
| 10.0000 | MILP_M | 10.4204 | 6.2561 | 143.1301 |
| 10.0000 | V1 | 0.1104 | 0.0955 | 0.2300 |
| 10.0000 | V3 | 0.5142 | 0.2974 | 0.9045 |
| 10.0000 | V4 | 0.5954 | 0.2985 | 1.0540 |
| 20.0000 | GREEDY_M | 1.2488 | 0.5970 | 4.0857 |
| 20.0000 | MILP_M | 20.6004 | 6.8127 | 238.7422 |
| 20.0000 | V1 | 0.1489 | 0.1350 | 0.3745 |
| 20.0000 | V3 | 0.8222 | 0.4556 | 1.1405 |
| 20.0000 | V4 | 0.7844 | 0.4554 | 1.6400 |
| 40.0000 | GREEDY_M | 1.8175 | 1.0451 | 4.3583 |
| 40.0000 | MILP_M | 32.3879 | 7.6248 | 114.1919 |
| 40.0000 | V1 | 0.2204 | 0.1976 | 0.3328 |
| 40.0000 | V3 | 1.2445 | 0.7373 | 1.9679 |
| 40.0000 | V4 | 1.2972 | 0.7288 | 1.6949 |


Units for median/min/max are milliseconds. Six historical states (first two monthly decisions for low-conservative, medium-moderate and high-aggressive), sizes 10/20/40 selected by ticker order, five repetitions per combination; 450 timed allocations. At n=40, median V3 is 1.244 ms, greedy 1.818 ms and integer reference 32.388 ms. These are shared-process CPU wall times on arm64 / Darwin 27.0.0; full hardware metadata is retained. Process caches, scheduling and only six states limit generalization. No extrapolation to thousands of securities or unconditional computational superiority is supported.

## Constraint interpretation

All executed guarded baskets are reconciled against pre-fill existing holdings, actual execution close and lagged decision covariance. Natural drift, bootstrap HHI exceptions and grandfathering remain visible; a nonzero breach duration is not automatically an illegal purchase. V1 is preserved with its original restrictions, not silently hardened. ETF is outside the common stock-utility experiment. Legacy and new algorithms remain isolated from application recommendation routes.
