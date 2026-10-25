# IntelliVest comparative study: final research report

Canonical run: `2026-10-23-run03` (UTC identifier; local completion 24 October 2026).

**Evidence classification: 2 — Exploratory historical results available with important limitations.** The study does not establish that Full IntelliVest outperforms simpler policies. It supports household-affordability compliance, shows some concentration improvements, and exposes an important null result for the current feedback mechanism.

## A. Dataset quality

Fresh Yahoo Finance data were acquired through yfinance with `auto_adjust=False`, `actions=True`, no repair and no synthetic fallback. The original 50-security/61,850-row PostgreSQL history was inspected through server-enforced read-only transactions and preserved. Of 60,613 overlapping raw closes across 49 resolved symbols, all matched the provider within recorded tolerances; adjusted closes differed for TECHM. No legacy row matched the synthetic generator's exact rounded 0.98 factor, but absence of that fingerprint does not establish provenance.

Fresh acquisition produced 70,315 observations for 49 securities, 2021-01-01 through 2026-10-22. Six independently downloaded dated NSE exchange files yielded 293 comparisons, 271 matches before exclusions. Every retained sampled comparison matched: 240 pairs, six sessions for each admitted security. The final isolated dataset contains **40 securities and 57,400 observations**, on 1,435 common observed sessions. No observations were interpolated or removed to align the admitted calendar.

Excluded security-master entries: TATAMOTORS, ITC, RELIANCE, BHARTIARTL, HDFCBANK, SHRIRAMFIN, BAJAJFINSV, BAJFINANCE, GRASIM and TRENT. Reasons include unreconciled merger/demerger/rights identities and nominal-price reconstruction disagreements. Exact reasons and discrepancy rows are retained in the data directory.

Adjusted closes were used consistently for historical ranking and risk estimation. Execution/valuation used nominal prices reconstructed from provider split-normalized prices and reported split events. Splits changed quantities, fractional entitlements received cash-in-lieu, and dividends were credited on ex-date. Adjustment-factor changes were checked against reported actions. Provider first-trade metadata preceded the admitted observations. These checks do not independently certify every adjustment or establish a complete point-in-time index/listing/delisting universe. Current surviving securities, current sector labels and revised vendor histories remain important limitations.

See [data audit](DATA_AUDIT_REPORT.md), [audit interpretation](DATA_QUALITY_INTERPRETATION.md), and `research/data/2026-10-23/admission.json`.

## B. Experimental methodology

Nine explicitly synthetic profiles crossed monthly buffers of INR 5,000/20,000/100,000 with conservative/moderate/aggressive tiers. Income, mandatory expenses, discretionary expenses and reserve assumptions are recorded in [configuration](config.json). Every principal account started with INR 100,000 cash, zero holdings and identical first-session monthly buffer transfers. Reserve subtraction and discretionary-expense treatment follow the implemented financial calculation; these are not survey-derived households.

The four principal policies were Affordability Only, Risk Only, No Feedback and Full IntelliVest. They shared actual historical/momentum scoring, minimum 120 and maximum 252 ranking returns, inverse-volatility sizing, existing-stock exclusion, at most three distinct sectors, whole-share rules and common accounting. Affordability Only disabled portfolio-exposure ordering. Risk Only replaced the household gate with finite brokerage-cash sizing. No Feedback retained ordinary exposure ordering and froze the initial policy. Full alone updated the existing multiplier/sector blocks after breaches. There is no independent hard pretrade HHI eligibility gate in the actual application; none was invented for the baseline.

Monthly decisions used completed first-session closes and next-session close execution. Daily valuation/risk monitoring used only information through that observation date. Baseline fee/slippage were 10/5 bp. Executable costs respected saved batch budget, cash and enabled household capacity. The actual live acceptance endpoint records intent only; automatic investor follow-through and the delayed-fill ledger are explicit research assumptions. Live intraday freshness/hash rejection was not claimed to be reproduced.

The main window was 2022–2025, selected before financial replay. Robustness used fixed 2022–2023, 2024–2025 and 2026 YTD windows. The final study executed **144 principal replays + 9 momentum ablations + 24 cost sensitivities + 12 secondary mechanism stresses = 189 simulations**. Statistical analysis used paired differences and a circular paired moving-block bootstrap: 20 sessions, 2,000 draws, seed 20261023. Overlapping periods and synthetic profiles were not treated as independent population samples.

See [full mathematical specification](SPECIFICATION.md). The frozen source, effective settings, package versions, dataset hashes, raw data and exact configuration are retained.

## C–D. Research findings and principal comparison

