"""Investor-first Sharpe, frozen-trade cash interest and holdings-conditional risk."""
import numpy as np
import pandas as pd
from research.risk_metrics import performance,tail_metrics,episode_lengths

SEED=20261024
EXPOSURE_BINS=np.array([0,.05,.25,.50,.75,1.00000001])


def cash_overlay(frame,annual_cash=0.,initial=100000.):
    g=frame.sort_values('date').copy().reset_index(drop=True)
    daily=np.expm1(np.log1p(annual_cash)/252)
    extra=0.;prev_base_cash=initial;prev_equity=initial
    rows=[]
    for row in g.itertuples():
        opening_cash=prev_base_cash+row.contribution+extra
        interest=opening_cash*daily
        extra+=interest
        equity=row.equity+extra
        ret=equity/(prev_equity+row.contribution)-1
        rows.append({'date':row.date,'equity':equity,'cash':row.cash+extra,'stock_value':row.stock_value,
                     'contribution':row.contribution,'return':ret,'cash_interest':interest,'cumulative_cash_interest':extra,
                     'cash_fraction':(row.cash+extra)/equity})
        prev_base_cash=row.cash;prev_equity=equity
    result=pd.DataFrame(rows)
    assert abs(result.equity.iloc[-1]-g.equity.iloc[-1]-result.cash_interest.sum())<1e-6
    if annual_cash==0:
        assert np.allclose(result['return'],g['return'],atol=1e-12)
    return result


def sharpe_diagnostic(frame,benchmark='legacy_linear',annual_rf=.04):
    r=frame['return'].to_numpy(dtype=float)
    assert np.isfinite(r).all()
    daily=annual_rf/252 if benchmark=='legacy_linear' else np.expm1(np.log1p(annual_rf)/252)
    sd=float(np.std(r,ddof=1)) if len(r)>1 else np.nan
    excess=r-daily
    tol=64*np.finfo(float).eps*max(1.,float(np.max(abs(r))))
    constant=len(r)<2 or np.ptp(r)<=tol or sd==0 or not np.isfinite(sd)
    ratio=np.nan if constant else float(np.sqrt(252)*excess.mean()/np.std(excess,ddof=1))
    old=np.sqrt(252)*(r.mean()-annual_rf/252)/sd if np.isfinite(sd) and sd>1e-15 else np.nan
    annual_vol=sd*np.sqrt(252)
    metric=performance(r,annual_rf)
    return {**metric,'original_formula_sharpe':float(old),'sharpe':ratio,'benchmark_convention':benchmark,
        'annual_rf_input':annual_rf,'daily_rf':daily,'annualized_arithmetic_rf':daily*252,
        'effective_compound_annual_rf':np.expm1(np.log1p(daily)*252),
        'mean_daily_return':float(r.mean()),'sample_daily_volatility':sd,
        'annualized_arithmetic_return':float(r.mean()*252),'annualized_arithmetic_excess_return':float(excess.mean()*252),
        'geometric_annualized_excess_return':float(metric['annualized_return']-annual_rf),
        'annualized_volatility':annual_vol,'valid_observations':len(r),
        'numerical_constant_tolerance':tol,'sharpe_valid':not constant,
        'numerical_validity_status':'undefined_numerically_constant' if constant else 'defined_low_volatility' if annual_vol<.01 else 'defined',
        'low_volatility_flag':bool(annual_vol<.01),'average_invested_allocation':float((1-frame.cash_fraction).mean()),
        'mean_cash_allocation':float(frame.cash_fraction.mean()),'cash_only_sessions':int((frame.stock_value==0).sum()),
        'cumulative_cash_interest':float(frame.cash_interest.sum()) if 'cash_interest' in frame else 0.}


