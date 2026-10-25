# Phase 10 executed research package

Read PHASE10_FINAL_REPORT.md first. The scientific classification is **C: applied affordability-aware framework with strong original-baseline execution improvements and limited established methodological novelty**. This remains exploratory benchmark research.

## Reproduce in a fresh directory

Repository root: `/Users/tushaarbharara/Desktop/database`. The executed directory is preserved. All modules honor `INTELLIVEST_PHASE10_OUT`; never point a new run at protected Phase 7/8/9 outputs.

```sh
export INTELLIVEST_PHASE10_OUT=research/results/phase10-reproduction-2026-10-25
.venv/bin/python -m research.phase10.common
.venv/bin/python -m research.phase10.reproduce
.venv/bin/python -m research.phase10.experiment
.venv/bin/python -m research.phase10.scalability
.venv/bin/python -m research.phase10.authority
.venv/bin/python -m research.phase10.literature
.venv/bin/python -m research.phase10.analyze
.venv/bin/python -m research.phase10.validate
.venv/bin/python -m research.phase10.reports
MPLCONFIGDIR=/private/tmp/intellivest-phase10-mpl PYTHONPATH=/private/tmp/intellivest-phase9-deps .venv/bin/python -m research.phase10.figures
# Copy this explanatory README to the fresh directory before finalizing.
.venv/bin/python -m research.phase10.finalize
```

No new market download, live database access or brokerage connection is required. Dependencies already available in the research environment: Python3.14.3, NumPy2.5.3, pandas3.0.6, SciPy1.18.1 plus original backend pure-source dependencies. Plotting uses matplotlib3.11.2 from the prior temporary plotting directory (which supplies NumPy2.5.4 for plots only). Use a dedicated environment with recorded versions elsewhere. Rendering is separate from numerical simulation. Literature was verified through publisher/author pages; the source URLs/DOIs and scoped review notes are saved.

The main experiment checkpoints whole states in allocation_runs.jsonl. Use a fresh output for a clean deterministic replay. Time-limited integer outcomes and wall-clock measurements can vary; deterministic heuristic allocations and solver-certified objective values are separately checked. No claim of bit-identical timeouts, alternative optimum quantities or CPU timings is made.

PROTOCOL.json freezes objectives, caps, constraints and scaling design before the grid. ANALYSIS_CONFIGURATION.json records descriptive three-month blocks/strata separately; this is not a formal preregistration or unseen holdout. No parameter was tuned to favor V3.

## Numerical conventions and main distinctions

Amounts are INR; CSV rates are fractions; runtimes seconds; memory bytes; observed durations sessions/months as labelled. Reports convert displayed rates to percentages. Utility is ordinal score-weighted nominal purchases divided by inclusive approved budget. Sector HHI excludes cash and includes existing holdings. Empty HHI is unavailable.

F3 = at most three purchased names, one per purchased sector, with existing holdings unrestricted in count. Fwide removes those two basket constraints only. Both use the frozen combined position/sector/volatility/VaR/HHI guard and identical authority, cash, costs and eligibility. V1 remains the original baseline, with its original holding exclusions and restrictions. V3/V4 are unchanged; non-default synthetic cap cases are labelled structure sensitivity adapters.

Signal batch utilization differs from historical unique-approved-capital utilization. Valid no-trade fallback differs from feasible positive execution. A one-share signal witness without a next-session purchase can reflect execution drift/cancellation rather than a pure allocator omission. Neither high utilization nor low cash implies ranking alpha.

## Export index

