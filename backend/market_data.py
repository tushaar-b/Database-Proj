"""Shared Yahoo Finance research data via yfinance; no broker credentials.

Only provider-confirmed NSE/INR symbols become current price evidence. Quotes
and completed daily history have separate caches and price bases. No DB writes.
"""
from concurrent.futures import ThreadPoolExecutor
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import logging
import traceback
from pathlib import Path
import math
from threading import RLock
from time import monotonic
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf
from psycopg2.extras import RealDictCursor
from backend.config import settings

logger = logging.getLogger(__name__)
IST = ZoneInfo('Asia/Kolkata')
_lock = RLock()
_quotes = {}
_history = {}
_attempt_after = {}
_history_after = {}
_issues = {}
_last_success = None
_provider_backoff = 0


def provider_state():
    return {'provider': 'yfinance', 'configured': True, 'connected': _last_success is not None,
            'last_success': _last_success, 'refresh_seconds': settings.MARKET_QUOTE_REFRESH_SECONDS,
            'issue': ('Some Yahoo quotations are unavailable; see individual fallback and symbol statuses.' if _issues else None),
            'usage': 'Yahoo Finance via yfinance; research/personal educational use, may be delayed; not an official exchange feed.'}


def yahoo_symbol(security):
    ticker = security['ticker_symbol'].upper()
    if security.get('exchange_code', security.get('exchange')) != 'NSE':
        return None
    if ticker == 'TATAMOTORS':
        # NSE CML70875/FAOP70882: renamed TMPV after the 2025 demerger.
        # The legacy holding/history represents an unreconciled corporate action;
        # neither passenger nor commercial shares may silently replace it.
        return None
    return ticker + '.NS'


def _price(value):
    number = Decimal(str(value))
    if not number.is_finite() or number <= 0 or not math.isfinite(float(number)):
        raise ValueError('Missing, nonfinite or nonpositive price')
    return number


def _timestamp(value):
    if value is None or value is pd.NaT:
        return None
    try:
        if isinstance(value, (int, float)):
            value = datetime.fromtimestamp(value, timezone.utc)
        stamp = pd.Timestamp(value)
        if pd.isna(stamp) or stamp.tzinfo is None:
            return None
        stamp = stamp.to_pydatetime().astimezone(IST)
        return stamp if stamp <= datetime.now(IST) else None
    except (TypeError, ValueError, OverflowError):
        return None


def _session_time(meta, name):
    period = meta.get('currentTradingPeriod') or {}
    regular = (period.get('regular') or {}) if isinstance(period, Mapping) else {}
    value = regular.get(name) if isinstance(regular, Mapping) else None
    # Session end can be in the future; it is a schedule, not an observation.
    try:
        stamp = pd.Timestamp(value, unit='s', tz='UTC') if isinstance(value, (int, float)) else pd.Timestamp(value)
        return stamp.to_pydatetime().astimezone(IST) if stamp.tzinfo and not pd.isna(stamp) else None
    except (ValueError, TypeError, OverflowError):
        return None


def _normalise_daily(frame):
    """Accept genuine daily bars only; skip malformed/missing observations.

    Daily indices are trading dates, never fabricated trade timestamps. A
    consistent adjusted/raw basis is chosen later for the entire return window.
    """
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return []
    if isinstance(frame.columns, pd.MultiIndex):
        # Ticker.history normally returns flat columns. Handle a single-symbol
        # frame from a supported downloader without guessing ambiguous columns.
        for level in range(frame.columns.nlevels):
            if len(frame.columns.get_level_values(level).unique()) == 1:
                frame = frame.copy()
                frame.columns = frame.columns.droplevel(level)
                break
    if isinstance(frame.columns, pd.MultiIndex) or 'Close' not in frame.columns:
        raise ValueError('Unexpected daily price columns')
    rows = {}
    for index, row in frame.iterrows():
        try:
            stamp = pd.Timestamp(index)
            if pd.isna(stamp) or isinstance(index, (int, float)):
                continue
            day = stamp.tz_convert(IST).date() if stamp.tzinfo else stamp.date()
            if day > datetime.now(IST).date():
                continue
            close = _price(row['Close'])
            try:
                adjusted = _price(row.get('Adj Close'))
            except (ValueError, InvalidOperation, TypeError):
                adjusted = None
            rows[day] = {'trade_date': day, 'close_price': close, 'adjusted_close': adjusted}
        except (ValueError, InvalidOperation, TypeError, OverflowError):
            continue
    return [rows[day] for day in sorted(rows)]