Primary 2022–2025 equal-profile descriptive means; rates below are percentages, HHI is unitless, turnover is a nonannualized ratio. Monetary values are INR. Maximum overspend is the global maximum, not an average of maxima. CVaR is realized one-day historical CVaR95; drawdown uses contribution-adjusted wealth. Mean Sharpe excludes undefined cases.

| Metric | Affordability Only | Risk Only | No Feedback | Full IntelliVest |
|---|---:|---:|---:|---:|
| Proposed affordability violation rate | 0.00% | 23.84% | 0.00% | 0.00% |
| Mean overspend per decision (INR) | 0 | 1,698.06 | 0 | 0 |
| Maximum overspend (INR) | 0 | 63,977.35 | 0 | 0 |
| Surplus utilization | 7.96% | 56.35% | 7.96% | 7.96% |
| No-purchase frequency | 71.30% | 60.19% | 71.99% | 71.99% |
| Mean sector HHI | 0.3860 | 0.1200 | 0.3478 | 0.3478 |
| HHI-breach sessions | 423.11 | 26.67 | 326.67 | 326.67 |
| Daily CVaR95 | 0.2819% | 1.4288% | 0.3100% | 0.3100% |
| Maximum drawdown | 2.8704% | 13.9173% | 2.8815% | 2.8815% |
| Annualized volatility | 1.9664% | 9.7706% | 2.1068% | 2.1068% |
| Cumulative time-weighted return | 10.2649% | 58.9724% | 11.1887% | 11.1887% |
| Annualized time-weighted return | 2.4290% | 12.4963% | 2.6352% | 2.6352% |
| Sharpe ratio | -10.2720 | 0.8375 | -21.8011 | -21.8011 |
| Turnover | 0.1263 | 0.6021 | 0.1251 | 0.1251 |
| Average idle cash (INR) | 918,351.57 | 582,321.56 | 924,915.89 | 924,915.89 |
| Average cash allocation | 85.82% | 30.14% | 85.62% | 85.62% |
| Transaction fees (INR) | 261.22 | 668.56 | 250.51 | 250.51 |
| Slippage cost (INR) | 130.54 | 334.11 | 125.19 | 125.19 |
| Effective policy adjustments | 0 | 0 | 0 | 6.11 |
| Direct feedback-modified decisions | 0 | 0 | 0 | 0 |
| Response time to a modified recommendation | NA | NA | NA | NA |

**RQ1 / H1:** Supported within these controlled scenarios. Full eliminated proposed household overspend relative to Risk Only, which could spend pre-existing brokerage savings beyond the current household buffer. This is a compliance result, not predictive investment skill.

**RQ2 / H2:** Partial support for concentration compliance; no support for lower primary mean CVaR or drawdown. Full lowered mean HHI by 0.0381 and mean HHI-breach duration by 96.44 sessions versus Affordability Only, but realized CVaR, drawdown and volatility were slightly higher. Risk control cannot be described as uniformly improving downside outcomes.

**RQ3 / H3:** Unsupported in the principal empty-account scenarios. Full generated 55 effective policy adjustments across nine primary profiles but **zero changed recommendations versus No Feedback**, and the two policies had identical primary trades, values and performance. Conditional response latency was unobserved, not zero. A separately labelled concentrated-start stress produced three changed proposals in the high-surplus/aggressive profile, demonstrating that a policy change can affect a decision; it did **not** reduce HHI-breach duration versus No Feedback. That extension was added after the initial null result and is a mechanism probe, not confirmatory evidence replacing it.

**RQ4:** Clear trade-offs rather than superiority. Full had lower realized risk than Risk Only but substantially lower return, more idle cash and much lower capital utilization. Against Affordability Only, concentration improved while downside metrics did not. The application excludes held securities and applies whole-share affordability after selecting a small candidate set; these actual rules can exhaust eligible purchases or repeatedly produce unaffordable selected candidates. Nearly cash-only profiles account for very negative Sharpe ratios: cash earned zero while the benchmark was 4%, and realized volatility was tiny. No unfavorable result was removed.

**RQ5:** Outcomes varied materially by profile and window. Full mean annualized return was 3.35% in 2022–2023, 1.76% in 2024–2025 and -1.17% in 2026 YTD. Primary Full outcomes ranged from approximately 0.016% annual return and HHI 1.0 in low/conservative to 8.26% return and HHI 0.1138 in high/aggressive. These are deterministic conditional scenarios, not independently sampled investors or markets.

