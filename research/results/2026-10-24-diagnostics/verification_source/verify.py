"""Independent post-run validation, including event attribution and reproducibility."""
import argparse
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd
from research.investor_scenarios import scenarios
from research.diagnostics.instrumentation import decision_record,probe,policy_json
from research.diagnostics.events import trace_events
from research.diagnostics.metrics import exposure_series,contiguous_max_drawdown,cash_overlay,sharpe_diagnostic,block_interval
from research.diagnostics.runner import verify_preserved,sha
from research.diagnostics.replay import replay
from backend.config import settings


def verify(out):
    passed=[]
    def check(name,condition):
        assert condition,name
        passed.append(name)
    s=scenarios()[0]
    days=pd.DatetimeIndex(['2022-01-03','2022-02-01'])
    def pool(price):
        return [{'ticker_symbol':'A','sector_name':'A','selection_score':1.,'size_weight':1.,'nominal_price':price,'strong_negative':False},
                {'ticker_symbol':'B','sector_name':'B','selection_score':0.,'size_weight':1.,'nominal_price':price,'strong_negative':False}]
    pools=[pool(10000.),pool(100.)]
    meta={'variant':'synthetic_fixture','window':'fixture','scenario':s.name,'strategy':'Full IntelliVest'}
    records=[]
    for day,p in zip(days,pools):
        after=probe(p,{}, {},'Full IntelliVest',s,100000.,(1.,('A',)))
        record=decision_record(day,s,'Full IntelliVest',p,{}, {},100000.,(1.,('A',)),(1.,()),after['budget'],after['selected'],after['orders'],'original')
        records.append({**record,**meta})
    events=pd.DataFrame([{**meta,'date':days[0],'previous_policy':policy_json((1.,())),
        'updated_policy':policy_json((1.,('A',))),'old_multiplier':1.,'new_multiplier':1.,
        'old_blocked':'[]','new_blocked':'["A"]','var_breach':False,'volatility_breach':False,'hhi_breach':True,
        'var_threshold':.1,'volatility_threshold':.03,'hhi_threshold':.25,'brokerage_cash_at_event':100000.}])
    cache={(str(day.date()),s.tier,True):p for day,p in zip(days,pools)}
    trace,opportunities=trace_events(events,pd.DataFrame(records),cache,{s.name:s},days)
    check('event probes all later opportunities, not first only',len(opportunities)==2 and not opportunities.recommendation_changed.iloc[0] and opportunities.recommendation_changed.iloc[1])
    check('first actual changed recommendation gets observed-session latency',trace.changed_opportunities_count.iloc[0]==1 and trace.event_response_sessions.iloc[0]==1)
    release=events.copy()
    release['previous_policy']=policy_json((1.,('A',)))
    release['updated_policy']=policy_json((1.,()))
    release['old_blocked']='["A"]';release['new_blocked']='[]';release['hhi_breach']=False
    neutral_records=[]
    for day,p in zip(days,pools):
        choice=probe(p,{}, {},'Full IntelliVest',s,100000.,(1.,()))
        neutral_records.append({**decision_record(day,s,'Full IntelliVest',p,{}, {},100000.,(1.,()),(1.,()),choice['budget'],choice['selected'],choice['orders'],'original'),**meta})
    release_trace,release_op=trace_events(release,pd.DataFrame(neutral_records),cache,{s.name:s},days)
    check('restoring neutral policy does not count as a Full-vs-No-Feedback effect',not release_trace.actual_recommendation_changed.iloc[0] and not release_op.recommendation_changed.any())
    check('prior-state release counterfactual is separately retained',release_trace.previous_policy_counterfactual_changed_opportunities.iloc[0]==1 and release_op.previous_policy_counterfactual_changed.any())
    # Exposure normalization must recover the same sleeve return at half/full exposure.
    dates=pd.bdate_range('2022-01-03',periods=3)
    half=pd.DataFrame({'date':dates,'equity':[100000.,101000.,102020.],'stock_value':[50000.,51000.,52020.],
        'cash':[50000.,50000.,50000.],'contribution':[0.,0.,0.],'return':[0.,.01,102020/101000-1]})
    all_equity=pd.DataFrame({'date':dates,'equity':[100000.,102000.,104040.],'stock_value':[100000.,102000.,104040.],
        'cash':[0.,0.,0.],'contribution':[0.,0.,0.],'return':[0.,.02,.02]})
    empty=pd.DataFrame()
    a=exposure_series(half,empty);b=exposure_series(all_equity,empty)
    check('per-unit equity return removes simple cash dilution',np.allclose(a.unit_exposure_return_gross.iloc[1:],b.unit_exposure_return_gross.iloc[1:],atol=1e-12))
    check('zero opening stock exposure is undefined, not zero sleeve return',np.isnan(a.unit_exposure_return_net.iloc[0]))
    check('drawdown does not compound across missing matched dates',abs(contiguous_max_drawdown(dates[[0,2]],[-.1,-.1],dates)-.1)<1e-12)
    config=json.loads((out/'DIAGNOSTIC_CONFIG.json').read_text())
    for key,value in config['effective_settings'].items():setattr(settings,key,value)
    old_hashes=json.loads((out/'PRESERVED_INPUT_HASHES.json').read_text())
    check('all previous study, paper, dataset and inspected sources preserved',verify_preserved(out)==len(old_hashes))
    for file,digest in config['diagnostic_code_sha256'].items():
        assert sha(out/'source_snapshot'/file)==digest,file
    check('executed diagnostic snapshot matches code hashes',True)
    d=pd.read_csv(out/'CASH_UTILIZATION.csv')
    parts=['deferred_accumulated_cash','tier_withheld','risk_withheld','budget_cent_rounding','no_candidate_budget','slot_cent_rounding','unaffordable_selected_slots','whole_share_residual_positive_slots','proposed_notional']
    check('every observed cash authorization waterfall reconciles',np.allclose(d[parts].sum(axis=1),d.brokerage_cash_before,rtol=1e-12,atol=1e-6))
    check('no simulated protected reserve is included in brokerage',(d.protected_reserve_in_brokerage==0).all())
    check('every actual fill including costs respects budget',(d.executed_cost<=d.actual_budget+1e-6).all())
    check('all decisions, including zero orders, have reconciled cash after purchases',d.cash_left_after_purchases.notna().all() and np.allclose(d.cash_left_after_purchases,d.brokerage_cash_before-d.executed_cost+d.overnight_cash_adjustment,atol=1e-8))
    e=pd.read_csv(out/'FEEDBACK_TRACE.csv');op=pd.read_csv(out/'FEEDBACK_EVENT_OPPORTUNITIES.csv')
    check('every observed event has one explicit primary classification',e.event_id.is_unique and e.reason_for_no_change.notna().all())
    check('all event-level changed opportunity counts reconcile',all(int(row.changed_opportunities_count if pd.notna(row.changed_opportunities_count) else 0)==int(op.loc[op.event_id==row.event_id,'recommendation_changed'].sum()) for row in e.itertuples()))
    check('all events with opportunities propagate the policy',e.loc[e.opportunity_before_policy_replaced,'policy_propagated'].all())
    check('original primary event effect agrees with fixed-policy decision null',not e.loc[e.variant=='original','actual_recommendation_changed'].any())
    h=pd.read_csv(out/'HHI_DIAGNOSTICS.csv')
    denominator=h.hhi_valid_sessions.replace(0,np.nan)
    check('HHI valid and undefined counts reconcile',(h.hhi_valid_sessions+h.hhi_undefined_sessions==h.sessions).all())
    check('HHI corrected frequencies use valid sessions',np.allclose(h.corrected_valid_hhi_breach_frequency,h.hhi_breach_sessions/denominator,equal_nan=True))
    v=pd.read_csv(out/'REPLAY_VALUATIONS.csv',parse_dates=['date'])
    for _,g in v.groupby(['variant','scenario','strategy']):
        g=g.sort_values('date');before=np.r_[100000.,g.equity.iloc[:-1]]+g.contribution
        assert np.allclose(g['return'],g.equity/before-1,atol=1e-12)
        assert g.cash.min()>=-1e-6
    check('all 78 controlled accounts reconcile contributions and nonnegative cash',True)
    source=pd.read_csv(out/'REPLAY_TRADES.csv',parse_dates=['date','decision_date'])
    buys=source[source.side=='BUY']
    check('all buys have delayed dates and integer quantities',(buys.date>buys.decision_date).all() and (buys.quantity==buys.quantity.astype(int)).all())
    check('no duplicate simulated buys',not buys.duplicated(['variant','scenario','strategy','decision_date','ticker']).any())
    # Reproduce a new alternative path independently from frozen data/cache.
    data=pd.read_csv(config['dataset'],parse_dates=['date'])
    ranking={}
    for key,value in json.loads((Path(config['baseline'])/'ranking_cache.json').read_text()).items():
        day,tier,momentum=key.split('|');ranking[(day,tier,momentum=='True')]=value
    scenario=next(x for x in scenarios() if x.name=='medium_moderate')
    _,frames=replay(data,scenario,'Full IntelliVest',*config['window'],ranking,config['fee'],config['slippage'],True,None,'accumulated_approved_cash_v1')
    expected=v[(v.variant=='accumulated_approved_cash_v1')&(v.scenario==scenario.name)&(v.strategy=='Full IntelliVest')].sort_values('date')
    for col in frames['valuations'].select_dtypes(include='number').columns:
        assert np.allclose(frames['valuations'][col],expected[col],rtol=1e-10,atol=1e-8,equal_nan=True),col
    check('independent alternative-authority replay reproduces every numeric ledger field',True)
    # Recompute one frozen-trade overlay and each daily benchmark independently.
    paths=pd.read_csv(out/'CASH_RETURN_PATHS.csv',parse_dates=['date'])
    g=v[(v.variant=='original')&(v.scenario=='medium_moderate')&(v.strategy=='Full IntelliVest')].sort_values('date')
    overlay=cash_overlay(g,.04)
    stored=paths[(paths.variant=='original')&(paths.scenario=='medium_moderate')&(paths.strategy=='Full IntelliVest')&(paths.annual_cash_return==.04)].sort_values('date')
    check('frozen-trade cash overlay reproducible',np.allclose(overlay.equity,stored.equity,rtol=1e-12) and np.allclose(overlay['return'],stored['return'],atol=1e-12))
    diagnostics=pd.read_csv(out/'SHARPE_DIAGNOSTICS.csv')
    for convention in ['legacy_linear','effective_geometric']:
        result=sharpe_diagnostic(overlay,convention)
        stored=diagnostics[(diagnostics.variant=='original')&(diagnostics.window=='primary_2022_2025')&(diagnostics.scenario=='medium_moderate')&(diagnostics.strategy=='Full IntelliVest')&(diagnostics.annual_cash_return==.04)&(diagnostics.benchmark_convention==convention)].iloc[0]
        assert np.isclose(result['sharpe'],stored.sharpe,rtol=1e-10)
    check('both benchmark-convention Sharpe overlays reproduce',True)
    pairs=v[(v.scenario=='medium_moderate')&(v.strategy=='Full IntelliVest')&(v.variant.isin(['original','accumulated_approved_cash_v1']))].pivot(index='date',columns='variant',values='return')
    resampled=block_interval(pairs.accumulated_approved_cash_v1,pairs.original)
    expected=pd.read_csv(out/'UNCERTAINTY.csv')
    expected=expected[(expected.scenario=='medium_moderate')&(expected.experiment=='capital_authorization')].iloc[0]
    check('fixed-seed conditional bootstrap reproduces reported interval',np.allclose([resampled['ci95_low'],resampled['ci95_high']],[expected.ci95_low,expected.ci95_high],rtol=1e-12))
    metadata={'status':'passed','checks':passed,'count':len(passed),'code_file':'research/diagnostics/verify.py',
              'code_sha256':sha(Path('research/diagnostics/verify.py')),'synthetic_fixtures':'mathematical checks only, never financial experiment data'}
    (out/'INDEPENDENT_VERIFICATION.json').write_text(json.dumps(metadata,indent=2)+'\n')
    dest=out/'verification_source'/'verify.py';dest.parent.mkdir(exist_ok=True);dest.write_text(Path('research/diagnostics/verify.py').read_text())
    print(json.dumps(metadata,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path('research/results/2026-10-24-diagnostics'))
    verify(p.parse_args().out)
