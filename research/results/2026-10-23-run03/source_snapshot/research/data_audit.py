"""Read-only market export, independent provider acquisition, and provenance audit."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, default=str, allow_nan=False) + '\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_database(out):
    import psycopg2
    from backend.config import settings
    conn = psycopg2.connect(settings.RISK_DB_URL, connect_timeout=5,
                            options='-c default_transaction_read_only=on')
    conn.set_session(readonly=True, isolation_level='REPEATABLE READ')
    with conn, conn.cursor() as cur:
        cur.execute('SHOW transaction_read_only')
        assert cur.fetchone()[0] == 'on'
        queries = {
            'security_master': 'SELECT * FROM security_master ORDER BY ticker_symbol',
            'legacy_quotes': '''SELECT s.ticker_symbol,q.trade_date,q.close_price,q.adjusted_close,q.volume
                FROM daily_market_quote q JOIN security_master s USING(security_id)
                ORDER BY s.ticker_symbol,q.trade_date''',
        }
        for name, sql in queries.items():
            cur.execute(sql)
            frame = pd.DataFrame(cur.fetchall(), columns=[x.name for x in cur.description])
            frame.to_csv(out / f'{name}.csv', index=False)
        cur.execute("SELECT table_name,column_name,data_type FROM information_schema.columns WHERE table_schema='public' AND table_name IN ('security_master','daily_market_quote') ORDER BY table_name,ordinal_position")
        dump(out / 'database_schema.json', cur.fetchall())
        cur.execute("SELECT proname,pg_get_functiondef(oid) FROM pg_proc WHERE proname IN ('portfolio_risk_summary','portfolio_risk_summary_v2')")
        dump(out / 'risk_sql.json', dict(cur.fetchall()))
        cur.execute("SELECT definition FROM pg_views WHERE viewname='daily_security_returns'")
        dump(out / 'security_return_sql.json', cur.fetchone())
    conn.close()


def download(out, start, end):
    import yfinance as yf
    yf.set_tz_cache_location('/private/tmp/intellivest-yfinance-research-cache')
    master = pd.read_csv(out / 'security_master.csv')
    statuses, frames = [], []
    raw = out / 'provider_raw'
    raw.mkdir(exist_ok=True)
    # No fallback, no insertion into PostgreSQL, no silent symbol substitution.
    for row in master.to_dict('records'):
        ticker = row['ticker_symbol']
        if ticker == 'TATAMOTORS':
            statuses.append({'ticker': ticker, 'status': 'excluded', 'reason': 'unreconciled demerger / symbol identity'})
            continue
        try:
            obj = yf.Ticker(ticker + '.NS')
            frame = obj.history(start=start, end=end, auto_adjust=False, actions=True,
                                repair=False, keepna=True, timeout=10, raise_errors=True)
            if frame.empty:
                raise ValueError('empty provider history')
            frame.to_csv(raw / f'{ticker}.csv')
            meta = obj.history_metadata
            dump(raw / f'{ticker}.metadata.json', dict(meta))
            required = ['Close', 'Adj Close', 'Open', 'Dividends', 'Stock Splits']
            if any(c not in frame for c in required):
                raise ValueError('missing required OHLC/adjustment/action fields')
            df = frame.reset_index().rename(columns={'Date': 'date', 'Close': 'close', 'Adj Close': 'adjusted_close',
                'Open': 'open', 'High': 'high', 'Low': 'low', 'Volume': 'volume', 'Dividends': 'dividend', 'Stock Splits': 'split'})
            df['date'] = pd.to_datetime(df['date']).dt.date
            df['ticker'] = ticker
            df['sector'] = row['sector_name']
            if (df.date.duplicated().any() or not np.isfinite(df[['close','adjusted_close','open']]).all().all()
                    or (df[['close','adjusted_close','open']] <= 0).any().any()):
                raise ValueError('invalid or duplicate provider bars; no interpolation permitted')
            if meta.get('currency') != 'INR':
                raise ValueError('provider currency is not confirmed INR')
            # Yahoo OHLC is split-normalized. Reconstruct nominal units using all
            # future splits in the acquired horizon. Return series stays adjusted.
            future = df['split'].replace(0, 1).iloc[::-1].cumprod().iloc[::-1] / df['split'].replace(0, 1)
            df['nominal_close'] = df['close'] * future
            df['nominal_open'] = df['open'] * future
            df['nominal_dividend'] = df['dividend'] * future
            frames.append(df)
            statuses.append({'ticker': ticker, 'status': 'provider_acquired', 'rows': len(df),
                             'first': str(df.date.min()), 'last': str(df.date.max()), 'source': 'yfinance/Yahoo Finance',
                             'splits': int((df['split'] != 0).sum()), 'dividends': int((df.dividend != 0).sum()),
                             'raw_sha256': sha(raw / f'{ticker}.csv')})
        except Exception as exc:
            statuses.append({'ticker': ticker, 'status': 'failed', 'reason': str(exc)[:800]})
        print(json.dumps(statuses[-1]), flush=True)
        dump(out / 'acquisition_log.json', statuses)
    cols = ['date','ticker','sector','close','adjusted_close','open','high','low','volume','dividend','split',
            'nominal_close','nominal_open','nominal_dividend']
    dataset = pd.concat(frames, ignore_index=True)[cols] if frames else pd.DataFrame(columns=cols)
    dataset.to_csv(out / 'provider_quotes.csv', index=False)
    return statuses


def audit(out):
    legacy = pd.read_csv(out / 'legacy_quotes.csv', parse_dates=['trade_date'])
    provider = pd.read_csv(out / 'provider_quotes.csv')
    union = set(legacy.trade_date)
    records = []
    for ticker, group in legacy.groupby('ticker_symbol'):
        adjusted = np.isclose(group.adjusted_close, (group.close_price * .98).round(2), atol=.011, rtol=0)
        rec = {'ticker': ticker, 'rows': len(group), 'first': str(group.trade_date.min().date()),
               'last': str(group.trade_date.max().date()), 'duplicates': int(group.trade_date.duplicated().sum()),
               'weekend_rows': int((group.trade_date.dt.dayofweek >= 5).sum()),
               'artificial_098_matches': int(adjusted.sum()), 'artificial_098_fraction': float(adjusted.mean()),
               'missing_union_dates': len(union - set(group.trade_date)),
               'zero_returns': int((group.close_price.pct_change() == 0).sum()),
               'daily_return_std': float(group.close_price.pct_change().std()),
               'invalid_prices': int((group[['close_price','adjusted_close']] <= 0).any(axis=1).sum())}
        if not provider.empty:
            p = provider[provider.ticker == ticker].copy()
            p['trade_date'] = pd.to_datetime(p.date)
            j = group.merge(p, on='trade_date')
            rec.update(overlap=len(j), close_matches=int(np.isclose(j.close_price, j.close, atol=.02, rtol=1e-5).sum()),
                       adjusted_matches=int(np.isclose(j.adjusted_close_x, j.adjusted_close_y, atol=.02, rtol=1e-5).sum()))
        records.append(rec)
    pd.DataFrame(records).to_csv(out / 'legacy_quality_by_security.csv', index=False)
    log = json.loads((out / 'acquisition_log.json').read_text())
    manifest = {'created_utc': datetime.now(timezone.utc).isoformat(), 'legacy_observations': len(legacy),
        'legacy_securities': len(records), 'legacy_range': [str(legacy.trade_date.min().date()),str(legacy.trade_date.max().date())],
        'provider_securities': int(provider.ticker.nunique()), 'provider_observations': len(provider),
        'provider_range': [] if provider.empty else [str(provider.date.min()),str(provider.date.max())],
        'synthetic_fingerprint_rows': sum(r['artificial_098_matches'] for r in records),
        'source': 'Yahoo Finance via yfinance; legacy PostgreSQL excluded from performance replay',
        'adjustment': 'Provider Adj Close for return/ranking; split-reconstructed nominal OHLC for execution; cash dividends credited on ex-date (pay-date approximation)',
        'limitations': ['Current surviving security master; no historical membership or complete delisting ledger',
            'Provider revised adjustments available at extraction; no historical data vintages',
            'Acquisition confirms source but is not independent exchange certification'],
        'status': 'provider_data_available_requires_validation' if len(provider) else 'blocked_no_verified_adjusted_history',
        'acquisition_log': log, 'versions': {k: importlib.metadata.version(k) for k in ['numpy','pandas','yfinance','psycopg2-binary']}}
    manifest['files_sha256'] = {p.name: sha(p) for p in sorted(out.glob('*')) if p.is_file() and p.name != 'manifest.json'}
    dump(out / 'manifest.json', manifest)
    report = f'''# Historical dataset audit\n\nAudit time: {manifest['created_utc']}\n\n## Existing database (read-only snapshot)\n\n{len(legacy):,} observations, {len(records)} securities, {manifest['legacy_range']}.\n{manifest['synthetic_fingerprint_rows']:,} rows match the synthetic generator's rounded 0.98 adjustment formula. This is a diagnostic fingerprint, not proof of provenance. The schema stores neither source nor ingestion time; no listing/delisting history exists. Full per-security checks are in `legacy_quality_by_security.csv`. Union-date gaps are diagnostics, not an exchange calendar. No historical rows were changed.\n\n## Independent acquisition\n\n{manifest['provider_observations']:,} provider observations across {manifest['provider_securities']} securities. Status: **{manifest['status']}**. See `acquisition_log.json` for every download failure and exclusion. Synthetic fallback is disabled. Legacy observations are quarantined from financial simulation, regardless of plausibility.\n\n## Adjustment and eligibility\n\n{manifest['adjustment']}. Raw responses and hashes are retained when available. Symbols are never silently substituted; TATAMOTORS is excluded because the implemented application flags unreconciled identity/corporate actions. Initial eligibility requires at least 120 completed adjusted returns and a contemporaneous bar; a first provider observation is not a verified listing date. Current sector labels and a surviving universe limit generalization. Historical index membership and delisted stocks cannot be reconstructed from these tables. Any replay is a restricted-universe exploratory study, not an unbiased market-wide evaluation.\n\n## Scientific gate\n\nIf fresh adjusted history is absent, historical financial comparisons, return curves, p-values, and superiority claims are unavailable. Policy arithmetic and synthetic engine checks can still be executed, explicitly as implementation diagnostics. Provider data, when acquired, must additionally pass identity, action and calendar checks before replay.\n\n## Source documentation\n\n- [yfinance history implementation](https://github.com/ranaroussi/yfinance/blob/main/yfinance/scrapers/history.py): OHLC, adjustment and action options.\n- [NSE historical reports](https://www.nseindia.com/static/resources/historical-reports-capital-market-daily-monthly-archives): exchange comparison source.\n\nNo claim of exchange corroboration is made merely because a provider responded.\n'''
    (out / 'DATA_AUDIT_REPORT.md').write_text(report)
    print(json.dumps({k:v for k,v in manifest.items() if k not in ['files_sha256','acquisition_log']}, indent=2))
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--start', default='2021-01-01')
    parser.add_argument('--end', default='2026-10-23', help='Exclusive end; excludes possibly incomplete current session')
    parser.add_argument('--offline', action='store_true', help='Audit existing acquisition files without network or DB')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if not args.offline:
        export_database(args.out)
        download(args.out, args.start, args.end)
    audit(args.out)


if __name__ == '__main__':
    main()
