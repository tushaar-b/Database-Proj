"""Versioned descriptive momentum and daily-unit ranking evidence.

No intraday price enters this module. Fractional returns are not percentages.
Policy defaults are research heuristics, not empirically validated predictions.
"""
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
import hashlib
import json
import math
from zoneinfo import ZoneInfo
import numpy as np
from backend.config import settings

METHOD_VERSION = 'risk_momentum_v1'
BASELINE_VERSION = 'risk_only_252_v1'
IST = ZoneInfo('Asia/Kolkata')


def momentum_policy():
    weights = [settings.MOMENTUM_WEIGHT_20, settings.MOMENTUM_WEIGHT_60, settings.MOMENTUM_WEIGHT_MA50]
    total = sum(weights)
    return {'version': METHOD_VERSION, 'baseline_version': BASELINE_VERSION,
            'return_windows': [20, 60], 'moving_average_windows': [20, 50],
            'flat_return_20': settings.MOMENTUM_FLAT_RETURN_20,
            'flat_return_60': settings.MOMENTUM_FLAT_RETURN_60,
            'ma_tolerance': settings.MOMENTUM_MA_TOLERANCE,
            'strong_decline_20': settings.MOMENTUM_STRONG_DECLINE_20,
            'negative_votes_required': settings.MOMENTUM_NEGATIVE_VOTES, 'strong_votes_required': settings.MOMENTUM_STRONG_VOTES,
            'positive_votes_required': settings.MOMENTUM_POSITIVE_VOTES, 'max_gap_days': settings.MOMENTUM_MAX_GAP_DAYS,
            'weights': [w / total for w in weights],
            'agreement_strength': settings.MOMENTUM_AGREEMENT_STRENGTH,
            'severity_cap': settings.MOMENTUM_SEVERITY_CAP,
            'unknown_severity': settings.MOMENTUM_UNKNOWN_SEVERITY,
            'max_history_age_days': settings.MOMENTUM_MAX_HISTORY_AGE_DAYS,
            'fingerprint_return_step': settings.MOMENTUM_FINGERPRINT_RETURN_STEP,
            'tier_weights': {'CONSERVATIVE': settings.MOMENTUM_CONSERVATIVE_WEIGHT,
                             'MODERATE': settings.MOMENTUM_MODERATE_WEIGHT,
                             'AGGRESSIVE': settings.MOMENTUM_AGGRESSIVE_WEIGHT}}


def adjusted_observations(series, as_of=None):
    """Keep a consecutive observed window with a single adjusted-price basis.

    Invalid/missing adjustments are retained as a quality failure rather than
    silently dropping a date and pretending a multi-session move was daily.
    """
    now = as_of or datetime.now(IST)
    records = {}
    duplicates = False
    for row in series.get('rows', []):
        day = row['trade_date']
        if day > now.date():
            continue
        duplicates |= day in records
        try:
            price = Decimal(str(row.get('adjusted_close')))
            if not price.is_finite() or price <= 0 or not math.isfinite(float(price)):
                price = None
        except (ValueError, InvalidOperation, TypeError):
            price = None
        records[day] = {'date': day, 'adjusted_close': price}
    rows = [records[d] for d in sorted(records)][-253:]
    return rows, duplicates


