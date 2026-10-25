"""Versioned acquisition only; no database access or synthetic fallback."""
import json,datetime
from pathlib import Path
import requests
from research.phase9.freeze import OUT,sha
D=OUT/'benchmark_sources';D.mkdir(exist_ok=True)
log=[]
for name,url,payload in [
 ('membership','https://archives.nseindia.com/content/indices/IndexInclExcl.xls',None),
 ('tri','https://www.niftyindices.com/Backpage.aspx/getTotalReturnIndexString',{'name':'NIFTY 50','startDate':'01-Jan-2022','endDate':'31-Dec-2025'})]:
    try:
        r=requests.get(url,timeout=20) if payload is None else requests.post(url,json=payload,headers={'Referer':'https://www.niftyindices.com/reports/historical-data','User-Agent':'Mozilla/5.0'},timeout=20)
        p=D/(name+'.raw');p.write_bytes(r.content)
        log.append({'name':name,'url':url,'request':payload,'status':r.status_code,'bytes':len(r.content),'sha256':sha(p)})
    except Exception as e:log.append({'name':name,'url':url,'error':str(e)})
try:
    import yfinance as yf
    yf.set_tz_cache_location('/private/tmp/intellivest-phase9-yf')
    obj=yf.Ticker('NIFTYBEES.NS');f=obj.history(start='2021-01-01',end='2026-01-01',auto_adjust=False,actions=True,repair=False,keepna=True,timeout=20,raise_errors=True)
    f.to_csv(D/'NIFTYBEES.csv');log.append({'name':'NIFTYBEES','source':'Yahoo/yfinance','rows':len(f),'sha256':sha(D/'NIFTYBEES.csv'),'independent_equity_holdout':False})
except Exception as e:log.append({'name':'NIFTYBEES','error':str(e)})
(D/'acquisition.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'log':log},indent=2));print(json.dumps(log,indent=2))
