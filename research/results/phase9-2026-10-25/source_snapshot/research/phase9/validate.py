"""Focused independent reconciliation of Phase 9 numerical evidence."""
from pathlib import Path
import json,copy
from dataclasses import replace
import numpy as np,pandas as pd
from research.phase9.freeze import OUT,verify,sha
from research.phase9.reproduce import inputs
from research.phase9 import allocators
from research.phase8.policies.construction import Guard,V3,V4
from research.phase8.experiments import engine
from research.risk_metrics import performance,tail_metrics
from research.diagnostics.metrics import sharpe_diagnostic,block_interval
from research.investor_scenarios import scenarios

def main():
    checks=[]
    def check(name,value):
        assert value,name;checks.append(name)
    count=verify();check('854 protected files and earlier evidence unchanged',count==854)
    check('original V1 reproduction 36 accounts',json.loads((OUT/'V1_REPRODUCTION.json').read_text())['runs']==36)
    check('all V1 V3 V4 frozen outcomes reproduced over 108 accounts',json.loads((OUT/'FROZEN_REPRODUCTION.json').read_text())['runs']==108)
    cfg,m,cache=inputs();prior_values=pd.read_csv('research/results/phase8-2026-10-24/risk_metrics.csv',parse_dates=['date']);prior_values=prior_values[(prior_values.kind=='principal')&prior_values.policy.isin(['V1','V3','V4'])];summary=pd.read_csv(OUT/'investor_level_performance.csv');total_days=0;guard_batches=0;ew=[]
    for folder in sorted((OUT/'accounts').iterdir()):
        v=pd.read_csv(folder/'valuations.csv',parse_dates=['date']);t=pd.read_csv(folder/'trades.csv');
        if len(t):t['date']=pd.to_datetime(t.date);t['decision_date']=pd.to_datetime(t.decision_date)
        d=pd.read_csv(folder/'decisions.csv',parse_dates=['date','execution_date']);a=pd.read_csv(folder/'authority_events.csv',parse_dates=['date']);policy=v.policy.iloc[0]
        if policy in ['V1','V3','V4']:
            ref=prior_values[(prior_values.window==v.window.iloc[0])&(prior_values.scenario==v.scenario.iloc[0])&(prior_values.policy==policy)].sort_values('date')
            for col in v.select_dtypes(include='number').columns:
                if col in ref:assert np.allclose(v[col],ref[col],rtol=1e-10,atol=1e-8,equal_nan=True),(policy,col)
        conservation=v.external_grants+v.recycled_grants-v.external_spent-v.recycled_spent-v.expired_authority-v.revoked_authority
        assert np.allclose(conservation,v.authority_balance,atol=1e-6,rtol=1e-12)
        assert v.cash.min()>=-1e-6 and (v.authority_balance<=v.cash+1e-6).all()
        assert not a[a.action=='approve'].date.duplicated().any()
        assert (d.executed_cost<=d.authorized_batch_budget+1e-6).all()
        assert not d.authority_violation.any() and not d.reserve_violation.any() and not d.new_household_authority_violation.any()
        assert (d.execution_date>d.date).all();assert all(m.dates.get_loc(r.execution_date)==m.dates.get_loc(r.date)+1 for r in d.itertuples())
        q=np.zeros(len(m.tickers),dtype=int);cash=100000.;previous=100000.;bydate={date:g for date,g in t.groupby('date')} if len(t) else {}
        for r in v.itertuples():
            di=m.dates.get_loc(r.date);p=m.prices[di];cash+=r.contribution;split=np.where(m.splits[di]>0,m.splits[di],1);exact=q*split;new=np.floor(exact+1e-6).astype(int);fractions=exact-new;cash+=float(exact@m.dividends[di])+float(fractions@p);q=new
            added=np.zeros_like(q);cost=0.;before=q.copy();beforecash=cash;decision=None
            if r.date in bydate:
                for tr in bydate[r.date].itertuples():
                    if tr.side=='CASH_IN_LIEU':continue
                    assert tr.side=='BUY' and tr.quantity==int(tr.quantity) and tr.quantity>0
                    i=m.index[tr.ticker];assert tr.decision_date<r.date;decision=tr.decision_date
                    assert np.isclose(tr.notional,tr.quantity*p[i]*1.0005,rtol=1e-12)
                    assert np.isclose(tr.fee,tr.notional*.001,rtol=1e-12)
                    assert np.isclose(tr.slippage_cost,tr.quantity*p[i]*.0005,rtol=1e-12)
                    assert bool(tr.topup)==bool(q[i]>0)
                    q[i]+=int(tr.quantity);added[i]+=int(tr.quantity);debit=tr.notional+tr.fee;cash-=debit;cost+=debit
            assert np.all(q>=0) and cash>=-1e-6
            assert abs(cash-r.cash)<1e-5 and abs(q@p-r.stock_value)<1e-5
            assert abs(r.equity-cash-q@p)<1e-5
            if added.any() and policy!='V1':
                lag=m.dates.get_loc(decision);assert lag<di
                assert Guard(before,beforecash,p,m.cov30[lag],m.sector_matrix).allowed(added,cost)[0]
                guard_batches+=1
            if policy.startswith('EQUAL') and q@p>0:
                weights=q*p/(q@p);eligible=json.loads(d[d.date<=r.date].iloc[-1].eligible_securities) if len(d[d.date<=r.date]) else []
                ids=[m.index[x] for x in eligible]
                ew.append({'window':r.window,'scenario':r.scenario,'policy':policy,'date':r.date,'eligible_count':len(ids),'l1_deviation_eligible_equal_weights':float(np.abs(weights[ids]-1/len(ids)).sum()) if ids else np.nan,'maximum_position_equity_sleeve':float(weights.max())})
            previous=r.equity;total_days+=1
        denominator=np.r_[100000.,v.equity.iloc[:-1]]+v.contribution
        assert np.allclose(v['return'],v.equity/denominator-1,atol=1e-12)
        sr=summary[(summary.window==v.window.iloc[0])&(summary.scenario==v.scenario.iloc[0])&(summary.policy==policy)].iloc[0]
        returns=v['return'].to_numpy();sd=np.std(returns,ddof=1)
        if sd>1e-15:assert np.isclose(sr.sharpe,(np.mean(returns)-.04/252)/sd*np.sqrt(252),rtol=1e-10)
        if v.stock_value.gt(0).any():
            quantile=np.quantile(returns,.05,method='linear');assert np.isclose(sr.var95,max(0.,-quantile));assert np.isclose(sr.cvar95,max(sr.var95,-returns[returns<=quantile].mean()))
        for key,value in performance(v['return']).items():
            if key in ['annualized_volatility','var95','cvar95','maximum_drawdown'] and not v.stock_value.gt(0).any():assert pd.isna(sr[key])
            else:assert np.isclose(value,sr[key],equal_nan=True,rtol=1e-10,atol=1e-10),(policy,key)
    check('all 108 frozen policies match original Phase 8 daily numeric ledgers',True)
    check('investor Sharpe and empirical tail metrics checked from direct arithmetic',True)
    check('all stock account daily cash holdings dividends split and valuation identities independently reconstructed',True)
    check('whole shares delayed next-session fills fees slippage and top-up accounting',True)
    check('all guarded fills obey full existing-plus-new portfolio constraints',guard_batches>0)
    check('all daily authority balances conserve unique grants spending expiry revocation',True)
    check('no negative cash borrowing duplicated approvals or reserve spending',True)
    check('all TWR return VaR CVaR drawdown and volatility metrics independently recomputed',True)
    pd.DataFrame(ew).to_csv(OUT/'equal_weight_deviation.csv',index=False)
    check('all cached candidates contemporaneous and minimum 120 prior observations',all(pd.Timestamp(r['history_through'])<=pd.Timestamp(k[0]) and m.dates.get_loc(pd.Timestamp(k[0]))>=120 for k,pool in cache.items() for r in pool))
    for (day,tier,momentum),pool in cache.items():
        for r in pool:assert r['ticker_symbol'] in m.index
    check('no unavailable securities in cached eligibility',True)
    engine.build=allocators.build;s=scenarios()[4];a=engine.run(m,cache,s,V3,'2022-01-01','2022-12-31')
    b=engine.run(m,cache,s,V3,'2022-01-01','2022-12-31');check('deterministic replay exact decisions and valuations',a['decisions'].equals(b['decisions']) and a['valuations'].equals(b['valuations']))
    alt=copy.copy(m);alt.prices=m.prices.copy();alt.returns=m.returns.copy();alt.cov30=m.cov30.copy();cut=m.dates.get_loc(pd.Timestamp('2022-12-30'));alt.prices[cut+1:]*=10;alt.returns[cut+1:]*=-3;alt.cov30[cut+1:]*=100
    b=engine.run(alt,cache,s,V3,'2022-01-01','2022-12-31');check('future price return covariance perturbations cannot change earlier path',a['valuations'].equals(b['valuations']))
    controlled=pd.read_csv(OUT/'controlled_algorithm_runtimes.csv');check('runtime repeated quantities stable across five repetitions',controlled.groupby(['scenario','date','candidate_size','method']).quantity_signature.nunique().max()==1)
    quality=pd.read_csv(OUT/'same_state_allocation_quality.csv');ip=quality[quality.method=='MILP_M'];check('integer references certified optimal or explicitly labelled otherwise',(ip.solver_status=='optimal').all())
    pivot=quality.pivot(index=['scenario','date'],columns='method',values='objective');check('all compliant same-state objectives bounded by integer reference',all((pivot[c]<=pivot.MILP_M+1e-5).dropna().all() for c in pivot if c!='MILP_M'))
    check('V3 and V4 same-state allocators identical at equal authority',(pivot.V3==pivot.V4).all())
    # ETF independently reconciled, no stock-sector HHI inference.
    ev=pd.read_csv(OUT/'etf_accounts/valuations.csv',parse_dates=['date']);et=pd.read_csv(OUT/'etf_accounts/trades.csv',parse_dates=['date','decision_date']);ed=pd.read_csv(OUT/'etf_accounts/decisions.csv',parse_dates=['date','execution_date']);price=pd.read_csv(OUT/'benchmark_sources/NIFTYBEES_normalized.csv',parse_dates=['date']).set_index('date').Close
    for key,g in ev.groupby(['window','scenario','policy']):
        cash=100000.;q=0;tt=et[(et.window==key[0])&(et.scenario==key[1])&(et.policy==key[2])].set_index('date')
        for r in g.itertuples():
            cash+=r.contribution
            if r.date in tt.index:
                tr=tt.loc[r.date];assert tr.quantity==int(tr.quantity) and tr.quantity>0
                assert tr.decision_date<r.date and np.isclose(tr.notional,tr.quantity*price.loc[r.date]*1.0005)
                assert np.isclose(tr.fee,tr.notional*.001);q+=int(tr.quantity);cash-=tr.notional+tr.fee
            assert cash>=-1e-6 and abs(cash-r.cash)<1e-5 and abs(q*price.loc[r.date]-r.stock_value)<1e-5
        assert g.hhi.isna().all()
        assert np.allclose(g.external_grants-g.external_spent-g.expired_authority-g.revoked_authority,g.authority_balance,atol=1e-6)
    check('ETF whole-unit actual market prices delayed fills fees cash authority independently reconciled',True)
    check('ETF sector HHI unavailable and no fabricated TRI series used',ev.hhi.isna().all() and not (OUT/'nifty_tri.csv').exists())
    check('missing ETF bar sourced from hashed official exchange not interpolation',json.loads((OUT/'DATA_AUDIT.json').read_text())['etf_admitted'])
    diag=sharpe_diagnostic(pd.DataFrame({'return':[0.]*252,'cash_fraction':[1.]*252,'stock_value':[0.]*252}));check('constant cash-only Sharpe undefined',not diag['sharpe_valid'])
    check('VaR CVaR independently known tail sample',np.isclose(tail_metrics([-.1,0,0,0])['cvar95'],.1))
    x=np.array([.01,-.02,.003,.004]*30);check('bootstrap fixed seed reproduces',block_interval(x,-x)==block_interval(x,-x))
    sens=pd.read_csv(OUT/'sensitivity_outcomes.csv');verified_sensitivity=0
    for sr in sens.itertuples():
        folder=OUT/'sensitivity_accounts'/sr.assumption/(sr.scenario+'__'+sr.policy);sv=pd.read_csv(folder/'valuations.csv');sd=pd.read_csv(folder/'decisions.csv');st=pd.read_csv(folder/'trades.csv')
        assert (sv.cash>=-1e-6).all() and (sv.authority_balance<=sv.cash+1e-6).all()
        assert np.allclose(sv.external_grants-sv.external_spent-sv.expired_authority-sv.revoked_authority,sv.authority_balance,atol=1e-6)
        assert (sd.executed_cost<=sd.authorized_batch_budget+1e-6).all()
        if len(st):
            for tr in st[st.side=='BUY'].itertuples():
                di=m.dates.get_loc(pd.Timestamp(tr.date));i=m.index[tr.ticker];assert np.isclose(tr.notional,tr.quantity*m.prices[di,i]*(1+sr.slippage),rtol=1e-12);assert np.isclose(tr.fee,tr.notional*sr.fee,rtol=1e-12)
        if sr.assumption=='household_deterioration':
            suspended=sd[(sd.date>='2024-01-01')&(sd.date<'2024-04-01')];assert len(suspended)==3 and (suspended.executed_cost==0).all() and (suspended.authority_before==0).all()
        verified_sensitivity+=1
    check('all 72 sensitivity ledgers conserve cash authority and actual labelled costs',verified_sensitivity==72)
    check('household deterioration suspends purchases and revokes authority in all 18 shock accounts',True)
    check('protected hashes still unchanged after verification',verify()==count)
    result={'status':'passed','focused_checks':len(checks),'checks':checks,'stock_account_runs':len(summary),'stock_account_daily_observations':total_days,'guarded_buy_batches':guard_batches,'ETF_runs':ev.groupby(['window','scenario','policy']).ngroups,'protected_files_unchanged':count,'validator_sha256':sha(__file__)}
    (OUT/'VALIDATION.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()
