"""Same-state policy probes and non-overlapping purchase-authorization waterfall."""
import json
from types import SimpleNamespace
import numpy as np
from research.strategies import CAPACITY, propose as original_propose, select_candidates


def propose(pool,holdings,weights,policy,scenario,cash,feedback,fixed_policy=(1.,()),authorization='original'):
    if authorization not in {'original','accumulated_approved_cash_v1'}:
        raise ValueError(authorization)
    effective=scenario if authorization=='original' else SimpleNamespace(buffer=cash,tier=scenario.tier)
    return original_propose(pool,holdings,weights,policy,effective,cash,feedback,fixed_policy)


def policy_json(policy):
    return json.dumps({'multiplier':float(policy[0]),'blocked_sectors':list(policy[1])},sort_keys=True)


def basket(orders):
    return sorted((o['ticker_symbol'],int(o['quantity'])) for o in orders)


def probe(pool,holdings,weights,policy,scenario,cash,feedback,fixed=(1.,()),authorization='original'):
    budget,selected,orders=propose(pool,holdings,weights,policy,scenario,cash,feedback,fixed,authorization)
    risk=policy!='Affordability Only'
    multiplier,blocked=feedback if policy=='Full IntelliVest' else fixed if risk else (1.,())
    after_held=[x for x in pool if holdings.get(x['ticker_symbol'],0)==0]
    eligible=[{**x,'sector_weight':weights.get(x['sector_name'],0.) if risk else 0.}
              for x in after_held if x['sector_name'] not in blocked]
    ranked=sorted(eligible,key=lambda x:(x['sector_weight'],-x['selection_score'],x['ticker_symbol']))
    total=sum(x['size_weight'] for x in selected)
    slots=[]
    for x in selected:
        allocation=np.floor(budget*x['size_weight']/total*100+1e-8)/100
        quantity=int(np.floor(allocation/x['nominal_price']))
        slots.append({'ticker':x['ticker_symbol'],'sector':x['sector_name'],'score':x['selection_score'],
                      'nominal_price':x['nominal_price'],'slot_budget':allocation,'quantity':quantity})
    return {'budget':budget,'eligible':eligible,'ranking':ranked,'selected':selected,'orders':orders,'slots':slots,
            'after_held':after_held,'multiplier':multiplier,'blocked':blocked}


def no_change_reason(before,after,cash):
    """One mutually exclusive explanation per comparison, with explicit precedence."""
    if basket(before['orders'])!=basket(after['orders']):
        return 'final_recommendation_changed'
    if cash<=0:
        return 'insufficient_brokerage_cash'
    before_names=[x['ticker_symbol'] for x in before['ranking']]
    after_names=[x['ticker_symbol'] for x in after['ranking']]
    if not before_names and not after_names:
        return 'stock_already_excluded_by_holdings_or_other_fixed_rule'
    if before_names==after_names and before['budget']==after['budget']:
        return 'restriction_already_satisfied_after_other_exclusions'
    if [x['ticker_symbol'] for x in before['selected']]==[x['ticker_symbol'] for x in after['selected']] and before['budget']==after['budget']:
        return 'removed_candidates_did_not_win_existing_exposure_order'
    if not before['orders'] and not after['orders']:
        return 'internal_change_but_whole_share_orders_remained_empty'
    return 'internal_change_but_final_quantities_identical'


