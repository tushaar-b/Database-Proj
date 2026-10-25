"""Independent all-account reconciliation and deterministic Phase 8 replay checks."""
import copy
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research.phase8.experiments.runner import OUT,preserve
from research.phase8.market import Market
from research.phase8.experiments.engine import run
from research.phase8.policies.construction import V4,V5,SELL,Guard
from research.investor_scenarios import scenarios
from research.diagnostics.metrics import block_interval
from research.risk_metrics import performance
from research.diagnostics.runner import sha


def verify(out=OUT):
    passed=[]
    def check(name,condition):
        assert condition,name
        passed.append(name)
    config=json.loads((out/'RUN_CONFIG.json').read_text())
    check('all earlier evidence and application sources unchanged',preserve(out)==len(json.loads((out/'PRESERVED_HASHES.json').read_text())))
    check('market dataset hash unchanged',sha(Path(config['dataset']))==config['dataset_sha256'])
    for path,digest in config['code_sha256'].items():assert sha(out/'source_snapshot'/path)==digest,path
    check('executed source snapshot hashes match',True)
    check('all 36 original V1 accounts reproduced before new comparisons',json.loads((out/'V1_REPRODUCTION.json').read_text())['runs']==36)
    check('all 36 shared-engine V1 accounts match original',json.loads((out/'V1_SHARED_ENGINE_PARITY.json').read_text())['runs']==36)
    v=pd.read_csv(out/'risk_metrics.csv',parse_dates=['date']);d=pd.read_csv(out/'recommendation_decisions.csv',parse_dates=['date','execution_date'])
    t=pd.read_csv(out/'trade_history.csv',parse_dates=['date','decision_date']);a=pd.read_csv(out/'authority_ledger.csv',parse_dates=['date'])
    s=pd.read_csv(out/'investor_level_results.csv')
    keys=['window','scenario','policy','kind']
    conservation=v.external_grants+v.recycled_grants-v.external_spent-v.recycled_spent-v.expired_authority-v.revoked_authority
    check('authority conservation on every daily observation',np.allclose(conservation,v.authority_balance,rtol=1e-12,atol=1e-6))
    check('cash is nonnegative and authority never exceeds cash',v.cash.min()>=-1e-6 and ((v.authority_balance-v.cash)<=1e-6).all())
    approvals=a[a.action=='approve']
    check('no duplicate monthly approval per account',not approvals.duplicated(keys+['date']).any())
    check('all principal versions receive identical contributions',(v[v.kind=='principal'].groupby(['window','scenario','date']).contribution.nunique()==1).all())
    check('all principal versions receive the same unique external grants',(v[v.kind=='principal'].groupby(['window','scenario','date']).external_grants.nunique()==1).all())
    check('no hidden initial purchase grant',all(abs(g.external_grants.iloc[0]-g.contribution.iloc[0]*{'CONSERVATIVE':.25,'MODERATE':.5,'AGGRESSIVE':.75}[g.tier.iloc[0]])<1e-7 for _,g in v.groupby(keys)))
    buy=t[t.side=='BUY'];sell=t[t.side=='SELL']
    check('whole shares and delayed execution for every simulated trade',((buy.quantity>0)&(buy.quantity==buy.quantity.astype(int))&(buy.date>buy.decision_date)).all() and ((sell.quantity>0)&(sell.quantity==sell.quantity.astype(int))&(sell.date>sell.decision_date)).all())
    check('no duplicate buy or sell execution',not t[t.side.isin(['BUY','SELL'])].duplicated(keys+['decision_date','ticker','side']).any())
    check('selling occurs only in the explicitly new research arm',set(sell.policy.unique())<= {'V5_SELL'})
    check('new household funding and reserve protections hold',not d.new_household_authority_violation.any() and not d.reserve_violation.any() and not d.authority_violation.any())
    check('fresh household authority draw does not exceed current protected surplus',(d.fresh_household_draw<=d.new_monthly_buffer+1e-7).all())
    check('all executed costs fit saved authorized batch budgets',(d.executed_cost<=d.authorized_batch_budget+1e-6).all())
    shock=d[(d.kind=='household_deterioration')&(d.date>='2024-01-01')&(d.date<'2024-04-01')]
    check('deteriorating-household suspension actually executed',len(shock)==45 and (shock.executed_cost==0).all() and (shock.authority_before==0).all())
    for _,g in v.groupby(keys):
        g=g.sort_values('date');before=np.r_[100000.,g.equity.iloc[:-1]]+g.contribution
        assert np.allclose(g['return'],g.equity/before-1,rtol=1e-10,atol=1e-12)
    check('contribution-adjusted return identity for all 249 accounts',True)
    for row in s.itertuples():
        assert row.authorized_budget_utilization<=1+1e-10
        assert row.hhi_breach_sessions<=row.hhi_valid_sessions
    check('unique external authority utilization is bounded without double-counting',True)
    check('undefined HHI sessions not treated as diversified breach observations',all(g.hhi.notna().sum()==r.hhi_valid_sessions for _,g in v.groupby(keys) for r in s[(s.window==g.window.iloc[0])&(s.scenario==g.scenario.iloc[0])&(s.policy==g.policy.iloc[0])&(s.kind==g.kind.iloc[0])].itertuples()))
    market=Market(pd.read_csv(config['dataset'],parse_dates=['date']))
    trade_groups={key:group for key,group in t.groupby(keys)};guarded={'V3','V4','V5','V5_SELL','GUARDS_ONLY','FEAS_ONLY','TOPUP_ONLY','V4_NO_MOMENTUM'}
    verified_days=0;guarded_batches=0;sale_batches=0
    for key,g in v.groupby(keys):
        g=g.sort_values('date');transactions=trade_groups.get(key,pd.DataFrame())
        by_day={day:group.to_dict('records') for day,group in transactions.groupby('date')} if len(transactions) else {}
        quantity=np.zeros(len(market.tickers),dtype=int);basis=np.zeros(len(quantity));cash=100000.;realized=0.
        if key[3]=='concentrated_start':
            i=market.index['ADANIENT'];quantity[i]=52;basis[i]=52*market.prices[market.dates.get_loc(g.date.iloc[0])-1,i];cash-=basis[i]
        for row in g.itertuples():
            di=market.dates.get_loc(row.date);prices=market.prices[di]
            cash+=row.contribution;split=np.where(market.splits[di]>0,market.splits[di],1.)
            exact=quantity*split;rounded=np.floor(exact+1e-6).astype(int);fractions=np.maximum(0.,exact-rounded)
            cash+=float(exact@market.dividends[di])
            for i in np.where(fractions>1e-6)[0]:
                proceeds=fractions[i]*prices[i];removed=basis[i]*fractions[i]/exact[i];basis[i]-=removed;cash+=proceeds;realized+=proceeds-removed
            quantity=rounded;day_transactions=by_day.get(row.date,[])
            before_sales=quantity.copy();sold=np.zeros_like(quantity)
            for tr in day_transactions:
                i=market.index[tr['ticker']]
                if tr['side']!='SELL':continue
                n=int(tr['quantity']);assert n<=quantity[i]
                assert np.isclose(tr['notional'],n*prices[i]*(1-.0005),rtol=1e-12)
                assert np.isclose(tr['fee'],tr['notional']*.001,rtol=1e-12)
                removed=basis[i]*n/quantity[i];basis[i]-=removed;quantity[i]-=n;sold[i]+=n
                profit=tr['notional']-tr['fee']-removed;realized+=profit;cash+=tr['notional']-tr['fee']
                assert abs(profit-tr['realized_gain'])<1e-6
            if sold.any():
                from research.phase8.policies.construction import hhi
                assert float(sold@prices)<=.1*float(before_sales@prices)+1e-6
                assert float(sold@prices)>=500-1e-6 and quantity.sum()>0
                assert hhi(quantity*prices,market.sector_matrix)<hhi(before_sales*prices,market.sector_matrix)-1e-12
                sale_batches+=1
            before_buy=quantity.copy();prebuy_cash=cash;added=np.zeros_like(quantity);debit=0.;decision_date=None
            for tr in day_transactions:
                if tr['side']!='BUY':continue
                i=market.index[tr['ticker']];n=int(tr['quantity']);decision_date=tr['decision_date']
                assert np.isclose(tr['notional'],n*prices[i]*1.0005,rtol=1e-12)
                assert np.isclose(tr['fee'],tr['notional']*.001,rtol=1e-12)
                assert bool(tr['topup'])==bool(quantity[i]>0)
                amount=tr['notional']+tr['fee'];basis[i]+=amount;cash-=amount;quantity[i]+=n;added[i]+=n;debit+=amount
            if added.any() and key[2] in guarded:
                lag=market.dates.get_loc(decision_date)
                assert lag<di
                guard=Guard(before_buy,prebuy_cash,prices,market.cov30[lag],market.sector_matrix)
                assert guard.allowed(added,debit,strict=key[2] in {'V5','V5_SELL'})[0],key
                after_equity=cash+float(quantity@prices)
                assert np.all(quantity*prices<=np.maximum(.20*after_equity,before_buy*prices)+1e-6)
                assert np.all(market.sector_matrix@(quantity*prices)<=np.maximum(.35*after_equity,market.sector_matrix@(before_buy*prices))+1e-6)
                guarded_batches+=1
            assert quantity.min()>=0 and cash>=-1e-6
            assert abs(cash-row.cash)<1e-5,(key,row.date,'cash',cash,row.cash)
            assert abs(float(quantity@prices)-row.stock_value)<1e-5,(key,row.date,'valuation')
            assert abs(float(basis.sum())-row.cost_basis)<1e-5,(key,row.date,'basis')
            assert abs(realized-row.realized_gain)<1e-5,(key,row.date,'realized')
            verified_days+=1
    check('independent every-day cash, holdings, basis and realized-PnL reconstruction',True)
    check('every guarded fill checks combined existing/proposed positions and sectors',guarded_batches>0)
    check('every actual corrective sale obeys size, whole-share and HHI-reduction limits',sale_batches>0)
    cache={}
    for k,value in json.loads((Path(config['frozen_baseline'])/'ranking_cache.json').read_text()).items():
        day,tier,m=k.split('|');cache[(day,tier,m=='True')]=value
    investors={s.name:s for s in scenarios()}
    for policy,scenario,kind,seed in [(V4,'medium_moderate','principal',None),(V5,'low_conservative','principal',None),(SELL,'low_conservative','concentrated_start',{'ADANIENT':52})]:
        repeated=run(market,cache,investors[scenario],policy,'2022-01-01','2025-12-31',kind,seed)
        expected=v[(v.policy==policy.name)&(v.scenario==scenario)&(v.kind==kind)&(v.window=='primary_2022_2025')].sort_values('date')
        for col in repeated['valuations'].select_dtypes(include='number').columns:
            assert np.allclose(repeated['valuations'][col],expected[col],rtol=1e-10,atol=1e-8,equal_nan=True),(policy.name,scenario,col)
    check('three independent new-policy replays reproduce numeric daily outputs',True)
    cutoff=market.dates.get_loc(pd.Timestamp('2022-12-30'))
    altered=copy.copy(market);altered.prices=market.prices.copy();altered.returns=market.returns.copy();altered.cov30=market.cov30.copy()
    altered.prices[cutoff+1:]*=10;altered.returns[cutoff+1:]*=-3;altered.cov30[cutoff+1:]*=100
    prefix=run(altered,cache,investors['medium_moderate'],V4,'2022-01-01','2022-12-30')['valuations']
    expected=v[(v.policy=='V4')&(v.scenario=='medium_moderate')&(v.kind=='principal')&(v.window=='primary_2022_2025')&(v.date<='2022-12-30')]
    check('future prices/returns/covariances cannot change an earlier replay prefix',np.allclose(prefix.equity,expected.equity,rtol=1e-12) and np.allclose(prefix['return'],expected['return'],atol=1e-12))
    pivot=v[(v.kind=='principal')&(v.window=='primary_2022_2025')&(v.scenario=='medium_moderate')].pivot(index='date',columns='policy',values='return')
    interval=block_interval(pivot.V4,pivot.V1)
    reference=pd.read_csv(out/'statistical_comparisons.csv');ref=reference[(reference.window=='primary_2022_2025')&(reference.scenario=='medium_moderate')&(reference.contrast=='V4 - V1')].iloc[0]
    check('fixed-seed paired bootstrap interval reproduces',np.allclose([interval['ci95_low'],interval['ci95_high']],[ref.ci95_low,ref.ci95_high],rtol=1e-12))
    result={'status':'passed','count':len(passed),'checks':passed,'verified_daily_account_observations':verified_days,
        'verified_guarded_buy_batches':guarded_batches,'verified_sale_batches':sale_batches,
        'verification_source_sha256':sha(Path(__file__)),'previous_files_unchanged':preserve(out)}
    (out/'INDEPENDENT_VERIFICATION.json').write_text(json.dumps(result,indent=2)+'\n')
    dest=out/'verification_source';dest.mkdir(exist_ok=True);(dest/'verify.py').write_text(Path(__file__).read_text())
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':verify()
