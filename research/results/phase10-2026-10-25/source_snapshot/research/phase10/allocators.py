"""Phase 10 comparators. V3/V4 source unchanged. Exact guard-aware integer reference."""
import time,types
from types import SimpleNamespace
import numpy as np,pandas as pd
from scipy.optimize import milp,Bounds,LinearConstraint
from research.phase8.policies.construction import Guard,hhi,build as frozen,V3,V4

class ParameterGuard(Guard):
    """Only synthetic cap sensitivities use parameters other than frozen .20/.35."""
    def __init__(self,*args,poscap=.2,sectorcap=.35):
        super().__init__(*args);self.pc=poscap;self.sc=sectorcap
    def allowed(self,a,cost,strict=False):
        if self.pc==.2 and self.sc==.35:return super().allowed(a,cost,strict)
        v=(self.q+a)*self.p;E=self.cash-cost+v.sum()
        if cost>self.cash+1e-7:return False,'cash'
        if np.any(v>np.maximum(self.pc*E,self.base_values)+1e-7):return False,'position_limit'
        if np.any(self.sectors@v>np.maximum(self.sc*E,self.base_sectors)+1e-7):return False,'sector_limit'
        H=hhi(v,self.sectors)
        if np.isfinite(self.base_hhi) and H>max(.25,self.base_hhi)+1e-10:return False,'hhi_limit'
        w=v/E;vol=np.sqrt(max(0.,w@self.cov@w))
        if vol>max(.03,self.base_vol)+1e-10:return False,'volatility_limit'
        if 1.645*vol>max(.10,1.645*self.base_vol)+1e-10:return False,'var_limit'
        return True,''

def context(st):
    p=st['p'];q=st['q'];S=st['S'];tickers=st['tickers'];blocked=set(st['feedback'][1]);valid=[r for r in st['pool'] if r['sector_name'] not in blocked]
    index={t:i for i,t in enumerate(tickers)};ids=[index[r['ticker_symbol']] for r in valid]
    rank=sorted(valid,key=lambda r:(-r['selection_score'],r['ticker_symbol']));utility=np.zeros(len(q))
    for j,r in enumerate(rank):utility[index[r['ticker_symbol']]]=p[index[r['ticker_symbol']]]*(len(rank)-j)/max(1,len(rank))
    guard=ParameterGuard(q,st['cash'],p,st['cov'],S,poscap=st['poscap'],sectorcap=st['sectorcap'])
    unit=p*1.0005*1.001
    return SimpleNamespace(st=st,p=p,q=q,S=S,n=len(q),ids=ids,rank=[index[r['ticker_symbol']] for r in rank],utility=utility,unit=unit,guard=guard,B=st['budget'],index=index,sector=np.argmax(S,axis=0))

def metrics(st,a,mode='F3',cap=None):
    c=context(st);a=np.asarray(a);cost=float(a@c.unit);v=(c.q+a)*c.p;stock=float(v.sum());H=hhi(v,c.S);E=st['cash']-cost+stock
    safe,reason=c.guard.allowed(a,cost)
    valid=bool(safe and cost<=c.B+1e-7 and (a>=0).all() and np.all(a==np.rint(a)) and all(i in c.ids for i in np.where(a>0)[0]))
    if mode=='F3':valid &= (np.count_nonzero(a)<=3 and (c.S@(a>0)).max(initial=0)<=1)
    if cap is not None and np.isfinite(H):valid &= H<=cap+1e-9
    return {'valid':bool(valid),'guard_reason':reason,'purchase':bool(a.any()),'cost':cost,'budget_fill':cost/c.B if c.B else np.nan,'U':float(c.utility@a),'U_norm':float(c.utility@a/c.B) if c.B else np.nan,'HHI':H,'D':1-H if np.isfinite(H) else np.nan,'purchase_positions':int(np.count_nonzero(a)),'post_positions':int(np.count_nonzero(c.q+a)),'max_sector_equity_weight':float((c.S@v).max()/stock) if stock else np.nan,'max_position_account_weight':float(v.max()/E),'max_sector_account_weight':float((c.S@v).max()/E),'post_account_volatility':float(np.sqrt(max(0.,(v/E)@st['cov']@(v/E))))}

