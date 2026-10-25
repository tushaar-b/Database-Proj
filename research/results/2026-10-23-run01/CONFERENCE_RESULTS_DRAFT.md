# IntelliVest comparative historical study: conference results draft

Evidence classification: **2. Exploratory historical results available with important limitations.** This draft reports executed simulations; it does not establish market-wide superiority.

## 1. Experimental Setup

We executed 144 principal policy/profile/window replays, nine momentum ablations and 24 transaction-cost sensitivity replays. The primary comparison covered complete calendar years 2022–2025, selected before strategy simulation. First-session monthly decisions used completed historical information and next-session closing-price execution. Portfolio valuation and monitoring were daily. Purchases incurred 10 bp commission and 5 bp adverse slippage. No leverage, shorting or fractional purchases were allowed. Each account started with INR 100,000 in cash and no holdings. The replay code operated on isolated CSV data and in-memory portfolios; server-enforced read-only database access was confined to the market audit. Mathematical and accounting checks were executed; unrelated application and browser tests were not run.

## 2. Historical Dataset

The legacy database contained 50 securities and 61,850 observations from 2021-10-19 through 2026-10-19. Its schema lacked source and ingestion fields. Fresh Yahoo Finance/yfinance acquisition produced 49 securities and 70,315 observations; TATAMOTORS was not silently remapped. NSE annual spot checks corroborated nominal prices and dates only on sampled sessions. After identity/corporate-action exclusions, the admitted dataset contained 41 securities and 58,835 observations from 2021-01-01 through 2026-10-22. Exact exclusions, disagreement rows, raw files and hashes appear in the audit. We did not treat plausible legacy prices as proof of authenticity. Historical indicator returns used adjusted closes consistently. Execution used reconstructed nominal prices and explicit split/dividend accounting. Vendor adjustments are revised historical data rather than archived point-in-time vintages. This was a restricted surviving-universe study; historical index membership and a complete delisting universe were unavailable.

## 3. Investor Scenarios

Nine synthetic scenarios crossed low, medium and high surplus with conservative, moderate and aggressive tiers. These profiles did not come from investor surveys. Monthly income/mandatory expenses/reserve were INR 45,000/30,000/10,000; 100,000/50,000/30,000; and 250,000/90,000/60,000, yielding buffers of INR 5,000, 20,000 and 100,000. All policies received identical monthly transfers. The implemented application subtracts reserve from each monthly surplus and excludes discretionary expenses from the buffer calculation; the replay preserved these semantics. Starting brokerage savings were distinct from the protected household reserve.

## 4. Baseline Configurations

Affordability Only retained household capacity, the common tier-specific stock ranking and whole-share sizing, but removed portfolio exposure ordering and adaptive restrictions. Risk Only retained portfolio exposure ordering and executable brokerage-cash limits, but sized from brokerage cash rather than household capacity. No Feedback retained affordability and ordinary exposure-aware selection with an initial fixed unrestricted policy. Full IntelliVest additionally applied the implemented dominant-sector blocks and .5/.25 capacity multipliers after breaches. All configurations excluded held stocks and used at most three distinct sectors per batch. The application has no independent hard pretrade HHI eligibility gate; this absence limits the interpretation of No Feedback as a risk-constrained baseline. No extra gate was invented. Detailed factor definitions are in SPECIFICATION.md.

## 5. Evaluation Metrics

Returns were daily time-weighted returns with external transfers removed. Risk was evaluated with sample volatility, linearly interpolated historical VaR95 and inclusive-tail CVaR95, equity-only sector HHI and time-weighted maximum drawdown. The implemented breach parametric VaR was 1.645 times trailing 30-session volatility; historical estimates used 252 aligned returns. Sharpe used a 4% annual risk-free rate and 252 sessions. Proposed household overspend was separated from actual brokerage execution. Turnover was purchase notional divided by average equity, without annualization. Reported mean outcomes gave equal weight to synthetic profiles. Undefined metrics were NA. Formulas, units, censoring and aggregation rules are specified in SPECIFICATION.md. Realized losses were kept separate from in-sample risk estimates.

### Table 1. Principal comparison

Equal-profile means for 2022–2025. Rates and returns are fractions, money is INR, durations are trading sessions. Feedback response time is conditional on an observed directly modified recommendation; missing responses are censored and cannot be interpreted as immediate responses.

