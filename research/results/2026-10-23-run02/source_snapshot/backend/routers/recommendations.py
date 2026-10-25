"""Affordability-constrained recommendations from verified market history."""
from datetime import date, datetime
from decimal import Decimal, ROUND_FLOOR
import hashlib
import json
import math
import platform
from importlib.metadata import version
import logging
import traceback
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
import psycopg2
from psycopg2.extras import RealDictCursor

from backend.auth import require_authenticated, require_csrf
from backend.config import settings
from backend.dependencies import advisory_connection, risk_connection
from backend.ownership import enforce_ownership
from backend.schemas import RecommendationDecision
from backend.services import evaluate_portfolio_risk, require_feedback_delivery
from backend.market_data import get_latest_quotes, quote_change_requires_review, get_historical_prices_batch

from backend.market_trends import METHOD_VERSION, momentum_policy, score_history, trend_explanation, ranking_evidence

logger = logging.getLogger(__name__)


class RecommendationRoute(APIRoute):
    """Return safe recommendation errors; log locations without SQL or secrets."""

    def get_route_handler(self):
        handler = super().get_route_handler()

        async def handle(request: Request):
            try:
                return await handler(request)
            except RequestValidationError:
                raise
            except Exception as exc:
                if isinstance(exc, HTTPException) and exc.status_code < 500:
                    raise
                error_id = uuid4().hex
                locations = [f"{Path(frame.filename).name}:{frame.lineno}:{frame.name}"
                             for frame in traceback.extract_tb(exc.__traceback__)]
                logger.error(
                    "Recommendation failure id=%s method=%s route=%s exception=%s sqlstate=%s locations=%s",
                    error_id, request.method, self.path, type(exc).__name__,
                    getattr(exc, "pgcode", None), " -> ".join(locations),
                )
                feedback_pending = (isinstance(exc, HTTPException) and isinstance(exc.detail, dict)
                                    and exc.detail.get("message") == "Risk feedback is queued for retry")
                message = ("Risk feedback is still synchronizing. Retry shortly; saved recommendations remain available."
                           if feedback_pending else
                           "Recommendations could not be loaded or updated. Please retry; saved recommendations remain available.")
                if isinstance(exc, HTTPException):
                    code = exc.status_code
                else:
                    code = 503 if isinstance(exc, psycopg2.Error) else 500
                return JSONResponse(status_code=code, content={"detail": message, "error_id": error_id},
                                    headers=exc.headers if isinstance(exc, HTTPException) else None)

        return handle


router = APIRouter(route_class=RecommendationRoute, prefix="/recommendations", tags=["Recommendations"], dependencies=[Depends(require_authenticated), Depends(require_csrf), Depends(enforce_ownership)])
BASE_CAPACITY = {"CONSERVATIVE": Decimal("0.25"), "MODERATE": Decimal("0.50"), "AGGRESSIVE": Decimal("0.75")}

# Use the complement of the existing tier allocation capacity as the observed
# risk penalty, keeping the ranking aligned with the established tier policy.
RISK_AVERSION = {tier: float(Decimal("1") - capacity) for tier, capacity in BASE_CAPACITY.items()}
OBSERVATION_WINDOW = 252
MINIMUM_OBSERVATIONS = 120


def _json_safe(value):
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _historical_candidates(cur, blocked_sectors, held_security_ids):
    cur.execute("""SELECT security_id::text,ticker_symbol,company_name,sector_name
                   FROM security_master WHERE NOT (sector_name=ANY(%s))
                   AND NOT (security_id::text=ANY(%s)) ORDER BY ticker_symbol""",
                (list(blocked_sectors), list(held_security_ids)))
    return [dict(row) for row in cur.fetchall()]


