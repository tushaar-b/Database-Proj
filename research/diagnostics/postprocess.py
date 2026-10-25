"""Explicit attribution/reporting refinement; financial simulations remain frozen."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import numpy as np
import pandas as pd
from research.diagnostics.runner import sha,verify_preserved
from research.diagnostics.events import trace_events
from research.investor_scenarios import scenarios
from research.diagnostics.report import generate


def main(out):
    protected_names=['CONTROLLED_REPLAY_SUMMARIES.csv','REPLAY_VALUATIONS.csv','REPLAY_TRADES.csv','REPLAY_DECISIONS.csv',
                     'SHARPE_DIAGNOSTICS.csv','CASH_RETURN_PATHS.csv','EXPOSURE_MATCHED_COMPARISONS.csv','UNCERTAINTY.csv']
    before={name:sha(out/name) for name in protected_names}
    cfg=json.loads((out/'DIAGNOSTIC_CONFIG.json').read_text())
    cache={}
    for key,value in json.loads((Path(cfg['baseline'])/'ranking_cache.json').read_text()).items():
        day,tier,momentum=key.split('|');cache[(day,tier,momentum=='True')]=value
    data=pd.read_csv(cfg['dataset'],usecols=['date'],parse_dates=['date'])
    days=pd.DatetimeIndex(sorted(data.date.unique()))
    events=pd.read_csv(out/'REPLAY_POLICY_CHANGES.csv',parse_dates=['date'])
    diagnostics=pd.read_csv(out/'REPLAY_DIAGNOSTICS.csv',parse_dates=['date'])
    trace,opportunities=trace_events(events,diagnostics,cache,{s.name:s for s in scenarios()},days)
    trace.to_csv(out/'FEEDBACK_TRACE.csv',index=False)
    opportunities.to_csv(out/'FEEDBACK_EVENT_OPPORTUNITIES.csv',index=False)
    trace.groupby(['variant','reason_for_no_change']).size().rename('events').reset_index().to_csv(out/'FEEDBACK_EVENT_CLASSIFICATION.csv',index=False)
    # No outside-household savings stock was modeled. Zero extra transfers is
    # an assumption; do not imply a measured outside account balance of zero.
    keys=['variant','window','scenario','strategy']
    execution_dates=pd.read_csv(out/'REPLAY_DECISIONS.csv',parse_dates=['date','execution_date'])[keys+['date','execution_date']]
    cash_closes=pd.read_csv(out/'REPLAY_VALUATIONS.csv',parse_dates=['date'])[keys+['date','cash']].rename(columns={'date':'execution_date','cash':'cash_left_after_purchases'})
    for name in ['CASH_UTILIZATION.csv','REPLAY_DIAGNOSTICS.csv']:
        df=pd.read_csv(out/name,parse_dates=['date'])
        df=df.drop(columns=['execution_date','cash_left_after_purchases','overnight_cash_adjustment'],errors='ignore')
        df=df.merge(execution_dates,on=keys+['date'],validate='one_to_one')
        df=df.merge(cash_closes,on=keys+['execution_date'],validate='many_to_one')
        assert df.cash_left_after_purchases.notna().all()
        df['overnight_cash_adjustment']=df.cash_left_after_purchases-df.brokerage_cash_before+df.executed_cost
        df['household_savings_not_yet_transferred']=np.nan
        df['outside_household_balance_modeled']=False
        df['additional_household_transfers_assumed']=0.
        df.to_csv(out/name,index=False)
    diagnostics=pd.read_csv(out/'REPLAY_DIAGNOSTICS.csv')
    diagnostics['held_stock_count']=diagnostics.holdings.map(lambda v:sum(q>0 for q in json.loads(v).values()))
    diagnostics['held_sector_count']=diagnostics.sector_weights.map(lambda v:len(json.loads(v)))
    breadth=diagnostics.groupby(['variant','scenario','strategy'])[['held_stock_count','held_sector_count']].mean().reset_index()
    breadth.to_csv(out/'HOLDINGS_BREADTH.csv',index=False)
    cash_profiles=pd.read_csv(out/'CASH_PROFILE_SUMMARY.csv')
    cash_profiles['modeled_gross_household_resources_initial_brokerage_plus_income']=cash_profiles.initial_approved_brokerage_cash+cash_profiles.gross_household_income_flow
    cash_profiles.to_csv(out/'CASH_PROFILE_SUMMARY.csv',index=False)
    unique=[]
    for (variant,strategy),g in cash_profiles.groupby(['variant','strategy']):
        unique.append({'variant':variant,'strategy':strategy,
            'mean_profile_unique_funding_deployed':g.unique_brokerage_funding_deployed_ratio.mean(),
            'pooled_unique_funding_deployed':g.cash_deployed_including_fees.sum()/g.total_unique_brokerage_funding.sum(),
            'mean_profile_budget_fill':g.decision_budget_fill_ratio.mean()})
    pd.DataFrame(unique).to_csv(out/'CASH_AGGREGATION.csv',index=False)
    generate(out)
    assert all(sha(out/name)==digest for name,digest in before.items()),'Financial/statistical output changed during reporting refinement'
    paths=[Path('research/diagnostics')/name for name in ['events.py','report.py','postprocess.py']]
    for path in paths:
        dest=out/'postprocessing_source'/path
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    manifest={'time_utc':datetime.now(timezone.utc).isoformat(),
        'clarification':'Primary feedback comparison is active versus initial fixed policy. Persisting the previous restriction is a separate counterfactual; releases are not new effects against a baseline that never blocked it.',
        'outside_household_balance':'unmodeled, hence NA; zero additional transfer remains explicit assumption',
        'financial_and_statistical_output_sha256_unchanged':before,
        'source_sha256':{str(p):sha(p) for p in paths},'original_inputs_unchanged':verify_preserved(out)}
    (out/'POSTPROCESSING_MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Attribution and reporting refinement completed; all financial/statistical output hashes unchanged',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,default=Path('research/results/2026-10-24-diagnostics'))
    main(p.parse_args().out)