- PRESERVED_HASHES.json: all 5,514 earlier research/application hashes, including the complete Phase9 package.
- PROTOCOL.json, ANALYSIS_CONFIGURATION.json, scalability_configurations.csv: fixed design and descriptive settings.
- BASELINE_REPRODUCTION.json, baseline_reproduction.csv: 27 frozen primary accounts and daily parity.
- phase9_allocation_reproduction.csv: 2,160 prior allocation/objective reproductions.
- matched_states.csv, states.npz, candidate_pools.json: exact 432 pretrade states, prices, integer holdings, covariance, sector matrix and candidate metadata.
- matched_constraints.csv, candidate_scores.csv: budgets, approval/cash limits, eligibility, scores, source history dates and price hashes.
- allocation_runs.jsonl, portfolio_allocations.csv: raw method results, including raw solver-reported statuses.
- portfolio_allocations_audited.csv, solver_certification_audit.csv: independent certification audit. One budget certificate is withheld because reported bound differs from recomputed cost by INR0.004357; the allocation is guard-compliant and unchanged.
- allocation_quantities.csv: per-security quantities, existing holdings, observed prices and inclusive costs.
- pareto_comparisons.csv, objective_measurements.csv, objective_summary.csv: identical normalized objectives and observed UD/UDB status.
- equal_constraint_summary.csv, allocation_distributions.csv: method means/medians/quantiles, coverage and certification rates.
- method_paired_differences.csv, per_profile_paired_distributions.csv: paired V3/greedy/reference/V4 comparisons. Uncertified-reference objective comparisons are unavailable rather than zero-filled.
- paired_allocation_differences.csv, statistical_comparisons.csv, synchronized_monthly_intervals.csv: state/profile effects, matching coverage and descriptive block intervals.
- stratified_outcomes.csv, V1_V3_state_execution_comparison.csv, CASE_SELECTION.json: complete positive/negative case and stratum evidence.
- rejection_accounting.csv: algorithm-specific internal rejection events and invalid returned baskets. V3 final cancellations, greedy failed one-share additions and MILP invalid relaxation incumbents are different event types and must not be compared as equivalent rejection rates.
- runtime_measurements.csv, runtime_summary.csv, memory_measurements.csv: warmed repetitions, p95/max, timeouts/status/gaps, Python-visible peaks and matrix storage. Scalability timestamps measure wall time without CPU isolation; a lightweight analysis process overlapped the initial portion. Native solver RSS and CPU model/RAM are unavailable. Synthetic 80/160 cases are computational evidence only.
- authority_transitions.csv, authority_ledger_events.csv, authority_account_outcomes.csv, v3_v4_differences.csv: logical operation/lot/ID counts, actual ledger actions and policy effects.
- authority_lifecycle_checks.csv, AUTHORITY_EXECUTION.json: twelve executed adverse/lifecycle scenarios.
- exhaustive_reference_checks.csv, VALIDATION.json: 24 brute-force tiny comparisons, including fee-induced grandfathering, and 29 focused passing checks.
- verified_references.csv, VERIFIED_REFERENCES.json, references.bib: eight verified publications, DOI metadata and overlap/novelty notes.
- claim_evidence_matrix.csv, PHASE10_RESEARCH_CLAIMS.md: supported/unsupported claims and source evidence.
- figures/: nine 300dpi PNG figures, nine editable SVGs, captions and explicit frontier/scaling qualifications.
- SOURCE_HASHES.json, source_snapshot/, ARTIFACT_INVENTORY.csv, OUTPUT_HASHES.json: exact source and output integrity.
- GIT_STATUS_BEFORE.txt, GIT_STATUS_AFTER.txt, COMPLETION.json: repository state, completed work and material remaining limitations.

## Reports

Required: PHASE10_FINAL_REPORT.md, PHASE10_EQUAL_CONSTRAINT_COMPARISON.md, PHASE10_PARETO_ANALYSIS.md, PHASE10_SCALABILITY.md, PHASE10_V3_V4_ANALYSIS.md, PHASE10_NOVELTY_ASSESSMENT.md, PHASE10_RESEARCH_CLAIMS.md and PHASE10_CONFERENCE_DRAFT.md. Supplement: PHASE10_CASE_ANALYSIS.md contains actual inputs, chosen quantities, scores and complete strata.

All 29 final checks pass. The certificate discrepancy is explicitly downgraded; no unsafe allocation or unreconciled certified-optimum claim remains. Raw development logs are preserved and superseded by VALIDATION.json plus the final audits. No unrelated frontend/browser tests were run. No application/data files were modified and no files were staged or committed.
