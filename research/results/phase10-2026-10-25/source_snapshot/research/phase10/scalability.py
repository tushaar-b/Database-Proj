"""Historical subset and synthetic OFAT runtime/memory; no synthetic financial returns."""
import json,time,tracemalloc,platform,os,sys,importlib.metadata
import numpy as np,pandas as pd
from research.phase10.common import OUT,load_states
from research.phase10.allocators import heuristic,reference,metrics

def synthetic(seed,n=40,budget=10000.,holdings=5,sectors=10,poscap=.2,sectorcap=.35,dispersion=1.):
    rng=np.random.default_rng(seed);p=np.exp(rng.uniform(np.log(50),np.log(5000),n));sectors=min(sectors,n);labels=np.arange(n)%sectors;S=np.eye(sectors)[labels].T
    cov=.000025*np.ones((n,n))+.000025*(S.T@S)+.0001*np.eye(n)
    q=np.zeros(n,dtype=int);held=rng.permutation(n)[:min(holdings,n)];q[held]=np.maximum(1,np.floor(1000/p[held])).astype(int)
    tickers=[f'SYN{i:03d}' for i in range(n)];sn=[f'SECTOR{i:02d}' for i in range(sectors)];scores=rng.normal(size=n)*dispersion
    pool=[{'ticker_symbol':t,'sector_name':sn[labels[i]],'selection_score':float(scores[i]),'size_weight':1.,'history_through':'synthetic_nonfinancial','strong_negative':False} for i,t in enumerate(tickers)]
    return {'id':f'SYN{seed}_{n}_{budget}_{holdings}_{sectors}_{poscap}_{sectorcap}_{dispersion}','scenario':'synthetic','date':'synthetic','tier':'not_applicable','q':q,'p':p,'cov':cov,'cash':100000.,'authority':budget,'budget':min(100000.,budget),'feedback':(1.,()),'pool':pool,'tickers':tickers,'sectors':sn,'S':S,'poscap':poscap,'sectorcap':sectorcap}

def cases():
    states=load_states();selected=[]
    for scenario in ['low_conservative','medium_moderate','high_aggressive']:
        selected += [s for s in states if s['scenario']==scenario][:2]
    for st in selected:
        for n in [10,20,40]:yield {**st,'pool':sorted(st['pool'],key=lambda r:r['ticker_symbol'])[:n]}, {'kind':'historical_subset','factor':'candidate_count','level':n,'seed':np.nan,'case_id':st['id']+'|N'+str(n)}
    configurations=[('candidate_count',n,{'n':n}) for n in [10,20,40,80,160]]
    for factor,values,key in [('budget',[1000.,100000.],'budget'),('existing_positions',[0,20],'holdings'),('represented_sectors',[3,16],'sectors'),('position_cap',[.1,.3],'poscap'),('sector_cap',[.2,.5],'sectorcap'),('score_dispersion',[.01,2.],'dispersion')]:
        configurations += [(factor,v,{key:v}) for v in values]
    for seed in [101,202,303]:
        for factor,level,kw in configurations:
            st=synthetic(seed,**kw);yield st,{'kind':'synthetic_OFAT','factor':factor,'level':level,'seed':seed,'case_id':st['id']}

def main():
    assert (OUT/'EXPERIMENT_EXECUTION.json').exists(),'Run timing after matched grid finishes'
    output=[];memory=[];configs=[]
    for st,meta in cases():
        configs.append({**meta,'candidate_count':len(st['pool']),'matrix_security_count':len(st['q']),'budget':st['budget'],'cash':st['cash'],'existing_positions':int(np.count_nonzero(st['q'])),'represented_sectors':len(st['sectors']),'position_cap':st['poscap'],'sector_cap':st['sectorcap'],'input_matrix_bytes':st['cov'].nbytes+st['S'].nbytes+st['p'].nbytes+st['q'].nbytes,'adapter':'frozen' if st['poscap']==.2 and st['sectorcap']==.35 else 'V3_structure_common_cap_sensitivity'})
        for method in ['GREEDY','V3','V4','REFERENCE']:
            def invoke():return reference(st,'F3',seconds=.5) if method=='REFERENCE' else heuristic(st,method,'F3')
            invoke() # same one-call warm-up boundary for every method
            for repeat in range(3):
                start=time.perf_counter();a,info=invoke();elapsed=time.perf_counter()-start
                output.append({**meta,'method':method,'repeat':repeat,'candidate_count':len(st['pool']),'matrix_security_count':len(st['q']),'budget':st['budget'],'existing_positions':int(np.count_nonzero(st['q'])),'represented_sectors':len(st['sectors']),'position_cap':st['poscap'],'sector_cap':st['sectorcap'],'seconds':elapsed,'quantity_signature':json.dumps(a.tolist()),**metrics(st,a),**info})
            tracemalloc.start();a,info=invoke();_,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
            memory.append({**meta,'method':method,'candidate_count':len(st['pool']),'python_visible_peak_bytes':peak,'native_solver_RSS':'unavailable','input_matrix_bytes':configs[-1]['input_matrix_bytes'],'instrumented_status':info['solver_status']})
        print('Timed',meta['case_id'],flush=True)
    r=pd.DataFrame(output);r.to_csv(OUT/'runtime_measurements.csv',index=False);pd.DataFrame(memory).to_csv(OUT/'memory_measurements.csv',index=False);pd.DataFrame(configs).to_csv(OUT/'scalability_configurations.csv',index=False)
    groups=['kind','factor','level','candidate_count','method'];summary=r.groupby(groups,dropna=False).agg(measurements=('seconds','size'),median_seconds=('seconds','median'),p95_seconds=('seconds',lambda x:x.quantile(.95)),maximum_seconds=('seconds','max'),valid_rate=('valid','mean'),purchase_rate=('purchase','mean'),timeout_rate=('solver_status',lambda x:x.str.contains('time_limit|feasible_limit|solver_1').mean()),certified_rate=('solver_status',lambda x:(x=='optimal_full_guard').mean())).reset_index();summary.to_csv(OUT/'runtime_summary.csv',index=False)
    env={'python':sys.version,'platform':platform.platform(),'machine':platform.machine(),'processor':platform.processor(),'logical_CPU_count':os.cpu_count(),'CPU_model_RAM':'not accessible under sandbox; no unverified model specification','versions':{k:importlib.metadata.version(k) for k in ['numpy','pandas','scipy']},'timing':'single process after historical grid; 1 warm-up +3 timed repeats; separate memory call; no network, CPU pinning or native RSS','cases':len(configs),'timed_calls':len(r),'warm_up_calls':len(configs)*4,'memory_calls':len(memory)}
    (OUT/'SCALABILITY_EXECUTION.json').write_text(json.dumps(env,indent=2));print(env)
if __name__=='__main__':main()
