"""Reproducible benchmark grid. Frozen engine reused through an isolated allocator hook."""
from dataclasses import replace,asdict
from pathlib import Path
import json,platform,time,importlib.metadata
import numpy as np,pandas as pd
from research.phase9.freeze import OUT,sha,verify
from research.phase9.reproduce import inputs
from research.phase9 import allocators
from research.phase8.experiments import engine
from research.phase8.policies.construction import V1,V3,V4,Policy
from research.phase8.analysis.metrics import summarize
from research.investor_scenarios import scenarios

POLICIES=[V1,V3,V4]+[replace(V3,name=a+'_'+r,carry=r=='C') for a in ['GREEDY','EQUAL','SIP','MILP','NEUTRAL'] for r in ['M','C']]+[Policy('RANK_GUARD_M',guards=True),replace(V3,name='FEAS_NO_TOPUP_M',topups=False),replace(V3,name='RANK_TOPUP_M',feasible=False)]

def main():
    assert (OUT/'FROZEN_REPRODUCTION.json').exists();assert not (OUT/'RUN_CONFIG.json').exists(),'Refusing overwrite'
    cfg,market,cache=inputs();engine.build=allocators.build
    config={'seed':20261024,'block':20,'draws':2000,'windows':cfg['windows'],'policies':[asdict(p) for p in POLICIES],'fees':.001,'slippage':.0005,'rf':.04,'cash_yield':0,'source_hashes':{str(p):sha(p) for p in Path('research/phase8').rglob('*.py')},'phase9_source_hashes':{str(p):sha(p) for p in Path('research/phase9').glob('*.py')},'dataset_sha256':sha('research/data/2026-10-23/research_quotes.csv'),'hardware':platform.uname()._asdict(),'processor':platform.processor(),'versions':{m:importlib.metadata.version(m) for m in ['numpy','pandas','scipy']},'independent_validation':False}
    (OUT/'RUN_CONFIG.json').write_text(json.dumps(config,indent=2));pd.DataFrame([asdict(p) for p in POLICIES]).to_csv(OUT/'strategy_configuration.csv',index=False)
    dest=OUT/'accounts';dest.mkdir();summaries=[]
    for w,(start,end) in cfg['windows'].items():
        for s in scenarios():
            for p in POLICIES:
                if p.name in {'RANK_GUARD_M','FEAS_NO_TOPUP_M','RANK_TOPUP_M'} and w!='primary_2022_2025':continue
                before=len(allocators.RUNTIMES);t=time.perf_counter();frames=engine.run(market,cache,s,p,start,end)
                meta={'window':w,'scenario':s.name,'tier':s.tier,'policy':p.name,'regime':'C' if p.carry else 'M','kind':'principal'}
                result=summarize(frames);result['wall_seconds']=time.perf_counter()-t
                if not frames['valuations'].stock_value.gt(0).any():
                    for k in ['annualized_volatility','var95','cvar95','maximum_drawdown']:result[k]=np.nan
                summaries.append({**meta,**result})
                folder=dest/(w+'__'+s.name+'__'+p.name);folder.mkdir()
                for name,f in frames.items():
                    for k,v in meta.items():f[k]=v
                    f.to_csv(folder/(name+'.csv'),index=False)
                rt=pd.DataFrame(allocators.RUNTIMES[before:]);
                for k,v in meta.items():rt[k]=v
                rt.to_csv(folder/'runtime.csv',index=False)
                pd.DataFrame(summaries).to_csv(OUT/'investor_level_performance.csv',index=False)
                print('Completed',w,s.name,p.name,round(result['wall_seconds'],3),flush=True)
    names=['valuations','decisions','trades','authority_events','fills','episodes','runtime']
    exports={'valuations':'portfolio_valuations','decisions':'allocation_decisions','trades':'benchmark_trades','authority_events':'authority_accounting','fills':'execution_events','episodes':'breach_episodes','runtime':'algorithm_runtimes'}
    for name in names:
        parts=[]
        for p in sorted(dest.glob('*/'+name+'.csv')):
            f=pd.read_csv(p)
            if len(f):parts.append(f)
        pd.concat(parts,ignore_index=True).to_csv(OUT/(exports[name]+'.csv'),index=False)
    s=pd.DataFrame(summaries);s[(s.window=='primary_2022_2025')].groupby(['regime','policy']).mean(numeric_only=True).to_csv(OUT/'primary_comparison.csv')
    s[s.policy.isin(['V1','RANK_GUARD_M','FEAS_NO_TOPUP_M','RANK_TOPUP_M','V3','V4','NEUTRAL_M','NEUTRAL_C'])].to_csv(OUT/'ablation_outcomes.csv',index=False)
    (OUT/'EXECUTION.json').write_text(json.dumps({'runs':len(s),'protected_files_unchanged':verify()},indent=2))
if __name__=='__main__':main()
