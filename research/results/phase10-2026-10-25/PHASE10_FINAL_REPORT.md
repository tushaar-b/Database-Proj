# IntelliVest Phase 10 final report

**Scientific decision: C — applied affordability-aware allocation framework with strong baseline execution improvements but limited established methodological novelty.** Exploratory evidence from nine synthetic investor profiles and previously examined historical paths. No independent holdout, unbiased point-in-time universe or population-level investor inference is established.

## Executed evidence

27 primary frozen V1/V3/V4 replays with daily parity; 2160 prior matched allocator outputs/objectives reproduced; 432 saved V3 states; 7344 matched allocation calls across F3 and Fwide; 69 scalability cases with 828 timed calls, 276 warm-ups and 276 memory calls; 24 authority replays; twelve lifecycle scenarios; and 24 exhaustive tiny-state optimization checks. These are computation counts, not independent investors. 29 focused checks passed and 0 failed. All 5514 protected files remain unchanged, including Phase9's entire output manifest and its854-file prior-input manifest.

## Strongest positive finding

Approved-capital utilization is reproduced at 14.52% for V1 and 95.13% for V3 (+80.61pp). Actual purchase frequency rises28.01%→99.31%, and signal-feasible decisions without next-session purchases fall218→3. The Phase9 controlled no-topup comparison29.83%→95.13% confirms existing-holding compatibility is a major component. This is a combined policy/constructor improvement over the original baseline; it does not establish a unique advantage over all budget-aware allocators. Equal-weight and greedy remain material comparators.

## Equal-constraint and trade-off results

| method | states | valid_rate | purchase_rate | mean_U_norm | mean_budget_fill | mean_HHI | mean_purchase_positions | ND_UD_rate | ND_UDB_rate |
|---|---|---|---|---|---|---|---|---|---|
| GREEDY | 432.000 | 100.000 | 100.000 | 94.607 | 98.760 | 0.118 | 2.257 | 67.824 | 76.389 |
| REF_B | 432.000 | 100.000 | 99.769 | 40.415 | 99.764 | 0.111 | 2.898 | 22.917 | 99.769 |
| REF_U | 432.000 | 100.000 | 100.000 | 95.309 | 98.993 | 0.120 | 2.162 | 100.000 | 100.000 |
| V3 | 432.000 | 100.000 | 100.000 | 59.778 | 97.430 | 0.106 | 2.870 | 97.685 | 98.148 |
| V4 | 432.000 | 100.000 | 100.000 | 59.778 | 97.430 | 0.106 | 2.870 | 97.685 | 98.148 |


V3 is observed-nondominated in 98.15% on U/D/B and 97.69% on U/D. Greedy dominates it in 0.69%. V3 mean utility/reference ratio is62.55% over 432 certified covered states. Unfavorable objective scores, higher-reference utility at similar HHI and negative cases are retained. Similar-HHI and similar-utility matching use prespecified tolerances with explicit coverage. The frontier is observed; neither all global Pareto points nor nonlinear joint-objective optima are claimed.

Under the prespecified balanced U/D/B objective V3 is best observed in only3.01% of states, versus 85.42% for pure diversification. Its high observed nondominance is limited by the coarse reference HHI grid:348/432 V3 allocations lie below the lowest extra cap .10. Near-HHI references offer mean additional normalized utility0.3431 over 397 covered states. These qualifications prevent a strong optimal-diversification claim.

## Research questions

| RQ | Evidence-based answer |
|---|---|
| RQ17 | Original primary deployment14.52%→95.13%; purchase frequency28.01%→99.31%; signal-feasible non-execution218→3. The endpoint includes next-session cancellations. |
| RQ18 | F3 mean V3−greedy U/B=-0.348281, fill=-0.013301, HHI=-0.012113; trade-off, not dominance. |
| RQ19 | V3 observed ND UDB=98.15%; greedy dominates it in 0.69%; global Pareto status unproven. |
| RQ20 | Controlled historical/synthetic size, budget, holdings, sector, cap and dispersion experiments completed; timings/memory/status retained. |
| RQ21 | V3/V4 same allocations at equal authority. V4 adds deployment and exposure, variable downside and dated-lot bookkeeping. Optional extension recommended. |
| RQ22 | Applied household-authority/feasibility integration and reproducible evaluation; new general optimizer or universal novelty not established. |

One solver-reported optimal budget certificate was withheld after a INR0.004357 objective-bound discrepancy; its allocation remains guard-compliant. Raw and audited status files are retained. This is a certification qualification, not an unsafe trade.

## Statistical and financial interpretation

