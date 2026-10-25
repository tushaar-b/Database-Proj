# Publication claim–evidence matrix

Exploratory evidence from nine synthetic investor profiles and previously examined historical paths. No independent holdout, unbiased point-in-time universe or population-level investor inference is established.

| claim | numerical_evidence | source_CSV_or_report | figure | assumptions | assessment | qualification | independent_validation_absent |
|---|---|---|---|---|---|---|---|
| Approved-capital deployment improves over original rank-first | V1 14.52%, V3 95.13%; +80.61pp; next-session no-buy witnesses218→3 | baseline_reproduction.csv; Phase9 benchmark_summary.csv | 01;02 | Original synthetic profiles; monthly authority; fees10bp/slip5bp | supported | Combined feasibility/top-up/guard policy effect, not isolated algorithm novelty | 1.000 |
| Controlled top-ups support recurring execution | Feasible/no-topup29.83%→V3 95.13%; +65.30pp | Phase9 ablation_outcomes.csv | 01 | Frozen feasible constructor, monthly authority | supported | Effect interacts with feasibility and changes exposure | 1.000 |
| V3 offers diversification/utility trade-offs | F3 ΔHHI=-0.012113; ΔU/B=-0.348281; ND UDB=98.15% | paired_allocation_differences.csv; pareto_comparisons.csv | 03;04;08 | Observed finite candidate set; all matched guards | supported conditionally | Not global Pareto; utility sacrifice and dominating cases retained | 1.000 |
| V3 universally dominates greedy | Greedy dominates V3 on UDB in 0.69% of states | paired_allocation_differences.csv | 03;08 | Common F3 set and normalized objectives | unsupported | No universal allocation or return superiority | 1.000 |
| Low computational latency | See measured medians/p95/max by size and input complexity | runtime_summary.csv; memory_measurements.csv | 05 | Same local process; warmed calls; timed solver resource cap | supported locally | Native solver memory unavailable; heuristic/reference work differs | 1.000 |
| V4 provides extra deployment | +4.82pp utilization; +1.36pp exposure; +0.0278pp daily CVaR | v3_v4_differences.csv; authority_transitions.csv | 07 | Same constructor; monthly versus carry authority | supported | Optional policy; no default deployment justification | 1.000 |
| Financial affordability and guarded feasibility preserved | 7344 returned allocations checked; 29 focused checks passed | VALIDATION.json; portfolio_allocations.csv | 09 | Tested states; includes labelled zero-purchase fallbacks | supported in tested cases | Not a universal theorem; bootstrap and grandfathering explicit | 1.000 |
| Novel general-purpose optimization algorithm | Existing discrete/cost/cardinality/sector prior art verified | verified_references.csv; PHASE10_NOVELTY_ASSESSMENT.md | none | Targeted literature audit | not established | Position as applied methodology/experimental framework | 1.000 |
| Independent validation or population superiority | No independent holdout; nine designed profiles share market paths | PROTOCOL.json; PHASE9_DATA_AUDIT.md | all | Restricted exposed surviving-security universe | unsupported | Requires prospective or genuinely unexamined independent evidence | 1.000 |


Recommended claim: “Feasibility-aware selection and controlled top-ups substantially improve conversion of household-approved investment authority into executable whole-share purchases relative to the original rank-first policy, while preserving the tested affordability and portfolio guards. Matched comparisons quantify the resulting utility–diversification trade-offs rather than establishing universal optimization superiority.”
