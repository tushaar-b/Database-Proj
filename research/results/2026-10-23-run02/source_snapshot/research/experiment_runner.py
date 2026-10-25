"""Run admitted data only. Does not import psycopg2 or application mutation services."""
import argparse
from dataclasses import asdict
from datetime import datetime,timezone
import importlib.metadata
import json
from pathlib import Path
import subprocess
import shutil
import time
import numpy as np
import pandas as pd
from backend.config import settings
from research.data_audit import dump,sha
from research.consistency_checks import run_checks
from research.investor_scenarios import scenarios
from research.strategies import POLICIES,candidates
from research.historical_replay import replay
from research.statistical_analysis import comparisons


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',type=Path,default=Path('research/data/2026-10-23'))
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--frozen-config',type=Path,help='Replay the recorded effective nonsecret research settings')
    args=parser.parse_args()
    if args.frozen_config:
        frozen=json.loads(args.frozen_config.read_text())
        for k,value in frozen['effective_settings'].items():
            if k.startswith('MOMENTUM_') or k in {'STOCK_ANNUAL_RISK_FREE_RATE','DEFAULT_TARGET_HHI_LIMIT','RISK_VAR_LIMIT_PERCENT','RISK_DAILY_VOLATILITY_LIMIT'}:
                setattr(settings,k,value)
    if args.out.exists() and (args.out/'config.json').exists():
        raise SystemExit('Run identifier already exists; choose a new output directory.')
    args.out.mkdir(parents=True,exist_ok=True)
    admission=json.loads((args.data/'admission.json').read_text())
    run_checks(args.out)
    if admission['status']!='exploratory_restricted_universe':
        dump(args.out/'blocked.json',{'reason':admission,'financial_replay_executed':False})
        raise SystemExit('Dataset admission blocked; only mathematical diagnostics executed.')
    dataset=pd.read_csv(args.data/'research_quotes.csv',parse_dates=['date'])
    assert sha(args.data/'research_quotes.csv')==admission['research_dataset_sha256']
    assert not dataset.duplicated(['date','ticker']).any()
    windows={'primary_2022_2025':('2022-01-01','2025-12-31'),
             'early_2022_2023':('2022-01-01','2023-12-31'),
             'late_2024_2025':('2024-01-01','2025-12-31'),
             'ytd_2026':('2026-01-01',str(dataset.date.max().date()))}
    investors=scenarios()
    code_files=list(Path('research').glob('*.py'))+[Path('research/specification.md'),Path('backend/market_trends.py'),Path('backend/routers/recommendations.py'),Path('backend/services.py'),Path('backend/config.py')]
    config={'created_utc':datetime.now(timezone.utc).isoformat(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        'code_sha256':{str(p):sha(p) for p in code_files},'dataset':admission,'windows':windows,
        'scenarios':[{**asdict(s),'monthly_buffer':s.buffer} for s in investors], 'strategies':POLICIES,
        'fee':.001,'slippage':.0005,'risk_free_rate':settings.STOCK_ANNUAL_RISK_FREE_RATE,
        'risk_limits':{'hhi':settings.DEFAULT_TARGET_HHI_LIMIT,'var':settings.RISK_VAR_LIMIT_PERCENT,'volatility':settings.RISK_DAILY_VOLATILITY_LIMIT},
        'momentum_policy':__import__('backend.market_trends',fromlist=['momentum_policy']).momentum_policy(),
        'seed':20261023,'bootstrap_block':20,'bootstrap_draws':2000,
        'lookbacks':{'ranking_max_returns':252,'ranking_min_returns':120,'risk':252,'volatility':30},
        'execution':'next observed session close','calendar':'actual common provider session dates, no interpolation',
        'versions':{m:importlib.metadata.version(m) for m in ['numpy','pandas','yfinance','scipy']},
        'interpretation':'exploratory restricted surviving universe; no population significance claims'}
    # Additional mechanistic stress: high pre-existing exposure, selected only
    # from pre-start returns. It never replaces the four principal comparisons.
    prior=dataset[dataset.date<pd.Timestamp(windows['primary_2022_2025'][0])]
    prior_prices=prior.pivot(index='date',columns='ticker',values='adjusted_close')
    prior_vol=prior_prices.pct_change(fill_method=None).tail(252).std(ddof=1)
    stress_ticker=sorted(prior_vol.index,key=lambda t:(-prior_vol[t],t))[0]
    prior_close=float(prior[prior.ticker==stress_ticker].iloc[-1].nominal_close)
    stress_seed={stress_ticker:int(np.floor(90000/prior_close))}
    config['feedback_stress']={'selection':'largest pre-start 252-return sample volatility; 90% initial target equity, no future outcomes',
        'initial_holdings':stress_seed,'initial_wealth':100000,'prior_nominal_close':prior_close,
        'interpretation':'mechanistic concentration/volatility stress, not an efficacy validation sample'}
    config['effective_settings']={k:v for k,v in settings.model_dump().items() if k.startswith('MOMENTUM_') or k in {'STOCK_ANNUAL_RISK_FREE_RATE','DEFAULT_TARGET_HHI_LIMIT','RISK_VAR_LIMIT_PERCENT','RISK_DAILY_VOLATILITY_LIMIT'}}
    for path in code_files:
        destination=args.out/'source_snapshot'/path
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,destination)
    config['source_snapshot']='source_snapshot/; working source hashes, not Git HEAD alone, identify executed code'
    config['versions'].update({m:importlib.metadata.version(m) for m in ['matplotlib','pypdf']})
    (args.out/'requirements-executed.txt').write_text('\n'.join(f'{m}=={version}' for m,version in config['versions'].items())+'\n')
    dump(args.out/'config.json',config)
    (args.out/'SPECIFICATION.md').write_text(Path('research/specification.md').read_text())
    (args.out/'DATA_AUDIT_REPORT.md').write_text((args.data/'DATA_AUDIT_REPORT.md').read_text())
    dates=pd.DatetimeIndex(sorted(dataset.date.unique()))
    decision_days=[]
    for start,end in windows.values():
        ds=dates[(dates>=pd.Timestamp(start))&(dates<=pd.Timestamp(end))]
        decision_days.extend(pd.Series(ds).groupby(ds.to_period('M')).first().tolist())
    cache={}
    began=time.time()
    for day in sorted(set(decision_days)):
        for tier in ['CONSERVATIVE','MODERATE','AGGRESSIVE']:
            for momentum in [True,False]:
                cache[(str(day.date()),tier,momentum)]=candidates(dataset,dates,day,tier,momentum)
        print(f'Ranked history through {day.date()} ({time.time()-began:.1f}s)',flush=True)
    dump(args.out/'ranking_cache.json',{f'{d}|{t}|{m}':v for (d,t,m),v in cache.items()})
    summaries=[]; outputs={}; ablations=[]; sensitivity=[]; stresses=[]
    def execute(window,s,policy,momentum=True,fee=.001,slippage=.0005,kind='principal',initial_seed=None):
        start,end=windows[window]
        summary,frames=replay(dataset,s,policy,start,end,cache,fee,slippage,momentum,initial_seed)
        meta={'window':window,'scenario':s.name,'surplus_group':s.surplus_group,'tier':s.tier,'strategy':policy,
              'kind':kind,'momentum':momentum,'fee_rate':fee,'slippage_rate':slippage}
        record={**meta,**summary}
        for key,frame in frames.items():
            for k,v in meta.items():frame[k]=v
            outputs.setdefault(key,[]).append(frame)
        with (args.out/'progress.jsonl').open('a') as log:
            log.write(json.dumps(record,allow_nan=True)+'\n')
        print(f'Completed {window} {s.name} {policy} {kind}',flush=True)
        return record
    for window in windows:
        for s in investors:
            for policy in POLICIES:
                summaries.append(execute(window,s,policy))
    for s in investors:
        ablations.append(execute('primary_2022_2025',s,'Full IntelliVest',momentum=False,kind='momentum_ablation'))
    primary_profiles=[s for s in investors if (s.surplus_group,s.tier) in [('low','CONSERVATIVE'),('medium','MODERATE'),('high','AGGRESSIVE')]]
    for s in primary_profiles:
        for fee,slip in [(0.,0.),(.0025,.001)]:
            for policy in POLICIES:
                sensitivity.append(execute('primary_2022_2025',s,policy,fee=fee,slippage=slip,kind='cost_sensitivity'))
    for s in primary_profiles:
        for policy in POLICIES:
            stresses.append(execute('primary_2022_2025',s,policy,kind='feedback_stress',initial_seed=stress_seed))
    tables={name:pd.concat(frames,ignore_index=True) for name,frames in outputs.items()}
    for name,frame in tables.items():
        frame.to_csv(args.out/f'{name}.csv',index=False)
    summary=pd.DataFrame(summaries)
    summary.to_csv(args.out/'strategy_summaries.csv',index=False)
    pd.DataFrame(ablations).to_csv(args.out/'momentum_ablation.csv',index=False)
    pd.DataFrame(sensitivity).to_csv(args.out/'cost_sensitivity.csv',index=False)
    pd.DataFrame(stresses).to_csv(args.out/'feedback_stress.csv',index=False)
    principal_v=tables['valuations'][tables['valuations'].kind=='principal']
    contrasts=comparisons(summary,principal_v)
    contrasts.to_csv(args.out/'paired_comparisons.csv',index=False)
    principal_d=tables['decisions'][tables['decisions'].kind=='principal']
    full=principal_d[principal_d.strategy=='Full IntelliVest']
    no=principal_d[principal_d.strategy=='No Feedback']
    changed=full[['window','scenario','date','orders']].merge(no[['window','scenario','date','orders']],on=['window','scenario','date'],suffixes=('_full','_no_feedback'))
    changed['different_decision']=changed.orders_full!=changed.orders_no_feedback
    changed.to_csv(args.out/'feedback_decision_comparison.csv',index=False)
    # Identical exogenous contributions and no policy cross-contamination.
    check=principal_v.groupby(['window','scenario','date']).contribution.nunique()
    assert (check==1).all()
    assert (principal_v.cash>=-1e-6).all()
    assert (principal_d[principal_d.strategy!='Risk Only'].overspend<1e-6).all()
    principal_p=tables['policy_changes'][tables['policy_changes'].kind=='principal']
    assert set(principal_p.strategy.unique())<= {'Full IntelliVest'}
    dump(args.out/'execution_validation.json',{'status':'passed','identical_contributions':True,'no_negative_cash':True,
        'affordability_proposal_caps':True,'feedback_mutations_full_only':True,'principal_runs':len(summary),
        'momentum_ablation_runs':len(ablations),'cost_sensitivity_runs':len(sensitivity),
        'feedback_stress_runs':len(stresses),
        'elapsed_seconds':time.time()-began})
    from research.generate_results import generate
    generate(args.out)
    dump(args.out/'output_hashes.json',{str(p.relative_to(args.out)):sha(p) for p in sorted(args.out.rglob('*')) if p.is_file() and p.name!='output_hashes.json'})
    print(args.out,flush=True)


if __name__=='__main__':
    main()