| Metric | Affordability Only | Risk Only | No Feedback | Full IntelliVest |
| --- | --- | --- | --- | --- |
| affordability_violation_rate | 0.0000 | 0.2569 | 0.0000 | 0.0000 |
| mean_overspend | 0.0000 | 1712.9835 | 0.0000 | 0.0000 |
| max_overspend | 0.0000 | 28760.8382 | 0.0000 | 0.0000 |
| surplus_utilization | 0.0798 | 0.5806 | 0.0829 | 0.0829 |
| no_purchase_frequency | 0.7130 | 0.5787 | 0.7106 | 0.7106 |
| mean_hhi | 0.3861 | 0.1240 | 0.3505 | 0.3505 |
| hhi_breach_sessions | 423.1111 | 26.6667 | 326.6667 | 326.6667 |
| cvar95 | 0.0028 | 0.0146 | 0.0032 | 0.0032 |
| maximum_drawdown | 0.0289 | 0.1409 | 0.0297 | 0.0297 |
| annualized_volatility | 0.0198 | 0.1006 | 0.0219 | 0.0219 |
| cumulative_return | 0.1072 | 0.6441 | 0.1266 | 0.1266 |
| annualized_return | 0.0253 | 0.1348 | 0.0294 | 0.0294 |
| sharpe | -10.2460 | 0.9072 | -21.7475 | -21.7475 |
| turnover | 0.1263 | 0.6184 | 0.1294 | 0.1294 |
| average_idle_cash | 917993.0536 | 554556.7577 | 915506.4428 | 915506.4428 |
| average_cash_allocation | 0.8575 | 0.2862 | 0.8516 | 0.8516 |
| transaction_fees | 261.8909 | 710.9047 | 265.3940 | 265.3940 |
| slippage_cost | 130.8800 | 355.2747 | 132.6307 | 132.6307 |
| policy_adjustments | 0.0000 | 0.0000 | 0.0000 | 6.1111 |
| direct_feedback_changed_decisions | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| feedback_response_sessions | NA | NA | NA | NA |

## 6. Results for RQ1: Affordability

Full minus Risk Only mean proposed-violation rate was -0.256944. Full violation rate was 0.000000, versus 0.256944 for Risk Only. Mean overspend per monthly decision was INR 0.00 and INR 1712.98, respectively. The maximum Risk Only proposal excess was INR 63977.35. This comparison assessed realistic household capacity even when accumulated brokerage savings allowed an order to execute. H1 is supported within these controlled scenarios. This is partly a mechanical compliance result of the gate, not evidence of predictive stock-selection skill. Figure 4 reports frequency and magnitude.

## 7. Results for RQ2: Portfolio Risk Control

Full minus Affordability Only mean daily CVaR95 difference was 0.000356, mean HHI difference was -0.035602, and maximum-drawdown difference was 0.000748. Mean HHI-breach-session difference was -96.44. H2 must be evaluated component by component; these signs do not justify a blanket risk or return superiority claim. Exposure ordering and feedback jointly differ in this contrast. Figures 2 and 3 show concentration and drawdown trajectories.

## 8. Results for RQ3: Closed-Loop Feedback

Full produced 55 effective policy adjustments and 0 monthly decisions different from its same-state fixed-policy counterfactual across the nine primary profiles. Full and No Feedback differed on 0 of 432 paired monthly decisions, including accumulated path effects. Mean HHI-breach-session difference was 0.00. Among observed breach episodes, 0 received a directly modified proposal and 9 had no observed such response. Mean conditional response latency was nan sessions; it omits censored cases and is not an unconditional improvement estimate. Policy changes, modified proposals and actual holdings correction were measured separately. H3 has no demonstrated decision effect; persistence outcomes did not decrease on average in these profiles. The buy-only mechanism did not execute corrective sales. Figure 5 shows the distinct events.

## 9. Results for RQ4: Investment Performance Trade-offs

Table 1 reports all four policies without removing unfavorable outcomes. Figure 1 distinguishes account equity from supplied capital; Figure 6 compares time-weighted annualized return and realized volatility. Full annualized return averaged 0.029399, versus 0.134849 for Risk Only, 0.025268 for Affordability Only and 0.029399 for No Feedback. Differences in cash exposure, stock eligibility exhaustion and invested capital accompany these outcomes. Lower volatility is not automatically better investment performance. Cost sensitivity and the realized return/cost/cash columns are retained in the machine-readable outputs.

## 10. RQ5 and Momentum Robustness

All nine cross-factor profiles were replayed in fixed 2022–2023, 2024–2025 and 2026 YTD windows in addition to the primary window. `robustness_subgroups.csv` preserves every profile/window/policy cell; overlapping windows do not provide independent replications. The actual implemented momentum ranking was ablated by zeroing only its tier penalty coefficients. `momentum_paired_differences.csv` reports paired returns, drawdown, volatility, CVaR, turnover, HHI and strong-negative-momentum selection frequency. A descriptive mean with-minus-without annualized-return difference was 0.000826; it is not a parameter-tuned efficacy result.

