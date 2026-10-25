# IntelliVest: Feasibility-Aware Whole-Share Portfolio Construction Under Household Affordability and Risk Constraints

Separate IEEE-style manuscript draft — exploratory research,25 October 2026. No author affiliation, acceptance status or external validation is invented.

## Abstract

Whole-share recommendations can fail even when household-approved funds remain available. We evaluate a deterministic feasibility-aware portfolio constructor that separates brokerage cash from investment authority, permits guarded existing-holding top-ups and prioritizes sector balance. Frozen historical replays across nine synthetic profiles reproduce approved-capital utilization of14.52% for the original rank-first policy and 95.13% for V3. Using432 identical decision states, we compare V3, constrained greedy and a guard-equivalent integer reference under matched financial, basket and portfolio restrictions. V3 is observed-nondominated on utility, diversification and budget fill in 98.15% of states, while greedy dominates it in 0.69%; V3 therefore presents an operational trade-off rather than universal optimality. Mean normalized utility is0.598 versus 0.946 for greedy, while HHI is0.106 versus 0.118; the coarse reference grid limits the nondominance interpretation. Controlled timing covers historical subsets and separately labelled synthetic cases up to 160 candidates. Carry-forward authority adds4.82pp utilization with additional exposure and downside. Findings support an auditable affordability-aware applied methodology; independent validation and general algorithmic novelty remain unestablished.

## I. Introduction

A stock ranking does not itself produce an executable whole-share portfolio. Expensive early candidates, exclusions of held names and quantity rounding can leave approved funds unspent. Actual brokerage cash also contains savings that a household has not authorized for investment. The research problem is to convert approved purchasing power into feasible recommendations while including existing holdings and respecting combined portfolio guards.

We contribute an explicit applied authority/feasibility workflow; a deterministic sector-priority constructor with controlled top-ups; reproduced execution and ablation evidence; and matched objective, Pareto and computational evaluations. These contributions are narrower than a new global optimization algorithm or a claim of market outperformance. RQ17–RQ22 investigate execution, utility/diversification, equal-constraint competitiveness, computational cost, carry-forward benefit and publication novelty.

## II. Related Work

Discrete transaction lots and heuristic allocation were studied by Mansini and Speranza[R1]. Cardinality-constrained frontiers and heuristic searches appear in Chang et al.[R2], while Kellerer et al.[R3] consider costs and minimum lots. Lobo et al.[R4] treat transaction costs and risk-constrained optimization; Bonami and Lejeune[R5] develop exact stochastic/integer portfolio approaches including sector restrictions. Existing-portfolio cost-aware rebalancing is addressed by Woodside-Oriakhi et al.[R6]. Mansini et al.[R7] review practical LP/MILP portfolio features, and Erwin and Engelbrecht[R8] review later metaheuristic work. These sources prevent novelty claims based merely on whole shares, constraints or heuristic search. IntelliVest's differentiation is its household-approved authority boundary and auditable applied integration; first-ever methodological originality is not established by this targeted audit.

## III. Problem Formulation


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


## IV. Proposed Methodology

Financial eligibility first determines current authority independently of brokerage savings. Candidates then enter a sector-priority scan using only historically available scores/prices. One-share combined feasibility is checked before basket admission. Existing held names are permitted under the same account/sector/risk guards as new names. At most three distinct-sector tickers enter weighted integer sizing and residual fills. The final basket is revalidated and next-session execution can reduce quantities or cancel unsafe fills. Risk controls are hard where encoded; score and sector priorities are soft preferences.

## V. Algorithm Pseudocode

