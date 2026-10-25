"""Read-only input freeze, scoped to this workspace."""
import hashlib,json,subprocess,os
from pathlib import Path
OUT=Path(os.environ.get('INTELLIVEST_PHASE9_OUT','research/results/phase9-2026-10-25'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def freeze():
    OUT.mkdir(parents=True,exist_ok=True)
    target=OUT/'PRESERVED_HASHES.json'
    if target.exists():return
    files=[p for root in ['research','backend','frontend','db','etl'] for p in Path(root).rglob('*') if p.is_file() and not any(s in p.parts for s in ['node_modules','__pycache__','.pytest_cache']) and 'phase9' not in str(p)]
    target.write_text(json.dumps({str(p):sha(p) for p in sorted(files)},indent=2))
    (OUT/'GIT_STATUS_BEFORE.txt').write_text(subprocess.check_output(['git','status','--short','--','.'],text=True))
def verify():
    manifest=json.loads((OUT/'PRESERVED_HASHES.json').read_text());changed=[p for p,h in manifest.items() if sha(p)!=h];assert not changed,changed
    return len(manifest)
if __name__=='__main__':freeze();print(verify())
