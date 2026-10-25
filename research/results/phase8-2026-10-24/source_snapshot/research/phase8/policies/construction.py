"""Transparent whole-share construction and explicitly versioned safeguards."""
from dataclasses import dataclass,replace
import numpy as np
from research.strategies import select_candidates


@dataclass(frozen=True)
class Policy:
    name: str
    carry: bool=False
    feasible: bool=False
    topups: bool=False
    guards: bool=False
    redirect: bool=False
    selling: bool=False
    momentum: bool=True


V1=Policy('V1')
V2=Policy('V2',carry=True)
V3=Policy('V3',feasible=True,topups=True,guards=True)
V4=Policy('V4',carry=True,feasible=True,topups=True,guards=True)
V5=replace(V4,name='V5',redirect=True)
SELL=replace(V5,name='V5_SELL',selling=True)
PRINCIPAL=[V1,V2,V3,V4,V5]
ABLATIONS=[Policy('GUARDS_ONLY',guards=True),Policy('FEAS_ONLY',feasible=True,guards=True),Policy('TOPUP_ONLY',topups=True,guards=True)]


def hhi(values,sector_matrix):
    total=float(values.sum())
    return float(np.sum((sector_matrix@values/total)**2)) if total>0 else np.nan


class Guard:
    def __init__(self,q,cash,prices,cov,sector_matrix,strict=False):
        self.q=q.copy();self.cash=cash;self.p=prices;self.cov=cov;self.sectors=sector_matrix;self.strict=strict
        values=q*prices;equity=cash+values.sum()
        self.pos=np.maximum(.20,values/equity)
        self.sector=np.maximum(.35,sector_matrix@values/equity)
        self.base_values=values.copy();self.base_sectors=sector_matrix@values
        self.base_hhi=hhi(values,sector_matrix)
        w=values/equity
        self.base_vol=float(np.sqrt(max(0,w@cov@w)))

    def allowed(self,added,cost,strict=False):
        if cost>self.cash+1e-7:return False,'cash'
        values=(self.q+added)*self.p;equity=self.cash-cost+values.sum()
        if np.any(values>np.maximum(.20*equity,self.base_values)+1e-7):return False,'position_limit'
        if np.any(self.sectors@values>np.maximum(.35*equity,self.base_sectors)+1e-7):return False,'sector_limit'
        concentration=hhi(values,self.sectors)
        if np.isfinite(self.base_hhi) and concentration>max(.25,self.base_hhi)+1e-10:return False,'hhi_limit'
        if strict and np.isfinite(self.base_hhi) and self.base_hhi>.25 and concentration>=self.base_hhi-1e-12:return False,'no_strict_hhi_improvement'
        w=values/equity;vol=float(np.sqrt(max(0,w@self.cov@w)))
        if vol>max(.03,self.base_vol)+1e-10:return False,'volatility_limit'
        if 1.645*vol>max(.10,1.645*self.base_vol)+1e-10:return False,'var_limit'
        return True,''