def _fetch_daily(symbol, period):
    """One supported yfinance history call, with metadata from that response."""
    ticker = yf.Ticker(symbol)
    frame = ticker.history(period=period, interval='1d', auto_adjust=False,
                           actions=True, timeout=settings.YFINANCE_TIMEOUT_SECONDS)
    if frame is None or frame.empty:
        raise ValueError('Yahoo returned no price observations')
    meta = ticker.history_metadata
    if (not isinstance(meta, Mapping) or meta.get('symbol') != symbol or meta.get('currency') != 'INR'
            or meta.get('exchangeName') not in ('NSI', 'NSE') or meta.get('instrumentType') != 'EQUITY'):
        raise ValueError('Yahoo symbol, listing or INR currency could not be validated')
    rows = _normalise_daily(frame)
    if not rows:
        raise ValueError('Yahoo returned no valid daily prices')
    metadata = {key: meta.get(key) for key in (
        'symbol', 'currency', 'exchangeName', 'instrumentType', 'regularMarketTime',
        'regularMarketPrice', 'currentTradingPeriod', 'longName')}
    metadata['normalization_quality'] = {'duplicate_dates': bool(frame.index.has_duplicates),
                                          'discarded_rows': max(0, len(frame) - len(rows))}
    return rows, metadata


def _completed_rows(rows, meta):
    now = datetime.now(IST)
    end = _session_time(meta, 'end')
    # Exclude a developing daily bar. Today's bar is eligible only after the
    # provider's actual session end plus a settlement buffer, never by weekday.
    completed_today = bool(end and end.date() == now.date() and now >= end + timedelta(minutes=15))
    return [r for r in rows if r['trade_date'] < now.date() or (r['trade_date'] == now.date() and completed_today)]


def _quote_from_rows(symbol, rows, meta):
    now = datetime.now(IST)
    stamp = _timestamp(meta.get('regularMarketTime'))
    start, end = _session_time(meta, 'start'), _session_time(meta, 'end')
    in_session = bool(start and end and start <= now <= end)
    completed = _completed_rows(rows, meta)
    latest = rows[-1]
    developing = latest['trade_date'] == now.date() and (not end or now < end + timedelta(minutes=15))
    if developing and stamp and stamp.date() == latest['trade_date']:
        price = _price(meta.get('regularMarketPrice', latest['close_price']))
        previous = next((r['close_price'] for r in reversed(completed) if r['trade_date'] < latest['trade_date']), None)
        observed, day, state = stamp, stamp.date(), 'latest_intraday_observation'
        fresh = bool((now - stamp).total_seconds() <= settings.MARKET_QUOTE_STALE_SECONDS)
    elif completed:
        latest = completed[-1]
        price = latest['close_price']
        previous = completed[-2]['close_price'] if len(completed) > 1 else None
        observed, day, state = None, latest['trade_date'], 'last_market_close'
        # Acceptance uses recent dated evidence, not an absent broker "live"
        # flag. A close must match Yahoo's last trading date, be within the
        # configurable age, and not stand in for an open current session.
        fresh = bool(stamp and stamp.date() == day and not in_session
                     and 0 <= (now.date() - day).days <= settings.MARKET_CLOSE_MAX_AGE_DAYS)
    else:
        price, previous = latest['close_price'], None
        observed, day, state, fresh = None, latest['trade_date'], 'latest_daily_observation', False
    return {'price': price.quantize(Decimal('.01')), 'previous_close': previous.quantize(Decimal('.01')) if previous else None,
            'observed_at': observed, 'price_date': day, 'source': 'yfinance', 'yahoo_symbol': symbol,
            'received_at': now, 'status': state, 'fresh_enough_for_operation': fresh, 'stale': not fresh,
            'price_basis': 'unadjusted_daily_close' if state == 'last_market_close' else 'provider_quotation',
            'timestamp_precision': 'provider_trade_time' if observed else 'date_only',
            'market_status': 'Within provider session window' if in_session else 'Outside provider session window' if end else 'Session timing unavailable',
            'issue': None if fresh else 'Dated/delayed Yahoo observation; refresh or revalidate before using it for a new investment.'}


