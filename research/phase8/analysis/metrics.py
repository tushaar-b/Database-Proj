"""Common metrics, authority denominators and paired temporal uncertainty."""
import numpy as np
import pandas as pd
from research.risk_metrics import performance,episode_lengths
from research.diagnostics.metrics import cash_overlay,sharpe_diagnostic,block_interval,exposure_series


def summarize(frames):
    v,d,t,e,p=[frames[k] for k in ['valuations','decisions','trades','episodes','policy_changes']]
    buys=t[t.side=='BUY'] if len(t) else t;sells=t[t.side=='SELL'] if len(t) else t
    valid=v.hhi.notna();lengths=episode_lengths(v.hhi_breach)
    last=v.iloc[-1];hhi_e=e[e.metric=='hhi'] if len(e) else e
    r=performance(v['return']);diag=sharpe_diagnostic(v)
    purchase=d.executed_cost>0
    gross=float(buys.notional.sum()+buys.fee.sum()) if len(buys) else 0.
    return {**r,'sharpe_valid':diag['sharpe_valid'],'sharpe_status':diag['numerical_validity_status'],
        'authorized_budget_utilization':float(last.external_spent/last.external_grants) if last.external_grants else np.nan,
        'external_approved_grants':float(last.external_grants),'external_authority_spent':float(last.external_spent),
        'recycled_approved':float(last.recycled_grants),'recycled_spent':float(last.recycled_spent),
        'expired_authority':float(last.expired_authority),'revoked_authority':float(last.revoked_authority),
        'recurring_offered_budget_fill':float(d.executed_cost.sum()/d.authorized_batch_budget.sum()) if d.authorized_batch_budget.sum() else np.nan,
        'gross_purchase_cost':gross,'unique_brokerage_funding_deployment':float(last.external_spent/(100000+v.contribution.sum())),
        'mean_remaining_authority':float(v.authority_balance.mean()),'ending_authority':float(last.authority_balance),
        'mean_cash_allocation':float(v.cash_fraction.mean()),'mean_invested_allocation':float((1-v.cash_fraction).mean()),
        'purchase_frequency':float(purchase.mean()),'feasible_but_unexecuted':int((d.feasible_single_share_opportunity&~purchase).sum()),
        'decision_count':len(d),'monthly_reference_violation_rate':float((d.monthly_reference_overspend>1e-8).mean()),
        'mean_monthly_reference_overspend':float(d.monthly_reference_overspend.mean()),
        'max_monthly_reference_overspend':float(d.monthly_reference_overspend.max()),
        'household_new_draw_violations':int(d.new_household_authority_violation.sum()),
        'reserve_violations':int(d.reserve_violation.sum()),'authority_violations':int(d.authority_violation.sum()),
        'mean_hhi':float(v.loc[valid,'hhi'].mean()),'max_hhi':float(v.hhi.max()),'hhi_valid_sessions':int(valid.sum()),
        'hhi_undefined_sessions':int((~valid).sum()),'holdings_coverage':float(valid.mean()),
        'hhi_breach_frequency':float(v.loc[valid,'hhi_breach'].mean()) if valid.any() else np.nan,
        'hhi_breach_sessions':int(v.hhi_breach.sum()),'mean_hhi_episode_sessions':float(np.mean(lengths)) if lengths else 0.,
        'max_hhi_episode_sessions':max(lengths,default=0),'hhi_episodes_resolved':int(hhi_e.resolved.sum()) if len(hhi_e) else 0,
        'hhi_episode_resolution_fraction':float(hhi_e.resolved.mean()) if len(hhi_e) else np.nan,
        'detected_breach_episodes':len(e),'policy_updates':len(p),
        'mean_policy_response_sessions':float(p.policy_effective_delay_sessions.mean()) if len(p) else np.nan,
        'changed_recommendations':int(d.direct_recommendation_change.sum()),'actual_trade_changed_decisions':int(d.actual_trade_change.sum()),
        'recommendation_response_sessions':float(e.response_sessions.mean()) if len(e) else np.nan,
        'feedback_incremental_fees':float(d.incremental_feedback_fees.sum()),'feedback_incremental_slippage':float(d.incremental_feedback_slippage.sum()),
        'new_position_trades':int(buys.new_position.sum()) if len(buys) else 0,'topup_trades':int(buys.topup.sum()) if len(buys) else 0,
        'buy_trades':len(buys),'sell_trades':len(sells),'realized_gain':float(last.realized_gain),
        'transaction_fees':float(t.fee.sum()) if len(t) else 0,'slippage_cost':float(t.slippage_cost.sum()) if len(t) else 0,
        'turnover':float(t.loc[t.side.isin(['BUY','SELL']),'notional'].sum()/v.equity.mean()) if len(t) else 0,
        'mean_position_concentration':float(v.max_position_weight.mean()),'ending_equity':float(last.equity),
        'contributions':float(v.contribution.sum()),'investment_gain':float(last.equity-100000-v.contribution.sum()),
        'negative_momentum_selection_rate':float(d.negative_momentum_selected.sum()/d.selected_count.sum()) if d.selected_count.sum() else np.nan}


def contrasts(summaries,valuations):
    rows=[]
    pairs=[('V2','V1'),('V3','V1'),('V4','V1'),('V5','V4')]
    metrics=['authorized_budget_utilization','feasible_but_unexecuted','mean_cash_allocation','mean_hhi','hhi_breach_sessions','cvar95','maximum_drawdown','annualized_return','turnover']
    for (window,scenario),g in summaries[summaries.kind=='principal'].groupby(['window','scenario']):
        s=g.set_index('policy')
        v=valuations[(valuations.kind=='principal')&(valuations.window==window)&(valuations.scenario==scenario)]
        pivot=v.pivot(index='date',columns='policy',values='return')
        for a,b in pairs:
            row={'window':window,'scenario':scenario,'contrast':a+' - '+b}
            row.update({m+'_difference':float(s.loc[a,m]-s.loc[b,m]) for m in metrics})
            row.update(block_interval(pivot[a],pivot[b]));rows.append(row)
    return pd.DataFrame(rows)


def exposure(valuations,trades):
    rows=[]
    for scenario,g in valuations[(valuations.kind=='principal')&(valuations.window=='primary_2022_2025')].groupby('scenario'):
        series={}
        for policy,p in g.groupby('policy'):
            ts=trades[(trades.kind=='principal')&(trades.window=='primary_2022_2025')&(trades.scenario==scenario)&(trades.policy==policy)]
            series[policy]=exposure_series(p,ts)
        for a,b in [('V4','V1'),('V5','V4')]:
            common=series[a].merge(series[b],on='date',suffixes=('_a','_b'))
            mask=(common.opening_exposure_a>0)&(common.opening_exposure_b>0)
            same=mask&(common.exposure_bin_a==common.exposure_bin_b)
            for label,m in [('positive_opening_exposure',mask),('same_date_same_bin',same)]:
                selected=common[m]
                from research.risk_metrics import tail_metrics
                rows.append({'scenario':scenario,'contrast':a+' - '+b,'matching':label,'coverage':float(m.mean()),'matched_sessions':int(m.sum()),
                    'gross_sleeve_cvar_a':tail_metrics(selected.unit_exposure_return_gross_a)['cvar95'],
                    'gross_sleeve_cvar_b':tail_metrics(selected.unit_exposure_return_gross_b)['cvar95'],
                    **block_interval(common.unit_exposure_return_gross_a,common.unit_exposure_return_gross_b,m.to_numpy())})
    return pd.DataFrame(rows)
