"""Archive exact source/configuration, integrity manifests and scoped Git state."""
import json,shutil,subprocess,datetime
from pathlib import Path
import pandas as pd
from research.phase10.common import OUT,P9,sha,verify

def main():
    validation=json.loads((OUT/'VALIDATION.json').read_text());assert validation['status']=='passed' and validation['checks_failed']==0
    assert sha('research/phase10/validate.py')==validation['source_sha256']
    required=['FINAL_REPORT','EQUAL_CONSTRAINT_COMPARISON','PARETO_ANALYSIS','SCALABILITY','V3_V4_ANALYSIS','NOVELTY_ASSESSMENT','RESEARCH_CLAIMS','CONFERENCE_DRAFT']
    for name in required:assert (OUT/('PHASE10_'+name+'.md')).stat().st_size>1000
    assert len(list((OUT/'figures').glob('*.png')))==9 and len(list((OUT/'figures').glob('*.svg')))==9
    sources=[p for root in ['research/phase10','research/phase8'] for p in Path(root).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    sources += [Path(p) for p in ['research/phase9/allocators.py','research/phase9/reproduce.py','research/phase9/freeze.py','research/phase8/analysis/metrics.py','research/diagnostics/metrics.py','research/strategies.py','research/risk_metrics.py','research/investor_scenarios.py']]
    hashes={str(p):sha(p) for p in sorted(set(sources))}
    for p in set(sources):
        dest=OUT/'source_snapshot'/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
    (OUT/'SOURCE_HASHES.json').write_text(json.dumps(hashes,indent=2))
    (OUT/'GIT_STATUS_AFTER.txt').write_text(subprocess.check_output(['git','status','--short','--','.'],text=True))
    target_status=subprocess.check_output(['git','status','--short','--','research/phase10',str(OUT)],text=True)
    p9checked=sum(1 for p,h in json.loads((P9/'OUTPUT_HASHES.json').read_text()).items() if sha(P9/p)==h);assert p9checked==len(json.loads((P9/'OUTPUT_HASHES.json').read_text()))
    execution=json.loads((OUT/'EXPERIMENT_EXECUTION.json').read_text());scaling=json.loads((OUT/'SCALABILITY_EXECUTION.json').read_text());auth=json.loads((OUT/'AUTHORITY_EXECUTION.json').read_text());audit=pd.read_csv(OUT/'solver_certification_audit.csv');downgraded=audit[~audit.bound_reconciles]
    completion={'status':'complete','completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'primary_frozen_replays':27,'prior_allocation_reproductions':2160,'matched_states':432,'allocation_calls':execution['allocation_calls'],'scalability_cases':scaling['cases'],'timed_calls':scaling['timed_calls'],'warm_up_calls':scaling['warm_up_calls'],'memory_calls':scaling['memory_calls'],'authority_replays':auth['accounts'],'authority_lifecycle_checks':12,'exhaustive_tiny_comparisons':24,'validation_checks_passed':validation['checks_passed'],'validation_checks_failed':0,'solver_certificates_withheld':len(downgraded),'withheld_certificate_reason':'One raw solver-reported budget optimum differs from recomputed inclusive cost by INR0.004357; raw allocation is valid; no certified optimality claimed for that row','protected_files_unchanged':verify(),'phase9_output_hashes_verified':p9checked,'new_required_reports':8,'supplementary_case_report':True,'PNG_figures':9,'SVG_figures':9,'classification':'C — applied affordability-aware framework; strong original-baseline execution improvement, limited established methodological novelty','evidence_class':'exploratory benchmark research; not independent validation','V4_recommendation':'B — optional extended authority policy; V3 simpler research default','git_target_status':target_status,'staged':False,'committed':False,'limitations':['Restricted previously examined surviving-security universe','Current sectors/provider listing metadata and sparse action corroboration','Coarse observed frontier: lowest HHI cap.10; V3 below.10 in348 states','Reference resource limits; 160-candidate synthetic reference timeouts','One budget certificate withheld after numerical bound audit','Python-visible memory only; native solver RSS unavailable','CPU model/RAM inaccessible; no CPU isolation; initial background analysis overlap','Production persistence, atomicity and withdrawals not tested']}
    (OUT/'COMPLETION.json').write_text(json.dumps(completion,indent=2))
    pd.DataFrame([{'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ['OUTPUT_HASHES.json','ARTIFACT_INVENTORY.csv']]).to_csv(OUT/'ARTIFACT_INVENTORY.csv',index=False)
    (OUT/'OUTPUT_HASHES.json').write_text(json.dumps({str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='OUTPUT_HASHES.json'},indent=2))
    print(json.dumps(completion,indent=2))
if __name__=='__main__':main()
