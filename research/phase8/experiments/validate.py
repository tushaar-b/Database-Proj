"""Focused conservation, construction, historical and feedback checks."""
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
from research.phase8.policies.authority import Authority
from research.phase8.policies.construction import V1,V3,V4,V5,Guard,build,corrective_sales,hhi
from research.risk_metrics import performance,tail_metrics


def validate(out):
    checks=[]
    def check(name,value):
        assert value,name
        checks.append(name)
    day=pd.Timestamp('2022-01-03')
    a=Authority(True);a.month(day,5000,.25);a.spend(250,day,'buy1')
    check('approval minus spending equals unused authority',abs(a.balance-1000)<1e-8)
    a.month(pd.Timestamp('2022-02-01'),5000,.25)
    check('carry adds new approval once, without a second tier deduction',abs(a.balance-2250)<1e-8)
    try:a.month(pd.Timestamp('2022-02-01'),5000,.25);duplicate=False
    except AssertionError:duplicate=True
    check('duplicate monthly approval rejected',duplicate)
    try:a.spend(1,day,'buy1');duplicate=False
    except AssertionError:duplicate=True
    check('duplicate purchase debit rejected',duplicate)
    a.month(pd.Timestamp('2022-03-01'),0,.25)
    check('household deterioration revokes unspent authority, no sale',a.balance==0 and a.revoked==2250)
    a.month(pd.Timestamp('2022-04-01'),5000,.25);a.revoke(500,day,'withdrawal')
    check('withdrawal removes authority without creating new approval',a.balance==750)
    a.recycle(100,day,'sale_proceeds');a.spend(800,day,'buy2');a.check()
    check('recycled proceeds and external approvals tracked separately',a.recycled_grants==100 and a.spent_recycled==50)
    a.month(pd.Timestamp('2023-04-03'),5000,.25)
    check('unused approvals expire at twelve calendar months',a.expired==50 and a.balance==1250)
    b=Authority(False);b.month(day,5000,.25);b.month(pd.Timestamp('2022-02-01'),5000,.25)
    check('monthly-reset authority reproduces V1 quota',b.balance==1250 and b.expired==1250)
    try:b.spend(1300,day,'bad');over=False
    except AssertionError:over=True
    check('overspending authority rejected',over)
    tickers=['A','B','C','D','E'];prices=np.array([1000.,1000.,1000.,10.,20.])
    market=SimpleNamespace(index={t:i for i,t in enumerate(tickers)},tickers=tickers,
        sectors=tickers,sector_index={t:i for i,t in enumerate(tickers)},sector_matrix=np.eye(5),prices=np.array([prices]),cov30=np.array([np.eye(5)*.0001]))
    pool=[{'ticker_symbol':t,'sector_name':t,'selection_score':5-i,'size_weight':1.,'nominal_price':prices[i],
           'history_through':str(day.date()),'strong_negative':False} for i,t in enumerate(tickers)]
    q=np.zeros(5,dtype=int)
    legacy,_=build(pool,q,10000,100,(1.,()),V1,market,0)
    feasible,info=build(pool,q,10000,100,(1.,()),V3,market,0)
    check('legacy top-three can return zero despite affordable alternatives',not legacy.any())
    check('feasibility-aware selection finds valid alternatives',feasible.any() and feasible[3]+feasible[4]>0)
    check('whole-share quantities and cost-inclusive budget',(feasible==feasible.astype(int)).all() and float(feasible@(prices*1.0005*1.001))<=100+1e-7)
    check('fewer than three names supported',len(info['selected'])==2)
    held=np.array([0,0,0,5,0])
    only=[pool[3]]
    top,_=build(only,held,10000,100,(1.,()),V3,market,0)
    check('eligible existing holding can receive a top-up',top[3]>0)
    excluded,_=build(only,held,10000,100,(1.,()),V1,market,0)
    check('V1 existing-holding exclusion preserved',not excluded.any())
    g=Guard(np.array([0,0,0,300,0]),7000,prices,np.eye(5)*.0001,np.eye(5))
    add=np.zeros(5,dtype=int);add[3]=1
    check('combined position checked, not only added shares',not g.allowed(add,10.015005)[0])
    values=np.array([60,20,10,10,0])*100.
    check('HHI hand calculation uses invested assets',abs(hhi(values,np.eye(5))-.42)<1e-12)
    check('empty portfolio HHI undefined',np.isnan(hhi(np.zeros(5),np.eye(5))))
    sold=corrective_sales(np.array([60,20,10,10,0]),np.ones(5)*100,np.eye(5))
    check('corrective selling reduces measured HHI',hhi((np.array([60,20,10,10,0])-sold)*100,np.eye(5))<.42)
    check('selling respects whole shares and ten-percent turnover bound',(sold==sold.astype(int)).all() and sold.sum()*100<=1000)
    check('single-sector selling cannot manufacture diversification',not corrective_sales(np.array([100,0,0,0,0]),np.ones(5)*100,np.eye(5)).any())
    blocked,_=build(pool,q,10000,100,(1.,tuple(tickers)),V4,market,0)
    check('feedback blocks reach candidate eligibility',not blocked.any())
    t=tail_metrics([-.10,-.05,0,.05,.10])
    check('VaR linear quantile and inclusive-tail CVaR',abs(t['var95']-.09)<1e-12 and abs(t['cvar95']-.10)<1e-12)
    p=performance([-.1,.1])
    check('drawdown includes initial wealth',abs(p['maximum_drawdown']-.1)<1e-12)
    check('geometric return excludes fictitious contributions',abs(p['cumulative_return']+.01)<1e-12)
    a=Authority(True);a.month(day,5000,.25)
    check('initial brokerage savings do not automatically mint authority',a.grants==1250 and a.balance==1250)
    safe=Guard(q,10000,prices,np.eye(5)*.0001,np.eye(5));added=np.array([0,0,0,1,0])
    check('bootstrap guard defined without calling empty portfolio diversified',safe.allowed(added,10.015005)[0] and np.isnan(safe.base_hhi))
    (out/'FOCUSED_CHECKS.json').write_text(json.dumps({'status':'passed','count':len(checks),'checks':checks},indent=2)+'\n')
    print(f'{len(checks)} Phase 8 focused checks passed',flush=True)
