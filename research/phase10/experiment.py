"""Matched exact-guard allocations and prespecified epsilon-grid alternatives."""
import json,time
import numpy as np,pandas as pd
from research.phase10.common import OUT,load_states,verify
from research.phase10.allocators import heuristic,reference,metrics

def main():
    protocol=json.loads((OUT/'PROTOCOL.json').read_text());states=load_states();path=OUT/'allocation_runs.jsonl'
    done=set()
    if path.exists():done={json.loads(line)['state_id'] for line in path.read_text().splitlines()}
    for j,st in enumerate(states):
        if st['id'] in done:continue
        rows=[]
        for mode in ['F3','Fwide']:
            calls=[('NO_TRADE',None,None)]+[(m,None,None) for m in ['V3','V4','GREEDY']]
            calls += [('REF_U',cap,'utility') for cap in (protocol['HHI_caps'] if mode=='F3' else [None])]+[('REF_B',None,'budget')]
            for method,cap,obj in calls:
                start=time.perf_counter()
                if method=='NO_TRADE':a=np.zeros(len(st['q']),dtype=int);info={'solver_status':'not_applicable','gap':np.nan,'rejected_proposals':0}
                elif method.startswith('REF'):a,info=reference(st,mode,obj,cap,protocol['solver_seconds_historical'],protocol['max_outer_cuts'])
                else:a,info=heuristic(st,method,mode)
                elapsed=time.perf_counter()-start
                metric=metrics(st,a,mode);target=metrics(st,a,mode,cap)
                label=method+('_H'+str(cap) if cap is not None else '')
                rows.append({'state_id':st['id'],'scenario':st['scenario'],'date':st['date'],'tier':st['tier'],'mode':mode,'method':label,'family':method,'HHI_cap':cap,'budget':st['budget'],'cash':st['cash'],'authority':st['authority'],'quantities':json.dumps(a.tolist()),'seconds':elapsed,'target_valid':target['valid'],**metric,**info})
        with path.open('a') as f:
            for row in rows:f.write(json.dumps(row,allow_nan=True)+'\n')
        print('Completed',j+1,st['id'],flush=True)
    result=pd.DataFrame([json.loads(line) for line in path.read_text().splitlines()]);result.to_csv(OUT/'portfolio_allocations.csv',index=False)
    long=[]
    for row in result.itertuples():
        a=json.loads(row.quantities);st=states[next(j for j,s in enumerate(states) if s['id']==row.state_id)]
        for i,n in enumerate(a):
            if n:long.append({'state_id':row.state_id,'mode':row.mode,'method':row.method,'ticker':st['tickers'][i],'sector':st['sectors'][int(np.argmax(st['S'][:,i]))],'existing_quantity':int(st['q'][i]),'purchased_quantity':int(n),'observed_price':st['p'][i],'inclusive_cost':float(n*st['p'][i]*1.0005*1.001)})
    pd.DataFrame(long).to_csv(OUT/'allocation_quantities.csv',index=False)
    (OUT/'EXPERIMENT_EXECUTION.json').write_text(json.dumps({'matched_states':len(states),'allocation_calls':len(result),'protected_files':verify(),'source_sha256':__import__('hashlib').sha256(open(__file__,'rb').read()).hexdigest()},indent=2))
if __name__=='__main__':main()
