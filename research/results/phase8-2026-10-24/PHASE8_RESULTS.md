# Phase 8 results: capital efficiency and actionable feedback

Evidence classification: **exploratory historical comparison on previously inspected restricted-universe data**. No new holdout or overall-superiority claim is made. V1 was reproduced before revised policies. 249 distinct configured replays completed. Prior studies, data and source remain protected. All monetary values are INR; rates/returns are fractions unless a figure says percent; duration is observed sessions. Means below weight the nine synthetic profiles equally. Undefined Sharpe/HHI is NA, never zero.

## Five-policy primary comparison (2022–2025)

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

Authority utilization counts each external approval once. The monthly-reference rate retains the original proposed notional > current monthly buffer definition, even when older valid approvals fund spending; it must not be relabelled as new household overspending. Fresh household, authority and reserve violations are separately verified. Initial unapproved cash and tier withholding are not misdescribed as protected reserves. The controlled carry design differs from the precursor unrestricted-cash sensitivity.

## RQ6–RQ10

- **RQ6: Supported in the studied scenarios.**
- **RQ7: Supported in the studied scenarios.**
- **RQ8: Partially supported.**
- **RQ9: Unsupported for incremental principal purchase-redirection actionability.**
- **RQ10: Inconclusive as an overall superiority claim; measured risk/performance trade-offs available.**

More deployed money is not proof of better stock selection. Additional guards, feasibility order, top-ups and carry interact; the ablation controls and exposure diagnostics are necessary. No conclusion is based only on the policy with highest return. Investor-level Sharpe and its range are retained rather than concealing unfavorable small-volatility outcomes:

| policy | defined | undefined | mean_sharpe | median_sharpe | min_sharpe | max_sharpe |
| --- | --- | --- | --- | --- | --- | --- |
| V1 | 9 | 0 | -21.80107 | -1.93437 | -132.19153 | 0.61913 |
| V2 | 9 | 0 | 0.21315 | 0.38314 | -0.86717 | 0.84807 |
| V3 | 9 | 0 | 0.56771 | 0.72864 | -0.18935 | 0.98698 |
| V4 | 9 | 0 | 0.61233 | 0.76072 | -0.07309 | 1.01489 |
| V5 | 9 | 0 | 0.61233 | 0.76072 | -0.07309 | 1.01489 |

## Feedback responsiveness versus risk correction

| policy | policy_updates | changed_recommendations | actual_trade_changed_decisions | hhi_episodes_resolved | hhi_episode_resolution_fraction | hhi_breach_sessions | feedback_incremental_fees |
| --- | --- | --- | --- | --- | --- | --- | --- |
| V1 | 6.11111 | 0.00000 | 0.00000 | 0.77778 | 0.77778 | 326.66667 | 0.00000 |
| V2 | 4.88889 | 0.00000 | 0.00000 | 1.00000 | 1.00000 | 54.22222 | 0.00000 |
| V3 | 2.66667 | 0.00000 | 0.00000 | 1.00000 | 1.00000 | 29.00000 | 0.00000 |
| V4 | 3.33333 | 0.00000 | 0.00000 | 1.33333 | 1.00000 | 25.44444 | 0.00000 |
| V5 | 3.88889 | 0.00000 | 0.00000 | 1.33333 | 1.00000 | 25.44444 | 0.00000 |

Same-state counters isolate active policy rules at the same actual portfolio/budget base. V1–V4 compare original feedback with a fixed initial policy; V5 compares its additional intervention with V4. Incremental fees/slippage are signed differences against an execution counterfactual, not the total cost of every basket marked changed. Paired path differences are separately exported. Breach resolution is an observed event outcome with terminal censoring, not automatically caused by a restriction or proposal. Policy timing is immediate state application at the scheduled daily observation, not measured live delivery latency.

## Secondary corrective-selling arm (not mixed into V5)