```text
V3(state, observed candidates, current-month authority):
  B <- floor_cent(feedback_multiplier * min(cash, approved authority))
  retain historically observed eligible names, including existing holdings
  remove feedback-blocked sectors
  order by (current sector sleeve weight, descending score, ticker)
  additions <- zero integer vector; selected sectors <- empty
  scan order:
    if sector is new and adding one share passes budget and combined guard:
      seed one share; select ticker and sector
    stop seeding at three tickers
  for each selected ticker:
    increase toward cached inverse-volatility size-weight target
    use integer binary search under combined budget/guard
  repeat residual fills among selected tickers until no addition is possible
  validate full existing-plus-proposed basket; cancel if final check fails
  recommend selected tickers and integer quantities
At next available session close:
  use actual observed price, adverse slippage, proportional fee and split changes
  cap fills by saved batch budget, cash and unspent authority
  revalidate full guard with decision-date covariance
  debit actual inclusive cost exactly once from cash and authority
V4: same constructor and fill; carry FIFO approval lots with 12-month expiry
    and revoke all outstanding carry when household capacity deteriorates
```


V3 is a heuristic. V4 extends only the authority ledger and is not a distinct optimizer. The reference is an evaluation tool; no improved V6 is introduced into the primary comparison.

## VI. Experimental Setup

The primary data and algorithms are frozen. Nine synthetic investor profiles share a restricted40-security historical universe; the original source contains 57,400 observations. All27 primary V1/V3/V4 accounts reproduce prior summaries and daily ledgers. We capture 432 exact V3 pretrade states and reproduce2160 earlier matched outputs/objectives before new evaluation. Matched financial inputs include cash, authority, saved budget, existing holdings, sectors, observed prices, candidate ranks, lagged covariance, fees and slippage. Historical allocation calls use1.5s reference limits. We do not refit V3/V4 or select parameters using favorable outcomes.

## VII. Baselines

V1 is the preserved rank-first baseline, retaining its original held-name restriction. The primary equal-rule comparator greedily buys the first feasible next share by descending score and ticker under F3; it stops when no permitted addition exists. The reference maximizes linear score utility or inclusive deployment with exact purchase-indicator grandfathering and valid norm supporting cuts, checking all outputs against the frozen guard. Fwide sensitivity removes only the purchased-basket cardinality/distinct-sector restrictions. Phase9's conservative reference remains preserved and is not relabelled as a full-guard optimum.

## VIII. Results and Ablations

The primary full-path V1/V3 comparison reproduces14.52%/95.13% unique-authority utilization and 218/3 signal-feasible no-buy events. The latter includes next-session guard/price effects. Previously executed controlled feasible/no-topup versus V3 arms yield29.83% versus 95.13% utilization, showing substantial existing-holding contribution. Components interact; their effects are not additive causal shares.

| method | states | valid_rate | purchase_rate | mean_U_norm | mean_budget_fill | mean_HHI | mean_purchase_positions | ND_UD_rate | ND_UDB_rate |
|---|---|---|---|---|---|---|---|---|---|
| GREEDY | 432.000 | 100.000 | 100.000 | 94.607 | 98.760 | 0.118 | 2.257 | 67.824 | 76.389 |
| REF_B | 432.000 | 100.000 | 99.769 | 40.415 | 99.764 | 0.111 | 2.898 | 22.917 | 99.769 |
| REF_U | 432.000 | 100.000 | 100.000 | 95.309 | 98.993 | 0.120 | 2.162 | 100.000 | 100.000 |
| V3 | 432.000 | 100.000 | 100.000 | 59.778 | 97.430 | 0.106 | 2.870 | 97.685 | 98.148 |
| V4 | 432.000 | 100.000 | 100.000 | 59.778 | 97.430 | 0.106 | 2.870 | 97.685 | 98.148 |


Percent columns contain normalized utility, fill, feasibility and observed nondominance; HHI is unitless. Results at identical states separate allocation behavior from evolving historical exposure. V3 is best observed under balanced U/D/B in only3.01% of states and under pure diversification in 85.42%. A coarse grid caveat is material:348 V3 states have HHI below the lowest extra reference cap .10; references are not directly minimizing HHI there. V3 trades candidate utility/fill against HHI; it is not excused from unfavorable scores merely because it follows another preference. At equal authority V3 and V4 quantities are identical.

