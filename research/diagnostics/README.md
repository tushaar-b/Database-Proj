# Controlled diagnostics

These modules operate on frozen CSV market data and synthetic portfolio states. They do not connect to a database or write to the original run, original conference draft, application source or market dataset.

The completed execution is `research/results/2026-10-24-diagnostics/`. Its initial root-cause report and protected-input manifest were written before implementation. It contains 78 replays, 372 frozen-trade cash-accounting paths and 744 investor/convention metric records. Cash paths are accounting sensitivities, not additional stock-trading experiments.

To reproduce in a fresh directory from the same protected input files, from the repository root:

```sh
mkdir -p research/results/diagnostics-reproduction
cp research/results/2026-10-24-diagnostics/INITIAL_ROOT_CAUSE_REPORT.md research/results/diagnostics-reproduction/
cp research/results/2026-10-24-diagnostics/PRESERVED_INPUT_HASHES.json research/results/diagnostics-reproduction/
.venv/bin/python -m research.diagnostics.runner --out research/results/diagnostics-reproduction
.venv/bin/python -m research.diagnostics.postprocess --out research/results/diagnostics-reproduction
.venv/bin/python -m research.diagnostics.verify --out research/results/diagnostics-reproduction
```

Install the repository/research dependencies in a suitable isolated environment. Exact executed package versions appear in DIAGNOSTIC_CONFIG.json. For this local execution, plotting dependencies were loaded with `PYTHONPATH=/private/tmp/intellivest-research-deps` to preserve the application environment; prepend that setting to the commands while those temporary dependencies exist.

The runner refuses an output directory with an existing DIAGNOSTIC_CONFIG.json. Postprocessing explicitly separates active-versus-initial-fixed policy effects from counterfactual persistence of the previous restriction, identifies unmodeled outside-household balances as NA, and regenerates tables/figures without changing financial/statistical CSVs. Its code and input hashes are separately archived. The verifier adds synthetic mathematical fixtures only, validates all observed account identities and reproduces an alternative cash-authority replay, frozen-trade overlay and fixed-seed interval.

Do not equate effective policy transitions, internal eligibility changes, final orders, execution differences and subsequent risk correction. Do not equate mean investor Sharpe with composite-return Sharpe. Cash authorization stages sum at each decision, but their sum across decisions is not unique capital. HHI is defined only on invested equity and excludes cash. Definitions, censoring and assumptions are in the initial and completed reports.
