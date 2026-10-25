"""Execute fixed Phase 8 protocol, preserve previous evidence, export measured outputs."""
from dataclasses import asdict,replace
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import subprocess
import numpy as np
import pandas as pd
from research.diagnostics.runner import sha
from research.investor_scenarios import scenarios
from research.phase8.market import Market
from research.phase8.experiments.engine import run
from research.phase8.experiments.validate import validate
from research.phase8.policies.construction import PRINCIPAL,ABLATIONS,V1,V4,V5,SELL
from research.phase8.analysis.metrics import summarize,contrasts,exposure
from research.diagnostics.metrics import cash_overlay,sharpe_diagnostic


OUT=Path('research/results/phase8-2026-10-24')


def preserve(out):
    hashes=json.loads((out/'PRESERVED_HASHES.json').read_text())
    changed=[p for p,digest in hashes.items() if sha(Path(p))!=digest]
    assert not changed,changed
    return len(hashes)


def main(out=OUT):
    assert json.loads((out/'V1_REPRODUCTION.json').read_text())['status']=='passed'
    if (out/'RUN_CONFIG.json').exists():raise SystemExit('Refusing to overwrite an executed Phase 8 run')
    preserve(out);validate(out)
    source=Path('research/results/2026-10-23-run03');cfg=json.loads((source/'config.json').read_text())
    assert cfg['risk_limits']=={'hhi':.25,'var':.10,'volatility':.03} and cfg['risk_free_rate']==.04
    data_path=Path('research/data/2026-10-23/research_quotes.csv')
    assert sha(data_path)==cfg['dataset']['research_dataset_sha256']
    market=Market(pd.read_csv(data_path,parse_dates=['date']));cache={}
    for k,v in json.loads((source/'ranking_cache.json').read_text()).items():
        day,tier,momentum=k.split('|');cache[(day,tier,momentum=='True')]=v
    config={'created_utc':datetime.now(timezone.utc).isoformat(),'dataset_sha256':sha(data_path),'dataset':str(data_path),
        'windows':cfg['windows'],'policy_definitions':[asdict(p) for p in PRINCIPAL+[SELL]+ABLATIONS],
        'authority':'tier-approved monthly grants, no initial approval, 12-month carry expiry, reduced buffer revokes carry',
        'position_account_cap':.20,'sector_account_cap':.35,'hhi_limit':.25,'daily_volatility_limit':.03,'parametric_var_limit':.10,
        'rebalance_value_cap':.10,'minimum_sale_plan_inr':500,'fee':.001,'slippage':.0005,'risk_free':.04,'cash_interest_primary':0.,
        'seed':20261024,'bootstrap_block':20,'bootstrap_draws':2000,'evidence':'exploratory; all market periods previously inspected',
        'profiles':[asdict(s) for s in scenarios()],'frozen_baseline':str(source),'primary_window':'primary_2022_2025'}
    code_files=[p for p in Path('research/phase8').rglob('*') if p.is_file() and '__pycache__' not in str(p)]
    config['code_sha256']={str(p):sha(p) for p in code_files}
    for path in code_files:
        dest=out/'source_snapshot'/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    (out/'RUN_CONFIG.json').write_text(json.dumps(config,indent=2)+'\n')
    (out/'PHASE8_EXPERIMENTAL_METHOD.md').write_text(Path('research/phase8/config/protocol.md').read_text())
    results=[];tables={};old_summary=pd.read_csv(source/'strategy_summaries.csv')
    old_v=pd.read_csv(source/'valuations.csv',parse_dates=['date']);v1_checks=[]
    old_d=pd.read_csv(source/'decisions.csv',parse_dates=['date'])
    def execute(policy,scenario,window,kind='principal',seed=None,shock=False):
        start,end=cfg['windows'][window]
        frames=run(market,cache,scenario,policy,start,end,kind,seed,shock)
        result=summarize(frames)
        meta={'window':window,'scenario':scenario.name,'tier':scenario.tier,'surplus_group':scenario.surplus_group,'policy':policy.name,'kind':kind}
        if policy.name=='V1' and kind=='principal':
            expected=old_summary[(old_summary.window==window)&(old_summary.scenario==scenario.name)&(old_summary.strategy=='Full IntelliVest')].iloc[0]
            for name in ['annualized_return','cumulative_return','annualized_volatility','sharpe','maximum_drawdown','var95','cvar95','turnover','mean_hhi','ending_equity']:
                assert np.isclose(result[name],expected[name],rtol=1e-10,atol=1e-8,equal_nan=True),(scenario.name,window,name,result[name],expected[name])
            original=old_v[(old_v.kind=='principal')&(old_v.window==window)&(old_v.scenario==scenario.name)&(old_v.strategy=='Full IntelliVest')].sort_values('date')
            for col in ['cash','equity','stock_value','return','hhi','estimated_var95','estimated_cvar95','volatility30']:
                assert np.allclose(frames['valuations'][col],original[col],rtol=1e-10,atol=1e-8,equal_nan=True),(scenario.name,window,col)
            prior_dec=old_d[(old_d.kind=='principal')&(old_d.window==window)&(old_d.scenario==scenario.name)&(old_d.strategy=='Full IntelliVest')].sort_values('date')
            for left,right in zip(frames['decisions'].proposed_quantities,prior_dec.orders):
                assert sorted(json.loads(left))==sorted(json.loads(right)),(scenario.name,window,'recommendation parity')
            v1_checks.append({**meta,'status':'same_engine_matches_original'})
        for key,frame in frames.items():
            for k,v in meta.items():frame[k]=v
            tables.setdefault(key,[]).append(frame)
        results.append({**meta,**result})
        with (out/'PROGRESS.jsonl').open('a') as log:log.write(json.dumps({**meta,'status':'completed'})+'\n')
        print('Completed '+window+' '+scenario.name+' '+policy.name+' '+kind,flush=True)
    # Validate every V1 account in the shared new accounting engine first.
    for window in cfg['windows']:
        for s in scenarios():execute(V1,s,window)
    (out/'V1_SHARED_ENGINE_PARITY.json').write_text(json.dumps({'status':'passed','runs':36,'checks':v1_checks},indent=2)+'\n')
    for window in cfg['windows']:
        for s in scenarios():
            for policy in PRINCIPAL[1:]:execute(policy,s,window)
    for s in scenarios():
        execute(SELL,s,'primary_2022_2025','corrective_selling')
        for policy in ABLATIONS:execute(policy,s,'primary_2022_2025','construction_ablation')
        execute(replace(V4,name='V4_NO_MOMENTUM',momentum=False),s,'primary_2022_2025','momentum_ablation')
    primary_names={'low_conservative','medium_moderate','high_aggressive'}
    for s in scenarios():
        if s.name not in primary_names:continue
        for policy in PRINCIPAL:execute(policy,s,'primary_2022_2025','household_deterioration',shock=True)
        for policy in [V4,V5,SELL]:execute(policy,s,'primary_2022_2025','concentrated_start',seed=cfg['feedback_stress']['initial_holdings'])
    combined={key:pd.concat(frames,ignore_index=True) for key,frames in tables.items()}
    summary=pd.DataFrame(results);summary.to_csv(out/'investor_level_results.csv',index=False)
    names={'valuations':'risk_metrics.csv','decisions':'recommendation_decisions.csv','trades':'trade_history.csv',
           'policy_changes':'policy_events.csv','fills':'execution_events.csv','episodes':'breach_episodes.csv','authority_events':'authority_ledger.csv'}
    for key,name in names.items():combined[key].to_csv(out/name,index=False)
    combined['decisions'].to_csv(out/'capital_utilization.csv',index=False)
    main=summary[(summary.kind=='principal')&(summary.window=='primary_2022_2025')]
    comparison=main.groupby('policy').mean(numeric_only=True).reset_index();comparison.to_csv(out/'policy_comparison.csv',index=False)
    summary[summary.kind.isin(['construction_ablation','momentum_ablation'])].to_csv(out/'ablation_results.csv',index=False)
    contrasts(summary,combined['valuations']).to_csv(out/'statistical_comparisons.csv',index=False)
    exposure(combined['valuations'],combined['trades']).to_csv(out/'exposure_adjusted.csv',index=False)
    # Cash-return assumptions do not alter trades or feed extra buying power.
    sensitivity=[]
    for (scenario,policy),v in combined['valuations'][(combined['valuations'].kind=='principal')&(combined['valuations'].window=='primary_2022_2025')].groupby(['scenario','policy']):
        for cash_rate in [0.,.04]:
            overlay=cash_overlay(v,cash_rate)
            for benchmark in ['legacy_linear','effective_geometric']:
                sensitivity.append({'scenario':scenario,'policy':policy,'cash_return':cash_rate,'benchmark':benchmark,**sharpe_diagnostic(overlay,benchmark)})
    pd.DataFrame(sensitivity).to_csv(out/'cash_interest_sensitivity.csv',index=False)
    # Path comparisons are not the same as same-state policy intervention.
    path=[];dec=combined['decisions'];tr=combined['trades']
    for (kind,window,scenario),group in dec.groupby(['kind','window','scenario']):
        for a,b in [('V5','V4'),('V5_SELL','V5')]:
            if not {a,b}.issubset(set(group.policy)):continue
            x=group[group.policy==a][['date','proposed_quantities','executed_quantities']]
            y=group[group.policy==b][['date','proposed_quantities','executed_quantities']]
            m=x.merge(y,on='date',suffixes=('_a','_b'))
            path.append({'kind':kind,'window':window,'scenario':scenario,'contrast':a+' - '+b,
                'different_proposals':int((m.proposed_quantities_a!=m.proposed_quantities_b).sum()),
                'different_buy_executions':int((m.executed_quantities_a!=m.executed_quantities_b).sum())})
    pd.DataFrame(path).to_csv(out/'feedback_path_differences.csv',index=False)
    summary[['window','scenario','policy','kind','detected_breach_episodes','policy_updates','changed_recommendations',
             'actual_trade_changed_decisions','hhi_episodes_resolved','hhi_episode_resolution_fraction','hhi_breach_sessions',
             'recommendation_response_sessions','feedback_incremental_fees','feedback_incremental_slippage']].to_csv(out/'feedback_effectiveness.csv',index=False)
    # Locate original nominal one-share witnesses, without assuming every one
    # can be resolved under the newly explicit risk/position constraints.
    old_cash=pd.read_csv('research/results/2026-10-24-diagnostics/CASH_UTILIZATION.csv',parse_dates=['date'])
    witnesses=old_cash[(old_cash.variant=='original')&(old_cash.strategy=='Full IntelliVest')&(old_cash.proposed_notional==0)&old_cash.available_one_share_candidate][['scenario','date']]
    resolved=witnesses.merge(dec[(dec.kind=='principal')&(dec.window=='primary_2022_2025')],on=['scenario','date'])
    resolved['original_witness_executed_now']=resolved.executed_cost>0
    resolved.groupby('policy').agg(original_witnesses=('date','size'),executed_now=('original_witness_executed_now','sum')).to_csv(out/'original_218_resolution.csv')
    assert not summary.household_new_draw_violations.any() and not summary.reserve_violations.any() and not summary.authority_violations.any()
    preserved=preserve(out)
    (out/'EXECUTION_VALIDATION.json').write_text(json.dumps({'status':'passed','runs':len(summary),'previous_files_unchanged':preserved,
        'zero_household_new_draw_violations':True,'zero_reserve_violations':True,'zero_authority_violations':True,'no_database_connections':True},indent=2)+'\n')
    from research.phase8.analysis.report import generate
    generate(out)
    (out/'GIT_STATUS.txt').write_text(subprocess.check_output(['git','status','--short','--','research/phase8','research/results/phase8-2026-10-24'],text=True))
    (out/'OUTPUT_HASHES.json').write_text(json.dumps({str(p.relative_to(out)):sha(p) for p in out.rglob('*') if p.is_file() and p.name!='OUTPUT_HASHES.json'},indent=2)+'\n')
    print('Phase 8 complete '+str(out),flush=True)


if __name__=='__main__':main()
