"""Transparent Phase 9 allocators, no changes to frozen construction source."""
import time
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from research.phase8.policies.construction import build as frozen,Guard,hhi
RUNTIMES=[]

def objective(pool,added,prices,index):
    # Positive ordinal utility per rupee; invariant to raw score scale.
    ranked=sorted(pool,key=lambda r:(-r['selection_score'],r['ticker_symbol']))
    return float(sum((len(ranked)-j)/max(1,len(ranked))*prices[index[r['ticker_symbol']]]*added[index[r['ticker_symbol']]] for j,r in enumerate(ranked)))

def integer_reference(valid,q,cash,budget,market,di,unit,guard):
    n=len(q);p=market.prices[di];v=q*p;E=cash+v.sum();friction=unit-p
    ids=[market.index[r['ticker_symbol']] for r in valid]
    ub=np.zeros(n);ub[ids]=np.floor(budget/unit[ids]+1e-9)
    A=[unit.copy()];b=[budget]
    # Existing overweight positions and sectors cannot be enlarged.
    for i in range(n):
        if v[i]>=.2*E:ub[i]=0
        else:
            row=.2*friction.copy();row[i]+=p[i];A.append(row);b.append(.2*E-v[i])
    for s in market.sector_matrix:
        base=s@v
        if base>=.35*E:
            ub[s>0]=0
        else:A.append(s*p+.35*friction);b.append(.35*E-base)
    util=np.zeros(n)
    for j,r in enumerate(sorted(valid,key=lambda r:(-r['selection_score'],r['ticker_symbol']))):util[market.index[r['ticker_symbol']]]=p[market.index[r['ticker_symbol']]]*(len(valid)-j)/max(1,len(valid))
    # SOC constraints are enforced by valid supporting hyperplanes (outer approximation).
    cov=market.cov30[di];ev,U=np.linalg.eigh(cov);L=np.diag(np.sqrt(np.maximum(ev,0)))@U.T
    vol_limit=max(.03,guard.base_vol)
    hlim=max(.25,guard.base_hhi) if np.isfinite(guard.base_hhi) else None
    started=time.perf_counter();status='iteration_limit';best=np.zeros(n,dtype=int);bound=np.nan
    for iteration in range(80):
        remain=3-(time.perf_counter()-started)
        if remain<=0:status='time_limit';break
        result=milp(-util,integrality=np.ones(n),bounds=Bounds(np.zeros(n),ub),constraints=LinearConstraint(np.array(A),-np.inf,np.array(b)),options={'time_limit':remain,'mip_rel_gap':0.0})
        if result.x is None:status='solver_'+str(result.status);break
        a=np.rint(result.x).astype(int);cost=float(a@unit)
        bound=-float(result.mip_dual_bound) if result.mip_dual_bound is not None else np.nan
        safe,why=guard.allowed(a,cost)
        if safe:
            best=a;status='optimal' if result.status==0 else 'feasible_time_limit';break
        after=v+a*p;newE=E-a@friction;added_cut=False
        if hlim is not None:
            z=market.sector_matrix@after;norm=np.linalg.norm(z)
            if norm>np.sqrt(hlim)*after.sum()+1e-10:
                normal=(z/norm)@market.sector_matrix-np.sqrt(hlim)*np.ones(n)
                A.append(normal*p);b.append(-normal@v);added_cut=True
        z=L@after;norm=np.linalg.norm(z)
        if norm>vol_limit*newE+1e-10:
            normal=(z/norm)@L
            A.append(normal*p+vol_limit*friction);b.append(vol_limit*E-normal@v);added_cut=True
        if not added_cut:status='numerical_guard_rejection_'+why;break
    return best,{'solver_status':status,'solver_bound':bound,'solver_iterations':iteration+1}

def build(pool,q,cash,authority,feedback,policy,market,di,fee=.001,slippage=.0005,override=None):
    start=time.perf_counter();name=policy.name;algorithm=name.split('_')[0]
    neutral=name.startswith('NEUTRAL')
    if neutral:pool=[{**r,'selection_score':0.,'size_weight':1.} for r in pool]
    if algorithm not in {'GREEDY','EQUAL','SIP','MILP'}:
        a,info=frozen(pool,q,cash,authority,feedback,policy,market,di,fee,slippage,override)
    else:
        # Frozen eligibility, authority multiplier and single-share feasibility witness.
        _,info=frozen(pool,q,cash,authority,feedback,policy,market,di,fee,slippage,override)
        valid=[r for r in pool if r['ticker_symbol'] in set(info['eligible'])]
        p=market.prices[di];unit=p*(1+slippage)*(1+fee);budget=info['budget'];a=np.zeros(len(q),dtype=int)
        guard=Guard(q,cash,p,market.cov30[di],market.sector_matrix)
        extra={}
        if algorithm=='MILP' and valid and budget>0:a,extra=integer_reference(valid,q,cash,budget,market,di,unit,guard)
        else:
            ranked=sorted(valid,key=lambda r:(-r['selection_score'],r['ticker_symbol']))
            ids=[market.index[r['ticker_symbol']] for r in ranked]
            if algorithm=='SIP':
                # Fixed lexicographic representative per sector, rotate by calendar month.
                reps={}
                for r in sorted(valid,key=lambda r:r['ticker_symbol']):reps.setdefault(r['sector_name'],market.index[r['ticker_symbol']])
                basket=[reps[s] for s in sorted(reps)];month=market.dates[di].year*12+market.dates[di].month
                ids=[basket[(month+j)%len(basket)] for j in range(min(3,len(basket)))] if basket else []
            while ids:
                order=sorted(ids,key=lambda i:((q[i]+a[i])*p[i],market.tickers[i])) if algorithm=='EQUAL' else ids
                changed=False
                for i in order:
                    trial=a.copy();trial[i]+=1;cost=float(trial@unit)
                    if cost<=budget+1e-7 and guard.allowed(trial,cost)[0]:a=trial;changed=True;break
                if not changed:break
        info['selected']=[market.tickers[i] for i in np.where(a>0)[0]];info.update(extra)
        info['negative_momentum_selected']=sum(bool(r.get('strong_negative')) for r in valid if a[market.index[r['ticker_symbol']]]>0)
    elapsed=time.perf_counter()-start
    RUNTIMES.append({'policy':name,'date':str(market.dates[di].date()),'candidate_count':len(pool),'eligible_count':info['eligible_count'],'seconds':elapsed,'budget':info['budget'],'objective':objective(pool,a,market.prices[di],market.index),'proposed_cost':float(a@(market.prices[di]*(1+slippage)*(1+fee))),'override':override is not None,**{k:v for k,v in info.items() if k.startswith('solver_')}})
    return a,info
