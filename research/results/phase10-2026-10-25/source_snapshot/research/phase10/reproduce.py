"""Reproduce all primary frozen accounts, capture exact 432 pre-decision states."""
from dataclasses import replace
import json
import numpy as np,pandas as pd
from research.phase10.common import OUT,P9,freeze,verify,sha
from research.phase9.reproduce import inputs
from research.phase9.allocators import build as p9build
from research.phase8.experiments import engine
from research.phase8.policies.construction import V1,V3,V4,build as frozen,hhi
from research.phase8.analysis.metrics import summarize
from research.investor_scenarios import scenarios

def main():
    freeze();cfg,m,cache=inputs();old=pd.read_csv(P9/'all_investor_performance.csv');oldquality=pd.read_csv(P9/'same_state_allocation_quality.csv');rows=[];cand=[];states=[];pools=[];baseline=[];matched=[];active={};checks=[]
    def capture(pool,q,cash,authority,feedback,policy,market,di,*args,**kw):
        a,info=frozen(pool,q,cash,authority,feedback,policy,market,di,*args,**kw)
        if policy.name=='V3' and kw.get('override') is None:
            ident=active['scenario']+'|'+str(market.dates[di].date());eligible=set(info['eligible']);v=q*market.prices[di];sector=market.sector_matrix@v
            rows.append({'state_id':ident,'scenario':active['scenario'],'tier':active['tier'],'date':str(market.dates[di].date()),'cash':cash,'authority':authority,'budget':info['budget'],'multiplier':feedback[0],'blocked_sectors':json.dumps(list(feedback[1])),'candidate_count':len(pool),'eligible_count':len(eligible),'affordable_count':info['affordable_count'],'existing_positions':int((q>0).sum()),'existing_sectors':int((sector>0).sum()),'initial_hhi':hhi(v,market.sector_matrix),'minimum_unit_price':float(np.min(market.prices[di]*1.0005*1.001)),'V3_quantities':json.dumps(a.tolist()),'history_through_max':max(r['history_through'] for r in pool)})
            states.append((q.copy(),market.prices[di].copy(),market.cov30[di].copy()));pools.append(pool)
            for r in pool:
                i=market.index[r['ticker_symbol']];cand.append({'state_id':ident,'date':str(market.dates[di].date()),'ticker':r['ticker_symbol'],'sector':r['sector_name'],'price':market.prices[di,i],'existing_quantity':int(q[i]),'selection_score':r['selection_score'],'size_weight':r['size_weight'],'eligible':r['ticker_symbol'] in eligible,'history_through':r['history_through'],'input_price_hash':r['input_price_hash']})
            for p in [V1,V3,V4,replace(V3,name='GREEDY_M'),replace(V3,name='MILP_M')]:
                b,bi=p9build(pool,q,cash,authority,feedback,p,market,di)
                ref=oldquality[(oldquality.scenario==active['scenario'])&(oldquality.date==str(market.dates[di].date()))&(oldquality.method==p.name)].iloc[0]
                expected=np.zeros(len(q),dtype=int)
                for t,n in json.loads(ref.quantity).items():expected[market.index[t]]=n
                # MILP can have alternative equal optima; require objective parity rather than identical ties.
                if p.name!='MILP_M':assert np.array_equal(b,expected),(ident,p.name)
                else:
                    from research.phase9.allocators import objective
                    valid=[r for r in pool if r['ticker_symbol'] in eligible]
                    assert np.isclose(objective(valid,b,market.prices[di],market.index),ref.objective,rtol=1e-10,atol=1e-5)
                matched.append({'state_id':ident,'method':p.name,'status':'reproduced','quantity_equal':bool(np.array_equal(b,expected))})
        return a,info
    engine.build=capture
    previous=pd.read_csv(P9/'portfolio_valuations.csv',parse_dates=['date']);previous=previous[(previous.window=='primary_2022_2025')&previous.policy.isin(['V1','V3','V4'])]
    for s in scenarios():
        active.update(scenario=s.name,tier=s.tier)
        for p in [V1,V3,V4]:
            f=engine.run(m,cache,s,p,'2022-01-01','2025-12-31');result=summarize(f);ref=old[(old.scenario==s.name)&(old.policy==p.name)&(old.window=='primary_2022_2025')].iloc[0]
            for k,v in result.items():
                if isinstance(v,(int,float,np.number)):assert np.isclose(v,ref[k],rtol=1e-10,atol=1e-8,equal_nan=True),(s.name,p.name,k)
            refv=previous[(previous.scenario==s.name)&(previous.policy==p.name)].sort_values('date')
            for c in f['valuations'].select_dtypes(include='number').columns:assert np.allclose(f['valuations'][c],refv[c],rtol=1e-10,atol=1e-8,equal_nan=True),(s.name,p.name,c)
            baseline.append({'scenario':s.name,'policy':p.name,'regime':'C' if p.carry else 'M',**result});checks.append({'scenario':s.name,'policy':p.name,'summary_and_daily_ledger':'passed'})
        print('Reproduced',s.name,flush=True)
    engine.build=frozen
    assert len(rows)==432
    np.savez_compressed(OUT/'states.npz',holdings=np.array([x[0] for x in states]),prices=np.array([x[1] for x in states]),covariances=np.array([x[2] for x in states]),sector_matrix=m.sector_matrix,tickers=np.array(m.tickers),sectors=np.array(m.sectors))
    pd.DataFrame(rows).to_csv(OUT/'matched_states.csv',index=False);pd.DataFrame(cand).to_csv(OUT/'candidate_scores.csv',index=False);(OUT/'candidate_pools.json').write_text(json.dumps(pools))
    pd.DataFrame(baseline).to_csv(OUT/'baseline_reproduction.csv',index=False);pd.DataFrame(matched).to_csv(OUT/'phase9_allocation_reproduction.csv',index=False)
    constraints=pd.DataFrame(rows)[['state_id','cash','authority','budget','multiplier','blocked_sectors','initial_hhi']];constraints['position_cap']=.20;constraints['sector_account_cap']=.35;constraints['HHI_limit']=constraints.initial_hhi.clip(lower=.25);constraints['bootstrap_HHI_exception']=constraints.initial_hhi.isna();constraints['fee']=.001;constraints['slippage']=.0005;constraints['max_purchased_tickers_F3']=3;constraints['max_purchased_tickers_per_sector_F3']=1;constraints['topups_allowed']=True;constraints['no_initial_approval_grant']=True;constraints.to_csv(OUT/'matched_constraints.csv',index=False)
    (OUT/'BASELINE_REPRODUCTION.json').write_text(json.dumps({'status':'passed','primary_accounts':27,'daily_ledger_parity':True,'same_state_reproductions':len(matched),'states':432,'checks':checks,'dataset_sha256':sha('research/data/2026-10-23/research_quotes.csv'),'protected_files':verify()},indent=2))
if __name__=='__main__':main()
