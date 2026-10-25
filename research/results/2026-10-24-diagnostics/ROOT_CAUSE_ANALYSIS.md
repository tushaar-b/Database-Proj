# Root-cause analysis: validated diagnostics

This report supplements the immutable INITIAL_ROOT_CAUSE_REPORT.md, which was produced before implementation changes. Run03 and its conference draft remain byte-for-byte preserved. Diagnostics made no database connection and changed no production behavior.

## 1. Why 55 updates did not change principal recommendations

The 55 original effective state updates were all sector-block transitions. No principal event reduced the multiplier or was triggered by VaR/volatility. The multiplier and blocks did reach the research proposal function. An offline parity check of the actual application's feedback builder matched all eight breach combinations. All 42 original/stress replays reproduced every original summary metric, numeric daily ledger column and final monthly order basket.

Of the original 55 updates, 28 persisted until an eligible monthly opportunity. 0 event states changed a positive-share order relative to the **initial fixed No Feedback policy on the same state**, at any opportunity before replacement. Looking across all 432 principal monthly Full decisions, candidate eligibility differed from that same-state fixed-policy counterfactual on 141 decisions, but final positive-share orders differed on 0. This is an internal restriction effect without final recommendation impact.

A second, distinct probe retains each event's immediately previous policy indefinitely, evaluated against the actual later portfolio state. 5 original **policy-release** events eventually differ from that prior-state counterfactual. These releases restore the same unrestricted choices No Feedback already allowed; they do not contradict zero Full-versus-No Feedback differences. Both contrasts are explicitly labelled in the trace. Their long retrospective prior-state latency is not reported as an observed breach correction or asynchronous delivery response.

Each event has exactly one primary classification; buy-only limitations are separate context, not an additional counted cause:

| reason_for_no_change | events |
| --- | --- |
| no_eligible_monthly_opportunity_before_next_policy_update | 27 |
| removed_candidates_did_not_win_existing_exposure_order | 21 |
| restriction_already_satisfied_after_other_exclusions | 7 |

The sector-exposure selector already prefers lower-exposure sectors, held securities are excluded, and at most three distinct sectors are selected. A dominant-sector block commonly removes stocks which would not have won selection. Changes can also occur and disappear between monthly decisions. In the original principal accounts the internally selected baskets also stayed identical: there was no need to invoke a hypothetical downstream rounding explanation for those particular updates. FEEDBACK_TRACE.csv includes prior/current policy, the initial-fixed comparison basis, flags, thresholds, available cash, full candidate lists/ranks and quantities for an actual representative opportunity; no-opportunity events explicitly leave rankings unobserved. FEEDBACK_EVENT_OPPORTUNITIES.csv evaluates every intervening opportunity, not only the first. REPLAY_DIAGNOSTICS.csv records the fixed-policy counterfactual for every decision. Whole-share effects explain deployment failure and some targeted stress events, separately from the principal sector-block redundancy.

Feedback can restrict sectors and reduce future budgets; it does not independently change the historical score formula or execute corrective sales. Live outbox signatures include alert identity, while replay counts effective state changes only. The application aggregates multiple portfolios, evaluates on requests and durably delivers cross-database events; replay models one account, daily risk checks and immediate deterministic state application. No actual asynchronous delivery latency was measured. Live recommendation acceptance records intent; simulated execution is an explicit common assumption. The separate rebalance endpoint is not automatically invoked by feedback.

## 2. Why Sharpe was extreme

Historical Sharpe used sqrt(252) × [mean(time-weighted daily return) − .04/252] / sample sd(daily return), ddof=1. The denominator is not padded by an epsilon. An sd<=1e-15 guard reports NA. The published cross-profile number was the arithmetic mean of defined investor ratios. CAGR is geometric and was separately reported; it was not incorrectly inserted into Sharpe. Independent Decimal calculations confirmed the arithmetic formula.

Investor-level Full results first (rates are fractions, 4% annual linear benchmark):

| scenario | annualized_return | annualized_volatility | annualized_arithmetic_excess_return | sharpe | valid_observations | average_invested_allocation | numerical_validity_status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| high_aggressive | 0.08265 | 0.06734 | 0.04169 | 0.61913 | 988 | 0.47167 | defined |
| high_conservative | 0.02196 | 0.01768 | -0.01812 | -1.02540 | 988 | 0.13121 | defined |
| high_moderate | 0.05331 | 0.04184 | 0.01282 | 0.30645 | 988 | 0.30531 | defined |
| low_aggressive | 0.01511 | 0.01075 | -0.02495 | -2.32019 | 988 | 0.06043 | defined |
| low_conservative | 0.00016 | 0.00030 | -0.03984 | -132.19153 | 988 | 0.00109 | defined_low_volatility |
| low_moderate | 0.00061 | 0.00109 | -0.03939 | -36.26286 | 988 | 0.00389 | defined_low_volatility |
| medium_aggressive | 0.04849 | 0.03535 | 0.00798 | 0.22586 | 988 | 0.23317 | defined |
| medium_conservative | 0.00126 | 0.00164 | -0.03874 | -23.62671 | 988 | 0.00962 | defined_low_volatility |
| medium_moderate | 0.01362 | 0.01364 | -0.02638 | -1.93437 | 988 | 0.07766 | defined |

