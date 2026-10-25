Canonical executed run: `2026-10-23-run03`.

# IntelliVest comparative historical study: conference results draft

Evidence classification: **2. Exploratory historical results available with important limitations.** This draft reports executed simulations; it does not establish market-wide superiority.

## 1. Experimental Setup

We executed 144 principal policy/profile/window replays, nine momentum ablations, 24 transaction-cost sensitivity replays and 12 separately labelled concentrated-start mechanism-stress replays. The primary comparison covered complete calendar years 2022–2025, selected before strategy simulation. First-session monthly decisions used completed historical information and next-session closing-price execution. Portfolio valuation and monitoring were daily. Purchases incurred 10 bp commission and 5 bp adverse slippage. No leverage, shorting or fractional purchases were allowed. The live acceptance endpoint records intent only; automatic investor follow-through was a research assumption, not existing live trade execution. Simulated fills including costs respected the saved batch budget; live intraday freshness/evidence-hash rejection was replaced by the documented delayed-fill convention. Each principal account started with INR 100,000 in cash and no holdings. The replay code operated on isolated CSV data and in-memory portfolios; server-enforced read-only database access was confined to the market audit. Mathematical and accounting checks were executed; unrelated application and browser tests were not run.

## 2. Historical Dataset

The legacy database contained 50 securities and 61,850 observations from 2021-10-19 through 2026-10-19. Its schema lacked source and ingestion fields. Fresh Yahoo Finance/yfinance acquisition produced 49 securities and 70,315 observations; TATAMOTORS was not silently remapped. NSE annual spot checks corroborated nominal prices and dates only on sampled sessions. After identity/corporate-action exclusions, the admitted dataset contained 40 securities and 57,400 observations from 2021-01-01 through 2026-10-22. Exact exclusions, disagreement rows, raw files and hashes appear in the audit. We did not treat plausible legacy prices as proof of authenticity. Historical indicator returns used adjusted closes consistently. Execution used reconstructed nominal prices and explicit split/dividend accounting. Vendor adjustments are revised historical data rather than archived point-in-time vintages. This was a restricted surviving-universe study; historical index membership and a complete delisting universe were unavailable.

## 3. Investor Scenarios

Nine synthetic scenarios crossed low, medium and high surplus with conservative, moderate and aggressive tiers. These profiles did not come from investor surveys. Monthly income/mandatory expenses/reserve were INR 45,000/30,000/10,000; 100,000/50,000/30,000; and 250,000/90,000/60,000, yielding buffers of INR 5,000, 20,000 and 100,000. All policies received identical monthly transfers. The implemented application subtracts reserve from each monthly surplus and excludes discretionary expenses from the buffer calculation; the replay preserved these semantics. Starting brokerage savings were distinct from the protected household reserve.

## 4. Baseline Configurations

Affordability Only retained household capacity, the common tier-specific stock ranking and whole-share sizing, but removed portfolio exposure ordering and adaptive restrictions. Risk Only retained portfolio exposure ordering and executable brokerage-cash limits, but sized from brokerage cash rather than household capacity. No Feedback retained affordability and ordinary exposure-aware selection with an initial fixed unrestricted policy. Full IntelliVest additionally applied the implemented dominant-sector blocks and .5/.25 capacity multipliers after breaches. All configurations excluded held stocks and used at most three distinct sectors per batch. The application has no independent hard pretrade HHI eligibility gate; this absence limits the interpretation of No Feedback as a risk-constrained baseline. No extra gate was invented. Detailed factor definitions are in SPECIFICATION.md.

## 5. Evaluation Metrics

Returns were daily time-weighted returns with external transfers removed. Risk was evaluated with sample volatility, linearly interpolated historical VaR95 and inclusive-tail CVaR95, equity-only sector HHI and time-weighted maximum drawdown. The implemented breach parametric VaR was 1.645 times trailing 30-session volatility; historical estimates used 252 aligned returns. Sharpe used a 4% annual risk-free rate and 252 sessions. Proposed household overspend was separated from actual brokerage execution. Turnover was purchase notional divided by average equity, without annualization. Reported mean outcomes gave equal weight to synthetic profiles. Undefined metrics were NA. Formulas, units, censoring and aggregation rules are specified in SPECIFICATION.md. Realized losses were kept separate from in-sample risk estimates.

### Table 1. Principal comparison

