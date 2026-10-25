"""Common-state allocation quality and controlled runtime, separate from path performance."""
import json,time
from dataclasses import replace
import numpy as np,pandas as pd
from research.phase9.freeze import OUT
from research.phase9.reproduce import inputs
from research.phase9 import allocators
from research.phase8.experiments import engine
from research.phase8.policies.construction import V1,V3,V4,Guard,build as frozen
from research.investor_scenarios import scenarios

def main():
    cfg,m,cache=inputs();rows=[];runtime=[];states=[];current={}
    policies=[V1,replace(V3,name='RANK_TOPUP_M',feasible=False),replace(V3,name='GREEDY_M'),V3,V4,replace(V3,name='MILP_M')]
    def capture(pool,q,cash,authority,feedback,policy,market,di,fee=.001,slippage=.0005,override=None):
        result=frozen(pool,q,cash,authority,feedback,policy,market,di,fee,slippage,override)
        if override is not None:return result
        info=result[1];eligible=[r for r in pool if r['ticker_symbol'] in set(info['eligible'])];guard=Guard(q,cash,market.prices[di],market.cov30[di],market.sector_matrix)
        for p in policies:
            start=time.perf_counter();a,i=allocators.build(pool,q,cash,authority,feedback,p,market,di);elapsed=time.perf_counter()-start
            cost=float(a@(market.prices[di]*1.0005*1.001));safe=cost<=info['budget']+1e-7 and guard.allowed(a,cost)[0]
            common_eligible=all(market.tickers[x] in set(info['eligible']) for x in np.where(a>0)[0])
            rows.append({'scenario':current['scenario'],'date':str(market.dates[di].date()),'method':p.name,'authority':authority,'cash':cash,'budget':info['budget'],'eligible_count':len(eligible),'affordable_count':info['affordable_count'],'executed_at_signal':bool(a.any()),'quantity':json.dumps({market.tickers[x]:int(a[x]) for x in np.where(a>0)[0]}),'cost':cost,'budget_fill':cost/info['budget'] if info['budget'] else np.nan,'common_constraint_valid':bool(safe and common_eligible),'objective':allocators.objective(eligible,a,market.prices[di],market.index) if safe and common_eligible else np.nan,'seconds':elapsed,**{k:v for k,v in i.items() if k.startswith('solver_')}})
        if current['scenario'] in ['low_conservative','medium_moderate','high_aggressive'] and len([x for x in states if x[0]==current['scenario']])<2:states.append((current['scenario'],pool,q.copy(),cash,authority,feedback,market,di))
        return result
    engine.build=capture
    for s in scenarios():
        current['scenario']=s.name;engine.run(m,cache,s,V3,'2022-01-01','2025-12-31');print(s.name,flush=True)
    pd.DataFrame(rows).to_csv(OUT/'same_state_allocation_quality.csv',index=False)
    for scenario,pool,q,cash,authority,feedback,market,di in states:
        for size in [10,20,40]:
            subset=sorted(pool,key=lambda r:r['ticker_symbol'])[:size]
            for p in [V1,replace(V3,name='GREEDY_M'),V3,V4,replace(V3,name='MILP_M')]:
                for repeat in range(5):
                    start=time.perf_counter();a,info=allocators.build(subset,q,cash,authority,feedback,p,market,di);seconds=time.perf_counter()-start
                    runtime.append({'scenario':scenario,'date':str(market.dates[di].date()),'candidate_size':len(subset),'method':p.name,'repeat':repeat,'seconds':seconds,'quantity_signature':json.dumps(a.tolist()),'solver_status':info.get('solver_status','not_applicable')})
    pd.DataFrame(runtime).to_csv(OUT/'controlled_algorithm_runtimes.csv',index=False)
if __name__=='__main__':main()
