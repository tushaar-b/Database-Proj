# Phase 9 executed research artifacts

Read PHASE9_FINAL_REPORT.md first. Rate CSV values are fractions, amounts INR, runtimes seconds, durations sessions. Reports explicitly convert displayed rates to percentages. Empty/undefined values are not zero risk. All paths below are relative to this repository root.

## Reproduction in a fresh output directory

The output is immutable after finalization. Preserve it and set INTELLIVEST_PHASE9_OUT to a fresh directory for another run; the main runner refuses an existing RUN_CONFIG.json. Read-only frozen source dependencies are under research/phase8, research/diagnostics and research/*.py. No database connection is needed. Do not rerun Phase 8's CLI against original output directories.

For a fresh run first set, for example, `export INTELLIVEST_PHASE9_OUT=research/results/phase9-reproduction-2026-10-25`. This environment variable controls all Phase 9 modules. Copy saved benchmark_sources into the fresh output to reuse exact raw inputs, or repeat acquisition and record the new hashes. The missing-session official zip must also be downloaded before audit.

Executed order:

```sh
.venv/bin/python -m research.phase9.freeze
.venv/bin/python -m research.phase9.reproduce
.venv/bin/python -m research.phase9.acquire
.venv/bin/python -m research.phase9.acquire_extra
# Official missing ETF bar: exact URL and hash in benchmark_sources/ETF_CORRECTION.json
PYTHONPATH=/private/tmp/intellivest-phase9-extra .venv/bin/python -m research.phase9.audit
.venv/bin/python -m research.phase9.runner
.venv/bin/python -m research.phase9.passive
.venv/bin/python -m research.phase9.same_state
.venv/bin/python -m research.phase9.sensitivity
.venv/bin/python -m research.phase9.analyze
.venv/bin/python -m research.phase9.validate
MPLCONFIGDIR=/private/tmp/intellivest-phase9-mpl PYTHONPATH=/private/tmp/intellivest-phase9-deps .venv/bin/python -m research.phase9.figures
.venv/bin/python -m research.phase9.reports
```

Acquisition needs authorized internet. Saved raw benchmark files can be reused without redownloading; analysis uses no network. The installed application environment already supplied NumPy, pandas, SciPy and yfinance. Matplotlib and xlrd were installed only in temporary directories, leaving repository dependency/environment files unchanged. Environment versions are in RUN_CONFIG.json and ENVIRONMENT.json. Future recreations should use a separate virtual environment and pinned recorded versions.

## Tables

- strategy_configuration.csv: frozen policy switches, name, carry regime.
- historical_universe_metadata.csv, DATA_AUDIT.json, etf_exchange_checks.csv: identifiers, dates, actions, source/verification limits.
- accounts/: per-window/profile/policy valuations, decisions, trades, authority events, fills, episodes and runtimes.
- benchmark_trades.csv and etf_accounts/trades.csv: every executed quantity, decision/execution date, fee/slippage and top-up flag.
- portfolio_valuations.csv and etf_accounts/valuations.csv: daily account cash/equity/returns and authority stocks.
- allocation_decisions.csv, allocation_utilization.csv: budgets, proposal/execution quantities, eligible/affordable counts and remaining authority.
- feasible_but_unexecuted.csv: compliant signal-date one-share witnesses without actual buys.
- cash_authority_accounting.csv: unique grants/spending/expiry/revocation, unused approved cash, other brokerage cash and protected-reserve distinction.
- investor_level_performance.csv, etf_investor_performance.csv, all_investor_performance.csv, portfolio_risk.csv: per-profile/window outcomes and risk coverage.
- benchmark_summary.csv: nine-profile primary descriptive means and Sharpe distribution.
- same_state_allocation_quality.csv: common-state objective/cost/quantities and solver status; no realized-return objective.
- algorithm_runtimes.csv: every main allocator invocation, including feedback counterfactual calls (override flag).
- controlled_algorithm_runtimes.csv: five repetitions, six historical states, sizes10/20/40; quantities verify timing repeatability.
- sensitivity_accounts/: complete raw cost/universe/shock replay ledgers.
- ablation_outcomes.csv, sensitivity_outcomes.csv, cash_yield_sharpe_sensitivity.csv: component, cost, universe, shock and frozen-trade cash-yield sensitivities.
- statistical_comparisons.csv, synchronized_temporal_intervals.csv: per-profile paired effects and shared-date temporal intervals.
- exposure_matched_comparisons.csv, equity_sleeve_metrics.csv: sleeve diagnostics, matching coverage and uncertainty.
- equal_weight_deviation.csv: daily actual equal-weight target deviation from independent holdings reconstruction.
- window_robustness.csv: means/medians/ranges across the original windows.

Important: algorithm_runtimes.csv's objective uses the full original pool rank and is only instrumentation. The common eligible-set objective for valid cross-method quality comparisons is computed explicitly in same_state_allocation_quality.csv. These score scales must not be mixed. Runtime call counts include feedback counterfactual evaluations; account counts do not.

## Integrity

PRESERVED_HASHES.json protects earlier evidence and application source; FROZEN_REPRODUCTION.json records numerical reproduction; RUN_CONFIG.json records inputs and primary code hashes; FINAL_SOURCE_HASHES.json and source_snapshot/ record all final Phase 9 code; OUTPUT_HASHES.json covers generated artifacts. VALIDATION.json and validation_final.log give the final focused executed checks; earlier validator development logs are superseded. GIT_STATUS_BEFORE.txt and GIT_STATUS_AFTER.txt are workspace-scoped. No files are staged or committed.

The original sensitivity draft had a literal-replacement ordering error caught during implementation review. The corrected placeholder-based cost adapter was executed to produce sensitivity_outcomes.csv; sensitivity_final.log is the final run. The primary grid never used the sensitivity adapter. No frozen V1/V3/V4 defect or modification was introduced.