Equal-profile means for 2022–2025, except maximum overspend, which is the maximum across all profiles. Rates and returns are fractions, money is INR, durations are trading sessions. Feedback response time is conditional on an observed directly modified recommendation; missing responses are censored and cannot be interpreted as immediate responses. Cash earned zero interest while the Sharpe benchmark was 4%; very cash-heavy profiles can therefore have strongly negative Sharpe ratios even with small positive nominal gains.

| Metric | Affordability Only | Risk Only | No Feedback | Full IntelliVest |
| --- | --- | --- | --- | --- |
| affordability_violation_rate | 0.0000 | 0.2384 | 0.0000 | 0.0000 |
| mean_overspend | 0.0000 | 1698.0594 | 0.0000 | 0.0000 |
| max_overspend | 0.0000 | 63977.3502 | 0.0000 | 0.0000 |
| surplus_utilization | 0.0796 | 0.5635 | 0.0796 | 0.0796 |
| no_purchase_frequency | 0.7130 | 0.6019 | 0.7199 | 0.7199 |
| mean_hhi | 0.3860 | 0.1200 | 0.3478 | 0.3478 |
| hhi_breach_sessions | 423.1111 | 26.6667 | 326.6667 | 326.6667 |
| cvar95 | 0.0028 | 0.0143 | 0.0031 | 0.0031 |
| maximum_drawdown | 0.0287 | 0.1392 | 0.0288 | 0.0288 |
| annualized_volatility | 0.0197 | 0.0977 | 0.0211 | 0.0211 |
| cumulative_return | 0.1026 | 0.5897 | 0.1119 | 0.1119 |
| annualized_return | 0.0243 | 0.1250 | 0.0264 | 0.0264 |
| sharpe | -10.2720 | 0.8375 | -21.8011 | -21.8011 |
| turnover | 0.1263 | 0.6021 | 0.1251 | 0.1251 |
| average_idle_cash | 918351.5730 | 582321.5635 | 924915.8896 | 924915.8896 |
| average_cash_allocation | 0.8582 | 0.3014 | 0.8562 | 0.8562 |
| transaction_fees | 261.2191 | 668.5611 | 250.5056 | 250.5056 |
| slippage_cost | 130.5443 | 334.1135 | 125.1902 | 125.1902 |
| policy_adjustments | 0.0000 | 0.0000 | 0.0000 | 6.1111 |
| direct_feedback_changed_decisions | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| feedback_response_sessions | NA | NA | NA | NA |

## 6. Results for RQ1: Affordability

Full minus Risk Only mean proposed-violation rate was -0.238426. Full violation rate was 0.000000, versus 0.238426 for Risk Only. Mean overspend per monthly decision was INR 0.00 and INR 1698.06, respectively. The maximum Risk Only proposal excess was INR 63977.35. This comparison assessed realistic household capacity even when accumulated brokerage savings allowed an order to execute. H1 is supported within these controlled scenarios. This is partly a mechanical compliance result of the gate, not evidence of predictive stock-selection skill. Figure 4 reports frequency and magnitude.

## 7. Results for RQ2: Portfolio Risk Control

Full minus Affordability Only mean daily CVaR95 difference was 0.000282, mean HHI difference was -0.038134, and maximum-drawdown difference was 0.000112. Mean HHI-breach-session difference was -96.44. H2 received support for concentration compliance but not for lower realized CVaR or drawdown in the primary profile means; these signs do not justify a blanket risk or return superiority claim. Exposure ordering and feedback jointly differ in this contrast. Figures 2 and 3 show concentration and drawdown trajectories.

## 8. Results for RQ3: Closed-Loop Feedback

Full produced 55 effective policy adjustments and 0 monthly decisions different from its same-state fixed-policy counterfactual across the nine primary profiles. Full and No Feedback differed on 0 of 432 paired monthly decisions, including accumulated path effects. Mean HHI-breach-session difference was 0.00. Among observed breach episodes, 0 received a directly modified proposal and 9 had no observed such response. Mean conditional response latency was unobserved (no directly modified proposal); conditional latency omits censored cases and is not an unconditional improvement estimate. Policy changes, modified proposals and actual holdings correction were measured separately. H3 was unsupported in the primary empty-account comparisons: no decision effect was demonstrated; persistence outcomes did not decrease on average in these profiles. The buy-only mechanism did not execute corrective sales. Figure 5 shows the distinct events.

### Supplementary mechanism stress