def assess_momentum(series, policy=None, as_of=None):
    policy = policy or momentum_policy()
    now = as_of or datetime.now(IST)
    rows, duplicates = adjusted_observations(series, now)
    count = len(rows)
    recent = rows[-61:]
    valid = bool(recent) and all(r['adjusted_close'] is not None for r in recent)
    values = [float(r['adjusted_close']) for r in recent] if valid else []
    price = values[-1] if values else None
    r20 = price / values[-21] - 1 if len(values) >= 21 else None
    r60 = price / values[-61] - 1 if len(values) >= 61 else None
    ma20 = sum(values[-20:]) / 20 if len(values) >= 20 else None
    ma50 = sum(values[-50:]) / 50 if len(values) >= 50 else None
    end = rows[-1]['date'] if rows else None
    issues = []
    if count < 61: issues.append('At least 61 completed adjusted daily closes are required for the full 60-session assessment.')
    if not valid: issues.append('Recent adjusted closes are missing or invalid; raw closes were not substituted.')
    if duplicates or series.get('quality', {}).get('duplicate_dates'): issues.append('Duplicate provider dates require review.')
    if series.get('quality', {}).get('discarded_rows', 0): issues.append('Provider normalization discarded rows; daily-frequency continuity cannot be assumed.')
    if series.get('quality', {}).get('date_mismatch'): issues.append('The provider daily endpoint and last-trade date disagree.')
    if series.get('source') != 'yfinance': issues.append('Recent provider history is unavailable; legacy database provenance is unverified.')
    if series.get('status') != 'available': issues.append('Provider history is a fallback, not a fresh confirmed daily series.')
    if end is None or (now.date() - end).days > policy['max_history_age_days']: issues.append('The last completed observation exceeds the configured calendar-age limit.')
    # Missing dates are never interpolated. A long unexplained gap in the
    # recent observed window prevents treating multi-session jumps as daily.
    if any((b['date'] - a['date']).days > policy['max_gap_days'] for a, b in zip(recent, recent[1:])):
        issues.append(f"An observed-date gap exceeds {policy['max_gap_days']} calendar days and requires review.")
    tolerance = policy['ma_tolerance']
    def direction(value, band):
        return None if value is None else 'positive' if value > band else 'negative' if value < -band else 'approximately_flat'
    relations = {'price_vs_ma20': direction(price / ma20 - 1, tolerance) if price and ma20 else None,
                 'price_vs_ma50': direction(price / ma50 - 1, tolerance) if price and ma50 else None,
                 'ma20_vs_ma50': direction(ma20 / ma50 - 1, tolerance) if ma20 and ma50 else None,
                 'return20_direction': direction(r20, policy['flat_return_20']),
                 'return60_direction': direction(r60, policy['flat_return_60'])}
    supported = all(v is not None for v in relations.values())
    negative = sum(v == 'negative' for v in relations.values()) if supported else None
    positive = sum(v == 'positive' for v in relations.values()) if supported else None
    observed_classification = 'Unavailable'
    if r20 is not None and r60 is not None and ma20 and ma50:
        if (r20 <= -policy['strong_decline_20'] and negative >= policy['strong_votes_required']
                and relations['price_vs_ma50'] == 'negative' and relations['ma20_vs_ma50'] == 'negative'):
            observed_classification = 'Strong Negative Momentum'
        elif negative >= policy['negative_votes_required'] and (r20 < -policy['flat_return_20'] or r60 < -policy['flat_return_60']):
            observed_classification = 'Negative Momentum'
        elif positive >= policy['positive_votes_required'] and r20 > policy['flat_return_20'] and r60 >= -policy['flat_return_60']:
            observed_classification = 'Positive Momentum'
        else:
            observed_classification = 'Neutral or Mixed Momentum'
    status = 'available' if not issues else 'insufficient_data' if count < 61 or not valid else 'stale_or_unverified'
    return {'methodology_version': METHOD_VERSION, 'status': status,
            'classification': observed_classification if status == 'available' else 'Unavailable',
            'observed_classification': observed_classification, 'issues': issues,
            'as_of': end, 'return20_start': recent[-21]['date'] if len(recent) >= 21 else None,
            'return60_start': recent[-61]['date'] if len(recent) >= 61 else None,
            'source': series.get('source'), 'price_basis': 'adjusted_close',
            'adjusted_close': price, 'return20': r20, 'return60': r60, 'ma20': ma20, 'ma50': ma50,
            'price_vs_ma50_gap': price / ma50 - 1 if price and ma50 else None,
            'relations': relations, 'negative_votes': negative, 'positive_votes': positive,
            'warning': status != 'available' or observed_classification in ('Negative Momentum', 'Strong Negative Momentum'),
            'observations': count, 'policy': policy}


