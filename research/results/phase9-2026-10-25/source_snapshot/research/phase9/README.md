# IntelliVest Phase 9

Isolated research benchmarks; no database mutations or live orders. Start with [the final report](../results/phase9-2026-10-25/PHASE9_FINAL_REPORT.md) and [reproduction instructions](../results/phase9-2026-10-25/README.md).

All modules honor `INTELLIVEST_PHASE9_OUT`; the default is the executed `research/results/phase9-2026-10-25` directory. Preserve existing evidence. Use a fresh output directory to replay the complete pipeline; runner.py refuses an existing RUN_CONFIG.json. Reuse the saved benchmark_sources for byte-identical inputs or document new download hashes. Frozen V1/V3/V4 policies are imported from Phase 8 unchanged.

Key files: freeze.py (integrity), reproduce.py, acquire*.py, audit.py, allocators.py, runner.py, passive.py, same_state.py, sensitivity.py, analyze.py, validate.py, figures.py and reports.py. The mathematical reference uses conservative linear grandfathering plus norm supporting cuts. Solver optimality is scoped to that encoded reference, not the entire frozen Guard feasible set.

The evidence is exploratory. High deployment is not unique to IntelliVest, ranking alpha is unproven, and carry-forward adds exposure and downside as well as returns. Read the limitations before reusing results in a paper.