def heuristic(st,method='V3',mode='F3'):
    c=context(st);rejected=0
    if method in ['V3','V4','V1']:
        from research.phase8.policies.construction import V1
        policy={'V3':V3,'V4':V4,'V1':V1}[method]
        m=SimpleNamespace(prices=c.p[None,:],cov30=st['cov'][None,:,:],sector_matrix=c.S,tickers=st['tickers'],sectors=st['sectors'],index=c.index,sector_index={s:i for i,s in enumerate(st['sectors'])})
        fn=frozen
        if st['poscap']!=.2 or st['sectorcap']!=.35:
            fn=types.FunctionType(frozen.__code__,{**frozen.__globals__,'Guard':lambda *args:ParameterGuard(*args,poscap=st['poscap'],sectorcap=st['sectorcap'])},argdefs=frozen.__defaults__)
        a,info=fn(st['pool'],c.q,st['cash'],st['authority'],st['feedback'],policy,m,0)
        return a,{'solver_status':'not_applicable','gap':np.nan,'rejected_proposals':sum(info['guard_reasons'].values()),'affordable_count':info['affordable_count']}
    a=np.zeros(c.n,dtype=int)
    # Identical one-share witnesses are measured for the greedy comparator as well.
    affordable=0
    for i in c.ids:
        t=a.copy();t[i]=1
        affordable+=int(t@c.unit<=c.B+1e-7 and c.guard.allowed(t,float(t@c.unit))[0])
    while True:
        accepted=False
        for i in c.rank:
            if mode=='F3' and a[i]==0 and (np.count_nonzero(a)>=3 or (c.S@(a>0))[c.sector[i]]>0):continue
            t=a.copy();t[i]+=1;cost=float(t@c.unit)
            if cost<=c.B+1e-7 and c.guard.allowed(t,cost)[0]:a=t;accepted=True;break
            rejected+=1
        if not accepted:break
    return a,{'solver_status':'not_applicable','gap':np.nan,'rejected_proposals':rejected,'affordable_count':affordable}

