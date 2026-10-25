# Updated research report: diagnostics and controlled re-evaluation

Evidence classification remains **exploratory restricted-universe historical research**. No previous baseline file was overwritten. The initial root-cause report preceded implementation. This report distinguishes software correctness, internal policy changes, final decisions, actual transactions and risk correction.

## 1. Motivation and original findings

Run03 reported 55 principal feedback adjustments but zero changed recommendations, mean Full Sharpe −21.80107 and 85.62147% cash. H1 had controlled compliance support; H2 was mixed; central H3 effectiveness was unsupported; financial performance varied with exposure. These historical findings remain preserved. The same frozen 40-security, 57,400-observation dataset and 2022–2025 primary window were used here, with no ranking retuning, calendar selection or forced selling.

## 2. Root causes and validation

See ROOT_CAUSE_ANALYSIS.md and its event classifications. All 36 principal and six concentrated-start No Feedback/Full reproductions matched the old financial metrics, daily ledger and final baskets. Twenty-seven focused checks verified application/research feedback parity, policy propagation, independent high-precision Sharpe calculations, annualization, benchmark conversion, constant-denominator handling, contributions, reserve deduction, authorization-waterfall reconciliation, cash compounding and HHI. Independent position-level sector aggregation verified replay HHI. No unrelated application/UI tests or database connections were used.

Investor-level Full results before aggregate summaries (rates are fractions):

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

## 3. Corrected reporting

The HHI breach denominator now excludes undefined equity-portfolio sessions. NA is not zero HHI. Original means and breach counts remain valid. Investor-level Sharpe arithmetic was correct under its stated linear benchmark; the former mean alone was misleading. We report mean, median, quantiles, range, defined/undefined count and exposure, retaining all unfavorable finite ratios. A separately constructed equal-weight daily return composite is not presented as an investor-average ratio or actual shared investment account.

| strategy | defined | undefined | mean_defined_sharpe | median_defined_sharpe | minimum_defined_sharpe | maximum_defined_sharpe |
| --- | --- | --- | --- | --- | --- | --- |
| Affordability Only | 9 | 0 | -10.27201 | -3.72890 | -50.48303 | 0.51367 |
| Full IntelliVest | 9 | 0 | -21.80107 | -1.93437 | -132.19153 | 0.61913 |
| No Feedback | 9 | 0 | -21.80107 | -1.93437 | -132.19153 | 0.61913 |
| Risk Only | 9 | 0 | 0.83746 | 0.81949 | 0.68455 | 0.98983 |

## 4. Experiment A: feedback isolation

Same-state probes hold the pre-decision portfolio, budget base, price data, tier and ranking fixed, changing only active feedback versus the initial fixed No Feedback policy. Event probes evaluate every opportunity while a state persists. A separately labelled prior-state probe asks what the immediately previous policy would have proposed on the same actual later state; releases relative to that counterfactual are not Full-versus-No Feedback effects. Actual Full/No Feedback path differences remain a separate output.

| variant | policy_updates | events_with_monthly_opportunity | events_changing_a_recommendation | monthly_decisions | eligibility_changed_decisions | internally_selected_basket_changed_decisions | same_state_final_changed_decisions | path_final_changed_decisions | different_transaction_records | mean_event_response_sessions_observed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original | 55 | 28 | 0 | 432 | 141 | 0 | 0 | 0 | 0 | NA |
| stress_original | 5 | 4 | 1 | 144 | 12 | 3 | 3 | 3 | 6 | 205.00000 |
| accumulated_approved_cash_v1 | 50 | 21 | 0 | 432 | 12 | 0 | 0 | 0 | 0 | NA |

The original principal null result is retained. Internal eligibility changes are not final recommendation changes; final proposal changes are not automatically executions; executions are not proof of risk correction. The concentrated-start extension remains targeted diagnostic evidence. Any accumulated-authority decision effect belongs to that separately named assumption. No new selling/rebalancing policy was introduced.

## 5. Experiments B and D: capital authorization and cash-interest sensitivity