| scenario | policy | annualized_return | cvar95 | mean_hhi | hhi_breach_sessions | turnover | transaction_fees | sell_trades | realized_gain |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| low_conservative | V5_SELL | 0.03821 | 0.00415 | 0.12274 | 61 | 0.25214 | 59.83958 | 0 | 0.00000 |
| low_moderate | V5_SELL | 0.06805 | 0.00718 | 0.11195 | 25 | 0.48081 | 119.85136 | 0 | 19.04267 |
| low_aggressive | V5_SELL | 0.09527 | 0.01029 | 0.10515 | 20 | 0.68412 | 179.74130 | 0 | 10.33912 |
| medium_conservative | V5_SELL | 0.05080 | 0.00536 | 0.10732 | 20 | 0.37162 | 239.58861 | 0 | 5.85886 |
| medium_moderate | V5_SELL | 0.09793 | 0.00984 | 0.09965 | 20 | 0.68622 | 479.35110 | 0 | 6.53225 |
| medium_aggressive | V5_SELL | 0.14247 | 0.01366 | 0.09919 | 20 | 0.95542 | 720.92444 | 1 | 50.35751 |
| high_conservative | V5_SELL | 0.05523 | 0.00601 | 0.10858 | 23 | 0.42574 | 1198.73972 | 0 | 8.34468 |
| high_moderate | V5_SELL | 0.10704 | 0.01129 | 0.09903 | 20 | 0.77858 | 2397.38043 | 0 | 8.85553 |
| high_aggressive | V5_SELL | 0.15878 | 0.01589 | 0.09939 | 20 | 1.07250 | 3608.36643 | 2 | -252.02341 |

Selling is whole-share, capped at 10% invested value per monthly decision, minimum INR 500, requires lower measured HHI, and pays the same fees/adverse slippage. It never liquidates to manufacture an empty diversified portfolio. Taxes are excluded. Recycled proceeds are recorded separately from household approvals. Trades are simulated only. Compare this arm with V5 and V4 rather than attributing its effects to purchase redirection.

## Statistical evidence and robustness

Paired profile/window differences, mean/median differences and circular 20-session block intervals (2,000 draws, seed 20261024) are exported. Representative medium/moderate annualized arithmetic daily-return differences—not CAGR differences—are:

| contrast | mean_annualized_arithmetic_return_difference | ci95_low | ci95_high | interval_status |
| --- | --- | --- | --- | --- |
| V2 - V1 | 0.04960 | 0.01349 | 0.08643 | conditional_descriptive_block_interval |
| V3 - V1 | 0.07582 | 0.02645 | 0.12932 | conditional_descriptive_block_interval |
| V4 - V1 | 0.08218 | 0.03114 | 0.13727 | conditional_descriptive_block_interval |
| V5 - V4 | 0.00000 | 0.00000 | 0.00000 | conditional_descriptive_block_interval |

Nine profiles are deterministic scenarios, not random sampled investors. Windows overlap and have all been examined previously. Conditional intervals do not support population efficacy or independent predictive validation; no p-values are invented. EXPOSURE_ADJUSTED.csv (lowercase filename exposure_adjusted.csv) reports same-date positive-exposure and same-bin coverage. Net/gross sleeve diagnostics are not equivalent to actual investor account returns, and sparse matches do not justify causal stock-selection claims.

## Limitations and interpretation

The 40-security current surviving universe omits delisted stocks and complete historical membership/identity. Sparse exchange checks do not certify every corporate action; vendor-adjustment vintages are unavailable. Current sector labels, split reconstruction and ex-date dividend availability are inherited approximations. The profiles are synthetic; reserve subtraction is the implemented monthly-flow convention and discretionary expenses remain outside the buffer deduction. Costs are simplified proportional assumptions with taxes/market impact excluded. New position/sector caps allow explicit bootstrap and grandfathered drift; they do not promise zero market-induced breaches. There is no hard CVaR eligibility limit, globally optimal integer allocation proof, or live automated trading. Construction can miss jointly feasible multi-stock solutions that require accepting an individually inadmissible intermediate lot.

Household-deterioration and concentrated-start stress results are separately labelled in investor_level_results.csv. They do not substitute for the primary null/unfavorable outcomes. A future product change requires explicit financial authorization semantics and prospective evaluation; no live behavior was changed here.

## Figures