def distribution(rows):
    result=[]
    groups=['variant','window','strategy','annual_cash_return','benchmark_convention']
    for key,g in rows.groupby(groups,dropna=False):
        x=g.loc[g.sharpe_valid,'sharpe']
        result.append({**dict(zip(groups,key)),'profiles':len(g),'defined':len(x),'undefined':len(g)-len(x),
            'mean_defined_sharpe':float(x.mean()),'median_defined_sharpe':float(x.median()),
            'minimum_defined_sharpe':float(x.min()),'maximum_defined_sharpe':float(x.max()),
            'q25_sharpe':float(x.quantile(.25)),'q75_sharpe':float(x.quantile(.75)),
            'mean_invested_allocation':float(g.average_invested_allocation.mean()),
            'mean_annualized_return':float(g.annualized_return.mean()),'mean_annualized_volatility':float(g.annualized_volatility.mean()),
            'profile_sharpe_exposure_correlation':float(g[['sharpe','average_invested_allocation']].corr().iloc[0,1])})
    return pd.DataFrame(result)


def hhi_diagnostic(frame):
    valid=frame.hhi.notna()
    breaches=valid&(frame.hhi>.25)
    return {'sessions':len(frame),'hhi_valid_sessions':int(valid.sum()),'hhi_undefined_sessions':int((~valid).sum()),
        'holdings_coverage':float(valid.mean()),'mean_hhi_conditional_on_holdings':float(frame.loc[valid,'hhi'].mean()),
        'original_all_session_breach_frequency':float(breaches.mean()),
        'corrected_valid_hhi_breach_frequency':float(breaches[valid].mean()) if valid.any() else np.nan,
        'hhi_breach_sessions':int(breaches.sum()),'longest_observed_breach_sessions':max(episode_lengths(breaches),default=0)}


def block_interval(a,b,mask=None,block=20,draws=2000):
    a,b=np.asarray(a,dtype=float),np.asarray(b,dtype=float)
    assert len(a)==len(b)
    valid=np.isfinite(a)&np.isfinite(b)
    if mask is not None:valid &= mask
    difference=np.where(valid,a-b,np.nan)
    n=int(valid.sum())
    record={'valid_paired_sessions':n,'mean_annualized_arithmetic_return_difference':float(np.nanmean(difference)) *252 if n else np.nan,
            'ci95_low':np.nan,'ci95_high':np.nan,'block_sessions':block,'draws':draws,'seed':SEED,
            'interval_status':'insufficient_fewer_than_60_pairs'}
    if n<60:return record
    rng=np.random.default_rng(SEED)
    starts=rng.integers(0,len(a),size=(draws,int(np.ceil(len(a)/block))))
    indices=((starts[:,:,None]+np.arange(block))%len(a)).reshape(draws,-1)[:,:len(a)]
    sampled=difference[indices]
    counts=np.isfinite(sampled).sum(axis=1)
    means=np.nansum(sampled,axis=1)/np.where(counts,counts,np.nan)*252
    lo,hi=np.nanquantile(means,[.025,.975])
    record.update(ci95_low=float(lo),ci95_high=float(hi),interval_status='conditional_descriptive_block_interval')
    return record


def exposure_series(frame,trades):
    g=frame.sort_values('date').reset_index(drop=True).copy()
    prev_equity=np.r_[100000.,g.equity.iloc[:-1]]
    opening_stock=np.r_[0.,g.stock_value.iloc[:-1]]
    before=prev_equity+g.contribution.to_numpy()
    exposure=opening_stock/before
    pnl=g.equity.to_numpy()-before
    if len(trades):
        costs=trades.groupby('date')[['fee','slippage_cost']].sum().sum(axis=1).reindex(g.date,fill_value=0).to_numpy()
    else:costs=np.zeros(len(g))
    g['opening_exposure']=exposure
    g['unit_exposure_return_net']=np.divide(pnl,opening_stock,out=np.full(len(g),np.nan),where=opening_stock>1e-12)
    g['unit_exposure_return_gross']=np.divide(pnl+costs,opening_stock,out=np.full(len(g),np.nan),where=opening_stock>1e-12)
    g['exposure_bin']=pd.cut(exposure,EXPOSURE_BINS,include_lowest=True,right=False).astype(str)
    g['transaction_cost']=costs
    return g


