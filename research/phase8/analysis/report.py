"""Eight exported research figures and standalone Phase 8 reports."""
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd


def md(df):
    def cell(x):
        if isinstance(x,(float,np.floating)):return 'NA' if not np.isfinite(x) else f'{x:.5f}'
        return str(x)
    return '| '+' | '.join(map(str,df.columns))+' |\n| '+' | '.join(['---']*len(df.columns))+' |\n'+'\n'.join('| '+' | '.join(cell(x) for x in row)+' |' for row in df.itertuples(index=False,name=None))


def generate(out):
    os.environ.setdefault('MPLCONFIGDIR','/private/tmp/intellivest-phase8-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    s=pd.read_csv(out/'investor_level_results.csv');v=pd.read_csv(out/'risk_metrics.csv',parse_dates=['date'])
    d=pd.read_csv(out/'recommendation_decisions.csv',parse_dates=['date'])
    stats=pd.read_csv(out/'statistical_comparisons.csv');path=pd.read_csv(out/'feedback_path_differences.csv')
    main=s[(s.kind=='principal')&(s.window=='primary_2022_2025')];mean=main.groupby('policy').mean(numeric_only=True)
    policies=['V1','V2','V3','V4','V5'];colors=dict(zip(policies,['#777777','#AD6E22','#397DAD','#23866A','#8A5BA6']))
    profiles=['low_conservative','medium_moderate','high_aggressive']
    primary_v=v[(v.kind=='principal')&(v.window=='primary_2022_2025')]
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,
                         'axes.grid':True,'grid.alpha':.18,'savefig.dpi':300})
    figures=out/'figures';figures.mkdir(exist_ok=True);captions=[]
    def save(fig,name,caption):
        fig.tight_layout();fig.savefig(figures/(name+'.png'),bbox_inches='tight');fig.savefig(figures/(name+'.svg'),bbox_inches='tight');plt.close(fig)
        captions.append(f'**{name}** — {caption}')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,col,title in [(axes[0],'authorized_budget_utilization','Unique external approval deployed'),(axes[1],'mean_cash_allocation','Average account cash')]:
        ax.bar(policies,mean.loc[policies,col]*100,color=[colors[p] for p in policies]);ax.set(ylabel='Percent (%)',title=title)
    fig.suptitle('Figure 1. Approved investment authority and portfolio cash',y=1.02)
    save(fig,'figure_1_capital_utilization','Equal-profile means, primary 2022–2025. Each external approval is counted once. Cash includes unapproved starting savings and tier-withheld transfers, but no protected reserve. Utilization and cash allocation have different denominators.')
    fig,axes=plt.subplots(1,3,figsize=(12,3.8))
    for ax,profile in zip(axes,profiles):
        for policy in policies:
            g=primary_v[(primary_v.scenario==profile)&(primary_v.policy==policy)].sort_values('date')
            ax.plot(g.date,g.equity/100000,color=colors[policy],label=policy,lw=1.1)
        g=primary_v[(primary_v.scenario==profile)&(primary_v.policy=='V1')].sort_values('date')
        ax.plot(g.date,(100000+g.contribution.cumsum())/100000,ls=':',color='#333',label='Capital supplied')
        ax.set(title=profile.replace('_',' ').title(),ylabel='Account value (INR lakh)',xlabel='Date');ax.tick_params(axis='x',rotation=30)
    axes[-1].legend(fontsize=7);fig.suptitle('Figure 2. Portfolio value under identical contributions',y=1.02)
    save(fig,'figure_2_portfolio_value','Nominal equity includes contributions. Dotted lines show the same initial cash plus transfers. Cash-flow-adjusted returns are separately reported; increased contributions are not counted as profits.')
    fig,axes=plt.subplots(1,3,figsize=(12,3.8))
    for ax,profile in zip(axes,profiles):
        for policy in policies:
            g=primary_v[(primary_v.scenario==profile)&(primary_v.policy==policy)].sort_values('date')
            ax.plot(g.date,g.hhi,color=colors[policy],label=policy,lw=1)
        ax.axhline(.25,color='#333',ls='--',lw=.8);ax.set(title=profile.replace('_',' ').title(),ylabel='Invested-sector HHI',xlabel='Date',ylim=(0,1.05));ax.tick_params(axis='x',rotation=30)
    axes[-1].legend(fontsize=7);fig.suptitle('Figure 3. Equity-only sector concentration and breaches',y=1.02)
    save(fig,'figure_3_hhi','Cash is not a sector; empty portfolios have undefined HHI. Initial three-sector bootstrap baskets may breach .25 and are explicitly monitored. New guards prevent worsening purchases; subsequent market drift can still cause breaches.')
    fig,axes=plt.subplots(1,3,figsize=(12,3.8))
    for ax,profile in zip(axes,profiles):
        for policy in policies:
            g=primary_v[(primary_v.scenario==profile)&(primary_v.policy==policy)].sort_values('date');wealth=(1+g['return']).cumprod().to_numpy();peak=np.maximum.accumulate(np.r_[1.,wealth])[1:]
            ax.plot(g.date,(wealth/peak-1)*100,color=colors[policy],label=policy,lw=1)
        ax.set(title=profile.replace('_',' ').title(),ylabel='Time-weighted drawdown (%)',xlabel='Date');ax.tick_params(axis='x',rotation=30)
    axes[-1].legend(fontsize=7);fig.suptitle('Figure 4. Drawdown with external flows removed',y=1.02)
    save(fig,'figure_4_drawdown','Drawdown uses a time-weighted wealth index and includes the initial peak of one. Increased capital deployment is not automatically improved downside performance.')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    ds=d[(d.kind=='principal')&(d.window=='primary_2022_2025')]
    x=np.arange(5)
    feasible=ds.groupby('policy').feasible_single_share_opportunity.sum().reindex(policies)
    executed=ds.assign(purchased=ds.executed_cost>0).groupby('policy').purchased.sum().reindex(policies)
    axes[0].bar(x-.18,feasible,width=.36,label='Single-share feasible opportunity');axes[0].bar(x+.18,executed,width=.36,label='Executed purchase decision')
    axes[0].set_xticks(x,policies);axes[0].set(ylabel='Monthly decisions (nine profiles)',title='Feasible opportunity and execution');axes[0].legend(fontsize=7)
    resolved=pd.read_csv(out/'original_218_resolution.csv').set_index('policy').reindex(policies)
    axes[1].bar(policies,resolved.executed_now,color=[colors[p] for p in policies]);axes[1].axhline(218,color='#555',ls='--',lw=.8)
    axes[1].set(ylabel='Matched historical decisions',title='Original 218 witnesses executing under new paths')
    fig.suptitle('Figure 5. Purchase feasibility and execution efficiency',y=1.02)
    save(fig,'figure_5_execution_efficiency','A feasible single-share witness is not proof of global integer-basket feasibility. Original witness resolution is matched by date/profile on different evolving portfolio paths; it is not a causal claim that all 218 could be resolved under identical states.')
    selling=s[(s.kind=='corrective_selling')&(s.window=='primary_2022_2025')].groupby('policy').mean(numeric_only=True)
    feedback=pd.concat([mean,selling]);labels=policies+['V5_SELL']
    fig,axes=plt.subplots(1,2,figsize=(11,4.2));x=np.arange(len(labels));w=.25
    for i,(col,label) in enumerate([('policy_updates','Policy updates'),('changed_recommendations','Changed proposals'),('actual_trade_changed_decisions','Changed execution decisions')]):
        axes[0].bar(x+(i-1)*w,feedback.reindex(labels)[col],width=w,label=label)
    axes[0].set_xticks(x,labels,rotation=20);axes[0].set(ylabel='Mean count per profile',title='State changes versus actions');axes[0].legend(fontsize=7)
    axes[1].bar(labels,feedback.reindex(labels).hhi_breach_sessions,color=[colors.get(p,'#B34F4F') for p in labels]);axes[1].set(ylabel='Mean observed HHI-breach sessions',title='Risk persistence measured separately');axes[1].tick_params(axis='x',rotation=20)
    fig.suptitle('Figure 6. Feedback effects and observed concentration persistence',y=1.02)
    save(fig,'figure_6_feedback','V1–V4 same-state counters freeze original feedback; V5 counters use V4 on the same state. V5_SELL is a separate secondary intervention. Resolution/shorter persistence is observed, not automatically attributed to a policy update. Comparisons have the same nine primary profiles.')
    fig,ax=plt.subplots(figsize=(7.5,4.8))
    for policy in policies:
        g=main[main.policy==policy];ax.scatter(g.annualized_volatility*100,g.annualized_return*100,color=colors[policy],label=policy,s=35,alpha=.8)
    ax.set(xlabel='Annualized account volatility (%)',ylabel='Annualized time-weighted return (%)',title='Figure 7. Risk and return across nine synthetic profiles');ax.legend(ncol=5,fontsize=8)
    save(fig,'figure_7_risk_return','Every point is a profile-policy outcome on the same previously inspected window. Differences in exposure, guards, selection and top-ups are examined in ablations; this is not a fitted efficient frontier.')
    ab=s[s.kind=='construction_ablation'].groupby('policy').mean(numeric_only=True)
    all_means=pd.concat([mean,ab]);ab_labels=['V1','GUARDS_ONLY','FEAS_ONLY','TOPUP_ONLY','V3','V2','V4','V5']
    fig,axes=plt.subplots(1,2,figsize=(12,4.3))
    for ax,col,title in [(axes[0],'authorized_budget_utilization','Approved-authority utilization (%)'),(axes[1],'cvar95','Realized daily CVaR95 (%)')]:
        ax.bar(ab_labels,all_means.reindex(ab_labels)[col]*100,color=[colors.get(p,'#57849A') for p in ab_labels]);ax.set(ylabel=title);ax.tick_params(axis='x',rotation=35)
    fig.suptitle('Figure 8. Construction ablations and interaction trade-offs',y=1.02)
    save(fig,'figure_8_ablations','Guard-only, feasibility-only and top-up-only arms share the new safeguards. V1/V3 is a combined change including guard assumptions, not a pure feasibility estimate. Returns/risks are descriptive and are not selected to favor higher deployment.')
    (figures/'CAPTIONS.md').write_text('\n\n'.join(captions)+'\n')
    # Preserve investor-first Sharpe, including extreme finite negative ratios.
    dist=[]
    for policy,g in main.groupby('policy'):
        z=g.loc[g.sharpe_valid,'sharpe']
        dist.append({'policy':policy,'defined':len(z),'undefined':len(g)-len(z),'mean_sharpe':z.mean(),'median_sharpe':z.median(),'min_sharpe':z.min(),'max_sharpe':z.max()})
    dist=pd.DataFrame(dist);dist.to_csv(out/'sharpe_distribution.csv',index=False)
    cols=['authorized_budget_utilization','feasible_but_unexecuted','mean_cash_allocation','purchase_frequency','mean_hhi','hhi_breach_frequency','hhi_breach_sessions','var95','cvar95','maximum_drawdown','annualized_volatility','annualized_return','sharpe','turnover','transaction_fees','slippage_cost','new_position_trades','topup_trades','changed_recommendations','actual_trade_changed_decisions','household_new_draw_violations','monthly_reference_violation_rate']
    comparison=mean.reindex(policies)[cols].T.reset_index().rename(columns={'index':'metric'})
    table=md(comparison)
    ab_table=pd.concat([main,s[s.kind=='construction_ablation'],s[s.kind=='momentum_ablation']],ignore_index=True).groupby('policy')[['authorized_budget_utilization','feasible_but_unexecuted','annualized_return','cvar95','mean_hhi','topup_trades','turnover']].mean().reset_index()
    group=stats[stats.window=='primary_2022_2025'].groupby('contrast')
    paired=group[['authorized_budget_utilization_difference','annualized_return_difference','cvar95_difference','hhi_breach_sessions_difference']].agg(['mean','median'])
    paired.columns=['_'.join(c) for c in paired.columns];paired.reset_index().to_csv(out/'paired_mean_median_differences.csv',index=False)
    def grade(condition):return 'Supported in the studied scenarios' if condition else 'Unsupported in the studied scenarios'
    gains=mean.loc['V2','authorized_budget_utilization']-mean.loc['V1','authorized_budget_utilization']
    a=ab_table.set_index('policy')
    grades={'RQ6':grade(gains>1e-6),'RQ7':grade(a.loc['FEAS_ONLY','feasible_but_unexecuted']<a.loc['GUARDS_ONLY','feasible_but_unexecuted']),
        'RQ8':'Partially supported' if a.loc['TOPUP_ONLY','topup_trades']>0 else 'Unsupported',
        'RQ9':'Supported for measured actionability and concentration persistence' if mean.loc['V5','changed_recommendations']>0 and mean.loc['V5','hhi_breach_sessions']<mean.loc['V4','hhi_breach_sessions'] else 'Partially supported' if mean.loc['V5','changed_recommendations']>0 else 'Unsupported for incremental principal purchase-redirection actionability',
        'RQ10':'Inconclusive as an overall superiority claim; measured risk/performance trade-offs available'}
    (out/'HYPOTHESIS_CLASSIFICATION.json').write_text(json.dumps(grades,indent=2)+'\n')
    implementation=f'''# Phase 8 implementation report

All proposed behavior is isolated under research/phase8/. No application, schema, user record, original output or original conference draft was modified. Exact source is archived in source_snapshot. Data and 489 prior files are protected by PRESERVED_HASHES.json; final preservation checks report the actual count.

## Behavioral versions

V1 reproduces original Full. V2 carries unused **tier-approved monthly quotas**, with zero initial grant, FIFO spending, 12-month expiry and revocation on reduced household capacity. It does not reinterpret all brokerage cash as approved and does not apply the tier twice. V3 retains monthly-reset authority, selects feasible valid candidates and allows controlled top-ups. V4 combines these mechanisms. V5 adds all-overweight-sector purchase redirection and strict HHI improvement on breached portfolios. V5_SELL is a separate secondary arm with explicit corrective selling, adverse slippage, fees, proportional basis and re-approval of actual net proceeds as recycled rather than external authority. There is no live execution.

New guards: position 20% and sector 35% of account equity; grandfathered drift-overweight nominal positions cannot be enlarged (fees can marginally change account fractions). Equity-only HHI cannot worsen an existing breach and must remain <=.25 after it has been attained; empty-account bootstrap is explicitly allowed/flagged. Existing volatility/VaR limits use complete point-in-time 30-return estimates, with nonworsening treatment of existing breaches. No hard CVaR threshold or universal no-breach claim is introduced. Existing holdings plus proposed shares enter every guard.

Authority conservation: external grants + recycled grants − external spending − recycled spending − expiry − revocation = unspent authority. Available=min(cash,unspent authority). Purchases consume actual inclusive cost exactly once. Budget utilization uses external-funded spending divided by unique external approval grants. Monthly repeated balances are not summed as fresh capital. Legacy monthly-reference excess and fresh household/authority violations are distinct outputs. Protected reserve never enters brokerage.

Shared source-compatible priority fills use next-session close, integer quantities and saved budget/cash/authority caps. New guard-enabled variants revalidate the combined fill; unsafe baskets cancel. Sales execute before buys only in V5_SELL. Signal sizing uses observed prices and cached historical ranking; risk estimates for fill checks use the lagged decision window. Corporate-action adjustment and dividend timing conventions are inherited and limited, not silently repaired. No future return observation is used.

Reused: original synthetic profiles, score/momentum ranking cache, original selector for legacy variants, risk definitions, time-weighted returns, investor-level Sharpe diagnostics, cash overlays and paired moving-block uncertainty. New code implements FIFO authority, risk-aware integer construction, top-ups, corrective sales, instrumentation, validation and report generation. The initial V1 reproduction covered 36 accounts; shared-engine V1 parity is separately checked before revised runs. See RUN_CONFIG.json and protocol for all equations/assumptions.
'''
    (out/'PHASE8_IMPLEMENTATION_REPORT.md').write_text(implementation)
    ablation=f'''# Phase 8 ablation study

All windows were previously inspected. These are exploratory controlled mechanism comparisons, not held-out predictions. Guards are explicit additional assumptions; guard-only, feasibility-only and top-up-only controls expose this confounding rather than hiding it. No coefficients were optimized for returns.

{md(ab_table)}

V2−V1 isolates the specified carry-forward authority design, not unrestricted use of starting savings. FEAS_ONLY−GUARDS_ONLY investigates candidate feasibility under the same new safeguards. TOPUP_ONLY−GUARDS_ONLY investigates categorical holding exclusion under those safeguards. V3 combines them; V4 additionally carries approvals. V5−V4 isolates purchase redirection. Selling is reported separately and cannot be credited to redirection alone. V4_NO_MOMENTUM uses the existing cached baseline score with only momentum's contribution zeroed. Candidate quality claims remain limited to the implemented historical screening/ranking, not predictive proof.

Matched resolution of the prior 218 nominal single-share witnesses:

{md(resolved.reset_index())}

Different portfolio paths can change current eligibility and risk bounds, so this is an observed matched-date/profile comparison, not a claim that every earlier witness should have been traded. Cash-interest sensitivity holds trades fixed. See ablation_results.csv, investor_level_results.csv and cash_interest_sensitivity.csv for per-investor unfavorable and neutral outcomes.
'''
    (out/'PHASE8_ABLATION_STUDY.md').write_text(ablation)
    selling_table=s[s.kind=='corrective_selling'][['scenario','policy','annualized_return','cvar95','mean_hhi','hhi_breach_sessions','turnover','transaction_fees','sell_trades','realized_gain']]
    feedback_table=main.groupby('policy')[['policy_updates','changed_recommendations','actual_trade_changed_decisions','hhi_episodes_resolved','hhi_episode_resolution_fraction','hhi_breach_sessions','feedback_incremental_fees']].mean().reset_index()
    stats_sample=stats[(stats.window=='primary_2022_2025')&(stats.scenario=='medium_moderate')][['contrast','mean_annualized_arithmetic_return_difference','ci95_low','ci95_high','interval_status']]
    results=f'''# Phase 8 results: capital efficiency and actionable feedback

Evidence classification: **exploratory historical comparison on previously inspected restricted-universe data**. No new holdout or overall-superiority claim is made. V1 was reproduced before revised policies. {len(s)} distinct configured replays completed. Prior studies, data and source remain protected. All monetary values are INR; rates/returns are fractions unless a figure says percent; duration is observed sessions. Means below weight the nine synthetic profiles equally. Undefined Sharpe/HHI is NA, never zero.

## Five-policy primary comparison (2022–2025)

{table}

Authority utilization counts each external approval once. The monthly-reference rate retains the original proposed notional > current monthly buffer definition, even when older valid approvals fund spending; it must not be relabelled as new household overspending. Fresh household, authority and reserve violations are separately verified. Initial unapproved cash and tier withholding are not misdescribed as protected reserves. The controlled carry design differs from the precursor unrestricted-cash sensitivity.

## RQ6–RQ10

'''+'\n'.join(f'- **{k}: {value}.**' for k,value in grades.items())+f'''

More deployed money is not proof of better stock selection. Additional guards, feasibility order, top-ups and carry interact; the ablation controls and exposure diagnostics are necessary. No conclusion is based only on the policy with highest return. Investor-level Sharpe and its range are retained rather than concealing unfavorable small-volatility outcomes:

{md(dist)}

## Feedback responsiveness versus risk correction

{md(feedback_table)}

Same-state counters isolate active policy rules at the same actual portfolio/budget base. V1–V4 compare original feedback with a fixed initial policy; V5 compares its additional intervention with V4. Incremental fees/slippage are signed differences against an execution counterfactual, not the total cost of every basket marked changed. Paired path differences are separately exported. Breach resolution is an observed event outcome with terminal censoring, not automatically caused by a restriction or proposal. Policy timing is immediate state application at the scheduled daily observation, not measured live delivery latency.

## Secondary corrective-selling arm (not mixed into V5)

{md(selling_table)}

Selling is whole-share, capped at 10% invested value per monthly decision, minimum INR 500, requires lower measured HHI, and pays the same fees/adverse slippage. It never liquidates to manufacture an empty diversified portfolio. Taxes are excluded. Recycled proceeds are recorded separately from household approvals. Trades are simulated only. Compare this arm with V5 and V4 rather than attributing its effects to purchase redirection.

## Statistical evidence and robustness

Paired profile/window differences, mean/median differences and circular 20-session block intervals (2,000 draws, seed 20261024) are exported. Representative medium/moderate annualized arithmetic daily-return differences—not CAGR differences—are:

{md(stats_sample)}

Nine profiles are deterministic scenarios, not random sampled investors. Windows overlap and have all been examined previously. Conditional intervals do not support population efficacy or independent predictive validation; no p-values are invented. EXPOSURE_ADJUSTED.csv (lowercase filename exposure_adjusted.csv) reports same-date positive-exposure and same-bin coverage. Net/gross sleeve diagnostics are not equivalent to actual investor account returns, and sparse matches do not justify causal stock-selection claims.

## Limitations and interpretation

The 40-security current surviving universe omits delisted stocks and complete historical membership/identity. Sparse exchange checks do not certify every corporate action; vendor-adjustment vintages are unavailable. Current sector labels, split reconstruction and ex-date dividend availability are inherited approximations. The profiles are synthetic; reserve subtraction is the implemented monthly-flow convention and discretionary expenses remain outside the buffer deduction. Costs are simplified proportional assumptions with taxes/market impact excluded. New position/sector caps allow explicit bootstrap and grandfathered drift; they do not promise zero market-induced breaches. There is no hard CVaR eligibility limit, globally optimal integer allocation proof, or live automated trading. Construction can miss jointly feasible multi-stock solutions that require accepting an individually inadmissible intermediate lot.

Household-deterioration and concentrated-start stress results are separately labelled in investor_level_results.csv. They do not substitute for the primary null/unfavorable outcomes. A future product change requires explicit financial authorization semantics and prospective evaluation; no live behavior was changed here.

## Figures

'''+'\n\n'.join(captions)+'\n'
    (out/'PHASE8_RESULTS.md').write_text(results)
    conference='''# Phase 8 conference draft — separate from all earlier paper material

## Motivation

Earlier implementation and historical diagnostics showed that financial affordability constraints could coexist with high cash allocation and nonbinding feedback. We investigated a second-generation research policy without changing the live application or treating reused historical periods as untouched validation.

## Proposed Improvements

We implemented FIFO carry-forward of tier-approved monthly authority, feasibility-aware whole-share construction, controlled holding top-ups and explicit position/sector/risk guards. The principal feedback extension redirected purchases away from every overweight sector. A separate secondary arm investigated capped, cost-bearing corrective sales and recycled-proceeds authorization. Neither intervention placed live trades or modified user portfolios.

## Experimental Design

The same nine synthetic profiles, starting capital, reserve-protected contributions, restricted 40-security adjusted-price dataset, historical ranking/momentum inputs, monthly decisions, daily monitoring and next-session execution were shared. Fees/slippage were 10/5 bp. The primary 2022–2025 window and additional 2022–2023, 2024–2025 and 2026 YTD windows had previously been inspected; the entire study is exploratory. No outcome-driven parameter search or independent holdout claim was used.

## Baseline Comparison

V1 reproduced the frozen original Full policy before comparison. V2 changed approval carry-forward only; V3 changed feasible construction/top-ups with declared guards; V4 combined these mechanisms; V5 added purchase redirection. Corrective selling remained separate. The complete method, authority conservation equation, original monthly-reference overspend and alternative fresh-funding definitions are disclosed in the accompanying reports.

## Results

'''+table+'''

Investor-level results, including extreme finite Sharpe ratios, are retained. Higher utilization was not treated as proof of better risk-adjusted performance. Feedback state changes, recommendation changes, executed changes, costs and subsequent concentration persistence were separately measured.

## Ablation Analysis

'''+md(ab_table)+'''

## Discussion

'''+ '\n'.join(f'- {k}: {value}.' for k,value in grades.items())+'''

## Threats to Validity

Current-universe survivorship, incomplete point-in-time membership and corporate-action certification, synthetic household assumptions, previously examined dates, modeled cash authority and simplified transaction costs constrain external validity. The initial bootstrap and grandfathered drift are explicit guard exceptions. Conditional moving-block intervals are descriptive; correlated sessions and scenario permutations are not independent investor experiments. The ranked integer heuristic is reproducible but does not claim global optimality. No omitted live CVaR constraint or real-world tax model is implied.

## Conclusion

The study measured whether explicit authority, feasibility, top-up and feedback changes affected decisions and investment outcomes. The tables and ablations support only the component-specific classifications above. Results do not establish overall investment superiority, a validated forecast or readiness to apply new trading behavior to real users. Independent prospective evidence would be required before such claims.
'''
    (out/'PHASE8_CONFERENCE_DRAFT.md').write_text(conference)
    (out/'README.md').write_text('# Phase 8 outputs\n\nRead PHASE8_RESULTS.md, PHASE8_EXPERIMENTAL_METHOD.md and PHASE8_IMPLEMENTATION_REPORT.md. Per-investor data are in investor_level_results.csv; main five-policy means in policy_comparison.csv. V5_SELL, stresses and ablations remain separate. Source/config/data hashes and exact code snapshots are retained. All eight figures have PNG/SVG versions and captions. Earlier evidence remains unchanged.\n')
