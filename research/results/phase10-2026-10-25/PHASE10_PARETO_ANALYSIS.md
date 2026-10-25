# Observed utility–diversification trade-offs

Exploratory evidence from nine synthetic investor profiles and previously examined historical paths. No independent holdout, unbiased point-in-time universe or population-level investor inference is established.

## Prespecified search and normalization

Candidate utility is ordinal utility-weighted nominal purchases / saved approved budget. Diversification is one minus equity-only posttrade sector HHI. Utilization is fee-inclusive cost / budget. No raw-score/HHI scale mixing or sample-fitted normalization is used. Empty-sleeve HHI is undefined. Five U/D preferences plus pure budget and equal-weight U/D/B were fixed in PROTOCOL.json before the historical grid; all methods receive the same scores. The reference solves max utility at no extra cap and HHI caps .35,.25,.20,.15,.10, plus max budget. The wider sensitivity solves only pure utility and budget, so its observed frontier is less densely sampled and its nondominance rate must not be compared as equal-coverage evidence.

An allocation is observed-nondominated if no valid evaluated allocation improves at least one selected component without worsening another (tolerance1e-8). Both UD and UDB status are exported. Empty HHI and failed/target-infeasible reference outputs are excluded from frontier candidates. The no-trade alternative is retained only where it has defined existing equity holdings. Matching tolerances were fixed: absolute HHI difference <=.01; normalized utility difference <=.02. Similarity does not mean exact equality.

## V3 placement

The lowest additional reference HHI target was .10, while V3 ends below .10 in 348/432 states. This coarse grid can favor V3's observed nondominance because the reference is not directly minimizing HHI in that region. V3 is best observed for pure diversification in 85.42% of states, but for balanced U/D/B in only3.01%. These are fixed-grid candidate comparisons, not proof of global diversified allocation competitiveness.

V3 is observed-nondominated in **97.69%** of F3 states for U/D and **98.15%** for U/D/B. Greedy dominates it on all three metrics in **0.69%**. These are observed finite-set results, not global Pareto certificates. The search can miss dominating portfolios, particularly when the reference reaches a resource limit. A high nondominance rate does not prove a favorable economic exchange rate between utility and HHI.

Relative to constrained greedy, mean V3 utility changes by -0.348281 of budget, fill by -0.013301, and HHI by -0.012113. Report all three together. Similar-HHI reference comparisons cover 397/432 states; mean additional reference utility is 0.343056. Similar-utility comparisons cover 41/432; mean V3 HHI minus best similar-utility reference HHI is -0.005815. Coverage is reported instead of extrapolating unavailable matches.

## Common scalar-objective comparisons

| preference | method | mean_objective | median_objective | mean_observed_regret | best_observed_fraction |
|---|---|---|---|---|---|
| balanced_UD | GREEDY | 0.9139 | 0.9350 | 0.0061 | 56.2500 |
| balanced_UD | REF_B | 0.6468 | 0.6331 | 0.2732 | 0.2315 |
| balanced_UD | REF_U | 0.9164 | 0.9366 | 0.0036 | 93.9815 |
| balanced_UD | V3 | 0.7458 | 0.7658 | 0.1742 | 2.7778 |
| balanced_UDB | GREEDY | 0.9384 | 0.9535 | 0.0049 | 59.0278 |
| balanced_UDB | REF_B | 0.7637 | 0.7554 | 0.1796 | 0.2315 |
| balanced_UDB | REF_U | 0.9409 | 0.9548 | 0.0025 | 90.2778 |
| balanced_UDB | V3 | 0.8220 | 0.8368 | 0.1214 | 3.0093 |
| budget | GREEDY | 0.9876 | 0.9953 | 0.0123 | 0.2315 |
| budget | REF_B | 0.9976 | 1.0000 | 0.0023 | 99.7685 |
| budget | REF_U | 0.9899 | 0.9964 | 0.0100 | 0.2315 |
| budget | V3 | 0.9743 | 0.9874 | 0.0256 | 0.4630 |
| diversification | GREEDY | 0.8817 | 0.9068 | 0.0151 | 1.1574 |
| diversification | REF_B | 0.8894 | 0.9072 | 0.0074 | 2.7778 |
| diversification | REF_U | 0.8797 | 0.9068 | 0.0171 | 0.9259 |
| diversification | V3 | 0.8938 | 0.9082 | 0.0030 | 85.4167 |
| moderate_diversification | GREEDY | 0.8978 | 0.9202 | 0.0076 | 52.7778 |
| moderate_diversification | REF_B | 0.7681 | 0.7671 | 0.1373 | 0.2315 |
| moderate_diversification | REF_U | 0.8981 | 0.9211 | 0.0073 | 88.8889 |
| moderate_diversification | V3 | 0.8198 | 0.8346 | 0.0856 | 3.7037 |
| moderate_utility | GREEDY | 0.9300 | 0.9505 | 0.0059 | 56.9444 |
| moderate_utility | REF_B | 0.5255 | 0.5028 | 0.4104 | 0.2315 |
| moderate_utility | REF_U | 0.9348 | 0.9529 | 0.0011 | 96.7593 |
| moderate_utility | V3 | 0.6718 | 0.7017 | 0.2641 | 1.6204 |
| utility | GREEDY | 0.9461 | 0.9690 | 0.0070 | 57.1759 |
| utility | REF_B | 0.4042 | 0.3728 | 0.5489 | 0.2315 |
| utility | REF_U | 0.9531 | 0.9714 | 0.0000 | 100.0000 |
| utility | V3 | 0.5978 | 0.6353 | 0.3553 | 1.1574 |


Every method is evaluated under every objective. V3's position is an empirical operational trade-off; differing internal preferences do not exempt it from unfavorable common-objective scores. No favorable subset of weights is selected as the only result. Figure3 shows one prespecified representative plus explicitly selected positive/negative extremes; aggregate CSVs retain all states.

## Statistical interpretation

Three-month circular blocks, 2000 draws, seed 20261025 provide descriptive monthly decision-difference intervals. Synchronized blocks preserve common market dates across profiles. Daily financial uncertainty from Phase 9 remains separate. No p-values or investor-population significance claims are produced. Strict numerical nondominance is sensitive to small differences; tolerances are disclosed and no economic optimality follows from it.