No corrected-accounting arm was invented because no cash/reserve accounting defect was confirmed. Instead, accumulated_approved_cash_v1 explicitly treats pre-existing unreserved brokerage savings and previous approved contributions as deployable capital and applies the unchanged tier/multiplier to this balance. Only the same reserve-protected buffer enters each month. Ranking, held-stock exclusion, whole-share sizing, trade timing and costs remain unchanged. This changes deployment authority; it is not a software correction or independently validated improvement. We report proposal excess against the original monthly reference even when cumulative approved funds cover it; that definition is not silently weakened.

Cash-interest models hold stock trades and contributions exactly fixed. Interest of 0% or 4% effective annual accrues on opening cash, including beginning-session contributions, over 252 observed sessions and is kept in an unspent subledger. Interest cannot feed back into stock selection in this experiment. It is a modeling sensitivity, not a guaranteed available cash product. Both the original linear daily benchmark and matched effective geometric benchmark are retained as separate dimensions.

Full investor-profile means, except median Sharpe:

| authorization | cash_return | benchmark | mean_annualized_return | mean_annualized_volatility | mean_defined_sharpe | median_defined_sharpe | mean_cash_allocation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| original | 0.00000 | legacy_linear | 0.02635 | 0.02107 | -21.80107 | -1.93437 | 0.85621 |
| original | 0.04000 | legacy_linear | 0.06067 | 0.02052 | 0.34051 | 0.89866 | 0.86014 |
| original | 0.04000 | effective_geometric | 0.06067 | 0.02052 | 0.80626 | 0.93641 | 0.86014 |
| accumulated_approved_cash_v1 | 0.00000 | legacy_linear | 0.12496 | 0.09771 | 0.83746 | 0.81949 | 0.30135 |
| accumulated_approved_cash_v1 | 0.04000 | effective_geometric | 0.13727 | 0.09681 | 0.97540 | 0.96048 | 0.30866 |

All-policy alternative-authorization results (zero-interest cash, original financial metric definitions):

| strategy | annualized_return | average_cash_allocation | affordability_violation_rate | surplus_utilization | mean_hhi | hhi_breach_sessions | direct_feedback_changed_decisions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Affordability Only | 0.11631 | 0.29825 | 0.27546 | 0.57181 | 0.14166 | 43.00000 | 0.00000 |
| Full IntelliVest | 0.12496 | 0.30135 | 0.23843 | 0.56354 | 0.11996 | 26.66667 | 0.00000 |
| No Feedback | 0.12496 | 0.30135 | 0.23843 | 0.56354 | 0.11996 | 26.66667 | 0.00000 |
| Risk Only | 0.12496 | 0.30135 | 0.23843 | 0.56354 | 0.11996 | 26.66667 | 0.00000 |

Authorized-decision-budget fill, original unique funding deployment and daily cash allocation have different denominators; none is called total household investment efficiency. Reserve withholding flows, reserve targets, untransferred household funds, brokerage funding and account cash are separate in CASH_PROFILE_SUMMARY.csv. No duplicate reserve was found. The alternative may spend accumulated approved savings beyond a current month's buffer, so original RQ1 monthly-cap compliance cannot be assumed for it.

## 6. Experiment C: exposure-conditioned comparisons

No strategy was forced to buy, sell or violate a rule to match exposure. We used fixed pre-specified opening-exposure bins [0,.05,.25,.50,.75,1], same profile/date pairing, and a second stricter same-bin comparison. Gross sleeve P&L adds back actual fees/slippage; net P&L includes them. Per-unit opening equity P&L is undefined with zero opening equity; entry costs on those dates are separately excluded from that diagnostic. These are normalized diagnostics, not executable equity-only strategies. Conditional drawdown resets between unmatched date gaps rather than compounding across omitted dates. Matching coverage and insufficient intervals are explicit.

| contrast | paired_sessions | coverage | gross_cvar_difference |
| --- | --- | --- | --- |
| Full IntelliVest - Affordability Only | 968.22222 | 0.97998 | 0.00259 |
| Full IntelliVest - No Feedback | 968.22222 | 0.97998 | 0.00000 |
| Full IntelliVest - Risk Only | 968.22222 | 0.97998 | 0.00505 |

The substantially lower Risk Only HHI is not caused by including cash as a sector or assigning empty portfolios zero HHI: neither occurred. Larger executable budgets and broader acquired holdings under the same no-repeat rule can change invested-sector breadth. Exposure normalization cannot remove stock-selection/path differences and may introduce selection bias. It supports descriptive risk/return trade-off analysis, not causal superiority.

