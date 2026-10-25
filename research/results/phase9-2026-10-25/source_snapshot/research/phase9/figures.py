"""Publication figures in PNG (300dpi) and editable SVG from executed evidence."""
from pathlib import Path
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from research.phase9.freeze import OUT
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','figure.dpi':120})
D=OUT/'figures';D.mkdir(exist_ok=True)
S=pd.read_csv(OUT/'benchmark_summary.csv').set_index('policy')
COLORS=['#7b8794','#526d82','#2b6f73','#e09b32','#6f58a2','#ba5b50','#738d45']
CAPTIONS=[]
def save(fig,name,caption):
    fig.tight_layout();fig.savefig(D/(name+'.png'),dpi=300,bbox_inches='tight');fig.savefig(D/(name+'.svg'),bbox_inches='tight');plt.close(fig);CAPTIONS.append(f'**{name}.** {caption}')
def panels(metric,title,ylabel,name):
    fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
    for ax,reg in zip(axes,['M','C']):
        names=(['V1','GREEDY_M','V3','MILP_M','EQUAL_M','SIP_M','ETF_M'] if reg=='M' else ['GREEDY_C','V4','MILP_C','EQUAL_C','SIP_C','ETF_C'])
        vals=S.loc[names,metric];ax.bar(names,vals*100,color=COLORS[:len(names)]);ax.set_title('Regime '+reg);ax.tick_params(axis='x',rotation=45);ax.set_ylabel(ylabel);ax.grid(axis='y',alpha=.15)
    fig.suptitle(title);return fig