def decision_record(day,scenario,policy,pool,holdings,weights,cash,feedback,fixed,budget,selected,orders,authorization):
    current=probe(pool,holdings,weights,policy,scenario,cash,feedback,fixed,authorization)
    baseline=probe(pool,holdings,weights,'No Feedback',scenario,cash,(1.,()),fixed,authorization)
    if policy=='Affordability Only':
        baseline=current
    base=cash if policy=='Risk Only' or authorization!='original' else min(cash,scenario.buffer)
    tier=CAPACITY[scenario.tier]
    mult=current['multiplier']
    # Disjoint authorization stages sum to cash at the signal date. Their sums
    # over dates are INR-opportunities, NOT unique household capital stocks.
    deferred=cash-base
    tier_withheld=base*(1-tier)
    risk_withheld=base*tier*(1-mult)
    rounding=base*tier*mult-budget
    candidate_exhaustion=budget if not selected else 0.
    allocation_rounding=budget-sum(x['slot_budget'] for x in current['slots']) if selected else 0.
    zero_slots=sum(x['slot_budget'] for x in current['slots'] if x['quantity']==0)
    positive_rounding=sum(x['slot_budget']-x['quantity']*x['nominal_price'] for x in current['slots'] if x['quantity']>0)
    notional=sum(o['proposed_notional'] for o in orders)
    parts=[deferred,tier_withheld,risk_withheld,rounding,candidate_exhaustion,allocation_rounding,zero_slots,positive_rounding,notional]
    assert min(parts)>=-1e-6 and abs(sum(parts)-cash)<1e-5,(parts,cash)
    minimum=min((x['nominal_price'] for x in current['eligible']),default=np.nan)
    if budget<=0:
        idle_reason='zero_authorized_budget'
    elif not current['eligible']:
        idle_reason='no_eligible_candidates_after_history_holdings_and_sector_rules'
    elif not orders and minimum>budget:
        idle_reason='all_eligible_stocks_exceed_whole_batch_budget'
    elif not orders:
        idle_reason='top_three_slot_sizing_zero_despite_feasible_one_share_candidate'
    elif zero_slots>1e-8:
        idle_reason='partial_basket_unaffordable_selected_slots'
    else:
        idle_reason='positive_purchase_with_round_lot_residual'
    return {'date':day,'scenario':scenario.name,'strategy':policy,'authorization':authorization,
        'protected_reserve_target_outside_brokerage':scenario.reserve,'protected_reserve_in_brokerage':0.,
        'household_savings_not_yet_transferred':0.,'newly_approved_monthly_surplus':scenario.buffer,
        'brokerage_cash_before':cash,'eligible_authorization_base':base,'cash_eligible_for_current_purchases':budget,
        'deferred_accumulated_cash':deferred,'tier_withheld':tier_withheld,'risk_withheld':risk_withheld,
        'budget_cent_rounding':rounding,'no_candidate_budget':candidate_exhaustion,'slot_cent_rounding':allocation_rounding,
        'unaffordable_selected_slots':zero_slots,'whole_share_residual_positive_slots':positive_rounding,
        'proposed_notional':notional,'executed_cost':0.,'unused_authorized_budget':budget,
        'primary_unused_reason':idle_reason,'valid_history_candidates':len(pool),'held_exclusions':len(pool)-len(current['after_held']),
        'sector_exclusions':len(current['after_held'])-len(current['eligible']),
        'eligible_candidates':len(current['eligible']),'minimum_eligible_price':minimum,
        'available_one_share_candidate':bool(minimum<=budget),'policy':policy_json(feedback),
        'fixed_policy':policy_json(fixed),'propagated_policy_multiplier':mult,'actual_budget':budget,
        'candidate_stocks_before_restrictions':json.dumps([x['ticker_symbol'] for x in pool]),
        'candidates_after_holdings':json.dumps([x['ticker_symbol'] for x in current['after_held']]),
        'candidates_before_feedback':json.dumps([x['ticker_symbol'] for x in baseline['eligible']]),
        'candidates_after_feedback':json.dumps([x['ticker_symbol'] for x in current['eligible']]),
        'ranking_before_feedback':json.dumps([x['ticker_symbol'] for x in baseline['ranking']]),
        'ranking_after_feedback':json.dumps([x['ticker_symbol'] for x in current['ranking']]),
        'quantities_before_feedback':json.dumps(basket(baseline['orders'])),
        'quantities_after_feedback':json.dumps(basket(current['orders'])),
        'slots':json.dumps(current['slots']),'holdings':json.dumps(holdings),'sector_weights':json.dumps(weights),
        'candidate_eligibility_changed':set(x['ticker_symbol'] for x in baseline['eligible'])!=set(x['ticker_symbol'] for x in current['eligible']),
        'selected_basket_changed':[x['ticker_symbol'] for x in baseline['selected']]!=[x['ticker_symbol'] for x in current['selected']],
        'final_recommendation_changed':basket(baseline['orders'])!=basket(current['orders']),
        'reason_for_no_change':no_change_reason(baseline,current,cash)}