## 7. Effects on research conclusions

- **RQ1 remains supported for the original controlled policy:** the household monthly gate prevented original proposed overspend. New accumulated authority has a different authorization assumption; monthly-reference violations remain reported and cannot be relabelled as original compliance.
- **RQ2 needs qualification:** original concentration improvements remain; denominator correction improves comparability but does not create a downside-risk win. Equity-only concentration and exposure-conditioned losses must be reported alongside account losses and cash.
- **RQ3 remains unsupported in the original principal design:** recording 55 policy updates did not establish changed recommendations or risk correction. The pipeline correctly propagated meaningful rules, but existing exposure ordering, other exclusions, whole-share sizing and timing often made them nonbinding. Targeted or alternative results remain separately labelled.
- **RQ4 remains a trade-off conclusion:** cash treatment, capital authority and invested exposure materially influence risk-adjusted performance. Mean investor Sharpe alone is not a sufficient summary. No policy is declared superior on these diagnostics.

## 8. Statistical uncertainty

Paired circular calendar-block bootstrap intervals use 20-session blocks, 2,000 draws and seed 20261024. Shared dates are resampled together. Exposure matching retains unobserved slots as NaN in the common calendar; intervals with fewer than 60 matched sessions are explicitly unavailable. This avoids inventing independent observations or reliable inference from sparse matches. Representative medium/moderate contrasts below are differences in annualized arithmetic mean daily returns, not CAGR differences:

| experiment | valid_paired_sessions | mean_annualized_arithmetic_return_difference | ci95_low | ci95_high | interval_status |
| --- | --- | --- | --- | --- | --- |
| cash_interest | 988 | 0.03572 | 0.03516 | 0.03624 | conditional_descriptive_block_interval |
| capital_authorization | 988 | 0.10425 | 0.01369 | 0.19850 | conditional_descriptive_block_interval |

Profiles are synthetic design choices and market windows overlap. These intervals condition on the observed restricted universe and do not establish population efficacy, a forecast or independent out-of-sample performance. All results, including unfavorable contrasts, remain in UNCERTAINTY.csv and EXPOSURE_MATCHED_COMPARISONS.csv. No p-values were fabricated.

## 9. Remaining limitations and future work

Survivorship and current-sector bias, missing delisted names, incomplete point-in-time eligibility and partial corporate-action certification remain unchanged. No new market data was substituted. Dividend payment-date approximation, no cash-product frictions, simplified fees/taxes and buy-only execution remain assumptions. The chronological primary sample was not used to tune a new policy; accumulated authority is a transparent sensitivity, not a claim of validated improvement. A future operational change should explicitly separate monthly savings capacity, previously approved brokerage capital, reserve-stock targets and contribution flows, then evaluate a prespecified policy on held-out dates. Candidate affordability before limited-slot selection and held-stock re-entry require separate versioned studies rather than silent changes to Full IntelliVest. Corrective selling would be a new investment policy, not a repair to the current restriction system.

## 10. Figures and reproducibility

Six real-data figures are in figures/ as 300-dpi PNG and SVG, with CAPTIONS.md. DIAGNOSTIC_CONFIG.json records parameters, source hashes and package versions; source_snapshot/ contains executed diagnostics. BASELINE_REPRODUCTION.json and FOCUSED_CHECKS.json record numerical checks. PRESERVATION_CHECK.json verifies prior results, original conference draft, dataset and inspected application sources unchanged. No database write path or live account was used. No commit was created; GIT_STATUS.txt records the pre-existing dirty tree and new research files.

Methodology references: [Sharpe (1994)](https://web.stanford.edu/~wfsharpe/art/sr/sr.htm), [GIPS cash-flow-aware return methodology](https://www.gipsstandards.org/standards/gips-standards-for-firms/gips-standards-handbook-for-firms/). The use of these definitions does not claim standards compliance or support investment superiority.

## Completion verification

27 focused checks and 26 independent checks passed. All 80 protected input files remained unchanged. See VALIDATION_SUMMARY.md for scope, source snapshots, exact reproduction and legacy/corrected metric field conventions.