save(panels('authorized_budget_utilization','Approved-capital utilization | 2022–2025','Unique approved authority used (%)',''), '01_capital_utilization','Mean of nine synthetic profile ratios. Each external grant enters the denominator once; regimes differ in expiry and carry-forward.')
save(panels('decision_purchase_efficiency','Decisions producing purchases | 2022–2025','Monthly decisions with executed purchases (%)',''),'02_feasible_purchase_efficiency','All 432 decisions per strategy, including decisions without affordable candidates. Basket-conditional execution rates and feasible non-execution counts are exported separately. Execution uses next-session closing prices.')
V=pd.concat([pd.read_csv(OUT/'portfolio_valuations.csv',parse_dates=['date']),pd.read_csv(OUT/'etf_accounts/valuations.csv',parse_dates=['date'])]);V=V[V.window=='primary_2022_2025']
fig,axes=plt.subplots(1,2,figsize=(11,4.3))
for ax,reg in zip(axes,['M','C']):
    names=['V3','GREEDY_M','EQUAL_M','SIP_M','ETF_M'] if reg=='M' else ['V4','GREEDY_C','EQUAL_C','SIP_C','ETF_C']
    for name,color in zip(names,COLORS):
        g=V[V.policy==name].copy();g['wealth']=g.groupby('scenario')['return'].transform(lambda r:(1+r).cumprod()*100);z=g.groupby('date').wealth.mean();ax.plot(z.index,z,label=name,color=color,lw=1.6)
    ax.xaxis.set_major_locator(mdates.YearLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.set_title('Regime '+reg);ax.set_ylabel('Mean profile TWR wealth (start = 100)');ax.legend(fontsize=8);ax.grid(alpha=.15)
fig.suptitle('Total portfolio performance, including zero-yield cash')
save(fig,'03_portfolio_performance','Mean normalized, contribution-adjusted wealth; this is not pooled account equity. NIFTYBEES is executable fund exposure. Daily NIFTY TRI data were unavailable and no price-index substitution was made.')
fig,ax=plt.subplots(figsize=(8,5))
for reg,marker in [('M','o'),('C','^')]:
    names=['V1','V3','GREEDY_M','EQUAL_M','SIP_M','ETF_M','MILP_M'] if reg=='M' else ['V4','GREEDY_C','EQUAL_C','SIP_C','ETF_C','MILP_C']
    for name,color in zip(names,COLORS):
        r=S.loc[name];ax.scatter(r.annualized_volatility*100,r.annualized_return*100,marker=marker,color=color,s=55);ax.annotate(name,(r.annualized_volatility*100,r.annualized_return*100),xytext=(3,4 if reg=='M' else -11),textcoords='offset points',fontsize=8)
ax.set(xlabel='Mean profile annualized volatility (%)',ylabel='Mean profile annualized geometric TWR (%)',title='Risk–return trade-off | circles M, triangles C');ax.grid(alpha=.15)
save(fig,'04_risk_return','Arithmetic means of investor-level annualized statistics, not an efficient frontier. Both market exposure and composition differ.')
fig,axes=plt.subplots(1,2,figsize=(11,4.3),sharey=True)
for ax,reg in zip(axes,['M','C']):
    names=['V1','V3','GREEDY_M','EQUAL_M','ETF_M'] if reg=='M' else ['V4','GREEDY_C','EQUAL_C','SIP_C','ETF_C']
    for name,color in zip(names,COLORS):
        g=V[V.policy==name].copy();g['drawdown']=g.groupby('scenario')['return'].transform(lambda r: (lambda w:w/np.maximum.accumulate(np.r_[1.,w])[1:]-1)((1+r).cumprod().to_numpy()))
        z=g.groupby('date').drawdown.mean();ax.plot(z.index,z*100,label=name,color=color)
    ax.xaxis.set_major_locator(mdates.YearLocator());ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.set(title='Regime '+reg,ylabel='Mean profile drawdown from prior peak (%)');ax.legend(fontsize=8);ax.grid(alpha=.15)
fig.suptitle('Contribution-adjusted portfolio drawdown')
save(fig,'05_drawdown','Mean of the nine individual TWR drawdown paths. Maximum of this mean path differs from mean individual maximum drawdown reported in the tables.')
fig,axes=plt.subplots(1,2,figsize=(11,4))
names=['V1','GREEDY_M','V3','EQUAL_M','GREEDY_C','V4','EQUAL_C']
axes[0].bar(names,S.loc[names,'mean_hhi'],color=COLORS);axes[0].axhline(.25,color='k',ls='--',lw=.8);axes[0].set(ylabel='Mean sector HHI, equity sleeve',title='Holdings-conditional concentration')
axes[1].bar(names,S.loc[names,'hhi_breach_frequency']*100,color=COLORS);axes[1].set(ylabel='Sessions above HHI 0.25 (%)',title='Frequency conditional on valid holdings')
for ax in axes:ax.tick_params(axis='x',rotation=45);ax.grid(axis='y',alpha=.15)
save(fig,'06_sector_concentration','ETF look-through HHI is unavailable and omitted. Grandfathering and empty-account bootstrap allow observed breaches; guards do not promise universal HHI below 0.25.')
R=pd.read_csv(OUT/'controlled_algorithm_runtimes.csv');fig,ax=plt.subplots(figsize=(8,4.5))
for name,color in zip(['V1','GREEDY_M','V3','V4','MILP_M'],COLORS):
    g=R[R.method==name].groupby('candidate_size').seconds;med=g.median()*1000;lo=g.quantile(.25)*1000;hi=g.quantile(.75)*1000
    ax.plot(med.index,med,marker='o',label=name,color=color);ax.fill_between(med.index,lo,hi,color=color,alpha=.12)
ax.set(xlabel='Historically available candidate subset size',ylabel='Allocation time (ms; logarithmic)',title='Controlled common-state runtime | median and IQR',yscale='log',xticks=[10,20,40]);ax.legend();ax.grid(alpha=.15)
save(fig,'07_algorithm_runtime','Six historical states, five repetitions per state, size and method. All use the same process and hardware; costs include feasibility witnesses and shared guard checks. Solver timings include setup. Warm caches and shared-machine load limit generalization.')
fig,axes=plt.subplots(1,3,figsize=(12,4))
names=['RANK_GUARD_M','FEAS_NO_TOPUP_M','RANK_TOPUP_M','V3','V4','NEUTRAL_M']
labels=['Rank + guards','Feasible, no top-up','Rank + top-up','V3','V4','Neutral M']
for ax,metric,title in zip(axes,['authorized_budget_utilization','annualized_return','cvar95'],['Approved utilization (%)','Annualized TWR (%)','Daily CVaR95 (%)']):
    ax.bar(labels,S.loc[names,metric]*100,color=COLORS[:len(names)]);ax.set_title(title);ax.tick_params(axis='x',rotation=65);ax.grid(axis='y',alpha=.15)
fig.suptitle('Construction ablations | common primary period')
save(fig,'08_ablation_results','Rank/feasibility and top-up arms use identical monthly authority and guards. V4 changes authority; neutral M changes scores and sizing preferences together. Effects interact and are not additive causal decompositions.')
fig,axes=plt.subplots(1,2,figsize=(11,4))
for ax,reg in zip(axes,['M','C']):
    names=['V1','V3','GREEDY_M','EQUAL_M','ETF_M'] if reg=='M' else ['V4','GREEDY_C','EQUAL_C','SIP_C','ETF_C']
    vals=[]
    for name in names:
        g=V[V.policy==name];vals.append([(g.stock_value/g.equity).mean(),(g.authority_balance/g.equity).mean(),((g.cash-g.authority_balance)/g.equity).mean()])
    a=np.array(vals)*100;bottom=np.zeros(len(names))
    for j,(label,color) in enumerate(zip(['Invested','Unused approved cash','Other brokerage cash'],['#2b6f73','#e09b32','#c8cfd5'])):ax.bar(names,a[:,j],bottom=bottom,label=label,color=color);bottom+=a[:,j]
    ax.set(title='Regime '+reg,ylabel='Mean daily account allocation (%)',ylim=(0,100));ax.tick_params(axis='x',rotation=45)
axes[1].legend(fontsize=8);fig.suptitle('Cash exposure and approval status')
save(fig,'09_cash_exposure','Unapproved brokerage cash is distinct from unused approved authority. Household reserves are outside brokerage. High cash allocation can coexist with near-complete use of approved authority.')
(D/'CAPTIONS.md').write_text('\n\n'.join(CAPTIONS)+'\n')
print('Saved nine figures in PNG and SVG')
