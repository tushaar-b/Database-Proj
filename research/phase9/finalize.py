"""Finalize source/archive integrity after all numerical checks and report generation."""
import json,shutil,subprocess,platform,sys,importlib.metadata
from pathlib import Path
import pandas as pd
from research.phase9.freeze import OUT,sha,verify

def main():
    result=json.loads((OUT/'VALIDATION.json').read_text());assert result['status']=='passed'
    assert sha('research/phase9/validate.py')==result['validator_sha256'],'Latest validator has not passed'
    sources=[p for root in ['research/phase9','research/phase8'] for p in Path(root).rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    sources += [Path(p) for p in ['research/strategies.py','research/risk_metrics.py','research/investor_scenarios.py','research/historical_replay.py','research/diagnostics/metrics.py']]
    hashes={str(p):sha(p) for p in sources}
    for p in sources:
        dst=OUT/'source_snapshot'/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
    (OUT/'FINAL_SOURCE_HASHES.json').write_text(json.dumps(hashes,indent=2))
    env={'python':sys.version,'platform':platform.platform(),'machine':platform.machine(),'processor':platform.processor(),'CPU_brand_and_RAM':'sysctl access denied in sandbox; model/RAM not independently recorded','versions':{k:importlib.metadata.version(k) for k in ['numpy','pandas','scipy','yfinance']},'plotting_versions':{},'hardware_timing_scope':'single local process; no CPU pinning, warm caches; controlled repeat samples retained'}
    for name,path in [('matplotlib','/private/tmp/intellivest-phase9-deps'),('xlrd','/private/tmp/intellivest-phase9-extra')]:
        dist=next(d for d in importlib.metadata.distributions(path=[path]) if d.metadata['Name'].lower()==name);env['plotting_versions'][name]=dist.version
    (OUT/'ENVIRONMENT.json').write_text(json.dumps(env,indent=2))
    dataset='research/data/2026-10-23/research_quotes.csv';etf=OUT/'benchmark_sources/NIFTYBEES_normalized.csv'
    rows=[{'dataset':'equity_original','path':dataset,'sha256':sha(dataset),'source':'Yahoo Finance via yfinance; six-date NSE spot corroboration','adjustment':'Adjusted close for score/returns; split reconstructed nominal execution; explicit ex-date dividends','securities':40,'observations':57400,'first':'2021-01-01','last':'2026-10-22','independent_holdout':False},{'dataset':'NIFTYBEES_normalized','path':str(etf),'sha256':sha(etf),'source':'Yahoo/yfinance plus one separately documented official NSE missing-bar correction','adjustment':'No reported actions; adjusted close equals nominal close; six-date NSE corroboration','securities':1,'observations':1236,'first':'2021-01-01','last':'2025-12-31','independent_holdout':False},{'dataset':'NIFTY50_TRI','source':'Official niftyindices endpoint HTTP401','observations':0,'independent_holdout':False,'adjustment':'Unavailable; never substituted by price index'},{'dataset':'historical_constituent_events','path':str(OUT/'benchmark_sources/membership.raw'),'sha256':sha(OUT/'benchmark_sources/membership.raw'),'source':'Official NSE IndexInclExcl.xls','observations':196,'first':'1996-09-18','last':'2020-07-31','independent_holdout':False,'adjustment':'Nifty 50 sheet event coverage only; insufficient for 2022–2025 PIT membership'}]
    pd.DataFrame(rows).to_csv(OUT/'historical_source_metadata.csv',index=False)
    status=subprocess.check_output(['git','status','--short','--','.'],text=True);(OUT/'GIT_STATUS_AFTER.txt').write_text(status)
    targeted=subprocess.check_output(['git','status','--short','--','research/phase9',str(OUT)],text=True)
    original=json.loads(Path('research/results/phase8-2026-10-24/PRESERVED_HASHES.json').read_text());allhash=json.loads((OUT/'PRESERVED_HASHES.json').read_text());assert all(allhash.get(p)==h for p,h in original.items())
    reports=['PHASE9_'+n+'.md' for n in ['DATA_AUDIT','BENCHMARK_SPECIFICATION','ALGORITHM_COMPARISON','INVESTMENT_BENCHMARKS','ABLATION_RESULTS','STATISTICAL_ANALYSIS','FINAL_REPORT','CONFERENCE_DRAFT']]
    assert all((OUT/n).stat().st_size>1000 for n in reports)
    assert len(list((OUT/'figures').glob('*.png')))==9 and len(list((OUT/'figures').glob('*.svg')))==9
    for p,h in hashes.items():assert sha(OUT/'source_snapshot'/p)==h
    result.update({'protected_files_unchanged':verify(),'original_489_hashes_also_unchanged':True,'required_reports':reports,'PNG_figures':9,'SVG_figures':9,'Phase9_source_files':len(list(Path('research/phase9').glob('*.py'))),'git_targeted_status':targeted,'staged_or_committed':False,'classification':'Exploratory benchmark research','incomplete_or_unavailable':['Independent holdout not established','Complete point-in-time 2022–2025 membership unavailable','Daily NIFTY50 TRI reference unavailable','Historical ETF look-through sectors and tracking-error series unavailable','Full frozen-guard exact optimization certificate not claimed','CPU model/RAM not readable under sandbox'],'remaining_failures':[]})
    (OUT/'COMPLETION.json').write_text(json.dumps(result,indent=2))
    files=[p for p in OUT.rglob('*') if p.is_file() and p.name not in ['OUTPUT_HASHES.json','ARTIFACT_INVENTORY.csv']]
    pd.DataFrame([{'path':str(p.relative_to(OUT)),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(files)]).to_csv(OUT/'ARTIFACT_INVENTORY.csv',index=False)
    (OUT/'OUTPUT_HASHES.json').write_text(json.dumps({str(p.relative_to(OUT)):sha(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='OUTPUT_HASHES.json'},indent=2))
    print(json.dumps({'status':'complete','validated_checks':result['focused_checks'],'protected_files':verify(),'generated_files':len(files)+2,'git':targeted},indent=2))
if __name__=='__main__':main()
