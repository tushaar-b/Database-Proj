"""Classify every effective policy transition against actual scheduled opportunities."""
import json
import numpy as np
import pandas as pd
from research.diagnostics.instrumentation import probe,basket,no_change_reason


def tuple_policy(value):
    obj=json.loads(value)
    return float(obj['multiplier']),tuple(obj['blocked_sectors'])


def trace_events(events,decisions,cache,investors,calendar):
    rows=[];opportunities=[]
    group_keys=['variant','window','scenario','strategy']
    for key,group in events.groupby(group_keys):
        group=group.sort_values('date').reset_index(drop=True)
        condition=np.ones(len(decisions),dtype=bool)
        for col,value in zip(group_keys,key):condition &= decisions[col].to_numpy()==value
        ds=decisions.loc[condition].sort_values('date')
        s=investors[key[2]]
        for i,event in enumerate(group.to_dict('records')):
            end=group.date.iloc[i+1] if i+1<len(group) else pd.Timestamp.max
            nexts=ds[(ds.date>=event['date'])&(ds.date<end)]
            next_any=ds[ds.date>=event['date']]
            current_opportunity=len(nexts)>0
            record={**event,'event_id':'|'.join(map(str,key))+f'|{i:04d}',
                'primary_comparison_basis':'active_feedback_vs_initial_fixed_policy_on_same_state',
                'effective_policy_window_end':end if end!=pd.Timestamp.max else pd.NaT,
                'opportunity_before_policy_replaced':current_opportunity,'eligible_monthly_opportunities':len(nexts),
                'next_decision_date':next_any.date.iloc[0] if len(next_any) else pd.NaT,
                'actual_recommendation_changed':False,'event_response_sessions':np.nan,
                'policy_propagated':np.nan,'policy_state_recorded':True,'buy_only_cannot_modify_existing_holdings':True,
                'available_investable_cash':event['brokerage_cash_at_event'],'candidate_stocks_before_restrictions':'[]',
                'candidate_stocks_after_restrictions':'[]','ranking_before_feedback':'[]','ranking_after_feedback':'[]',
                'quantities_before_feedback':'[]','quantities_after_feedback':'[]',
                'candidate_eligibility_changed':False,'internal_selected_basket_changed':False,
                'binding_budget_change':event['old_multiplier']!=event['new_multiplier']}
            active=[]
            if event['var_breach']:active.append('VAR_95_BREACH')
            if event['volatility_breach']:active.append('VOLATILITY_SPIKE')
            if event['hhi_breach']:active.append('SECTOR_HHI_EXCEEDED')
            record['triggering_metric']=';'.join(active) if active else 'BREACH_RESOLVED_POLICY_RELEASE'
            record['configured_thresholds']=json.dumps({'var':event['var_threshold'],'daily_volatility':event['volatility_threshold'],'hhi':event['hhi_threshold']})
            if not current_opportunity:
                record['reason_for_no_change']='no_eligible_monthly_opportunity_before_next_policy_update' if len(next_any) else 'no_remaining_recommendation_opportunity_in_window'
            else:
                evaluated=[]
                for _,d in nexts.iterrows():
                    pool=cache[(str(d.date.date()),s.tier,True)]
                    held=json.loads(d.holdings);weights=json.loads(d.sector_weights)
                    prior=probe(pool,held,weights,'Full IntelliVest',s,d.brokerage_cash_before,tuple_policy(event['previous_policy']),authorization=d.authorization)
                    before=probe(pool,held,weights,'No Feedback',s,d.brokerage_cash_before,(1.,()),tuple_policy(d.fixed_policy),d.authorization)
                    after=probe(pool,held,weights,'Full IntelliVest',s,d.brokerage_cash_before,tuple_policy(event['updated_policy']),authorization=d.authorization)
                    changed=basket(before['orders'])!=basket(after['orders'])
                    prior_changed=basket(prior['orders'])!=basket(after['orders'])
                    assert tuple_policy(d.policy)==tuple_policy(event['updated_policy']),'policy was not propagated to recorded decision'
                    assert basket(after['orders'])==[tuple(x) for x in json.loads(d.quantities_after_feedback)]
                    evaluated.append((d,before,after,changed,prior,prior_changed))
                    opportunities.append({'event_id':record['event_id'],**dict(zip(group_keys,key)),
                        'decision_date':d.date,'initial_fixed_policy_counterfactual_quantities':json.dumps(basket(before['orders'])),
                        'previous_policy_counterfactual_quantities':json.dumps(basket(prior['orders'])),
                        'updated_policy_quantities':json.dumps(basket(after['orders'])),
                        'recommendation_changed':changed,'previous_policy_counterfactual_changed':prior_changed,
                        'reason':no_change_reason(before,after,d.brokerage_cash_before)})
                selected=next((x for x in evaluated if x[3]),evaluated[0])
                d,before,after,changed,prior,prior_changed=selected
                record['policy_propagated']=True
                record['changed_opportunities_count']=sum(int(x[3]) for x in evaluated)
                record['previous_policy_counterfactual_changed_opportunities']=sum(int(x[5]) for x in evaluated)
                first_prior=next((x for x in evaluated if x[5]),None)
                record['previous_policy_counterfactual_first_changed_date']=first_prior[0].date if first_prior else pd.NaT
                record['previous_policy_counterfactual_latency']=int(calendar.get_loc(first_prior[0].date)-calendar.get_loc(event['date'])) if first_prior else np.nan
                record['previous_policy_counterfactual_quantities']=json.dumps(basket(prior['orders']))
                record['representative_decision_date']=d.date
                record['candidate_universe_before_holdings_and_sector_checks']=json.dumps([x['ticker_symbol'] for x in cache[(str(d.date.date()),s.tier,True)]])
                record.update(available_investable_cash=d.brokerage_cash_before,
                    candidate_stocks_before_restrictions=json.dumps([x['ticker_symbol'] for x in before['eligible']]),
                    candidate_stocks_after_restrictions=json.dumps([x['ticker_symbol'] for x in after['eligible']]),
                    ranking_before_feedback=json.dumps([x['ticker_symbol'] for x in before['ranking']]),
                    ranking_after_feedback=json.dumps([x['ticker_symbol'] for x in after['ranking']]),
                    quantities_before_feedback=json.dumps(basket(before['orders'])),quantities_after_feedback=json.dumps(basket(after['orders'])),
                    budget_before_feedback=before['budget'],budget_after_feedback=after['budget'],
                    actual_recommendation_changed=changed,
                    candidate_eligibility_changed=set(x['ticker_symbol'] for x in before['eligible'])!=set(x['ticker_symbol'] for x in after['eligible']),
                    internal_selected_basket_changed=[x['ticker_symbol'] for x in before['selected']]!=[x['ticker_symbol'] for x in after['selected']],
                    reason_for_no_change=no_change_reason(before,after,d.brokerage_cash_before))
                if changed:
                    record['event_response_sessions']=int(calendar.get_loc(d.date)-calendar.get_loc(event['date']))
            rows.append(record)
    return pd.DataFrame(rows),pd.DataFrame(opportunities)