def reference(st,mode='F3',objective='utility',cap=None,seconds=1.5,max_iterations=100):
    """MILP with binary purchase disjunctions and valid SOC supporting cuts.

    Certifies a linear objective only when the outer solution passes the full guard
    and the MILP status is optimal. Resource limits retain an explicitly feasible
    incumbent. Nonlinear scalarizations and global Pareto optimality are not claimed.
    """
    started=time.perf_counter();c=context(st);n=c.n;v=c.q*c.p;E=st['cash']+v.sum();fric=c.unit-c.p;pc=st['poscap'];sc=st['sectorcap'];Fmax=c.B*float(np.max(fric/c.unit));N=2*n
    ub=np.zeros(n);ub[c.ids]=np.floor((c.B+1e-8)/c.unit[c.ids]);ub=np.maximum(ub,0)
    A=[];b=[];lb=[]
    def row(x,rhs,lower=-np.inf):A.append(x);b.append(rhs);lb.append(lower)
    r=np.zeros(N);r[:n]=c.unit;row(r,c.B)
    for i in range(n):
        r=np.zeros(N);r[i]=1;r[n+i]=-ub[i];row(r,0)
        r=np.zeros(N);r[n+i]=1;r[i]=-1;row(r,0)
        M=max(0.,v[i]-pc*E+pc*Fmax)+1e-8
        r=np.zeros(N);r[:n]=pc*fric;r[i]+=c.p[i];r[n+i]=M;row(r,pc*E-v[i]+M)
    for sector in c.S:
        sv=float(sector@v);M=max(0.,sv-sc*E+sc*Fmax)+1e-8
        # If any ticker in the sector is purchased its sector ceiling applies;
        # otherwise unchanged grandfathered holdings remain allowed.
        for i in np.where(sector>0)[0]:
            r=np.zeros(N);r[:n]=sector*c.p+sc*fric;r[n+i]=M;row(r,sc*E-sv+M)
        if mode=='F3':r=np.zeros(N);r[n:]=sector;row(r,1)
    if mode=='F3':r=np.zeros(N);r[n:]=1;row(r,3)
    # Search positive purchases only. Zero remains a valid fallback, but is not an
    # invented diversified solution in empty states.
    r=np.zeros(N);r[:n]=1;row(r,np.inf,1.)
    baseH=c.guard.base_hhi;hlimit=max(.25,baseH) if np.isfinite(baseH) else 1.
    if cap is not None:hlimit=min(hlimit,cap)
    eig,U=np.linalg.eigh(st['cov']);L=np.diag(np.sqrt(np.maximum(eig,0)))@U.T;vol_limit=max(.03,c.guard.base_vol)
    coefficient=c.utility if objective=='utility' else c.unit
    target=np.r_[-coefficient,np.zeros(n)]
    best=np.zeros(n,dtype=int);best_score=-np.inf;status='iteration_limit';gap=np.nan;bound=np.nan;rejected=0;solver_status=-1;nodes=0
    def add_cuts(a):
        nonlocal rejected
        after=v+a*c.p;newE=E-float(a@fric);z=c.S@after;norm=np.linalg.norm(z);added=False
        if norm>np.sqrt(hlimit)*after.sum()+1e-10:
            normal=(z/norm)@c.S-np.sqrt(hlimit)*np.ones(n);r=np.zeros(N);r[:n]=normal*c.p;row(r,-normal@v);added=True
        z=L@after;norm=np.linalg.norm(z)
        if norm>vol_limit*newE+1e-10:
            normal=(z/norm)@L;r=np.zeros(N);r[:n]=normal*c.p+vol_limit*fric;row(r,vol_limit*E-normal@v);added=True
        return added
    if np.any(v):add_cuts(np.zeros(n))
    iterations=0
    for iteration in range(max_iterations):
        iterations=iteration+1;remaining=seconds-(time.perf_counter()-started)
        if remaining<=0:status='time_limit';break
        result=milp(target,integrality=np.ones(N),bounds=Bounds(np.zeros(N),np.r_[ub,np.ones(n)]),constraints=LinearConstraint(np.asarray(A),np.asarray(lb),np.asarray(b)),options={'time_limit':remaining,'mip_rel_gap':0.})
        solver_status=int(result.status);nodes+=int(getattr(result,'mip_node_count',0) or 0)
        if result.x is None:
            status='infeasible_positive_purchase' if result.status==2 else 'solver_'+str(result.status);break
        a=np.rint(result.x[:n]).astype(int);cost=float(a@c.unit);safe,why=c.guard.allowed(a,cost)
        h=hhi(v+a*c.p,c.S);safe=bool(safe and cost<=c.B+1e-7 and (not np.isfinite(h) or h<=hlimit+1e-9))
        bound=-float(result.mip_dual_bound) if getattr(result,'mip_dual_bound',None) is not None else np.nan;gap=float(result.mip_gap) if getattr(result,'mip_gap',None) is not None else np.nan
        if safe:
            value=float(coefficient@a)
            if value>best_score:best=a;best_score=value
            status='optimal_full_guard' if result.status==0 else 'feasible_limit';break
        rejected+=1
        if not add_cuts(a):status='numerical_guard_rejection_'+why;break
    if not best.any() and status not in ['infeasible_positive_purchase']:gap=np.nan
    if status=='infeasible_positive_purchase' and best.any():status='retained_feasible_incumbent'
    return best,{'solver_status':status,'raw_solver_status':solver_status,'gap':gap,'linear_objective_bound':bound,'solver_iterations':iterations,'solver_nodes':nodes,'rejected_proposals':rejected,'reference_objective':objective,'HHI_target':cap,'solver_seconds_limit':seconds}
