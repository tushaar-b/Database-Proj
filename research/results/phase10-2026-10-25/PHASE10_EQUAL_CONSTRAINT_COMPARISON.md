# Equal-constraint algorithmic comparison

Exploratory evidence from nine synthetic investor profiles and previously examined historical paths. No independent holdout, unbiased point-in-time universe or population-level investor inference is established.

## Audit and common feasible sets

The Phase 9 reference suppressed unchanged positions near fee-induced cap crossings through conservative linear grandfathering. Phase 10 preserves that implementation and adds a separately named guard-equivalent reference with binary purchase indicators. Both primary F3 and wide sensitivity use identical budget, cash, top-up permissions, sector exclusions, prices, ordinal scores, covariance, costs and original portfolio guard. A reference can still differ because it solves a linear objective while V3 follows sector-priority sizing. V3's .20/.35 caps are account-equity constraints, not equity-sleeve ceilings. V1 retains original held-name exclusions and original policy restrictions; it is the original-baseline contrast rather than an equal-rule optimality competitor.

F3 makes max three purchased tickers and one purchased ticker per sector common hard restrictions. Fwide removes both. No limit is imposed on existing holdings count. V3 and V4 remain frozen; their voluntary basket rule is unchanged. Every returned allocation, including fallback no-trade portfolios, is independently checked. Failed HHI-target searches are not counted as feasible positive allocations. Reference status/gaps retain the difference between a linear-relaxation solve and a full-guard certificate.

## Matched F3 results

Percent columns: valid/purchase rates, normalized utility, budget fill and nondominance rates. HHI and number of positions are unscaled. Means condition on exact V3 historical states rather than different policy paths.

| method | states | valid_rate | purchase_rate | mean_U_norm | mean_budget_fill | mean_HHI | mean_purchase_positions | ND_UD_rate | ND_UDB_rate |
|---|---|---|---|---|---|---|---|---|---|
| GREEDY | 432.000 | 100.000 | 100.000 | 94.607 | 98.760 | 0.118 | 2.257 | 67.824 | 76.389 |
| REF_B | 432.000 | 100.000 | 99.769 | 40.415 | 99.764 | 0.111 | 2.898 | 22.917 | 99.769 |
| REF_U | 432.000 | 100.000 | 100.000 | 95.309 | 98.993 | 0.120 | 2.162 | 100.000 | 100.000 |
| V3 | 432.000 | 100.000 | 100.000 | 59.778 | 97.430 | 0.106 | 2.870 | 97.685 | 98.148 |
| V4 | 432.000 | 100.000 | 100.000 | 59.778 | 97.430 | 0.106 | 2.870 | 97.685 | 98.148 |


V3 minus constrained greedy: normalized utility -0.348281, budget fill -0.013301, posttrade HHI -0.012113. Lower HHI is better. These are paired state means, not nine-profile independent samples. Greedy dominates V3 on utility/diversification/budget in 0.69% of states. V3's mean ratio to certified unconstrained-F3 utility optima is 62.55% over 432 covered states; this denominator excludes uncertified/resource-limited results. The original Phase 9 62.39% remains preserved as a wider conservative-reference comparison.

## Identical objectives and distributions

The full objective family and numerical preferences are defined in PROTOCOL.json. Candidate utility, pure utilization, diversification and joint U/D/B scalar scores are computed for every method in objective_measurements.csv. objective_summary.csv gives mean, median, observed-best fraction and regret to the best evaluated allocation. A best-observed scalarization is not a globally solved nonlinear objective. Quantiles and per-profile/stratum data are retained; the pure utility/budget reference is certified only where solver status explicitly permits it.


For investor $u$ and decision $t$, let $h_i\in\mathbb Z_+$ denote existing holdings, $p_i>0$ the observed nominal close, $q_i\in\mathbb Z_+$ new shares, $C$ actual brokerage cash, and $A$ approved unspent authority. Household buffer $F_u=\max(0,I_u-M_u-R_u)$ excludes mandatory expenditure and protected reserve; this is the frozen research rule, which does not separately subtract the scenario's discretionary field. Tier capacity $a_u\in\{.25,.50,.75\}$ gives unique monthly approval $G_{u,t}=\lfloor100a_uF_u\rfloor/100$. Existing brokerage savings receive no automatic approval. With frozen feedback multiplier $\rho_t$,

$$ B=\lfloor100\rho_t\min(C,A)\rfloor/100,\qquad c_i=p_i(1+.0005)(1+.001),\qquad K(q)=\sum_i c_iq_i\le B. $$

Hard financial restrictions are $K\le C$, $K\le A$, no borrowing, no negative holdings, no fractional shares and no protected-reserve spending. Let $\mathcal E_t$ be the cached observed eligible set after sector feedback; $q_i=0$ outside it. V3 permits controlled top-ups, so held eligible names remain available.

Write $v_i=h_ip_i$, $v'_i=(h_i+q_i)p_i$, $E=C+\sum_i v_i$, and $E'=C-K+\sum_i v'_i$. For sector incidence $S$ the frozen portfolio guard requires

