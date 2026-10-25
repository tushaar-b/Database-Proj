"""Fixed scalarizations, observed Pareto dominance, paired and stratified effects."""
import json
import numpy as np,pandas as pd
from research.phase10.common import OUT,P9
from research.diagnostics.metrics import block_interval

def dominance(values,tol=1e-8):
    x=np.asarray(values,float);dominates=(x[:,None,:]>=x[None,:,:]-tol).all(axis=2)&(x[:,None,:]>x[None,:,:]+tol).any(axis=2)
    return ~dominates.any(axis=0),dominates.sum(axis=0)

def main():
    protocol=json.loads((OUT/'PROTOCOL.json').read_text());r=pd.read_csv(OUT/'portfolio_allocations.csv');states=pd.read_csv(OUT/'matched_states.csv')
    r['solver_reported_status']=r.solver_status
    certified=r.solver_status=='optimal_full_guard';objective=np.where(r.reference_objective=='utility',r.U,r.cost)
    consistent=np.isclose(objective,r.linear_objective_bound,rtol=1e-7,atol=1e-5)
    audit=r.loc[certified,['state_id','mode','method','solver_status','gap','linear_objective_bound']].copy();audit['recomputed_objective']=objective[certified];audit['difference']=audit.recomputed_objective-audit.linear_objective_bound;audit['bound_reconciles']=consistent[certified];audit['rtol']=1e-7;audit['atol_INR']=1e-5;audit.to_csv(OUT/'solver_certification_audit.csv',index=False)
    r.loc[certified&~consistent,'solver_status']='solver_reported_optimal_bound_discrepancy'
    r.to_csv(OUT/'portfolio_allocations_audited.csv',index=False)
    r['linear_MILP_gap']=r.gap;r['certified_full_guard_gap']=np.where(r.solver_status=='optimal_full_guard',r.gap,np.nan);r['observed_nondominated_UD']=False;r['observed_nondominated_UDB']=False;r['dominating_candidates']=np.nan;r['frontier_eligible']=r.valid&r.HHI.notna()&((~r.family.str.startswith('REF'))|(r.purchase&r.target_valid))
    comparisons=[];preferences=[]
    for (ident,mode),g in r.groupby(['state_id','mode'],sort=False):
        eligible=g[g.frontier_eligible];x=eligible[['U_norm','D','budget_fill']].to_numpy()
        for columns,label in [([0,1],'UD'),([0,1,2],'UDB')]:
            nd,counts=dominance(x[:,columns],protocol['dominance_tolerance']);r.loc[eligible.index,'observed_nondominated_'+label]=nd
            if label=='UDB':r.loc[eligible.index,'dominating_candidates']=counts
        v=g[g.method=='V3'].iloc[0];gr=g[g.method=='GREEDY'].iloc[0]
        ref=eligible[eligible.family.str.startswith('REF')];nearH=ref[abs(ref.HHI-v.HHI)<=protocol['similar_HHI_tolerance']];nearU=ref[abs(ref.U_norm-v.U_norm)<=protocol['similar_utility_tolerance']]
        dominates_greedy=bool(gr.U_norm>=v.U_norm-1e-8 and gr.D>=v.D-1e-8 and gr.budget_fill>=v.budget_fill-1e-8 and (gr.U_norm>v.U_norm+1e-8 or gr.D>v.D+1e-8 or gr.budget_fill>v.budget_fill+1e-8))
        comparisons.append({'state_id':ident,'scenario':v.scenario,'date':v.date,'mode':mode,'V3_minus_greedy_U_norm':v.U_norm-gr.U_norm,'V3_minus_greedy_HHI':v.HHI-gr.HHI,'V3_minus_greedy_budget_fill':v.budget_fill-gr.budget_fill,'greedy_dominates_V3_UDB':dominates_greedy,'similar_HHI_reference_count':len(nearH),'max_reference_U_at_similar_HHI_minus_V3':nearH.U_norm.max()-v.U_norm if len(nearH) else np.nan,'similar_utility_reference_count':len(nearU),'V3_HHI_minus_min_reference_HHI_at_similar_utility':v.HHI-nearU.HHI.min() if len(nearU) else np.nan})
        for name,weights in protocol['joint_preferences'].items():
            scores=x@np.array(weights);best=float(np.max(scores)) if len(scores) else np.nan
            for row in g.itertuples():
                score=weights[0]*row.U_norm+weights[1]*(row.D if np.isfinite(row.D) else 0.)+weights[2]*row.budget_fill if (weights[1]==0 or np.isfinite(row.HHI)) else np.nan
                preferences.append({'state_id':ident,'scenario':row.scenario,'mode':mode,'method':row.method,'preference':name,'utility_weight':weights[0],'diversification_weight':weights[1],'budget_weight':weights[2],'objective':score,'best_observed':best,'regret_to_observed':best-score if np.isfinite(score) else np.nan,'observed_best':bool(np.isfinite(score) and score>=best-1e-8),'frontier_eligible':row.frontier_eligible})
    r.groupby(['mode','method']).agg(returned_baskets=('state_id','size'),rejected_internal_events=('rejected_proposals','sum'),invalid_returned_baskets=('valid',lambda x:int((~x).sum())),positive_purchase_outputs=('purchase','sum')).to_csv(OUT/'rejection_accounting.csv')
    r.to_csv(OUT/'pareto_comparisons.csv',index=False);pd.DataFrame(comparisons).to_csv(OUT/'paired_allocation_differences.csv',index=False);pd.DataFrame(preferences).to_csv(OUT/'objective_measurements.csv',index=False)
    r['positive_target_allocation']=r.purchase&r.target_valid
    summary=r.groupby(['mode','method'],dropna=False).agg(states=('state_id','size'),valid_rate=('valid','mean'),purchase_rate=('purchase','mean'),mean_U_norm=('U_norm','mean'),median_U_norm=('U_norm','median'),mean_budget_fill=('budget_fill','mean'),median_budget_fill=('budget_fill','median'),mean_HHI=('HHI','mean'),median_HHI=('HHI','median'),mean_purchase_positions=('purchase_positions','mean'),mean_post_positions=('post_positions','mean'),mean_max_sector_equity_weight=('max_sector_equity_weight','mean'),median_seconds=('seconds','median'),p95_seconds=('seconds',lambda x:x.quantile(.95)),ND_UD_rate=('observed_nondominated_UD','mean'),ND_UDB_rate=('observed_nondominated_UDB','mean'),reference_purchase_target_rate=('positive_target_allocation','mean')).reset_index();summary['certified_rate']=summary.apply(lambda row: float((r[(r['mode']==row['mode'])&(r.method==row.method)].solver_status=='optimal_full_guard').mean()),axis=1)
    summary.to_csv(OUT/'equal_constraint_summary.csv',index=False)
    distribution=r.groupby(['mode','method'])[['U_norm','budget_fill','HHI','seconds','purchase_positions']].quantile([0,.25,.5,.75,.95,1]).reset_index().rename(columns={'level_2':'quantile'});distribution.to_csv(OUT/'allocation_distributions.csv',index=False)
    pairrows=[]
    for (ident,mode),g in r.groupby(['state_id','mode']):
        v=g[g.method=='V3'].iloc[0]
        for method in ['GREEDY','REF_U','REF_B','V4']:
            b=g[g.method==method].iloc[0];qualified=not method.startswith('REF') or b.solver_status=='optimal_full_guard'
            pairrows.append({'state_id':ident,'scenario':v.scenario,'mode':mode,'contrast':'V3 - '+method,'qualified_comparison':qualified,**{c+'_difference':v[c]-b[c] if qualified else np.nan for c in ['U_norm','budget_fill','HHI','seconds']}})
    pairdf=pd.DataFrame(pairrows);pairdf.to_csv(OUT/'method_paired_differences.csv',index=False)
    pairdf.groupby(['mode','scenario','contrast'])[['U_norm_difference','budget_fill_difference','HHI_difference','seconds_difference']].agg(['count','mean','median','min','max']).to_csv(OUT/'per_profile_paired_distributions.csv')
    pd.DataFrame(preferences).groupby(['mode','preference','method']).agg(mean_objective=('objective','mean'),median_objective=('objective','median'),mean_observed_regret=('regret_to_observed','mean'),best_observed_fraction=('observed_best','mean')).to_csv(OUT/'objective_summary.csv')
    # No zero-filling of unavailable comparisons; sample coverage accompanies strata.
    merged=r.merge(states[['state_id','budget','existing_positions','initial_hhi','eligible_count','minimum_unit_price']],on='state_id',suffixes=('','_state'))
    candidates=pd.read_csv(OUT/'candidate_scores.csv');medianprice=candidates[candidates.eligible].groupby('state_id').price.median()*1.0005*1.001;merged['median_unit_to_budget']=merged.state_id.map(medianprice)/merged.budget
    merged['budget_stratum']=pd.cut(merged.budget,[0,2500,15000,np.inf],labels=['low_le2500','middle_2500_15000','high_gt15000'],include_lowest=True)
    merged['holdings_stratum']=pd.cut(merged.existing_positions,[-1,0,9,np.inf],labels=['empty','one_to_nine','ten_plus'])
    merged['concentration_stratum']=np.where(merged.initial_hhi.isna(),'empty',np.where(merged.initial_hhi>.25,'concentrated','diversified'))
    merged['affordability_stratum']=pd.cut(merged.median_unit_to_budget,[0,.1,.5,np.inf],labels=['low_price_relative_to_budget','middle_price_relative_to_budget','high_price_relative_to_budget'],include_lowest=True)
    merged['candidate_stratum']=pd.cut(merged.eligible_count,[0,20,35,np.inf],labels=['up_to_20','21_to_35','over_35'],include_lowest=True)
    strata=[]
    for group in ['budget_stratum','holdings_stratum','concentration_stratum','affordability_stratum','candidate_stratum','tier']:
        z=merged.groupby(['mode','method',group],observed=True).agg(states=('state_id','size'),valid_rate=('valid','mean'),purchase_rate=('purchase','mean'),mean_budget_fill=('budget_fill','mean'),mean_U_norm=('U_norm','mean'),mean_HHI=('HHI','mean'),median_seconds=('seconds','median'),ND_UDB_rate=('observed_nondominated_UDB','mean')).reset_index().rename(columns={group:'stratum'});z['grouping']=group;strata.append(z)
    pd.concat(strata,ignore_index=True).to_csv(OUT/'stratified_outcomes.csv',index=False)
    # Per-profile paired effects; monthly decisions are ordered within each profile.
    pairs=[];comp=pd.DataFrame(comparisons)
    for (mode,scenario),g in comp.groupby(['mode','scenario']):
        for metric in ['V3_minus_greedy_U_norm','V3_minus_greedy_HHI','V3_minus_greedy_budget_fill']:
            x=g.sort_values('date')[metric].to_numpy();# descriptive monthly circular blocks: 3 months, 2000 draws
            rng=np.random.default_rng(20261025);indices=(rng.integers(0,len(x),size=(2000,int(np.ceil(len(x)/3))))[:,:,None]+np.arange(3))%len(x);means=np.nanmean(x[indices.reshape(2000,-1)[:,:len(x)]],axis=1)
            pairs.append({'mode':mode,'scenario':scenario,'metric':metric,'states':len(g),'mean_difference':np.nanmean(x),'median_difference':np.nanmedian(x),'ci95_low':np.nanquantile(means,.025),'ci95_high':np.nanquantile(means,.975),'resampling':'3-month circular paired blocks','draws':2000,'seed':20261025})
    pd.DataFrame(pairs).to_csv(OUT/'statistical_comparisons.csv',index=False)
    # Synchronized monthly blocks preserve cross-profile market dependence.
    synchronized=[]
    for mode,g in comp.groupby('mode'):
        for metric in ['V3_minus_greedy_U_norm','V3_minus_greedy_HHI','V3_minus_greedy_budget_fill']:
            x=g.groupby('date')[metric].mean().sort_index().to_numpy();rng=np.random.default_rng(20261025);idx=(rng.integers(0,len(x),size=(2000,16))[:,:,None]+np.arange(3))%len(x);means=np.nanmean(x[idx.reshape(2000,48)],axis=1)
            synchronized.append({'mode':mode,'metric':metric,'mean_difference':np.mean(x),'median_monthly_mean':np.median(x),'ci95_low':np.quantile(means,.025),'ci95_high':np.quantile(means,.975),'months':len(x),'profiles':9,'block_months':3,'draws':2000,'seed':20261025,'interpretation':'conditional descriptive path interval; not synthetic-investor population inference'})
    pd.DataFrame(synchronized).to_csv(OUT/'synchronized_monthly_intervals.csv',index=False)
    # Complete case list, with reproducible illustrative selections of both signs.
    p9=pd.read_csv(P9/'same_state_allocation_quality.csv');v1=p9[p9.method=='V1'].copy();v1['state_id']=v1.scenario+'|'+v1.date
    v3=r[(r['mode']=='F3')&(r.method=='V3')].merge(v1[['state_id','budget_fill','quantity']],on='state_id',suffixes=('','_V1'));v3['V3_minus_V1_same_state_fill']=v3.budget_fill-v3.budget_fill_V1;v3.to_csv(OUT/'V1_V3_state_execution_comparison.csv',index=False)
    positive=v3.sort_values(['V3_minus_V1_same_state_fill','state_id'],ascending=[False,True]).iloc[0].state_id
    negatives=comp[(comp['mode']=='F3')&comp.greedy_dominates_V3_UDB];negative=negatives.sort_values(['V3_minus_greedy_U_norm','state_id']).iloc[0].state_id if len(negatives) else comp[comp['mode']=='F3'].sort_values('V3_minus_greedy_U_norm').iloc[0].state_id
    examples={'positive_extreme_vs_V1':positive,'negative_extreme_vs_greedy':negative,'prespecified_representative':'medium_moderate|2022-01-03'}
    (OUT/'CASE_SELECTION.json').write_text(json.dumps({'selection_rules':'largest positive same-state V3-V1 fill; largest utility deficit among greedy-dominated V3 states; first medium-moderate decision; all aggregate states retained','cases':examples},indent=2))
    print(summary.to_string(index=False));print('Cases',examples)
if __name__=='__main__':main()
