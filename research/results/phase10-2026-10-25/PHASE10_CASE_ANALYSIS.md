# Positive and negative allocation cases

Exploratory evidence from nine synthetic investor profiles and previously examined historical paths. No independent holdout, unbiased point-in-time universe or population-level investor inference is established.

largest positive same-state V3-V1 fill; largest utility deficit among greedy-dominated V3 states; first medium-moderate decision; all aggregate states retained

## positive_extreme_vs_V1 — low_conservative|2025-06-02

Cash INR265428.04, approved authority INR1250.00, saved batch budget INR1250.00. Existing holdings: `{"ADANIPORTS": 6, "BEL": 25, "BPCL": 12, "COALINDIA": 4, "DRREDDY": 1, "HCLTECH": 1, "HINDALCO": 3, "ICICIBANK": 4, "JSWSTEEL": 4, "M&M": 2, "NTPC": 14, "ONGC": 6, "POWERGRID": 7, "SBILIFE": 1, "SUNPHARMA": 3, "TATACONSUM": 6, "TATASTEEL": 10, "WIPRO": 22}`. All candidate prices/scores and covariance are retained in matched-state exports.

| method | budget_fill | U_norm | HHI | purchase_positions | post_positions |
|---|---|---|---|---|---|
| V3 | 99.96577 | 94.82520 | 0.10189 | 1.00000 | 18.00000 |
| GREEDY | 99.96577 | 94.82520 | 0.10189 | 1.00000 | 18.00000 |
| REF_U | 99.96577 | 94.82520 | 0.10189 | 1.00000 | 18.00000 |

| method | ticker | sector | existing_quantity | purchased_quantity | observed_price | selection_score | size_weight | inclusive_cost |
|---|---|---|---|---|---|---|---|---|
| V3 | DRREDDY | Healthcare | 1.0000 | 1.0000 | 1247.7000 | -0.0303 | 25.8968 | 1249.5721 |
| GREEDY | DRREDDY | Healthcare | 1.0000 | 1.0000 | 1247.7000 | -0.0303 | 25.8968 | 1249.5721 |
| REF_U | DRREDDY | Healthcare | 1.0000 | 1.0000 | 1247.7000 | -0.0303 | 25.8968 | 1249.5721 |


## negative_extreme_vs_greedy — low_conservative|2024-06-03

Cash INR217131.60, approved authority INR1250.00, saved batch budget INR1250.00. Existing holdings: `{"ADANIPORTS": 4, "BEL": 24, "BPCL": 5, "COALINDIA": 2, "HCLTECH": 1, "HINDALCO": 2, "ICICIBANK": 3, "JSWSTEEL": 4, "M&M": 2, "NTPC": 10, "ONGC": 5, "POWERGRID": 6, "SBILIFE": 1, "SUNPHARMA": 3, "TATACONSUM": 5, "TATASTEEL": 7, "WIPRO": 7}`. All candidate prices/scores and covariance are retained in matched-state exports.

| method | budget_fill | U_norm | HHI | purchase_positions | post_positions |
|---|---|---|---|---|---|
| V3 | 89.73444 | 35.98980 | 0.10259 | 3.00000 | 17.00000 |
| GREEDY | 92.93925 | 92.80000 | 0.10256 | 1.00000 | 17.00000 |
| REF_U | 92.93925 | 92.80000 | 0.10256 | 1.00000 | 17.00000 |

| method | ticker | sector | existing_quantity | purchased_quantity | observed_price | selection_score | size_weight | inclusive_cost |
|---|---|---|---|---|---|---|---|---|
| V3 | NTPC | Power | 10.0000 | 1.0000 | 391.8000 | -0.0319 | 21.5146 | 392.3879 |
| V3 | ONGC | Energy | 5.0000 | 1.0000 | 284.1000 | -0.0355 | 21.0760 | 284.5263 |
| V3 | WIPRO | Information Technology | 7.0000 | 1.0000 | 444.1000 | -0.0324 | 23.9861 | 444.7664 |
| GREEDY | ICICIBANK | Financial Services | 3.0000 | 1.0000 | 1160.0000 | -0.0232 | 30.0794 | 1161.7406 |
| REF_U | ICICIBANK | Financial Services | 3.0000 | 1.0000 | 1160.0000 | -0.0232 | 30.0794 | 1161.7406 |


## prespecified_representative — medium_moderate|2022-01-03

Cash INR120000.00, approved authority INR10000.00, saved batch budget INR10000.00. Existing holdings: `{}`. All candidate prices/scores and covariance are retained in matched-state exports.

| method | budget_fill | U_norm | HHI | purchase_positions | post_positions |
|---|---|---|---|---|---|
| V3 | 99.76247 | 93.67144 | 0.34254 | 3.00000 | 3.00000 |
| GREEDY | 98.85060 | 94.81744 | 0.92634 | 2.00000 | 2.00000 |
| REF_U | 99.70037 | 95.88157 | 0.63813 | 2.00000 | 2.00000 |