$$v'_i\le\max(.20E',v_i),\qquad(Sv')_s\le\max(.35E',(Sv)_s).$$

Sector concentration is equity-only:

$$H(v')=\sum_s\left(\frac{(Sv')_s}{\sum_i v'_i}\right)^2.$$

It is undefined with no invested holdings; cash is never an artificial sector. If a pretrade sleeve exists, $H(v')\le\max(.25,H(v))$. Empty-account bootstrap skips this HHI ceiling. The guard permits existing concentration to persist, so neither .25 HHI nor .35 sector share of the equity sleeve is a universal posttrade bound. The .35 ceiling is a fraction of total account equity, not of equity holdings alone.

With point-in-time 30-return covariance $\Sigma_t$ and $w=v/E$, $w'=v'/E'$,

$$\sqrt{{w'}^T\Sigma_tw'}\le\max(.03,\sqrt{w^T\Sigma_tw}),$$
$$1.645\sqrt{{w'}^T\Sigma_tw'}\le\max(.10,1.645\sqrt{w^T\Sigma_tw}).$$

There is no hard CVaR limit. CVaR remains a separate historical outcome. Feedback can reduce $B$ and block the currently largest sector when equity HHI is breached.

The primary matched feasible set F3 additionally imposes $|\{i:q_i>0\}|\le3$ and at most one purchased ticker per sector. These are frozen V3 basket choices made hard for every comparator. Existing holdings are not limited to three. Fwide removes only these two purchased-basket restrictions, retaining all other restrictions; V3 still voluntarily selects at most three.

For common eligible rank $r_i$ among $m$ names, descending score then ticker, define $s_i=(m-r_i+1)/m$ and

$$ U=\sum_i s_ip_iq_i,\quad \bar U=U/B,\quad D=1-H(v'),\quad Z=K/B. $$

Components are bounded on a common scale without outcome-fitted standardization: $\bar U,Z\in[0,1]$ and defined $D\in[0,1]$. $s_i$ evaluates ordering rather than raw score magnitude; it is not a forecast of realized return. Preferences fixed before the grid were $(\alpha,\beta,\gamma)=(1,0,0),(.75,.25,0),(.5,.5,0),(.25,.75,0),(0,1,0),(0,0,1),(1/3,1/3,1/3)$ for

$$J=\alpha\bar U+\beta D+\gamma Z.$$

Every method is scored identically under every $J$. V3 does not globally optimize $J$. Pure-utility/budget scores remain defined when the empty portfolio's HHI is unavailable; any objective with positive diversification weight is undefined in that case.

The Phase 10 reference solves max $U$ and max $K$ linear objectives over the common set; max $U$ is also solved at prespecified HHI caps .35,.25,.20,.15,.10. Binary purchase indicators encode the grandfathering disjunction: an unchanged position/sector can remain at its prior nominal value, whereas any enlargement must satisfy the account ceiling. With a PSD covariance factor $L$, HHI and volatility are expressed as norm inequalities and enforced with valid supporting-hyperplane cuts in successive linear MILPs. A returned point is labelled certified only if the linear MILP terminates optimally and the allocation passes the full frozen guard, target and common basket constraints. That supplies a numerical certificate for its stated linear objective and epsilon subproblem, not a global Pareto or nonlinear scalar-objective certificate. Historical calls have 1.5s and 100-cut limits; scalability calls have 0.5s. Failed calls return an explicitly labelled no-trade fallback, which is not presented as a successful positive-purchase solution.


## Solver coverage

One budget solve reported optimality but its bound differed from actual inclusive cost by INR0.004357. Its certificate is explicitly withheld under the independent rtol1e-7/atol1e-5 audit. Raw allocations/status are preserved in portfolio_allocations.csv; portfolio_allocations_audited.csv and solver_certification_audit.csv expose the downgrade. No purchase or objective was changed.

| mode | solver_status | calls |
|---|---|---|
| F3 | feasible_limit | 326.000 |
| F3 | infeasible_positive_purchase | 70.000 |
| F3 | optimal_full_guard | 2544.000 |
| F3 | solver_1 | 4.000 |
| F3 | solver_reported_optimal_bound_discrepancy | 1.000 |
| F3 | time_limit | 79.000 |
| Fwide | feasible_limit | 370.000 |
| Fwide | numerical_guard_rejection_ | 1.000 |
| Fwide | optimal_full_guard | 493.000 |


Do not infer integer-program failure from a legitimate HHI-infeasible target, or feasibility from a valid zero-purchase fallback. Solver runtime caps limit the observed alternative set. Target-feasible positive purchases and all returned guard-compliant outputs are separate columns. Rejection counters have different event meanings: failed greedy one-share attempts, V3 final-basket cancellations, and invalid MILP relaxation incumbents. They must not be compared as equivalent rates. Rejected internal MILP relaxations are expected during outer approximation; they are never emitted as valid purchases.
