# Statistical and exposure analysis

All findings are exploratory comparisons of nine synthetic profiles sharing historical market paths. Previously inspected observations, overlapping windows, surviving-security selection and current sector labels prevent independent-validation or population-level claims.

## Design and resampling

The experimental unit is a synthetic profile paired across strategies, conditional on a common historical path. There are nine designed profiles, not hundreds of independently sampled investors. Profile/window/replay counts are not independent sample sizes. No population p-values, optimal-parameter searches or multiplicity-adjusted significance claims are made.

Daily TWR follows E_t/(E_(t-1)+contribution_t)-1. Annualization uses 252 sessions. Sharpe uses mean daily excess return / sample daily standard deviation × sqrt(252), with primary rf=0.04/252; effective-geometric rf is a separate sensitivity. Historical VaR is negative empirical linear 5% return quantile truncated at zero; CVaR is the mean loss in observations at/below that quantile, at least VaR. Drawdown includes initial wealth=1 in the running peak. Cash-only/no-holding risk is unavailable at the account summary level where meaningful risk observations are absent; constant return Sharpe is undefined. Primary profiles all have defined but sometimes very unstable Sharpe ratios.

The existing deterministic circular moving-block procedure is retained: 20 observed-session blocks, 2,000 draws, seed 20261024. Paired daily return differences are resampled together. For the following mean-profile intervals, date blocks are synchronized across all nine profiles, preserving their shared market dependence. The statistic is the mean annualized **arithmetic daily-return difference**, not a confidence interval for the difference in geometric annualized returns. Per-profile intervals and geometric paired differences are separately exported. Intervals describe path uncertainty conditional on this exposed historical sample; they do not validate synthetic profiles as a human population.

| contrast | profiles | mean_annualized_arithmetic_return_difference | ci95_low | ci95_high |
|---|---|---|---|---|
| V3 - GREEDY_M | 9.000 | 2.715 | -0.410 | 5.838 |
| V4 - GREEDY_C | 9.000 | 2.775 | -0.451 | 5.959 |
| V3 - EQUAL_M | 9.000 | 1.526 | -0.228 | 3.401 |
| V4 - EQUAL_C | 9.000 | 1.700 | -0.129 | 3.631 |
| V4 - V3 | 9.000 | 0.392 | 0.152 | 0.627 |
| V3 - NEUTRAL_M | 9.000 | -0.438 | -2.333 | 1.391 |
| V4 - NEUTRAL_C | 9.000 | -0.420 | -2.337 | 1.479 |
| V3 - SIP_M | 9.000 | -0.844 | -3.601 | 2.037 |
| V4 - SIP_C | 9.000 | -0.801 | -3.894 | 2.430 |
| V3 - ETF_M | 9.000 | 3.657 | 1.028 | 6.501 |
| V4 - ETF_C | 9.000 | 3.965 | 1.214 | 6.952 |
| V3 - RANK_TOPUP_M | 9.000 | 3.979 | 1.406 | 6.728 |
| V3 - FEAS_NO_TOPUP_M | 9.000 | 4.088 | 1.244 | 7.218 |
| V3 - V1 | 9.000 | 5.828 | 2.005 | 10.048 |


Units are percentage points/year. V3/greedy and V4/greedy intervals include zero, as do equal-weight, SIP and neutral-preference comparisons. V3/ETF and V4/ETF temporal intervals are positive in this sample, but universe, exposure and retrospective-data caveats remain. The V4/V3 interval is positive under this resampling statistic; it does not prove that ledger complexity is worthwhile or that downside-adjusted utility improves.

## Investor-level Sharpe distribution

