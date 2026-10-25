"""Research math, accounting, policy isolation and temporal-integrity checks."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research.risk_metrics import tail_metrics,performance,episode_lengths
from research.investor_scenarios import scenarios,Scenario
from research.strategies import feedback_policy,propose,candidates
from research.historical_replay import replay


def run_checks(out):
    passed=[]
    def check(name,condition):
        if not condition:
            raise AssertionError(name)
        passed.append(name)
    t=tail_metrics([-.1,-.05,0,.05,.1])
    check('inclusive-tail CVaR hand calculation',abs(t['cvar95']-.1)<1e-12)
    check('VaR linear percentile hand calculation',abs(t['var95']-.09)<1e-12)
    check('drawdown includes initial wealth',abs(performance([-.1,.1])['maximum_drawdown']-.1)<1e-12)
    check('episode durations include censored terminal run',episode_lengths([1,1,0,1])==[2,1])
    check('combined breach multiplier',feedback_policy((True,True,False),{})==(.25,()))
    check('sector-only policy',feedback_policy((False,False,True),{'A':.8,'B':.2})==(1.,('A',)))
    s=Scenario('test','low','CONSERVATIVE',10000,5000,0,4000,10000)
    pool=[{'ticker_symbol':'A','sector_name':'A','selection_score':1.,'size_weight':1.,'nominal_price':100.,'strong_negative':False}]
    _,_,risk=propose(pool,{}, {},'Risk Only',s,10000,(1.,()))
    _,_,full=propose(pool,{}, {},'Full IntelliVest',s,10000,(1.,()))
    check('Risk Only proposed overspend is measurable',sum(o['proposed_notional'] for o in risk)>s.buffer)
    check('Full proposal respects household buffer',sum(o['proposed_notional'] for o in full)<=s.buffer)
    check('No Feedback suppresses multiplier and blocks',propose(pool,{}, {},'No Feedback',s,10000,(.25,('A',)))[2]==full)
    check('Full sector block actually changes decision',not propose(pool,{}, {},'Full IntelliVest',s,10000,(1.,('A',)))[2])
    dates=pd.bdate_range('2020-01-01',periods=300)
    # Synthetic fixture exists only in memory and is never admitted as historical evidence.
    p=100*np.exp(np.arange(300)*.0005+np.sin(np.arange(300))*.01)
    fixture=pd.DataFrame({'date':dates,'ticker':'A','sector':'A','adjusted_close':p,
        'nominal_close':p,'split':0.,'nominal_dividend':0.})
    cache={}
    for day in dates:
        if day.day<=7:
            cache[(str(day.date()),s.tier,True)]=pool
    # Build every date key to avoid imposing a calendar-day monthly assumption.
    cache={(str(day.date()),s.tier,True):pool for day in dates}
    result,frames=replay(fixture,s,'Full IntelliVest',str(dates[150].date()),str(dates[-1].date()),cache)
    v=frames['valuations']; tr=frames['trades']
    check('nonnegative cash throughout synthetic replay',v.cash.min()>=-1e-6)
    check('whole integer share executions',all(tr.quantity==tr.quantity.astype(int)))
    check('strictly delayed execution',all(tr.date>tr.decision_date))
    check('unique signal/security execution',not tr.duplicated(['decision_date','ticker']).any())
    check('contribution-adjusted return identity',np.allclose(v.equity,np.r_[s.initial_cash,v.equity.iloc[:-1]]*(1+0)+v.contribution+(np.r_[s.initial_cash,v.equity.iloc[:-1]]+v.contribution)*v['return']))
    # Actual ranker must give identical history scores when future bars change.
    day=dates[200]
    a=candidates(fixture,dates,day,s.tier)
    changed=fixture.copy()
    changed.loc[changed.date>day,'adjusted_close']*=100
    b=candidates(changed,dates,day,s.tier)
    check('point-in-time ranker ignores changed future observations',a==b and len(a)==1)
    check('historical clock produces available momentum',a[0]['history_through']==str(day.date()))
    # Flat prices plus contributions must not manufacture investment returns.
    flat=fixture.copy()
    flat['nominal_close']=100.;flat['adjusted_close']=100.
    _,f=replay(flat,s,'Affordability Only',str(dates[150].date()),str(dates[-1].date()),cache,fee=0,slippage=0)
    check('flat prices / zero cost / contributions yield zero return',np.allclose(f['valuations']['return'],0))
    # Two-for-one split on execution date preserves wealth and whole quantities.
    split=flat.copy();split.loc[210:,'nominal_close']=50.;split.loc[210,'split']=2.
    _,f=replay(split,s,'Affordability Only',str(dates[150].date()),str(dates[-1].date()),cache,fee=0,slippage=0)
    check('split ledger preserves nominal wealth',np.allclose(f['valuations']['return'],0))
    out.mkdir(parents=True,exist_ok=True)
    (out/'consistency_checks.json').write_text(json.dumps({'status':'passed','checks':passed,'fixture':'synthetic mathematical diagnostics only'},indent=2)+'\n')
    print(f'{len(passed)} research consistency checks passed',flush=True)
    return passed


if __name__=='__main__':
    run_checks(Path('research/results/checks'))