Distribution summaries across investors:

| strategy | defined | undefined | mean_defined_sharpe | median_defined_sharpe | minimum_defined_sharpe | maximum_defined_sharpe |
| --- | --- | --- | --- | --- | --- | --- |
| Affordability Only | 9 | 0 | -10.27201 | -3.72890 | -50.48303 | 0.51367 |
| Full IntelliVest | 9 | 0 | -21.80107 | -1.93437 | -132.19153 | 0.61913 |
| No Feedback | 9 | 0 | -21.80107 | -1.93437 | -132.19153 | 0.61913 |
| Risk Only | 9 | 0 | 0.83746 | 0.81949 | 0.68455 | 0.98983 |

Full mean −21.80107 is preserved; the median is -1.93437. Near-cash profiles earn almost zero but are measured against a positive benchmark, producing very negative finite ratios when volatility is small. They are economically sensitive to the cash/benchmark convention rather than evidence of denominator clipping. Every ratio remains available. New reporting flags annualized volatility below 1% descriptively without changing the denominator or deleting the ratio; numerically constant series are explicitly undefined using a machine-precision range check. SHARPE_DIAGNOSTICS.csv contains arithmetic and geometric returns, daily/annual benchmark conventions, excess returns, sample sd, observation counts, exposure and validity. Synthetic-return-composite Sharpe is separately labelled and is not the mean investor ratio.

The legacy daily benchmark .04/252 compounds to slightly more than 4% annually. This documented linear convention is not silently corrected. The cash-interest sensitivity instead models 4% effective annual cash return and therefore also reports the consistent geometric daily benchmark. The mismatch between these conventions can matter particularly in nearly cash-only accounts.

For comparison, the synthetic equal-weight daily return composite's Sharpe was -0.68046. It is a different estimand from both −21.80107 (mean of investor ratios) and −1.93437 (median). It is not presented as the investor-level mean, an actual pooled brokerage account, or evidence that averaging away low-exposure investors improves their own outcomes.

## 3. Why cash was 85.62%

No protected reserve is inside brokerage: **0% of observed brokerage cash is a reserve balance**. Reserve is subtracted once from monthly income minus mandatory expenses; only the resulting buffer is contributed. There was no second subtraction in portfolio accounting. Monthly reserve withholding is a flow assumption inherited from the application, not verified accumulation of a real emergency fund. Initial INR 100,000 is pre-existing unreserved brokerage savings. Discretionary expenses are recorded but not deducted by the implemented buffer formula.

Original purchase authorization resets to buffer × tier × multiplier. Accumulated unspent brokerage cash does not enlarge that budget. Tier withholding, small top-three weighted slots, unaffordable selected securities, no repeat purchases of holdings, candidate exhaustion and residual whole-share rounding explain low deployment. This is restrictive rule/design behavior and interaction, not a detected cash-balance or double-reserve accounting defect. 218 Full decisions placed no order despite at least one currently eligible one-share candidate costing no more than the entire batch budget. This is a selection/sizing interaction; it does not prove the same three-slot basket was affordable.

At the monthly signal points, the mean fraction of brokerage cash deferred by the current-month-only authority was 94.13902%; tier withholding accounted for 2.78000%; authorized but unused budget for 1.79930%; and proposed purchases for 1.27889%. These signal-time averages decompose purchase authorization; they are not a causal partition of the separate daily 85.62% cash statistic. All 432 decisions had 40 valid-history candidates before holdings/sector checks. All 93 zero-eligibility decisions had already held every one of those 40 stocks. Missing history and a reserve in brokerage therefore explain none of those cases. Outside-household accumulated savings balances are unmodeled, not measured as zero; the model assumes no additional transfer beyond the stated buffer.

| primary_unused_reason | decisions |
| --- | --- |
| no_eligible_candidates_after_history_holdings_and_sector_rules | 93 |
| partial_basket_unaffordable_selected_slots | 88 |
| positive_purchase_with_round_lot_residual | 33 |
| top_three_slot_sizing_zero_despite_feasible_one_share_candidate | 218 |