## 11. Statistical Interpretation

We calculated matched profile/window differences and paired circular moving-block bootstrap intervals for annualized arithmetic daily-mean-return differences (20-session blocks, 2,000 draws, seed 20261023). Shared dates were resampled jointly across policies. These conditional time-series intervals are not intervals for a population of investors or a universe of markets. Scenarios were not treated as random samples and daily observations were not subjected to independent-observation t-tests. No inferential p-values or claims of statistical superiority were produced. `primary_uncertainty.csv` and `paired_comparisons.csv` retain each conditional interval and descriptive paired difference.

### Table 2. Mean paired differences (Full minus baseline)

| contrast | affordability_violation_rate_difference | mean_hhi_difference | hhi_breach_sessions_difference | cvar95_difference | maximum_drawdown_difference | annualized_return_difference |
| --- | --- | --- | --- | --- | --- | --- |
| Full IntelliVest - Affordability Only | 0.0000 | -0.0356 | -96.4444 | 0.0004 | 0.0007 | 0.0041 |
| Full IntelliVest - No Feedback | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Full IntelliVest - Risk Only | -0.2569 | 0.2264 | 300.0000 | -0.0114 | -0.1112 | -0.1055 |

## 12. Threats to Validity

Current surviving securities and current sector labels induce selection bias; delisted names and historical membership are absent. Exchange price corroboration is sparse and does not independently certify every dividend-adjusted observation. Some complex corporate actions were excluded rather than approximated. Whole-share eligibility, absence of repeat purchases of held stocks and a maximum of three sectors per batch can exhaust eligible candidates and create cash-heavy portfolios. Initial purchase concentration can itself exceed HHI .25. High-surplus and low-surplus outcomes are conditional on the same INR 100,000 starting account. The initial empty portfolio makes the fixed policy in No Feedback unrestricted; no absent HHI gate was invented.

## 13. Limitations

Dividend availability was approximated on ex-date rather than unknown payment dates. Split reconstruction uses the downloaded horizon and revised vendor prices; there were no contemporaneous data vintages. Cash earned no interest. Costs were proportional assumptions, not a complete Indian tax/stamp-duty schedule. No investor acceptance behavior, market impact, forced rebalancing or predictive calibration was modeled. Feedback monitoring was scheduled daily, whereas the application evaluates on requests. Results do not prove that VaR estimates forecast losses accurately. Ending HHI episodes were right-censored. Averaging conditional response times omits nonresponses; their counts remain explicit. Conditional bootstrap intervals and overlapping calendar windows cannot establish general effectiveness.

## 14. Conclusion Supported by Results

The executed pipeline distinguished affordability compliance, portfolio concentration, realized investment performance and feedback decision changes. H1 was supported for the defined scenarios. Feedback did not demonstrate changed proposals, while persistent portfolio-breach outcomes required separate evaluation. H2 and H3 were not collapsed into an unconditional superiority statement. H4 was treated as a trade-off question, with all measured policy outcomes retained. The evidence supports a reproducible exploratory restricted-universe comparison, not a publication-ready market-wide claim of superior advisory performance. Further validation requires complete action-aware security histories, broader point-in-time eligibility and independent out-of-sample market periods.

## Scenario outcomes