def _log_failure(symbol, operation, exc):
    # Do not log exception text, cookies, account IDs, database URLs or records.
    logger.warning('yfinance %s unavailable symbol=%s exception=%s', operation, symbol, type(exc).__name__)
    if not isinstance(exc, (ValueError, InvalidOperation)) and not type(exc).__module__.startswith(('yfinance', 'curl_cffi', 'requests', 'urllib3')):
        locations = [f'{Path(f.filename).name}:{f.lineno}:{f.name}' for f in traceback.extract_tb(exc.__traceback__)]
        logger.error('Unexpected market-data error symbol=%s exception=%s locations=%s', symbol, type(exc).__name__, ' -> '.join(locations))


def _retrieve_quote(security):
    global _provider_backoff
    symbol = yahoo_symbol(security)
    if not symbol:
        return security['id'], None, 'missing_symbol'
    if monotonic() < _provider_backoff:
        return security['id'], None, 'provider_unavailable'
    try:
        rows, meta = _fetch_daily(symbol, '1mo')
        return security['id'], _quote_from_rows(symbol, rows, meta), None
    except Exception as exc:
        _log_failure(symbol, 'quotation', exc)
        if 'RateLimit' in type(exc).__name__ or type(exc).__name__ in ('DNSError', 'Timeout', 'ConnectTimeout', 'ReadTimeout', 'ConnectionError'):
            _provider_backoff = max(_provider_backoff, monotonic() + settings.MARKET_PROVIDER_BACKOFF_SECONDS)
        return security['id'], None, 'rate_limited' if 'RateLimit' in type(exc).__name__ else 'provider_unavailable'


def get_latest_quotes(conn, security_ids=None):
    global _last_success, _provider_backoff
    wanted = {str(s) for s in security_ids} if security_ids is not None else None
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute('''SELECT sm.*,sm.security_id::text AS id,q.close_price,q.trade_date,p.close_price AS previous_close
                       FROM security_master sm LEFT JOIN LATERAL
                       (SELECT close_price,trade_date FROM daily_market_quote WHERE security_id=sm.security_id
                        AND close_price>0 AND trade_date<=CURRENT_DATE ORDER BY trade_date DESC LIMIT 1) q ON TRUE
                       LEFT JOIN LATERAL (SELECT close_price FROM daily_market_quote WHERE security_id=sm.security_id
                        AND close_price>0 AND trade_date<q.trade_date ORDER BY trade_date DESC LIMIT 1) p ON TRUE
                       ORDER BY sm.ticker_symbol''')
        securities = [dict(r) for r in cur.fetchall()]
    securities = [s for s in securities if wanted is None or s['id'] in wanted]
    with _lock:
        due = [s for s in securities if monotonic() >= _attempt_after.get(s['id'], 0)]
        if due and monotonic() >= _provider_backoff:
            # One in-flight refresh per shared cache; bounded per-symbol work.
            for s in due:
                _attempt_after[s['id']] = monotonic() + settings.MARKET_QUOTE_REFRESH_SECONDS
            with ThreadPoolExecutor(max_workers=4) as pool:
                for sid, quotation, issue in pool.map(_retrieve_quote, due):
                    if quotation:
                        _quotes[sid] = quotation
                        _issues.pop(sid, None)
                        _last_success = datetime.now(IST)
                    else:
                        _issues[sid] = issue
                        _attempt_after[sid] = monotonic() + settings.MARKET_PROVIDER_BACKOFF_SECONDS
                        if issue == 'rate_limited':
                            _provider_backoff = monotonic() + settings.MARKET_PROVIDER_BACKOFF_SECONDS
        result = {}
        for security in securities:
            sid = security['id']
            cached = _quotes.get(sid)
            base = {'security_id': sid, 'ticker_symbol': security['ticker_symbol'], 'company_name': security['company_name'],
                    'sector_name': security['sector_name'], 'exchange': security['exchange_code'], 'currency': 'INR'}
            if cached:
                row = {**base, **cached}
                receipt_age = (datetime.now(IST) - cached['received_at']).total_seconds()
                observation_age = (datetime.now(IST) - cached['observed_at']).total_seconds() if cached['observed_at'] else None
                if sid in _issues or receipt_age > settings.MARKET_QUOTE_REFRESH_SECONDS * 2:
                    row.update(status='historical_fallback', stale=True, fresh_enough_for_operation=False,
                               issue='Yahoo retrieval failed or cache expired; showing the last valid cached quotation with its actual observation time.')
                elif row['status'] == 'latest_intraday_observation' and (observation_age is None or observation_age > settings.MARKET_QUOTE_STALE_SECONDS):
                    row.update(stale=True, fresh_enough_for_operation=False, issue='The intraday Yahoo observation is delayed; refresh before accepting a new investment.')
            else:
                missing_symbol = not yahoo_symbol(security)
                issue = ('Missing/unreconciled Yahoo listing: the legacy TATAMOTORS security requires corporate-action reconciliation; no successor is substituted.'
                         if missing_symbol else 'Yahoo Finance temporarily unavailable or returned no valid observations. Showing dated database fallback where available.')
                row = {**base, 'price': security['close_price'], 'previous_close': security['previous_close'],
                       'observed_at': None, 'price_date': security['trade_date'], 'received_at': None,
                       'source': 'PostgreSQL historical close (provenance unverified)',
                       'status': 'historical_fallback' if security['close_price'] else 'unavailable',
                       'stale': True, 'fresh_enough_for_operation': False, 'timestamp_precision': 'date_only',
                       'price_basis': 'unadjusted_historical_close', 'market_status': 'Unknown', 'issue': issue}
            row['error_kind'] = _issues.get(sid) or ('missing_symbol' if not yahoo_symbol(security) else None)
            row['change'] = row['price'] - row['previous_close'] if row['price'] and row['previous_close'] else None
            row['change_percent'] = row['change'] / row['previous_close'] * 100 if row['change'] is not None else None
            result[sid] = row
        return result


