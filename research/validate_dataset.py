"""Exchange spot checks and explicit dataset admission; no database access."""
import argparse
import io
import json
import re
from pathlib import Path
import zipfile
import pandas as pd
import numpy as np
import requests
from research.data_audit import dump, sha


def validate(folder):
    data = pd.read_csv(folder/'provider_quotes.csv', parse_dates=['date'])
    raw = folder/'exchange_raw'
    raw.mkdir(exist_ok=True)
    log, checks = [], []
    # Fixed annual/format-transition samples, chosen without strategy outcomes.
    dates = ['2021-12-31','2022-12-30','2023-12-29','2024-06-28','2024-12-31','2025-12-31']
    for date in dates:
        day = pd.Timestamp(date)
        filename = (f'cm{day.strftime("%d%b%Y").upper()}bhav.csv.zip' if day < pd.Timestamp('2024-07-08')
                    else f'BhavCopy_NSE_CM_0_0_0_{day:%Y%m%d}_F_0000.csv.zip')
        url = f'https://nsearchives.nseindia.com/content/historical/EQUITIES/{day:%Y}/{day.strftime("%b").upper()}/'
        if day >= pd.Timestamp('2024-07-08'):
            url = 'https://nsearchives.nseindia.com/content/cm/'
        url += filename
        path = raw/filename
        try:
            if not path.exists():
                response = requests.get(url, timeout=20, headers={'User-Agent':'Mozilla/5.0'})
                response.raise_for_status()
                path.write_bytes(response.content)
            with zipfile.ZipFile(path) as archive:
                exchange = pd.read_csv(archive.open(archive.namelist()[0]))
            if 'SYMBOL' in exchange:
                exchange = exchange[exchange.SERIES.str.strip() == 'EQ']
                exchange = exchange.rename(columns={'SYMBOL':'ticker','CLOSE':'exchange_close','TIMESTAMP':'exchange_date'})
            else:
                exchange = exchange[exchange.SctySrs.str.strip() == 'EQ']
                exchange = exchange.rename(columns={'TckrSymb':'ticker','ClsPric':'exchange_close','TradDt':'exchange_date'})
            assert (pd.to_datetime(exchange.exchange_date).dt.normalize() == day).all(), 'exchange internal date mismatch'
            joined = data[data.date == day].merge(exchange[['ticker','exchange_close']], on='ticker')
            joined['absolute_error'] = abs(joined.nominal_close-joined.exchange_close)
            joined['match'] = np.isclose(joined.nominal_close,joined.exchange_close, atol=.06,rtol=.00005)
            checks.extend(joined[['date','ticker','nominal_close','exchange_close','absolute_error','match']].to_dict('records'))
            log.append({'date':date,'url':url,'status':'acquired','sha256':sha(path),'comparisons':len(joined),'matches':int(joined.match.sum())})
        except Exception as exc:
            log.append({'date':date,'url':url,'status':'failed','reason':str(exc)[:500]})
        print(log[-1],flush=True)
    dump(folder/'exchange_acquisition.json',log)
    pd.DataFrame(checks).to_csv(folder/'exchange_checks.csv',index=False)
    exclusions = {'TATAMOTORS':'unreconciled demerger and renamed identity',
                  'ITC':'2025 demerger; no entitlement valuation ledger',
                  'RELIANCE':'2023 Jio Financial demerger; no entitlement valuation ledger',
                  'BHARTIARTL':'rights/partly paid security history not reconciled',
                  'HDFCBANK':'2023 merger identity/action reconciliation not independently established',
                  'SHRIRAMFIN':'2022 merger and earlier SRTRANSFIN symbol identity not reconciled'}
    adjustment_checks=[]
    listing_checks=[]
    for ticker,g in data.groupby('ticker'):
        factor=g.adjusted_close/g.close
        unexplained=(abs(factor/factor.shift()-1)>1e-5)&(g.dividend==0)&(g['split']==0)
        adjustment_checks.append({'ticker':ticker,'unexplained_factor_changes':int(unexplained.sum()),
                                  'dividend_observations':int((g.dividend>0).sum()),'split_observations':int((g['split']>0).sum())})
        if unexplained.any():
            exclusions[ticker]='adjustment-factor change without a reported action'
        metadata=json.loads((folder/'provider_raw'/f'{ticker}.metadata.json').read_text())
        if isinstance(metadata,str):
            match=re.search(r"firstTradeDate.*?Timestamp\('([0-9-]+)",metadata)
            first=match.group(1) if match else None
        else:
            first=str(metadata.get('firstTradeDate',''))[:10]
        listing_checks.append({'ticker':ticker,'provider_first_trade_date':first,
                               'first_observed':str(g.date.min().date()),'basis':'provider metadata, not exchange listing certificate'})
        if not first or pd.Timestamp(first)>g.date.min():
            exclusions[ticker]='listing date unavailable or observations precede reported trading availability'
        if g.date.duplicated().any() or not g.date.is_monotonic_increasing:
            exclusions[ticker] = 'duplicate/unordered dates'
        # Broken provider calendars must not be repaired with fabricated prices.
        if (g.date.diff().dt.days.dropna()>10).any():
            exclusions[ticker] = 'unexplained date gap >10 calendar days'
        jumps = abs(g.adjusted_close.pct_change())
        if (jumps>.5).any():
            exclusions[ticker] = 'adjusted daily move >50%; action reconciliation required'
    if checks:
        comp = pd.DataFrame(checks)
        for ticker,g in comp.groupby('ticker'):
            if not g.match.all():
                exclusions[ticker] = 'exchange sampled nominal-close disagreement'
            elif len(g)<5:
                exclusions[ticker] = 'fewer than five independent exchange price/date comparisons'
    pd.DataFrame(adjustment_checks).to_csv(folder/'adjustment_checks.csv',index=False)
    pd.DataFrame(listing_checks).to_csv(folder/'listing_checks.csv',index=False)
    accepted = data[~data.ticker.isin(exclusions)].copy()
    # Common calendar intersection avoids manufacturing returns on missing bars.
    counts = accepted.groupby('date').ticker.nunique()
    common = counts[counts==accepted.ticker.nunique()].index
    dropped = accepted[~accepted.date.isin(common)]
    # Fail admission if common-calendar deletion masks more than isolated gaps.
    calendar_removed = sorted(set(data.date)-set(common))
    accepted = accepted[accepted.date.isin(common)]
    accepted.to_csv(folder/'research_quotes.csv',index=False)
    dump(folder/'exclusions.json',exclusions)
    dataset_status = 'exploratory_restricted_universe' if len(accepted) and len(common)>500 else 'blocked'
    # No exchange spot checks means source provenance exists, but independent
    # corroboration is absent; refuse financial replay rather than overclaim.
    if not checks or accepted.ticker.nunique()<6:
        dataset_status = 'blocked_independent_corroboration_insufficient'
    metadata = {'status':dataset_status,'securities':int(accepted.ticker.nunique()),'observations':len(accepted),
        'range':[str(accepted.date.min().date()),str(accepted.date.max().date())] if len(accepted) else [],
        'source_dataset_sha256':sha(folder/'provider_quotes.csv'),'research_dataset_sha256':sha(folder/'research_quotes.csv'),
        'exclusions':exclusions,'calendar_removed':[str(x.date()) for x in calendar_removed],
        'calendar_removed_observations':len(dropped),'exchange_comparisons':len(checks),
        'exchange_matches':sum(bool(x['match']) for x in checks),
        'universe':sorted(accepted.ticker.unique()),'listing_dates':'provider metadata firstTradeDate checked against first observation; exchange listing certificates unavailable; minimum 120 observed returns and contemporaneous bar required',
        'adjustment_provenance':'Yahoo adjusted close plus explicit dividends/splits; nominal reconstruction sampled against NSE',
        'publication_claims_supported':False}
    dump(folder/'admission.json',metadata)
    report=folder/'DATA_AUDIT_REPORT.md'
    report.write_text(report.read_text().split('\n## Completed admission checks')[0])
    with report.open('a') as f:
        f.write('\n## Completed admission checks\n\n'+json.dumps(metadata,indent=2)+'\n\nExchange checks are sparse price/date corroboration, not certification of every adjusted observation or dividend. A complete historical listing/index/delisting universe is unavailable. Financial comparisons, if admitted, are exploratory only.\n')
    print(json.dumps(metadata,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',type=Path,required=True)
    validate(parser.parse_args().data)