def contiguous_max_drawdown(dates,returns,all_dates):
    """Do not chain returns across discarded unmatched dates."""
    location=pd.Index(all_dates).get_indexer(dates)
    r=np.asarray(returns)
    if not len(r) or (r<=-1).any():return np.nan
    groups=np.cumsum(np.r_[True,np.diff(location)>1])
    result=0.
    for key in np.unique(groups):
        sample=r[groups==key]
        wealth=np.cumprod(1+sample)
        peak=np.maximum.accumulate(np.r_[1.,wealth])[1:]
        result=max(result,float(np.max(1-wealth/peak)))
    return result


def exposure_comparisons(ledgers,trades):
    series={};strata=[];comparisons=[];uncertainty=[]
    for (variant,window,scenario,strategy),g in ledgers.groupby(['variant','window','scenario','strategy']):
        if variant!='original' or window!='primary_2022_2025':continue
        t=trades[(trades.variant==variant)&(trades.window==window)&(trades.scenario==scenario)&(trades.strategy==strategy)]
        z=exposure_series(g,t)
        series[(scenario,strategy)]=z
        for bin_name,b in z.groupby('exposure_bin'):
            positive=b[b.unit_exposure_return_net.notna()]
            strata.append({'scenario':scenario,'strategy':strategy,'opening_exposure_bin':bin_name,'sessions':len(b),
                'positive_exposure_sessions':len(positive),'mean_opening_exposure':float(b.opening_exposure.mean()),
                'conditional_mean_hhi':float(b.hhi.mean()),'mean_account_daily_return':float(b['return'].mean()),
                'account_cvar95':tail_metrics(b['return'])['cvar95'],
                'unit_net_cvar95':tail_metrics(positive.unit_exposure_return_net)['cvar95'],
                'unit_gross_cvar95':tail_metrics(positive.unit_exposure_return_gross)['cvar95']})
    for scenario in sorted(set(s for s,_ in series)):
        full=series[(scenario,'Full IntelliVest')]
        for baseline in ['Affordability Only','Risk Only','No Feedback']:
            base=series[(scenario,baseline)]
            both=full.merge(base,on='date',suffixes=('_full','_base'))
            common=(both.opening_exposure_full>1e-12)&(both.opening_exposure_base>1e-12)
            same_bin=common&(both.exposure_bin_full==both.exposure_bin_base)
            for name,mask in [('common_positive_opening_exposure',common),('same_date_same_exposure_bin',same_bin)]:
                row={'scenario':scenario,'contrast':'Full IntelliVest - '+baseline,'matching':name,'paired_sessions':int(mask.sum()),
                     'all_sessions':len(both),'coverage':float(mask.mean())}
                for suffix in ['full','base']:
                    observed=both.loc[mask]
                    gross=observed['unit_exposure_return_gross_'+suffix]
                    net=observed['unit_exposure_return_net_'+suffix]
                    row.update({f'{suffix}_mean_opening_exposure':float(observed['opening_exposure_'+suffix].mean()),
                        f'{suffix}_mean_hhi':float(observed['hhi_'+suffix].mean()),
                        f'{suffix}_unit_net_cvar95':tail_metrics(net)['cvar95'],
                        f'{suffix}_unit_gross_cvar95':tail_metrics(gross)['cvar95'],
                        f'{suffix}_unit_net_max_drawdown_contiguous':contiguous_max_drawdown(observed.date,net,both.date),
                        f'{suffix}_unit_gross_max_drawdown_contiguous':contiguous_max_drawdown(observed.date,gross,both.date),
                        f'{suffix}_mean_account_daily_return':float(observed['return_'+suffix].mean()),
                        f'{suffix}_unit_gross_annualized_arithmetic_return':float(gross.mean()*252)})
                comparisons.append(row)
                uncertainty.append({'scenario':scenario,'contrast':row['contrast'],'experiment':'exposure_'+name,
                    **block_interval(both.unit_exposure_return_gross_full,both.unit_exposure_return_gross_base,mask.to_numpy())})
    return pd.DataFrame(strata),pd.DataFrame(comparisons),pd.DataFrame(uncertainty),series
