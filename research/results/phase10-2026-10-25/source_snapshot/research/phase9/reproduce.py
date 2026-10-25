import json
import numpy as np
import pandas as pd
from research.phase9.freeze import OUT,freeze,verify,sha
from research.phase8.experiments.reproduce_v1 import run as original
from research.phase8.experiments.engine import run
from research.phase8.market import Market
from research.phase8.policies.construction import V1,V3,V4
from research.phase8.analysis.metrics import summarize
from research.investor_scenarios import scenarios

def inputs():
    cfg=json.loads(Path('research/results/2026-10-23-run03/config.json').read_text())
    cache={}
    for k,v in json.loads(Path('research/results/2026-10-23-run03/ranking_cache.json').read_text()).items():
        d,t,m=k.split('|');cache[d,t,m=='True']=v
    return cfg,Market(pd.read_csv('research/data/2026-10-23/research_quotes.csv',parse_dates=['date'])),cache
from pathlib import Path
if __name__=='__main__':
    freeze();original(OUT)
    cfg,market,cache=inputs();old=pd.read_csv('research/results/phase8-2026-10-24/investor_level_results.csv');checks=[]
    for window,(start,end) in cfg['windows'].items():
        for s in scenarios():
            for p in [V1,V3,V4]:
                f=run(market,cache,s,p,start,end);result=summarize(f)
                ref=old[(old.window==window)&(old.scenario==s.name)&(old.policy==p.name)&(old.kind=='principal')].iloc[0]
                for k,v in result.items():
                    if isinstance(v,(float,int,np.number)):assert np.isclose(v,ref[k],rtol=1e-10,atol=1e-8,equal_nan=True),(window,s.name,p.name,k)
                checks.append({'window':window,'scenario':s.name,'policy':p.name,'status':'passed'})
        print('Frozen policies reproduced '+window,flush=True)
    (OUT/'FROZEN_REPRODUCTION.json').write_text(json.dumps({'status':'passed','runs':len(checks),'checks':checks,'protected_files':verify(),'dataset_sha256':sha('research/data/2026-10-23/research_quotes.csv')},indent=2))
