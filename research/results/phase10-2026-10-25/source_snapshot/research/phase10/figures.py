"""Nine publication figures from executed allocations, ledgers and timing measurements."""
from pathlib import Path
import json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
from research.phase10.common import OUT,P9,load_states
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none'})
D=OUT/'figures';D.mkdir(exist_ok=True);captions=[]
COL={'V1':'#7b8794','GREEDY':'#b36b38','V3':'#147d92','V4':'#7460a0','REF_U':'#576879','REF_B':'#7d8c46','REFERENCE':'#576879'}
def save(fig,name,caption):
    fig.tight_layout();fig.savefig(D/(name+'.png'),dpi=300,bbox_inches='tight');fig.savefig(D/(name+'.svg'),bbox_inches='tight');plt.close(fig);captions.append(f'**{name}.** {caption}')
def main():
    old=pd.read_csv(P9/'benchmark_summary.csv').set_index('policy');r=pd.read_csv(OUT/'pareto_comparisons.csv');runtime=pd.read_csv(OUT/'runtime_measurements.csv');examples=json.loads((OUT/'CASE_SELECTION.json').read_text())['cases'];states={s['id']:s for s in load_states()}
    names=['V1','GREEDY_M','V3','GREEDY_C','V4'];labels=['V1 (M)','Greedy (M)','V3 (M)','Greedy (C)','V4 (C)'];colors=[COL['V1'],COL['GREEDY'],COL['V3'],COL['GREEDY'],COL['V4']]
    fig,ax=plt.subplots(figsize=(8,4));ax.bar(labels,old.loc[names,'authorized_budget_utilization']*100,color=colors);ax.set(ylabel='Unique approved capital used (%)',title='Historical execution deployment | 2022–2025',ylim=(0,105));ax.grid(axis='y',alpha=.15)
    save(fig,'01_budget_utilization','Nine-profile means from reproduced frozen policies and preserved Phase 9 greedy paths. M=current month, C=accumulated authority. Phase 9 greedy allowed wide baskets; this path chart is separate from Phase 10 matched F3 signal comparisons.')
    fig,axes=plt.subplots(1,2,figsize=(11,4));axes[0].bar(labels,old.loc[names,'decision_purchase_efficiency']*100,color=colors);axes[0].set(ylabel='Monthly decisions producing purchases (%)',ylim=(0,105),title='Actual next-session purchases');axes[1].bar(labels,old.loc[names,'feasible_but_unexecuted_total'],color=colors);axes[1].set(ylabel='Signal-feasible decisions without a buy (count)',title='Non-execution despite one-share witness')
    for ax in axes:ax.tick_params(axis='x',rotation=25);ax.grid(axis='y',alpha=.15)
    save(fig,'02_execution_feasibility','432 decisions per strategy. The one-share witness is checked at signal time; some no-buy events result from next-session price/guard cancellations, so this is not a pure count of allocator-caused avoidable failures.')
    ids=[examples['prespecified_representative'],examples['positive_extreme_vs_V1'],examples['negative_extreme_vs_greedy']]
    fig,axes=plt.subplots(1,3,figsize=(14,4.4))
    for ax,ident in zip(axes,ids):
        g=r[(r.state_id==ident)&(r['mode']=='F3')&r.frontier_eligible];ref=g[g.family.str.startswith('REF')];ax.scatter(ref.HHI,ref.U_norm,label='Valid reference candidates',s=25,color='#919aa3',alpha=.8)
        frontier=g[g.observed_nondominated_UD].drop_duplicates(['HHI','U_norm']).sort_values('HHI');ax.plot(frontier.HHI,frontier.U_norm,color='#576879',lw=1,ls='--',label='Observed UD frontier')
        for method,marker in [('V3','*'),('GREEDY','^')]:
            x=g[g.method==method];ax.scatter(x.HHI,x.U_norm,s=110 if method=='V3' else 60,marker=marker,color=COL[method],label=method,zorder=5)
        ax.xaxis.set_major_locator(MaxNLocator(4))
        ax.tick_params(axis='x',labelsize=8)
        ax.set(xlabel='Post-trade equity-sector HHI (lower is better)',ylabel='Candidate utility / authorized budget',title=ident.replace('|','\n'));ax.grid(alpha=.15)
    axes[0].legend(fontsize=8);fig.suptitle('Observed utility–diversification frontiers | exact common F3 restrictions')
    save(fig,'03_observed_pareto_frontier','Each panel has one common historical input. Points are the prespecified epsilon-grid results plus frozen heuristics and no-trade baseline. Dashed lines join observed nondominated points only, not a certified global or continuous frontier. No feasible HHI is assigned to an empty portfolio. Positive and negative extremes are selected by disclosed rules; aggregate outcomes retain all 432 states.')
    fig,axes=plt.subplots(1,2,figsize=(11,4.3))
    for ax,ident in zip(axes,ids[:2]):
        g=r[(r.state_id==ident)&(r['mode']=='F3')&r.frontier_eligible]
        for family in ['REF_U','REF_B','GREEDY','V3']:
            x=g[g.family==family];ax.scatter(x.HHI,x.budget_fill*100,color=COL[family],label=family,s=75 if family=='V3' else 30,marker='*' if family=='V3' else 'o')
        ax.set(xlabel='Post-trade sector HHI',ylabel='Authorized batch budget filled (%)',title=ident.replace('|','\n'));ax.legend(fontsize=8);ax.grid(alpha=.15)
    save(fig,'04_utilization_diversification','Same-state allocation usage is distinct from historical unique-authority utilization. Different feasible points trade budget fill and post-trade concentration. Failed/target-infeasible reference fallbacks are omitted from the alternative set.')
    fig,axes=plt.subplots(1,3,figsize=(14,4.2))
    for ax,kind in zip(axes[:2],['historical_subset','synthetic_OFAT']):
        g=runtime[(runtime.kind==kind)&(runtime.factor=='candidate_count')]
        for method in ['GREEDY','V3','V4','REFERENCE']:
            by=g[g.method==method].groupby('candidate_count').seconds;med=by.median()*1000;hi=by.quantile(.95)*1000;ax.plot(med.index,med,marker='o',label=method,color=COL[method],ls='--' if method=='V4' else '-');ax.fill_between(med.index,med,hi,color=COL[method],alpha=.08)
        ax.set(xlabel='Eligible candidate subset size',ylabel='Median time (ms; log scale)',yscale='log',title='Historical subsets' if kind=='historical_subset' else 'Synthetic computation only');ax.grid(alpha=.15)
    axes[0].set_xticks([10,20,40]);axes[1].set_xticks([10,20,40,80,160]);axes[2].set_xticks([10,20,40,80,160])
    axes[1].text(.03,.97,'160 candidates: reference timeout9/9\nNo positive purchase returned',transform=axes[1].transAxes,fontsize=8,va='top',bbox={'facecolor':'white','alpha':.9,'edgecolor':'none'})
    memory=pd.read_csv(OUT/'memory_measurements.csv');memory=memory[(memory.kind=='synthetic_OFAT')&(memory.factor=='candidate_count')]
    for method in ['GREEDY','V3','V4','REFERENCE']:
        x=memory[memory.method==method].groupby('candidate_count').python_visible_peak_bytes.median()/1024;axes[2].plot(x.index,x,label=method,color=COL[method],marker='o',ls='--' if method=='V4' else '-')
    axes[2].set(xlabel='Synthetic candidate count',ylabel='Python-visible peak memory (KiB)',yscale='log',title='Separate instrumented memory calls');axes[0].legend(fontsize=8)
    save(fig,'05_runtime_scaling','F3 restrictions shared by all methods. Timings follow one warm-up, three repeats, no data fetching; shaded band is median-to-95th percentile. Historical matrices retain all 40 holdings even with smaller candidate subsets. Synthetic 80/160 cases are not market evidence. Integer reference has a 0.5s resource cap; quality/status must accompany latency. Memory excludes unobserved solver-native RSS.')
    ident=examples['prespecified_representative'];st=states[ident];g=r[(r.state_id==ident)&(r['mode']=='F3')&r.method.isin(['V3','GREEDY','REF_U'])];vectors={x.method:np.array(json.loads(x.quantities)) for x in g.itertuples()};ids_used=np.where(sum(vectors.values())>0)[0];fig,ax=plt.subplots(figsize=(10,4.5));x=np.arange(len(ids_used));width=.25
    for j,method in enumerate(['V3','GREEDY','REF_U']):ax.bar(x+(j-1)*width,vectors[method][ids_used]*st['p'][ids_used],width,label=method,color=COL[method])
    ax.set(xticks=x,xticklabels=[st['tickers'][i] for i in ids_used],ylabel='Signal-price purchased nominal value (INR)',title='Same historical input: '+ident.replace('|',' | '));ax.legend();ax.grid(axis='y',alpha=.15)
    save(fig,'06_allocation_comparison','Actual integer quantities at the first medium-moderate V3 decision. Prices, scores, holdings, approved budget and quantities are exported. Fees/slippage are additionally included in feasibility costs, while bars show nominal value. This is a signal allocation, not a separately executed investment path.')
    d=pd.read_csv(OUT/'v3_v4_differences.csv');d=d[d.kind=='primary'].sort_values('scenario');fig,axes=plt.subplots(1,2,figsize=(12,4.2));labels=d.scenario.str.replace('_',' ')
    for ax,col,title in zip(axes,['authorized_budget_utilization','mean_invested_allocation'],['V4 minus V3: approved utilization','V4 minus V3: average invested exposure']):ax.barh(labels,d[col]*100,color=COL['V4']);ax.set(xlabel='Percentage-point difference',title=title);ax.grid(axis='x',alpha=.15)
    save(fig,'07_V4_incremental_benefit','Nine paired historical profiles. V3/V4 use the same constructor and differ in monthly versus accumulated authority. Additional exposure and losses are reported alongside deployment; higher utilization alone does not select a preferred default.')
    stt=pd.read_csv(OUT/'statistical_comparisons.csv');stt=stt[stt['mode']=='F3'];fig,axes=plt.subplots(1,3,figsize=(14,4.4))
    for ax,metric,title in zip(axes,['V3_minus_greedy_U_norm','V3_minus_greedy_budget_fill','V3_minus_greedy_HHI'],['Normalized utility: V3 − greedy','Budget fill: V3 − greedy','Sector HHI: V3 − greedy']):
        g=stt[stt.metric==metric].sort_values('scenario');ax.errorbar(g.mean_difference*100,np.arange(len(g)),xerr=np.array([g.mean_difference-g.ci95_low,g.ci95_high-g.mean_difference])*100,fmt='o',color=COL['V3'],capsize=2);ax.axvline(0,color='grey',lw=.8);ax.set(yticks=np.arange(len(g)),yticklabels=g.scenario.str.replace('_',' '),xlabel='Difference × 100',title=title);ax.grid(axis='x',alpha=.15)
    save(fig,'08_per_investor_robustness','Each marker is a 48-decision paired mean. Bars are descriptive three-month circular block intervals, 2000 draws, seed20261025. Nine synthetic profiles share historical market paths; these are not population confidence intervals. Lower HHI is better; higher utility and fill are better.')
    fig,ax=plt.subplots(figsize=(8,4));f=r[(r['mode']=='F3')&r.method.isin(['V3','V4','GREEDY','REF_U','REF_B'])];n=f.groupby('method').valid.agg(['size','sum']);ax.bar(n.index,n['sum']/n['size']*100,color=[COL.get(m,'#576879') for m in n.index]);ax.set(ylabel='Returned portfolios passing full guard (%)',ylim=(0,110),title='Common-guard compliance | all 432 matched inputs')
    for j,row in enumerate(n.itertuples()):ax.text(j,101,f'{int(row.sum)}/{int(row.size)}',ha='center',fontsize=9)
    ax.grid(axis='y',alpha=.15)
    save(fig,'09_constraint_compliance','Includes valid no-trade fallbacks. Compliance is not purchase feasibility: solver outcomes, purchase rates and HHI-target failures are exported separately. Every returned allocation is independently checked for whole shares, cash, authority, costs, position caps, sector caps and lagged risk. Bootstrap and drift grandfathering remain explicit exceptions to universal concentration ceilings.')
    (D/'CAPTIONS.md').write_text('\n\n'.join(captions)+'\n');print('Saved nine PNG and nine SVG figures')
if __name__=='__main__':main()
