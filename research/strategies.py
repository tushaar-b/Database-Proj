"""Pure policy adapter. Reuse actual ranking with a historical observation clock."""
from contextlib import contextmanager
from datetime import datetime
import ast
from pathlib import Path
import numpy as np
from backend import market_trends as trends

POLICIES = ('Affordability Only','Risk Only','No Feedback','Full IntelliVest')
CAPACITY = {'CONSERVATIVE':.25,'MODERATE':.5,'AGGRESSIVE':.75}


@contextmanager
def historical_clock(day):
    """score_history lacks as_of; temporarily scope its clock, single-thread only."""
    old = trends.datetime
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            return datetime.combine(day, datetime.min.time()).replace(hour=16, tzinfo=tz)
    trends.datetime = Clock
    try:
        yield
    finally:
        trends.datetime = old


# Compile only the application's pure selector, without importing mutation routes.
source = Path(__file__).resolve().parents[1]/'backend/routers/recommendations.py'
tree = ast.parse(source.read_text())
selector = next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_select_candidates')
namespace = {}
exec(compile(ast.Module(body=[selector],type_ignores=[]),str(source),'exec'),namespace)
select_candidates = namespace['_select_candidates']


def candidates(dataset, dates, day, tier, momentum=True):
    policy = trends.momentum_policy()
    if not momentum:
        policy = {**policy,'tier_weights':dict.fromkeys(CAPACITY,0.)}
    result=[]
    with historical_clock(day.date()):
        for ticker,g in dataset.groupby('ticker',sort=True):
            history = g[g.date<=day].tail(253)
            if history.empty or history.iloc[-1].date != day:
                continue
            # Require adjacent common-calendar observations, never bridge gaps.
            expected = dates[dates<=day][-len(history):]
            if list(history.date) != list(expected):
                continue
            series={'rows':[{'trade_date':r.date.date(),'adjusted_close':r.adjusted_close} for r in history.itertuples()],
                    'source':'yfinance','status':'available','quality':{}}
            scored=trends.score_history(series,tier,1-CAPACITY[tier],policy)
            if scored is None:
                continue
            result.append({'ticker_symbol':ticker,'sector_name':g.iloc[0].sector,
                'selection_score':scored['selection_score'],'baseline_score':scored['baseline_score'],
                'size_weight':1/scored['daily_volatility']**(1-CAPACITY[tier]),
                'nominal_price':float(history.iloc[-1].nominal_close),
                'strong_negative':scored['trend']['classification']=='Strong Negative Momentum',
                'history_through':str(scored['history_through']),'input_price_hash':scored['input_price_hash']})
    return result


def propose(pool, holdings, sector_weights, policy, scenario, cash, feedback, fixed_policy=(1.,())):
    risk = policy!='Affordability Only'
    mult,blocked = feedback if policy=='Full IntelliVest' else fixed_policy if risk else (1.,())
    budget = (cash if policy=='Risk Only' else scenario.buffer)*CAPACITY[scenario.tier]*mult
    # Match ROUND_FLOOR cent budgets and per-candidate allocations.
    budget = np.floor(budget*100+1e-8)/100
    available=[{**x,'sector_weight':sector_weights.get(x['sector_name'],0.) if risk else 0.}
               for x in pool if holdings.get(x['ticker_symbol'],0)==0 and x['sector_name'] not in blocked]
    selected=select_candidates(available) if budget>0 else []
    total=sum(x['size_weight'] for x in selected)
    orders=[]
    for x in selected:
        allocation=np.floor(budget*x['size_weight']/total*100+1e-8)/100
        quantity=int(np.floor(allocation/x['nominal_price']))
        if quantity:
            orders.append({**x,'quantity':quantity,'proposed_notional':quantity*x['nominal_price']})
    return budget,selected,orders


def feedback_policy(flags,sector_weights):
    reducing=int(flags[0])+int(flags[1])
    multiplier=(1.,.5,.25)[reducing]
    blocked=()
    if flags[2] and sector_weights:
        blocked=(sorted(sector_weights,key=lambda s:(-sector_weights[s],s))[0],)
    return multiplier,blocked
