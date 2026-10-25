"""Independent result-file checks and deterministic representative replay."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from research.data_audit import sha,dump
from research.investor_scenarios import scenarios
from research.historical_replay import replay
from backend.config import settings


def verify(folder,data_folder):
    config=json.loads((folder/'config.json').read_text())
    checks=[]
    for key,value in config['effective_settings'].items():setattr(settings,key,value)
    data=pd.read_csv(data_folder/'research_quotes.csv',parse_dates=['date'])
    assert sha(data_folder/'research_quotes.csv')==config['dataset']['research_dataset_sha256']
    checks.append('frozen dataset SHA256 matches executed config')
    for path,digest in config['code_sha256'].items():
        assert sha(folder/'source_snapshot'/path)==digest,path
    checks.append('all frozen source files match recorded code hashes')
    # Validate every principal account, rather than only aggregate outcomes.
    v=pd.read_csv(folder/'valuations.csv',parse_dates=['date'])
    principal=v[v.kind=='principal']
    summaries=pd.read_csv(folder/'strategy_summaries.csv')
    trades=pd.read_csv(folder/'trades.csv',parse_dates=['date','decision_date'])
    for (window,scenario,policy),g in principal.groupby(['window','scenario','strategy']):
        g=g.sort_values('date')
        s=summaries[(summaries.window==window)&(summaries.scenario==scenario)&(summaries.strategy==policy)].iloc[0]
        initial=100000.
        before=np.r_[initial,g.equity.iloc[:-1]]+g.contribution
        assert np.allclose(g['return'],g.equity/before-1,atol=1e-12)
        assert abs(s.investment_gain-(g.equity.iloc[-1]-initial-g.contribution.sum()))<1e-6
        assert np.isclose(s.cumulative_return,np.prod(1+g['return'])-1,atol=1e-10)
        assert g.cash.min()>=-1e-6
    checks.append('every principal account reconciles returns, contributions, equity and gain')
    buy=trades[trades.side=='BUY']
    assert (buy.date>buy.decision_date).all()
    assert (buy.quantity==buy.quantity.astype(int)).all()
    assert not buy.duplicated(['kind','window','scenario','strategy','fee_rate','slippage_rate','decision_date','ticker']).any()
    checks.append('all buys have delayed execution, integer quantities and no duplicates')
    decisions=pd.read_csv(folder/'decisions.csv')
    assert (decisions.executed_cost<=decisions.budget+1e-6).all()
    checks.append('all fills including fees respect their saved monthly batch budget')
    cache={}
    for key,value in json.loads((folder/'ranking_cache.json').read_text()).items():
        day,tier,momentum=key.split('|');cache[(day,tier,momentum=='True')]=value
    investors={s.name:s for s in scenarios()}
    reference=pd.read_csv(folder/'feedback_stress.csv')
    reruns=[]
    selections=[('principal','medium_moderate',policy) for policy in config['strategies']]
    selections+=[('feedback_stress','low_conservative','Full IntelliVest')]
    for kind,name,policy in selections:
        seed=config['feedback_stress']['initial_holdings'] if kind=='feedback_stress' else None
        summary,frames=replay(data,investors[name],policy,*config['windows']['primary_2022_2025'],cache,
                              config['fee'],config['slippage'],True,seed)
        base=reference if seed else summaries[summaries.window=='primary_2022_2025']
        expected=base[(base.scenario==name)&(base.strategy==policy)].iloc[0]
        for metric,actual in summary.items():
            stored=expected[metric]
            if isinstance(actual,(float,np.floating)) and np.isnan(actual):
                assert pd.isna(stored),(name,policy,metric)
            else:
                assert np.isclose(float(actual),float(stored),rtol=1e-10,atol=1e-8),(name,policy,metric,actual,stored)
        observed=v[(v.kind==kind)&(v.window=='primary_2022_2025')&(v.scenario==name)&(v.strategy==policy)].sort_values('date')
        for col in frames['valuations'].select_dtypes(include='number').columns:
            assert np.allclose(frames['valuations'][col],observed[col],rtol=1e-10,atol=1e-8,equal_nan=True),(name,policy,col)
        reruns.append({'kind':kind,'scenario':name,'strategy':policy,'status':'identical_within_1e-10_relative_tolerance'})
    checks.append('five independent representative replays reproduce every summary and numeric daily ledger column')
    result={'status':'passed','checks':checks,'deterministic_replays':reruns}
    dump(folder/'reproducibility_verification.json',result)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--data',type=Path,required=True)
    args=parser.parse_args();verify(args.run,args.data)