def _load_portfolio_context(risk, user_id):
    with risk.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT portfolio_id::text FROM portfolio WHERE user_id=%s ORDER BY portfolio_id", (user_id,))
        portfolio_ids = [row["portfolio_id"] for row in cur.fetchall()]
    # Risk evaluation switches to SERIALIZABLE and requires an idle connection.
    risk.commit()
    risk_summaries = []
    for portfolio_id in portfolio_ids:
        evaluation = evaluate_portfolio_risk(risk, portfolio_id)
        risk_summaries.append(_json_safe(evaluation["summary"]))
    return portfolio_ids, risk_summaries


def _market_context(risk, user_id, blocked, tier):
    aversion = RISK_AVERSION[tier]
    with risk.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT h.portfolio_id::text,h.security_id::text,sm.ticker_symbol,
                      sm.sector_name,h.quantity,h.average_buy_price,
                      latest.close_price,latest.trade_date
               FROM portfolio p JOIN holding h USING(portfolio_id)
               JOIN security_master sm USING(security_id)
               LEFT JOIN LATERAL (
                   SELECT close_price,trade_date FROM daily_market_quote q
                   WHERE q.security_id=h.security_id ORDER BY q.trade_date DESC LIMIT 1
               ) latest ON TRUE
               WHERE p.user_id=%s AND h.quantity>0
               ORDER BY h.portfolio_id,h.security_id""", (user_id,),
        )
        holdings = [dict(row) for row in cur.fetchall()]
        held_ids = sorted({row["security_id"] for row in holdings})
        quotes = get_latest_quotes(risk)
        for row in holdings:
            quote = quotes[row['security_id']]
            row['close_price'] = quote['price']
            row['trade_date'] = quote['price_date']
        sector_values: dict[str, Decimal] = {}
        for row in holdings:
            if row["close_price"] is not None:
                sector_values[row["sector_name"]] = sector_values.get(row["sector_name"], Decimal("0")) + Decimal(row["close_price"]) * row["quantity"]
        total_equity_value = sum(sector_values.values(), Decimal("0"))
        sector_weights = {
            sector: (value / total_equity_value if total_equity_value else Decimal("0"))
            for sector, value in sector_values.items()
        }
        cur.execute("SELECT MAX(trade_date) AS market_data_through FROM daily_market_quote WHERE trade_date<=CURRENT_DATE")
        market_data_through = cur.fetchone()["market_data_through"]
        candidates = _historical_candidates(cur, blocked, held_ids)

    histories = get_historical_prices_batch(risk, [c['security_id'] for c in candidates], '1Y')
    policy = momentum_policy()
    evaluated = []
    excluded = []
    for candidate in candidates:
        quote = quotes[candidate['security_id']]
        if quote.get('error_kind') == 'missing_symbol' or not quote['price']:
            excluded.append({'ticker': candidate['ticker_symbol'], 'reason': 'unresolved_listing_or_missing_price'})
            continue
        metrics = score_history(histories[candidate['security_id']], tier, aversion, policy)
        if metrics is None:
            series = histories[candidate['security_id']]
            excluded.append({'ticker': candidate['ticker_symbol'], 'reason': 'insufficient_or_invalid_consistent_adjusted_history_120_returns_required',
                             'history_source': series.get('source'), 'history_status': series.get('status')})
            continue
        candidate.update(metrics)
        candidate['close_price'] = quote['price']
        candidate['quote_date'] = quote['observed_at'] or quote['price_date']
        candidate['quote_source'] = quote['source']
        candidate['quote_status'] = quote['status']
        candidate['listing_resolved'] = True
        candidate['sector_weight'] = sector_weights.get(candidate['sector_name'], Decimal('0'))
        candidate['size_weight'] = 1 / (candidate['daily_volatility'] ** aversion)
        evaluated.append(candidate)
    through = max((c['history_through'] for c in evaluated), default=market_data_through)
    return holdings, sector_weights, evaluated, through, excluded


def _select_candidates(candidates):
    # Prioritize sectors with lower saved exposure, then measured historical
    # score within that diversification order. Ties are stable by ticker.
    ranked = sorted(candidates, key=lambda row: (row["sector_weight"], -row["selection_score"], row["ticker_symbol"]))
    selected, sectors = [], set()
    for candidate in ranked:
        if candidate["sector_name"] in sectors:
            continue
        selected.append(candidate)
        sectors.add(candidate["sector_name"])
        if len(selected) == 3:
            break
    return selected


def _return_rows(cur, user_id, batch_id, pending_only=False):
    cur.execute(
        """SELECT rec_id::text,user_id::text,stock_ticker,target_allocation_pct,
                  recommended_amount,status_state::text,batch_id::text,shares,explanation,ranking_evidence,
                  generated_timestamp
           FROM recommendation_log WHERE user_id=%s AND batch_id IS NOT DISTINCT FROM %s::uuid
             AND (%s=FALSE OR status_state='PENDING')
           ORDER BY stock_ticker,rec_id""", (user_id, batch_id, pending_only),
    )
    return [dict(row) for row in cur.fetchall()]


@router.post("/{user_id}/generate", status_code=status.HTTP_201_CREATED)
def generate_recommendations(
    user_id: UUID,
    advisory=Depends(advisory_connection),
    risk=Depends(risk_connection),
):
    user_id_text = str(user_id)
    portfolio_ids, risk_summaries = _load_portfolio_context(risk, user_id_text)
    delivery = require_feedback_delivery(risk, advisory)

    with advisory:
        with advisory.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT risk_tolerance_tier::text FROM user_profile WHERE user_id=%s FOR UPDATE", (user_id_text,))
            profile = cur.fetchone()
            if not profile:
                raise HTTPException(status_code=404, detail="User not found")
            tier = profile["risk_tolerance_tier"]
            cur.execute(
                "SELECT investable_buffer FROM surplus_snapshot WHERE user_id=%s ORDER BY evaluated_at DESC,snapshot_id DESC LIMIT 1",
                (user_id_text,),
            )
            snapshot = cur.fetchone()
            if not snapshot:
                raise HTTPException(status_code=409, detail="Evaluate cashflow before generating recommendations")
            buffer = Decimal(snapshot["investable_buffer"])
            cur.execute(
                "SELECT capacity_multiplier,blocked_sectors,reason FROM recommendation_policy WHERE user_id=%s",
                (user_id_text,),
            )
            policy = cur.fetchone()
            multiplier = Decimal(policy["capacity_multiplier"]) if policy else Decimal("1")
            blocked = sorted(set(policy["blocked_sectors"] or [])) if policy else []
            policy_reason = policy["reason"] if policy else "No active risk breach; normal allocation policy applies."
            budget = (buffer * BASE_CAPACITY[tier] * multiplier).quantize(Decimal("0.01"), rounding=ROUND_FLOOR)

            holdings, sector_weights, candidates, market_data_through, data_exclusions = _market_context(risk, user_id_text, blocked, tier)
            active_alerts = []
            if portfolio_ids:
                with risk.cursor(cursor_factory=RealDictCursor) as risk_cur:
                    risk_cur.execute(
                        """SELECT a.portfolio_id::text,a.breached_metric::text,a.drift_magnitude_pct
                           FROM rebalance_alert a JOIN portfolio p USING(portfolio_id)
                           WHERE p.user_id=%s AND a.portfolio_id=ANY(%s::uuid[])
                             AND a.resolved_flag=FALSE
                           ORDER BY a.portfolio_id,a.breached_metric""",
                        (user_id_text, portfolio_ids),
                    )
                    active_alerts = [dict(row) for row in risk_cur.fetchall()]

            # Logarithmic price bands: each configured 2% band is stable across
            # polling timestamps. Actual exact price is still used for sizing.
            step = math.log1p(settings.RECOMMENDATION_PRICE_CHANGE_FRACTION)
            def stable_candidate(row):
                omitted = {'close_price', 'quote_date', 'quote_source', 'quote_status', 'sector_weight', 'history_fetched_at', 'trend', 'input_prices'}
                return {**{k: v for k, v in row.items() if k not in omitted},
                        'momentum_signature': {
                            'status': row['trend']['status'], 'classification': row['trend']['classification'],
                            'as_of': row['trend']['as_of'], 'relations': row['trend']['relations'],
                            'return20_band': math.floor(row['trend']['return20'] / settings.MOMENTUM_FINGERPRINT_RETURN_STEP) if row['trend']['return20'] is not None else None,
                            'return60_band': math.floor(row['trend']['return60'] / settings.MOMENTUM_FINGERPRINT_RETURN_STEP) if row['trend']['return60'] is not None else None},
                        'price_band': math.floor(math.log(float(row['close_price'])) / step),
                        'quote_basis': 'provider_valid' if row['quote_status'] in ('latest_intraday_observation', 'last_market_close') else 'dated_or_unavailable',
                        'sector_weight': round(float(row['sector_weight']), 2)}
            preview_selected = _select_candidates(candidates) if buffer > 0 and budget > 0 else []
            preview_weight = sum((Decimal(str(c['size_weight'])) for c in preview_selected), Decimal(0))
            affordable_signature = {
                c['security_id']: int(((budget * Decimal(str(c['size_weight'])) / preview_weight).quantize(Decimal('.01'), rounding=ROUND_FLOOR)) / Decimal(str(c['close_price'])))
                for c in preview_selected
            }
            fingerprint_data = {
                "methodology_version": METHOD_VERSION, "momentum_policy": momentum_policy(),
                "buffer": buffer,
                "tier": tier,
                "capacity_multiplier": multiplier,
                "blocked_sectors": blocked,
                "policy_reason": policy_reason,
                "alerts": active_alerts,
                "risk_summaries": risk_summaries,
                "risk_limits": {
                    "var_fraction": settings.RISK_VAR_LIMIT_PERCENT,
                    "daily_volatility": settings.RISK_DAILY_VOLATILITY_LIMIT,
                    "reconsider_days": settings.RECOMMENDATION_RECONSIDER_DAYS,
                },
                "portfolios": portfolio_ids,
                "holdings": [{k: v for k, v in h.items() if k not in {"close_price", "trade_date"}} for h in holdings],
                "sector_weights": {k: round(float(v), 2) for k, v in sector_weights.items()},
                "market_data_through": market_data_through,
                "candidate_history": [stable_candidate(c) for c in candidates],
                "price_change_fraction": settings.RECOMMENDATION_PRICE_CHANGE_FRACTION,
                "whole_share_affordability": affordable_signature, "data_exclusions": data_exclusions,
            }
            fingerprint = hashlib.sha256(
                json.dumps(_json_safe(fingerprint_data), sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()

            cur.execute(
                """SELECT batch_id::text,user_id::text,input_fingerprint,available_buffer,
                          allocation_budget,outcome_reason,created_at
                   FROM recommendation_batch
                   WHERE user_id=%s AND input_fingerprint=%s
                   ORDER BY created_at DESC LIMIT 1""", (user_id_text, fingerprint),
            )
            prior = cur.fetchone()
            if prior:
                cur.execute(
                    """SELECT COUNT(*) AS pending_count FROM recommendation_log
                       WHERE user_id=%s AND batch_id=%s AND status_state='PENDING'""",
                    (user_id_text, prior["batch_id"]),
                )
                has_pending = cur.fetchone()["pending_count"] > 0
                cur.execute(
                    """SELECT created_at >= now() - (%s * interval '1 day') AS within_reconsideration
                       FROM recommendation_batch WHERE batch_id=%s""",
                    (settings.RECOMMENDATION_RECONSIDER_DAYS, prior["batch_id"]),
                )
                within_reconsideration = bool(cur.fetchone()["within_reconsideration"])
                if has_pending or within_reconsideration:
                    return {
                        "batch_id": prior["batch_id"], "available_buffer": prior["available_buffer"],
                        "allocation_budget": prior["allocation_budget"], "reason": prior["outcome_reason"],
                        "recommendations": _return_rows(cur, user_id_text, prior["batch_id"]),
                        "reused": True, "freshness": "unchanged_inputs",
                        "feedback_events_processed": delivery["events_applied"],
                    }

            # Legacy batches have no reproducible price snapshot. A user-requested
            # generation may supersede them, preserving all recorded evidence.
            selected = _select_candidates(candidates) if buffer > 0 and budget > 0 else []
            if buffer <= 0:
                reason = "No recommendation was created because your current investable surplus is zero."
            elif budget <= 0:
                reason = "No recommendation was created because active risk policy leaves no allocation budget."
            elif not selected:
                reason = "No securities met the market-history, holdings, and active sector-policy requirements."
            else:
                reason = "Candidates were screened against current holdings, active risk restrictions, up to 252 completed daily returns and recent market momentum; unavailable trend evidence receives an explicit uncertainty penalty."

            cur.execute(
                """INSERT INTO recommendation_batch
                   (user_id,input_fingerprint,available_buffer,allocation_budget,outcome_reason,ranking_snapshot,created_at)
                   VALUES (%s,%s,%s,%s,%s,%s::jsonb,clock_timestamp())
                   RETURNING batch_id::text,created_at""",
                (user_id_text, fingerprint, buffer, budget, reason,
                 json.dumps(_json_safe({'methodology_version': METHOD_VERSION, 'baseline_version': 'risk_only_252_v1',
                     'decision_inputs': fingerprint_data, 'eligible_candidates': candidates, 'data_exclusions': data_exclusions,
                     'selected_tickers': [c['ticker_symbol'] for c in selected],
                     'policy': momentum_policy(), 'risk_tier': tier,
                     'runtime_versions': {'python': platform.python_version(), 'numpy': version('numpy'), 'yfinance': version('yfinance')},
                     'selection_order': 'sector_weight_ascending, adjusted_daily_score_descending, ticker_ascending; one security per sector, at most three',
                     'historical_data_through': market_data_through}), allow_nan=False)),
            )
            batch = cur.fetchone()
            batch_id = batch["batch_id"]
            # A changed input signature makes an undecided older batch stale;
            # preserve it for audit under an explicit non-decision state.
            cur.execute(
                """UPDATE recommendation_log r SET status_state='SUPERSEDED'
                   FROM recommendation_batch b
                   WHERE r.batch_id=b.batch_id AND r.user_id=%s
                     AND r.status_state='PENDING' AND b.input_fingerprint IS DISTINCT FROM %s""",
                (user_id_text, fingerprint),
            )

            cur.execute("UPDATE recommendation_log SET status_state='SUPERSEDED' WHERE user_id=%s AND batch_id IS NULL AND status_state='PENDING'", (user_id_text,))

            last_decisions = {}
            cur.execute(
                """SELECT DISTINCT ON (r.stock_ticker) r.stock_ticker,r.status_state::text,
                          b.input_fingerprint
                   FROM recommendation_log r LEFT JOIN recommendation_batch b USING(batch_id)
                   WHERE r.user_id=%s AND r.status_state IN ('ACCEPTED','REJECTED')
                   ORDER BY r.stock_ticker,r.generated_timestamp DESC,r.rec_id DESC""",
                (user_id_text,),
            )
            for row in cur.fetchall():
                last_decisions[row["stock_ticker"]] = row

            inserted = []
            spent = Decimal("0")
            weight_total = sum((Decimal(str(row["size_weight"])) for row in selected), Decimal("0"))
            for candidate in selected:
                price = Decimal(str(candidate["close_price"]))
                weight = Decimal(str(candidate["size_weight"]))
                allocation_budget = (budget * weight / weight_total).quantize(Decimal("0.01"), rounding=ROUND_FLOOR)
                shares = int((allocation_budget / price).to_integral_value(rounding=ROUND_FLOOR)) if price > 0 else 0
                amount = price * shares
                if shares < 1 or spent + amount > min(budget, buffer):
                    continue

                sector_weight = Decimal(candidate["sector_weight"])
                volatility_pct = candidate["historical_volatility_annualized"] * 100
                cvar_pct = candidate["historical_cvar_95_loss_daily"] * 100
                historical_return_pct = candidate["historical_return_annualized"] * 100
                explanation = (
                    f"Eligible: this stock is not in your saved holdings and its sector is not restricted by an active risk policy. "
                    f"It ranked using {candidate['observations']} recent daily returns (up to {OBSERVATION_WINDOW} sessions) under your {tier.lower()} risk preference: "
                    f"observed annualized average return {historical_return_pct:.1f}%, volatility {volatility_pct:.1f}%, and one-day historical CVaR 95% loss {cvar_pct:.2f}% of value. "
                    f"The comparison applies a {RISK_AVERSION[tier]:.2f} volatility and tail-loss penalty; historical measures are not forecasts. "
                    f"The sector is {sector_weight * 100:.1f}% of your currently invested value; its estimated share is {shares} whole share(s) "
                    f"at ₹{price:.2f}, costing ₹{amount:.2f} within the ₹{allocation_budget:.2f} portion of your ₹{budget:.2f} policy budget; "
                    f"the portion is weighted inversely to observed volatility and adjusted for your risk preference. "
                    f"Price basis: {candidate['quote_source']} · {candidate['quote_status']} · {candidate['quote_date']}; VaR and volatility breach limits were refreshed for your saved portfolios. "
                    f"No separate candidate-level CVaR breach limit is configured; historical CVaR is used only in ranking."
                )
                explanation += " " + trend_explanation(candidate)
                prior_decision = last_decisions.get(candidate["ticker_symbol"])
                if prior_decision and prior_decision["status_state"] == "REJECTED":
                    previous_fingerprint = prior_decision["input_fingerprint"]
                    if previous_fingerprint is None:
                        explanation += " You previously declined this idea; its original input snapshot was not recorded, so it was re-evaluated using the current data."
                    elif previous_fingerprint != fingerprint:
                        explanation += " You previously declined this idea; it was reconsidered because saved financial, portfolio, policy, or market inputs changed."
                    else:
                        explanation += f" You previously declined this idea; it was reconsidered after the configured {settings.RECOMMENDATION_RECONSIDER_DAYS}-day review interval."
                elif prior_decision and prior_decision["status_state"] == "ACCEPTED":
                    explanation += " You previously accepted this as intent; it is not treated as owned unless it appears in your saved holdings."
                cur.execute(
                    """INSERT INTO recommendation_log
                       (user_id,stock_ticker,target_allocation_pct,recommended_amount,status_state,batch_id,shares,explanation,ranking_evidence,generated_timestamp)
                       VALUES (%s,%s,%s,%s,'PENDING',%s,%s,%s,%s::jsonb,clock_timestamp())
                       RETURNING rec_id::text,stock_ticker,target_allocation_pct,recommended_amount,
                                 status_state::text,batch_id::text,shares,explanation,ranking_evidence,generated_timestamp""",
                    (user_id_text, candidate["ticker_symbol"], amount / buffer * 100, amount, batch_id, shares, explanation, json.dumps(_json_safe({**ranking_evidence(candidate), "allocation_budget": allocation_budget, "quote_price": price}), allow_nan=False)),
                )
                inserted.append(dict(cur.fetchone()))
                spent += amount

            cur.execute("UPDATE recommendation_batch SET ranking_snapshot=ranking_snapshot || %s::jsonb WHERE batch_id=%s", (
                json.dumps(_json_safe({'recorded_recommendations': inserted, 'total_recorded_cost': spent}), allow_nan=False), batch_id))

            if selected and not inserted:
                reason = "Eligible securities were found, but none could be purchased as a whole share within the allocation budget."
                cur.execute("UPDATE recommendation_batch SET outcome_reason=%s WHERE batch_id=%s", (reason, batch_id))
            return {
                "batch_id": batch_id, "available_buffer": buffer, "allocation_budget": budget,
                "total_recommended_cost": spent, "policy_multiplier": multiplier,
                "blocked_sectors": blocked, "reason": reason, "reused": False,
                "freshness": "new_input_signature", "methodology_version": METHOD_VERSION, "feedback_events_processed": delivery["events_applied"],
                "history_window_sessions": OBSERVATION_WINDOW,
                "minimum_history_sessions": MINIMUM_OBSERVATIONS,
                "risk_aversion": RISK_AVERSION[tier], "recommendations": inserted,
            }


@router.get("/{user_id}")
def list_recommendations(
    user_id: UUID,
    status_filter: str | None = Query(default=None, alias="status"),
    conn=Depends(advisory_connection),
    risk=Depends(risk_connection),
):
    supported = {"PENDING", "ACCEPTED", "REJECTED", "SUPERSEDED"}
    if status_filter and status_filter not in supported:
        raise HTTPException(status_code=422, detail="status must be PENDING, ACCEPTED, REJECTED, or SUPERSEDED")
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT batch_id::text FROM recommendation_batch WHERE user_id=%s ORDER BY created_at DESC,batch_id DESC LIMIT 1", (str(user_id),))
        latest_batch = cur.fetchone()
        latest_batch_id = latest_batch["batch_id"] if latest_batch else None
        query = """SELECT r.rec_id::text,r.user_id::text,r.stock_ticker,r.target_allocation_pct,
                           r.recommended_amount,r.status_state::text,r.batch_id::text,r.shares,
                           r.explanation,r.ranking_evidence,r.generated_timestamp,b.created_at AS batch_created_at,
                           b.allocation_budget AS saved_allocation_budget,b.available_buffer AS saved_available_buffer,
                           (r.batch_id=%s::uuid) AS is_latest_batch
                    FROM recommendation_log r LEFT JOIN recommendation_batch b USING(batch_id)
                    WHERE r.user_id=%s"""
        values = [latest_batch_id, str(user_id)]
        if status_filter:
            query += " AND r.status_state=%s"
            values.append(status_filter)
        query += " ORDER BY b.created_at DESC NULLS LAST,r.generated_timestamp DESC,r.rec_id"
        cur.execute(query, values)
        rows = [dict(row) for row in cur.fetchall()]
    quotes = {q['ticker_symbol']: q for q in get_latest_quotes(risk).values()}
    for row in rows:
        q = quotes.get(row['stock_ticker'])
        original = row['recommended_amount'] / row['shares'] if row['shares'] else None
        row['methodology_update_required'] = not row.get('ranking_evidence') or row['ranking_evidence'].get('methodology_version') != METHOD_VERSION
        row['original_price'] = original
        row['affordable_shares_at_recorded_amount'] = int(row['recommended_amount'] / q['price']) if q and q['price'] else None
        row['quote'] = q
        row['latest_estimated_cost'] = q['price'] * row['shares'] if q and q['price'] and row['shares'] else None
        row['requires_regeneration'] = bool(row['methodology_update_required'] or not q or q['stale'] or not original or not q['price']
            or quote_change_requires_review(original, q['price'])
            or (row['saved_allocation_budget'] is not None and row['latest_estimated_cost'] > row['saved_allocation_budget']))
    totals = {}
    for row in rows:
        if row['status_state'] in ('PENDING', 'ACCEPTED') and row['batch_id']:
            totals[row['batch_id']] = totals.get(row['batch_id'], Decimal(0)) + (row['latest_estimated_cost'] or Decimal(0))
    for row in rows:
        if row['saved_allocation_budget'] is not None and totals.get(row['batch_id'], Decimal(0)) > row['saved_allocation_budget']:
            row['requires_regeneration'] = True
    return rows


@router.post("/{user_id}/{recommendation_id}/decision")
def decide_recommendation(
    user_id: UUID,
    recommendation_id: UUID,
    body: RecommendationDecision,
    conn=Depends(advisory_connection),
    risk=Depends(risk_connection),
):
    if body.decision == 'ACCEPTED':
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT r.stock_ticker,r.recommended_amount,r.shares,r.ranking_evidence,r.batch_id::text,b.allocation_budget,b.available_buffer FROM recommendation_log r LEFT JOIN recommendation_batch b USING(batch_id) WHERE r.rec_id=%s AND r.user_id=%s", (str(recommendation_id), str(user_id)))
            saved = cur.fetchone()
        if not saved:
            raise HTTPException(404, 'Recommendation not found')
        if not saved['ranking_evidence'] or saved['ranking_evidence'].get('methodology_version') != METHOD_VERSION:
            raise HTTPException(409, 'This saved recommendation predates the trend-aware methodology. Check for updates before accepting; its original evidence is preserved.')
        quotes = {q['ticker_symbol']: q for q in get_latest_quotes(risk).values()}
        q = quotes.get(saved['stock_ticker'])
        evidence = saved['ranking_evidence']
        if q and q.get('fresh_enough_for_operation'):
            series = get_historical_prices_batch(risk, [q['security_id']], '1Y')[q['security_id']]
            current = score_history(series, evidence['risk_tier'], float(evidence['risk_aversion']), momentum_policy())
            if (not current or current['input_price_hash'] != evidence.get('input_price_hash')
                    or current['trend']['status'] != evidence.get('trend', {}).get('status')
                    or momentum_policy() != evidence.get('trend', {}).get('policy')):
                raise HTTPException(409, 'Historical ranking or recent-trend evidence changed or cannot be revalidated. Check for updates; the saved decision evidence remains unchanged.')
        original = saved['recommended_amount'] / saved['shares'] if saved['shares'] else None
        if not q or not q['price'] or not original or not q.get('fresh_enough_for_operation', False):
            raise HTTPException(409, 'Acceptance needs a sufficiently recent yfinance observation or latest dated market close. The saved recommendation is retained; historical fallback cannot validate affordability.')
        if quote_change_requires_review(original, q['price']):
            raise HTTPException(409, 'The price changed materially. Check for updates before accepting; the original estimate is retained.')
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT stock_ticker,shares FROM recommendation_log WHERE user_id=%s AND batch_id=%s AND status_state IN ('PENDING','ACCEPTED')", (str(user_id), saved['batch_id']))
            batch_rows = cur.fetchall()
        costs = [quotes.get(r['stock_ticker'], {}).get('price') * r['shares']
                 for r in batch_rows if quotes.get(r['stock_ticker'], {}).get('price') and quotes.get(r['stock_ticker'], {}).get('fresh_enough_for_operation') and r['shares']]
        if (len(costs) != len(batch_rows) or saved['allocation_budget'] is None or saved['available_buffer'] is None
                or sum(costs, Decimal(0)) > min(saved['allocation_budget'], saved['available_buffer'])):
            raise HTTPException(409, 'The proposed batch no longer fits its saved whole-share budget. Check for updates; no recorded estimate was changed.')
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """UPDATE recommendation_log SET status_state=%s
                   WHERE rec_id=%s AND user_id=%s AND status_state='PENDING'
                   RETURNING rec_id::text,stock_ticker,status_state::text,recommended_amount,shares""",
                (body.decision, str(recommendation_id), str(user_id)),
            )
            row = cur.fetchone()
            if not row:
                cur.execute("SELECT status_state::text FROM recommendation_log WHERE rec_id=%s AND user_id=%s", (str(recommendation_id), str(user_id)))
                existing = cur.fetchone()
                if not existing:
                    raise HTTPException(status_code=404, detail="Recommendation not found")
                raise HTTPException(status_code=409, detail=f"Recommendation already {existing['status_state'].lower()}")
            result = dict(row)
    if body.decision == "ACCEPTED":
        result["trade_execution"] = "not_executed; acceptance records user intent only"
    return result


@router.get("/{user_id}/batches/{batch_id}/evidence")
def batch_evidence(user_id: UUID, batch_id: UUID, conn=Depends(advisory_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT batch_id::text,created_at,input_fingerprint,ranking_snapshot FROM recommendation_batch WHERE batch_id=%s AND user_id=%s", (str(batch_id), str(user_id)))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, 'Recommendation batch not found')
    return dict(row)
