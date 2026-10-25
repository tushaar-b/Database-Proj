"""Frozen Phase 10 protocol and input integrity. No production or prior-output writes."""
from pathlib import Path
import os,json,hashlib,subprocess,datetime
import numpy as np
OUT=Path(os.environ.get('INTELLIVEST_PHASE10_OUT','research/results/phase10-2026-10-25'))
P9=Path('research/results/phase9-2026-10-25')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def verify():
    h=json.loads((OUT/'PRESERVED_HASHES.json').read_text());bad=[p for p,v in h.items() if sha(p)!=v];assert not bad,bad;return len(h)
def freeze():
    OUT.mkdir(parents=True,exist_ok=True)
    if (OUT/'PROTOCOL.json').exists():verify();return
    for root in ['research/phase8','research/phase9','research/diagnostics','research/results/2026-10-23-run03','research/results/2026-10-24-diagnostics','research/results/phase8-2026-10-24',str(P9)]:assert Path(root).is_dir(),root
    files=[p for root in ['research','backend','frontend','db','etl'] for p in Path(root).rglob('*') if p.is_file() and not any(x in p.parts for x in ['__pycache__','node_modules','.pytest_cache']) and 'phase10' not in str(p)]
    (OUT/'PRESERVED_HASHES.json').write_text(json.dumps({str(p):sha(p) for p in sorted(files)},indent=2))
    for p,h in json.loads((P9/'OUTPUT_HASHES.json').read_text()).items():assert sha(P9/p)==h,p
    for p,h in json.loads((P9/'PRESERVED_HASHES.json').read_text()).items():assert sha(p)==h,p
    (OUT/'GIT_STATUS_BEFORE.txt').write_text(subprocess.check_output(['git','status','--short','--','.'],text=True))
    protocol={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'git_revision':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'seed':20261025,'historical_states':432,'primary_set':'F3: max three purchased tickers and max one purchased ticker per sector; existing holdings unrestricted in count','wide_sensitivity':'Fwide: no new-basket cardinality or distinct-sector limit','position_cap':.20,'sector_cap':.35,'fee':.001,'slippage':.0005,'HHI_caps':[None,.35,.25,.20,.15,.10],'reference_objectives':['utility','budget'],'wide_objectives':['utility','budget'],'joint_preferences':{'utility':[1,0,0],'moderate_utility':[.75,.25,0],'balanced_UD':[.5,.5,0],'moderate_diversification':[.25,.75,0],'diversification':[0,1,0],'budget':[0,0,1],'balanced_UDB':[1/3,1/3,1/3]},'objective_component_order':['U/B','1-HHI','inclusive_cost/B'],'similar_HHI_tolerance':.01,'similar_utility_tolerance':.02,'dominance_tolerance':1e-8,'solver_seconds_historical':1.5,'solver_seconds_scalability':.5,'max_outer_cuts':100,'solver_mip_gap':0.,'bootstrap_block':20,'bootstrap_draws':2000,'bootstrap_seed':20261024,'synthetic_seeds':[101,202,303],'scalability_sizes':[10,20,40,80,160],'scalability_repetitions':3,'scalability_design':'one factor at a time around n40 budget10000 holdings5 sectors10 position.20 sector.35 dispersion1; budgets1000/100000 holdings0/20 sectors3/16 position.10/.30 sector.20/.50 dispersion.01/2; 3 seeds','memory':'separate tracemalloc Python-visible peak, not solver native RSS; matrix storage separately','classification':'exploratory; all historical periods exposed','normalization':'ordinal positive utility weighted nominal rupees / fee-inclusive batch budget; D=1-posttrade equity-only sector HHI; K=inclusive cost/B; no outcome-based scaling','matching':'all candidate comparisons paired by exact pretrade state, universe, cash, authority, costs and guard'}
    (OUT/'PROTOCOL.json').write_text(json.dumps(protocol,indent=2));print({'frozen_files':verify(),'phase9_output_hashes_verified':True})

def load_states():
    import pandas as pd
    z=np.load(OUT/'states.npz');meta=pd.read_csv(OUT/'matched_states.csv');pools=json.loads((OUT/'candidate_pools.json').read_text());states=[]
    for j,r in meta.iterrows():
        states.append({'id':r.state_id,'scenario':r.scenario,'date':r.date,'tier':r.tier,'q':z['holdings'][j],'p':z['prices'][j],'cov':z['covariances'][j],'cash':r.cash,'authority':r.authority,'budget':r.budget,'feedback':(r.multiplier,tuple(json.loads(r.blocked_sectors))),'pool':pools[j],'tickers':list(z['tickers']),'sectors':list(z['sectors']),'S':z['sector_matrix'],'poscap':.2,'sectorcap':.35})
    return states
if __name__=='__main__':freeze()
