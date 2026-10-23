"""Authenticated stock research, with explicit portfolio/recommendation ownership."""
from decimal import Decimal
from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from psycopg2.extras import RealDictCursor
from backend.auth import require_authenticated, require_csrf
from backend.dependencies import risk_connection, advisory_connection
from backend.ownership import enforce_ownership
from backend.market_data import get_latest_quotes, provider_state, price_holdings, quote_change_requires_review
from backend.stock_analytics import historical_analysis, json_native

router = APIRouter(prefix='/intelligence', tags=['Stock Intelligence'],
                   dependencies=[Depends(require_authenticated), Depends(require_csrf), Depends(enforce_ownership)])


@router.get('/quotes')
def quotations(conn=Depends(risk_connection)):
    return {'quotes': list(get_latest_quotes(conn).values()), 'market_data': provider_state()}


@router.post('/refresh')
def refresh(conn=Depends(risk_connection)):
    # Cache interval and failure backoff cannot be bypassed by rapid clicks.
    return quotations(conn)


@router.get('/stocks/{ticker}')
def stock(ticker: str, request: Request,
          window: Literal['1M', '3M', '6M', '1Y', 'ALL'] = '1Y',
          history_source: Literal['adjusted', 'raw'] = 'adjusted',
          portfolio_id: UUID | None = None, recommendation_id: UUID | None = None,
          conn=Depends(risk_connection), advisory=Depends(advisory_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute('SELECT security_id::text,ticker_symbol,company_name,sector_name,exchange_code FROM security_master WHERE ticker_symbol=%s', (ticker.upper(),))
        security = cur.fetchone()
    if not security:
        raise HTTPException(404, 'Security not found')
    security = dict(security)
    latest = get_latest_quotes(conn, [security['security_id']])[security['security_id']]
    recommendation = None
    if recommendation_id:
        with advisory.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''SELECT r.rec_id::text,r.stock_ticker,r.recommended_amount,r.shares,r.explanation,
                           r.generated_timestamp,r.status_state::text,r.batch_id::text,b.created_at AS batch_created_at,
                           b.allocation_budget,b.available_buffer FROM recommendation_log r
                           LEFT JOIN recommendation_batch b USING(batch_id)
                           WHERE r.rec_id=%s AND r.user_id=%s AND r.stock_ticker=%s''',
                        (str(recommendation_id), request.state.user_id, ticker.upper()))
            saved = cur.fetchone()
        if not saved:
            raise HTTPException(404, 'Recommendation not found for this security')
        recommendation = dict(saved)
        with advisory.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT investable_buffer,evaluated_at FROM surplus_snapshot WHERE user_id=%s ORDER BY evaluated_at DESC,snapshot_id DESC LIMIT 1", (request.state.user_id,))
            surplus = cur.fetchone()
            cur.execute("SELECT capacity_multiplier,blocked_sectors,reason FROM recommendation_policy WHERE user_id=%s", (request.state.user_id,))
            policy = cur.fetchone()
        recommendation['current_investable_buffer'] = surplus['investable_buffer'] if surplus else None
        recommendation['buffer_evaluated_at'] = surplus['evaluated_at'] if surplus else None
        recommendation['current_policy'] = dict(policy) if policy else None
        original = recommendation['recommended_amount'] / recommendation['shares'] if recommendation['shares'] else None
        price = latest['price']
        new_shares = int(recommendation['recommended_amount'] / price) if price else None
        recommendation.update(original_price=original,
                              latest_estimated_cost=price * recommendation['shares'] if price and recommendation['shares'] else None,
                              affordable_shares_at_recorded_amount=new_shares,
                              requires_regeneration=bool(latest['stale'] or not original or not price or quote_change_requires_review(original, price) or (recommendation['allocation_budget'] is not None and price * recommendation['shares'] > recommendation['allocation_budget'])))
    impact = None
    if portfolio_id:
        rows = price_holdings(conn, str(portfolio_id))
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT cash_balance,target_hhi_limit FROM portfolio WHERE portfolio_id=%s', (str(portfolio_id),))
            portfolio = dict(cur.fetchone())
            cur.execute('SELECT breached_metric::text FROM rebalance_alert WHERE portfolio_id=%s AND resolved_flag=FALSE', (str(portfolio_id),))
            restrictions = [r['breached_metric'] for r in cur.fetchall()]
        owned = next((r for r in rows if r['security_id'] == security['security_id']), None)
        invested = sum((r['market_value'] or Decimal(0) for r in rows), Decimal(0))
        sectors = {}
        for r in rows:
            sectors[r['sector_name']] = sectors.get(r['sector_name'], Decimal(0)) + (r['market_value'] or Decimal(0))
        hhi = sum((v / invested) ** 2 for v in sectors.values()) if invested else None
        complete = all(r['market_value'] is not None for r in rows)
        impact = {'holding': owned, 'invested_value': invested if complete else None, 'priced_holdings_subtotal': invested, 'cash_balance': portfolio['cash_balance'],
                  'sector_weight': sectors.get(security['sector_name'], Decimal(0)) / invested if invested and complete else None,
                  'sector_hhi': hhi if complete else None, 'target_hhi_limit': portfolio['target_hhi_limit'], 'active_restrictions': restrictions,
                  'has_stale_quotes': any(r['quote']['stale'] for r in rows),
                  'valuation_complete': complete}
        if complete and not owned and recommendation and recommendation['latest_estimated_cost'] is not None:
            cost = recommendation['latest_estimated_cost']
            after = invested + cost
            updated = {**sectors, security['sector_name']: sectors.get(security['sector_name'], Decimal(0)) + cost}
            impact['hypothetical'] = {'shares': recommendation['shares'], 'cost': cost, 'invested_value_after': after,
                                      'cash_after': portfolio['cash_balance'] - cost,
                                      'remaining_investable_buffer': recommendation['current_investable_buffer'] - cost if recommendation['current_investable_buffer'] is not None else None,
                                      'affordable_in_portfolio': cost <= portfolio['cash_balance'],
                                      'sector_weight_after': updated[security['sector_name']] / after if after else None,
                                      'sector_hhi_after': sum((v / after) ** 2 for v in updated.values()) if after else None}
    return json_native({'security': security, 'quote': latest, 'market_data': provider_state(),
            'history': historical_analysis(conn, security['security_id'], window, history_source),
            'portfolio_impact': impact, 'recommendation': recommendation})
