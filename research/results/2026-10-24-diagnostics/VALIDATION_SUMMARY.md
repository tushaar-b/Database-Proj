# Completion and numerical validation

- 42 original/stress comparisons reproduced the prior summary metrics, numeric daily ledgers and monthly baskets.
- 36 alternative-authority replays completed, yielding 78 controlled replays in total. The additional independent alternative replay is a verification, not another distinct experimental configuration.
- 372 frozen-trade cash-accounting paths and 744 investor/cash/benchmark-convention records were calculated. These are not claimed as 372 new trading backtests.
- 27 focused checks and 26 independent checks passed (53 total listed checks).
- All 80 protected input files are byte-for-byte unchanged, including every run03 output, the existing conference draft, the historical dataset and inspected application/source files.
- No database connection, UI automation, frontend tests, user-account changes, selling or forced liquidation was performed.
- Conditional moving-block intervals retain fixed seeds and shared market dates; eight sparse exposure comparisons are explicitly unavailable rather than assigned invented intervals.
- All six final PNG figures were visually reviewed, with SVG equivalents retained.

The raw reproduction summary retains legacy `hhi_breach_frequency` for exact old-result matching. The new canonical diagnostic frequency is `HHI_DIAGNOSTICS.csv:corrected_valid_hhi_breach_frequency`, with defined/undefined counts. Cross-profile means and pooled valid-session rates are separately listed in HHI_AGGREGATION.csv. Outside-household savings balances were not simulated and are NA; zero additional transfer is an explicit model assumption, not a measured savings balance.

Source snapshots identify the initial execution. POSTPROCESSING_MANIFEST.json separately records attribution/reporting refinement and certifies that simulation, Sharpe, interest-path, exposure-comparison and statistical CSV hashes did not change. Active-versus-initial-fixed policy effects are distinct from hypothetical persistence of the immediately previous restriction. Verification source is separately archived. The separate interpretation document does not overwrite any previous paper.

Reproduction commands are in research/diagnostics/README.md. Original protected input paths must remain available. No commit was created; the pre-existing dirty working tree was preserved.