**Momentum:** The actual momentum coefficient ablation produced a mean with-minus-without annualized-return difference of +0.1209 percentage points, drawdown difference of -0.0824 percentage points and strong-negative-momentum selection-rate difference of -0.5605 percentage points. CVaR and volatility effects were approximately neutral and varied by profile. This secondary descriptive result does not establish predictive efficacy.

All individual outcomes, costs, scenarios and uncertainty intervals are retained, including negative and neutral findings. See [complete comparison](MAIN_COMPARISON.md), [scenario results](investor_scenario_comparisons.csv), [paired comparisons](paired_comparisons.csv), [momentum differences](momentum_paired_differences.csv), [cost sensitivity](cost_sensitivity.csv) and [feedback stress](feedback_stress.csv).

## E. Figures and raw outputs

Publication figures have PNG and SVG versions, with captions in [CAPTIONS.md](figures/CAPTIONS.md):

1. [Portfolio values and identical supplied capital](figures/figure_1_portfolio_value.png).
2. [Equity-sector HHI](figures/figure_2_sector_hhi.png).
3. [Contribution-adjusted drawdowns](figures/figure_3_drawdown.png).
4. [Affordability violation frequency and magnitude](figures/figure_4_affordability.png).
5. [Primary feedback observations and policy changes](figures/figure_5_feedback_response.png).
6. [Risk and return across profiles](figures/figure_6_risk_return.png).
7. [Supplementary concentrated-start mechanism stress](figures/figure_7_feedback_stress.png).

Detailed CSVs include `trades.csv`, `order_events.csv`, `positions.csv`, `valuations.csv`, `decisions.csv`, `policy_changes.csv`, `breach_episodes.csv`, `strategy_summaries.csv` and `robustness_subgroups.csv`. They contain market data and synthetic state, not real-user accounts or financial records.

## F. Statistical evidence and verification

For the medium/moderate primary profile, the annualized arithmetic daily-mean-return difference Full minus Risk Only was -10.42 percentage points, with conditional block-bootstrap 95% interval [-19.45, -1.35] points. Full minus Affordability Only was +0.51 points, interval [-0.30, +1.28]. Full minus No Feedback was exactly zero, interval [0, 0]. These are conditional paired time-series intervals, not population efficacy estimates; no p-values or general statistical-superiority claims were made.

Twenty mathematical/accounting/temporal checks passed. Every principal account reconciled external contributions, daily returns and gains. All buys had delayed dates, integer shares and no duplicate executions. Saved budget caps held including costs. Five independent representative replays reproduced all summary metrics and numeric daily ledger columns within 1e-10 relative tolerance. Frozen source and dataset hashes matched. See [verification](reproducibility_verification.json) and [execution checks](execution_validation.json).

## G–H. Limitations and conference readiness

This remains a restricted surviving-universe study with sparse exchange corroboration, incomplete corporate-action certification and no historical data vintages. Current sectors, excluded complex actions, absent delisted stocks and hypothetical household assumptions limit external validity. Dividends were available on ex-date rather than payment date; cash earned no interest; fees/slippage were simplified and do not model every Indian tax or market-impact component. There were no corrective sales or investor-acceptance behavior. Feedback ran daily rather than on application requests. Unresolved episodes were censored. Overlapping windows and profile permutations do not supply independent market replications.

**Classification 2 is appropriate.** The implementation and exploratory evidence can inform the paper, but they do not support a claim that the complete framework achieves superior financial or advisory performance. H1 has controlled compliance support; H2 is mixed; central H3 stability/decision superiority is unsupported. The separate [conference results draft](CONFERENCE_RESULTS_DRAFT.md) retains these conclusions. Original paper PDFs were not overwritten.

## I. Files and Git

Research code and documentation were created only under `research/`: data audit/admission, scenarios, strategy adapter, historical replay, risk metrics, experiment runner, statistical analysis, result generation, consistency checks and independent verification. No existing application source, UI, authentication, ownership controls or user transaction tables were changed by this task. No database reset, research user, simulated live portfolio or Supabase connection was created.

Frozen data: `research/data/2026-10-23/`. Canonical outputs: `research/results/2026-10-23-run03/`. Earlier runs were retained and marked superseded; their changes are explained in [execution history](../RUN_HISTORY.md). Postprocessing source is archived separately from the original executed simulation snapshot, with no change to simulation CSVs.

Git reports `?? research/` in addition to the project's pre-existing dirty state. No commit was created. The unchanged pre-existing HEAD is `ad21a5240171cac28d2f6caafca3182cd08507ba`. See [working-tree status](GIT_STATUS.txt), [created files](CREATED_FILES.txt), [configuration](config.json), source snapshots and output hashes for provenance.
