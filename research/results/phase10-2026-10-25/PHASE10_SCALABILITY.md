# Controlled runtime and memory study

## Scope and hardware

69 input cases: 18 historical subset cases and 51 synthetic OFAT cases. Each case/method has one warm-up, three timed repeats and one separate memory call: 828 timed calls, 276 warm-ups and 276 instrumented memory calls. Four methods are greedy, V3, V4 at equal authority and the Phase 10 exact-guard utility reference. The historical experiment finished before this single-process timing study started. No network or historical acquisition occurs inside timed calls.

Platform: macOS-27.0.1-arm64-arm-64bit-Mach-O; architecture arm64; logical CPU count 10. CPU brand and installed RAM could not be read under the sandbox, so no model is invented. Python/software versions are in SCALABILITY_EXECUTION.json. CPU frequency, pinning, thermal state and native solver RSS are uncontrolled. A lightweight analysis process overlapped the initial timing portion; these are wall-clock observations without CPU isolation, especially limiting interpretation of small heuristic timing differences. Timings are empirical and environment-specific.

## Candidate-size results

Median/p95/maximum columns below are milliseconds. Valid rate includes a no-trade fallback; purchase rate is separate. Certified rate applies to the reference's linear objective only. Timeouts and gaps must accompany runtime comparisons because a 0.5s capped solve can return less allocation quality.

| kind | candidate_count | method | measurements | median_seconds | p95_seconds | maximum_seconds | valid_rate | purchase_rate | timeout_rate | certified_rate |
|---|---|---|---|---|---|---|---|---|---|---|
| historical_subset | 10.0000 | GREEDY | 18.0000 | 0.5065 | 1.8088 | 1.8210 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| historical_subset | 10.0000 | REFERENCE | 18.0000 | 11.4196 | 166.6014 | 167.1226 | 100.0000 | 100.0000 | 0.0000 | 100.0000 |
| historical_subset | 10.0000 | V3 | 18.0000 | 0.5333 | 0.8798 | 0.9609 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| historical_subset | 10.0000 | V4 | 18.0000 | 0.5202 | 0.8705 | 0.8753 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| historical_subset | 20.0000 | GREEDY | 18.0000 | 0.7941 | 2.4550 | 2.4731 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| historical_subset | 20.0000 | REFERENCE | 18.0000 | 27.0795 | 226.8092 | 242.8859 | 100.0000 | 100.0000 | 0.0000 | 100.0000 |
| historical_subset | 20.0000 | V3 | 18.0000 | 0.7591 | 1.2411 | 1.3834 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| historical_subset | 20.0000 | V4 | 18.0000 | 0.7554 | 1.1057 | 1.1095 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| historical_subset | 40.0000 | GREEDY | 18.0000 | 1.3749 | 4.1092 | 4.2474 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| historical_subset | 40.0000 | REFERENCE | 18.0000 | 39.6322 | 176.4158 | 176.5683 | 100.0000 | 100.0000 | 0.0000 | 100.0000 |
| historical_subset | 40.0000 | V3 | 18.0000 | 1.2538 | 2.2646 | 2.4424 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| historical_subset | 40.0000 | V4 | 18.0000 | 1.2165 | 2.2767 | 2.3575 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| synthetic_OFAT | 10.0000 | GREEDY | 9.0000 | 1.0555 | 1.2276 | 1.2385 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| synthetic_OFAT | 10.0000 | REFERENCE | 9.0000 | 52.9783 | 68.4157 | 68.6015 | 100.0000 | 100.0000 | 0.0000 | 100.0000 |
| synthetic_OFAT | 10.0000 | V3 | 9.0000 | 0.6576 | 0.8475 | 0.8949 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| synthetic_OFAT | 10.0000 | V4 | 9.0000 | 0.6552 | 0.7021 | 0.7038 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| synthetic_OFAT | 20.0000 | GREEDY | 9.0000 | 0.7297 | 1.9236 | 2.0680 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| synthetic_OFAT | 20.0000 | REFERENCE | 9.0000 | 94.7009 | 266.7469 | 268.0583 | 100.0000 | 100.0000 | 0.0000 | 100.0000 |
| synthetic_OFAT | 20.0000 | V3 | 9.0000 | 0.7786 | 1.1403 | 1.1516 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| synthetic_OFAT | 20.0000 | V4 | 9.0000 | 0.7755 | 1.4408 | 1.4422 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| synthetic_OFAT | 40.0000 | GREEDY | 9.0000 | 3.8445 | 5.2127 | 5.2464 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| synthetic_OFAT | 40.0000 | REFERENCE | 9.0000 | 170.6234 | 217.8758 | 237.1050 | 100.0000 | 100.0000 | 0.0000 | 100.0000 |
| synthetic_OFAT | 40.0000 | V3 | 9.0000 | 1.6245 | 1.7680 | 1.7928 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| synthetic_OFAT | 40.0000 | V4 | 9.0000 | 1.6051 | 1.6987 | 1.6995 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| synthetic_OFAT | 80.0000 | GREEDY | 9.0000 | 6.7683 | 9.0653 | 9.5603 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| synthetic_OFAT | 80.0000 | REFERENCE | 9.0000 | 123.2406 | 499.8678 | 505.4629 | 100.0000 | 100.0000 | 11.1111 | 88.8889 |
| synthetic_OFAT | 80.0000 | V3 | 9.0000 | 2.7568 | 3.5544 | 3.5871 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| synthetic_OFAT | 80.0000 | V4 | 9.0000 | 2.6648 | 3.7106 | 3.8152 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| synthetic_OFAT | 160.0000 | GREEDY | 9.0000 | 6.8392 | 8.1516 | 8.1517 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| synthetic_OFAT | 160.0000 | REFERENCE | 9.0000 | 511.9593 | 536.9890 | 546.8935 | 100.0000 | 0.0000 | 100.0000 | 0.0000 |
| synthetic_OFAT | 160.0000 | V3 | 9.0000 | 5.0060 | 5.8318 | 5.8669 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |
| synthetic_OFAT | 160.0000 | V4 | 9.0000 | 4.9207 | 5.2108 | 5.2412 | 100.0000 | 100.0000 | 0.0000 | 0.0000 |


