"""Deterministic daily accounting; CSV-only input and in-memory portfolio state."""
import json
import numpy as np
import pandas as pd
from backend.config import settings
from research.strategies import propose, feedback_policy
from research.risk_metrics import performance, tail_metrics, episode_lengths


def signature(orders):
    return tuple(sorted((o['ticker_symbol'],o['quantity']) for o in orders))


def replay(dataset,scenario,policy,start,end,cache,fee=.001,slippage=.0005,momentum=True,initial_seed=None):
    dates=pd.DatetimeIndex(sorted(dataset.date.unique()))
    days=dates[(dates>=pd.Timestamp(start))&(dates<=pd.Timestamp(end))]
    closes=dataset.pivot(index='date',columns='ticker',values='nominal_close')
    adjusted=dataset.pivot(index='date',columns='ticker',values='adjusted_close')
    returns=adjusted.pct_change(fill_method=None)
    bars={(r.date,r.ticker):r for r in dataset.itertuples()}
    sectors=dict(dataset[['ticker','sector']].drop_duplicates().itertuples(index=False,name=None))
    holdings,costs={},{}
    cash=previous_equity=scenario.initial_cash
    feedback=(1.,())
    fixed_policy=(1.,())
    if initial_seed:
        prior_day=dates[dates<days[0]][-1]
        seed_value=0.
        initial_sector_values={}
        for ticker,q in initial_seed.items():
            assert isinstance(q,int) and q>0
            value=q*float(closes.loc[prior_day,ticker])
            holdings[ticker]=q
            costs[ticker]=value
            seed_value+=value
            initial_sector_values[sectors[ticker]]=initial_sector_values.get(sectors[ticker],0.)+value
        cash-=seed_value
        assert cash>=0
        initial_weights={s:v/seed_value for s,v in initial_sector_values.items()}
        hist=returns.loc[:prior_day,list(initial_seed)].tail(30).dropna(how='any')
        hr=hist.to_numpy()@np.array([initial_seed[t]*float(closes.loc[prior_day,t])/scenario.initial_cash for t in hist.columns])
        sigma=float(np.std(hr,ddof=1)) if len(hr)==30 else np.nan
        flags=(bool(1.645*sigma>settings.RISK_VAR_LIMIT_PERCENT),bool(sigma>settings.RISK_DAILY_VOLATILITY_LIMIT),
               sum(w*w for w in initial_weights.values())>settings.DEFAULT_TARGET_HHI_LIMIT)
        fixed_policy=feedback_policy(flags,initial_weights)
        feedback=fixed_policy
    pending=[]
    batch_budget_remaining=0.
    remaining_capacity=0.
    valuations,decisions,trades,policies,positions,order_events=[],[],[],[],[],[]
    prior_flags=(False,False,False)
    prior_weights={}
    last_month=None
    last_set=None
    episodes=[]
    current_episodes={}
    total_realized=0.
    for di,day in enumerate(days):
        contribution=0.
        monthly=last_month!=(day.year,day.month)
        if monthly:
            contribution=scenario.buffer
            cash+=contribution
            remaining_capacity=scenario.buffer
            last_month=(day.year,day.month)
        # Corporate actions apply to overnight holders, before today's trades.
        dividends=0.
        for ticker,q in list(holdings.items()):
            bar=bars[(day,ticker)]  # Missing held bar is fatal, never zero-filled.
            split=bar.split if bar.split else 1.
            dividend=q*split*bar.nominal_dividend
            dividends+=dividend
            exact=q*split
            units=int(np.floor(exact+1e-6))
            fraction=max(0.,exact-units)
            if fraction>1e-6:
                proceeds=fraction*bar.nominal_close
                removed_cost=costs[ticker]*fraction/exact
                costs[ticker]-=removed_cost
                total_realized+=proceeds-removed_cost
                cash+=proceeds
                trades.append({'date':day,'decision_date':pd.NaT,'ticker':ticker,'side':'CASH_IN_LIEU',
                    'quantity':0,'fractional_entitlement':fraction,'notional':proceeds,'fee':0.,'slippage_cost':0.,'cash_after':cash})
            holdings[ticker]=units
        cash+=dividends
        executed=0.
        if pending:
            for order in pending:
                ticker=order['ticker_symbol']
                bar=bars.get((day,ticker))
                if bar is None:
                    order_events.append({'date':day,'decision_date':order['decision_date'],'ticker':ticker,
                        'requested_quantity':order['quantity'],'executed_quantity':0,'status':'cancelled_missing_bar'})
                    continue
                raw=bar.nominal_close
                price=raw*(1+slippage)
                # Adjust pending nominal quantities for a split between signal and execution.
                requested=int(np.floor(order['quantity']*(bar.split or 1.)+1e-6))
                available=min(cash,batch_budget_remaining) if policy=='Risk Only' else min(cash,remaining_capacity,batch_budget_remaining)
                q=min(requested,int(np.floor((available+1e-8)/(price*(1+fee)))))
                order_events.append({'date':day,'decision_date':order['decision_date'],'ticker':ticker,
                    'requested_quantity':requested,'executed_quantity':max(q,0),
                    'status':'filled' if q==requested else 'partial_capacity_fill' if q>0 else 'cancelled_capacity_or_cash'})
                if q<=0:
                    continue
                notional=q*price
                commission=notional*fee
                debit=notional+commission
                cash-=debit
                batch_budget_remaining-=debit
                remaining_capacity-=debit
                executed+=debit
                holdings[ticker]=holdings.get(ticker,0)+q
                costs[ticker]=costs.get(ticker,0)+debit
                trades.append({'date':day,'decision_date':order['decision_date'],'ticker':ticker,'side':'BUY',
                    'quantity':q,'fractional_entitlement':0.,'notional':notional,'fee':commission,
                    'slippage_cost':q*raw*slippage,'cash_after':cash})
            if decisions:
                decisions[-1]['executed_cost']=executed
                decisions[-1]['unused_capacity']=max(0.,scenario.buffer-executed)
            pending=[]
        values={t:q*float(closes.loc[day,t]) for t,q in holdings.items() if q>0}
        stock_value=sum(values.values())
        equity=cash+stock_value
        assert cash>=-1e-6 and all(isinstance(q,int) and q>=0 for q in holdings.values())
        sector_values={s:sum(v for t,v in values.items() if sectors[t]==s) for s in set(sectors.values())}
        weights={s:v/stock_value for s,v in sector_values.items() if v>0} if stock_value else {}
        hhi=sum(w*w for w in weights.values()) if weights else np.nan
        estimated_var=vol30=estimated_cvar=estimated_hvar=np.nan
        n=0
        if values:
            hist=returns.loc[:day,list(values)].tail(252).dropna(how='any')
            n=len(hist)
            hypothetical=hist.to_numpy()@np.array([values[t]/equity for t in hist.columns])
            if n>=30:
                vol30=float(np.std(hypothetical[-30:],ddof=1))
                estimated_var=1.645*vol30
            if n==252:
                tail=tail_metrics(hypothetical)
                estimated_cvar,estimated_hvar=tail['cvar95'],tail['var95']
        flags=(bool(estimated_var>settings.RISK_VAR_LIMIT_PERCENT),bool(vol30>settings.RISK_DAILY_VOLATILITY_LIMIT),
               bool(hhi>settings.DEFAULT_TARGET_HHI_LIMIT))
        for idx,name in enumerate(['var','volatility','hhi']):
            if flags[idx] and not prior_flags[idx]:
                event={'metric':name,'breach_date':day,'breach_index':di,'first_modified_date':None,'response_sessions':None,'resolved_date':None}
                episodes.append(event)
                current_episodes[name]=event
            elif not flags[idx] and prior_flags[idx]:
                current_episodes[name]['resolved_date']=day
                current_episodes.pop(name)
        computed=feedback_policy(flags,weights)
        if policy=='Full IntelliVest' and computed!=feedback:
            policies.append({'date':day,'old_multiplier':feedback[0],'new_multiplier':computed[0],
                'old_blocked':json.dumps(feedback[1]),'new_blocked':json.dumps(computed[1]),
                'var_breach':flags[0],'volatility_breach':flags[1],'hhi_breach':flags[2]})
            feedback=computed
        direct_effect=False
        if monthly and di+1<len(days):
            pool=cache[(str(day.date()),scenario.tier,momentum)]
            budget,selected,orders=propose(pool,holdings,weights,policy,scenario,cash,feedback,fixed_policy)
            _,_,counter=propose(pool,holdings,weights,'No Feedback',scenario,cash,(1.,()),fixed_policy)
            direct_effect=policy=='Full IntelliVest' and signature(orders)!=signature(counter)
            if direct_effect:
                for event in current_episodes.values():
                    if event['first_modified_date'] is None and event['breach_index']<=di:
                        event['first_modified_date']=day
                        event['response_sessions']=di-event['breach_index']
            selected_set={x['ticker_symbol'] for x in selected}
            stability=np.nan if last_set is None else len(selected_set&last_set)/len(selected_set|last_set) if selected_set|last_set else 1.
            last_set=selected_set
            proposed=sum(x['proposed_notional'] for x in orders)
            decisions.append({'date':day,'execution_date':days[di+1],'household_buffer':scenario.buffer,
                'budget':budget,'proposed_notional':proposed,'overspend':max(0.,proposed-scenario.buffer),
                'affordability_violation':proposed>scenario.buffer+1e-8,'selected':json.dumps(sorted(selected_set)),
                'orders':json.dumps(signature(orders)),'executed_cost':0.,'unused_capacity':scenario.buffer,
                'selected_strong_negative':sum(x['strong_negative'] for x in selected),'selected_count':len(selected),
                'direct_feedback_change':direct_effect,'stability_jaccard':stability,
                'capacity_multiplier':feedback[0],'blocked_sectors':json.dumps(feedback[1]),
                'candidate_evidence':json.dumps(pool)})
            pending=[{**o,'decision_date':day} for o in orders]
            batch_budget_remaining=budget
        r=equity/(previous_equity+contribution)-1
        assert abs((equity-previous_equity-contribution)-r*(previous_equity+contribution))<1e-5
        drift=.5*sum(abs(weights.get(s,0)-prior_weights.get(s,0)) for s in set(weights)|set(prior_weights)) if prior_weights else np.nan
        valuations.append({'date':day,'cash':cash,'stock_value':stock_value,'equity':equity,'contribution':contribution,
            'return':r,'dividends':dividends,'hhi':hhi,'cash_fraction':cash/equity,'estimated_var95':estimated_hvar,
            'estimated_parametric_var95':estimated_var,'estimated_cvar95':estimated_cvar,'volatility30':vol30,
            'risk_observations':n,'var_breach':flags[0],'volatility_breach':flags[1],'hhi_breach':flags[2],
            'any_breach':any(flags),'repeated_breach':any(a and b for a,b in zip(flags,prior_flags)),
            'allocation_drift':drift,'policy_multiplier':feedback[0],'policy_blocked':json.dumps(feedback[1]),
            'cost_basis':sum(costs.values()),'unrealized_gain':stock_value-sum(costs.values()),'realized_gain':total_realized})
        positions.extend({'date':day,'ticker':t,'quantity':holdings[t],'cost_basis':costs[t],
                          'market_value':v,'sector':sectors[t]} for t,v in values.items())
        previous_equity,prior_flags,prior_weights=equity,flags,weights
    v,d,t,p,e=map(pd.DataFrame,[valuations,decisions,trades,policies,episodes])
    hhi_lengths=episode_lengths(v.hhi_breach)
    overs=d.overspend
    summary={**performance(v['return'],settings.STOCK_ANNUAL_RISK_FREE_RATE),
        'affordability_violation_rate':float(d.affordability_violation.mean()),'mean_overspend':float(overs.mean()),
        'conditional_mean_overspend':float(overs[overs>0].mean()) if (overs>0).any() else 0.,'max_overspend':float(overs.max()),
        'surplus_utilization':float(d.executed_cost.sum()/(scenario.buffer*len(d))) if scenario.buffer else np.nan,
        'mean_unused_capacity':float(d.unused_capacity.mean()),'no_purchase_frequency':float((d.executed_cost==0).mean()),
        'mean_hhi':float(v.hhi.mean()),'max_hhi':float(v.hhi.max()),'hhi_breach_frequency':float(v.hhi_breach.mean()),
        'hhi_breach_sessions':int(v.hhi_breach.sum()),'mean_hhi_episode_sessions':float(np.mean(hhi_lengths)) if hhi_lengths else 0.,
        'max_hhi_episode_sessions':max(hhi_lengths,default=0),'terminal_hhi_censored':bool(v.hhi_breach.iloc[-1]),
        'risk_breach_sessions':int(v.any_breach.sum()),'repeated_breach_sessions':int(v.repeated_breach.sum()),
        'detected_breach_episodes':len(e),'policy_adjustments':len(p),'direct_feedback_changed_decisions':int(d.direct_feedback_change.sum()),
        'feedback_response_sessions':float(e.response_sessions.dropna().mean()) if len(e) and e.response_sessions.notna().any() else np.nan,
        'feedback_responses':int(e.response_sessions.notna().sum()) if len(e) else 0,
        'feedback_unanswered':int(e.response_sessions.isna().sum()) if len(e) else 0,
        'stability_jaccard':float(d.stability_jaccard.mean()),'mean_allocation_drift':float(v.allocation_drift.mean()),
        'turnover':float(t.loc[t.side=='BUY','notional'].sum()/v.equity.mean()) if len(t) else 0.,
        'transaction_fees':float(t.fee.sum()) if len(t) else 0.,'slippage_cost':float(t.slippage_cost.sum()) if len(t) else 0.,
        'average_cash_allocation':float(v.cash_fraction.mean()),'average_idle_cash':float(v.cash.mean()),
        'ending_equity':float(v.equity.iloc[-1]),'contributions':float(v.contribution.sum()),
        'investment_gain':float(v.equity.iloc[-1]-scenario.initial_cash-v.contribution.sum()),
        'strong_negative_selection_rate':float(d.selected_strong_negative.sum()/d.selected_count.sum()) if d.selected_count.sum() else np.nan,
        'decision_count':len(d),'sessions':len(v),'trade_count':int((t.side=='BUY').sum()) if len(t) else 0}
    return summary,{'valuations':v,'decisions':d,'trades':t,'order_events':pd.DataFrame(order_events),'policy_changes':p,'breach_episodes':e,'positions':pd.DataFrame(positions)}
