# Investment benchmark results

All findings are exploratory comparisons of nine synthetic profiles sharing historical market paths. Previously inspected observations, overlapping windows, surviving-security selection and current sector labels prevent independent-validation or population-level claims.

## Primary 2022–2025 comparison

All displayed rates are percent; HHI and Sharpe are unitless. Means are across the same nine profiles. Sharpe column is the median of defined investor ratios, using a 4%/252 daily benchmark. CVaR is daily historical 95% expected tail loss; maximum drawdown uses daily contribution-adjusted TWR. M and C are separate authority regimes. ETF is an executable NIFTYBEES proxy, not a purchased index or a TRI reference.

| policy | regime | authorized_budget_utilization | annualized_return | annualized_volatility | cvar95 | maximum_drawdown | mean_hhi | mean_cash_allocation | median_defined_sharpe |
|---|---|---|---|---|---|---|---|---|---|
| V1 | M | 14.523 | 2.635 | 2.107 | 0.310 | 2.882 | 0.348 | 85.621 | -1.934 |
| GREEDY_M | M | 94.255 | 5.749 | 5.126 | 0.723 | 9.963 | 0.252 | 62.439 | 0.341 |
| V3 | M | 95.134 | 8.614 | 6.302 | 0.899 | 10.106 | 0.106 | 60.492 | 0.729 |
| MILP_M | M | 92.013 | 5.389 | 4.877 | 0.682 | 9.589 | 0.257 | 63.629 | 0.349 |
| EQUAL_M | M | 95.684 | 7.030 | 5.284 | 0.763 | 9.029 | 0.132 | 61.431 | 0.502 |
| SIP_M | M | 94.074 | 9.404 | 7.852 | 1.142 | 12.592 | 0.163 | 60.274 | 0.671 |
| ETF_M | M | 97.085 | 4.792 | 4.496 | 0.620 | 7.195 | unavailable | 61.503 | 0.246 |
| GREEDY_C | C | 99.683 | 6.094 | 5.295 | 0.746 | 10.554 | 0.257 | 60.907 | 0.339 |
| V4 | C | 99.958 | 9.031 | 6.492 | 0.927 | 10.483 | 0.106 | 59.136 | 0.761 |
| MILP_C | C | 99.802 | 5.981 | 5.277 | 0.741 | 10.633 | 0.256 | 60.557 | 0.363 |
| EQUAL_C | C | 99.974 | 7.256 | 5.416 | 0.780 | 9.246 | 0.133 | 60.117 | 0.629 |
| SIP_C | C | 99.882 | 9.756 | 8.165 | 1.191 | 12.973 | 0.159 | 58.618 | 0.679 |
| ETF_C | C | 99.930 | 4.876 | 4.573 | 0.631 | 7.328 | unavailable | 60.851 | 0.261 |
| NEUTRAL_M | M | 94.760 | 9.029 | 7.058 | 1.012 | 12.050 | 0.105 | 60.328 | 0.681 |
| NEUTRAL_C | C | 99.938 | 9.417 | 7.307 | 1.048 | 12.365 | 0.104 | 58.714 | 0.719 |


NIFTY 50 TRI daily reference: **unavailable (official endpoint HTTP 401)**. NIFTYBEES M/C are executable and separately labelled; tracking error and fund look-through HHI are unavailable. Its market prices include fund tracking/expense effects. Baseline application fees and adverse slippage are applied to every purchase, in addition to these embedded effects. Three conventional strategies are economically distinct: one fund, all-name equal-weight target purchases, and calendar-rotating sector representatives.

V3 returns 8.61% with 6.30% volatility, versus ETF M 4.79% and 4.50%. Its daily CVaR is 0.899% versus 0.620%, and drawdown 10.11% versus 7.19%. V4 returns 9.03% with 6.49% volatility versus ETF C 4.88% and 4.57%; daily CVaR is 0.927% versus 0.631%, drawdown 10.48% versus 7.33%. These are additional realized returns accompanied by larger losses and different equity composition/exposure, not demonstrated market-wide superiority.

Equal-weight M uses 95.68% approved capital versus V3 95.13%, so near-complete monthly deployment is not unique to IntelliVest. Under C, both are near 100%. SIP and neutral-preference policies produce higher mean primary returns than V3/V4, alongside higher CVaR and drawdown. The frozen ranking is therefore not validated as superior stock selection by these data.

## Contributions, turnover and execution costs

| policy | cumulative_return | ending_equity | turnover | transaction_fees | slippage_cost | buy_trades | sell_trades |
|---|---|---|---|---|---|---|---|
| V1 | 11.189 | 2299364.261 | 0.125 | 250.506 | 125.190 | 22.444 | 0.000 |
| GREEDY_M | 24.793 | 2411658.759 | 0.629 | 934.688 | 467.110 | 113.444 | 0.000 |
| V3 | 39.177 | 2613998.519 | 0.612 | 968.471 | 483.994 | 135.556 | 0.000 |
| MILP_M | 23.112 | 2385542.317 | 0.619 | 905.991 | 452.769 | 106.667 | 0.000 |
| EQUAL_M | 31.233 | 2529156.136 | 0.643 | 984.645 | 492.076 | 484.222 | 0.000 |
| SIP_M | 43.225 | 2606250.531 | 0.606 | 971.214 | 485.364 | 68.556 | 0.000 |
| ETF_M | 20.443 | 2400338.087 | 0.680 | 989.571 | 494.538 | 48.000 | 0.000 |
| GREEDY_C | 26.445 | 2423703.632 | 0.662 | 993.636 | 496.570 | 109.000 | 0.000 |
| V4 | 41.391 | 2634298.500 | 0.633 | 998.871 | 499.186 | 135.333 | 0.000 |
| MILP_C | 25.924 | 2419740.879 | 0.666 | 996.969 | 498.235 | 109.556 | 0.000 |
| EQUAL_C | 32.307 | 2535401.676 | 0.662 | 998.843 | 499.172 | 488.889 | 0.000 |
| SIP_C | 45.024 | 2601567.346 | 0.634 | 998.607 | 499.054 | 69.667 | 0.000 |
| ETF_C | 20.816 | 2402739.379 | 0.693 | 998.743 | 499.122 | 48.000 | 0.000 |
| NEUTRAL_M | 41.392 | 2617769.516 | 0.605 | 967.909 | 483.713 | 134.333 | 0.000 |
| NEUTRAL_C | 43.375 | 2631844.657 | 0.632 | 998.762 | 499.131 | 136.222 | 0.000 |


Ending equity in INR includes original savings and external contributions; it is not a return measure. Cumulative return is TWR. Turnover is total bought/sold execution notional / mean account equity over the entire window, not annualized turnover. All strategies are purchase-only and sales are zero. Fees/slippage are mean total INR per profile over four years, not portfolio-weighted pooled costs. Rebalance frequency is monthly purchase review; no actual sale equalization is performed. Equal-weight deviation and all daily holdings-derived metrics are exported.

## Coverage

Four stock windows: 2022–2025, 2022–2023, 2024–2025 and January–22 October 2026. ETF coverage ends 2025, so only the first three are compared. Overlapping windows are robustness descriptions, not independent replications. Per-profile, per-window return, contributions, ending value, HHI coverage/breach frequency/duration, purchases, sales, turnover, fees, slippage and Sharpe are in all_investor_performance.csv and portfolio_risk.csv.