## Independent complexity factors

The center is n40, approved budget INR10000, five existing holdings, ten sectors, position cap .20, sector cap .35 and score dispersion 1. OFAT alternatives change budget 1000/100000, holdings 0/20, sectors 3/16, position caps.10/.30, sector caps.20/.50 and dispersion.01/2, using three fixed seeds101/202/303. All non-size results are in runtime_summary.csv and configurations in scalability_configurations.csv. No factorial interaction or universal asymptotic claim follows from this OFAT design.

Historical subsets have 10/20/40 candidates but retain the complete 40-name holding/covariance matrix. Synthetic80/160 have actual larger matrices. Synthetic prices, scores and covariance are used solely to test computation and constraints; no synthetic return or investment-performance claim is made. Score dispersion is a positive scaling preserving order; the ordinal objective and V3 ordering are invariant to that transformation by design, which is reported rather than interpreted as financial robustness. Non-default cap tests use a separately labelled V3-structure guard-parameter adapter; the frozen V3 primary policy is unchanged.

## Memory

| candidate_count | method | median_python_peak_KiB | input_matrix_KiB |
|---|---|---|---|
| 10.000 | GREEDY | 4.102 | 1.719 |
| 10.000 | REFERENCE | 51.285 | 1.719 |
| 10.000 | V3 | 10.547 | 1.719 |
| 10.000 | V4 | 10.734 | 1.719 |
| 20.000 | GREEDY | 5.273 | 5.000 |
| 20.000 | REFERENCE | 131.373 | 5.000 |
| 20.000 | V3 | 15.000 | 5.000 |
| 20.000 | V4 | 15.070 | 5.000 |
| 40.000 | GREEDY | 7.602 | 16.250 |
| 40.000 | REFERENCE | 413.179 | 16.250 |
| 40.000 | V3 | 23.648 | 16.250 |
| 40.000 | V4 | 23.648 | 16.250 |
| 80.000 | GREEDY | 12.820 | 57.500 |
| 80.000 | REFERENCE | 1455.037 | 57.500 |
| 80.000 | V3 | 41.695 | 57.500 |
| 80.000 | V4 | 41.695 | 57.500 |
| 160.000 | GREEDY | 23.422 | 215.000 |
| 160.000 | REFERENCE | 5484.113 | 215.000 |
| 160.000 | V3 | 82.680 | 215.000 |
| 160.000 | V4 | 82.680 | 215.000 |


These are Python-visible tracemalloc peaks from separate instrumented calls, not full process memory or native HiGHS RSS. Dense input matrices are reported separately and can already be allocated before the call. Memory timing is excluded from latency distributions.

## Complexity limits

Dense covariance storage is O(n²) and a full guard evaluation costs O(n²+s*n). Greedy's repeated one-share scans are pseudopolynomial in share budget, with up to O(Q*n) attempted additions. V3 sorts and checks seeds, then searches quantities for at most three names; residual loops and dense guards prevent an unsupported blanket polynomial-time claim in binary input length. Binary MILP branch-and-bound has no claimed polynomial bound. Norm outer approximation and time limits are implementation controls, not a new complexity theorem. A faster heuristic and an optimizing reference do different work; latency alone does not establish optimization superiority.
