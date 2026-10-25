"""Isolated monthly research ledger with shared delayed execution and risk monitoring."""
import json
import numpy as np
import pandas as pd
from research.strategies import CAPACITY,feedback_policy
from research.phase8.policies.authority import Authority
from research.phase8.policies.construction import build,Guard,corrective_sales


def signature(q,market):return json.dumps([(market.tickers[i],int(n)) for i,n in enumerate(q) if n],separators=(',',':'))


def run(market,cache,scenario,policy,start,end,kind='principal',initial_seed=None,shock=False):
    dates=market.dates;indices=np.where((dates>=pd.Timestamp(start))&(dates<=pd.Timestamp(end)))[0]
    n=len(market.tickers);q=np.zeros(n,dtype=int);basis=np.zeros(n);cash=float(scenario.initial_cash)
    if initial_seed:
        for ticker,units in initial_seed.items():
            i=market.index[ticker];q[i]=units;basis[i]=units*market.prices[indices[0]-1,i];cash-=basis[i]
    ledger=Authority(policy.carry);previous_equity=scenario.initial_cash
    feedback=(1.,());pending=None;last_month=None;last_buffer=None;realized=0.;last_flags=(False,False,False)
    effective_signature=None
    vals=[];decisions=[];trades=[];policies=[];fills=[];episodes=[];active={};seen_execution=set()
    external_before_month=0.;monthly_grant=0.
    # Initial concentrated-start policy is measured on the actual pre-start state.
    if initial_seed:
        state=market.state(q,cash,indices[0]-1);feedback=feedback_policy(state['flags'],state['weights'])
    initial_feedback=feedback
    for di in indices:
        day=dates[di];monthly=last_month!=(day.year,day.month);contribution=0.
        buffer=0. if shock and pd.Timestamp('2024-01-01')<=day<pd.Timestamp('2024-04-01') else scenario.buffer
        if monthly:
            contribution=buffer;cash+=contribution
            external_before_month=ledger.balance
            monthly_grant=ledger.month(day,buffer,CAPACITY[scenario.tier]);last_month=(day.year,day.month);last_buffer=buffer
            carried_after_review=ledger.balance-monthly_grant
        # Actions apply to overnight holdings, not shares bought at this close.
        splits=np.where(market.splits[di]>0,market.splits[di],1.)
        exact=q*splits;new_q=np.floor(exact+1e-6).astype(int);fractions=np.maximum(0.,exact-new_q)
        dividends=float(np.sum(exact*market.dividends[di]));cash+=dividends
        for i in np.where(fractions>1e-6)[0]:
            proceeds=fractions[i]*market.prices[di,i];removed=basis[i]*fractions[i]/exact[i]
            basis[i]-=removed;cash+=proceeds;realized+=proceeds-removed
            trades.append({'date':day,'decision_date':pd.NaT,'ticker':market.tickers[i],'side':'CASH_IN_LIEU','quantity':0,
                'fractional_entitlement':fractions[i],'notional':proceeds,'fee':0.,'slippage_cost':0.,'realized_gain':proceeds-removed,'new_position':False,'topup':False,'feedback_attributable':False})
        q=new_q
        if pending is not None:
            assert day>pending['date'] and pending['id'] not in seen_execution
            seen_execution.add(pending['id']);record=decisions[-1]
            before_q=q.copy();before_cash=cash;before_authority=ledger.balance
            unit=market.prices[di]*(1+.0005)*(1+.001)
            cf_fill=np.zeros(n,dtype=int);cf_cost=0.
            cf_requested=np.floor(pending['counter_buys']*splits+1e-6).astype(int)
            for ticker in pending['counter_order']:
                i=market.index[ticker];quantity=min(int(cf_requested[i]),max(0,int(np.floor((min(before_cash,before_authority,pending['counter_budget'])-cf_cost+1e-8)/unit[i]))))
                cf_fill[i]=quantity;cf_cost+=quantity*unit[i]
            if policy.guards and cf_fill.any():
                cf_guard=Guard(before_q,before_cash,market.prices[di],market.cov30[pending['di']],market.sector_matrix)
                if not cf_guard.allowed(cf_fill,cf_cost)[0]:cf_fill[:]=0;cf_cost=0.
            # Only explicit V5_SELL can sell. All other versions are buy-only.
            sold_net=0.
            requested_sells=np.floor(pending['sells']*splits+1e-6).astype(int)
            if requested_sells.any():
                # Price drift cannot turn a planned correction into worsening
                # concentration or exceed the actual 10% invested-value cap.
                cap=.10*float(q@market.prices[di]);sale_value=float(requested_sells@market.prices[di])
                if sale_value>cap:requested_sells=np.floor(requested_sells*(cap/sale_value)).astype(int)
                from research.phase8.policies.construction import hhi
                if float(requested_sells@market.prices[di])<500 or requested_sells.sum()==0 or hhi((q-requested_sells)*market.prices[di],market.sector_matrix)>=state_before_sale_hhi(q,market,di)-1e-12:
                    requested_sells[:]=0
            for i in np.where(requested_sells>0)[0]:
                units=min(int(q[i]),int(requested_sells[i]))
                if not units:continue
                price=market.prices[di,i]*(1-.0005);notional=units*price;fee=notional*.001;net=notional-fee
                cost=basis[i]*units/q[i];basis[i]-=cost;q[i]-=units;cash+=net;sold_net+=net;realized+=net-cost
                ledger.recycle(net,day,pending['id']+'sell'+str(i))
                trades.append({'date':day,'decision_date':pending['date'],'ticker':market.tickers[i],'side':'SELL','quantity':units,
                    'notional':notional,'fee':fee,'slippage_cost':units*market.prices[di,i]*.0005,'realized_gain':net-cost,
                    'new_position':False,'topup':False,'feedback_attributable':True})
            actual_cap=min(cash,ledger.balance,pending['budget'])
            requested=np.floor(pending['buys']*splits+1e-6).astype(int)
            fill=np.zeros(n,dtype=int);cost=0.
            unit=market.prices[di]*(1+.0005)*(1+.001)
            # Shared source-compatible order-priority whole-share fill cap.
            for ticker in pending['order']:
                i=market.index[ticker]
                units=min(int(requested[i]),max(0,int(np.floor((actual_cap-cost+1e-8)/unit[i]))))
                fill[i]=units;cost+=units*unit[i]
            cancellation=''
            if policy.guards and fill.any():
                guard=Guard(q,cash,market.prices[di],market.cov30[pending['di']],market.sector_matrix)
                safe,why=guard.allowed(fill,cost,strict=policy.redirect)
                if not safe:fill[:]=0;cost=0.;cancellation='execution_'+why
            assert cost<=min(cash,ledger.balance,pending['budget'])+1e-6
            ext=rec=0.
            for i in np.where(fill>0)[0]:
                units=int(fill[i]);notional=units*market.prices[di,i]*(1+.0005);fee=notional*.001;debit=notional+fee
                new_position=q[i]==0;e,r=ledger.spend(debit,day,pending['id']+'buy'+str(i));ext+=e;rec+=r
                cash-=debit;basis[i]+=debit;q[i]+=units
                trades.append({'date':day,'decision_date':pending['date'],'ticker':market.tickers[i],'side':'BUY','quantity':units,
                    'notional':notional,'fee':fee,'slippage_cost':units*market.prices[di,i]*.0005,'realized_gain':0.,
                    'new_position':bool(new_position),'topup':not new_position,
                    'feedback_attributable':bool(units!=cf_fill[i])})
            fills.append({'date':day,'decision_date':pending['date'],'requested':signature(requested,market),'executed':signature(fill,market),
                'cancel_reason':cancellation,'cost':cost,'sold_net_proceeds':sold_net})
            record.update(executed_quantities=signature(fill,market),executed_cost=cost,sold_net_proceeds=sold_net,
                cash_after_purchases=cash,authority_after_purchases=ledger.balance,external_authority_spent=ext,
                recycled_authority_spent=rec,execution_cancel_reason=cancellation,
                counterfactual_executed_quantities=signature(cf_fill,market),
                actual_trade_change=bool(not np.array_equal(fill,cf_fill) or sold_net>0),
                incremental_feedback_fees=(float(fill@market.prices[di])*1.0005*.001+sold_net/(1-.001)*.001)-(float(cf_fill@market.prices[di])*1.0005*.001),
                incremental_feedback_slippage=(float(fill@market.prices[di])*.0005+float(requested_sells@market.prices[di])*.0005)-(float(cf_fill@market.prices[di])*.0005))
            pending=None
        assert cash>=-1e-6 and (q>=0).all();ledger.check(cash)
        state=market.state(q,cash,di);flags=state['flags']
        for k,metric in enumerate(['var','volatility','hhi']):
            if flags[k] and not last_flags[k]:
                event={'metric':metric,'breach_date':day,'breach_index':int(di),'resolved_date':pd.NaT,'resolved':False,
                       'first_changed_recommendation':pd.NaT,'response_sessions':np.nan,'left_censored':bool(di==indices[0] and initial_seed)}
                episodes.append(event);active[metric]=event
            elif not flags[k] and last_flags[k]:
                active[metric].update(resolved=True,resolved_date=day);active.pop(metric)
        computed=feedback_policy(flags,state['weights'])
        extra=tuple(sorted(s for s,w in state['weights'].items() if w>.25)) if policy.redirect and flags[2] else ()
        new_signature=(computed[0],tuple(sorted(set(computed[1])|set(extra))),bool(policy.redirect and flags[2]),bool(policy.selling and flags[2]))
        if effective_signature is None:effective_signature=(feedback[0],feedback[1],False,False)
        if new_signature!=effective_signature:
            policies.append({'date':day,'previous_policy':json.dumps(effective_signature),'updated_policy':json.dumps(new_signature),
                'hhi':state['hhi'],'var':state['parametric_var95'],'volatility':state['daily_volatility'],
                'hhi_breach':flags[2],'var_breach':flags[0],'volatility_breach':flags[1],
                'policy_effective_delay_sessions':0})
        effective_signature=new_signature;feedback=computed
        if monthly and di<indices[-1]:
            pool=cache[(str(day.date()),scenario.tier,policy.momentum)]
            assert all(pd.Timestamp(r['history_through'])<=day for r in pool)
            available=min(cash,ledger.balance)
            sells=corrective_sales(q,market.prices[di],market.sector_matrix) if policy.selling and flags[2] and buffer>0 else np.zeros(n,dtype=int)
            sale_estimate=float(sells@market.prices[di])*(1-.0005)*(1-.001)
            planning_q=q-sells;planning_cash=cash+sale_estimate
            plan,info=build(pool,planning_q,planning_cash,available+sale_estimate,feedback,policy,market,di)
            # Explicit counterfactual: V5 vs V4 on exactly the same pre-action
            # state/budget. Original feedback vs fixed policy is separate.
            from dataclasses import replace
            if policy.redirect:
                cf_policy=replace(policy,name='counterfactual_V4',redirect=False,selling=False)
                counter,counter_info=build(pool,q,cash,available,feedback,cf_policy,market,di)
            else:
                counter,counter_info=build(pool,q,cash,available,feedback,policy,market,di,override=initial_feedback)
            direct=not np.array_equal(plan,counter) or sells.any()
            if direct:
                for event in active.values():
                    if pd.isna(event['first_changed_recommendation']):event.update(first_changed_recommendation=day,response_sessions=int(di-event['breach_index']))
            notional=float(plan@market.prices[di]);estimated_cost=notional*(1+.0005)*(1+.001)
            executable_signal_cost=min(estimated_cost,info['budget'],available+sale_estimate)
            fresh_household_draw=max(0.,executable_signal_cost-carried_after_review-sale_estimate)
            record={'date':day,'execution_date':dates[di+1],'brokerage_cash':cash,'authority_before':ledger.balance,
                'new_monthly_buffer':buffer,'new_monthly_approval':monthly_grant,'carry_before_month':external_before_month,
                'authorized_batch_budget':info['budget'],'proposed_notional':notional,'estimated_cost':estimated_cost,
                'monthly_reference_overspend':max(0.,notional-buffer),
                'new_household_authority_violation':bool(fresh_household_draw>buffer+1e-7),
                'fresh_household_draw':fresh_household_draw,'carried_authority_after_review':carried_after_review,
                'reserve_violation':bool(contribution>scenario.buffer+1e-7),
                'authority_violation':bool(executable_signal_cost>available+sale_estimate+1e-7),'protected_reserve_in_brokerage':0.,
                'selected_basket':json.dumps(info['selected']),'eligible_securities':json.dumps(info['eligible']),
                'candidate_securities':json.dumps([r['ticker_symbol'] for r in pool]),
                'affordable_securities':json.dumps(info['single_feasible_candidates']),
                'proposed_quantities':signature(plan,market),'sell_proposal':signature(sells,market),
                'counterfactual_quantities':signature(counter,market),'direct_recommendation_change':bool(direct),
                'counterfactual_basis':'V4_same_state' if policy.redirect else 'fixed_original_feedback_same_state',
                'executed_quantities':'[]','executed_cost':0.,'sold_net_proceeds':0.,
                'counterfactual_executed_quantities':'[]','actual_trade_change':False,'incremental_feedback_fees':0.,'incremental_feedback_slippage':0.,
                'cash_after_purchases':cash,'authority_after_purchases':ledger.balance,'external_authority_spent':0.,'recycled_authority_spent':0.,
                'feasible_single_share_opportunity':bool(info['affordable_count']>0),'held_exclusions':info['held_exclusions'],
                'sector_exclusions':info['sector_exclusions'],'unused_reason':info['unused_reason'],
                'candidate_count':info['candidate_count'],'eligible_count':info['eligible_count'],
                'negative_momentum_selected':info['negative_momentum_selected'],'selected_count':len(info['selected']),
                'position_count':int((q>0).sum()),'bootstrap':not bool(q.any()),'hhi_at_signal':state['hhi'],
                'authority_grants_to_date':ledger.grants,'external_authority_spent_to_date':ledger.spent_external,
                'authority_expired_to_date':ledger.expired,'authority_revoked_to_date':ledger.revoked}
            decisions.append(record)
            pending={'date':day,'di':int(di),'id':f'{policy.name}|{day.date()}','buys':plan,'sells':sells,
                     'budget':info['budget'],'order':info['selected'],'direct_change':direct,
                     'counter_buys':counter,'counter_budget':counter_info['budget'],'counter_order':counter_info['selected']}
        equity=state['equity'];ret=equity/(previous_equity+contribution)-1
        vals.append({'date':day,'cash':cash,'stock_value':state['stock_value'],'equity':equity,'contribution':contribution,
            'return':ret,'cash_fraction':cash/equity,'dividends':dividends,'hhi':state['hhi'],
            'max_position_weight':state['max_position_weight'],'estimated_var95':state['estimated_var95'],
            'estimated_cvar95':state['estimated_cvar95'],'estimated_parametric_var95':state['parametric_var95'],
            'volatility30':state['daily_volatility'],'hhi_breach':flags[2],'var_breach':flags[0],'volatility_breach':flags[1],
            'authority_balance':ledger.balance,'external_grants':ledger.grants,'external_spent':ledger.spent_external,
            'recycled_grants':ledger.recycled_grants,'recycled_spent':ledger.spent_recycled,'expired_authority':ledger.expired,
            'revoked_authority':ledger.revoked,'cost_basis':float(basis.sum()),'unrealized_gain':state['stock_value']-basis.sum(),
            'realized_gain':realized,'position_count':int((q>0).sum()),'any_breach':any(flags)})
        previous_equity=equity;last_flags=flags
    return {key:pd.DataFrame(value) for key,value in {'valuations':vals,'decisions':decisions,'trades':trades,
        'policy_changes':policies,'fills':fills,'episodes':episodes,'authority_events':ledger.events}.items()}


def state_before_sale_hhi(q,market,di):
    from research.phase8.policies.construction import hhi
    return hhi(q*market.prices[di],market.sector_matrix)
