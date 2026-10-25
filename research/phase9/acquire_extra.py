import requests,json
from research.phase9.freeze import OUT,sha
D=OUT/'benchmark_sources';log=[]
for name,url in [('etf_missing_session','https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20251024_F_0000.csv.zip'),('historical_page','https://www.niftyindices.com/reports/historical-data')]:
    try:
        r=requests.get(url,timeout=25);(D/(name+'.raw')).write_bytes(r.content);log.append({'name':name,'url':url,'status':r.status_code,'sha256':sha(D/(name+'.raw'))})
    except Exception as e:log.append({'name':name,'error':str(e)})
try:
    payload={'cinfo':json.dumps({'name':'NIFTY 50','startDate':'01-Jan-2022','endDate':'31-Dec-2025'})}
    r=requests.post('https://www.niftyindices.com/Backpage.aspx/getTotalReturnIndexString',json=payload,headers={'Referer':'https://www.niftyindices.com/reports/historical-data','User-Agent':'Mozilla/5.0'},timeout=25);(D/'tri_retry.raw').write_bytes(r.content);log.append({'name':'tri_retry','payload':payload,'status':r.status_code})
except Exception as e:log.append({'name':'tri_retry','error':str(e)})
(D/'acquisition_extra.json').write_text(json.dumps(log,indent=2));print(log)
