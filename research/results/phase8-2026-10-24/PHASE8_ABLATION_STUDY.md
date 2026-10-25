# Phase 8 ablation study

All windows were previously inspected. These are exploratory controlled mechanism comparisons, not held-out predictions. Guards are explicit additional assumptions; guard-only, feasibility-only and top-up-only controls expose this confounding rather than hiding it. No coefficients were optimized for returns.

| policy | authorized_budget_utilization | feasible_but_unexecuted | annualized_return | cvar95 | mean_hhi | topup_trades | turnover |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FEAS_ONLY | 0.29831 | 0.11111 | 0.04392 | 0.00515 | 0.13287 | 0.00000 | 0.20733 |
| GUARDS_ONLY | 0.14523 | 24.22222 | 0.02635 | 0.00310 | 0.34783 | 0.00000 | 0.12506 |
| TOPUP_ONLY | 0.35285 | 19.55556 | 0.04548 | 0.00482 | 0.33983 | 42.00000 | 0.30603 |
| V1 | 0.14523 | 24.22222 | 0.02635 | 0.00310 | 0.34783 | 0.00000 | 0.12506 |
| V2 | 0.57053 | 6.22222 | 0.05880 | 0.00666 | 0.13570 | 0.00000 | 0.34411 |
| V3 | 0.95134 | 0.33333 | 0.08614 | 0.00899 | 0.10607 | 109.55556 | 0.61157 |
| V4 | 0.99958 | 0.22222 | 0.09031 | 0.00927 | 0.10588 | 109.33333 | 0.63332 |
| V4_NO_MOMENTUM | 0.99789 | 0.22222 | 0.08897 | 0.00930 | 0.10612 | 110.22222 | 0.63332 |
| V5 | 0.99958 | 0.22222 | 0.09031 | 0.00927 | 0.10588 | 109.33333 | 0.63332 |

V2−V1 isolates the specified carry-forward authority design, not unrestricted use of starting savings. FEAS_ONLY−GUARDS_ONLY investigates candidate feasibility under the same new safeguards. TOPUP_ONLY−GUARDS_ONLY investigates categorical holding exclusion under those safeguards. V3 combines them; V4 additionally carries approvals. V5−V4 isolates purchase redirection. Selling is reported separately and cannot be credited to redirection alone. V4_NO_MOMENTUM uses the existing cached baseline score with only momentum's contribution zeroed. Candidate quality claims remain limited to the implemented historical screening/ranking, not predictive proof.

Matched resolution of the prior 218 nominal single-share witnesses:

| policy | original_witnesses | executed_now |
| --- | --- | --- |
| V1 | 218 | 0 |
| V2 | 218 | 112 |
| V3 | 218 | 215 |
| V4 | 218 | 216 |
| V5 | 218 | 216 |

Different portfolio paths can change current eligibility and risk bounds, so this is an observed matched-date/profile comparison, not a claim that every earlier witness should have been traded. Cash-interest sensitivity holds trades fixed. See ablation_results.csv, investor_level_results.csv and cash_interest_sensitivity.csv for per-investor unfavorable and neutral outcomes.