def _history_due(cached, key):
    if monotonic() >= _history_after.get(key, 0):
        return True
    if not cached:
        return False
    # Crossing the provider's completed-session boundary invalidates a cache
    # fetched before that boundary, even inside its normal one-hour TTL.
    boundary = cached.get('completion_boundary')
    return bool(boundary and datetime.now(IST) >= boundary and cached['fetched_at'] < boundary)


def _retrieve_history(security, window):
    global _provider_backoff
    symbol = yahoo_symbol(security)
    if monotonic() < _provider_backoff:
        return None
    try:
        period = {'1M': '3mo', '3M': '6mo', '6M': '1y', '1Y': '2y', 'ALL': '10y'}[window]
        raw, meta = _fetch_daily(symbol, period)
        rows = _completed_rows(raw, meta)
        if not rows:
            raise ValueError('No completed daily observations')
        last_trade = _timestamp(meta.get('regularMarketTime'))
        end = _session_time(meta, 'end')
        quality = {**meta.get('normalization_quality', {}),
                   'date_mismatch': bool(last_trade and last_trade.date() != raw[-1]['trade_date'])}
        return {'rows': rows, 'source': 'yfinance', 'issue': None, 'status': 'available',
                'fetched_at': datetime.now(IST), 'yahoo_symbol': symbol,
                'provider_last_trade_date': last_trade.date() if last_trade else None,
                'provider_daily_date': raw[-1]['trade_date'], 'quality': quality,
                'completion_boundary': end + timedelta(minutes=15) if end and end.date() == datetime.now(IST).date() else None}
    except Exception as exc:
        _log_failure(symbol, 'daily history', exc)
        if 'RateLimit' in type(exc).__name__ or type(exc).__name__ in ('DNSError', 'Timeout', 'ConnectTimeout', 'ReadTimeout', 'ConnectionError'):
            _provider_backoff = max(_provider_backoff, monotonic() + settings.MARKET_PROVIDER_BACKOFF_SECONDS)
        return None