| scenario | strategy | annualized_return | cvar95 | mean_hhi | hhi_breach_sessions | affordability_violation_rate | surplus_utilization |
| --- | --- | --- | --- | --- | --- | --- | --- |
| low_conservative | Affordability Only | 0.0006 | 0.0001 | 1.0000 | 907 | 0.0000 | 0.0024 |
| low_conservative | Risk Only | 0.1440 | 0.0141 | 0.1205 | 40 | 0.4375 | 0.9131 |
| low_conservative | No Feedback | 0.0002 | 0.0000 | 1.0000 | 907 | 0.0000 | 0.0010 |
| low_conservative | Full IntelliVest | 0.0002 | 0.0000 | 1.0000 | 907 | 0.0000 | 0.0010 |
| low_moderate | Affordability Only | 0.0016 | 0.0003 | 1.0000 | 907 | 0.0000 | 0.0058 |
| low_moderate | Risk Only | 0.1629 | 0.0172 | 0.1184 | 40 | 0.3958 | 1.0413 |
| low_moderate | No Feedback | 0.0006 | 0.0002 | 1.0000 | 907 | 0.0000 | 0.0030 |
| low_moderate | Full IntelliVest | 0.0006 | 0.0002 | 1.0000 | 907 | 0.0000 | 0.0030 |
| low_aggressive | Affordability Only | 0.0102 | 0.0010 | 0.2841 | 391 | 0.0000 | 0.0616 |
| low_aggressive | Risk Only | 0.1572 | 0.0169 | 0.1297 | 20 | 0.3333 | 1.0151 |
| low_aggressive | No Feedback | 0.0151 | 0.0016 | 0.1947 | 164 | 0.0000 | 0.0682 |
| low_aggressive | Full IntelliVest | 0.0151 | 0.0016 | 0.1947 | 164 | 0.0000 | 0.0682 |
| medium_conservative | Affordability Only | 0.0026 | 0.0003 | 0.3515 | 947 | 0.0000 | 0.0135 |
| medium_conservative | Risk Only | 0.1289 | 0.0125 | 0.1374 | 40 | 0.1667 | 0.5252 |
| medium_conservative | No Feedback | 0.0013 | 0.0002 | 0.3176 | 782 | 0.0000 | 0.0075 |
| medium_conservative | Full IntelliVest | 0.0013 | 0.0002 | 0.3176 | 782 | 0.0000 | 0.0075 |
| medium_moderate | Affordability Only | 0.0085 | 0.0012 | 0.2590 | 474 | 0.0000 | 0.0500 |
| medium_moderate | Risk Only | 0.1296 | 0.0145 | 0.1162 | 20 | 0.2500 | 0.3977 |
| medium_moderate | No Feedback | 0.0136 | 0.0020 | 0.1280 | 40 | 0.0000 | 0.0609 |
| medium_moderate | Full IntelliVest | 0.0136 | 0.0020 | 0.1280 | 40 | 0.0000 | 0.0609 |
| medium_aggressive | Affordability Only | 0.0429 | 0.0041 | 0.1529 | 61 | 0.0000 | 0.1365 |
| medium_aggressive | Risk Only | 0.1331 | 0.0157 | 0.1183 | 20 | 0.2083 | 0.4142 |
| medium_aggressive | No Feedback | 0.0493 | 0.0051 | 0.1172 | 40 | 0.0000 | 0.1564 |
| medium_aggressive | Full IntelliVest | 0.0493 | 0.0051 | 0.1172 | 40 | 0.0000 | 0.1564 |
| high_conservative | Affordability Only | 0.0226 | 0.0025 | 0.1577 | 61 | 0.0000 | 0.0751 |
| high_conservative | Risk Only | 0.1040 | 0.0109 | 0.1264 | 20 | 0.0625 | 0.2716 |
| high_conservative | No Feedback | 0.0234 | 0.0026 | 0.1369 | 40 | 0.0000 | 0.0747 |
| high_conservative | Full IntelliVest | 0.0234 | 0.0026 | 0.1369 | 40 | 0.0000 | 0.0747 |
| high_moderate | Affordability Only | 0.0608 | 0.0062 | 0.1400 | 40 | 0.0000 | 0.1499 |
| high_moderate | Risk Only | 0.1258 | 0.0140 | 0.1261 | 20 | 0.2292 | 0.3160 |
| high_moderate | No Feedback | 0.0638 | 0.0065 | 0.1351 | 40 | 0.0000 | 0.1499 |
| high_moderate | Full IntelliVest | 0.0638 | 0.0065 | 0.1351 | 40 | 0.0000 | 0.1499 |
| high_aggressive | Affordability Only | 0.0776 | 0.0097 | 0.1296 | 20 | 0.0000 | 0.2230 |
| high_aggressive | Risk Only | 0.1281 | 0.0156 | 0.1235 | 20 | 0.2292 | 0.3308 |
| high_aggressive | No Feedback | 0.0974 | 0.0104 | 0.1249 | 20 | 0.0000 | 0.2250 |
| high_aggressive | Full IntelliVest | 0.0974 | 0.0104 | 0.1249 | 20 | 0.0000 | 0.2250 |

## Figures

**figure_1_portfolio_value** — Nominal account equity includes contributions. Dotted lines show initial cash plus identical supplied capital; cash-flow-adjusted returns are reported separately.

**figure_2_sector_hhi** — HHI excludes cash; undefined before the first purchase. The dashed line is the fixed 0.25 threshold. Policy changes do not imply holdings have corrected.

**figure_3_drawdown** — Daily time-weighted wealth, including the initial wealth peak. Losses are negative; external transfers are removed from return calculations.

**figure_4_affordability** — Equal-profile means in the primary window. Overspend is proposed notional beyond monthly household capacity, measured separately from brokerage execution feasibility.

**figure_5_feedback_response** — Markers distinguish breached observations, effective policy changes and proposals changed against the same-state fixed-policy counterfactual. Suppression of future purchases is not a corrective sale.

**figure_6_risk_return** — Each point is a profile-policy replay on the same market window. Profiles are deterministic design scenarios, not independent sampled investors; no efficacy frontier is inferred.