After the initial primary null decision effect was observed, we added and explicitly labelled a mechanism stress, without replacing the primary comparison. The starting portfolio targeted 90% of the same INR 100,000 wealth to the stock with the largest pre-start 252-return volatility, using only information before 2022. Three primary financial/risk profiles and all four policies were replayed; initial fixed constraints for the baselines were derived from the same pre-start portfolio. Full made 3 decisions different from its same-state frozen-policy counterfactual and 5 policy adjustments. The mean Full-minus-No Feedback HHI-breach-session difference was 0.00. This targeted exposure stress was a diagnostic mechanism probe, not confirmatory evidence selected independently of the initial null finding. It did not alter the primary result. Supplementary Figure 7 and feedback_stress.csv preserve its outcomes.

| scenario | strategy | annualized_return | cvar95 | mean_hhi | hhi_breach_sessions | policy_adjustments | direct_feedback_changed_decisions |
| --- | --- | --- | --- | --- | --- | --- | --- |
| low_conservative | Affordability Only | 0.0752 | 0.0437 | 0.9898 | 988 | 0 | 0 |
| low_conservative | Risk Only | 0.1368 | 0.0448 | 0.4732 | 712 | 0 | 0 |
| low_conservative | No Feedback | 0.0748 | 0.0437 | 0.9964 | 988 | 0 | 0 |
| low_conservative | Full IntelliVest | 0.0748 | 0.0437 | 0.9964 | 988 | 4 | 0 |
| medium_moderate | Affordability Only | 0.0668 | 0.0250 | 0.6483 | 988 | 0 | 0 |
| medium_moderate | Risk Only | 0.1666 | 0.0286 | 0.2101 | 253 | 0 | 0 |
| medium_moderate | No Feedback | 0.0701 | 0.0254 | 0.6162 | 988 | 0 | 0 |
| medium_moderate | Full IntelliVest | 0.0701 | 0.0254 | 0.6162 | 988 | 0 | 0 |
| high_aggressive | Affordability Only | 0.0944 | 0.0153 | 0.1315 | 21 | 0 | 0 |
| high_aggressive | Risk Only | 0.1229 | 0.0177 | 0.1170 | 21 | 0 | 0 |
| high_aggressive | No Feedback | 0.0956 | 0.0155 | 0.1224 | 21 | 0 | 0 |
| high_aggressive | Full IntelliVest | 0.1008 | 0.0156 | 0.1248 | 21 | 1 | 3 |

## 9. Results for RQ4: Investment Performance Trade-offs

Table 1 reports all four policies without removing unfavorable outcomes. Figure 1 distinguishes account equity from supplied capital; Figure 6 compares time-weighted annualized return and realized volatility. Full annualized return averaged 0.026352, versus 0.124963 for Risk Only, 0.024290 for Affordability Only and 0.026352 for No Feedback. Differences in cash exposure, stock eligibility exhaustion and invested capital accompany these outcomes. Lower volatility is not automatically better investment performance. Cost sensitivity and the realized return/cost/cash columns are retained in the machine-readable outputs.

## 10. RQ5 and Momentum Robustness

All nine cross-factor profiles were replayed in fixed 2022–2023, 2024–2025 and 2026 YTD windows in addition to the primary window. `robustness_subgroups.csv` preserves every profile/window/policy cell; overlapping windows do not provide independent replications. The actual implemented momentum ranking was ablated by zeroing only its tier penalty coefficients. `momentum_paired_differences.csv` reports paired returns, drawdown, volatility, CVaR, turnover, HHI and strong-negative-momentum selection frequency. A descriptive mean with-minus-without annualized-return difference was 0.001209; it is not a parameter-tuned efficacy result.

## 11. Statistical Interpretation

We calculated matched profile/window differences and paired circular moving-block bootstrap intervals for annualized arithmetic daily-mean-return differences (20-session blocks, 2,000 draws, seed 20261023). Shared dates were resampled jointly across policies. These conditional time-series intervals are not intervals for a population of investors or a universe of markets. Scenarios were not treated as random samples and daily observations were not subjected to independent-observation t-tests. No inferential p-values or claims of statistical superiority were produced. `primary_uncertainty.csv` and `paired_comparisons.csv` retain each conditional interval and descriptive paired difference.

### Table 2. Mean paired differences (Full minus baseline)