Paired monthly allocation differences use three-month circular blocks,2000 draws, seed 20261025, with synchronized date blocks across the nine synthetic profiles. Intervals describe conditional temporal variability, not investor-population effects. Per-profile/stratum distributions and both positive/negative examples are exported. Phase9 financial risk trade-offs remain intact: V3/V4 return8.61%/9.03% with daily CVaR0.899%/0.927% and drawdown10.11%/10.48%; no claim of lower risk from higher deployment is made.

V4 adds4.82pp utilization and 1.36pp exposure, with 0.418pp extra annualized return and 0.0278pp extra daily CVaR on average. It is an optional authority extension, not a distinct constructor or an automatically preferred default. Primary ledger lot count reaches3 versus 1; no-spend expiry checks reach12. Production atomicity and withdrawal recovery remain untested.

## Worked historical example

Verified historical example: medium_moderate|2022-01-03, saved approved budget INR10000.00, actual cash INR120000.00, existing holdings 0. These are historical research inputs, not illustrative invented prices.

| method | ticker | sector | existing_quantity | purchased_quantity | observed_price | inclusive_cost |
|---|---|---|---|---|---|---|
| V3 | BRITANNIA | Consumer Goods | 0.0000 | 1.0000 | 3617.5500 | 3622.9782 |
| V3 | INFY | Information Technology | 0.0000 | 2.0000 | 1898.4500 | 3802.5972 |
| V3 | SUNPHARMA | Healthcare | 0.0000 | 3.0000 | 848.9500 | 2550.6716 |
| GREEDY | INFY | Information Technology | 0.0000 | 5.0000 | 1898.4500 | 9506.4929 |
| GREEDY | NTPC | Power | 0.0000 | 3.0000 | 126.0000 | 378.5672 |
| REF_U | HINDUNILVR | Consumer Goods | 0.0000 | 1.0000 | 2361.3000 | 2364.8432 |
| REF_U | INFY | Information Technology | 0.0000 | 4.0000 | 1898.4500 | 7605.1943 |

| method | cost | budget_fill | U_norm | HHI | purchase_positions |
|---|---|---|---|---|---|
| V3 | 9976.2469 | 99.7625 | 93.6714 | 0.3425 | 3.0000 |
| GREEDY | 9885.0601 | 98.8506 | 94.8174 | 0.9263 | 2.0000 |
| REF_U | 9970.0375 | 99.7004 | 95.8816 | 0.6381 | 2.0000 |


## Novelty and paper positioning

Eight verified primary-source references establish prior art for integer lots, cardinality, costs, rebalancing, sectors and heuristic trade-offs. The differentiator is an applied integration of household-approved authority, protected reserve separation, whole-share feasibility, top-ups, combined guards and auditable delayed execution. No new general optimizer or proof of first-ever combination is established. Lead with the execution problem and quantified baseline improvement; present the Pareto and greedy evidence as a fair boundary on the contribution.

1. **Recommended — IntelliVest: Feasibility-Aware Whole-Share Portfolio Construction Under Household Affordability and Risk Constraints.** Focus: domain-specific method and tested execution improvement. Evidence: reproduced authority utilization, matched guards, trade-offs and latency. Weakness: limited novelty, exposed surviving universe. Position: applied algorithmic methodology/experimental systems paper. “Algorithm” is acceptable for pseudocode, but the title should not imply a new exact optimizer.

2. **Converting Approved Retail Investment Budgets into Executable Whole-Share Portfolios: An Experimental Study.** Focus: auditability and execution evidence. Evidence: utilization, top-up ablations, actual cost/guard reconciliation. Weakness: weaker methodological novelty. Position: applied quantitative systems and reproducibility.

3. **Utility–Diversification Trade-offs in Affordability-Constrained Whole-Share Portfolio Construction.** Focus: equal-constraint comparison and observed Pareto study. Evidence: paired frontier/objective results and scaling. Weakness: finite search, resource caps and no global frontier. Position: experimental comparison; avoid “optimal” in the title.

## Remaining limitations and readiness

The universe has 40 surviving retained securities and 57,400 Yahoo/yfinance observations with sparse independent exchange checks, current sector labels, listing metadata rather than certificates, and corporate-action/dividend timing limitations. Historical periods were already inspected. Phase9's new ETF is a benchmark, not a holdout; daily TRI and complete historical index membership remain unavailable. Synthetic scaling has no financial-performance meaning. Solver timeouts restrict alternative coverage; memory excludes native solver RSS. Some cap sensitivities are explicitly labelled structure adapters rather than frozen-policy outputs.

The package is ready for coauthor review and venue-specific manuscript preparation, **not ready to claim independently validated or novel-optimizer superiority**. A stronger submission needs a prospective freeze/unexamined point-in-time data, stronger external comparators matched to the household domain, a closer systematic novelty search, and realistic withdrawal/persistence/cost/action validation. The polished draft remains separate from every earlier paper.
