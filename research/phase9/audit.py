import json,zipfile
import pandas as pd,numpy as np
from research.phase9.freeze import OUT,sha

def main():
    data=pd.read_csv('research/data/2026-10-23/research_quotes.csv',parse_dates=['date']);D=OUT/'benchmark_sources'
    audit=[]
    listings=pd.read_csv('research/data/2026-10-23/listing_checks.csv')
    for t,g in data.groupby('ticker'):
        audit.append({'ticker':t,'sector':g.sector.iloc[0],'rows':len(g),'first':str(g.date.min().date()),'last':str(g.date.max().date()),'duplicates':int(g.date.duplicated().sum()),'missing_prices':int(g[['nominal_close','adjusted_close']].isna().sum().sum()),'nonpositive_prices':int((g[['nominal_close','adjusted_close']]<=0).sum().sum()),'unexplained_adjustment_factor_changes':int(((abs((g.adjusted_close/g.close)/(g.adjusted_close/g.close).shift()-1)>1e-5)&(g.dividend==0)&(g['split']==0)).sum()),'split_events':int((g['split']>0).sum()),'dividend_events':int((g.nominal_dividend>0).sum()),'provider_first_trade_date':listings.set_index('ticker').loc[t,'provider_first_trade_date'],'exchange_listing_verified':False,'historical_sector_verified':False})
    pd.DataFrame(audit).to_csv(OUT/'historical_universe_metadata.csv',index=False)
    etf=pd.read_csv(D/'NIFTYBEES.csv');etf['date']=pd.to_datetime(etf.Date,utc=True).dt.tz_convert('Asia/Kolkata').dt.tz_localize(None).dt.normalize()
    checks=[]
    correction=D/'etf_missing_session.zip'
    if correction.exists():
        with zipfile.ZipFile(correction) as z:ex=pd.read_csv(z.open(z.namelist()[0]))
        bar=ex[ex.TckrSymb.str.strip()=='NIFTYBEES'].iloc[0]
        day=pd.Timestamp(bar.TradDt);mask=etf.date==day
        assert mask.sum()==1 and etf.loc[mask,'Close'].isna().all()
        for dest,src in [('Close','ClsPric'),('Adj Close','ClsPric'),('Open','OpnPric'),('High','HghPric'),('Low','LwPric')]:etf.loc[mask,dest]=float(bar[src])
        (D/'ETF_CORRECTION.json').write_text(json.dumps({'date':str(day.date()),'source_url':'https://archives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20251024_F_0000.csv.zip','sha256':sha(correction),'ticker':'NIFTYBEES','close':float(bar.ClsPric),'adjustment':'No reported splits/distributions; all other adjusted closes equal closes. Only nominal close used for execution and valuation.'},indent=2))
    for p in sorted(Path('research/data/2026-10-23/exchange_raw').glob('*.zip')):
        with zipfile.ZipFile(p) as z:e=pd.read_csv(z.open(z.namelist()[0]))
        if 'SYMBOL' in e:
            x=e[e.SYMBOL.str.strip()=='NIFTYBEES'];tc='TIMESTAMP';pc='CLOSE'
        else:x=e[e.TckrSymb.str.strip()=='NIFTYBEES'];tc='TradDt';pc='ClsPric'
        for _,r in x.iterrows():
            day=pd.Timestamp(r[tc]);g=etf[etf.date==day]
            if len(g):checks.append({'date':str(day.date()),'provider_close':float(g.Close.iloc[0]),'exchange_close':float(r[pc]),'match':bool(np.isclose(g.Close.iloc[0],r[pc],atol=.06,rtol=.00005)),'exchange_file':str(p),'exchange_sha256':sha(p)})
    pd.DataFrame(checks).to_csv(OUT/'etf_exchange_checks.csv',index=False)
    dates=pd.DatetimeIndex(sorted(data.date.unique()));expected=dates[dates<='2025-12-31'];missing=expected.difference(etf.date)
    admitted=len(checks)>=5 and all(r['match'] for r in checks) and not len(missing) and not etf.date.duplicated().any() and np.isfinite(etf.Close).all() and (etf.Close>0).all() and not (etf['Stock Splits']>0).any()
    result={'equity_rows':len(data),'equity_securities':data.ticker.nunique(),'equity_dates':len(dates),'equity_duplicate_keys':int(data.duplicated(['ticker','date']).sum()),'etf_admitted':bool(admitted),'etf_rows':len(etf),'etf_missing_common_sessions':len(missing),'etf_spot_checks':checks,'etf_dividends':float(etf.Dividends.sum()),'etf_splits':float(etf['Stock Splits'].sum()),'etf_adjusted_equals_close':bool(np.allclose(etf.Close,etf['Adj Close'])),'independent_holdout':False}
    (OUT/'DATA_AUDIT.json').write_text(json.dumps(result,indent=2));etf.to_csv(D/'NIFTYBEES_normalized.csv',index=False)
    try:
        sheets=pd.read_excel(D/'membership.raw',sheet_name=None,engine='xlrd')
        for name,f in sheets.items():f.to_csv(D/('membership_'+name.replace('/','_')+'.csv'),index=False)
        (D/'membership_structure.json').write_text(json.dumps({n:{'rows':len(f),'columns':list(f.columns.astype(str)),'preview':f.head(8).astype(str).to_dict('records')} for n,f in sheets.items()},indent=2))
    except Exception as e:(D/'membership_parse_error.txt').write_text(str(e))
    print(json.dumps(result,indent=2))
from pathlib import Path
if __name__=='__main__':main()