| policy | median_defined_sharpe | mean_defined_sharpe | min_defined_sharpe | max_defined_sharpe | undefined_sharpe_count | low_volatility_sharpe_count |
|---|---|---|---|---|---|---|
| V1 | -1.934 | -21.801 | -132.192 | 0.619 | 0.000 | 3.000 |
| GREEDY_M | 0.341 | 0.195 | -0.516 | 0.591 | 0.000 | 0.000 |
| V3 | 0.729 | 0.568 | -0.189 | 0.987 | 0.000 | 0.000 |
| MILP_M | 0.349 | 0.124 | -0.584 | 0.541 | 0.000 | 0.000 |
| EQUAL_M | 0.502 | 0.358 | -0.689 | 0.903 | 0.000 | 0.000 |
| SIP_M | 0.671 | 0.572 | -0.005 | 0.968 | 0.000 | 0.000 |
| ETF_M | 0.246 | -0.077 | -1.489 | 0.539 | 0.000 | 0.000 |
| GREEDY_C | 0.339 | 0.258 | -0.311 | 0.653 | 0.000 | 0.000 |
| V4 | 0.761 | 0.612 | -0.073 | 1.015 | 0.000 | 0.000 |
| MILP_C | 0.363 | 0.231 | -0.382 | 0.635 | 0.000 | 0.000 |
| EQUAL_C | 0.629 | 0.409 | -0.461 | 0.905 | 0.000 | 0.000 |
| SIP_C | 0.679 | 0.612 | 0.264 | 0.959 | 0.000 | 0.000 |
| ETF_C | 0.261 | -0.036 | -1.276 | 0.541 | 0.000 | 0.000 |
| NEUTRAL_M | 0.681 | 0.565 | -0.083 | 0.954 | 0.000 | 0.000 |
| NEUTRAL_C | 0.719 | 0.603 | -0.024 | 0.947 | 0.000 | 0.000 |


The primary V1 ratio range includes -132.19 from very small risky exposure; its mean must not be presented without this distribution. V3 median 0.729, V4 median 0.761. Defined ratios can still be numerically or economically unstable. low_volatility_sharpe_count counts defined ratios with annualized volatility below 1%, using the diagnostic phase's unchanged threshold. Per-investor flags and distributions are retained. Four-percent frozen-trade cash yield and both risk-free conventions are exported in cash_yield_sharpe_sensitivity.csv. The interest overlay adds no new approval and does not change trades; it is not a reinvestment-policy experiment. It reduces the interpretation of idle cash as wasted economic capital.

## Exposure-aware comparison

Equity-sleeve daily gross return is account PnL plus explicitly simulated fees/slippage divided by opening equity holdings, conditional on positive opening holdings. It can include dividends and is undefined without an opening sleeve. It is a diagnostic return, not a separately self-financing investable strategy. No sleeve drawdown is chained over missing unmatched dates. Same-date matching uses fixed opening-exposure bins [0,5,25,50,75,100]%; bins are broad and do not exactly match exposures or composition.

| contrast | coverage | gross_sleeve_cvar_a | gross_sleeve_cvar_b |
|---|---|---|---|
| V3 - EQUAL_M | 94.636 | 2.221 | 2.097 |
| V3 - ETF_M | 92.600 | 2.180 | 1.766 |
| V3 - FEAS_NO_TOPUP_M | 49.426 | 2.272 | 2.127 |
| V3 - GREEDY_M | 86.617 | 2.253 | 1.984 |
| V3 - NEUTRAL_M | 97.222 | 2.271 | 2.643 |
| V3 - RANK_TOPUP_M | 24.078 | 2.401 | 2.503 |
| V3 - SIP_M | 94.647 | 2.264 | 2.979 |
| V3 - V1 | 15.418 | 2.407 | 2.418 |
| V4 - EQUAL_C | 97.267 | 2.250 | 2.092 |
| V4 - ETF_C | 93.219 | 2.182 | 1.766 |
| V4 - GREEDY_C | 94.186 | 2.250 | 1.959 |
| V4 - NEUTRAL_C | 97.076 | 2.265 | 2.636 |
| V4 - SIP_C | 94.051 | 2.245 | 2.955 |
| V4 - V3 | 96.154 | 2.268 | 2.277 |


V3/V1 matching covers only 15.42% of sessions on average, while V4/V3 covers 96.15%. Sparse V1 matches cannot support a causal risk advantage. Even among comparable exposure bins, V3 has higher gross sleeve CVaR than greedy/ETF and lower than SIP/neutral. This reinforces composition and risk trade-offs. Mean conditional CVaRs in the table are not pooled return-tail estimates. Per-profile coverage, temporal intervals and full sleeve metrics are exported.

## Robustness

Original early, late and 2026 stock windows are rerun unchanged. window_robustness.csv and all_investor_performance.csv show means, medians and ranges. Cost sensitivities use zero versus 20bp fees+10bp slippage on low-conservative, medium-moderate, high-aggressive only; these selected-profile means must not be compared directly with nine-profile primary means. Reduced-universe sensitivity uses the first 20 ticker-sorted retained securities, chosen without future returns; it is not a reconstructed point-in-time market universe. Household deterioration sets buffer to zero January–March 2024 and revokes authority before the grant review. No independent dataset was found. No bootstrap addresses survivorship, historical sector error or researcher exposure to 2022–2025.
