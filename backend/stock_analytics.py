"""Descriptive daily statistics; never append intraday quotations to returns."""
from datetime import timedelta
import math
import numpy as np
from backend.market_data import get_historical_prices
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger(__name__)
from backend.config import settings


def json_native(value):
    """All NumPy scalars leave the analytics boundary as JSON-native values."""
    if isinstance(value, np.generic):
        return json_native(value.item())
    if isinstance(value, dict):
        return {k: json_native(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_native(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def historical_analysis(conn, security_id, window, history_source='adjusted'):
    series = get_historical_prices(conn, security_id, window, history_source)
    source = series['source']
    provenance = ('Yahoo Adj Close with auto_adjust=False, where present consistently across the selected window; Yahoo applies its own split/dividend adjustment conventions. No independent adjustment guarantee or total-return forecast. '
                  if source == 'yfinance' else 'Legacy database records lack per-row provenance; analyses are provisional. ')
    provenance += series.get('issue') or ''
    rows = []
    for row in series['rows']:
        try:
            close = Decimal(str(row['close_price']))
            if not close.is_finite() or close <= 0:
                continue
            adjusted = row.get('adjusted_close')
            adjusted = Decimal(str(adjusted)) if adjusted is not None else None
            adjusted = adjusted if adjusted is not None and adjusted.is_finite() and adjusted > 0 else None
            rows.append({'trade_date': row['trade_date'], 'close_price': close, 'adjusted_close': adjusted})
        except (ValueError, TypeError, InvalidOperation, KeyError):
            continue
    rows = sorted({r['trade_date']: r for r in rows}.values(), key=lambda r: r['trade_date'])
    if rows and window != 'ALL':
        start = rows[-1]['trade_date'] - timedelta(days={'1M': 30, '3M': 90, '6M': 180, '1Y': 365}[window])
        rows = [r for r in rows if r['trade_date'] >= start]
    # One consistent basis over the whole window; never coalesce row by row.
    adjusted = history_source != 'raw' and bool(rows) and all(r['adjusted_close'] and r['adjusted_close'] > 0 for r in rows)
    basis = ('yahoo_adjusted_close' if source == 'yfinance' else 'stored_adjusted_close') if adjusted else 'raw_close'
    if not adjusted and history_source != 'raw':
        provenance += ' Adjusted prices are incomplete: the entire selected window uses raw Close; no row-level mixing.'
    if not adjusted:
        provenance += ' Raw Close follows the source split conventions and can contain corporate-action effects; it is not a dividend-adjusted total-return series.'
    prices = np.array([float(r['adjusted_close'] if adjusted else r['close_price']) for r in rows])
    returns = prices[1:] / prices[:-1] - 1 if len(prices) > 1 else np.array([])
    n = len(returns)
    sigma = float(np.std(returns, ddof=1)) if n > 1 else None
    if sigma is not None and abs(sigma) < 1e-12:
        sigma = 0.0
    p05 = float(np.quantile(returns, .05, method='linear')) if n >= 60 else None
    tail = returns[returns <= p05] if p05 is not None else np.array([])
    rf = settings.STOCK_ANNUAL_RISK_FREE_RATE
    stats = {'observations': len(rows), 'return_observations': n,
             'period_return': float(prices[-1] / prices[0] - 1) if len(prices) > 1 else None,
             'highest': float(max(prices)) if len(prices) else None, 'lowest': float(min(prices)) if len(prices) else None,
             'mean_daily_return': float(np.mean(returns)) if n else None,
             'median_daily_return': float(np.median(returns)) if n else None,
             'best_daily_return': float(max(returns)) if n else None, 'worst_daily_return': float(min(returns)) if n else None,
             'positive_days': int(sum(returns > 0)), 'negative_days': int(sum(returns < 0)), 'flat_days': int(sum(returns == 0)),
             'daily_volatility': sigma, 'annualized_volatility': sigma * math.sqrt(252) if sigma is not None else None,
             'historical_return_p05': p05, 'tail_mean_return': float(np.mean(tail)) if len(tail) else None,
             'historical_var_95_daily': max(0., -p05) if p05 is not None else None,
             'historical_cvar_95_daily': max(0., -float(np.mean(tail))) if len(tail) else None,
             'sharpe_annualized': (float(np.mean(returns)) - rf / 252) / sigma * math.sqrt(252) if n >= 60 and sigma else None,
             'downside_deviation_annualized': math.sqrt(float(np.mean(np.minimum(returns, 0) ** 2))) * math.sqrt(252) if n else None,
             'risk_free_rate': rf, 'confidence': .95, 'horizon': '1 trading day', 'minimum_tail_observations': 60,
             'beta': None, 'beta_reason': 'No verified benchmark return series is configured.'}
    peaks = np.maximum.accumulate(prices) if len(prices) else prices
    drawdowns = prices / peaks - 1 if len(prices) else prices
    stats['maximum_drawdown'] = float(min(drawdowns)) if len(drawdowns) else None
    points = []
    for i, row in enumerate(rows):
        points.append({'date': row['trade_date'], 'price': float(prices[i]), 'drawdown': float(drawdowns[i]),
                       'daily_return': float(returns[i-1]) if i else None,
                       'rolling_volatility': float(np.std(returns[i-30:i], ddof=1)) * math.sqrt(252) if i >= 30 else None})
    histogram = []
    if n:
        counts, edges = np.histogram(returns, bins=min(24, max(5, int(math.sqrt(n)))))
        histogram = [{'lower': float(edges[i]), 'upper': float(edges[i+1]),
                      'midpoint': float((edges[i]+edges[i+1])/2), 'count': int(count),
                      'tail': bool(p05 is not None and edges[i] <= p05)} for i, count in enumerate(counts)]
    return json_native({'window': window, 'start': rows[0]['trade_date'] if rows else None,
            'end': rows[-1]['trade_date'] if rows else None, 'price_basis': basis,
            'source': source, 'provenance': provenance, 'history_source': history_source,
            'status': series['status'], 'issue': series.get('issue'),
            'data_status': 'Insufficient historical data' if n < 60 else 'available',
            'all_history_limit': '10 years maximum per Yahoo request; completed daily observations only',
            'assumptions': 'Simple close-to-close daily returns; sample volatility (n−1); 252 sessions/year; linear 5th percentile; CVaR averages returns at or below that percentile. Intraday quotes excluded. Ranges end at the last completed observation in the selected series; no interpolation of missing observations.',
            'statistics': stats, 'points': points, 'histogram': histogram})