def score_history(series, tier, aversion, policy=None):
    """Retain the baseline daily score, adding a volatility-scaled daily penalty."""
    policy = policy or momentum_policy()
    rows, duplicates = adjusted_observations(series)
    if len(rows) < 121 or duplicates or any(r['adjusted_close'] is None for r in rows):
        return None
    prices = np.array([float(r['adjusted_close']) for r in rows], dtype=float)
    returns = prices[1:] / prices[:-1] - 1
    if not np.isfinite(returns).all() or (returns <= -1).any() or len(returns) < 120:
        return None
    sigma, mean = float(np.std(returns, ddof=1)), float(np.mean(returns))
    if not math.isfinite(sigma) or sigma <= 1e-12:
        return None
    p05 = float(np.quantile(returns, .05, method='linear'))
    cvar = max(0., -float(np.mean(returns[returns <= p05])))
    baseline = mean - aversion * (sigma + cvar)
    trend = assess_momentum(series, policy)
    components = None
    if trend['status'] == 'available':
        # Geometric daily equivalents put multi-session declines back into the
        # same daily fractional-return units as the original score.
        components = [max(0., -math.expm1(math.log1p(trend['return20']) / 20)),
                      max(0., -math.expm1(math.log1p(trend['return60']) / 60)),
                      max(0., -math.expm1(math.log1p(trend['price_vs_ma50_gap']) / 50))]
        normalized = [min(policy['severity_cap'], v / sigma) for v in components]
        severity = sum(w * z for w, z in zip(policy['weights'], normalized))
        severity *= 1 + policy['agreement_strength'] * trend['negative_votes'] / 5
        penalty_type = 'momentum'
    else:
        normalized = None
        severity = policy['unknown_severity']
        penalty_type = 'data_quality_uncertainty'
    coefficient = policy['tier_weights'][tier]
    penalty = coefficient * sigma * severity
    input_prices = [{'date': r['date'].isoformat(), 'adjusted_close': str(r['adjusted_close'])} for r in rows]
    price_hash = hashlib.sha256(json.dumps(input_prices, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return {'observations': len(returns), 'mean_daily_return': mean, 'daily_volatility': sigma,
            'historical_cvar_95_loss': cvar, 'historical_cvar_95_loss_daily': cvar,
            'historical_var_95_loss_daily': max(0., -p05), 'history_through': rows[-1]['date'],
            'history_start': rows[0]['date'], 'history_source': series.get('source'),
            'history_status': series.get('status'), 'history_fetched_at': series.get('fetched_at'),
            'historical_return_annualized': mean * 252, 'historical_volatility_annualized': sigma * math.sqrt(252),
            'baseline_score': baseline, 'selection_score': baseline - penalty,
            'momentum_penalty': penalty, 'penalty_type': penalty_type, 'severity': severity,
            'daily_equivalent_declines': components, 'normalized_components': normalized,
            'momentum_tier_coefficient': coefficient, 'trend': trend,
            'input_prices': input_prices, 'input_price_hash': price_hash,
            'methodology_version': METHOD_VERSION, 'risk_tier': tier, 'risk_aversion': aversion}


def trend_explanation(candidate):
    t = candidate['trend']
    if t['status'] != 'available':
        return (f"Recent Market Trend unavailable or stale. Last completed observation: {t['as_of']}; source: {t['source']}. " + ' '.join(t['issues'])
                + f" An explicit daily uncertainty penalty of {candidate['momentum_penalty']:.8f} was applied; missing momentum was not treated as neutral. ")
    warning = 'Recent Price Weakness Detected. ' if t['warning'] else ''
    return (f"{warning}Recent Market Trend: {t['classification']}, using adjusted daily closes through {t['as_of']}. "
            f"20-session return {t['return20'] * 100:.2f}% (from {t['return20_start']}); 60-session return {t['return60'] * 100:.2f}% (from {t['return60_start']}); "
            f"20-session average ₹{t['ma20']:.2f}; 50-session average ₹{t['ma50']:.2f}; last adjusted close ₹{t['adjusted_close']:.2f}. "
            f"{t['negative_votes']}/5 indicators signal weakness. The daily-unit momentum penalty is {candidate['momentum_penalty']:.8f}, "
            f"with tier coefficient {candidate['momentum_tier_coefficient']:.2f}; baseline score {candidate['baseline_score']:.8f}, adjusted score {candidate['selection_score']:.8f}. "
            "A decline is not an exclusion: this security remained competitive under sector priority and the adjusted risk-aware score, then passed whole-share affordability. "
            "These historical signals do not predict future direction or establish undervaluation. ")


def ranking_evidence(candidate):
    fields = ('methodology_version', 'risk_tier', 'risk_aversion', 'observations', 'history_start', 'history_through',
              'history_source', 'history_status', 'input_price_hash', 'mean_daily_return', 'daily_volatility',
              'historical_cvar_95_loss_daily', 'historical_var_95_loss_daily', 'baseline_score', 'selection_score',
              'momentum_penalty', 'penalty_type', 'severity', 'daily_equivalent_declines', 'normalized_components',
              'momentum_tier_coefficient', 'trend', 'sector_weight', 'quote_date', 'quote_source', 'quote_status')
    return {field: candidate.get(field) for field in fields}