## IX. Runtime and Trade-off Analysis

The observed alternative set uses fixed HHI caps and normalized joint preferences. V3 is UD-nondominated in 97.69% and UDB-nondominated in 98.15% of matched F3 states. Greedy dominates V3 in 0.69%. These are finite-search results, not global frontier certificates. Similar-HHI and similar-utility comparisons have explicitly reported coverage.

The controlled study contains 69 cases and 828 timed calls. Historical candidates are limited to legitimate10/20/40-name subsets; larger80/160 cases are synthetic computational inputs with fixed seeds. Budget, existing positions, sectors, caps and score dispersion vary independently in an OFAT design. Latency medians/p95/max, target/purchase feasibility, solver gap/status and separate Python-visible memory appear in the accompanying scalability table and Figure5. Optimizer resource limits and differences in work prevent a generic speed-superiority conclusion. Dense risk matrices scale quadratically in storage; empirical timings do not prove polynomial complexity.

V4 adds4.82pp utilization,1.36pp invested exposure and 0.418pp annualized return, with 0.0278pp more daily CVaR and 0.377pp more drawdown on average. Lot/ID/event measurements and twelve lifecycle tests support auditability assessment, not production atomicity. It is an optional authority extension rather than an automatic default.

## X. Statistical Assessment

Per-profile paired monthly effects and synchronized three-month circular block intervals use2000 draws, seed 20261025. Shared date blocks preserve dependence across designed profiles. No dependent account-days are counted as independent people. Financial metrics inherited from reproduced Phase9 remain distinct from allocation objectives: V3/V4 return8.61%/9.03% with daily CVaR0.899%/0.927% and drawdown10.11%/10.48%. Additional deployment is not free risk reduction. No population p-values, external validation or statistically superior-return claim is made.

## XI. Threats to Validity

Surviving-universe selection, current sector labels, provider listing metadata, sparse exchange corroboration and corporate-action/ex-date dividend approximations remain. The previously inspected periods are not a holdout. NIFTYBEES data from Phase9 do not create an independent evaluation set. One solver-reported budget optimum had an INR0.004357 bound/cost discrepancy and its certificate was withheld. The reference's resource limits and finite HHI grid can miss dominating alternatives; numerical certificates apply only to the stated linear subproblem. Strict nondominance does not establish economic value. F3 is a matched basket restriction rather than the sole possible retail portfolio design. Synthetic scaling is not market performance; native solver RSS and complete hardware model information are unavailable. Household scenarios omit production persistence, live withdrawals, taxes and realistic liquidity/market-impact modeling. The targeted literature audit is not an exhaustive proof of originality.

## XII. Conclusion

Feasibility selection and controlled top-ups substantially improve the conversion of approved household authority into executable whole-share purchases relative to the original rank-first policy. Common-constraint experiments quantify a diversification/utility/deployment exchange rather than establishing universal superiority over greedy or integer optimization. The strongest defensible contribution is an auditable applied affordability-aware construction methodology with reproduced baseline improvement and transparent limits. Independent prospective data and closer domain-matched prior-art evaluation are needed for a stronger methodological claim.

## Worked historical allocation

Verified historical example: medium_moderate|2022-01-03, saved approved budget INR10000.00, actual cash INR120000.00, existing holdings 0. These are historical research inputs, not illustrative invented prices.

| method | ticker | sector | existing_quantity | purchased_quantity | observed_price | inclusive_cost |
|---|---|---|---|---|---|---|
| V3 | BRITANNIA | Consumer Goods | 0.0000 | 1.0000 | 3617.5500 | 3622.9782 |
| V3 | INFY | Information Technology | 0.0000 | 2.0000 | 1898.4500 | 3802.5972 |
| V3 | SUNPHARMA | Healthcare | 0.0000 | 3.0000 | 848.9500 | 2550.6716 |
| GREEDY | INFY | Information Technology | 0.0000 | 5.0000 | 1898.4500 | 9506.4929 |
| GREEDY | NTPC | Power | 0.0000 | 3.0000 | 126.0000 | 378.5672 |
| REF_U | HINDUNILVR | Consumer Goods | 0.0000 | 1.0000 | 2361.3000 | 2364.8432 |
| REF_U | INFY | Information Technology | 0.0000 | 4.0000 | 1898.4500 | 7605.1943 |