All original brokerage cash is financially unreserved money; only a subset is authorized for current orders. Therefore 100% is genuinely unused brokerage cash, but it is incorrect to call 100% immediately policy-deployable. Mean authorized-budget fill was 14.52282%, while mean cumulative unique brokerage funding deployed was 7.39218%. These differ from the prior contributed-surplus utilization of 7.95610%, which excluded starting cash from its denominator.

| scenario | total_unique_brokerage_funding | cash_deployed_including_fees | unique_brokerage_funding_deployed_ratio | decision_budget_fill_ratio | mean_deferred_accumulated_cash | mean_unused_authorized_cash | zero_orders_despite_a_feasible_single_share |
| --- | --- | --- | --- | --- | --- | --- | --- |
| high_aggressive | 4900000.00000 | 1006920.17028 | 0.20549 | 0.27970 | 1637201.47205 | 54022.49645 | 0 |
| high_conservative | 4900000.00000 | 349388.66854 | 0.07130 | 0.29116 | 2203078.00940 | 17721.06941 | 0 |
| high_moderate | 4900000.00000 | 670385.80789 | 0.13681 | 0.27933 | 1918657.67771 | 36033.62900 | 0 |
| low_aggressive | 340000.00000 | 16367.32233 | 0.04814 | 0.09093 | 208284.36668 | 3409.01412 | 33 |
| low_conservative | 340000.00000 | 237.95651 | 0.00070 | 0.00397 | 217341.89729 | 1245.04257 | 47 |
| low_moderate | 340000.00000 | 713.86954 | 0.00210 | 0.00595 | 216925.24187 | 2485.12772 | 47 |
| medium_aggressive | 1060000.00000 | 147191.12990 | 0.13886 | 0.20443 | 468941.97983 | 11933.51813 | 21 |
| medium_conservative | 1060000.00000 | 7164.38402 | 0.00676 | 0.02985 | 566113.38083 | 4850.74200 | 42 |
| medium_moderate | 1060000.00000 | 58435.67124 | 0.05513 | 0.12174 | 537880.27486 | 8782.59018 | 28 |

CASH_UTILIZATION.csv provides a non-overlapping cash-at-signal waterfall: accumulated cash deferred by monthly authority, tier withholding, risk-multiplier withholding, rounding, no-candidate budget, unaffordable selected slots, positive-slot round-lot residual and proposed notional. Their sum reconciles to cash at that decision. Execution costs and overnight changes are shown separately. Sums over opportunities are NOT unique money; unique funding and reserve flow/target are separately identified. These stage labels quantify authorization, not causal Shapley contributions of interacting rules.

## 4. Confirmed corrections and unchanged rules

The confirmed reporting defect was HHI breach-frequency denominator handling. Mean HHI already excluded NA and cash was never an equity sector. The corrected denominator uses only valid holdings observations and explicitly reports coverage. Full had 169 undefined primary HHI sessions. Breach totals and conditional means remain unchanged.

| strategy | original_all_session_breach_frequency | corrected_valid_hhi_breach_frequency | holdings_coverage | mean_hhi_conditional_on_holdings |
| --- | --- | --- | --- | --- |
| Affordability Only | 0.42825 | 0.44670 | 0.98099 | 0.38597 |
| Full IntelliVest | 0.33063 | 0.34898 | 0.98099 | 0.34783 |
| No Feedback | 0.33063 | 0.34898 | 0.98099 | 0.34783 |
| Risk Only | 0.02699 | 0.02702 | 0.99899 | 0.11996 |

Cross-profile means of conditional breach frequencies and pooled valid-session frequencies are different estimands. Both are provided, together with exact denominators:

| strategy | undefined_hhi_sessions | valid_hhi_sessions | breach_sessions | mean_profile_valid_hhi_breach_frequency | pooled_valid_hhi_breach_frequency | mean_hhi_conditional_on_holdings |
| --- | --- | --- | --- | --- | --- | --- |
| Affordability Only | 169 | 8723 | 3808 | 0.44670 | 0.43655 | 0.38597 |
| Full IntelliVest | 169 | 8723 | 2940 | 0.34898 | 0.33704 | 0.34783 |
| No Feedback | 169 | 8723 | 2940 | 0.34898 | 0.33704 | 0.34783 |
| Risk Only | 9 | 8883 | 240 | 0.02702 | 0.02702 | 0.11996 |

No propagation, reserve double-counting, TWR, transaction-cost or Sharpe arithmetic defect was found. No production source was changed. A more complete event-level response definition includes policy releases: the prior breach-episode latency only credited modifications while a breach remained active, so it did not count the concentrated-start release effects. This is reported as a different event/episode outcome, not evidence that a breach was corrected by selling.
