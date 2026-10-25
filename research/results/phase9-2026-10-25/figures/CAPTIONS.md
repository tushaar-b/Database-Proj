**01_capital_utilization.** Mean of nine synthetic profile ratios. Each external grant enters the denominator once; regimes differ in expiry and carry-forward.

**02_feasible_purchase_efficiency.** All 432 decisions per strategy, including decisions without affordable candidates. Basket-conditional execution rates and feasible non-execution counts are exported separately. Execution uses next-session closing prices.

**03_portfolio_performance.** Mean normalized, contribution-adjusted wealth; this is not pooled account equity. NIFTYBEES is executable fund exposure. Daily NIFTY TRI data were unavailable and no price-index substitution was made.

**04_risk_return.** Arithmetic means of investor-level annualized statistics, not an efficient frontier. Both market exposure and composition differ.

**05_drawdown.** Mean of the nine individual TWR drawdown paths. Maximum of this mean path differs from mean individual maximum drawdown reported in the tables.

**06_sector_concentration.** ETF look-through HHI is unavailable and omitted. Grandfathering and empty-account bootstrap allow observed breaches; guards do not promise universal HHI below 0.25.

**07_algorithm_runtime.** Six historical states, five repetitions per state, size and method. All use the same process and hardware; costs include feasibility witnesses and shared guard checks. Solver timings include setup. Warm caches and shared-machine load limit generalization.

**08_ablation_results.** Rank/feasibility and top-up arms use identical monthly authority and guards. V4 changes authority; neutral M changes scores and sizing preferences together. Effects interact and are not additive causal decompositions.

**09_cash_exposure.** Unapproved brokerage cash is distinct from unused approved authority. Household reserves are outside brokerage. High cash allocation can coexist with near-complete use of approved authority.
