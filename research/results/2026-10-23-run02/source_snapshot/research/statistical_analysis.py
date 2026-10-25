"""Paired conditional uncertainty; never treats investor scenarios as random people."""
import numpy as np
import pandas as pd


def paired_block_interval(a,b,seed=20261023,block=20,draws=2000):
    a,b=np.asarray(a),np.asarray(b)
    assert len(a)==len(b) and len(a)>=block
    difference=a-b
    rng=np.random.default_rng(seed)
    n=len(a)
    # Same resampled dates for both policies. Circular blocks preserve local dependence.
    starts=rng.integers(0,n,size=(draws,int(np.ceil(n/block))))
    indices=((starts[:,:,None]+np.arange(block))%n).reshape(draws,-1)[:,:n]
    means=difference[indices].mean(axis=1)*252
    lo,hi=np.quantile(means,[.025,.975])
    return {'annualized_arithmetic_mean_return_difference':float(difference.mean()*252),
            'conditional_ci95_low':float(lo),'conditional_ci95_high':float(hi),
            'block_sessions':block,'bootstrap_draws':draws,'seed':seed,'sessions':n}


def comparisons(summaries,valuations):
    rows=[]
    metrics=['affordability_violation_rate','mean_overspend','mean_hhi','hhi_breach_sessions','risk_breach_sessions',
             'cvar95','maximum_drawdown','annualized_return','sharpe','turnover','average_cash_allocation',
             'surplus_utilization','policy_adjustments','direct_feedback_changed_decisions']
    for (window,scenario),g in summaries.groupby(['window','scenario']):
        full=g[g.strategy=='Full IntelliVest'].iloc[0]
        for baseline in ['Risk Only','Affordability Only','No Feedback']:
            base=g[g.strategy==baseline].iloc[0]
            row={'window':window,'scenario':scenario,'contrast':'Full IntelliVest - '+baseline}
            row.update({m+'_difference':float(full[m]-base[m]) for m in metrics})
            v=valuations[(valuations.window==window)&(valuations.scenario==scenario)]
            pivot=v.pivot(index='date',columns='strategy',values='return')
            row.update(paired_block_interval(pivot['Full IntelliVest'],pivot[baseline]))
            rows.append(row)
    return pd.DataFrame(rows)
