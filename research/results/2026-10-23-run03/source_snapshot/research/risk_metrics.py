import numpy as np


def tail_metrics(returns):
    r = np.asarray(returns, dtype=float)
    if len(r) < 2:
        return {'var95': np.nan, 'cvar95': np.nan}
    assert np.isfinite(r).all()
    q = np.quantile(r, .05, method='linear')
    var = max(0., -float(q))
    return {'var95': var, 'cvar95': max(var, -float(r[r <= q].mean()))}


def performance(returns, rf=.04):
    r = np.asarray(returns, dtype=float)
    assert len(r) and np.isfinite(r).all() and (r > -1).all()
    wealth = np.cumprod(1+r)
    peak = np.maximum.accumulate(np.r_[1., wealth])[1:]
    sd = np.std(r, ddof=1) if len(r)>1 else 0
    return {'cumulative_return': float(wealth[-1]-1), 'annualized_return': float(wealth[-1]**(252/len(r))-1),
            'annualized_volatility': float(sd*np.sqrt(252)),
            'sharpe': float((r.mean()-rf/252)/sd*np.sqrt(252)) if sd>1e-15 else np.nan,
            'maximum_drawdown': float(-np.min(wealth/peak-1)), **tail_metrics(r)}


def episode_lengths(flags):
    lengths, current = [], 0
    for flag in flags:
        if flag:
            current += 1
        elif current:
            lengths.append(current)
            current = 0
    if current:
        lengths.append(current)
    return lengths
