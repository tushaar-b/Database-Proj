# Diagnostic output index

- INITIAL_ROOT_CAUSE_REPORT.md: inspection findings and fixed design before implementation.
- ROOT_CAUSE_ANALYSIS.md / UPDATED_RESEARCH_REPORT.md: validated interpretation and executed comparisons.
- FEEDBACK_TRACE.csv / FEEDBACK_EVENT_OPPORTUNITIES.csv: one row per effective event and every actual opportunity while active.
- REPLAY_DIAGNOSTICS.csv: full policy/candidate/quantity/cash snapshots per decision; fixed-policy same-state counterfactuals.
- SHARPE_DIAGNOSTICS.csv / SHARPE_DISTRIBUTION.csv: investor-first metrics, conventions, validity and distributions.
- CASH_UTILIZATION.csv / CASH_PROFILE_SUMMARY.csv: per-decision disjoint authorization and per-profile unique funding.
- SENSITIVITY_RESULTS.csv: profile-level controlled cash/benchmark/authorization dimensions.
- HHI_DIAGNOSTICS.csv / EXPOSURE_MATCHED_COMPARISONS.csv / EXPOSURE_STRATA.csv: valid-session concentration and descriptive exposure controls.
- UNCERTAINTY.csv: paired conditional moving-block intervals, with sparse comparisons flagged unavailable.
- CONFERENCE_INTERPRETATION.md: claim-level qualifications without overwriting previous drafts.
- figures/: six PNG/SVG figures and captions.

Run from repository root with the repository plus matplotlib dependencies. The initial report/hash manifest must exist before executing `python -m research.diagnostics.runner --out <new-directory>`. The runner refuses an existing DIAGNOSTIC_CONFIG.json. Frozen reference paths and settings are in DIAGNOSTIC_CONFIG.json. Original stock trades are kept fixed in cash-interest overlays. All profile monetary units are INR; return, risk, exposure and frequency values are fractions; event latency is observed sessions; undefined values are blank/NA, not zero. See source_snapshot for the exact code. No live database access is performed.
