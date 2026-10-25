"""Diagnostic reports and six figures, built exclusively from executed outputs."""
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd


def table(frame):
    def cell(value):
        if isinstance(value,(float,np.floating)):return 'NA' if not np.isfinite(value) else f'{value:.5f}'
        return str(value)
    return '| '+' | '.join(frame.columns)+' |\n| '+' | '.join(['---']*len(frame.columns))+' |\n'+'\n'.join('| '+' | '.join(cell(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None))


def generate(out):
    os.environ.setdefault('MPLCONFIGDIR','/private/tmp/intellivest-diagnostic-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from research.strategies import POLICIES
    config=json.loads((out/'DIAGNOSTIC_CONFIG.json').read_text())
    sharpe=pd.read_csv(out/'SHARPE_DIAGNOSTICS.csv')
    distribution=pd.read_csv(out/'SHARPE_DISTRIBUTION.csv')
    cash=pd.read_csv(out/'CASH_UTILIZATION.csv',parse_dates=['date'])
    cash_profiles=pd.read_csv(out/'CASH_PROFILE_SUMMARY.csv')
    summaries=pd.read_csv(out/'CONTROLLED_REPLAY_SUMMARIES.csv')
    events=pd.read_csv(out/'FEEDBACK_TRACE.csv',parse_dates=['date'])
    decisions=pd.read_csv(out/'REPLAY_DIAGNOSTICS.csv',parse_dates=['date'])
    paths=pd.read_csv(out/'CASH_RETURN_PATHS.csv',parse_dates=['date'])
    hhi=pd.read_csv(out/'HHI_DIAGNOSTICS.csv')
    trades=pd.read_csv(out/'REPLAY_TRADES.csv',parse_dates=['date'])
    ledgers=pd.read_csv(out/'REPLAY_VALUATIONS.csv',parse_dates=['date'])
    matched=pd.read_csv(out/'EXPOSURE_MATCHED_COMPARISONS.csv')
    uncertainty=pd.read_csv(out/'UNCERTAINTY.csv')
    classifications=pd.read_csv(out/'FEEDBACK_EVENT_CLASSIFICATION.csv')
    original=summaries[summaries.variant=='original']
    full=original[original.strategy=='Full IntelliVest']
    e=events[events.variant=='original']
    full_decisions=decisions[(decisions.variant=='original')&(decisions.strategy=='Full IntelliVest')]
    profiles=list(config.get('scenario_order',full.scenario))
    colors=dict(zip(POLICIES,['#C88B24','#7758A4','#387AA9','#25846B']))
    figdir=out/'figures';figdir.mkdir(exist_ok=True)
    plt.rcParams.update({'font.size':9,'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False,
                         'axes.grid':True,'grid.alpha':.18,'figure.dpi':150,'savefig.dpi':300})
    captions=[]
    def save(fig,name,caption):
        fig.tight_layout();fig.savefig(figdir/(name+'.png'),bbox_inches='tight');fig.savefig(figdir/(name+'.svg'),bbox_inches='tight')
        plt.close(fig);captions.append(f'**{name}** — {caption}')
    # Actual transactions are compared separately from proposed quantities.
    transaction_diffs=[]
    for (variant,scenario),g in trades.groupby(['variant','scenario']):
        full_t=g[g.strategy=='Full IntelliVest'];no_t=g[g.strategy=='No Feedback']
        keys=['date','ticker','side']
        a=full_t.groupby(keys)[['quantity','notional','fee']].sum().reset_index()
        b=no_t.groupby(keys)[['quantity','notional','fee']].sum().reset_index()
        merged=a.merge(b,on=keys,how='outer',suffixes=('_full','_no')).fillna(0)
        merged['transaction_different']=(merged.quantity_full!=merged.quantity_no)|(~np.isclose(merged.notional_full,merged.notional_no,rtol=1e-10,atol=1e-8))
        merged['variant']=variant;merged['scenario']=scenario;transaction_diffs.append(merged)
    transaction=pd.concat(transaction_diffs,ignore_index=True)
    transaction.to_csv(out/'TRANSACTION_DIFFERENCES.csv',index=False)
    impact=[]
    path_comparison=pd.read_csv(out/'FEEDBACK_PATH_COMPARISON.csv')
    for variant in ['original','stress_original','accumulated_approved_cash_v1']:
        ev=events[events.variant==variant]
        ds=decisions[(decisions.variant==variant)&(decisions.strategy=='Full IntelliVest')]
        impact.append({'variant':variant,'policy_updates':len(ev),'events_with_monthly_opportunity':int(ev.opportunity_before_policy_replaced.sum()),
            'events_changing_a_recommendation':int(ev.actual_recommendation_changed.sum()),
            'monthly_decisions':len(ds),'eligibility_changed_decisions':int(ds.candidate_eligibility_changed.sum()),
            'internally_selected_basket_changed_decisions':int(ds.selected_basket_changed.sum()),
            'same_state_final_changed_decisions':int(ds.final_recommendation_changed.sum()),
            'path_final_changed_decisions':int(path_comparison.loc[path_comparison.variant==variant,'different_final_recommendation'].sum()),
            'different_transaction_records':int(transaction.loc[transaction.variant==variant,'transaction_different'].sum()),
            'mean_event_response_sessions_observed':float(ev.event_response_sessions.mean())})
    impact=pd.DataFrame(impact);impact.to_csv(out/'FEEDBACK_IMPACT_SUMMARY.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(11,4))
    x=np.arange(3);w=.22
    names=['Original','Concentrated start','Accumulated authority']
    for i,(col,label) in enumerate([('policy_updates','Effective policy updates'),('events_with_monthly_opportunity','Updates with opportunity'),('events_changing_a_recommendation','Updates affecting a proposal')]):
        axes[0].bar(x+(i-1)*w,impact[col],width=w,label=label)
    for i,(col,label) in enumerate([('eligibility_changed_decisions','Candidate eligibility changed'),('same_state_final_changed_decisions','Final proposal changed'),('different_transaction_records','Different executed trade record')]):
        axes[1].bar(x+(i-1)*w,impact[col],width=w,label=label)
    for ax in axes:
        ax.set_xticks(x,names,rotation=15,ha='right');ax.legend(fontsize=7);ax.set_ylabel('Count')
    axes[0].set_title('Event-level opportunities');axes[1].set_title('Decision and transaction effects')
    fig.suptitle('Figure 1. Feedback updates are distinct from decision impact',y=1.02)
    save(fig,'figure_1_feedback_impact','Counts distinguish events, monthly opportunities and executed trade records. Original and accumulated comparisons use nine profiles; concentrated-start uses three. No forced selling was introduced.')
    fig,axes=plt.subplots(1,3,figsize=(12,4.4),sharey=True)
    selections=[(0.,'legacy_linear','Zero cash interest; legacy benchmark'),(.04,'legacy_linear','4% cash; legacy benchmark'),(.04,'effective_geometric','4% cash; matched effective benchmark')]
    for ax,(rate,bench,title) in zip(axes,selections):
        sample=sharpe[(sharpe.variant=='original')&(sharpe.window=='primary_2022_2025')&(sharpe.annual_cash_return==rate)&(sharpe.benchmark_convention==bench)]
        for j,policy in enumerate(POLICIES):
            values=sample[sample.strategy==policy].sharpe.dropna().to_numpy()
            ax.scatter(j+np.linspace(-.12,.12,len(values)),values,color=colors[policy],s=24)
            if len(values):
                ax.scatter(j,np.median(values),marker='_',s=240,color='#222',zorder=4)
                ax.scatter(j,np.mean(values),marker='D',s=25,color='#A44',zorder=4)
        ax.set_xticks(range(4),['Afford.','Risk Only','No Feedback','Full'],rotation=25,ha='right')
        ax.set_title(title,fontsize=9);ax.axhline(0,color='#777',lw=.7);ax.set_yscale('symlog',linthresh=1)
    axes[0].set_ylabel('Investor Sharpe (symmetric log display)')
    fig.suptitle('Figure 2. Sharpe distribution: every defined profile retained',y=1.02)
    save(fig,'figure_2_sharpe_distribution','Dots show investor ratios; black ticks mark medians and red diamonds means. Symmetric-log axes retain large negative values. Undefined ratios are excluded and counted in SHARPE_DISTRIBUTION.csv. Cash trades are frozen across interest models.')
    fig,axes=plt.subplots(3,1,figsize=(12,10))
    cp=cash_profiles[(cash_profiles.variant=='original')&(cash_profiles.strategy=='Full IntelliVest')].set_index('scenario').reindex(profiles)
    parts=[('mean_deferred_accumulated_cash','Deferred accumulated cash'),('mean_tier_withheld','Tier withholding'),
           ('mean_risk_withheld','Risk multiplier withholding'),('mean_no_candidate_budget','No eligible candidates'),
           ('mean_unaffordable_selected_slots','Unaffordable selected slots'),('mean_whole_share_residual_positive_slots','Whole-share residual'),
           ('mean_proposed_notional','Proposed purchase')]
    bottom=np.zeros(len(cp));x=np.arange(len(cp))
    for col,label in parts:
        amount=cp[col].to_numpy()/cp.mean_brokerage_cash_before.to_numpy()*100
        axes[0].bar(x,amount,bottom=bottom,label=label);bottom+=amount
    axes[0].set(ylabel='Mean signal-date brokerage cash (%)',ylim=(0,105),title='Original Full: disjoint authorization stages; reserve share is 0%')
    axes[0].legend(ncol=3,fontsize=7)
    for i,variant in enumerate(['original','accumulated_approved_cash_v1']):
        g=cash_profiles[(cash_profiles.variant==variant)&(cash_profiles.strategy=='Full IntelliVest')].set_index('scenario').reindex(profiles)
        label='Original monthly authority' if variant=='original' else 'Accumulated approved cash'
        axes[1].bar(x+(i-.5)*.35,g.decision_budget_fill_ratio*100,width=.35,label=label)
        axes[2].bar(x+(i-.5)*.35,g.unique_brokerage_funding_deployed_ratio*100,width=.35,label=label)
    axes[1].set(ylabel='Executed cost / authorized decision budget (%)',title='Budget fill is distinct from unique funding deployed')
    axes[1].legend(fontsize=8)
    axes[2].set(ylabel='Executed cost / unique brokerage funding (%)',title='Unique funding counts initial savings and contributions once')
    axes[2].legend(fontsize=8)
    labels=[p.replace('conservative','C').replace('moderate','M').replace('aggressive','A').replace('_',' / ') for p in profiles]
    for ax in axes:ax.set_xticks(x,labels,rotation=25,ha='right')
    save(fig,'figure_3_cash_utilization','Waterfall amounts are averaged decision-state cash, not summed unique money. Tiny cent-rounding stages remain in CSV. Monthly reserve is withheld outside brokerage once. Budget fill can fall under accumulated authority because the same unused balance is authorized repeatedly; unique-funding deployment counts each contribution only once. C/M/A denote conservative/moderate/aggressive. Alternative authorization preserves reserve-protected contributions.')
    fig,axes=plt.subplots(1,3,figsize=(12,3.8))
    selected_profiles=['low_conservative','medium_moderate','high_aggressive']
    for ax,profile in zip(axes,selected_profiles):
        for policy in ['Full IntelliVest','Risk Only']:
            for rate in [0.,.04]:
                g=paths[(paths.variant=='original')&(paths.scenario==profile)&(paths.strategy==policy)&(paths.annual_cash_return==rate)].sort_values('date')
                ax.plot(g.date,(1+g['return']).cumprod(),color=colors[policy],ls='-' if rate==0 else '--',label=f'{policy}; cash {rate:.0%}',lw=1.2)
        ax.set(title=profile.replace('_',' ').title(),ylabel='Time-weighted wealth index',xlabel='Date');ax.tick_params(axis='x',rotation=30)
    axes[-1].legend(fontsize=7)
    fig.suptitle('Figure 4. Cash return sensitivity with identical stock transactions',y=1.02)
    save(fig,'figure_4_cash_return_paths','4% effective annual modeled cash return accrues on opening brokerage cash over 252 sessions; earnings remain unspent. It is an assumption, not a guaranteed investment product. External contributions are removed from returns.')
    fig,axes=plt.subplots(1,2,figsize=(10,4.2))
    sample=sharpe[(sharpe.variant=='original')&(sharpe.window=='primary_2022_2025')&(sharpe.annual_cash_return==0)&(sharpe.benchmark_convention=='legacy_linear')]
    for policy in POLICIES:
        g=sample[sample.strategy==policy]
        axes[0].scatter(g.average_invested_allocation*100,g.annualized_return*100,color=colors[policy],label=policy)
        axes[1].scatter(g.average_invested_allocation*100,g.cvar95*100,color=colors[policy],label=policy)
    axes[0].set(ylabel='Annualized account return (%)',xlabel='Mean invested allocation (%)')
    axes[1].set(ylabel='Account daily CVaR95 (%)',xlabel='Mean invested allocation (%)');axes[1].legend(fontsize=8)
    fig.suptitle('Figure 5. Account risk and return depend on invested exposure',y=1.02)
    save(fig,'figure_5_exposure_risk_return','Points are nine deterministic profiles per policy on common dates. Exposure-conditioned gross/net sleeve comparisons and matching coverage are exported separately; normalized sleeve diagnostics are not executable strategies or causal estimates.')
    hh=hhi[(hhi.variant=='original')&(hhi.window=='primary_2022_2025')]
    fig,axes=plt.subplots(2,1,figsize=(12,6.7),gridspec_kw={'height_ratios':[2,1]})
    x=np.arange(len(profiles));w=.19
    for i,policy in enumerate(POLICIES):
        g=hh[hh.strategy==policy].set_index('scenario').reindex(profiles)
        axes[0].bar(x+(i-1.5)*w,g.mean_hhi_conditional_on_holdings,width=w,label=policy,color=colors[policy])
    axes[0].axhline(.25,color='#555',ls='--',lw=.8);axes[0].set(ylabel='Mean HHI conditional on holdings',ylim=(0,1.05));axes[0].legend(fontsize=8,ncol=4)
    coverage=hh.pivot(index='strategy',columns='scenario',values='holdings_coverage').reindex(index=POLICIES,columns=profiles)
    axes[1].imshow(coverage,aspect='auto',vmin=0,vmax=1,cmap='Blues')
    for i,policy in enumerate(POLICIES):
        for j,profile in enumerate(profiles):axes[1].text(j,i,f'{coverage.loc[policy,profile]*100:.1f}%',ha='center',va='center',color='white' if coverage.loc[policy,profile]>.6 else '#222',fontsize=8)
    axes[1].set_yticks(range(4),POLICIES);axes[1].grid(False)
    axes[1].set_title('Sessions with defined equity-sector HHI (holdings coverage)',fontsize=9)
    for ax in axes:ax.set_xticks(x,labels,rotation=25,ha='right')
    fig.suptitle('Figure 6. Sector concentration excludes cash and undefined sessions',y=1.02)
    save(fig,'figure_6_hhi_conditional','Cash is never an equity sector. Empty portfolios have NA HHI; breach frequency uses valid HHI sessions. The lower panel reports measurement coverage rather than assigning empty portfolios zero concentration.')
    (figdir/'CAPTIONS.md').write_text('\n\n'.join(captions)+'\n')
    # Tables and narrative do not overwrite any previous conference material.
    primary_dist=distribution[(distribution.variant=='original')&(distribution.window=='primary_2022_2025')&(distribution.annual_cash_return==0)&(distribution.benchmark_convention=='legacy_linear')]
    shard=primary_dist[['strategy','defined','undefined','mean_defined_sharpe','median_defined_sharpe','minimum_defined_sharpe','maximum_defined_sharpe']]
    investor_sharpe=sharpe[(sharpe.variant=='original')&(sharpe.window=='primary_2022_2025')&(sharpe.strategy=='Full IntelliVest')&(sharpe.annual_cash_return==0)&(sharpe.benchmark_convention=='legacy_linear')]
    investor_sharpe=investor_sharpe[['scenario','annualized_return','annualized_volatility','annualized_arithmetic_excess_return','sharpe','valid_observations','average_invested_allocation','numerical_validity_status']]
    composite=pd.read_csv(out/'SYNTHETIC_RETURN_COMPOSITES.csv')
    composite_full=float(composite[(composite.variant=='original')&(composite.window=='primary_2022_2025')&(composite.strategy=='Full IntelliVest')&(composite.annual_cash_return==0)&(composite.benchmark_convention=='legacy_linear')].sharpe.iloc[0])
    old_hhi=hh.groupby('strategy')[['original_all_session_breach_frequency','corrected_valid_hhi_breach_frequency','holdings_coverage','mean_hhi_conditional_on_holdings']].mean().reset_index()
    pooled=[]
    for policy,g in hh.groupby('strategy'):
        pooled.append({'strategy':policy,'undefined_hhi_sessions':int(g.hhi_undefined_sessions.sum()),
            'valid_hhi_sessions':int(g.hhi_valid_sessions.sum()),'breach_sessions':int(g.hhi_breach_sessions.sum()),
            'mean_profile_valid_hhi_breach_frequency':float(g.corrected_valid_hhi_breach_frequency.mean()),
            'pooled_valid_hhi_breach_frequency':float(g.hhi_breach_sessions.sum()/g.hhi_valid_sessions.sum()),
            'mean_hhi_conditional_on_holdings':float(g.mean_hhi_conditional_on_holdings.mean())})
    pooled=pd.DataFrame(pooled);pooled.to_csv(out/'HHI_AGGREGATION.csv',index=False)
    def sensitivity_row(variant,rate,bench):
        g=sharpe[(sharpe.variant==variant)&(sharpe.window=='primary_2022_2025')&(sharpe.strategy=='Full IntelliVest')&(sharpe.annual_cash_return==rate)&(sharpe.benchmark_convention==bench)]
        return {'authorization':variant,'cash_return':rate,'benchmark':bench,'mean_annualized_return':g.annualized_return.mean(),
            'mean_annualized_volatility':g.annualized_volatility.mean(),'mean_defined_sharpe':g.sharpe.mean(),
            'median_defined_sharpe':g.sharpe.median(),'mean_cash_allocation':g.mean_cash_allocation.mean()}
    full_table=pd.DataFrame([sensitivity_row('original',0.,'legacy_linear'),sensitivity_row('original',.04,'legacy_linear'),
        sensitivity_row('original',.04,'effective_geometric'),sensitivity_row('accumulated_approved_cash_v1',0.,'legacy_linear'),
        sensitivity_row('accumulated_approved_cash_v1',.04,'effective_geometric')])
    full_table.to_csv(out/'FULL_SENSITIVITY_AGGREGATES.csv',index=False)
    cf=cash_profiles[(cash_profiles.variant=='original')&(cash_profiles.strategy=='Full IntelliVest')]
    compact=cf[['scenario','total_unique_brokerage_funding','cash_deployed_including_fees','unique_brokerage_funding_deployed_ratio','decision_budget_fill_ratio','mean_deferred_accumulated_cash','mean_unused_authorized_cash','zero_orders_despite_a_feasible_single_share']]
    reasons=cash[(cash.variant=='original')&(cash.strategy=='Full IntelliVest')].groupby('primary_unused_reason').size().rename('decisions').reset_index()
    reasons.to_csv(out/'CASH_REASON_FREQUENCIES.csv',index=False)
    findings={'original_feedback_updates':len(e),'original_updates_with_monthly_opportunity':int(e.opportunity_before_policy_replaced.sum()),
        'original_events_changing_recommendations':int(e.actual_recommendation_changed.sum()),
        'original_monthly_candidate_eligibility_changes':int(full_decisions.candidate_eligibility_changed.sum()),
        'original_monthly_final_recommendation_changes':int(full_decisions.final_recommendation_changed.sum()),
        'original_full_mean_sharpe':float(primary_dist[primary_dist.strategy=='Full IntelliVest'].mean_defined_sharpe.iloc[0]),
        'original_full_median_sharpe':float(primary_dist[primary_dist.strategy=='Full IntelliVest'].median_defined_sharpe.iloc[0]),
        'original_full_mean_cash':float(full.average_cash_allocation.mean()),'reserve_share_of_brokerage_cash':0.,
        'original_full_mean_budget_fill':float(cf.decision_budget_fill_ratio.mean()),
        'original_full_mean_unique_funding_deployed':float(cf.unique_brokerage_funding_deployed_ratio.mean()),
        'zero_orders_despite_feasible_one_share':int(cf.zero_orders_despite_a_feasible_single_share.sum()),
        'full_undefined_hhi_sessions':int(hh[hh.strategy=='Full IntelliVest'].hhi_undefined_sessions.sum()),
        'replay_count':len(summaries),'frozen_trade_accounting_models':int(len(sharpe)/2),
        'hypothesis_optimization':False}
    (out/'KEY_FINDINGS.json').write_text(json.dumps(findings,indent=2)+'\n')
    original_class=classifications[classifications.variant=='original']
    prior_event_count=int((e.previous_policy_counterfactual_changed_opportunities.fillna(0)>0).sum()) if 'previous_policy_counterfactual_changed_opportunities' in e else 0
    cash_decisions=cash[(cash.variant=='original')&(cash.strategy=='Full IntelliVest')]
    stage_percentages={name:float((cash_decisions[name]/cash_decisions.brokerage_cash_before).mean()) for name in ['deferred_accumulated_cash','tier_withheld','unused_authorized_budget','proposed_notional']}
    root=f'''# Root-cause analysis: validated diagnostics

This report supplements the immutable INITIAL_ROOT_CAUSE_REPORT.md, which was produced before implementation changes. Run03 and its conference draft remain byte-for-byte preserved. Diagnostics made no database connection and changed no production behavior.

## 1. Why 55 updates did not change principal recommendations

The 55 original effective state updates were all sector-block transitions. No principal event reduced the multiplier or was triggered by VaR/volatility. The multiplier and blocks did reach the research proposal function. An offline parity check of the actual application's feedback builder matched all eight breach combinations. All 42 original/stress replays reproduced every original summary metric, numeric daily ledger column and final monthly order basket.

Of the original {len(e)} updates, {int(e.opportunity_before_policy_replaced.sum())} persisted until an eligible monthly opportunity. {int(e.actual_recommendation_changed.sum())} event states changed a positive-share order relative to the **initial fixed No Feedback policy on the same state**, at any opportunity before replacement. Looking across all 432 principal monthly Full decisions, candidate eligibility differed from that same-state fixed-policy counterfactual on {int(full_decisions.candidate_eligibility_changed.sum())} decisions, but final positive-share orders differed on {int(full_decisions.final_recommendation_changed.sum())}. This is an internal restriction effect without final recommendation impact.

A second, distinct probe retains each event's immediately previous policy indefinitely, evaluated against the actual later portfolio state. {prior_event_count} original **policy-release** events eventually differ from that prior-state counterfactual. These releases restore the same unrestricted choices No Feedback already allowed; they do not contradict zero Full-versus-No Feedback differences. Both contrasts are explicitly labelled in the trace. Their long retrospective prior-state latency is not reported as an observed breach correction or asynchronous delivery response.

Each event has exactly one primary classification; buy-only limitations are separate context, not an additional counted cause:

{table(original_class[['reason_for_no_change','events']])}

The sector-exposure selector already prefers lower-exposure sectors, held securities are excluded, and at most three distinct sectors are selected. A dominant-sector block commonly removes stocks which would not have won selection. Changes can also occur and disappear between monthly decisions. In the original principal accounts the internally selected baskets also stayed identical: there was no need to invoke a hypothetical downstream rounding explanation for those particular updates. FEEDBACK_TRACE.csv includes prior/current policy, the initial-fixed comparison basis, flags, thresholds, available cash, full candidate lists/ranks and quantities for an actual representative opportunity; no-opportunity events explicitly leave rankings unobserved. FEEDBACK_EVENT_OPPORTUNITIES.csv evaluates every intervening opportunity, not only the first. REPLAY_DIAGNOSTICS.csv records the fixed-policy counterfactual for every decision. Whole-share effects explain deployment failure and some targeted stress events, separately from the principal sector-block redundancy.

Feedback can restrict sectors and reduce future budgets; it does not independently change the historical score formula or execute corrective sales. Live outbox signatures include alert identity, while replay counts effective state changes only. The application aggregates multiple portfolios, evaluates on requests and durably delivers cross-database events; replay models one account, daily risk checks and immediate deterministic state application. No actual asynchronous delivery latency was measured. Live recommendation acceptance records intent; simulated execution is an explicit common assumption. The separate rebalance endpoint is not automatically invoked by feedback.

## 2. Why Sharpe was extreme

Historical Sharpe used sqrt(252) × [mean(time-weighted daily return) − .04/252] / sample sd(daily return), ddof=1. The denominator is not padded by an epsilon. An sd<=1e-15 guard reports NA. The published cross-profile number was the arithmetic mean of defined investor ratios. CAGR is geometric and was separately reported; it was not incorrectly inserted into Sharpe. Independent Decimal calculations confirmed the arithmetic formula.

Investor-level Full results first (rates are fractions, 4% annual linear benchmark):

{table(investor_sharpe)}

Distribution summaries across investors:

{table(shard)}

Full mean −21.80107 is preserved; the median is {findings['original_full_median_sharpe']:.5f}. Near-cash profiles earn almost zero but are measured against a positive benchmark, producing very negative finite ratios when volatility is small. They are economically sensitive to the cash/benchmark convention rather than evidence of denominator clipping. Every ratio remains available. New reporting flags annualized volatility below 1% descriptively without changing the denominator or deleting the ratio; numerically constant series are explicitly undefined using a machine-precision range check. SHARPE_DIAGNOSTICS.csv contains arithmetic and geometric returns, daily/annual benchmark conventions, excess returns, sample sd, observation counts, exposure and validity. Synthetic-return-composite Sharpe is separately labelled and is not the mean investor ratio.

The legacy daily benchmark .04/252 compounds to slightly more than 4% annually. This documented linear convention is not silently corrected. The cash-interest sensitivity instead models 4% effective annual cash return and therefore also reports the consistent geometric daily benchmark. The mismatch between these conventions can matter particularly in nearly cash-only accounts.

For comparison, the synthetic equal-weight daily return composite's Sharpe was {composite_full:.5f}. It is a different estimand from both −21.80107 (mean of investor ratios) and −1.93437 (median). It is not presented as the investor-level mean, an actual pooled brokerage account, or evidence that averaging away low-exposure investors improves their own outcomes.

## 3. Why cash was 85.62%

No protected reserve is inside brokerage: **0% of observed brokerage cash is a reserve balance**. Reserve is subtracted once from monthly income minus mandatory expenses; only the resulting buffer is contributed. There was no second subtraction in portfolio accounting. Monthly reserve withholding is a flow assumption inherited from the application, not verified accumulation of a real emergency fund. Initial INR 100,000 is pre-existing unreserved brokerage savings. Discretionary expenses are recorded but not deducted by the implemented buffer formula.

Original purchase authorization resets to buffer × tier × multiplier. Accumulated unspent brokerage cash does not enlarge that budget. Tier withholding, small top-three weighted slots, unaffordable selected securities, no repeat purchases of holdings, candidate exhaustion and residual whole-share rounding explain low deployment. This is restrictive rule/design behavior and interaction, not a detected cash-balance or double-reserve accounting defect. {findings['zero_orders_despite_feasible_one_share']} Full decisions placed no order despite at least one currently eligible one-share candidate costing no more than the entire batch budget. This is a selection/sizing interaction; it does not prove the same three-slot basket was affordable.

At the monthly signal points, the mean fraction of brokerage cash deferred by the current-month-only authority was {stage_percentages['deferred_accumulated_cash']:.5%}; tier withholding accounted for {stage_percentages['tier_withheld']:.5%}; authorized but unused budget for {stage_percentages['unused_authorized_budget']:.5%}; and proposed purchases for {stage_percentages['proposed_notional']:.5%}. These signal-time averages decompose purchase authorization; they are not a causal partition of the separate daily 85.62% cash statistic. All 432 decisions had 40 valid-history candidates before holdings/sector checks. All 93 zero-eligibility decisions had already held every one of those 40 stocks. Missing history and a reserve in brokerage therefore explain none of those cases. Outside-household accumulated savings balances are unmodeled, not measured as zero; the model assumes no additional transfer beyond the stated buffer.

{table(reasons)}

All original brokerage cash is financially unreserved money; only a subset is authorized for current orders. Therefore 100% is genuinely unused brokerage cash, but it is incorrect to call 100% immediately policy-deployable. Mean authorized-budget fill was {findings['original_full_mean_budget_fill']:.5%}, while mean cumulative unique brokerage funding deployed was {findings['original_full_mean_unique_funding_deployed']:.5%}. These differ from the prior contributed-surplus utilization of 7.95610%, which excluded starting cash from its denominator.

{table(compact)}

CASH_UTILIZATION.csv provides a non-overlapping cash-at-signal waterfall: accumulated cash deferred by monthly authority, tier withholding, risk-multiplier withholding, rounding, no-candidate budget, unaffordable selected slots, positive-slot round-lot residual and proposed notional. Their sum reconciles to cash at that decision. Execution costs and overnight changes are shown separately. Sums over opportunities are NOT unique money; unique funding and reserve flow/target are separately identified. These stage labels quantify authorization, not causal Shapley contributions of interacting rules.

## 4. Confirmed corrections and unchanged rules

The confirmed reporting defect was HHI breach-frequency denominator handling. Mean HHI already excluded NA and cash was never an equity sector. The corrected denominator uses only valid holdings observations and explicitly reports coverage. Full had {findings['full_undefined_hhi_sessions']} undefined primary HHI sessions. Breach totals and conditional means remain unchanged.

{table(old_hhi)}

Cross-profile means of conditional breach frequencies and pooled valid-session frequencies are different estimands. Both are provided, together with exact denominators:

{table(pooled)}

No propagation, reserve double-counting, TWR, transaction-cost or Sharpe arithmetic defect was found. No production source was changed. A more complete event-level response definition includes policy releases: the prior breach-episode latency only credited modifications while a breach remained active, so it did not count the concentrated-start release effects. This is reported as a different event/episode outcome, not evidence that a breach was corrected by selling.
'''
    (out/'ROOT_CAUSE_ANALYSIS.md').write_text(root)
    exp=matched[matched.matching=='common_positive_opening_exposure'].copy()
    exp['gross_cvar_difference']=exp.full_unit_gross_cvar95-exp.base_unit_gross_cvar95
    exposure_summary=exp.groupby('contrast')[['paired_sessions','coverage','gross_cvar_difference']].mean().reset_index()
    changes=summaries[summaries.variant=='accumulated_approved_cash_v1'].groupby('strategy')[['annualized_return','average_cash_allocation','affordability_violation_rate','surplus_utilization','mean_hhi','hhi_breach_sessions','direct_feedback_changed_decisions']].mean().reset_index()
    stats=uncertainty[(uncertainty.scenario=='medium_moderate')&uncertainty.experiment.isin(['cash_interest','capital_authorization'])]
    report=f'''# Updated research report: diagnostics and controlled re-evaluation

Evidence classification remains **exploratory restricted-universe historical research**. No previous baseline file was overwritten. The initial root-cause report preceded implementation. This report distinguishes software correctness, internal policy changes, final decisions, actual transactions and risk correction.

## 1. Motivation and original findings

Run03 reported 55 principal feedback adjustments but zero changed recommendations, mean Full Sharpe −21.80107 and 85.62147% cash. H1 had controlled compliance support; H2 was mixed; central H3 effectiveness was unsupported; financial performance varied with exposure. These historical findings remain preserved. The same frozen 40-security, 57,400-observation dataset and 2022–2025 primary window were used here, with no ranking retuning, calendar selection or forced selling.

## 2. Root causes and validation

See ROOT_CAUSE_ANALYSIS.md and its event classifications. All 36 principal and six concentrated-start No Feedback/Full reproductions matched the old financial metrics, daily ledger and final baskets. Twenty-seven focused checks verified application/research feedback parity, policy propagation, independent high-precision Sharpe calculations, annualization, benchmark conversion, constant-denominator handling, contributions, reserve deduction, authorization-waterfall reconciliation, cash compounding and HHI. Independent position-level sector aggregation verified replay HHI. No unrelated application/UI tests or database connections were used.

Investor-level Full results before aggregate summaries (rates are fractions):

{table(investor_sharpe)}

## 3. Corrected reporting

The HHI breach denominator now excludes undefined equity-portfolio sessions. NA is not zero HHI. Original means and breach counts remain valid. Investor-level Sharpe arithmetic was correct under its stated linear benchmark; the former mean alone was misleading. We report mean, median, quantiles, range, defined/undefined count and exposure, retaining all unfavorable finite ratios. A separately constructed equal-weight daily return composite is not presented as an investor-average ratio or actual shared investment account.

{table(shard)}

## 4. Experiment A: feedback isolation

Same-state probes hold the pre-decision portfolio, budget base, price data, tier and ranking fixed, changing only active feedback versus the initial fixed No Feedback policy. Event probes evaluate every opportunity while a state persists. A separately labelled prior-state probe asks what the immediately previous policy would have proposed on the same actual later state; releases relative to that counterfactual are not Full-versus-No Feedback effects. Actual Full/No Feedback path differences remain a separate output.

{table(impact)}

The original principal null result is retained. Internal eligibility changes are not final recommendation changes; final proposal changes are not automatically executions; executions are not proof of risk correction. The concentrated-start extension remains targeted diagnostic evidence. Any accumulated-authority decision effect belongs to that separately named assumption. No new selling/rebalancing policy was introduced.

## 5. Experiments B and D: capital authorization and cash-interest sensitivity

No corrected-accounting arm was invented because no cash/reserve accounting defect was confirmed. Instead, accumulated_approved_cash_v1 explicitly treats pre-existing unreserved brokerage savings and previous approved contributions as deployable capital and applies the unchanged tier/multiplier to this balance. Only the same reserve-protected buffer enters each month. Ranking, held-stock exclusion, whole-share sizing, trade timing and costs remain unchanged. This changes deployment authority; it is not a software correction or independently validated improvement. We report proposal excess against the original monthly reference even when cumulative approved funds cover it; that definition is not silently weakened.

Cash-interest models hold stock trades and contributions exactly fixed. Interest of 0% or 4% effective annual accrues on opening cash, including beginning-session contributions, over 252 observed sessions and is kept in an unspent subledger. Interest cannot feed back into stock selection in this experiment. It is a modeling sensitivity, not a guaranteed available cash product. Both the original linear daily benchmark and matched effective geometric benchmark are retained as separate dimensions.

Full investor-profile means, except median Sharpe:

{table(full_table)}

All-policy alternative-authorization results (zero-interest cash, original financial metric definitions):

{table(changes)}

Authorized-decision-budget fill, original unique funding deployment and daily cash allocation have different denominators; none is called total household investment efficiency. Reserve withholding flows, reserve targets, untransferred household funds, brokerage funding and account cash are separate in CASH_PROFILE_SUMMARY.csv. No duplicate reserve was found. The alternative may spend accumulated approved savings beyond a current month's buffer, so original RQ1 monthly-cap compliance cannot be assumed for it.

## 6. Experiment C: exposure-conditioned comparisons

No strategy was forced to buy, sell or violate a rule to match exposure. We used fixed pre-specified opening-exposure bins [0,.05,.25,.50,.75,1], same profile/date pairing, and a second stricter same-bin comparison. Gross sleeve P&L adds back actual fees/slippage; net P&L includes them. Per-unit opening equity P&L is undefined with zero opening equity; entry costs on those dates are separately excluded from that diagnostic. These are normalized diagnostics, not executable equity-only strategies. Conditional drawdown resets between unmatched date gaps rather than compounding across omitted dates. Matching coverage and insufficient intervals are explicit.

{table(exposure_summary)}

The substantially lower Risk Only HHI is not caused by including cash as a sector or assigning empty portfolios zero HHI: neither occurred. Larger executable budgets and broader acquired holdings under the same no-repeat rule can change invested-sector breadth. Exposure normalization cannot remove stock-selection/path differences and may introduce selection bias. It supports descriptive risk/return trade-off analysis, not causal superiority.

## 7. Effects on research conclusions

- **RQ1 remains supported for the original controlled policy:** the household monthly gate prevented original proposed overspend. New accumulated authority has a different authorization assumption; monthly-reference violations remain reported and cannot be relabelled as original compliance.
- **RQ2 needs qualification:** original concentration improvements remain; denominator correction improves comparability but does not create a downside-risk win. Equity-only concentration and exposure-conditioned losses must be reported alongside account losses and cash.
- **RQ3 remains unsupported in the original principal design:** recording 55 policy updates did not establish changed recommendations or risk correction. The pipeline correctly propagated meaningful rules, but existing exposure ordering, other exclusions, whole-share sizing and timing often made them nonbinding. Targeted or alternative results remain separately labelled.
- **RQ4 remains a trade-off conclusion:** cash treatment, capital authority and invested exposure materially influence risk-adjusted performance. Mean investor Sharpe alone is not a sufficient summary. No policy is declared superior on these diagnostics.

## 8. Statistical uncertainty

Paired circular calendar-block bootstrap intervals use 20-session blocks, 2,000 draws and seed 20261024. Shared dates are resampled together. Exposure matching retains unobserved slots as NaN in the common calendar; intervals with fewer than 60 matched sessions are explicitly unavailable. This avoids inventing independent observations or reliable inference from sparse matches. Representative medium/moderate contrasts below are differences in annualized arithmetic mean daily returns, not CAGR differences:

{table(stats[['experiment','valid_paired_sessions','mean_annualized_arithmetic_return_difference','ci95_low','ci95_high','interval_status']])}

Profiles are synthetic design choices and market windows overlap. These intervals condition on the observed restricted universe and do not establish population efficacy, a forecast or independent out-of-sample performance. All results, including unfavorable contrasts, remain in UNCERTAINTY.csv and EXPOSURE_MATCHED_COMPARISONS.csv. No p-values were fabricated.

## 9. Remaining limitations and future work

Survivorship and current-sector bias, missing delisted names, incomplete point-in-time eligibility and partial corporate-action certification remain unchanged. No new market data was substituted. Dividend payment-date approximation, no cash-product frictions, simplified fees/taxes and buy-only execution remain assumptions. The chronological primary sample was not used to tune a new policy; accumulated authority is a transparent sensitivity, not a claim of validated improvement. A future operational change should explicitly separate monthly savings capacity, previously approved brokerage capital, reserve-stock targets and contribution flows, then evaluate a prespecified policy on held-out dates. Candidate affordability before limited-slot selection and held-stock re-entry require separate versioned studies rather than silent changes to Full IntelliVest. Corrective selling would be a new investment policy, not a repair to the current restriction system.

## 10. Figures and reproducibility

Six real-data figures are in figures/ as 300-dpi PNG and SVG, with CAPTIONS.md. DIAGNOSTIC_CONFIG.json records parameters, source hashes and package versions; source_snapshot/ contains executed diagnostics. BASELINE_REPRODUCTION.json and FOCUSED_CHECKS.json record numerical checks. PRESERVATION_CHECK.json verifies prior results, original conference draft, dataset and inspected application sources unchanged. No database write path or live account was used. No commit was created; GIT_STATUS.txt records the pre-existing dirty tree and new research files.

Methodology references: [Sharpe (1994)](https://web.stanford.edu/~wfsharpe/art/sr/sr.htm), [GIPS cash-flow-aware return methodology](https://www.gipsstandards.org/standards/gips-standards-for-firms/gips-standards-handbook-for-firms/). The use of these definitions does not claim standards compliance or support investment superiority.
'''
    (out/'UPDATED_RESEARCH_REPORT.md').write_text(report)
    (out/'CONFERENCE_INTERPRETATION.md').write_text('''# Additional conference interpretation — original paper and drafts unchanged

Use UPDATED_RESEARCH_REPORT.md and ROOT_CAUSE_ANALYSIS.md with the immutable run03 evidence.

| Claim | Evidence and required wording |
|---|---|
| Working feedback pipeline | Static inspection and eight offline policy combinations support single-account rule propagation; real asynchronous delivery latency was not experimentally measured. |
| Policy updates occurred | 55 effective state updates in the original principal scenarios; this is not 55 changed recommendations. |
| Recommendations changed | Original primary final baskets did not change. Candidate eligibility changes, event-level updates and targeted stress effects are separately reported. |
| Portfolio risk was corrected | Buy restrictions cannot directly sell existing exposure. An adjustment or even a changed order is not proof of shorter concentration breaches. |
| Sharpe was incorrect | Arithmetic was independently reproduced. The mean investor ratio was a poor standalone summary; retain it and add distributions, exposure and cash/benchmark assumptions. |
| Cash was a protected reserve | False for the simulation: no protected reserve entered brokerage. Distinguish unreserved account cash from the amount authorized for current orders. |
| Integrated safeguards outperform | Not established by the original experiment or these conditional diagnostic sensitivities. Report compliance support, mixed risk and exposure/performance trade-offs. |

Correct the HHI breach-frequency denominator in new material, explicitly retain the old frequency convention as historical reporting, and show undefined-session counts. Do not rewrite the original experiment with a modified cash authorization model. New assumption results and the targeted stress remain exploratory and are not independently validated policy improvements.
''')
    (out/'README.md').write_text('''# Diagnostic output index

- INITIAL_ROOT_CAUSE_REPORT.md: inspection findings and fixed design before implementation.
- ROOT_CAUSE_ANALYSIS.md / UPDATED_RESEARCH_REPORT.md: validated interpretation and executed comparisons.
- FEEDBACK_TRACE.csv / FEEDBACK_EVENT_OPPORTUNITIES.csv: one row per effective event and every actual opportunity while active.
- REPLAY_DIAGNOSTICS.csv: full policy/candidate/quantity/cash snapshots per decision; fixed-policy same-state counterfactuals.
- SHARPE_DIAGNOSTICS.csv / SHARPE_DISTRIBUTION.csv: investor-first metrics, conventions, validity and distributions.
- CASH_UTILIZATION.csv / CASH_PROFILE_SUMMARY.csv: per-decision disjoint authorization and per-profile unique funding.
- SENSITIVITY_RESULTS.csv: profile-level controlled cash/benchmark/authorization dimensions.
- HHI_DIAGNOSTICS.csv / EXPOSURE_MATCHED_COMPARISONS.csv / EXPOSURE_STRATA.csv: valid-session concentration and descriptive exposure controls.
- UNCERTAINTY.csv: paired conditional moving-block intervals, with sparse comparisons flagged unavailable.
- CONFERENCE_INTERPRETATION.md: claim-level qualifications without overwriting previous drafts.
- figures/: six PNG/SVG figures and captions.

Run from repository root with the repository plus matplotlib dependencies. The initial report/hash manifest must exist before executing `python -m research.diagnostics.runner --out <new-directory>`. The runner refuses an existing DIAGNOSTIC_CONFIG.json. Frozen reference paths and settings are in DIAGNOSTIC_CONFIG.json. Original stock trades are kept fixed in cash-interest overlays. All profile monetary units are INR; return, risk, exposure and frequency values are fractions; event latency is observed sessions; undefined values are blank/NA, not zero. See source_snapshot for the exact code. No live database access is performed.
''')
