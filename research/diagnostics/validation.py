"""Focused numerical checks and offline parity with the real feedback builder."""
import ast
from decimal import Decimal,localcontext
import hashlib
import itertools
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research.strategies import feedback_policy
from research.investor_scenarios import scenarios
from research.diagnostics.instrumentation import propose,probe,basket,decision_record
from research.diagnostics.metrics import sharpe_diagnostic,cash_overlay,hhi_diagnostic


def checks(out):
    passed=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        passed.append(name)
    tree=ast.parse(Path('backend/services.py').read_text())
    node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_feedback_snapshot')
    env={'hashlib':hashlib,'json':json}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'backend/services.py','exec'),env)
    metrics=['VAR_95_BREACH','VOLATILITY_SPIKE','SECTOR_HHI_EXCEEDED']
    class Cursor:
        def __init__(self,flags):self.flags=flags;self.query=''
        def execute(self,query,args):self.query=query
        def fetchall(self):
            if 'FROM rebalance_alert' in self.query:
                return [{'alert_id':str(i),'portfolio_id':'synthetic-portfolio','metric':m}
                        for i,(flag,m) in enumerate(zip(self.flags,metrics)) if flag]
            return [{'portfolio_id':'synthetic-portfolio','sector_name':'A'}]
    for flags in itertools.product([False,True],repeat=3):
        payload,*_=env['_feedback_snapshot'](Cursor(flags),'synthetic-user','synthetic-portfolio')
        expected=feedback_policy(flags,{'A':.8,'B':.2})
        check('application/research feedback rule parity '+str(flags),
              (payload['capacity_multiplier'],tuple(payload['blocked_sectors']))==expected)
    s=scenarios()[0]
    pool=[{'ticker_symbol':'A','sector_name':'A','selection_score':1.,'size_weight':1.,'nominal_price':100.,'strong_negative':False},
          {'ticker_symbol':'B','sector_name':'B','selection_score':0.,'size_weight':1.,'nominal_price':100.,'strong_negative':False}]
    neutral=probe(pool,{}, {},'Full IntelliVest',s,100000,(1.,()))
    blocked=probe(pool,{}, {},'Full IntelliVest',s,100000,(1.,('A',)))
    check('feedback sector restriction reaches eligibility','A' not in [x['ticker_symbol'] for x in blocked['eligible']])
    check('binding sector restriction can change final quantities',basket(neutral['orders'])!=basket(blocked['orders']))
    half=probe(pool,{}, {},'Full IntelliVest',s,100000,(.5,()))
    check('feedback capacity reaches actual budget',half['budget']==neutral['budget']/2)
    check('No Feedback suppresses dynamic policy',basket(probe(pool,{}, {},'No Feedback',s,100000,(.25,('A',)))['orders'])==basket(neutral['orders']))
    record=decision_record(pd.Timestamp('2022-01-03'),s,'Full IntelliVest',pool,{}, {},100000,(1.,()),(1.,()),neutral['budget'],neutral['selected'],neutral['orders'],'original')
    check('reserve is outside brokerage and not deducted twice',record['protected_reserve_in_brokerage']==0 and neutral['budget']==s.buffer*.25)
    check('cash authorization waterfall reconciles',abs(record['deferred_accumulated_cash']+record['tier_withheld']+record['risk_withheld']+record['budget_cent_rounding']+record['no_candidate_budget']+record['slot_cent_rounding']+record['unaffordable_selected_slots']+record['whole_share_residual_positive_slots']+record['proposed_notional']-100000)<1e-8)
    check('alternative authorization retains protected monthly transfer',propose(pool,{}, {},'Full IntelliVest',s,100000,(1.,()),authorization='accumulated_approved_cash_v1')[0]==25000 and s.buffer==5000)
    frame=pd.DataFrame({'date':pd.bdate_range('2022-01-01',periods=3),'equity':[101000.,103020.,101989.8],
                        'cash':[0.,0.,0.],'stock_value':[101000.,103020.,101989.8],'contribution':[0.,0.,0.],
                        'return':[.01,.02,-.01],'cash_fraction':[0.,0.,0.]})
    calc=sharpe_diagnostic(frame)
    with localcontext() as context:
        context.prec=50
        rs=list(map(Decimal,['.01','.02','-.01']))
        mean=sum(rs)/3;sd=(sum((x-mean)**2 for x in rs)/2).sqrt()
        exact=(Decimal(252).sqrt()*(mean-Decimal('.04')/252)/sd)
    check('Sharpe agrees with independent Decimal sample calculation',abs(calc['sharpe']-float(exact))<1e-12)
    check('geometric annualization independent product',abs(calc['annualized_return']-(1.01*1.02*.99)**84+1)<1e-10)
    check('linear daily risk-free conversion',calc['daily_rf']==.04/252)
    geo=sharpe_diagnostic(frame,'effective_geometric')
    check('effective annual benchmark compounds to 4 percent',abs((1+geo['daily_rf'])**252-1-.04)<1e-13)
    constant=frame.copy();constant['return']=0.;constant['equity']=100000.;constant['cash']=100000.;constant['stock_value']=0.;constant['cash_fraction']=1.
    check('constant zero-return Sharpe explicitly undefined',np.isnan(sharpe_diagnostic(constant)['sharpe']))
    tiny=constant.copy();tiny['return']=[1e-7,-1e-7,0]
    check('small but nonconstant volatility is not clipped or hidden',sharpe_diagnostic(tiny)['sharpe_valid'] and sharpe_diagnostic(tiny)['sharpe']< -1000)
    overlay=cash_overlay(constant,.04)
    daily=(1.04)**(1/252)-1
    check('cash-only interest compounds correctly',abs(overlay.equity.iloc[-1]-100000*(1+daily)**3)<1e-8)
    check('cash-only matched benchmark has constant differential returns',np.isnan(sharpe_diagnostic(overlay,'effective_geometric')['sharpe']))
    contributed=constant.copy();contributed['contribution']=[5000.,0.,5000.];contributed['equity']=[105000.,105000.,110000.];contributed['cash']=contributed.equity
    zero=cash_overlay(contributed,0.)
    check('contributions do not create returns',np.allclose(zero['return'],0))
    check('zero-interest overlay reproduces original returns',np.allclose(cash_overlay(frame,0.)['return'],frame['return']))
    hhi=pd.DataFrame({'hhi':[np.nan,.68,.2]})
    h=hhi_diagnostic(hhi)
    check('equity sector weights hand HHI',abs(.8**2+.2**2-.68)<1e-12)
    check('HHI undefined sessions excluded from corrected denominator',h['hhi_undefined_sessions']==1 and h['corrected_valid_hhi_breach_frequency']==.5 and h['original_all_session_breach_frequency']==1/3)
    (out/'FOCUSED_CHECKS.json').write_text(json.dumps({'status':'passed','count':len(passed),'checks':passed},indent=2)+'\n')
    print(f'{len(passed)} focused diagnostics checks passed',flush=True)
    return passed