| contrast | affordability_violation_rate_difference | mean_hhi_difference | hhi_breach_sessions_difference | cvar95_difference | maximum_drawdown_difference | annualized_return_difference |
| --- | --- | --- | --- | --- | --- | --- |
| Full IntelliVest - Affordability Only | 0.0000 | -0.0381 | -96.4444 | 0.0003 | 0.0001 | 0.0021 |
| Full IntelliVest - No Feedback | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Full IntelliVest - Risk Only | -0.2384 | 0.2279 | 300.0000 | -0.0112 | -0.1104 | -0.0986 |

## 12. Threats to Validity

Current surviving securities and current sector labels induce selection bias; delisted names and historical membership are absent. Exchange price corroboration is sparse and does not independently certify every dividend-adjusted observation. Some complex corporate actions were excluded rather than approximated. Whole-share eligibility, absence of repeat purchases of held stocks and a maximum of three sectors per batch can exhaust eligible candidates and create cash-heavy portfolios. Initial purchase concentration can itself exceed HHI .25. High-surplus and low-surplus outcomes are conditional on the same INR 100,000 starting account. The initial empty portfolio makes the fixed policy in No Feedback unrestricted; no absent HHI gate was invented.

## 13. Limitations

Dividend availability was approximated on ex-date rather than unknown payment dates. Split reconstruction uses the downloaded horizon and revised vendor prices; there were no contemporaneous data vintages. Cash earned no interest. Costs were proportional assumptions, not a complete Indian tax/stamp-duty schedule. No investor acceptance behavior, market impact, forced rebalancing or predictive calibration was modeled. Feedback monitoring was scheduled daily, whereas the application evaluates on requests. Results do not prove that VaR estimates forecast losses accurately. Ending HHI episodes were right-censored. Averaging conditional response times omits nonresponses; their counts remain explicit. Conditional bootstrap intervals and overlapping calendar windows cannot establish general effectiveness.

## 14. Conclusion Supported by Results

The executed pipeline distinguished affordability compliance, portfolio concentration, realized investment performance and feedback decision changes. H1 was supported for the defined scenarios. Feedback did not demonstrate changed proposals in the primary empty-account comparisons, while persistent portfolio-breach outcomes required separate evaluation. H2 and H3 were not collapsed into an unconditional superiority statement. RQ4 was treated as a trade-off question, with all measured policy outcomes retained. The evidence supports a reproducible exploratory restricted-universe comparison, not a publication-ready market-wide claim of superior advisory performance. Further validation requires complete action-aware security histories, broader point-in-time eligibility and independent out-of-sample market periods.

## Scenario outcomes

