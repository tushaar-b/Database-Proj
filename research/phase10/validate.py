"""Focused numerical verification, including exhaustive tiny-state optimization audits."""
import itertools,json,copy
from pathlib import Path
import numpy as np,pandas as pd
from research.phase10.common import OUT,P9,sha,verify,load_states
from research.phase10.allocators import reference,heuristic,metrics,context
from research.phase8.policies.construction import Guard

def main():
    checks=[]
    def check(name,value):assert value,name;checks.append(name)
    preserved=verify();check('all protected prior evidence and application hashes unchanged',preserved>5000)
    for p,h in json.loads((P9/'OUTPUT_HASHES.json').read_text()).items():assert sha(P9/p)==h,p
    check('every Phase 9 output manifest hash independently rechecked',True)
    repro=json.loads((OUT/'BASELINE_REPRODUCTION.json').read_text());check('all 27 selected primary frozen accounts and daily ledgers reproduced',repro['primary_accounts']==27 and repro['daily_ledger_parity'])
    check('2160 previous matched allocator outputs or objectives reproduced',repro['same_state_reproductions']==2160)
    states=load_states();byid={s['id']:s for s in states};rows=pd.read_csv(OUT/'portfolio_allocations_audited.csv');check('all 432 exact pretrade states available',len(states)==432 and len(byid)==432)
    check('all candidate histories at or before decision date',all(pd.Timestamp(r['history_through'])<=pd.Timestamp(s['date']) for s in states for r in s['pool']))
    decisions=pd.read_csv(P9/'allocation_decisions.csv');decisions=decisions[(decisions.policy=='V3')&(decisions.window=='primary_2022_2025')];decisions['state_id']=decisions.scenario+'|'+decisions.date
    stateframe=pd.read_csv(OUT/'matched_states.csv');d=stateframe.merge(decisions,on='state_id',suffixes=('_new','_old'));check('cash authority and saved batch budget match original state',np.allclose(d.cash,d.brokerage_cash)&np.allclose(d.authority,d.authority_before)&np.allclose(d.budget,d.authorized_batch_budget))
    guard_failures=[]
    for row in rows.itertuples():
        s=byid[row.state_id];a=np.array(json.loads(row.quantities));p=s['p'];v=s['q']*p;new=(s['q']+a)*p;cost=float(a@(p*1.0005*1.001));E=s['cash']-cost+new.sum();sector=s['S']@new
        assert np.all(a>=0) and np.array_equal(a,np.rint(a));assert cost<=min(s['cash'],s['authority'],s['budget'])+1e-7
        assert abs(cost-row.cost)<1e-6
        assert abs(cost/s['budget']-row.budget_fill)<1e-10
        allowed=set(context(s).ids);assert all(i in allowed for i in np.where(a>0)[0])
        assert Guard(s['q'],s['cash'],p,s['cov'],s['S']).allowed(a,cost)[0]
        assert np.all(new<=np.maximum(.2*E,v)+1e-7)
        assert np.all(sector<=np.maximum(.35*E,s['S']@v)+1e-7)
        h=float(np.sum((sector/new.sum())**2)) if new.sum()>0 else np.nan
        assert np.isclose(row.HHI,h,equal_nan=True,atol=1e-12)
        assert np.isclose(row.D,1-h,equal_nan=True,atol=1e-12)
        assert 0<=row.U_norm<=1+1e-9 and 0<=row.budget_fill<=1+1e-9
        if row.mode=='F3':assert (a>0).sum()<=3 and (s['S']@(a>0)).max()<=1
        if row.solver_status=='optimal_full_guard':
            assert a.any() and row.target_valid and row.gap<=1e-7
            val=row.U if row.reference_objective=='utility' else row.cost
            assert np.isclose(val,row.linear_objective_bound,rtol=1e-7,atol=1e-5)
        assert row.valid
    check('all returned allocations pass independent cash authority budget integrality and cost checks',True)
    check('all returned allocations pass frozen posttrade position sector and risk guard',True)
    check('F3 cardinality and distinct-sector purchase constraints shared by all methods',True)
    check('posttrade HHI excludes cash and is undefined for empty holdings',True)
    check('all utility and budget normalizations lie in fixed zero-one range',True)
    check('all optimal claims require feasible target allocation and matching MILP bound',True)
    audit=pd.read_csv(OUT/'solver_certification_audit.csv');downgraded=rows[rows.solver_status=='solver_reported_optimal_bound_discrepancy'];check('solver objective-bound discrepancies preserved and certificates explicitly withheld',len(downgraded)==int((~audit.bound_reconciles).sum()))
    r=pd.read_csv(OUT/'pareto_comparisons.csv');count=0
    for (ident,mode),g in r.groupby(['state_id','mode']):
        valid=g[g.frontier_eligible]
        for row in valid.itertuples():
            a=np.array([row.U_norm,row.D,row.budget_fill]);x=valid[['U_norm','D','budget_fill']].to_numpy();dominates=np.all(x>=a-1e-8,axis=1)&np.any(x>a+1e-8,axis=1)
            assert row.observed_nondominated_UDB==not_any(dominates)
            dominates=np.all(x[:,:2]>=a[:2]-1e-8,axis=1)&np.any(x[:,:2]>a[:2]+1e-8,axis=1)
            assert row.observed_nondominated_UD==not_any(dominates);count+=1
    for (ident,mode),g in rows.groupby(['state_id','mode']):
        for method,column in [('REF_U','U'),('REF_B','cost')]:
            optimum=g[g.method==method].iloc[0]
            if optimum.solver_status=='optimal_full_guard':assert (g[column]<=optimum[column]+1e-5).all(),(ident,mode,method)
    check('all certified unconstrained utility and budget optima bound same-set evaluated allocations',True)
    check('observed Pareto status independently recomputed for every eligible candidate',count>0)
    objectives=pd.read_csv(OUT/'objective_measurements.csv');pref=json.loads((OUT/'PROTOCOL.json').read_text())['joint_preferences']
    for name,w in pref.items():
        assert np.isclose(sum(w),1)
        part=objectives[objectives.preference==name].merge(r[['state_id','mode','method','U_norm','D','budget_fill']],on=['state_id','mode','method'])
        assert np.allclose(part.objective,w[0]*part.U_norm+w[1]*(part.D if w[1] else part.D.fillna(0.))+w[2]*part.budget_fill,equal_nan=True)
    check('all prespecified joint objectives use identical normalized scores for every method',True)
    h=r[r.method.isin(['V3','V4'])].pivot(index=['state_id','mode'],columns='method',values='quantities');check('V3 and V4 allocation quantities identical at equal authority',h.V3.equals(h.V4))
    # Tiny exhaustive finite feasible sets verify exact disjunctions and objective certificates.
    audits=[]
    for case in ['empty','existing','fee_crossing']:
        p=np.array([2.,1.,1.5,4.]);q=np.array([0,0,0,0]) if case=='empty' else np.array([1,1,0,0]) if case=='existing' else np.array([5,0,0,0]);cash=40.005 if case=='fee_crossing' else 20.;B=5.
        s={'id':case,'q':q,'p':p,'cov':np.eye(4)*.0001,'S':np.eye(4),'tickers':['A','B','C','D'],'sectors':['a','b','c','d'],'cash':cash,'authority':B,'budget':B,'feedback':(1.,()),'poscap':.2,'sectorcap':.35,'pool':[{'ticker_symbol':t,'sector_name':sec,'selection_score':4-j,'size_weight':1.} for j,(t,sec) in enumerate(zip(['A','B','C','D'],['a','b','c','d']))]}
        ub=np.floor(B/(p*1.0005*1.001)).astype(int)
        for mode in ['F3','Fwide']:
            for cap in [None,.35]:
                feasible=[]
                for a in itertools.product(*[range(x+1) for x in ub]):
                    a=np.array(a)
                    if not a.any():continue
                    z=metrics(s,a,mode,cap)
                    if z['valid']:feasible.append((a,z))
                for objective in ['utility','budget']:
                    a,info=reference(s,mode,objective,cap,seconds=3.);z=metrics(s,a,mode,cap);key='U' if objective=='utility' else 'cost';opt=max([x[1][key] for x in feasible],default=0.)
                    assert np.isclose(z[key],opt,rtol=1e-8,atol=1e-6),(case,mode,cap,objective,z[key],opt,info)
                    if feasible:assert info['solver_status']=='optimal_full_guard' and z['valid']
                    else:assert info['solver_status']=='infeasible_positive_purchase'
                    audits.append({'case':case,'mode':mode,'HHI_cap':cap,'objective':objective,'enumerated_feasible_positive_allocations':len(feasible),'exhaustive_optimum':opt,'reference_objective':z[key],'solver_status':info['solver_status'],'passed':True})
    pd.DataFrame(audits).to_csv(OUT/'exhaustive_reference_checks.csv',index=False)
    check('24 exhaustive tiny-state objective checks including fee-induced grandfathering crossing',len(audits)==24)
    run=pd.read_csv(OUT/'runtime_measurements.csv');memory=pd.read_csv(OUT/'memory_measurements.csv');configs=pd.read_csv(OUT/'scalability_configurations.csv')
    check('scalability uses all five requested candidate sizes in synthetic cases',set(run[run.kind=='synthetic_OFAT'].candidate_count)=={10,20,40,80,160})
    check('all scalability allocations valid with no fractional quantities',run.valid.all())
    check('runtime repeats use same case-input and all four methods',all(len(g)==3 for _,g in run.groupby(['case_id','method'])) and set(run.method)=={'V3','V4','GREEDY','REFERENCE'})
    check('Python-visible memory explicitly separated from unavailable native solver RSS',(memory.python_visible_peak_bytes>0).all() and memory.native_solver_RSS.eq('unavailable').all())
    simple=run[run.method.isin(['GREEDY','V3','V4'])].groupby(['case_id','method']).quantity_signature.nunique();check('deterministic heuristic quantities across warmed repetitions',(simple==1).all())
    lifecycle=pd.read_csv(OUT/'authority_lifecycle_checks.csv');check('all twelve expiry revocation duplicate and cash lifecycle checks pass',len(lifecycle)==12 and lifecycle.status.eq('passed').all())
    authority=pd.read_csv(OUT/'authority_account_outcomes.csv');base=pd.read_csv(OUT/'baseline_reproduction.csv')
    z=authority[authority.kind=='primary'].merge(base,on=['scenario','policy'],suffixes=('_new','_old'))
    check('authority instrumentation leaves all eighteen primary V3/V4 outcomes unchanged',np.allclose(z.annualized_return_new,z.annualized_return_old)&np.allclose(z.authorized_budget_utilization_new,z.authorized_budget_utilization_old))
    check('all historical input sources remain hash reproducible',repro['dataset_sha256']==sha('research/data/2026-10-23/research_quotes.csv'))
    # A second call repeats paired monthly statistics, avoiding claims about independent investors.
    dif=pd.read_csv(OUT/'paired_allocation_differences.csv');st=pd.read_csv(OUT/'synchronized_monthly_intervals.csv')
    for row in st.itertuples():
        x=dif[dif['mode']==row.mode].groupby('date')[row.metric].mean().sort_index().to_numpy();rng=np.random.default_rng(20261025);idx=(rng.integers(0,48,size=(2000,16))[:,:,None]+np.arange(3))%48;means=np.nanmean(x[idx.reshape(2000,48)],axis=1)
        assert np.allclose([row.mean_difference,row.ci95_low,row.ci95_high],[x.mean(),*np.quantile(means,[.025,.975])])
    check('synchronized paired three-month block intervals reproduce',True)
    check('prior evidence and application hashes unchanged after verification',verify()==preserved)
    result={'status':'passed','checks_passed':len(checks),'checks_failed':0,'checks':checks,'protected_files':preserved,'allocation_rows_verified':len(rows),'pareto_points_verified':count,'tiny_exhaustive_cases':len(audits),'timed_calls':len(run),'source_sha256':sha(__file__)}
    (OUT/'VALIDATION.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
def not_any(x):return not bool(np.any(x))
if __name__=='__main__':main()
