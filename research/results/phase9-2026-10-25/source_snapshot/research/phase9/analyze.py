"""Paired temporal uncertainty and exposure-aware descriptive analysis."""
import json
import numpy as np,pandas as pd
from research.phase9.freeze import OUT
from research.diagnostics.metrics import block_interval,exposure_series
from research.risk_metrics import tail_metrics

def main():
    s=pd.concat([pd.read_csv(OUT/'investor_level_performance.csv'),pd.read_csv(OUT/'etf_investor_performance.csv')],ignore_index=True)
    v=pd.concat([pd.read_csv(OUT/'portfolio_valuations.csv',parse_dates=['date']),pd.read_csv(OUT/'etf_accounts/valuations.csv',parse_dates=['date'])],ignore_index=True)
    t=pd.concat([pd.read_csv(OUT/'benchmark_trades.csv',parse_dates=['date']),pd.read_csv(OUT/'etf_accounts/trades.csv',parse_dates=['date'])],ignore_index=True)
    d=pd.concat([pd.read_csv(OUT/'allocation_decisions.csv'),pd.read_csv(OUT/'etf_accounts/decisions.csv')],ignore_index=True)
    s.to_csv(OUT/'all_investor_performance.csv',index=False);s.to_csv(OUT/'portfolio_risk.csv',index=False)
    primary=s[s.window=='primary_2022_2025'];summary=primary.groupby(['regime','policy']).mean(numeric_only=True)
    summary['feasible_but_unexecuted_total']=primary.groupby(['regime','policy']).feasible_but_unexecuted.sum()
    for key,g in primary.groupby(['regime','policy']):
        defined=g.loc[g.sharpe_valid,'sharpe'];summary.loc[key,'median_defined_sharpe']=defined.median();summary.loc[key,'mean_defined_sharpe']=defined.mean();summary.loc[key,'min_defined_sharpe']=defined.min();summary.loc[key,'max_defined_sharpe']=defined.max();summary.loc[key,'undefined_sharpe_count']=int((~g.sharpe_valid).sum());summary.loc[key,'low_volatility_sharpe_count']=int((g.sharpe_valid&(g.annualized_volatility<.01)).sum())
        z=d[(d.window=='primary_2022_2025')&(d.policy==key[1])];summary.loc[key,'decision_purchase_efficiency']=(z.executed_cost>0).mean();proposed=z.proposed_notional>0
        summary.loc[key,'proposed_basket_execution_rate']=(z.loc[proposed,'executed_cost']>0).mean();summary.loc[key,'proposed_baskets']=proposed.sum()
    summary.to_csv(OUT/'benchmark_summary.csv')
    d['authorized_budget_remaining']=d.authorized_batch_budget-d.executed_cost;d['affordable_count']=d.affordable_securities.map(lambda x:len(json.loads(x)))
    d['proposed_positions']=d.proposed_quantities.map(lambda x:len(json.loads(x)));d['executed_positions']=d.executed_quantities.map(lambda x:len(json.loads(x)))
    d.to_csv(OUT/'allocation_utilization.csv',index=False);d[d.feasible_single_share_opportunity&(d.executed_cost==0)].to_csv(OUT/'feasible_but_unexecuted.csv',index=False)
    cash=v[['window','scenario','policy','date','cash','stock_value','equity','contribution','authority_balance','external_grants','external_spent','expired_authority','revoked_authority']].copy();cash['unapproved_brokerage_cash']=cash.cash-cash.authority_balance;cash['protected_household_reserve_in_brokerage']=0;cash.to_csv(OUT/'cash_authority_accounting.csv',index=False)
    pairs=[('V3','GREEDY_M'),('V4','GREEDY_C'),('V3','EQUAL_M'),('V4','EQUAL_C'),('V4','V3'),('V3','NEUTRAL_M'),('V4','NEUTRAL_C'),('V3','SIP_M'),('V4','SIP_C'),('V3','ETF_M'),('V4','ETF_C'),('V3','RANK_TOPUP_M'),('V3','FEAS_NO_TOPUP_M'),('V3','V1')]
    paired=[];exposure=[];sleeves=[];synchronized=[]
    metrics=['annualized_return','authorized_budget_utilization','mean_invested_allocation','annualized_volatility','cvar95','maximum_drawdown','turnover','transaction_fees','mean_hhi']
    for w,sw in s.groupby('window'):
        vw=v[v.window==w];tw=t[t.window==w];series={}
        for (scenario,policy),g in vw.groupby(['scenario','policy']):
            z=exposure_series(g,tw[(tw.scenario==scenario)&(tw.policy==policy)]);series[scenario,policy]=z
            r=z.unit_exposure_return_gross.dropna();sleeves.append({'window':w,'scenario':scenario,'policy':policy,'positive_opening_sessions':len(r),'coverage':len(r)/len(z),'gross_sleeve_annual_arithmetic_return':r.mean()*252,'gross_sleeve_annual_volatility':r.std(ddof=1)*np.sqrt(252),**tail_metrics(r)})
        for a,b in pairs:
            diffs=[]
            for scenario,sg in sw.groupby('scenario'):
                if not {a,b}<=set(sg.policy):continue
                x=sg.set_index('policy');aa=series[scenario,a];bb=series[scenario,b];z=aa.merge(bb,on='date',suffixes=('_a','_b'))
                row={'window':w,'scenario':scenario,'contrast':a+' - '+b,**{m+'_difference':x.loc[a,m]-x.loc[b,m] for m in metrics},**block_interval(z.return_a,z.return_b)};paired.append(row);diffs.append(z.return_a.to_numpy()-z.return_b.to_numpy())
                positive=(z.opening_exposure_a>0)&(z.opening_exposure_b>0);matched=positive&(z.exposure_bin_a==z.exposure_bin_b)
                for label,mask in [('positive',positive),('same_date_same_bin',matched)]:
                    exposure.append({'window':w,'scenario':scenario,'contrast':a+' - '+b,'matching':label,'matched_sessions':int(mask.sum()),'coverage':mask.mean(),'gross_sleeve_cvar_a':tail_metrics(z.loc[mask,'unit_exposure_return_gross_a'])['cvar95'],'gross_sleeve_cvar_b':tail_metrics(z.loc[mask,'unit_exposure_return_gross_b'])['cvar95'],**block_interval(z.unit_exposure_return_gross_a,z.unit_exposure_return_gross_b,mask.to_numpy())})
            if diffs:
                average=np.mean(diffs,axis=0);synchronized.append({'window':w,'contrast':a+' - '+b,'profiles':len(diffs),'resampling_unit':'common-date circular 20-session blocks synchronized across all nine profiles',**block_interval(average,np.zeros(len(average)))})
    pd.DataFrame(paired).to_csv(OUT/'statistical_comparisons.csv',index=False);pd.DataFrame(exposure).to_csv(OUT/'exposure_matched_comparisons.csv',index=False);pd.DataFrame(sleeves).to_csv(OUT/'equity_sleeve_metrics.csv',index=False);pd.DataFrame(synchronized).to_csv(OUT/'synchronized_temporal_intervals.csv',index=False)
    s.groupby(['window','regime','policy']).annualized_return.agg(['mean','median','min','max']).to_csv(OUT/'window_robustness.csv')
    # Actual equal-weight deviation, reconstructed from quantities and prices by validation.
    print(summary[['annualized_return','annualized_volatility','cvar95','maximum_drawdown','authorized_budget_utilization','mean_cash_allocation','median_defined_sharpe']].to_string())
if __name__=='__main__':main()
