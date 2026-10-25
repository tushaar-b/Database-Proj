"""Instrument unchanged authority transitions and execute adverse lifecycle checks."""
import json,time
from dataclasses import replace
import numpy as np,pandas as pd
from research.phase10.common import OUT,P9
from research.phase9.reproduce import inputs
from research.phase8.experiments import engine
from research.phase8.policies.authority import Authority
from research.phase8.policies.construction import V3,V4,build as frozen
from research.phase8.analysis.metrics import summarize
from research.investor_scenarios import scenarios

def main():
    cfg,m,cache=inputs();events=[];accounts=[];raw=[];current={}
    class Instrumented(Authority):
        def record(self,operation,before,seconds,day):
            events.append({**current,'date':str(pd.Timestamp(day).date()),'operation':operation,'seconds':seconds,'lots_before':before,'lots_after':len(self.lots),'id_count':len(self.ids),'spend_id_count':len(self.spent_ids),'balance':self.balance,'grants':self.grants,'spent':self.spent_external,'expired':self.expired,'revoked':self.revoked})
        def month(self,day,buffer,tier):
            before=len(self.lots);start=time.perf_counter();r=super().month(day,buffer,tier);self.record('month_review',before,time.perf_counter()-start,day);return r
        def spend(self,amount,day,identifier):
            before=len(self.lots);start=time.perf_counter();r=super().spend(amount,day,identifier);self.record('spend',before,time.perf_counter()-start,day);return r
    engine.Authority=Instrumented;engine.build=frozen
    for kind in ['primary','household_deterioration']:
        for s in scenarios():
            if kind!='primary' and s.name not in ['low_conservative','medium_moderate','high_aggressive']:continue
            for policy in [V3,V4]:
                current.update(scenario=s.name,policy=policy.name,kind=kind);f=engine.run(m,cache,s,policy,'2022-01-01','2025-12-31',shock=kind!='primary');accounts.append({**current,**summarize(f)})
                raw.extend([{**current,**event} for event in f['authority_events'].to_dict('records')])
    engine.Authority=Authority
    pd.DataFrame(raw).to_csv(OUT/'authority_ledger_events.csv',index=False)
    pd.DataFrame(events).to_csv(OUT/'authority_transitions.csv',index=False);pd.DataFrame(accounts).to_csv(OUT/'authority_account_outcomes.csv',index=False)
    s=pd.DataFrame(accounts);paired=[]
    for (kind,scenario),g in s.groupby(['kind','scenario']):
        x=g.set_index('policy');paired.append({'kind':kind,'scenario':scenario,**{c:float(x.loc['V4',c]-x.loc['V3',c]) for c in ['authorized_budget_utilization','external_authority_spent','mean_invested_allocation','annualized_return','annualized_volatility','cvar95','maximum_drawdown','turnover','transaction_fees','slippage_cost','expired_authority','revoked_authority']}})
    pd.DataFrame(paired).to_csv(OUT/'v3_v4_differences.csv',index=False)
    tests=[]
    def passed(name,fn):
        fn();tests.append({'scenario':name,'status':'passed'})
    def rejects(fn):
        try:fn()
        except AssertionError:return
        raise AssertionError('Expected rejected invalid transition')
    day=pd.Timestamp('2022-01-03')
    def empty():a=Authority(True);assert a.balance==0 and a.grants==0
    passed('No initial savings approval',empty)
    def duplicate():
        a=Authority(True);a.month(day,1000,.5);rejects(lambda:a.month(day,1000,.5))
    passed('Duplicate month approval rejected',duplicate)
    def duplicate_spend():
        a=Authority(True);a.month(day,1000,.5);a.spend(100,day,'one');rejects(lambda:a.spend(100,day,'one'))
    passed('Duplicate spending ID rejected',duplicate_spend)
    def overspend():
        a=Authority(True);a.month(day,1000,.5);rejects(lambda:a.spend(501,day,'too_much'))
    passed('Authority overspending rejected',overspend)
    def expiry():
        a=Authority(True);a.month(day,1000,.5)
        for k in range(1,12):a.month(day+pd.DateOffset(months=k),1000,.5)
        assert a.expired==0 and len(a.lots)==12;a.month(day+pd.DateOffset(months=12),1000,.5);assert a.expired==500 and len(a.lots)==12;a.check()
    passed('Eleven versus twelve month expiry boundary and lot bound',expiry)
    def deterioration():
        a=Authority(True);a.month(day,1000,.5);a.month(day+pd.DateOffset(months=1),500,.5);assert a.revoked==500 and a.balance==250;a.check()
    passed('Reduced household capacity revokes all carry before fresh approval',deterioration)
    def fifo():
        a=Authority(True);a.month(day,1000,.5);a.month(day+pd.DateOffset(months=1),1000,.5);a.spend(700,day+pd.DateOffset(months=1),'one');assert len(a.lots)==1 and a.balance==300 and a.lots[0]['day'].month==2;a.check()
    passed('FIFO spending crosses lots exactly once',fifo)
    def monthly():
        a=Authority(False);a.month(day,1000,.5);a.month(day+pd.DateOffset(months=1),1000,.5);assert a.expired==500 and a.balance==500;a.check()
    passed('Monthly-only expiry has no carry',monthly)
    def revoke():
        a=Authority(True);a.month(day,1000,.5);a.revoke(200,day,'explicit_cash_withdrawal_review');assert a.balance==300 and a.revoked==200;a.check()
    passed('Explicit authority revocation conservation primitive',revoke)
    def cash():
        a=Authority(True);a.month(day,1000,.5);rejects(lambda:a.check(499))
    passed('Authority exceeding actual brokerage cash detected',cash)
    def recycled():
        a=Authority(True);a.recycle(100,day,'sale');rejects(lambda:a.recycle(100,day,'sale'));a.check()
    passed('Duplicate recycled grant rejected; sale authority outside primary policy',recycled)
    def boundary():
        a=Authority(True);a.month(day,1000,.5);a.spend(500,day,'all');assert a.balance==0;a.check()
    passed('Exact full approval spend conserves zero remainder',boundary)
    pd.DataFrame(tests).to_csv(OUT/'authority_lifecycle_checks.csv',index=False)
    (OUT/'AUTHORITY_EXECUTION.json').write_text(json.dumps({'accounts':len(accounts),'primary_accounts':18,'shock_accounts':6,'transitions':len(events),'lifecycle_checks':len(tests),'passed':len(tests),'failed':0},indent=2));print({'accounts':len(accounts),'checks':len(tests)})
if __name__=='__main__':main()
