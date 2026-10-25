"""Additional diagnostic columns and interpretation; no financial results rewritten."""
import json
from pathlib import Path
import shutil
import numpy as np
import pandas as pd
from research.diagnostics.runner import sha
from research.phase8.experiments.runner import OUT,preserve
from research.phase8.analysis.report import generate,md


def finalize(out=OUT):
    protected=['investor_level_results.csv','policy_comparison.csv','risk_metrics.csv','trade_history.csv','statistical_comparisons.csv','ablation_results.csv']
    before={name:sha(out/name) for name in protected}
    d=pd.read_csv(out/'recommendation_decisions.csv',parse_dates=['date','execution_date'])
    t=pd.read_csv(out/'trade_history.csv',parse_dates=['date','decision_date'])
    keys=['window','scenario','policy','kind']
    data=pd.read_csv('research/data/2026-10-23/research_quotes.csv',parse_dates=['date'])
    prices=data.pivot(index='date',columns='ticker',values='nominal_close')
    lookup=t[t.side.isin(['BUY','SELL'])].groupby(keys+['decision_date'])[['fee','slippage_cost']].sum()
    rows=[]
    for r in d.to_dict('records'):
        selected=json.loads(r['eligible_securities']);budget=r['authorized_batch_budget']
        affordable=sum(prices.loc[r['date'],ticker]*1.0005*1.001<=budget+1e-8 for ticker in selected)
        why=[]
        if r['authority_before']<=0:why.append('no_approved_cash')
        if r['candidate_count']==0:why.append('no_valid_history_candidates')
        if r['held_exclusions']>0:why.append('existing_holding_restriction_present')
        if r['sector_exclusions']>0:why.append('sector_restriction_present')
        if r['eligible_count']==0:why.append('no_eligible_stock')
        elif affordable==0:why.append('no_cost_affordable_stock')
        elif not r['feasible_single_share_opportunity']:why.append('other_portfolio_risk_restriction')
        if r['executed_cost']<budget-1e-7:
            if r['proposed_notional']>0:why.append('whole_share_or_portfolio_guard_residual')
            if r['feasible_single_share_opportunity'] and r['proposed_notional']==0:why.append('no_order_due_to_construction_policy')
        if pd.notna(r.get('execution_cancel_reason')) and r['execution_cancel_reason']:why.append(str(r['execution_cancel_reason']))
        if r['proposed_notional']>0 and r['executed_cost']==0 and not r.get('execution_cancel_reason'):why.append('next_session_budget_or_cost_change')
        r['contributing_reasons']=json.dumps(why)
        r['price_only_affordable_count']=affordable
        r['approved_cash_at_signal']=min(r['brokerage_cash'],r['authority_before'])
        r['remaining_purchasing_authority']=r['authority_after_purchases'];r['remaining_brokerage_cash']=r['cash_after_purchases']
        r['authorized_budget_unused_after_execution']=max(0.,budget-r['executed_cost'])
        k=tuple(r[c] for c in keys)+(r['date'],)
        r['actual_transaction_fees']=float(lookup.loc[k,'fee']) if k in lookup.index else 0.
        r['actual_slippage_cost']=float(lookup.loc[k,'slippage_cost']) if k in lookup.index else 0.
        rows.append(r)
    d=pd.DataFrame(rows);d.to_csv(out/'capital_utilization.csv',index=False)
    d.to_csv(out/'recommendation_decisions.csv',index=False)
    reason_rows=[]
    primary=d[(d.kind=='principal')&(d.window=='primary_2022_2025')]
    for policy,g in primary.groupby('policy'):
        for reason,count in g.contributing_reasons.map(json.loads).explode().value_counts().items():
            reason_rows.append({'policy':policy,'constraint_or_reason':reason,'decision_count':int(count),
                                'interpretation':'overlapping verified constraint presence; not additive causal money attribution'})
    pd.DataFrame(reason_rows).to_csv(out/'unused_fund_reasons.csv',index=False)
    generate(out)
    s=pd.read_csv(out/'investor_level_results.csv')
    stress=s[s.kind=='concentrated_start'][['scenario','policy','annualized_return','cvar95','mean_hhi','hhi_breach_sessions','hhi_episodes_resolved','sell_trades','turnover','transaction_fees']]
    shock=s[s.kind=='household_deterioration'][['scenario','policy','revoked_authority','external_approved_grants','authorized_budget_utilization','annualized_return','mean_cash_allocation']]
    selling=s[s.kind=='corrective_selling'].groupby('policy')[['changed_recommendations','actual_trade_changed_decisions','hhi_breach_sessions','hhi_episodes_resolved','transaction_fees','turnover','annualized_return','cvar95']].mean().reset_index()
    update=f'''\n## Additional stress interpretation\n\nThe following concentrated-start cases had already been examined in previous phases. They are targeted exploratory mechanism probes, not new holdouts. Monthly purchase redirection remains identical to V4 in these cases. Corrective selling is a distinct additional action with explicit costs and recycling; all adverse outcomes remain visible. In the low/conservative stress, observed HHI-breach sessions fell from 988 to 148, while turnover and costs increased; the high/aggressive selling stress had lower return than the buy-only parent. This supports conditional actionability of the separate selling mechanism, not general superiority or a principal-redirection effect.\n\n{md(stress)}\n\nPrimary corrective-selling means (separate from V5):\n\n{md(selling)}\n\nIn the primary nine profiles, V5_SELL executed three sales across two monthly decisions. Its mean breach duration stayed equal to V4/V5 at 25.44444 sessions; resolved HHI-episode totals also stayed equal (12 observed episodes). Thus actual corrective transactions did not establish an incremental primary concentration-duration improvement.\n\nHousehold deterioration stresses used identical reduced contributions for all versions. January–March 2024 purchases were suspended and unused carry was revoked; no holdings were automatically liquidated due to reduced income. These scenarios do not include exogenous brokerage withdrawals; generic authority revocation is available and numerically tested, but no empirical withdrawal outcome is claimed.\n\n{md(shock)}\n'''
    results=out/'PHASE8_RESULTS.md';results.write_text(results.read_text()+update)
    conf=out/'PHASE8_CONFERENCE_DRAFT.md';conf.write_text(conf.read_text()+update.split('Household deterioration stresses')[0])
    # Keep classifications explicit: actionability in targeted sales cannot be
    # substituted for the unchanged principal purchase-redirection experiment.
    (out/'SECONDARY_FEEDBACK_INTERPRETATION.md').write_text('# Secondary corrective feedback\n\n'+update)
    assert all(sha(out/name)==digest for name,digest in before.items())
    sources=[Path('research/phase8/analysis/finalize.py'),Path('research/phase8/analysis/report.py')]
    for source in sources:
        dest=out/'postprocessing_source'/source;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
    (out/'POSTPROCESSING_MANIFEST.json').write_text(json.dumps({'financial_and_statistical_hashes_unchanged':before,
        'sources':{str(p):sha(p) for p in sources},'previous_files_preserved':preserve(out),
        'changes':'Enriched decision diagnostics, overlapping constraint-presence labels and explicit targeted-stress interpretation. No policy parameters, trades, valuations or financial results changed.'},indent=2)+'\n')
    print('Phase 8 interpretation finalized without financial/statistical changes',flush=True)


if __name__=='__main__':finalize()