| method | cost | budget_fill | U_norm | HHI | purchase_positions |
|---|---|---|---|---|---|
| V3 | 9976.2469 | 99.7625 | 93.6714 | 0.3425 | 3.0000 |
| GREEDY | 9885.0601 | 98.8506 | 94.8174 | 0.9263 | 2.0000 |
| REF_U | 9970.0375 | 99.7004 | 95.8816 | 0.6381 | 2.0000 |


## Verified References

[R1] R. Mansini and M. G. Speranza, “Heuristic algorithms for the portfolio selection problem with minimum transaction lots,” *European Journal of Operational Research*, vol. 114, no. 2, pp. 219–233, 1999. DOI: [10.1016/S0377-2217(98)00252-5](https://doi.org/10.1016/S0377-2217(98)00252-5).

[R2] T.-J. Chang, N. Meade, J. E. Beasley and Y. M. Sharaiha, “Heuristics for cardinality constrained portfolio optimisation,” *Computers & Operations Research*, vol. 27, no. 13, pp. 1271–1302, 2000. DOI: [10.1016/S0305-0548(99)00074-X](https://doi.org/10.1016/S0305-0548(99)00074-X).

[R3] H. Kellerer, R. Mansini and M. G. Speranza, “Selecting Portfolios with Fixed Costs and Minimum Transaction Lots,” *Annals of Operations Research*, vol. 99, pp. 287–304, 2000. DOI: [10.1023/A:1019279918596](https://doi.org/10.1023/A:1019279918596).

[R4] M. S. Lobo, M. Fazel and S. Boyd, “Portfolio optimization with linear and fixed transaction costs,” *Annals of Operations Research*, vol. 152, no. 1, pp. 341–365, 2007. DOI: [10.1007/s10479-006-0145-1](https://doi.org/10.1007/s10479-006-0145-1).

[R5] P. Bonami and M. A. Lejeune, “An Exact Solution Approach for Portfolio Optimization Problems Under Stochastic and Integer Constraints,” *Operations Research*, vol. 57, no. 3, pp. 650–670, 2009. DOI: [10.1287/opre.1080.0599](https://doi.org/10.1287/opre.1080.0599).

[R6] M. Woodside-Oriakhi, C. Lucas and J. E. Beasley, “Portfolio rebalancing with an investment horizon and transaction costs,” *Omega*, vol. 41, no. 2, pp. 406–420, 2013. DOI: [10.1016/j.omega.2012.03.003](https://doi.org/10.1016/j.omega.2012.03.003).

[R7] R. Mansini, W. Ogryczak and M. G. Speranza, “Twenty years of linear programming based portfolio optimization,” *European Journal of Operational Research*, vol. 234, no. 2, pp. 518–535, 2014. DOI: [10.1016/j.ejor.2013.08.035](https://doi.org/10.1016/j.ejor.2013.08.035).

[R8] K. Erwin and A. Engelbrecht, “Meta-heuristics for portfolio optimization,” *Soft Computing*, vol. 27, pp. 19045–19073, 2023. DOI: [10.1007/s00500-023-08177-x](https://doi.org/10.1007/s00500-023-08177-x).

## Reproducibility

Source/configuration snapshots, matched states and constraints, candidate scores, allocation vectors, solver outcomes, frontier labels, paired effects, authority transitions, exhaustive checks, nine PNG/SVG figures and manifests accompany this draft. VALIDATION.json records29 passing focused checks and zero unresolved failures. Existing application, databases, algorithms and earlier manuscripts remain unchanged. This Markdown draft requires coauthor review and venue-specific formatting before submission.
