# Controlled ablation results

All findings are exploratory comparisons of nine synthetic profiles sharing historical market paths. Previously inspected observations, overlapping windows, surviving-security selection and current sector labels prevent independent-validation or population-level claims.

All rates below are percent. Guard, feasibility and top-up arms use the frozen constructor switches and identical monthly authority; carry-forward changes only the ledger. These components interact, so marginal effects depend on the chosen control.

| policy | authorized_budget_utilization | decision_purchase_efficiency | feasible_but_unexecuted_total | annualized_return | cvar95 | maximum_drawdown | mean_hhi | mean_cash_allocation |
|---|---|---|---|---|---|---|---|---|
| V1 | 14.523 | 28.009 | 218.000 | 2.635 | 0.310 | 2.882 | 0.348 | 85.621 |
| RANK_GUARD_M | 14.523 | 28.009 | 218.000 | 2.635 | 0.310 | 2.882 | 0.348 | 85.621 |
| FEAS_NO_TOPUP_M | 29.831 | 31.713 | 1.000 | 4.392 | 0.515 | 5.111 | 0.133 | 74.885 |
| RANK_TOPUP_M | 35.285 | 59.259 | 176.000 | 4.548 | 0.482 | 5.284 | 0.340 | 79.013 |
| V3 | 95.134 | 99.306 | 3.000 | 8.614 | 0.899 | 10.106 | 0.106 | 60.492 |
| V4 | 99.958 | 99.537 | 2.000 | 9.031 | 0.927 | 10.483 | 0.106 | 59.136 |
| NEUTRAL_M | 94.760 | 99.537 | 2.000 | 9.029 | 1.012 | 12.050 | 0.105 | 60.328 |
| NEUTRAL_C | 99.938 | 100.000 | 0.000 | 9.417 | 1.048 | 12.365 | 0.104 | 58.714 |


## A — Feasibility-aware selection

RANK_GUARD_M and V1 happen to give identical primary outcomes; this is an observed result, not a promise that guards are irrelevant elsewhere. With no top-ups, feasibility increases utilization from 14.52% to 29.83% (15.31 percentage points), and feasible non-execution falls from 218 to 1. The latter does not imply high deployment: held-name exclusion can remove all opportunities after initial purchases. With top-ups held enabled, replacing rank-first selection by V3 raises utilization from 35.29% to 95.13% (59.85 pp), and feasible non-executions fall from 176 to 3. Return and downside both rise along the changed holding paths. Same-state score utility is greater for V3 than rank-first, but less than greedy/reference.

## B — Existing-holding top-ups

FEAS_NO_TOPUP_M versus V3 isolates top-ups with feasible selection/guards/monthly authority fixed. Utilization rises 29.83% to 95.13% (+65.30 pp), purchase frequency 31.71% to 99.31%, and mean sector HHI falls 0.1329 to 0.1061. Annualized return rises 4.39% to 8.61%, daily CVaR 0.515% to 0.899% and maximum drawdown 5.11% to 10.11%. Top-ups contribute substantially to persistent execution, but their benefit includes added equity exposure. Candidate and holding counts are exported for every decision.

## C — Carry-forward

V3 versus V4 uses an identical constructor. Unique utilization rises 95.13% to 99.96% (+4.82 pp), average invested allocation increases 1.36 pp, annualized return increases 0.418 pp, daily CVaR increases 0.0278 pp and drawdown increases 0.377 pp. Turnover rises from 0.6116 to 0.6333 over four years, with mean fees rising INR968.47 to INR998.87. This is an authorization/deployment policy effect. At the same state and authority, V3 and V4 quantities/objectives are identical over all 432 states.

## D — Ranking/preferences

NEUTRAL_M/C zeroes score and replaces inverse-volatility weights by equal targets, keeping the allocator/eligible set/guards and regime fixed. Neutral M returns 9.03% versus V3 8.61%, but daily CVaR rises 0.899% to 1.012%, drawdown 10.11% to 12.05%, and volatility 6.30% to 7.06%. Neutral C returns 9.42% versus V4 9.03%, with CVaR 1.048% versus 0.927% and drawdown 12.37% versus 10.48%. The combined ranking/sizing preference is not supported as a return improvement. The design cannot separately attribute score ordering and volatility-weight targets; a score-only neutralization would be an additional ablation.

## Equal-weight and sector effects

V3's primary mean sector HHI (0.1061) is below greedy M (0.2523), while equal-weight M is 0.1323. These are endogenous composition differences. Same-state utility and exposure analyses expose this trade-off but do not supply a fixed-sector causal decomposition. Sector-neutral resampling, score-only neutralization and target-weight matching are not claimed as completed experiments.
