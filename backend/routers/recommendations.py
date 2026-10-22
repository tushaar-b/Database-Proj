"""Affordability-constrained recommendations from verified market history."""
from datetime import date, datetime
from decimal import Decimal, ROUND_FLOOR
import hashlib
import json
import math
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
    cur.execute(
        """WITH prices AS (
                 SELECT security_id,trade_date,
                        COALESCE(adjusted_close,close_price)::double precision AS price,
                        LAG(COALESCE(adjusted_close,close_price)::double precision)
                            OVER (PARTITION BY security_id ORDER BY trade_date) AS previous_price
                 FROM daily_market_quote
             ), returns AS (
                 SELECT security_id,trade_date,price/NULLIF(previous_price,0)-1 AS daily_return
                 FROM prices WHERE previous_price>0
             ), ranked AS (
                 SELECT security_id,trade_date,daily_return,
                        ROW_NUMBER() OVER (PARTITION BY security_id ORDER BY trade_date DESC) AS observation_rank
                 FROM returns WHERE daily_return IS NOT NULL
             ), stats AS (
                 SELECT security_id,COUNT(*)::integer AS observations,
                        AVG(daily_return) AS mean_daily_return,
                        STDDEV_SAMP(daily_return) AS daily_volatility,
                        PERCENTILE_CONT(0.05) WITHIN GROUP (ORDER BY daily_return) AS return_p05,
                        MAX(trade_date) AS history_through
                 FROM ranked WHERE observation_rank<=%s GROUP BY security_id
             ), tails AS (
                 SELECT r.security_id,GREATEST(0,-AVG(r.daily_return)) AS historical_cvar_95_loss
                 FROM ranked r JOIN stats s USING(security_id)
                 WHERE r.observation_rank<=%s AND r.daily_return<=s.return_p05
                 GROUP BY r.security_id
             ), latest AS (
                 SELECT DISTINCT ON (security_id) security_id,close_price,trade_date
                 FROM daily_market_quote ORDER BY security_id,trade_date DESC
             )
             SELECT sm.security_id::text,sm.ticker_symbol,sm.company_name,sm.sector_name,
                    latest.close_price,latest.trade_date AS quote_date,
                    stats.observations,stats.mean_daily_return,stats.daily_volatility,
                    tails.historical_cvar_95_loss,stats.history_through
             FROM security_master sm
             JOIN latest USING(security_id)
             JOIN stats USING(security_id)
             JOIN tails USING(security_id)
             WHERE stats.observations >= %s
               AND stats.daily_volatility IS NOT NULL AND stats.daily_volatility > 0
               AND NOT (sm.sector_name=ANY(%s))
               AND NOT (sm.security_id::text=ANY(%s))
             ORDER BY sm.ticker_symbol""",
        (OBSERVATION_WINDOW, OBSERVATION_WINDOW, MINIMUM_OBSERVATIONS,
         list(blocked_sectors), list(held_security_ids)),
    )
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
        sector_values: dict[str, Decimal] = {}
        for row in holdings:
            if row["close_price"] is not None:
                sector_values[row["sector_name"]] = sector_values.get(row["sector_name"], Decimal("0")) + Decimal(row["close_price"]) * row["quantity"]
        total_equity_value = sum(sector_values.values(), Decimal("0"))
        sector_weights = {
            sector: (value / total_equity_value if total_equity_value else Decimal("0"))
            for sector, value in sector_values.items()
        }
        cur.execute("SELECT MAX(trade_date) AS market_data_through FROM daily_market_quote")
        market_data_through = cur.fetchone()["market_data_through"]
        candidates = _historical_candidates(cur, blocked, held_ids)

    for candidate in candidates:
        mean = float(candidate["mean_daily_return"])
        volatility = float(candidate["daily_volatility"])
        cvar = float(candidate["historical_cvar_95_loss"])
        # Daily historical return less a tier-weighted volatility and tail-loss
        # penalty; it orders securities only and does not predict future return.
        candidate["historical_return_annualized"] = mean * OBSERVATION_WINDOW
        candidate["historical_volatility_annualized"] = volatility * math.sqrt(OBSERVATION_WINDOW)
        candidate["historical_cvar_95_loss_daily"] = cvar
        candidate["selection_score"] = mean - aversion * (volatility + cvar)
        candidate["sector_weight"] = sector_weights.get(candidate["sector_name"], Decimal("0"))
        candidate["size_weight"] = 1 / (volatility ** aversion)
    return holdings, sector_weights, candidates, market_data_through


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
                  recommended_amount,status_state::text,batch_id::text,shares,explanation,
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

            holdings, sector_weights, candidates, market_data_through = _market_context(risk, user_id_text, blocked, tier)
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

            fingerprint_data = {
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
                "holdings": holdings,
                "sector_weights": sector_weights,
                "market_data_through": market_data_through,
                "candidate_history": candidates,
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

            # Legacy pending rows have no captured fingerprint. Keep them active
            # for a user decision instead of silently replacing them.
            cur.execute(
                """SELECT DISTINCT r.batch_id::text AS batch_id FROM recommendation_log r
                   LEFT JOIN recommendation_batch b USING(batch_id)
                   WHERE r.user_id=%s AND r.status_state='PENDING'
                     AND (b.batch_id IS NULL OR b.input_fingerprint IS NULL)
                   LIMIT 1""", (user_id_text,),
            )
            legacy_pending = cur.fetchone()
            if legacy_pending:
                return {
                    "batch_id": legacy_pending["batch_id"], "available_buffer": buffer, "allocation_budget": budget,
                    "reason": "An earlier pending batch is retained for your decision; no duplicate batch was created.",
                    "recommendations": _return_rows(cur, user_id_text, legacy_pending["batch_id"], pending_only=True),
                    "reused": True, "freshness": "legacy_pending_batch",
                    "feedback_events_processed": delivery["events_applied"],
                }

            selected = _select_candidates(candidates) if buffer > 0 and budget > 0 else []
            if buffer <= 0:
                reason = "No recommendation was created because your current investable surplus is zero."
            elif budget <= 0:
                reason = "No recommendation was created because active risk policy leaves no allocation budget."
            elif not selected:
                reason = "No securities met the market-history, holdings, and active sector-policy requirements."
            else:
                reason = "Candidates were screened against current holdings, active risk restrictions, and 252-session market history."

            cur.execute(
                """INSERT INTO recommendation_batch
                   (user_id,input_fingerprint,available_buffer,allocation_budget,outcome_reason)
                   VALUES (%s,%s,%s,%s,%s)
                   RETURNING batch_id::text,created_at""",
                (user_id_text, fingerprint, buffer, budget, reason),
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
                    f"Latest quote: {candidate['quote_date']}; VaR and volatility breach limits were refreshed for your saved portfolios. "
                    f"No separate candidate-level CVaR breach limit is configured; historical CVaR is used only in ranking."
                )
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
                       (user_id,stock_ticker,target_allocation_pct,recommended_amount,status_state,batch_id,shares,explanation)
                       VALUES (%s,%s,%s,%s,'PENDING',%s,%s,%s)
                       RETURNING rec_id::text,stock_ticker,target_allocation_pct,recommended_amount,
                                 status_state::text,batch_id::text,shares,explanation,generated_timestamp""",
                    (user_id_text, candidate["ticker_symbol"], amount / buffer * 100, amount, batch_id, shares, explanation),
                )
                inserted.append(dict(cur.fetchone()))
                spent += amount

            if selected and not inserted:
                reason = "Eligible securities were found, but none could be purchased as a whole share within the allocation budget."
                cur.execute("UPDATE recommendation_batch SET outcome_reason=%s WHERE batch_id=%s", (reason, batch_id))
            return {
                "batch_id": batch_id, "available_buffer": buffer, "allocation_budget": budget,
                "total_recommended_cost": spent, "policy_multiplier": multiplier,
                "blocked_sectors": blocked, "reason": reason, "reused": False,
                "freshness": "new_input_signature", "feedback_events_processed": delivery["events_applied"],
                "history_window_sessions": OBSERVATION_WINDOW,
                "minimum_history_sessions": MINIMUM_OBSERVATIONS,
                "risk_aversion": RISK_AVERSION[tier], "recommendations": inserted,
            }


@router.get("/{user_id}")
def list_recommendations(
    user_id: UUID,
    status_filter: str | None = Query(default=None, alias="status"),
    conn=Depends(advisory_connection),
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
                           r.explanation,r.generated_timestamp,b.created_at AS batch_created_at,
                           (r.batch_id=%s::uuid) AS is_latest_batch
                    FROM recommendation_log r LEFT JOIN recommendation_batch b USING(batch_id)
                    WHERE r.user_id=%s"""
        values = [latest_batch_id, str(user_id)]
        if status_filter:
            query += " AND r.status_state=%s"
            values.append(status_filter)
        query += " ORDER BY b.created_at DESC NULLS LAST,r.generated_timestamp DESC,r.rec_id"
        cur.execute(query, values)
        return [dict(row) for row in cur.fetchall()]


@router.post("/{user_id}/{recommendation_id}/decision")
def decide_recommendation(
    user_id: UUID,
    recommendation_id: UUID,
    body: RecommendationDecision,
    conn=Depends(advisory_connection),
):
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
