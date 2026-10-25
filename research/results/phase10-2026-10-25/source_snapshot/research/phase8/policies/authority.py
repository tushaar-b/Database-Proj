"""FIFO authorization ledger; cash and authorization are separate conserved stocks."""
from dataclasses import dataclass,field
import math


@dataclass
class Authority:
    carry: bool
    lots: list=field(default_factory=list)
    grants: float=0.
    recycled_grants: float=0.
    spent_external: float=0.
    spent_recycled: float=0.
    expired: float=0.
    revoked: float=0.
    previous_buffer: float|None=None
    ids: set=field(default_factory=set)
    spent_ids: set=field(default_factory=set)
    events: list=field(default_factory=list)

    @property
    def balance(self):return sum(x['remaining'] for x in self.lots)

    def check(self,cash=None):
        assert abs(self.grants+self.recycled_grants-self.spent_external-self.spent_recycled-self.expired-self.revoked-self.balance)<1e-5
        assert min([self.balance]+[x['remaining'] for x in self.lots])>=-1e-7
        if cash is not None:assert self.balance<=cash+1e-5

    def revoke(self,amount,day,reason):
        amount=min(max(amount,0.),self.balance);remaining=amount
        for lot in self.lots:
            taken=min(remaining,lot['remaining']);lot['remaining']-=taken;remaining-=taken
        self.revoked+=amount
        self.lots=[x for x in self.lots if x['remaining']>1e-8]
        self.events.append({'date':day,'action':'revoke','amount':amount,'reason':reason,'balance':self.balance})
        self.check()

    def month(self,day,buffer,tier):
        key=f'{day.year}-{day.month:02d}'
        assert key not in self.ids,'duplicate monthly approval'
        self.ids.add(key)
        if self.previous_buffer is not None and buffer<self.previous_buffer-1e-8:
            self.revoke(self.balance,day,'household_capacity_deterioration')
        expired=[]
        for lot in self.lots:
            age=(day.year-lot['day'].year)*12+day.month-lot['day'].month
            if not self.carry or age>=12:expired.append(lot)
        for lot in expired:
            self.expired+=lot['remaining']
            self.events.append({'date':day,'action':'expire','amount':lot['remaining'],'reason':'monthly_reset' if not self.carry else '12_month_review'})
        self.lots=[x for x in self.lots if x not in expired]
        grant=math.floor(max(0.,buffer)*tier*100+1e-8)/100
        self.grants+=grant
        if grant:self.lots.append({'day':day,'remaining':grant,'origin':'external'})
        self.previous_buffer=buffer
        self.events.append({'date':day,'action':'approve','amount':grant,'reason':'reserve_protected_monthly_quota','balance':self.balance})
        self.check();return grant

    def recycle(self,amount,day,identifier):
        assert identifier not in self.ids,'duplicate recycled proceeds'
        self.ids.add(identifier)
        if amount>0:self.lots.append({'day':day,'remaining':amount,'origin':'recycled'})
        self.recycled_grants+=amount
        self.events.append({'date':day,'action':'recycle','amount':amount,'reason':identifier,'balance':self.balance})
        self.check()

    def spend(self,amount,day,identifier):
        assert identifier not in self.spent_ids,'duplicate purchase debit'
        assert 0<=amount<=self.balance+1e-7,(amount,self.balance)
        self.spent_ids.add(identifier);remaining=amount;external=0.;recycled=0.
        for lot in self.lots:
            take=min(remaining,lot['remaining']);lot['remaining']-=take;remaining-=take
            if lot['origin']=='external':external+=take
            else:recycled+=take
        assert remaining<1e-6
        self.spent_external+=external;self.spent_recycled+=recycled
        self.lots=[x for x in self.lots if x['remaining']>1e-8]
        self.events.append({'date':day,'action':'spend','amount':amount,'external':external,'recycled':recycled,'reason':identifier,'balance':self.balance})
        self.check();return external,recycled