| scenario | strategy | annualized_return | cvar95 | mean_hhi | hhi_breach_sessions | affordability_violation_rate | surplus_utilization |
| --- | --- | --- | --- | --- | --- | --- | --- |
| low_conservative | Affordability Only | 0.0006 | 0.0001 | 1.0000 | 907 | 0.0000 | 0.0024 |
| low_conservative | Risk Only | 0.1416 | 0.0140 | 0.1213 | 40 | 0.3958 | 0.9182 |
| low_conservative | No Feedback | 0.0002 | 0.0000 | 1.0000 | 907 | 0.0000 | 0.0010 |
| low_conservative | Full IntelliVest | 0.0002 | 0.0000 | 1.0000 | 907 | 0.0000 | 0.0010 |
| low_moderate | Affordability Only | 0.0016 | 0.0003 | 1.0000 | 907 | 0.0000 | 0.0058 |
| low_moderate | Risk Only | 0.1613 | 0.0171 | 0.1185 | 40 | 0.3958 | 1.0441 |
| low_moderate | No Feedback | 0.0006 | 0.0002 | 1.0000 | 907 | 0.0000 | 0.0030 |
| low_moderate | Full IntelliVest | 0.0006 | 0.0002 | 1.0000 | 907 | 0.0000 | 0.0030 |
| low_aggressive | Affordability Only | 0.0102 | 0.0010 | 0.2841 | 391 | 0.0000 | 0.0616 |
| low_aggressive | Risk Only | 0.1490 | 0.0168 | 0.1299 | 20 | 0.3125 | 0.9885 |
| low_aggressive | No Feedback | 0.0151 | 0.0016 | 0.1947 | 164 | 0.0000 | 0.0682 |
| low_aggressive | Full IntelliVest | 0.0151 | 0.0016 | 0.1947 | 164 | 0.0000 | 0.0682 |
| medium_conservative | Affordability Only | 0.0026 | 0.0003 | 0.3515 | 947 | 0.0000 | 0.0135 |
| medium_conservative | Risk Only | 0.1201 | 0.0121 | 0.1365 | 40 | 0.1667 | 0.5039 |
| medium_conservative | No Feedback | 0.0013 | 0.0002 | 0.3176 | 782 | 0.0000 | 0.0075 |
| medium_conservative | Full IntelliVest | 0.0013 | 0.0002 | 0.3176 | 782 | 0.0000 | 0.0075 |
| medium_moderate | Affordability Only | 0.0085 | 0.0012 | 0.2590 | 474 | 0.0000 | 0.0500 |
| medium_moderate | Risk Only | 0.1200 | 0.0141 | 0.1117 | 20 | 0.2292 | 0.3740 |
| medium_moderate | No Feedback | 0.0136 | 0.0020 | 0.1280 | 40 | 0.0000 | 0.0609 |
| medium_moderate | Full IntelliVest | 0.0136 | 0.0020 | 0.1280 | 40 | 0.0000 | 0.0609 |
| medium_aggressive | Affordability Only | 0.0429 | 0.0041 | 0.1529 | 61 | 0.0000 | 0.1365 |
| medium_aggressive | Risk Only | 0.1236 | 0.0153 | 0.1139 | 20 | 0.1875 | 0.3894 |
| medium_aggressive | No Feedback | 0.0485 | 0.0051 | 0.1169 | 40 | 0.0000 | 0.1533 |
| medium_aggressive | Full IntelliVest | 0.0485 | 0.0051 | 0.1169 | 40 | 0.0000 | 0.1533 |
| high_conservative | Affordability Only | 0.0212 | 0.0024 | 0.1567 | 61 | 0.0000 | 0.0741 |
| high_conservative | Risk Only | 0.0948 | 0.0103 | 0.1197 | 20 | 0.0208 | 0.2504 |
| high_conservative | No Feedback | 0.0220 | 0.0026 | 0.1371 | 40 | 0.0000 | 0.0728 |
| high_conservative | Full IntelliVest | 0.0220 | 0.0026 | 0.1371 | 40 | 0.0000 | 0.0728 |
| high_moderate | Affordability Only | 0.0565 | 0.0061 | 0.1412 | 40 | 0.0000 | 0.1499 |
| high_moderate | Risk Only | 0.1057 | 0.0136 | 0.1148 | 20 | 0.2083 | 0.2943 |
| high_moderate | No Feedback | 0.0533 | 0.0061 | 0.1224 | 40 | 0.0000 | 0.1397 |
| high_moderate | Full IntelliVest | 0.0533 | 0.0061 | 0.1224 | 40 | 0.0000 | 0.1397 |
| high_aggressive | Affordability Only | 0.0744 | 0.0097 | 0.1284 | 20 | 0.0000 | 0.2228 |
| high_aggressive | Risk Only | 0.1086 | 0.0152 | 0.1134 | 20 | 0.2292 | 0.3091 |
| high_aggressive | No Feedback | 0.0826 | 0.0101 | 0.1138 | 20 | 0.0000 | 0.2098 |
| high_aggressive | Full IntelliVest | 0.0826 | 0.0101 | 0.1138 | 20 | 0.0000 | 0.2098 |

## Figures

**figure_1_portfolio_value** — Nominal account equity includes contributions. Dotted lines show initial cash plus identical supplied capital; cash-flow-adjusted returns are reported separately.

**figure_2_sector_hhi** — HHI excludes cash; undefined before the first purchase. The dashed line is the fixed 0.25 threshold. Policy changes do not imply holdings have corrected.

**figure_3_drawdown** — Daily time-weighted wealth, including the initial wealth peak. Losses are negative; external transfers are removed from return calculations.

**figure_4_affordability** — Equal-profile means in the primary window. Overspend is proposed notional beyond monthly household capacity, measured separately from brokerage execution feasibility.

**figure_5_feedback_response** — Markers distinguish breached observations, effective policy changes and proposals changed against the same-state fixed-policy counterfactual. Suppression of future purchases is not a corrective sale.

**figure_6_risk_return** — Each point is a profile-policy replay on the same market window. Profiles are deterministic design scenarios, not independent sampled investors; no efficacy frontier is inferred.

**figure_7_feedback_stress** — All three targeted concentrated-start profiles, selected with pre-start volatility only. Stars identify changed proposals; none occurred in the low/conservative or medium/moderate profiles. This mechanism probe is supplementary and cannot replace the principal null result.
