"""Evidence-linked reports and a separate IEEE-style Markdown manuscript."""
import json,re
from pathlib import Path
import numpy as np,pandas as pd
from research.phase10.common import OUT,P9,load_states,verify

def table(f,cols=None,percent=(),digits=3):
    f=f.copy() if cols is None else f[cols].copy()
    for c in f:
        if c in percent:f[c]=f[c]*100
        if pd.api.types.is_numeric_dtype(f[c]):f[c]=f[c].map(lambda x:'unavailable' if pd.isna(x) else f'{x:.{digits}f}')
        else:f[c]=f[c].fillna('unavailable').astype(str)
    return '| '+' | '.join(f.columns)+' |\n|'+'|'.join(['---']*len(f.columns))+'|\n'+'\n'.join('| '+' | '.join(row)+' |' for row in f.values)+'\n'
def write(name,s):
    s=re.sub(r'\b(at|from|to|in|over|across|contains|has|capture|cover|versus|seed|with|and|budget|holdings|sectors|dispersion|March|January|October)(?=\d)',r'\1 ',s)
    (OUT/name).write_text(s.strip()+'\n')
FORMULATION=r'''
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
'''
PSEUDOCODE='''```text
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
'''

def main():
    R=pd.read_csv(OUT/'pareto_comparisons.csv');S=pd.read_csv(OUT/'equal_constraint_summary.csv');P=S[S['mode']=='F3'].set_index('method');old=pd.read_csv(P9/'benchmark_summary.csv').set_index('policy');comp=pd.read_csv(OUT/'paired_allocation_differences.csv');st=pd.read_csv(OUT/'synchronized_monthly_intervals.csv');runtime=pd.read_csv(OUT/'runtime_summary.csv');auth=pd.read_csv(OUT/'authority_transitions.csv');ledger=pd.read_csv(OUT/'authority_ledger_events.csv');v4=pd.read_csv(OUT/'v3_v4_differences.csv');v4=v4[v4.kind=='primary'];refs=pd.read_csv(OUT/'verified_references.csv',dtype=str).fillna('');pro=json.loads((OUT/'PROTOCOL.json').read_text());env=json.loads((OUT/'SCALABILITY_EXECUTION.json').read_text());valid=json.loads((OUT/'VALIDATION.json').read_text());states={s['id']:s for s in load_states()};cases=json.loads((OUT/'CASE_SELECTION.json').read_text())['cases']
    caveat='Exploratory evidence from nine synthetic investor profiles and previously examined historical paths. No independent holdout, unbiased point-in-time universe or population-level investor inference is established.'
    primary=S[(S['mode']=='F3')&S.method.isin(['V3','V4','GREEDY','REF_U','REF_B'])]
    main_table=table(primary,['method','states','valid_rate','purchase_rate','mean_U_norm','mean_budget_fill','mean_HHI','mean_purchase_positions','ND_UD_rate','ND_UDB_rate'],['valid_rate','purchase_rate','mean_U_norm','mean_budget_fill','ND_UD_rate','ND_UDB_rate'])
    primarycomp=comp[comp['mode']=='F3'];refsU=R[(R['mode']=='F3')&(R.method=='REF_U')];v=R[(R['mode']=='F3')&(R.method=='V3')];ratio=v[['state_id','U']].merge(refsU[['state_id','U','solver_status']],on='state_id',suffixes=('_V3','_ref'));ratio=ratio[(ratio.solver_status=='optimal_full_guard')&(ratio.U_ref>0)];utility_ratio=(ratio.U_V3/ratio.U_ref).mean()
    solver=R[R.family.str.startswith('REF')].groupby(['mode','solver_status']).size().rename('calls').reset_index()
    nd=P.loc['V3','ND_UDB_rate'];nd2=P.loc['V3','ND_UD_rate'];dom=primarycomp.greedy_dominates_V3_UDB.mean();meanH=primarycomp.V3_minus_greedy_HHI.mean();meanU=primarycomp.V3_minus_greedy_U_norm.mean();meanZ=primarycomp.V3_minus_greedy_budget_fill.mean()
    eq_details='''The Phase 9 reference suppressed unchanged positions near fee-induced cap crossings through conservative linear grandfathering. Phase 10 preserves that implementation and adds a separately named guard-equivalent reference with binary purchase indicators. Both primary F3 and wide sensitivity use identical budget, cash, top-up permissions, sector exclusions, prices, ordinal scores, covariance, costs and original portfolio guard. A reference can still differ because it solves a linear objective while V3 follows sector-priority sizing. V3's .20/.35 caps are account-equity constraints, not equity-sleeve ceilings. V1 retains original held-name exclusions and original policy restrictions; it is the original-baseline contrast rather than an equal-rule optimality competitor.'''
    write('PHASE10_EQUAL_CONSTRAINT_COMPARISON.md',f'''# Equal-constraint algorithmic comparison

{caveat}

## Audit and common feasible sets

{eq_details}

F3 makes max three purchased tickers and one purchased ticker per sector common hard restrictions. Fwide removes both. No limit is imposed on existing holdings count. V3 and V4 remain frozen; their voluntary basket rule is unchanged. Every returned allocation, including fallback no-trade portfolios, is independently checked. Failed HHI-target searches are not counted as feasible positive allocations. Reference status/gaps retain the difference between a linear-relaxation solve and a full-guard certificate.

## Matched F3 results

Percent columns: valid/purchase rates, normalized utility, budget fill and nondominance rates. HHI and number of positions are unscaled. Means condition on exact V3 historical states rather than different policy paths.

{main_table}

V3 minus constrained greedy: normalized utility {meanU:.6f}, budget fill {meanZ:.6f}, posttrade HHI {meanH:.6f}. Lower HHI is better. These are paired state means, not nine-profile independent samples. Greedy dominates V3 on utility/diversification/budget in {dom*100:.2f}% of states. V3's mean ratio to certified unconstrained-F3 utility optima is {utility_ratio*100:.2f}% over {len(ratio)} covered states; this denominator excludes uncertified/resource-limited results. The original Phase 9 62.39% remains preserved as a wider conservative-reference comparison.

## Identical objectives and distributions

The full objective family and numerical preferences are defined in PROTOCOL.json. Candidate utility, pure utilization, diversification and joint U/D/B scalar scores are computed for every method in objective_measurements.csv. objective_summary.csv gives mean, median, observed-best fraction and regret to the best evaluated allocation. A best-observed scalarization is not a globally solved nonlinear objective. Quantiles and per-profile/stratum data are retained; the pure utility/budget reference is certified only where solver status explicitly permits it.

{FORMULATION}

## Solver coverage

One budget solve reported optimality but its bound differed from actual inclusive cost by INR0.004357. Its certificate is explicitly withheld under the independent rtol1e-7/atol1e-5 audit. Raw allocations/status are preserved in portfolio_allocations.csv; portfolio_allocations_audited.csv and solver_certification_audit.csv expose the downgrade. No purchase or objective was changed.

{table(solver)}

Do not infer integer-program failure from a legitimate HHI-infeasible target, or feasibility from a valid zero-purchase fallback. Solver runtime caps limit the observed alternative set. Target-feasible positive purchases and all returned guard-compliant outputs are separate columns. Rejection counters have different event meanings: failed greedy one-share attempts, V3 final-basket cancellations, and invalid MILP relaxation incumbents. They must not be compared as equivalent rates. Rejected internal MILP relaxations are expected during outer approximation; they are never emitted as valid purchases.
''')
    similar=primarycomp.agg({'max_reference_U_at_similar_HHI_minus_V3':['count','mean','median'],'V3_HHI_minus_min_reference_HHI_at_similar_utility':['count','mean','median']})
    prefs=pd.read_csv(OUT/'objective_summary.csv');prefs=prefs[(prefs['mode']=='F3')&prefs.method.isin(['V3','GREEDY','REF_U','REF_B'])]
    write('PHASE10_PARETO_ANALYSIS.md',f'''# Observed utility–diversification trade-offs

{caveat}

## Prespecified search and normalization

Candidate utility is ordinal utility-weighted nominal purchases / saved approved budget. Diversification is one minus equity-only posttrade sector HHI. Utilization is fee-inclusive cost / budget. No raw-score/HHI scale mixing or sample-fitted normalization is used. Empty-sleeve HHI is undefined. Five U/D preferences plus pure budget and equal-weight U/D/B were fixed in PROTOCOL.json before the historical grid; all methods receive the same scores. The reference solves max utility at no extra cap and HHI caps .35,.25,.20,.15,.10, plus max budget. The wider sensitivity solves only pure utility and budget, so its observed frontier is less densely sampled and its nondominance rate must not be compared as equal-coverage evidence.

An allocation is observed-nondominated if no valid evaluated allocation improves at least one selected component without worsening another (tolerance1e-8). Both UD and UDB status are exported. Empty HHI and failed/target-infeasible reference outputs are excluded from frontier candidates. The no-trade alternative is retained only where it has defined existing equity holdings. Matching tolerances were fixed: absolute HHI difference <=.01; normalized utility difference <=.02. Similarity does not mean exact equality.

## V3 placement

The lowest additional reference HHI target was .10, while V3 ends below .10 in348/432 states. This coarse grid can favor V3's observed nondominance because the reference is not directly minimizing HHI in that region. V3 is best observed for pure diversification in85.42% of states, but for balanced U/D/B in only3.01%. These are fixed-grid candidate comparisons, not proof of global diversified allocation competitiveness.

V3 is observed-nondominated in **{nd2*100:.2f}%** of F3 states for U/D and **{nd*100:.2f}%** for U/D/B. Greedy dominates it on all three metrics in **{dom*100:.2f}%**. These are observed finite-set results, not global Pareto certificates. The search can miss dominating portfolios, particularly when the reference reaches a resource limit. A high nondominance rate does not prove a favorable economic exchange rate between utility and HHI.

Relative to constrained greedy, mean V3 utility changes by {meanU:.6f} of budget, fill by {meanZ:.6f}, and HHI by {meanH:.6f}. Report all three together. Similar-HHI reference comparisons cover {int(primarycomp.max_reference_U_at_similar_HHI_minus_V3.notna().sum())}/432 states; mean additional reference utility is {primarycomp.max_reference_U_at_similar_HHI_minus_V3.mean():.6f}. Similar-utility comparisons cover {int(primarycomp.V3_HHI_minus_min_reference_HHI_at_similar_utility.notna().sum())}/432; mean V3 HHI minus best similar-utility reference HHI is {primarycomp.V3_HHI_minus_min_reference_HHI_at_similar_utility.mean():.6f}. Coverage is reported instead of extrapolating unavailable matches.

## Common scalar-objective comparisons

{table(prefs,['preference','method','mean_objective','median_objective','mean_observed_regret','best_observed_fraction'],['best_observed_fraction'],digits=4)}

Every method is evaluated under every objective. V3's position is an empirical operational trade-off; differing internal preferences do not exempt it from unfavorable common-objective scores. No favorable subset of weights is selected as the only result. Figure3 shows one prespecified representative plus explicitly selected positive/negative extremes; aggregate CSVs retain all states.

## Statistical interpretation

Three-month circular blocks, 2000 draws, seed20261025 provide descriptive monthly decision-difference intervals. Synchronized blocks preserve common market dates across profiles. Daily financial uncertainty from Phase 9 remains separate. No p-values or investor-population significance claims are produced. Strict numerical nondominance is sensitive to small differences; tolerances are disclosed and no economic optimality follows from it.
''')
    timing=runtime[(runtime.factor=='candidate_count')].copy();timing[['median_seconds','p95_seconds','maximum_seconds']]*=1000
    memory=pd.read_csv(OUT/'memory_measurements.csv');mem=memory[(memory.kind=='synthetic_OFAT')&(memory.factor=='candidate_count')].groupby(['candidate_count','method']).agg(median_python_peak_KiB=('python_visible_peak_bytes',lambda x:x.median()/1024),input_matrix_KiB=('input_matrix_bytes',lambda x:x.median()/1024)).reset_index()
    write('PHASE10_SCALABILITY.md',f'''# Controlled runtime and memory study

## Scope and hardware

{env['cases']} input cases: 18 historical subset cases and 51 synthetic OFAT cases. Each case/method has one warm-up, three timed repeats and one separate memory call: {env['timed_calls']} timed calls, {env['warm_up_calls']} warm-ups and {env['memory_calls']} instrumented memory calls. Four methods are greedy, V3, V4 at equal authority and the Phase 10 exact-guard utility reference. The historical experiment finished before this single-process timing study started. No network or historical acquisition occurs inside timed calls.

Platform: {env['platform']}; architecture {env['machine']}; logical CPU count {env['logical_CPU_count']}. CPU brand and installed RAM could not be read under the sandbox, so no model is invented. Python/software versions are in SCALABILITY_EXECUTION.json. CPU frequency, pinning, thermal state and native solver RSS are uncontrolled. A lightweight analysis process overlapped the initial timing portion; these are wall-clock observations without CPU isolation, especially limiting interpretation of small heuristic timing differences. Timings are empirical and environment-specific.

## Candidate-size results

Median/p95/maximum columns below are milliseconds. Valid rate includes a no-trade fallback; purchase rate is separate. Certified rate applies to the reference's linear objective only. Timeouts and gaps must accompany runtime comparisons because a 0.5s capped solve can return less allocation quality.

{table(timing,['kind','candidate_count','method','measurements','median_seconds','p95_seconds','maximum_seconds','valid_rate','purchase_rate','timeout_rate','certified_rate'],['valid_rate','purchase_rate','timeout_rate','certified_rate'],digits=4)}

## Independent complexity factors

The center is n40, approved budget INR10000, five existing holdings, ten sectors, position cap .20, sector cap .35 and score dispersion1. OFAT alternatives change budget1000/100000, holdings0/20, sectors3/16, position caps.10/.30, sector caps.20/.50 and dispersion.01/2, using three fixed seeds101/202/303. All non-size results are in runtime_summary.csv and configurations in scalability_configurations.csv. No factorial interaction or universal asymptotic claim follows from this OFAT design.

Historical subsets have 10/20/40 candidates but retain the complete 40-name holding/covariance matrix. Synthetic80/160 have actual larger matrices. Synthetic prices, scores and covariance are used solely to test computation and constraints; no synthetic return or investment-performance claim is made. Score dispersion is a positive scaling preserving order; the ordinal objective and V3 ordering are invariant to that transformation by design, which is reported rather than interpreted as financial robustness. Non-default cap tests use a separately labelled V3-structure guard-parameter adapter; the frozen V3 primary policy is unchanged.

## Memory

{table(mem,digits=3)}

These are Python-visible tracemalloc peaks from separate instrumented calls, not full process memory or native HiGHS RSS. Dense input matrices are reported separately and can already be allocated before the call. Memory timing is excluded from latency distributions.

## Complexity limits

Dense covariance storage is O(n²) and a full guard evaluation costs O(n²+s*n). Greedy's repeated one-share scans are pseudopolynomial in share budget, with up to O(Q*n) attempted additions. V3 sorts and checks seeds, then searches quantities for at most three names; residual loops and dense guards prevent an unsupported blanket polynomial-time claim in binary input length. Binary MILP branch-and-bound has no claimed polynomial bound. Norm outer approximation and time limits are implementation controls, not a new complexity theorem. A faster heuristic and an optimizing reference do different work; latency alone does not establish optimization superiority.
''')
    ops=auth[auth.kind=='primary'].groupby('policy').agg(instrumented_operations=('operation','size'),max_outstanding_lots=('lots_after','max'),max_approval_IDs=('id_count','max'),max_spend_IDs=('spend_id_count','max'),median_transition_microseconds=('seconds',lambda x:x.median()*1e6)).reset_index()
    le=ledger[ledger.kind=='primary'].groupby(['policy','action']).agg(events=('amount','size'),total_INR=('amount','sum')).reset_index()
    write('PHASE10_V3_V4_ANALYSIS.md',f'''# V3/V4 complexity–benefit analysis

{caveat}

## Financial and construction separation

All 432 matched V3/V4 quantities are identical at equal state/authority, in both F3 and Fwide. The 18 primary authority-instrumented accounts reproduce prior financial outcomes; six shock accounts and twelve targeted lifecycle checks were also executed. V4 is not a different share constructor.

{table(v4,['scenario','authorized_budget_utilization','mean_invested_allocation','annualized_return','annualized_volatility','cvar95','maximum_drawdown','transaction_fees'],['authorized_budget_utilization','mean_invested_allocation','annualized_return','annualized_volatility','cvar95','maximum_drawdown'])}

Rate differences are percentage points. Mean V4−V3 utilization +4.82pp, invested exposure +1.36pp, annualized return +0.418pp, daily CVaR +0.0278pp and drawdown +0.377pp. Mean transaction fees increase INR30.40 over four years. Profile effects vary; drawdown does not increase in every profile. These observations do not identify a universal household utility benefit.

## Measured operational state

{table(ops,digits=3)}

{table(le,digits=3)}

The first table counts method-entry month-review/spend operations; the second reports actual ledger events, including expiry. V4 can have fewer operations because its holding path yields different trade counts. Complexity is not measured by lines of code. V4 carries dated approval lots, FIFO balances, expiry/revocation reasons and spending identity state. The primary observed maximum is three outstanding lots versus one under V3; no-spend lifecycle tests reach twelve before expiry. Both versions retain approval and spending ID sets, whose growth is distinct from the bounded lot count.

Twelve actual checks cover no initial grant; duplicate approval; duplicate debit; overspend; 11/12-month boundary; reduced household capacity; FIFO crossing; monthly expiry; explicit revocation primitive; cash/authority mismatch; duplicate recycled proceeds; exact full spend. All passed. Shock inputs suspend buying January–March2024 after capacity review. Explicit brokerage withdrawals and concurrent production persistence were not simulated.

## Operational risks and recommendation

Potential integration failures include lost/duplicated approvals after retries, cash reconciliation errors, incorrect calendar aging, FIFO double debits, failure to revoke carry, and concurrent or non-atomic cash/authority writes. The research primitives detect selected invalid operations but do not test database atomicity, persistence recovery, live withdrawals or tax handling. Additional production engineering would be necessary.

**Recommendation: B — optional extended policy.** V3 is the simpler research default. V4 may suit an explicit preference for approval carry-forward, but is not justified as the preferred default solely by higher deployment. Both remain research-isolated; this recommendation does not authorize deployment. Additional independent periods and operational persistence/withdrawal tests are needed before integration.
''')
    bibliography='\n\n'.join(f"[{r.id}] {r.authors}, “{r.title},” *{r.venue}*, vol. {r.volume}{', no. '+r.issue if r.issue else ''}, pp. {r.pages}, {r.year}. DOI: [{r.doi}](https://doi.org/{r.doi})." for r in refs.itertuples())
    related='\n\n'.join(f"**[{r.id}]** {r.relevance} Primary verification: [publisher]({r.source})"+(f", [author source]({r.author_source})." if r.author_source else '.') for r in refs.itertuples())
    write('PHASE10_NOVELTY_ASSESSMENT.md',f'''# Targeted research novelty assessment

## Verified literature and overlap

Eight publications were checked through publisher or author primary pages for title, authors, venue, year, pages and DOI. Some publisher full texts were inaccessible; the audit relies on available abstracts, metadata and author descriptions where stated. It is a targeted comparison, not an exhaustive systematic search or proof that no similar system exists.

{related}

## Exact contribution boundary

Integer shares, transaction costs, cardinality, sector constraints, existing-portfolio rebalancing and heuristic trade-offs all have prior art. Phase 10's integer reference is a validation comparator assembled from established disjunction and norm-cut techniques; it is not a proposed new IntelliVest solver. V3 is a deterministic sector-priority feasibility heuristic with inverse-volatility target sizing and controlled top-ups, not a newly established general optimization algorithm.

The narrow supported differentiator is the integration of a **household-approved authority boundary** (separate from actual brokerage cash and protected reserves), point-in-time whole-share feasibility, existing-holding top-ups, explicit combined portfolio guards and delayed execution, accompanied by auditable component and constraint-matched experiments. The largest result is a relative improvement over the original IntelliVest rank-first policy, not proof that the full combination is novel relative to all portfolio literature. A household-domain formulation and reproducible applied evaluation can be useful without a new optimization theorem.

Categories: (1) new optimization method **not established**; (2) new combination **possible as domain integration, not proven globally original**; (3) domain-specific affordability integration **supported as implemented**; (4) auditable applied framework **supported**; (5) substantial engineering/experimental contribution **supported**. The final scientific classification is **C: applied affordability-aware allocation framework with strong baseline execution improvements but limited established methodological novelty**.

## What would strengthen the claim

A closer systematic search for household approval models and sector-priority whole-share heuristics; genuinely independent point-in-time universes/prospective frozen outcomes; more realistic costs, corporate actions and withdrawals; stronger state coverage and certified trade-off searches; and a methodological distinction with a formal or empirical advantage over strong prior-art allocators. This study does not establish those missing items.

## Verified references

{bibliography}
''')
    # Actual worked input and allocation, no illustrative prices passed off as evidence.
    ident=cases['prespecified_representative'];example=R[(R.state_id==ident)&(R['mode']=='F3')&R.method.isin(['V3','GREEDY','REF_U'])];ss=states[ident];long=pd.read_csv(OUT/'allocation_quantities.csv');examplelong=long[(long.state_id==ident)&(long['mode']=='F3')&long.method.isin(['V3','GREEDY','REF_U'])]
    worked=f'''Verified historical example: {ident}, saved approved budget INR{ss['budget']:.2f}, actual cash INR{ss['cash']:.2f}, existing holdings {int(np.count_nonzero(ss['q']))}. These are historical research inputs, not illustrative invented prices.\n\n'''+table(examplelong,['method','ticker','sector','existing_quantity','purchased_quantity','observed_price','inclusive_cost'],digits=4)+'\n'+table(example,['method','cost','budget_fill','U_norm','HHI','purchase_positions'],['budget_fill','U_norm'],digits=4)
    case_sections=[];candidates=pd.read_csv(OUT/'candidate_scores.csv');strata=pd.read_csv(OUT/'stratified_outcomes.csv')
    for label,case_id in cases.items():
        state=states[case_id];z=R[(R.state_id==case_id)&(R['mode']=='F3')&R.method.isin(['V3','GREEDY','REF_U'])]
        selected=long[(long.state_id==case_id)&(long['mode']=='F3')&long.method.isin(['V3','GREEDY','REF_U'])].merge(candidates[['state_id','ticker','selection_score','size_weight']],on=['state_id','ticker'])
        holdings={state['tickers'][i]:int(n) for i,n in enumerate(state['q']) if n}
        case_sections.append('## '+label+' — '+case_id+'\n\nCash INR'+f"{state['cash']:.2f}"+', approved authority INR'+f"{state['authority']:.2f}"+', saved batch budget INR'+f"{state['budget']:.2f}"+'. Existing holdings: `'+json.dumps(holdings)+'`. All candidate prices/scores and covariance are retained in matched-state exports.\n\n'+table(z,['method','budget_fill','U_norm','HHI','purchase_positions','post_positions'],['budget_fill','U_norm'],digits=5)+'\n'+table(selected,['method','ticker','sector','existing_quantity','purchased_quantity','observed_price','selection_score','size_weight','inclusive_cost'],digits=4))
    stratum_table=strata[(strata['mode']=='F3')&strata.method.isin(['V3','GREEDY'])]
    write('PHASE10_CASE_ANALYSIS.md','# Positive and negative allocation cases\n\n'+caveat+'\n\n'+json.loads((OUT/'CASE_SELECTION.json').read_text())['selection_rules']+'\n\n'+ '\n\n'.join(case_sections)+'\n\n## Complete stratification\n\n'+table(stratum_table,['method','grouping','stratum','states','mean_U_norm','mean_budget_fill','mean_HHI','valid_rate'],['mean_U_norm','mean_budget_fill','valid_rate'])+'\n\nDiversification differences are greatest in empty/concentrated inputs; those strata contain9/13 states. With ten-plus existing holdings (395 states), V3 mean HHI0.0934 versus greedy0.0967 accompanies normalized utility0.5912 versus0.9477. These small/co-dependent strata do not support human-population claims. Fixed candidate-count strata without observations are unavailable, not silently extrapolated.')
    claims=[
['Approved-capital deployment improves over original rank-first','V1 14.52%, V3 95.13%; +80.61pp; next-session no-buy witnesses218→3','baseline_reproduction.csv; Phase9 benchmark_summary.csv','01;02','Original synthetic profiles; monthly authority; fees10bp/slip5bp','supported','Combined feasibility/top-up/guard policy effect, not isolated algorithm novelty'],
['Controlled top-ups support recurring execution','Feasible/no-topup29.83%→V3 95.13%; +65.30pp','Phase9 ablation_outcomes.csv','01','Frozen feasible constructor, monthly authority','supported','Effect interacts with feasibility and changes exposure'],
['V3 offers diversification/utility trade-offs',f'F3 ΔHHI={meanH:.6f}; ΔU/B={meanU:.6f}; ND UDB={nd*100:.2f}%','paired_allocation_differences.csv; pareto_comparisons.csv','03;04;08','Observed finite candidate set; all matched guards','supported conditionally','Not global Pareto; utility sacrifice and dominating cases retained'],
['V3 universally dominates greedy',f'Greedy dominates V3 on UDB in {dom*100:.2f}% of states','paired_allocation_differences.csv','03;08','Common F3 set and normalized objectives','unsupported','No universal allocation or return superiority'],
['Low computational latency','See measured medians/p95/max by size and input complexity','runtime_summary.csv; memory_measurements.csv','05','Same local process; warmed calls; timed solver resource cap','supported locally','Native solver memory unavailable; heuristic/reference work differs'],
['V4 provides extra deployment','+4.82pp utilization; +1.36pp exposure; +0.0278pp daily CVaR','v3_v4_differences.csv; authority_transitions.csv','07','Same constructor; monthly versus carry authority','supported','Optional policy; no default deployment justification'],
['Financial affordability and guarded feasibility preserved',f"{valid['allocation_rows_verified']} returned allocations checked; {valid['checks_passed']} focused checks passed",'VALIDATION.json; portfolio_allocations.csv','09','Tested states; includes labelled zero-purchase fallbacks','supported in tested cases','Not a universal theorem; bootstrap and grandfathering explicit'],
['Novel general-purpose optimization algorithm','Existing discrete/cost/cardinality/sector prior art verified','verified_references.csv; PHASE10_NOVELTY_ASSESSMENT.md','none','Targeted literature audit','not established','Position as applied methodology/experimental framework'],
['Independent validation or population superiority','No independent holdout; nine designed profiles share market paths','PROTOCOL.json; PHASE9_DATA_AUDIT.md','all','Restricted exposed surviving-security universe','unsupported','Requires prospective or genuinely unexamined independent evidence']]
    claimsframe=pd.DataFrame(claims,columns=['claim','numerical_evidence','source_CSV_or_report','figure','assumptions','assessment','qualification']);claimsframe['independent_validation_absent']=True;claimsframe.to_csv(OUT/'claim_evidence_matrix.csv',index=False)
    write('PHASE10_RESEARCH_CLAIMS.md','# Publication claim–evidence matrix\n\n'+caveat+'\n\n'+table(claimsframe)+'\n\nRecommended claim: “Feasibility-aware selection and controlled top-ups substantially improve conversion of household-approved investment authority into executable whole-share purchases relative to the original rank-first policy, while preserving the tested affordability and portfolio guards. Matched comparisons quantify the resulting utility–diversification trade-offs rather than establishing universal optimization superiority.”')
    rq=f'''| RQ | Evidence-based answer |
|---|---|
| RQ17 | Original primary deployment14.52%→95.13%; purchase frequency28.01%→99.31%; signal-feasible non-execution218→3. The endpoint includes next-session cancellations. |
| RQ18 | F3 mean V3−greedy U/B={meanU:.6f}, fill={meanZ:.6f}, HHI={meanH:.6f}; trade-off, not dominance. |
| RQ19 | V3 observed ND UDB={nd*100:.2f}%; greedy dominates it in{dom*100:.2f}%; global Pareto status unproven. |
| RQ20 | Controlled historical/synthetic size, budget, holdings, sector, cap and dispersion experiments completed; timings/memory/status retained. |
| RQ21 | V3/V4 same allocations at equal authority. V4 adds deployment and exposure, variable downside and dated-lot bookkeeping. Optional extension recommended. |
| RQ22 | Applied household-authority/feasibility integration and reproducible evaluation; new general optimizer or universal novelty not established. |'''
    titles='''1. **Recommended — IntelliVest: Feasibility-Aware Whole-Share Portfolio Construction Under Household Affordability and Risk Constraints.** Focus: domain-specific method and tested execution improvement. Evidence: reproduced authority utilization, matched guards, trade-offs and latency. Weakness: limited novelty, exposed surviving universe. Position: applied algorithmic methodology/experimental systems paper. “Algorithm” is acceptable for pseudocode, but the title should not imply a new exact optimizer.

2. **Converting Approved Retail Investment Budgets into Executable Whole-Share Portfolios: An Experimental Study.** Focus: auditability and execution evidence. Evidence: utilization, top-up ablations, actual cost/guard reconciliation. Weakness: weaker methodological novelty. Position: applied quantitative systems and reproducibility.

3. **Utility–Diversification Trade-offs in Affordability-Constrained Whole-Share Portfolio Construction.** Focus: equal-constraint comparison and observed Pareto study. Evidence: paired frontier/objective results and scaling. Weakness: finite search, resource caps and no global frontier. Position: experimental comparison; avoid “optimal” in the title.'''
    write('PHASE10_FINAL_REPORT.md',f'''# IntelliVest Phase 10 final report

**Scientific decision: C — applied affordability-aware allocation framework with strong baseline execution improvements but limited established methodological novelty.** {caveat}

## Executed evidence

27 primary frozen V1/V3/V4 replays with daily parity; 2160 prior matched allocator outputs/objectives reproduced; 432 saved V3 states; {len(R)} matched allocation calls across F3 and Fwide; {env['cases']} scalability cases with {env['timed_calls']} timed calls, {env['warm_up_calls']} warm-ups and {env['memory_calls']} memory calls; 24 authority replays; twelve lifecycle scenarios; and 24 exhaustive tiny-state optimization checks. These are computation counts, not independent investors. {valid['checks_passed']} focused checks passed and {valid['checks_failed']} failed. All {verify()} protected files remain unchanged, including Phase9's entire output manifest and its854-file prior-input manifest.

## Strongest positive finding

Approved-capital utilization is reproduced at14.52% for V1 and95.13% for V3 (+80.61pp). Actual purchase frequency rises28.01%→99.31%, and signal-feasible decisions without next-session purchases fall218→3. The Phase9 controlled no-topup comparison29.83%→95.13% confirms existing-holding compatibility is a major component. This is a combined policy/constructor improvement over the original baseline; it does not establish a unique advantage over all budget-aware allocators. Equal-weight and greedy remain material comparators.

## Equal-constraint and trade-off results

{main_table}

V3 is observed-nondominated in{nd*100:.2f}% on U/D/B and{nd2*100:.2f}% on U/D. Greedy dominates it in{dom*100:.2f}%. V3 mean utility/reference ratio is{utility_ratio*100:.2f}% over{len(ratio)} certified covered states. Unfavorable objective scores, higher-reference utility at similar HHI and negative cases are retained. Similar-HHI and similar-utility matching use prespecified tolerances with explicit coverage. The frontier is observed; neither all global Pareto points nor nonlinear joint-objective optima are claimed.

Under the prespecified balanced U/D/B objective V3 is best observed in only3.01% of states, versus85.42% for pure diversification. Its high observed nondominance is limited by the coarse reference HHI grid:348/432 V3 allocations lie below the lowest extra cap .10. Near-HHI references offer mean additional normalized utility0.3431 over397 covered states. These qualifications prevent a strong optimal-diversification claim.

## Research questions

{rq}

One solver-reported optimal budget certificate was withheld after a INR0.004357 objective-bound discrepancy; its allocation remains guard-compliant. Raw and audited status files are retained. This is a certification qualification, not an unsafe trade.

## Statistical and financial interpretation

Paired monthly allocation differences use three-month circular blocks,2000 draws, seed20261025, with synchronized date blocks across the nine synthetic profiles. Intervals describe conditional temporal variability, not investor-population effects. Per-profile/stratum distributions and both positive/negative examples are exported. Phase9 financial risk trade-offs remain intact: V3/V4 return8.61%/9.03% with daily CVaR0.899%/0.927% and drawdown10.11%/10.48%; no claim of lower risk from higher deployment is made.

V4 adds4.82pp utilization and1.36pp exposure, with0.418pp extra annualized return and0.0278pp extra daily CVaR on average. It is an optional authority extension, not a distinct constructor or an automatically preferred default. Primary ledger lot count reaches3 versus1; no-spend expiry checks reach12. Production atomicity and withdrawal recovery remain untested.

## Worked historical example

{worked}

## Novelty and paper positioning

Eight verified primary-source references establish prior art for integer lots, cardinality, costs, rebalancing, sectors and heuristic trade-offs. The differentiator is an applied integration of household-approved authority, protected reserve separation, whole-share feasibility, top-ups, combined guards and auditable delayed execution. No new general optimizer or proof of first-ever combination is established. Lead with the execution problem and quantified baseline improvement; present the Pareto and greedy evidence as a fair boundary on the contribution.

{titles}

## Remaining limitations and readiness

The universe has40 surviving retained securities and57,400 Yahoo/yfinance observations with sparse independent exchange checks, current sector labels, listing metadata rather than certificates, and corporate-action/dividend timing limitations. Historical periods were already inspected. Phase9's new ETF is a benchmark, not a holdout; daily TRI and complete historical index membership remain unavailable. Synthetic scaling has no financial-performance meaning. Solver timeouts restrict alternative coverage; memory excludes native solver RSS. Some cap sensitivities are explicitly labelled structure adapters rather than frozen-policy outputs.

The package is ready for coauthor review and venue-specific manuscript preparation, **not ready to claim independently validated or novel-optimizer superiority**. A stronger submission needs a prospective freeze/unexamined point-in-time data, stronger external comparators matched to the household domain, a closer systematic novelty search, and realistic withdrawal/persistence/cost/action validation. The polished draft remains separate from every earlier paper.
''')
    write('PHASE10_CONFERENCE_DRAFT.md',f'''# IntelliVest: Feasibility-Aware Whole-Share Portfolio Construction Under Household Affordability and Risk Constraints

Separate IEEE-style manuscript draft — exploratory research,25 October2026. No author affiliation, acceptance status or external validation is invented.

## Abstract

Whole-share recommendations can fail even when household-approved funds remain available. We evaluate a deterministic feasibility-aware portfolio constructor that separates brokerage cash from investment authority, permits guarded existing-holding top-ups and prioritizes sector balance. Frozen historical replays across nine synthetic profiles reproduce approved-capital utilization of14.52% for the original rank-first policy and95.13% for V3. Using432 identical decision states, we compare V3, constrained greedy and a guard-equivalent integer reference under matched financial, basket and portfolio restrictions. V3 is observed-nondominated on utility, diversification and budget fill in{nd*100:.2f}% of states, while greedy dominates it in{dom*100:.2f}%; V3 therefore presents an operational trade-off rather than universal optimality. Mean normalized utility is0.598 versus0.946 for greedy, while HHI is0.106 versus0.118; the coarse reference grid limits the nondominance interpretation. Controlled timing covers historical subsets and separately labelled synthetic cases up to160 candidates. Carry-forward authority adds4.82pp utilization with additional exposure and downside. Findings support an auditable affordability-aware applied methodology; independent validation and general algorithmic novelty remain unestablished.

## I. Introduction

A stock ranking does not itself produce an executable whole-share portfolio. Expensive early candidates, exclusions of held names and quantity rounding can leave approved funds unspent. Actual brokerage cash also contains savings that a household has not authorized for investment. The research problem is to convert approved purchasing power into feasible recommendations while including existing holdings and respecting combined portfolio guards.

We contribute an explicit applied authority/feasibility workflow; a deterministic sector-priority constructor with controlled top-ups; reproduced execution and ablation evidence; and matched objective, Pareto and computational evaluations. These contributions are narrower than a new global optimization algorithm or a claim of market outperformance. RQ17–RQ22 investigate execution, utility/diversification, equal-constraint competitiveness, computational cost, carry-forward benefit and publication novelty.

## II. Related Work

Discrete transaction lots and heuristic allocation were studied by Mansini and Speranza[R1]. Cardinality-constrained frontiers and heuristic searches appear in Chang et al.[R2], while Kellerer et al.[R3] consider costs and minimum lots. Lobo et al.[R4] treat transaction costs and risk-constrained optimization; Bonami and Lejeune[R5] develop exact stochastic/integer portfolio approaches including sector restrictions. Existing-portfolio cost-aware rebalancing is addressed by Woodside-Oriakhi et al.[R6]. Mansini et al.[R7] review practical LP/MILP portfolio features, and Erwin and Engelbrecht[R8] review later metaheuristic work. These sources prevent novelty claims based merely on whole shares, constraints or heuristic search. IntelliVest's differentiation is its household-approved authority boundary and auditable applied integration; first-ever methodological originality is not established by this targeted audit.

## III. Problem Formulation

{FORMULATION}

## IV. Proposed Methodology

Financial eligibility first determines current authority independently of brokerage savings. Candidates then enter a sector-priority scan using only historically available scores/prices. One-share combined feasibility is checked before basket admission. Existing held names are permitted under the same account/sector/risk guards as new names. At most three distinct-sector tickers enter weighted integer sizing and residual fills. The final basket is revalidated and next-session execution can reduce quantities or cancel unsafe fills. Risk controls are hard where encoded; score and sector priorities are soft preferences.

## V. Algorithm Pseudocode

{PSEUDOCODE}

V3 is a heuristic. V4 extends only the authority ledger and is not a distinct optimizer. The reference is an evaluation tool; no improved V6 is introduced into the primary comparison.

## VI. Experimental Setup

The primary data and algorithms are frozen. Nine synthetic investor profiles share a restricted40-security historical universe; the original source contains57,400 observations. All27 primary V1/V3/V4 accounts reproduce prior summaries and daily ledgers. We capture432 exact V3 pretrade states and reproduce2160 earlier matched outputs/objectives before new evaluation. Matched financial inputs include cash, authority, saved budget, existing holdings, sectors, observed prices, candidate ranks, lagged covariance, fees and slippage. Historical allocation calls use1.5s reference limits. We do not refit V3/V4 or select parameters using favorable outcomes.

## VII. Baselines

V1 is the preserved rank-first baseline, retaining its original held-name restriction. The primary equal-rule comparator greedily buys the first feasible next share by descending score and ticker under F3; it stops when no permitted addition exists. The reference maximizes linear score utility or inclusive deployment with exact purchase-indicator grandfathering and valid norm supporting cuts, checking all outputs against the frozen guard. Fwide sensitivity removes only the purchased-basket cardinality/distinct-sector restrictions. Phase9's conservative reference remains preserved and is not relabelled as a full-guard optimum.

## VIII. Results and Ablations

The primary full-path V1/V3 comparison reproduces14.52%/95.13% unique-authority utilization and218/3 signal-feasible no-buy events. The latter includes next-session guard/price effects. Previously executed controlled feasible/no-topup versus V3 arms yield29.83% versus95.13% utilization, showing substantial existing-holding contribution. Components interact; their effects are not additive causal shares.

{main_table}

Percent columns contain normalized utility, fill, feasibility and observed nondominance; HHI is unitless. Results at identical states separate allocation behavior from evolving historical exposure. V3 is best observed under balanced U/D/B in only3.01% of states and under pure diversification in85.42%. A coarse grid caveat is material:348 V3 states have HHI below the lowest extra reference cap .10; references are not directly minimizing HHI there. V3 trades candidate utility/fill against HHI; it is not excused from unfavorable scores merely because it follows another preference. At equal authority V3 and V4 quantities are identical.

## IX. Runtime and Trade-off Analysis

The observed alternative set uses fixed HHI caps and normalized joint preferences. V3 is UD-nondominated in{nd2*100:.2f}% and UDB-nondominated in{nd*100:.2f}% of matched F3 states. Greedy dominates V3 in{dom*100:.2f}%. These are finite-search results, not global frontier certificates. Similar-HHI and similar-utility comparisons have explicitly reported coverage.

The controlled study contains{env['cases']} cases and{env['timed_calls']} timed calls. Historical candidates are limited to legitimate10/20/40-name subsets; larger80/160 cases are synthetic computational inputs with fixed seeds. Budget, existing positions, sectors, caps and score dispersion vary independently in an OFAT design. Latency medians/p95/max, target/purchase feasibility, solver gap/status and separate Python-visible memory appear in the accompanying scalability table and Figure5. Optimizer resource limits and differences in work prevent a generic speed-superiority conclusion. Dense risk matrices scale quadratically in storage; empirical timings do not prove polynomial complexity.

V4 adds4.82pp utilization,1.36pp invested exposure and0.418pp annualized return, with0.0278pp more daily CVaR and0.377pp more drawdown on average. Lot/ID/event measurements and twelve lifecycle tests support auditability assessment, not production atomicity. It is an optional authority extension rather than an automatic default.

## X. Statistical Assessment

Per-profile paired monthly effects and synchronized three-month circular block intervals use2000 draws, seed20261025. Shared date blocks preserve dependence across designed profiles. No dependent account-days are counted as independent people. Financial metrics inherited from reproduced Phase9 remain distinct from allocation objectives: V3/V4 return8.61%/9.03% with daily CVaR0.899%/0.927% and drawdown10.11%/10.48%. Additional deployment is not free risk reduction. No population p-values, external validation or statistically superior-return claim is made.

## XI. Threats to Validity

Surviving-universe selection, current sector labels, provider listing metadata, sparse exchange corroboration and corporate-action/ex-date dividend approximations remain. The previously inspected periods are not a holdout. NIFTYBEES data from Phase9 do not create an independent evaluation set. One solver-reported budget optimum had an INR0.004357 bound/cost discrepancy and its certificate was withheld. The reference's resource limits and finite HHI grid can miss dominating alternatives; numerical certificates apply only to the stated linear subproblem. Strict nondominance does not establish economic value. F3 is a matched basket restriction rather than the sole possible retail portfolio design. Synthetic scaling is not market performance; native solver RSS and complete hardware model information are unavailable. Household scenarios omit production persistence, live withdrawals, taxes and realistic liquidity/market-impact modeling. The targeted literature audit is not an exhaustive proof of originality.

## XII. Conclusion

Feasibility selection and controlled top-ups substantially improve the conversion of approved household authority into executable whole-share purchases relative to the original rank-first policy. Common-constraint experiments quantify a diversification/utility/deployment exchange rather than establishing universal superiority over greedy or integer optimization. The strongest defensible contribution is an auditable applied affordability-aware construction methodology with reproduced baseline improvement and transparent limits. Independent prospective data and closer domain-matched prior-art evaluation are needed for a stronger methodological claim.

## Worked historical allocation

{worked}

## Verified References

{bibliography}

## Reproducibility

Source/configuration snapshots, matched states and constraints, candidate scores, allocation vectors, solver outcomes, frontier labels, paired effects, authority transitions, exhaustive checks, nine PNG/SVG figures and manifests accompany this draft. VALIDATION.json records{valid['checks_passed']} passing focused checks and zero unresolved failures. Existing application, databases, algorithms and earlier manuscripts remain unchanged. This Markdown draft requires coauthor review and venue-specific formatting before submission.
''')
    print('Wrote eight Phase 10 reports')
if __name__=='__main__':main()
