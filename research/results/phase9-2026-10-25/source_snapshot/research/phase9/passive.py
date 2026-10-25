"""Executable whole-unit ETF benchmark; fund-level exposure, no invented look-through HHI."""
import json
from dataclasses import replace
import numpy as np,pandas as pd
from research.phase9.freeze import OUT
from research.phase9.reproduce import inputs
from research.phase8.experiments import engine
from research.phase8.market import Market
from research.phase8.policies.construction import V3
from research.phase8.analysis.metrics import summarize
from research.investor_scenarios import scenarios

def build(pool,q,cash,authority,feedback,policy,market,di,fee=.001,slippage=.0005,override=None):
    budget=np.floor(min(cash,authority)*100+1e-8)/100;unit=market.prices[di,0]*(1+fee)*(1+slippage);qty=int(np.floor((budget+1e-8)/unit));a=np.array([qty])
    return a,{'budget':budget,'selected':['NIFTYBEES'] if qty else [],'eligible':['NIFTYBEES'],'single_feasible_candidates':['NIFTYBEES'] if budget>=unit else [],'affordable_count':int(budget>=unit),'held_exclusions':0,'sector_exclusions':0,'unused_reason':'whole_unit_residual','candidate_count':1,'eligible_count':1,'negative_momentum_selected':0}

def main():
    assert json.loads((OUT/'DATA_AUDIT.json').read_text())['etf_admitted']
    cfg,_,_=inputs();f=pd.read_csv(OUT/'benchmark_sources/NIFTYBEES_normalized.csv',parse_dates=['date'])
    d=pd.DataFrame({'date':f.date,'ticker':'NIFTYBEES','sector':'Fund look-through unavailable','nominal_close':f.Close,'adjusted_close':f['Adj Close'],'split':f['Stock Splits'],'nominal_dividend':f.Dividends});market=Market(d)
    cache={(str(day.date()),s.tier,True):[{'ticker_symbol':'NIFTYBEES','sector_name':'Fund look-through unavailable','selection_score':0.,'size_weight':1.,'history_through':str(day.date())}] for day in market.dates for s in scenarios()}
    engine.build=build;dest=OUT/'etf_accounts';dest.mkdir(exist_ok=True);summaries=[];tables={}
    for w,(start,end) in cfg['windows'].items():
        if w=='ytd_2026':continue
        for s in scenarios():
            for regime in ['M','C']:
                policy=replace(V3,name='ETF_'+regime,carry=regime=='C',guards=False)
                frames=engine.run(market,cache,s,policy,start,end)
                # Fund concentration is not sector concentration.
                frames['valuations']['hhi']=np.nan;frames['valuations']['hhi_breach']=False
                result=summarize(frames)
                for key in ['mean_hhi','max_hhi','hhi_breach_frequency','max_hhi_episode_sessions','mean_hhi_episode_sessions','mean_position_concentration']:result[key]=np.nan
                meta={'window':w,'scenario':s.name,'tier':s.tier,'policy':policy.name,'regime':regime,'kind':'principal'};summaries.append({**meta,**result})
                for name,f in frames.items():
                    for k,v in meta.items():f[k]=v
                    tables.setdefault(name,[]).append(f)
                print(w,s.name,policy.name,flush=True)
    pd.DataFrame(summaries).to_csv(OUT/'etf_investor_performance.csv',index=False)
    for k,f in tables.items():pd.concat(f,ignore_index=True).to_csv(dest/(k+'.csv'),index=False)
if __name__=='__main__':main()
