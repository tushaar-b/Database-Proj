"""Offline controlled diagnostics. Never connects to PostgreSQL or updates old runs."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import numpy as np
import pandas as pd
from backend.config import settings
from research.investor_scenarios import scenarios
from research.strategies import POLICIES
from research.diagnostics.replay import replay
from research.diagnostics.validation import checks
from research.diagnostics.events import trace_events
from research.diagnostics.metrics import cash_overlay,sharpe_diagnostic,distribution,hhi_diagnostic,exposure_comparisons,block_interval


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def dump(path,value):
    path.write_text(json.dumps(value,indent=2,default=str,allow_nan=False)+'\n')


def verify_preserved(out):
    manifest=json.loads((out/'PRESERVED_INPUT_HASHES.json').read_text())
    failures=[path for path,digest in manifest.items() if sha(Path(path))!=digest]
    assert not failures,failures
    return len(manifest)


def reconcile(summary,frames,expected):
    for metric,actual in summary.items():
        if metric not in expected:continue
        recorded=expected[metric]
        if pd.isna(actual):assert pd.isna(recorded),metric
        else:assert np.isclose(float(actual),float(recorded),rtol=1e-10,atol=1e-8),(metric,actual,recorded)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,default=Path('research/results/2026-10-24-diagnostics'))
    parser.add_argument('--baseline',type=Path,default=Path('research/results/2026-10-23-run03'))
    parser.add_argument('--data',type=Path,default=Path('research/data/2026-10-23/research_quotes.csv'))
    args=parser.parse_args();out=args.out
    assert (out/'INITIAL_ROOT_CAUSE_REPORT.md').exists(),'Initial diagnostic report must precede implementation/execution'
    if (out/'DIAGNOSTIC_CONFIG.json').exists():raise SystemExit('Refusing to overwrite an existing diagnostic execution')
    verify_preserved(out)
    original=json.loads((args.baseline/'config.json').read_text())
    for key,value in original['effective_settings'].items():setattr(settings,key,value)
    dataset=pd.read_csv(args.data,parse_dates=['date'])
    assert sha(args.data)==original['dataset']['research_dataset_sha256']
    cache={}
    for key,value in json.loads((args.baseline/'ranking_cache.json').read_text()).items():
        day,tier,momentum=key.split('|');cache[(day,tier,momentum=='True')]=value
    investors={s.name:s for s in scenarios()}
    config={'created_utc':datetime.now(timezone.utc).isoformat(),'local_date':'2026-10-24',
        'baseline':str(args.baseline),'dataset':str(args.data),'dataset_sha256':sha(args.data),
        'effective_settings':original['effective_settings'],'window':original['windows']['primary_2022_2025'],
        'strategies':POLICIES,'seed':20261024,'fee':original['fee'],'slippage':original['slippage'],
        'principal_reproductions':36,'concentrated_start_reproductions':6,'alternative_authorization_replays':36,
        'cash_return_assumptions':[0.,.04],'cash_return_conversion':'effective annual geometric / 252 observed sessions',
        'cash_return_timing':'opening cash including beginning-session contributions; earnings kept in unspent subledger; stock trades fixed',
        'benchmark_conventions':['legacy_linear','effective_geometric'],
        'alternative_policy':'accumulated_approved_cash_v1: apply unchanged tier/multiplier to approved brokerage cash, same monthly protected transfer, no selling or held-stock re-entry',
        'exposure_bins':[0,.05,.25,.5,.75,1.0],'matching':'same profile/date and positive opening exposure; optional same bin; descriptive, no forced allocation',
        'bootstrap':{'block':20,'draws':2000,'seed':20261024,'minimum_pairs_for_interval':60},
        'versions':{m:importlib.metadata.version(m) for m in ['numpy','pandas','scipy','matplotlib']}}
    source_files=sorted(Path('research/diagnostics').glob('*.py'))
    config['diagnostic_code_sha256']={str(p):sha(p) for p in source_files}
    for path in source_files:
        dest=out/'source_snapshot'/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    dump(out/'DIAGNOSTIC_CONFIG.json',config)
    checks(out)
    old_s=pd.read_csv(args.baseline/'strategy_summaries.csv')
    old_stress=pd.read_csv(args.baseline/'feedback_stress.csv')
    old_v=pd.read_csv(args.baseline/'valuations.csv',parse_dates=['date'])
    old_d=pd.read_csv(args.baseline/'decisions.csv',parse_dates=['date'])
    baseline=old_v[old_v.kind=='principal'].copy();baseline['variant']='original'
    results=[];frames_by_name={};validation=[]
    start,end=config['window']
    def execute(s,policy,variant,seed=None):
        authorization='accumulated_approved_cash_v1' if variant=='accumulated_approved_cash_v1' else 'original'
        summary,frames=replay(dataset,s,policy,start,end,cache,config['fee'],config['slippage'],True,seed,authorization)
        meta={'variant':variant,'window':'primary_2022_2025','scenario':s.name,'strategy':policy,'tier':s.tier,'surplus_group':s.surplus_group}
        if variant in {'original','stress_original'}:
            reference=old_stress if seed else old_s[old_s.window=='primary_2022_2025']
            expected=reference[(reference.scenario==s.name)&(reference.strategy==policy)].iloc[0]
            reconcile(summary,frames,expected)
            reference_kind='feedback_stress' if seed else 'principal'
            source=old_v[(old_v.kind==reference_kind)&(old_v.window=='primary_2022_2025')&(old_v.scenario==s.name)&(old_v.strategy==policy)].sort_values('date')
            for col in frames['valuations'].select_dtypes(include='number').columns:
                assert np.allclose(frames['valuations'][col],source[col],rtol=1e-10,atol=1e-8,equal_nan=True),(s.name,policy,col)
            source_d=old_d[(old_d.kind==reference_kind)&(old_d.window=='primary_2022_2025')&(old_d.scenario==s.name)&(old_d.strategy==policy)].sort_values('date')
            assert list(frames['decisions'].orders)==list(source_d.orders),(s.name,policy,'basket mismatch')
            validation.append({**meta,'all_original_summary_fields_match':True,'all_daily_numeric_ledger_fields_match':True,'all_final_baskets_match':True})
        # Independently reconstruct sector HHI from position-level market values.
        pos=frames['positions'];v=frames['valuations']
        if len(pos):
            sector=pos.groupby(['date','sector']).market_value.sum()
            total=sector.groupby(level=0).transform('sum')
            hhi=((sector/total)**2).groupby(level=0).sum()
            assert np.allclose(hhi,v.set_index('date').loc[hhi.index,'hhi'],atol=1e-12)
        assert v.cash.min()>=-1e-6
        assert (frames['decisions'].executed_cost<=frames['decisions'].budget+1e-6).all()
        for name,frame in frames.items():
            if name=='positions':
                # Decision snapshots suffice for causal trace; full state can be
                # deterministically replayed, without a redundant large export.
                frame=frame[frame.date.isin(frames['decisions'].date)].copy() if len(frame) else frame
            for key,value in meta.items():frame[key]=value
            frames_by_name.setdefault(name,[]).append(frame)
        results.append({**meta,**summary})
        with (out/'PROGRESS.jsonl').open('a') as log:log.write(json.dumps({**meta,'status':'completed'})+'\n')
        print(f'Completed {variant}: {s.name} / {policy}',flush=True)
    for s in investors.values():
        for policy in POLICIES:execute(s,policy,'original')
    primary=[investors[x] for x in ['low_conservative','medium_moderate','high_aggressive']]
    for s in primary:
        for policy in ['No Feedback','Full IntelliVest']:
            execute(s,policy,'stress_original',original['feedback_stress']['initial_holdings'])
    # Original reproduction must pass before any controlled policy sensitivity.
    dump(out/'BASELINE_REPRODUCTION.json',{'status':'passed','runs':len(validation),'comparisons':validation})
    for s in investors.values():
        for policy in POLICIES:execute(s,policy,'accumulated_approved_cash_v1')
    combined={key:pd.concat(frames,ignore_index=True) for key,frames in frames_by_name.items()}
    for key,frame in combined.items():frame.to_csv(out/f'REPLAY_{key.upper()}.csv',index=False)
    summaries=pd.DataFrame(results);summaries.to_csv(out/'CONTROLLED_REPLAY_SUMMARIES.csv',index=False)
    events,opportunities=trace_events(combined['policy_changes'],combined['diagnostics'],cache,investors,pd.DatetimeIndex(sorted(dataset.date.unique())))
    events.to_csv(out/'FEEDBACK_TRACE.csv',index=False)
    opportunities.to_csv(out/'FEEDBACK_EVENT_OPPORTUNITIES.csv',index=False)
    events.groupby(['variant','reason_for_no_change']).size().rename('events').reset_index().to_csv(out/'FEEDBACK_EVENT_CLASSIFICATION.csv',index=False)
    cash=combined['diagnostics'].copy()
    cash['unused_authorized_budget']=np.maximum(0,cash.actual_budget-cash.executed_cost)
    cash['decision_budget_utilization']=np.divide(cash.executed_cost,cash.actual_budget,out=np.full(len(cash),np.nan),where=cash.actual_budget>0)
    cash.to_csv(out/'CASH_UTILIZATION.csv',index=False)
    cash_summary=[]
    for (variant,scenario,policy),g in cash.groupby(['variant','scenario','strategy']):
        s=investors[scenario];n=len(g)
        record={'variant':variant,'scenario':scenario,'strategy':policy,'decisions':n,
            'gross_household_income_flow':s.income*n,'mandatory_expense_flow':s.mandatory*n,
            'discretionary_expense_reported_not_deducted':s.discretionary*n,
            'monthly_reserve_target_outside_brokerage':s.reserve,'model_reserve_withheld_flow_not_verified_reserve_balance':s.reserve*n,
            'protected_reserve_in_brokerage':0.,'initial_approved_brokerage_cash':s.initial_cash,
            'approved_monthly_contributions':s.buffer*n,'total_unique_brokerage_funding':s.initial_cash+s.buffer*n,
            'cash_deployed_including_fees':float(g.executed_cost.sum()),
            'unique_brokerage_funding_deployed_ratio':float(g.executed_cost.sum()/(s.initial_cash+s.buffer*n)),
            'decision_budget_fill_ratio':float(g.executed_cost.sum()/g.actual_budget.sum()) if g.actual_budget.sum()>0 else np.nan,
            'mean_unused_authorized_cash':float(g.unused_authorized_budget.mean()),
            'zero_order_opportunities':int((g.proposed_notional==0).sum()),
            'zero_orders_despite_a_feasible_single_share':int(((g.proposed_notional==0)&g.available_one_share_candidate).sum())}
        for col in ['brokerage_cash_before','deferred_accumulated_cash','tier_withheld','risk_withheld','budget_cent_rounding','no_candidate_budget','slot_cent_rounding','unaffordable_selected_slots','whole_share_residual_positive_slots','proposed_notional','actual_budget']:
            record['mean_'+col]=float(g[col].mean())
        cash_summary.append(record)
    pd.DataFrame(cash_summary).to_csv(out/'CASH_PROFILE_SUMMARY.csv',index=False)
    # Investor-first calculation across all historical windows, plus controlled
    # primary alternatives. Never pool investor observations as independent data.
    additional=combined['valuations'][combined['valuations'].variant!='original']
    all_ledgers=pd.concat([baseline,additional],ignore_index=True)
    diag_rows=[];paths=[];hhi_rows=[];uncertainty=[];composites={}
    group_keys=['variant','window','scenario','strategy']
    for key,g in all_ledgers.groupby(group_keys):
        meta=dict(zip(group_keys,key));g=g.sort_values('date')
        hhi_rows.append({**meta,**hhi_diagnostic(g)})
        for cash_rate in [0.,.04]:
            overlay=cash_overlay(g,cash_rate)
            for bench in ['legacy_linear','effective_geometric']:
                diag_rows.append({**meta,'annual_cash_return':cash_rate,**sharpe_diagnostic(overlay,bench)})
            if key[1]=='primary_2022_2025':
                x=overlay.copy()
                for k,value in meta.items():x[k]=value
                x['annual_cash_return']=cash_rate;paths.append(x)
            composites.setdefault((key[0],key[1],key[3],cash_rate),[]).append(overlay[['date','return','cash_fraction','stock_value']].assign(scenario=key[2]))
    sharpe=pd.DataFrame(diag_rows);sharpe.to_csv(out/'SHARPE_DIAGNOSTICS.csv',index=False)
    dist=distribution(sharpe);dist.to_csv(out/'SHARPE_DISTRIBUTION.csv',index=False)
    pd.DataFrame(hhi_rows).to_csv(out/'HHI_DIAGNOSTICS.csv',index=False)
    interest_paths=pd.concat(paths,ignore_index=True);interest_paths.to_csv(out/'CASH_RETURN_PATHS.csv',index=False)
    composite_rows=[]
    for (variant,window,strategy,rate),frames in composites.items():
        g=pd.concat(frames).groupby('date')[['return','cash_fraction','stock_value']].mean().reset_index()
        for bench in ['legacy_linear','effective_geometric']:
            composite_rows.append({'variant':variant,'window':window,'strategy':strategy,'annual_cash_return':rate,
                'construction':'equal-weight daily return composite, not mean of investor Sharpe ratios',**sharpe_diagnostic(g,bench)})
    pd.DataFrame(composite_rows).to_csv(out/'SYNTHETIC_RETURN_COMPOSITES.csv',index=False)
    exposure_ledgers=combined['valuations'][combined['valuations'].variant=='original']
    strata,matched,exposure_ci,series=exposure_comparisons(exposure_ledgers,combined['trades'])
    strata.to_csv(out/'EXPOSURE_STRATA.csv',index=False);matched.to_csv(out/'EXPOSURE_MATCHED_COMPARISONS.csv',index=False)
    for scenario in investors:
        f=interest_paths[(interest_paths.variant=='original')&(interest_paths.scenario==scenario)&(interest_paths.strategy=='Full IntelliVest')]
        p=f.pivot(index='date',columns='annual_cash_return',values='return')
        uncertainty.append({'scenario':scenario,'contrast':'4 percent cash - zero cash; fixed trades','experiment':'cash_interest',**block_interval(p[.04],p[0.])})
        f=combined['valuations'][(combined['valuations'].scenario==scenario)&(combined['valuations'].strategy=='Full IntelliVest')&(combined['valuations'].variant!='stress_original')]
        p=f.pivot(index='date',columns='variant',values='return')
        uncertainty.append({'scenario':scenario,'contrast':'accumulated approved cash - original authorization','experiment':'capital_authorization',**block_interval(p.accumulated_approved_cash_v1,p.original)})
    pd.concat([pd.DataFrame(uncertainty),exposure_ci],ignore_index=True).to_csv(out/'UNCERTAINTY.csv',index=False)
    sensitivity=sharpe[sharpe.window=='primary_2022_2025'].copy()
    details=summaries[['variant','scenario','strategy','affordability_violation_rate','transaction_fees','slippage_cost','turnover','policy_adjustments','direct_feedback_changed_decisions','surplus_utilization','hhi_breach_sessions','hhi_valid_sessions','holdings_coverage']]
    sensitivity=sensitivity.merge(details,on=['variant','scenario','strategy'],validate='many_to_one')
    sensitivity.to_csv(out/'SENSITIVITY_RESULTS.csv',index=False)
    # Per-policy path comparison is distinct from a same-state intervention.
    decision_comparisons=[]
    for variant,g in combined['decisions'].groupby('variant'):
        full=g[g.strategy=='Full IntelliVest'];no=g[g.strategy=='No Feedback']
        pairs=full[['date','scenario','orders']].merge(no[['date','scenario','orders']],on=['date','scenario'],suffixes=('_full','_no'))
        pairs['different_final_recommendation']=pairs.orders_full!=pairs.orders_no
        pairs['variant']=variant;decision_comparisons.append(pairs)
    pd.concat(decision_comparisons,ignore_index=True).to_csv(out/'FEEDBACK_PATH_COMPARISON.csv',index=False)
    preserved=verify_preserved(out)
    dump(out/'PRESERVATION_CHECK.json',{'status':'passed','unchanged_protected_files':preserved,'database_connections':0,'old_output_writes':0})
    from research.diagnostics.report import generate
    generate(out)
    (out/'GIT_STATUS.txt').write_text(subprocess.check_output(['git','status','--short','--','research','backend','frontend'],text=True))
    dump(out/'OUTPUT_HASHES.json',{str(p.relative_to(out)):sha(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name!='OUTPUT_HASHES.json'})
    print('Completed diagnostics: '+str(out),flush=True)


if __name__=='__main__':main()