def build(pool,q,cash,authority,feedback,policy,market,di,fee=.001,slippage=.0005,override=None):
    multiplier,blocked=feedback if override is None else override
    budget=np.floor(min(cash,authority)*multiplier*100+1e-8)/100
    prices=market.prices[di];values=q*prices;total=values.sum()
    sector_weights=market.sector_matrix@values/total if total else np.zeros(len(market.sectors))
    blocked=set(blocked)
    if policy.redirect and total and hhi(values,market.sector_matrix)>.25:
        blocked|={s for s,w in zip(market.sectors,sector_weights) if w>.25}
    valid=[];reasons={};held_excluded=0;sector_excluded=0
    for row in pool:
        t=row['ticker_symbol'];i=market.index[t];sector=row['sector_name']
        if q[i]>0 and not policy.topups:held_excluded+=1;continue
        if sector in blocked:sector_excluded+=1;continue
        valid.append({**row,'sector_weight':sector_weights[market.sector_index[sector]],'index':i,'nominal_price':prices[i]})
    ranked=sorted(valid,key=lambda r:(r['sector_weight'],-r['selection_score'],r['ticker_symbol']))
    added=np.zeros(len(q),dtype=int)
    guard=Guard(q,cash,prices,market.cov30[di],market.sector_matrix,policy.redirect)
    unit=prices*(1+slippage)*(1+fee)
    def allowed(a):
        cost=float(a@unit)
        return cost<=budget+1e-7 and (not policy.guards or guard.allowed(a,cost)[0])
    single_feasible=[]
    for row in ranked:
        a=np.zeros(len(q),dtype=int);a[row['index']]=1
        if allowed(a):single_feasible.append(row['ticker_symbol'])
    selected=[]
    if budget>0 and policy.feasible:
        sectors=set()
        for row in ranked:
            if row['sector_name'] in sectors:continue
            a=added.copy();a[row['index']]+=1
            if allowed(a):
                selected.append(row);sectors.add(row['sector_name']);added=a
                if len(selected)==3:break
    elif budget>0:
        selected=select_candidates(valid)
        weights=sum(r['size_weight'] for r in selected)
        for row in selected:
            allocation=np.floor(budget*row['size_weight']/weights*100+1e-8)/100
            added[row['index']]=int(np.floor(allocation/prices[row['index']]))
        if policy.guards and not allowed(added):
            requested=added.copy();added[:]=0
            for row in selected:
                i=row['index'];lo,hi=0,int(requested[i])
                while lo<hi:
                    mid=(lo+hi+1)//2;a=added.copy();a[i]+=mid
                    if allowed(a):lo=mid
                    else:hi=mid-1
                added[i]+=lo
    if policy.feasible and selected:
        weight_total=sum(r['size_weight'] for r in selected)
        def add_max(i,upper):
            nonlocal added
            lo,hi=0,max(0,int(upper))
            while lo<hi:
                mid=(lo+hi+1)//2;a=added.copy();a[i]+=mid
                if allowed(a):lo=mid
                else:hi=mid-1
            added[i]+=lo;return lo
        for row in selected:
            i=row['index'];target=budget*row['size_weight']/weight_total
            add_max(i,max(0,int(target/unit[i])-added[i]))
        while True:
            changed=0
            for row in selected:
                i=row['index'];remaining=max(0,budget-float(added@unit))
                changed+=add_max(i,int(np.floor((remaining+1e-8)/unit[i])))
            if not changed:break
    cost=float(added@unit)
    if policy.guards and added.any():
        safe,reason=guard.allowed(added,cost,strict=policy.redirect)
        if not safe:added[:]=0;reasons[reason]=1
    if not budget:reason='no_approved_investment_cash'
    elif not valid:reason='existing_holding_restriction' if held_excluded==len(pool) else 'sector_concentration_restriction'
    elif not single_feasible:reason='no_affordable_or_risk_feasible_stock'
    elif not added.any():reason='policy_design_or_batch_risk_guard'
    elif float(added@unit)<budget-1e-7:reason='whole_share_or_concentration_residual'
    else:reason='budget_filled'
    return added,{'budget':float(budget),'candidate_count':len(pool),'eligible_count':len(valid),'affordable_count':len(single_feasible),
        'single_feasible_candidates':single_feasible,'held_exclusions':held_excluded,'sector_exclusions':sector_excluded,
        'selected':[r['ticker_symbol'] for r in selected],'eligible':[r['ticker_symbol'] for r in ranked],
        'blocked_sectors':sorted(blocked),'multiplier':multiplier,'unused_reason':reason,'guard_reasons':reasons,
        'negative_momentum_selected':sum(bool(r.get('strong_negative')) for r in selected)}


def corrective_sales(q,prices,sector_matrix):
    """Monotone whole-share HHI descent; 10% invested-value cap, never liquidation."""
    requested=np.zeros(len(q),dtype=int);work=q.copy();initial=float(work@prices)
    if initial<=0:return requested
    limit=.10*initial;spent=0.
    while hhi(work*prices,sector_matrix)>.25+1e-12:
        values=work*prices;sector_values=sector_matrix@values
        s=int(np.argmax(sector_values));indices=np.where(sector_matrix[s]>0)[0]
        candidates=sorted(indices,key=lambda i:(-values[i],i))
        accepted=False
        for i in candidates:
            if work[i]<=0 or spent+prices[i]>limit+1e-8:continue
            next_q=work.copy();next_q[i]-=1
            if next_q.sum()==0:continue
            if hhi(next_q*prices,sector_matrix)<hhi(work*prices,sector_matrix)-1e-12:
                work=next_q;requested[i]+=1;spent+=prices[i];accepted=True;break
        if not accepted:break
    if spent<500:requested[:]=0
    assert np.all(requested<=q) and float(requested@prices)<=limit+1e-7
    return requested
