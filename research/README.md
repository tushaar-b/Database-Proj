# IntelliVest comparative historical research

Read `specification.md` before interpreting results. This directory is isolated from application user tables. No UI or authentication changes are required. The only database connection is the audit's server-enforced read-only market snapshot; replay reads local CSV files and never calls mutation endpoints.

From the repository root, with repository and research dependencies installed:

```sh
.venv/bin/python -m research.data_audit --out research/data/2026-10-23
.venv/bin/python -m research.validate_dataset --data research/data/2026-10-23
.venv/bin/python -m research.experiment_runner --data research/data/2026-10-23 --out research/results/2026-10-23-run01
```

Acquisition uses network access to Yahoo and NSE and does not insert into PostgreSQL. It has no synthetic fallback. To reproduce a frozen run, retain the raw/data CSV files and hashes and run only the third command with a new output directory. The audit can recompute legacy checks offline with `--offline`; exchange validation reuses cached raw ZIPs. Data has applicable provider usage restrictions and is for this local research study; a download is not a redistribution license.

`research/results/<run>/config.json` records code/dataset hashes, parameters, scenario assumptions, source versions and seed. Capture the working source files as well as Git HEAD because the surrounding repository may already be dirty. Principal results have exactly four policies. Ablations and cost sensitivities are separately labeled by `kind` in detailed outputs. All results retain unsuccessful and unfavorable outcomes.

`consistency_checks` executes synthetic mathematical fixtures solely to check accounting, delays, splits, time-weighted returns, policy isolation and future-price exclusion. They are never presented as historical financial evidence. The experiment runner refuses datasets that have not passed the admission checks. Conditional moving-block intervals describe uncertainty on observed paired time series; they do not establish efficacy across independent investors or markets.

Output CSVs include trades, positions, daily valuations and estimates, monthly decisions with ranking evidence, policy changes, breach episodes, principal summaries, subgroups, paired differences, momentum and cost sensitivity. Figures have PNG and SVG versions with captions. `CONFERENCE_RESULTS_DRAFT.md` is separate from the unchanged conference PDFs.

The final recorded run also includes a separately labelled `feedback_stress` extension and a frozen source snapshot. Use `--frozen-config research/results/<run>/config.json` to restore its effective nonsecret research settings. This stress was added after the first run's primary null feedback effect; it is a mechanism probe, not a replacement central comparison. Earlier runs are preserved and explicitly marked superseded when additional identity exclusions change the admitted universe.

Metrics and units: return/risk/violation/cash/HHI rates are fractions (multiply by 100 for percent except HHI); monetary amounts are INR; time and breach duration are observed trading sessions; turnover is total one-way purchase notional / mean daily equity; undefined values are blank/NA, not zero. Detailed formulas and episode censoring are in the specification. No-purchase and unused-capacity metrics are aggregated per scheduled decision. Surplus utilization can exceed one in Risk Only because pre-existing savings are spendable. Realized and in-sample risk are separate columns.