def get_historical_prices_batch(conn, security_ids, window='1Y', price_basis='adjusted'):
    """One security query and bounded provider batching, without sharing a DB
    connection across threads. The same cache backs analytics and ranking.
    """
    global _last_success
    ids = sorted({str(s) for s in security_ids})
    if not ids:
        return {}
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute('SELECT security_id::text,ticker_symbol,exchange_code FROM security_master WHERE security_id=ANY(%s::uuid[]) ORDER BY ticker_symbol', (ids,))
        securities = [dict(r) for r in cur.fetchall()]
    result = {}
    with _lock:
        due = [s for s in securities if yahoo_symbol(s) and _history_due(_history.get((yahoo_symbol(s), window)), (yahoo_symbol(s), window))]
        if due and monotonic() >= _provider_backoff:
            for s in due:
                _history_after[(yahoo_symbol(s), window)] = monotonic() + settings.MARKET_HISTORY_CACHE_SECONDS
            with ThreadPoolExecutor(max_workers=4) as pool:
                fetched = list(pool.map(lambda s: _retrieve_history(s, window), due))
            for security, record in zip(due, fetched):
                key = (yahoo_symbol(security), window)
                if record:
                    _history[key] = record
                    _last_success = datetime.now(IST)
                else:
                    _history_after[key] = monotonic() + settings.MARKET_PROVIDER_BACKOFF_SECONDS
                    if key in _history:
                        _history[key] = {**_history[key], 'status': 'cached_fallback',
                                         'completion_boundary': None,
                                         'issue': 'Yahoo history temporarily unavailable; using dated cached daily observations.'}
        for security in securities:
            symbol = yahoo_symbol(security)
            cached = _history.get((symbol, window)) if symbol else None
            if cached:
                # A stale cache remains descriptive history, never a fresh trend.
                if (datetime.now(IST) - cached['fetched_at']).total_seconds() > settings.MARKET_HISTORY_CACHE_SECONDS:
                    cached = {**cached, 'status': 'cached_fallback', 'issue': 'Cached daily history is older than its refresh interval.'}
                result[security['security_id']] = {**cached, 'requested_basis': price_basis}
    missing = [s['security_id'] for s in securities if s['security_id'] not in result]
    if missing:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''SELECT security_id::text,trade_date,close_price,adjusted_close FROM daily_market_quote
                           WHERE security_id=ANY(%s::uuid[]) AND close_price>0 AND trade_date<CURRENT_DATE
                           ORDER BY security_id,trade_date''', (missing,))
            fallback = {sid: [] for sid in missing}
            for row in cur.fetchall():
                record = dict(row)
                fallback[record.pop('security_id')].append(record)
        for security in securities:
            sid = security['security_id']
            if sid in result:
                continue
            rows = fallback[sid]
            result[sid] = {'rows': rows, 'source': 'PostgreSQL daily_market_quote',
                           'status': 'historical_fallback' if rows else 'unavailable',
                           'issue': 'Yahoo daily history is unavailable; legacy provenance and adjustment accuracy require audit.',
                           'requested_basis': price_basis, 'yahoo_symbol': yahoo_symbol(security), 'fetched_at': None,
                           'quality': {}}
    return result


def get_historical_prices(conn, security_id, window, price_basis='adjusted'):
    return get_historical_prices_batch(conn, [security_id], window, price_basis).get(str(security_id),
        {'rows': [], 'source': 'unavailable', 'status': 'unavailable', 'issue': 'Security history unavailable.', 'fetched_at': None})


def price_holdings(conn, portfolio_id):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute('''SELECT h.holding_id::text,h.security_id::text,h.quantity,h.average_buy_price,
                       sm.ticker_symbol,sm.company_name,sm.sector_name FROM holding h
                       JOIN security_master sm USING(security_id) WHERE portfolio_id=%s ORDER BY sm.ticker_symbol''', (str(portfolio_id),))
        rows = [dict(r) for r in cur.fetchall()]
    quotes = get_latest_quotes(conn, [r['security_id'] for r in rows]) if rows else {}
    for row in rows:
        q = quotes[row['security_id']]
        row.update(quote=q, latest_price=q['price'], price_date=q['price_date'],
                   market_value=q['price'] * row['quantity'] if q['price'] else None,
                   unrealized_gain_loss=(q['price'] - row['average_buy_price']) * row['quantity'] if q['price'] else None)
    total = sum((r['market_value'] or Decimal(0) for r in rows), Decimal(0))
    complete = all(r['market_value'] is not None for r in rows)
    for row in rows:
        row['portfolio_weight'] = row['market_value'] / total if complete and total and row['market_value'] is not None else None
    return rows


def valuation(conn, portfolio_id, cash):
    rows = price_holdings(conn, portfolio_id)
    complete = all(r['market_value'] is not None for r in rows)
    invested = sum((r['market_value'] or Decimal(0) for r in rows), Decimal(0))
    observations = sorted({str(r['quote']['observed_at'] or r['price_date']) for r in rows})
    dates = [r['price_date'] for r in rows if r['price_date']]
    return {'portfolio_valuation': cash + invested if complete else None, 'holdings_value': invested if complete else None,
            'priced_holdings_subtotal': invested, 'unrealized_gain_loss': sum((r['unrealized_gain_loss'] or Decimal(0) for r in rows), Decimal(0)) if complete else None,
            'calculation_date': min(dates) if dates else None, 'quote_observations': observations,
            'mixed_quote_times': len(observations) > 1, 'has_stale_quotes': any(r['quote']['stale'] for r in rows),
            'valuation_complete': complete, 'market_data': provider_state()}


def quote_change_requires_review(original, latest):
    return original > 0 and abs(latest / original - 1) >= Decimal(str(settings.RECOMMENDATION_PRICE_CHANGE_FRACTION))
