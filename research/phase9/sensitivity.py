"""Prespecified cost, risk-free, cash yield and restricted-universe sensitivities."""
from dataclasses import replace
from pathlib import Path
import types,json
import pandas as pd,numpy as np
from research.phase9.freeze import OUT
from research.phase9.reproduce import inputs
from research.phase9 import allocators
from research.phase8.policies.construction import V3,V4
from research.phase8.analysis.metrics import summarize
from research.diagnostics.metrics import cash_overlay,sharpe_diagnostic
from research.investor_scenarios import scenarios

def main():
    cfg,m,cache=inputs();rows=[]
    policies=[V3,V4,replace(V3,name='GREEDY_M'),replace(V4,name='GREEDY_C'),replace(V3,name='EQUAL_M'),replace(V4,name='EQUAL_C')]
    selected=[s for s in scenarios() if s.name in ['low_conservative','medium_moderate','high_aggressive']]
    source=Path('research/phase8/experiments/engine.py').read_text()
    for assumption in ['cost_zero','cost_double','universe_lexicographic20','household_deterioration']:
        fee,slip=(0.,0.) if assumption=='cost_zero' else (.002,.001) if assumption=='cost_double' else (.001,.0005)
        # Compile a separately labelled execution adapter, preserving original on disk.
        text=source.replace('.0005','PHASE9_SLIP').replace('.001','PHASE9_FEE').replace('PHASE9_SLIP',repr(slip)).replace('PHASE9_FEE',repr(fee))
        module=types.ModuleType('phase9_cost_engine');exec(compile(text,'phase9_'+assumption,'exec'),module.__dict__)
        def build(*args,**kwargs):return allocators.build(*args,**kwargs,fee=fee,slippage=slip)
        module.build=build
        restricted={k:[r for r in v if r['ticker_symbol'] in set(m.tickers[:20])] for k,v in cache.items()} if assumption=='universe_lexicographic20' else cache
        for s in selected:
            for p in policies:
                frames=module.run(m,restricted,s,p,'2022-01-01','2025-12-31',shock=assumption=='household_deterioration')
                folder=OUT/'sensitivity_accounts'/assumption/(s.name+'__'+p.name);folder.mkdir(parents=True,exist_ok=True)
                for name,f in frames.items():f.to_csv(folder/(name+'.csv'),index=False)
                rows.append({'assumption':assumption,'scenario':s.name,'policy':p.name,'fee':fee,'slippage':slip,**summarize(frames)})
        print(assumption,flush=True)
    pd.DataFrame(rows).to_csv(OUT/'sensitivity_outcomes.csv',index=False)
    v=pd.concat([pd.read_csv(OUT/'portfolio_valuations.csv',parse_dates=['date']),pd.read_csv(OUT/'etf_accounts/valuations.csv',parse_dates=['date'])],ignore_index=True);cash=[]
    for (window,scenario,policy),g in v[v.window=='primary_2022_2025'].groupby(['window','scenario','policy']):
        for rate in [0.,.04]:
            overlay=cash_overlay(g,rate)
            for convention in ['legacy_linear','effective_geometric']:cash.append({'scenario':scenario,'policy':policy,'cash_yield':rate,**sharpe_diagnostic(overlay,convention)})
    pd.DataFrame(cash).to_csv(OUT/'cash_yield_sharpe_sensitivity.csv',index=False)
if __name__=='__main__':main()
