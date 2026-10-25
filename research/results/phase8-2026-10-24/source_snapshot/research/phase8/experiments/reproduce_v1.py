"""Stage 2: reproduce frozen V1 before interpreting any revised policy."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from backend.config import settings
from research.historical_replay import replay
from research.investor_scenarios import scenarios


def run(out):
    root=Path('research/results/2026-10-23-run03')
    config=json.loads((root/'config.json').read_text())
    for key,value in config['effective_settings'].items():setattr(settings,key,value)
    data=pd.read_csv('research/data/2026-10-23/research_quotes.csv',parse_dates=['date'])
    cache={}
    for key,value in json.loads((root/'ranking_cache.json').read_text()).items():
        day,tier,momentum=key.split('|');cache[(day,tier,momentum=='True')]=value
    expected=pd.read_csv(root/'strategy_summaries.csv')
    oldv=pd.read_csv(root/'valuations.csv',parse_dates=['date'])
    results=[];tables={};checks=[]
    for window,(start,end) in config['windows'].items():
        for scenario in scenarios():
            summary,frames=replay(data,scenario,'Full IntelliVest',start,end,cache)
            source=expected[(expected.window==window)&(expected.scenario==scenario.name)&(expected.strategy=='Full IntelliVest')].iloc[0]
            for metric,actual in summary.items():
                recorded=source[metric]
                assert (pd.isna(actual) and pd.isna(recorded)) or np.isclose(float(actual),float(recorded),rtol=1e-10,atol=1e-8),(window,scenario.name,metric)
            ref=oldv[(oldv.kind=='principal')&(oldv.window==window)&(oldv.scenario==scenario.name)&(oldv.strategy=='Full IntelliVest')].sort_values('date')
            for col in frames['valuations'].select_dtypes(include='number').columns:
                assert np.allclose(frames['valuations'][col],ref[col],rtol=1e-10,atol=1e-8,equal_nan=True),(window,scenario.name,col)
            meta={'window':window,'scenario':scenario.name,'tier':scenario.tier,'policy':'V1','kind':'principal'}
            results.append({**meta,**summary});checks.append({**meta,'status':'matched_original_summary_and_daily_ledger'})
            for key,frame in frames.items():
                if key=='positions':continue
                for k,v in meta.items():frame[k]=v
                tables.setdefault(key,[]).append(frame)
            print('V1 reproduced '+window+' '+scenario.name,flush=True)
    dest=out/'baseline_v1';dest.mkdir(exist_ok=True)
    pd.DataFrame(results).to_csv(dest/'summaries.csv',index=False)
    for name,frames in tables.items():pd.concat(frames,ignore_index=True).to_csv(dest/(name+'.csv'),index=False)
    (out/'V1_REPRODUCTION.json').write_text(json.dumps({'status':'passed','runs':36,'checks':checks},indent=2)+'\n')


if __name__=='__main__':run(Path('research/results/phase8-2026-10-24'))