**figure_1_capital_utilization** — Equal-profile means, primary 2022–2025. Each external approval is counted once. Cash includes unapproved starting savings and tier-withheld transfers, but no protected reserve. Utilization and cash allocation have different denominators.

**figure_2_portfolio_value** — Nominal equity includes contributions. Dotted lines show the same initial cash plus transfers. Cash-flow-adjusted returns are separately reported; increased contributions are not counted as profits.

**figure_3_hhi** — Cash is not a sector; empty portfolios have undefined HHI. Initial three-sector bootstrap baskets may breach .25 and are explicitly monitored. New guards prevent worsening purchases; subsequent market drift can still cause breaches.

**figure_4_drawdown** — Drawdown uses a time-weighted wealth index and includes the initial peak of one. Increased capital deployment is not automatically improved downside performance.

**figure_5_execution_efficiency** — A feasible single-share witness is not proof of global integer-basket feasibility. Original witness resolution is matched by date/profile on different evolving portfolio paths; it is not a causal claim that all 218 could be resolved under identical states.

**figure_6_feedback** — V1–V4 same-state counters freeze original feedback; V5 counters use V4 on the same state. V5_SELL is a separate secondary intervention. Resolution/shorter persistence is observed, not automatically attributed to a policy update. Comparisons have the same nine primary profiles.

**figure_7_risk_return** — Every point is a profile-policy outcome on the same previously inspected window. Differences in exposure, guards, selection and top-ups are examined in ablations; this is not a fitted efficient frontier.

**figure_8_ablations** — Guard-only, feasibility-only and top-up-only arms share the new safeguards. V1/V3 is a combined change including guard assumptions, not a pure feasibility estimate. Returns/risks are descriptive and are not selected to favor higher deployment.

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

Household deterioration stresses used identical reduced contributions for all versions. January–March 2024 purchases were suspended and unused carry was revoked; no holdings were automatically liquidated due to reduced income. These scenarios do not include exogenous brokerage withdrawals; generic authority revocation is available and numerically tested, but no empirical withdrawal outcome is claimed.

| scenario | policy | revoked_authority | external_approved_grants | authorized_budget_utilization | annualized_return | mean_cash_allocation |
| --- | --- | --- | --- | --- | --- | --- |
| low_conservative | V1 | 1250.00000 | 56250.00000 | 0.00423 | 0.00016 | 0.99888 |
| low_conservative | V2 | 6379.10980 | 56250.00000 | 0.75972 | 0.02520 | 0.88918 |
| low_conservative | V3 | 137.73355 | 56250.00000 | 0.91776 | 0.03531 | 0.85099 |
| low_conservative | V4 | 381.72444 | 56250.00000 | 0.99188 | 0.03872 | 0.84004 |
| low_conservative | V5 | 381.72444 | 56250.00000 | 0.99188 | 0.03872 | 0.84004 |
| medium_moderate | V1 | 10000.00000 | 450000.00000 | 0.10518 | 0.01359 | 0.92335 |
| medium_moderate | V2 | 1357.00261 | 450000.00000 | 0.53032 | 0.06570 | 0.64620 |
| medium_moderate | V3 | 618.19381 | 450000.00000 | 0.95572 | 0.09261 | 0.57775 |
| medium_moderate | V4 | 543.53429 | 450000.00000 | 0.99854 | 0.09920 | 0.56560 |
| medium_moderate | V5 | 543.53429 | 450000.00000 | 0.99854 | 0.09920 | 0.56560 |
| high_aggressive | V1 | 75000.00000 | 3375000.00000 | 0.29835 | 0.08458 | 0.51489 |
| high_aggressive | V2 | 750679.05241 | 3375000.00000 | 0.31091 | 0.08736 | 0.49731 |
| high_aggressive | V3 | 5195.26447 | 3375000.00000 | 0.97227 | 0.15280 | 0.29464 |
| high_aggressive | V4 | 23696.70466 | 3375000.00000 | 0.99293 | 0.16021 | 0.27734 |
| high_aggressive | V5 | 23696.70466 | 3375000.00000 | 0.99293 | 0.16021 | 0.27734 |