| method | ticker | sector | existing_quantity | purchased_quantity | observed_price | selection_score | size_weight | inclusive_cost |
|---|---|---|---|---|---|---|---|---|
| V3 | BRITANNIA | Consumer Goods | 0.0000 | 1.0000 | 3617.5500 | -0.0171 | 9.3877 | 3622.9782 |
| V3 | INFY | Information Technology | 0.0000 | 2.0000 | 1898.4500 | -0.0168 | 8.7288 | 3802.5972 |
| V3 | SUNPHARMA | Healthcare | 0.0000 | 3.0000 | 848.9500 | -0.0208 | 7.8532 | 2550.6716 |
| GREEDY | INFY | Information Technology | 0.0000 | 5.0000 | 1898.4500 | -0.0168 | 8.7288 | 9506.4929 |
| GREEDY | NTPC | Power | 0.0000 | 3.0000 | 126.0000 | -0.0241 | 7.5255 | 378.5672 |
| REF_U | HINDUNILVR | Consumer Goods | 0.0000 | 1.0000 | 2361.3000 | -0.0200 | 8.9241 | 2364.8432 |
| REF_U | INFY | Information Technology | 0.0000 | 4.0000 | 1898.4500 | -0.0168 | 8.7288 | 7605.1943 |


## Complete stratification

| method | grouping | stratum | states | mean_U_norm | mean_budget_fill | mean_HHI | valid_rate |
|---|---|---|---|---|---|---|---|
| GREEDY | budget_stratum | low_le2500 | 96.000 | 86.941 | 97.072 | 0.125 | 100.000 |
| GREEDY | budget_stratum | middle_2500_15000 | 192.000 | 95.128 | 98.839 | 0.117 | 100.000 |
| GREEDY | budget_stratum | high_gt15000 | 144.000 | 99.022 | 99.780 | 0.116 | 100.000 |
| V3 | budget_stratum | low_le2500 | 96.000 | 51.472 | 95.631 | 0.119 | 100.000 |
| V3 | budget_stratum | middle_2500_15000 | 192.000 | 59.676 | 97.030 | 0.103 | 100.000 |
| V3 | budget_stratum | high_gt15000 | 144.000 | 65.452 | 99.162 | 0.102 | 100.000 |
| GREEDY | holdings_stratum | empty | 9.000 | 92.173 | 98.740 | 0.639 | 100.000 |
| GREEDY | holdings_stratum | one_to_nine | 28.000 | 93.147 | 97.614 | 0.256 | 100.000 |
| GREEDY | holdings_stratum | ten_plus | 395.000 | 94.765 | 98.842 | 0.097 | 100.000 |
| V3 | holdings_stratum | empty | 9.000 | 88.611 | 96.876 | 0.474 | 100.000 |
| V3 | holdings_stratum | one_to_nine | 28.000 | 59.828 | 98.209 | 0.169 | 100.000 |
| V3 | holdings_stratum | ten_plus | 395.000 | 59.118 | 97.387 | 0.093 | 100.000 |
| GREEDY | concentration_stratum | concentrated | 13.000 | 91.511 | 97.409 | 0.326 | 100.000 |
| GREEDY | concentration_stratum | diversified | 410.000 | 94.758 | 98.803 | 0.100 | 100.000 |
| GREEDY | concentration_stratum | empty | 9.000 | 92.173 | 98.740 | 0.639 | 100.000 |
| V3 | concentration_stratum | concentrated | 13.000 | 78.742 | 97.981 | 0.220 | 100.000 |
| V3 | concentration_stratum | diversified | 410.000 | 58.544 | 97.425 | 0.095 | 100.000 |
| V3 | concentration_stratum | empty | 9.000 | 88.611 | 96.876 | 0.474 | 100.000 |
| GREEDY | affordability_stratum | low_price_relative_to_budget | 172.000 | 98.753 | 99.680 | 0.120 | 100.000 |
| GREEDY | affordability_stratum | middle_price_relative_to_budget | 180.000 | 94.574 | 98.780 | 0.115 | 100.000 |
| GREEDY | affordability_stratum | high_price_relative_to_budget | 80.000 | 85.765 | 96.736 | 0.123 | 100.000 |
| V3 | affordability_stratum | low_price_relative_to_budget | 172.000 | 65.071 | 99.011 | 0.103 | 100.000 |
| V3 | affordability_stratum | middle_price_relative_to_budget | 180.000 | 58.963 | 96.757 | 0.104 | 100.000 |
| V3 | affordability_stratum | high_price_relative_to_budget | 80.000 | 50.234 | 95.545 | 0.119 | 100.000 |
| GREEDY | candidate_stratum | 21_to_35 | 13.000 | 91.511 | 97.409 | 0.326 | 100.000 |
| GREEDY | candidate_stratum | over_35 | 419.000 | 94.703 | 98.802 | 0.112 | 100.000 |
| V3 | candidate_stratum | 21_to_35 | 13.000 | 78.742 | 97.981 | 0.220 | 100.000 |
| V3 | candidate_stratum | over_35 | 419.000 | 59.190 | 97.413 | 0.103 | 100.000 |
| GREEDY | tier | AGGRESSIVE | 144.000 | 96.432 | 99.138 | 0.114 | 100.000 |
| GREEDY | tier | CONSERVATIVE | 144.000 | 92.300 | 98.100 | 0.123 | 100.000 |
| GREEDY | tier | MODERATE | 144.000 | 95.087 | 99.042 | 0.118 | 100.000 |
| V3 | tier | AGGRESSIVE | 144.000 | 60.980 | 97.893 | 0.101 | 100.000 |
| V3 | tier | CONSERVATIVE | 144.000 | 57.862 | 97.092 | 0.114 | 100.000 |
| V3 | tier | MODERATE | 144.000 | 60.492 | 97.305 | 0.104 | 100.000 |


Diversification differences are greatest in empty/concentrated inputs; those strata contain9/13 states. With ten-plus existing holdings (395 states), V3 mean HHI0.0934 versus greedy0.0967 accompanies normalized utility0.5912 versus 0.9477. These small/co-dependent strata do not support human-population claims. Fixed candidate-count strata without observations are unavailable, not silently extrapolated.
