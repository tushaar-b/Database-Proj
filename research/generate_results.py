"""Measured tables, publication figures and a guarded conference-results draft."""
import json
import os
from pathlib import Path
import numpy as np
import pandas as pd


def markdown(frame):
    def cell(x):
        if isinstance(x,(float,np.floating)):
            return 'NA' if not np.isfinite(x) else f'{x:.4f}'
        return str(x)
    return '| '+' | '.join(map(str,frame.columns))+' |\n| '+' | '.join(['---']*len(frame.columns))+' |\n'+ '\n'.join('| '+' | '.join(cell(x) for x in row)+' |' for row in frame.itertuples(index=False,name=None))


def generate(out):
    os.environ.setdefault('MPLCONFIGDIR','/private/tmp/intellivest-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from research.strategies import POLICIES
    s=pd.read_csv(out/'strategy_summaries.csv')
    v=pd.read_csv(out/'valuations.csv',parse_dates=['date'])
    v=v[v.kind=='principal']
    d=pd.read_csv(out/'decisions.csv',parse_dates=['date'])
    d=d[d.kind=='principal']
    p=pd.read_csv(out/'policy_changes.csv',parse_dates=['date'])
    p=p[p.kind=='principal']
    contrasts=pd.read_csv(out/'paired_comparisons.csv')
    config=json.loads((out/'config.json').read_text())
    primary=s[s.window=='primary_2022_2025']
    metrics=['affordability_violation_rate','mean_overspend','max_overspend','surplus_utilization','no_purchase_frequency',
        'mean_hhi','hhi_breach_sessions','cvar95','maximum_drawdown','annualized_volatility','cumulative_return',
        'annualized_return','sharpe','turnover','average_idle_cash','average_cash_allocation','transaction_fees','slippage_cost',
        'policy_adjustments','direct_feedback_changed_decisions','feedback_response_sessions']
    comparison=primary.groupby('strategy')[metrics].mean().reindex(POLICIES).T
    comparison.loc['max_overspend']=primary.groupby('strategy').max_overspend.max().reindex(POLICIES)
    comparison.index.name='Metric'
    comparison.reset_index().to_csv(out/'main_comparison.csv',index=False)
    primary.to_csv(out/'investor_scenario_comparisons.csv',index=False)
    subgroup=s.groupby(['window','surplus_group','tier','strategy'])[metrics].mean().reset_index()
    subgroup.to_csv(out/'robustness_subgroups.csv',index=False)
    comparison_text=markdown(comparison.reset_index())
    (out/'MAIN_COMPARISON.md').write_text('# Four-policy comparison\n\nPrimary 2022–2025 window; equal-weight descriptive means across nine synthetic profiles, except max_overspend, which is the maximum across all profiles. Fractional rates/returns, INR amounts, session durations. NA means undefined/unobserved, never zero. HHI averages exclude empty-equity dates.\n\n'+comparison_text+'\n')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,'axes.spines.right':False,
                         'axes.grid':True,'grid.alpha':.2,'figure.dpi':150,'savefig.dpi':300})
    colors=dict(zip(POLICIES,['#D28D22','#7B5AA6','#3479A8','#238268']))
    figdir=out/'figures';figdir.mkdir(exist_ok=True)
    captions=[]
    def save(fig,name,caption):
        fig.tight_layout()
        fig.savefig(figdir/(name+'.png'),bbox_inches='tight')
        fig.savefig(figdir/(name+'.svg'),bbox_inches='tight')
        plt.close(fig)
        captions.append(f'**{name}** — {caption}')
    profiles=['low_conservative','medium_moderate','high_aggressive']
    pv=v[v.window=='primary_2022_2025']
    fig,axes=plt.subplots(1,3,figsize=(12,3.5))
    for ax,profile in zip(axes,profiles):
        for policy in POLICIES:
            g=pv[(pv.scenario==profile)&(pv.strategy==policy)].sort_values('date')
            ax.plot(g.date,g.equity/100000,label=policy,color=colors[policy],lw=1.4)
        g=pv[(pv.scenario==profile)&(pv.strategy==POLICIES[0])].sort_values('date')
        ax.plot(g.date,(100000+g.contribution.cumsum())/100000,color='#777777',ls=':',label='Initial + contributions')
        ax.set(title=profile.replace('_',' ').title(),ylabel='Account value (INR lakh)',xlabel='Date')
        ax.tick_params(axis='x',rotation=30)
    axes[-1].legend(fontsize=7)
    fig.suptitle('Figure 1. Portfolio value and identical capital supplied',y=1.02)
    save(fig,'figure_1_portfolio_value','Nominal account equity includes contributions. Dotted lines show initial cash plus identical supplied capital; cash-flow-adjusted returns are reported separately.')
    fig,axes=plt.subplots(1,3,figsize=(12,3.4))
    for ax,profile in zip(axes,profiles):
        for policy in POLICIES:
            g=pv[(pv.scenario==profile)&(pv.strategy==policy)].sort_values('date')
            ax.plot(g.date,g.hhi,color=colors[policy],lw=1,label=policy)
        ax.axhline(config['risk_limits']['hhi'],color='#555',ls='--',lw=.8)
        ax.set(title=profile.replace('_',' ').title(),ylabel='Equity-sector HHI',xlabel='Date',ylim=(0,1.03))
        ax.tick_params(axis='x',rotation=30)
    axes[-1].legend(fontsize=7)
    fig.suptitle('Figure 2. Sector concentration and the configured limit',y=1.02)
    save(fig,'figure_2_sector_hhi','HHI excludes cash; undefined before the first purchase. The dashed line is the fixed 0.25 threshold. Policy changes do not imply holdings have corrected.')
    fig,axes=plt.subplots(1,3,figsize=(12,3.4))
    for ax,profile in zip(axes,profiles):
        for policy in POLICIES:
            g=pv[(pv.scenario==profile)&(pv.strategy==policy)].sort_values('date')
            wealth=(1+g['return']).cumprod().to_numpy()
            peak=np.maximum.accumulate(np.r_[1.,wealth])[1:]
            ax.plot(g.date,100*(wealth/peak-1),color=colors[policy],label=policy,lw=1.1)
        ax.set(title=profile.replace('_',' ').title(),ylabel='Time-weighted drawdown (%)',xlabel='Date')
        ax.tick_params(axis='x',rotation=30)
    axes[-1].legend(fontsize=7)
    fig.suptitle('Figure 3. Drawdown after removing external contributions',y=1.02)
    save(fig,'figure_3_drawdown','Daily time-weighted wealth, including the initial wealth peak. Losses are negative; external transfers are removed from return calculations.')
    fig,axes=plt.subplots(1,2,figsize=(9,3.8))
    x=np.arange(4)
    means=primary.groupby('strategy').mean(numeric_only=True).reindex(POLICIES)
    axes[0].bar(x,means.affordability_violation_rate*100,color=[colors[a] for a in POLICIES])
    axes[1].bar(x,means.mean_overspend,color=[colors[a] for a in POLICIES])
    for ax in axes:
        ax.set_xticks(x,POLICIES,rotation=25,ha='right')
    axes[0].set(ylabel='Decisions exceeding household buffer (%)',title='Violation frequency')
    axes[1].set(ylabel='Mean overspend per monthly decision (INR)',title='Violation magnitude')
    fig.suptitle('Figure 4. Proposed-purchase affordability violations')
    save(fig,'figure_4_affordability','Equal-profile means in the primary window. Overspend is proposed notional beyond monthly household capacity, measured separately from brokerage execution feasibility.')
    fig,axes=plt.subplots(2,1,figsize=(10,5.5),sharex=True)
    profile='medium_moderate'
    for policy in ['No Feedback','Full IntelliVest']:
        g=pv[(pv.scenario==profile)&(pv.strategy==policy)].sort_values('date')
        axes[0].plot(g.date,g.hhi,color=colors[policy],label=policy,lw=1.2)
    g=pv[(pv.scenario==profile)&(pv.strategy=='Full IntelliVest')].sort_values('date')
    flags=g[g.hhi_breach]
    axes[0].scatter(flags.date,np.full(len(flags),.98),s=4,color='#A44',label='HHI breach observation')
    axes[0].axhline(.25,color='#555',ls='--',lw=.8)
    changes=p[(p.window=='primary_2022_2025')&(p.scenario==profile)]
    axes[0].scatter(changes.date,np.full(len(changes),.93),marker='v',s=18,color='#222',label='Effective policy change')
    decisions=d[(d.window=='primary_2022_2025')&(d.scenario==profile)&(d.strategy=='Full IntelliVest')]
    changed=decisions[decisions.direct_feedback_change]
    axes[0].scatter(changed.date,np.full(len(changed),.88),marker='*',s=35,color='#D28D22',label='Directly modified proposal')
    axes[0].set(ylabel='Equity-sector HHI',ylim=(0,1.04),title='Figure 5. Feedback observations and decisions — medium/moderate')
    axes[0].legend(fontsize=7,loc='center right')
    axes[1].step(g.date,g.policy_multiplier,where='post',color=colors['Full IntelliVest'],label='Capacity multiplier')
    blocked=g.policy_blocked.map(lambda x:len(json.loads(x)))
    axes[1].step(g.date,blocked,where='post',color='#7B5AA6',label='Blocked-sector count')
    axes[1].set(ylabel='Policy state',xlabel='Date',ylim=(-.05,1.15));axes[1].legend(fontsize=8)
    save(fig,'figure_5_feedback_response','Markers distinguish breached observations, effective policy changes and proposals changed against the same-state fixed-policy counterfactual. Suppression of future purchases is not a corrective sale.')
    fig,ax=plt.subplots(figsize=(7,4.4))
    for policy in POLICIES:
        g=primary[primary.strategy==policy]
        ax.scatter(g.annualized_volatility*100,g.annualized_return*100,color=colors[policy],s=35,alpha=.8,label=policy)
    ax.set(xlabel='Realized annualized volatility (%)',ylabel='Time-weighted annualized return (%)',
           title='Figure 6. Risk and return across nine synthetic profiles')
    ax.legend(fontsize=8)
    save(fig,'figure_6_risk_return','Each point is a profile-policy replay on the same market window. Profiles are deterministic design scenarios, not independent sampled investors; no efficacy frontier is inferred.')
    (figdir/'CAPTIONS.md').write_text('\n\n'.join(captions)+'\n')
    primary_c=contrasts[contrasts.window=='primary_2022_2025']
    contrast_table=primary_c.groupby('contrast')[[m+'_difference' for m in ['affordability_violation_rate','mean_hhi','hhi_breach_sessions','cvar95','maximum_drawdown','annualized_return']]].mean().reset_index()
    ci_table=primary_c[['scenario','contrast','annualized_arithmetic_mean_return_difference','conditional_ci95_low','conditional_ci95_high']]
    ci_table.to_csv(out/'primary_uncertainty.csv',index=False)
    ablation=pd.read_csv(out/'momentum_ablation.csv')
    ablation=ablation.merge(primary[primary.strategy=='Full IntelliVest'][['scenario','annualized_return','maximum_drawdown','annualized_volatility','cvar95','turnover','mean_hhi','strong_negative_selection_rate']],on='scenario',suffixes=('_without','_with'))
    for metric in ['annualized_return','maximum_drawdown','annualized_volatility','cvar95','turnover','mean_hhi','strong_negative_selection_rate']:
        ablation[metric+'_with_minus_without']=ablation[metric+'_with']-ablation[metric+'_without']
    ablation.to_csv(out/'momentum_paired_differences.csv',index=False)
    stress_path=out/'feedback_stress.csv'
    stress=pd.read_csv(stress_path) if stress_path.exists() else pd.DataFrame()
    if len(stress):
        sv=pd.read_csv(out/'valuations.csv',parse_dates=['date'])
        sv=sv[sv.kind=='feedback_stress']
        sd=pd.read_csv(out/'decisions.csv',parse_dates=['date'])
        sd=sd[(sd.kind=='feedback_stress')&(sd.strategy=='Full IntelliVest')]
        fig,axes=plt.subplots(2,3,figsize=(12,5.5),sharex=True)
        for col,profile in enumerate(profiles):
            for policy in ['No Feedback','Full IntelliVest']:
                g=sv[(sv.strategy==policy)&(sv.scenario==profile)].sort_values('date')
                axes[0,col].plot(g.date,g.hhi,label=policy,color=colors[policy],lw=1)
                axes[1,col].step(g.date,g.policy_multiplier,label=policy,color=colors[policy],where='post')
            modified=sd[(sd.scenario==profile)&sd.direct_feedback_change]
            axes[0,col].scatter(modified.date,np.full(len(modified),.96),marker='*',s=35,color='#D28D22',label='Direct modified proposal')
            axes[0,col].axhline(.25,color='#555',ls='--',lw=.8)
            axes[0,col].set(ylabel='Equity-sector HHI',title=profile.replace('_',' ').title(),ylim=(0,1.05))
            axes[1,col].set(ylabel='Capacity multiplier',xlabel='Date',ylim=(0,1.05))
            axes[1,col].tick_params(axis='x',rotation=30)
        axes[0,-1].legend(fontsize=7)
        axes[1,-1].legend(fontsize=7)
        fig.suptitle('Supplementary Figure 7. Concentrated-start mechanism stress',y=1.02)
        save(fig,'figure_7_feedback_stress','All three targeted concentrated-start profiles, selected with pre-start volatility only. Stars identify changed proposals; none occurred in the low/conservative or medium/moderate profiles. This mechanism probe is supplementary and cannot replace the principal null result.')
        (figdir/'CAPTIONS.md').write_text('\n\n'.join(captions)+'\n')
    full=primary[primary.strategy=='Full IntelliVest'].set_index('scenario')
    risk=primary[primary.strategy=='Risk Only'].set_index('scenario')
    affordable=primary[primary.strategy=='Affordability Only'].set_index('scenario')
    no=primary[primary.strategy=='No Feedback'].set_index('scenario')
    fvsn=pd.read_csv(out/'feedback_decision_comparison.csv')
    fvsn=fvsn[fvsn.window=='primary_2022_2025']
    rq1=(full.affordability_violation_rate-risk.affordability_violation_rate).mean()
    rq2=(full.cvar95-affordable.cvar95).mean()
    rq2h=(full.mean_hhi-affordable.mean_hhi).mean()
    rq3=(full.hhi_breach_sessions-no.hhi_breach_sessions).mean()
    changed_count=int(full.direct_feedback_changed_decisions.sum())
    compact=primary[['scenario','strategy','annualized_return','cvar95','mean_hhi','hhi_breach_sessions','affordability_violation_rate','surplus_utilization']]
    readiness='2. Exploratory historical results available with important limitations.'
    stress_text='No secondary concentrated-start stress was executed in this run.'
    if len(stress):
        stress_full=stress[stress.strategy=='Full IntelliVest']
        stress_no=stress[stress.strategy=='No Feedback'].set_index('scenario')
        stress_delta=(stress_full.set_index('scenario').hhi_breach_sessions-stress_no.hhi_breach_sessions).mean()
        stress_text=f'''After the initial primary null decision effect was observed, we added and explicitly labelled a mechanism stress, without replacing the primary comparison. The starting portfolio targeted 90% of the same INR 100,000 wealth to the stock with the largest pre-start 252-return volatility, using only information before 2022. Three primary financial/risk profiles and all four policies were replayed; initial fixed constraints for the baselines were derived from the same pre-start portfolio. Full made {int(stress_full.direct_feedback_changed_decisions.sum())} decisions different from its same-state frozen-policy counterfactual and {int(stress_full.policy_adjustments.sum())} policy adjustments. The mean Full-minus-No Feedback HHI-breach-session difference was {stress_delta:.2f}. This targeted exposure stress was a diagnostic mechanism probe, not confirmatory evidence selected independently of the initial null finding. It did not alter the primary result. Supplementary Figure 7 and feedback_stress.csv preserve its outcomes.\n\n{markdown(stress[['scenario','strategy','annualized_return','cvar95','mean_hhi','hhi_breach_sessions','policy_adjustments','direct_feedback_changed_decisions']])}'''
    text=f'''# IntelliVest comparative historical study: conference results draft

Evidence classification: **{readiness}** This draft reports executed simulations; it does not establish market-wide superiority.

## 1. Experimental Setup

We executed {len(s)} principal policy/profile/window replays, nine momentum ablations, 24 transaction-cost sensitivity replays and {len(stress)} separately labelled concentrated-start mechanism-stress replays. The primary comparison covered complete calendar years 2022–2025, selected before strategy simulation. First-session monthly decisions used completed historical information and next-session closing-price execution. Portfolio valuation and monitoring were daily. Purchases incurred 10 bp commission and 5 bp adverse slippage. No leverage, shorting or fractional purchases were allowed. Each principal account started with INR 100,000 in cash and no holdings. The replay code operated on isolated CSV data and in-memory portfolios; server-enforced read-only database access was confined to the market audit. Mathematical and accounting checks were executed; unrelated application and browser tests were not run.

## 2. Historical Dataset

The legacy database contained 50 securities and 61,850 observations from 2021-10-19 through 2026-10-19. Its schema lacked source and ingestion fields. Fresh Yahoo Finance/yfinance acquisition produced 49 securities and 70,315 observations; TATAMOTORS was not silently remapped. NSE annual spot checks corroborated nominal prices and dates only on sampled sessions. After identity/corporate-action exclusions, the admitted dataset contained {config['dataset']['securities']} securities and {config['dataset']['observations']:,} observations from {config['dataset']['range'][0]} through {config['dataset']['range'][1]}. Exact exclusions, disagreement rows, raw files and hashes appear in the audit. We did not treat plausible legacy prices as proof of authenticity. Historical indicator returns used adjusted closes consistently. Execution used reconstructed nominal prices and explicit split/dividend accounting. Vendor adjustments are revised historical data rather than archived point-in-time vintages. This was a restricted surviving-universe study; historical index membership and a complete delisting universe were unavailable.

## 3. Investor Scenarios

Nine synthetic scenarios crossed low, medium and high surplus with conservative, moderate and aggressive tiers. These profiles did not come from investor surveys. Monthly income/mandatory expenses/reserve were INR 45,000/30,000/10,000; 100,000/50,000/30,000; and 250,000/90,000/60,000, yielding buffers of INR 5,000, 20,000 and 100,000. All policies received identical monthly transfers. The implemented application subtracts reserve from each monthly surplus and excludes discretionary expenses from the buffer calculation; the replay preserved these semantics. Starting brokerage savings were distinct from the protected household reserve.

## 4. Baseline Configurations

Affordability Only retained household capacity, the common tier-specific stock ranking and whole-share sizing, but removed portfolio exposure ordering and adaptive restrictions. Risk Only retained portfolio exposure ordering and executable brokerage-cash limits, but sized from brokerage cash rather than household capacity. No Feedback retained affordability and ordinary exposure-aware selection with an initial fixed unrestricted policy. Full IntelliVest additionally applied the implemented dominant-sector blocks and .5/.25 capacity multipliers after breaches. All configurations excluded held stocks and used at most three distinct sectors per batch. The application has no independent hard pretrade HHI eligibility gate; this absence limits the interpretation of No Feedback as a risk-constrained baseline. No extra gate was invented. Detailed factor definitions are in SPECIFICATION.md.

## 5. Evaluation Metrics

Returns were daily time-weighted returns with external transfers removed. Risk was evaluated with sample volatility, linearly interpolated historical VaR95 and inclusive-tail CVaR95, equity-only sector HHI and time-weighted maximum drawdown. The implemented breach parametric VaR was 1.645 times trailing 30-session volatility; historical estimates used 252 aligned returns. Sharpe used a 4% annual risk-free rate and 252 sessions. Proposed household overspend was separated from actual brokerage execution. Turnover was purchase notional divided by average equity, without annualization. Reported mean outcomes gave equal weight to synthetic profiles. Undefined metrics were NA. Formulas, units, censoring and aggregation rules are specified in SPECIFICATION.md. Realized losses were kept separate from in-sample risk estimates.

### Table 1. Principal comparison

Equal-profile means for 2022–2025, except maximum overspend, which is the maximum across all profiles. Rates and returns are fractions, money is INR, durations are trading sessions. Feedback response time is conditional on an observed directly modified recommendation; missing responses are censored and cannot be interpreted as immediate responses. Cash earned zero interest while the Sharpe benchmark was 4%; very cash-heavy profiles can therefore have strongly negative Sharpe ratios even with small positive nominal gains.

{comparison_text}

## 6. Results for RQ1: Affordability

Full minus Risk Only mean proposed-violation rate was {rq1:.6f}. Full violation rate was {full.affordability_violation_rate.mean():.6f}, versus {risk.affordability_violation_rate.mean():.6f} for Risk Only. Mean overspend per monthly decision was INR {full.mean_overspend.mean():.2f} and INR {risk.mean_overspend.mean():.2f}, respectively. The maximum Risk Only proposal excess was INR {risk.max_overspend.max():.2f}. This comparison assessed realistic household capacity even when accumulated brokerage savings allowed an order to execute. H1 is {'supported within these controlled scenarios' if rq1<0 else 'unsupported by a lower observed violation rate'}. This is partly a mechanical compliance result of the gate, not evidence of predictive stock-selection skill. Figure 4 reports frequency and magnitude.

## 7. Results for RQ2: Portfolio Risk Control

Full minus Affordability Only mean daily CVaR95 difference was {rq2:.6f}, mean HHI difference was {rq2h:.6f}, and maximum-drawdown difference was {(full.maximum_drawdown-affordable.maximum_drawdown).mean():.6f}. Mean HHI-breach-session difference was {(full.hhi_breach_sessions-affordable.hhi_breach_sessions).mean():.2f}. H2 must be evaluated component by component; these signs do not justify a blanket risk or return superiority claim. Exposure ordering and feedback jointly differ in this contrast. Figures 2 and 3 show concentration and drawdown trajectories.

## 8. Results for RQ3: Closed-Loop Feedback

Full produced {int(full.policy_adjustments.sum())} effective policy adjustments and {changed_count} monthly decisions different from its same-state fixed-policy counterfactual across the nine primary profiles. Full and No Feedback differed on {int(fvsn.different_decision.sum())} of {len(fvsn)} paired monthly decisions, including accumulated path effects. Mean HHI-breach-session difference was {rq3:.2f}. Among observed breach episodes, {int(full.feedback_responses.sum())} received a directly modified proposal and {int(full.feedback_unanswered.sum())} had no observed such response. Mean conditional response latency was {full.feedback_response_sessions.mean():.2f} sessions; it omits censored cases and is not an unconditional improvement estimate. Policy changes, modified proposals and actual holdings correction were measured separately. H3 has {'demonstrated decision responsiveness' if changed_count else 'no demonstrated decision effect'}; persistence outcomes {'decreased on average in these profiles' if rq3<0 else 'did not decrease on average in these profiles'}. The buy-only mechanism did not execute corrective sales. Figure 5 shows the distinct events.

### Supplementary mechanism stress

{stress_text}

## 9. Results for RQ4: Investment Performance Trade-offs

Table 1 reports all four policies without removing unfavorable outcomes. Figure 1 distinguishes account equity from supplied capital; Figure 6 compares time-weighted annualized return and realized volatility. Full annualized return averaged {full.annualized_return.mean():.6f}, versus {risk.annualized_return.mean():.6f} for Risk Only, {affordable.annualized_return.mean():.6f} for Affordability Only and {no.annualized_return.mean():.6f} for No Feedback. Differences in cash exposure, stock eligibility exhaustion and invested capital accompany these outcomes. Lower volatility is not automatically better investment performance. Cost sensitivity and the realized return/cost/cash columns are retained in the machine-readable outputs.

## 10. RQ5 and Momentum Robustness

All nine cross-factor profiles were replayed in fixed 2022–2023, 2024–2025 and 2026 YTD windows in addition to the primary window. `robustness_subgroups.csv` preserves every profile/window/policy cell; overlapping windows do not provide independent replications. The actual implemented momentum ranking was ablated by zeroing only its tier penalty coefficients. `momentum_paired_differences.csv` reports paired returns, drawdown, volatility, CVaR, turnover, HHI and strong-negative-momentum selection frequency. A descriptive mean with-minus-without annualized-return difference was {ablation.annualized_return_with_minus_without.mean():.6f}; it is not a parameter-tuned efficacy result.

## 11. Statistical Interpretation

We calculated matched profile/window differences and paired circular moving-block bootstrap intervals for annualized arithmetic daily-mean-return differences (20-session blocks, 2,000 draws, seed 20261023). Shared dates were resampled jointly across policies. These conditional time-series intervals are not intervals for a population of investors or a universe of markets. Scenarios were not treated as random samples and daily observations were not subjected to independent-observation t-tests. No inferential p-values or claims of statistical superiority were produced. `primary_uncertainty.csv` and `paired_comparisons.csv` retain each conditional interval and descriptive paired difference.

### Table 2. Mean paired differences (Full minus baseline)

{markdown(contrast_table)}

## 12. Threats to Validity

Current surviving securities and current sector labels induce selection bias; delisted names and historical membership are absent. Exchange price corroboration is sparse and does not independently certify every dividend-adjusted observation. Some complex corporate actions were excluded rather than approximated. Whole-share eligibility, absence of repeat purchases of held stocks and a maximum of three sectors per batch can exhaust eligible candidates and create cash-heavy portfolios. Initial purchase concentration can itself exceed HHI .25. High-surplus and low-surplus outcomes are conditional on the same INR 100,000 starting account. The initial empty portfolio makes the fixed policy in No Feedback unrestricted; no absent HHI gate was invented.

## 13. Limitations

Dividend availability was approximated on ex-date rather than unknown payment dates. Split reconstruction uses the downloaded horizon and revised vendor prices; there were no contemporaneous data vintages. Cash earned no interest. Costs were proportional assumptions, not a complete Indian tax/stamp-duty schedule. No investor acceptance behavior, market impact, forced rebalancing or predictive calibration was modeled. Feedback monitoring was scheduled daily, whereas the application evaluates on requests. Results do not prove that VaR estimates forecast losses accurately. Ending HHI episodes were right-censored. Averaging conditional response times omits nonresponses; their counts remain explicit. Conditional bootstrap intervals and overlapping calendar windows cannot establish general effectiveness.

## 14. Conclusion Supported by Results

The executed pipeline distinguished affordability compliance, portfolio concentration, realized investment performance and feedback decision changes. H1 was {'supported for the defined scenarios' if rq1<0 else 'not supported by the measured comparison'}. Feedback {'changed subsequent proposals' if changed_count else 'did not demonstrate changed proposals'}, while persistent portfolio-breach outcomes required separate evaluation. H2 and H3 were not collapsed into an unconditional superiority statement. H4 was treated as a trade-off question, with all measured policy outcomes retained. The evidence supports a reproducible exploratory restricted-universe comparison, not a publication-ready market-wide claim of superior advisory performance. Further validation requires complete action-aware security histories, broader point-in-time eligibility and independent out-of-sample market periods.

## Scenario outcomes

{markdown(compact)}

## Figures

'''+'\n\n'.join(captions)+'\n'
    text=text.replace('nan sessions; it omits censored cases', 'unobserved (no directly modified proposal); conditional latency omits censored cases')
    text=text.replace('H2 must be evaluated component by component;', 'H2 received support for concentration compliance but not for lower realized CVaR or drawdown in the primary profile means;')
    text=text.replace('H3 has no demonstrated decision effect;', 'H3 was unsupported in the primary empty-account comparisons: no decision effect was demonstrated;')
    text=text.replace('Feedback did not demonstrate changed proposals,', 'Feedback did not demonstrate changed proposals in the primary empty-account comparisons,')
    text=text.replace('H4 was treated as a trade-off question', 'RQ4 was treated as a trade-off question')
    text=text.replace('The fixed monthly schedule replaces UI reconsideration', 'The fixed monthly schedule replaces UI reconsideration')
    # Explicitly state the live-intent versus simulated-trade distinction.
    text=text.replace('No leverage, shorting or fractional purchases were allowed.', 'No leverage, shorting or fractional purchases were allowed. The live acceptance endpoint records intent only; automatic investor follow-through was a research assumption, not existing live trade execution. Simulated fills including costs respected the saved batch budget; live intraday freshness/evidence-hash rejection was replaced by the documented delayed-fill convention.')
    (out/'CONFERENCE_RESULTS_DRAFT.md').write_text(text)
    (out.parent/'CONFERENCE_RESULTS_DRAFT.md').write_text(f'Canonical executed run: `{out.name}`.\n\n'+text)
    (out/'RESULTS_SUMMARY.md').write_text(f'# Executed research results\n\n{readiness}\n\n'+comparison_text+f'\n\nRQ1 Full–Risk Only violation-rate difference: {rq1:.6f}.\nRQ2 Full–Affordability Only CVaR difference: {rq2:.6f}; HHI difference: {rq2h:.6f}.\nRQ3 Full–No Feedback HHI-breach sessions difference: {rq3:.2f}; {changed_count} direct feedback decision changes.\n\nSee CONFERENCE_RESULTS_DRAFT.md for interpretations and limitations.\n')


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('out',type=Path)
    generate(parser.parse_args().out)
