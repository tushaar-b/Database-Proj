from decimal import Decimal, ROUND_FLOOR
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from psycopg2.extras import RealDictCursor

from backend.dependencies import advisory_connection, risk_connection
from backend.services import require_feedback_delivery
from backend.schemas import RecommendationDecision

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])
BASE_CAPACITY = {"CONSERVATIVE": Decimal("0.25"), "MODERATE": Decimal("0.50"), "AGGRESSIVE": Decimal("0.75")}


@router.post("/{user_id}/generate", status_code=status.HTTP_201_CREATED)
def generate_recommendations(
    user_id: UUID,
    advisory=Depends(advisory_connection),
    risk=Depends(risk_connection),
):
    delivery = require_feedback_delivery(risk, advisory)
    batch_id = uuid4()
    with advisory:
        with advisory.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT risk_tolerance_tier::text FROM user_profile WHERE user_id=%s FOR UPDATE", (str(user_id),))
            profile = cur.fetchone()
            if not profile:
                raise HTTPException(status_code=404, detail="User not found")
            cur.execute("SELECT investable_buffer FROM surplus_snapshot WHERE user_id=%s ORDER BY evaluated_at DESC,snapshot_id DESC LIMIT 1", (str(user_id),))
            snapshot = cur.fetchone()
            if not snapshot:
                raise HTTPException(status_code=409, detail="Evaluate cashflow before generating recommendations")
            buffer = Decimal(snapshot["investable_buffer"])
            if buffer <= 0:
                return {"batch_id": str(batch_id), "available_buffer": buffer, "recommendations": [], "reason": "Investable buffer is zero."}
            cur.execute("SELECT COUNT(*) AS pending_count FROM recommendation_log WHERE user_id=%s AND status_state='PENDING'", (str(user_id),))
            if cur.fetchone()["pending_count"]:
                raise HTTPException(status_code=409, detail="Resolve the existing pending recommendation batch before generating another")
            cur.execute("SELECT capacity_multiplier,blocked_sectors,reason FROM recommendation_policy WHERE user_id=%s", (str(user_id),))
            policy = cur.fetchone()
            multiplier = Decimal(policy["capacity_multiplier"]) if policy else Decimal("1")
            blocked = set(policy["blocked_sectors"] or []) if policy else set()
            policy_reason = policy["reason"] if policy else "No active risk breach; normal allocation policy applies."
            ratio = BASE_CAPACITY[profile["risk_tolerance_tier"]] * multiplier
            budget = (buffer * ratio).quantize(Decimal("0.01"), rounding=ROUND_FLOOR)
            with risk.cursor(cursor_factory=RealDictCursor) as risk_cur:
                risk_cur.execute(
                    """SELECT sm.security_id::text,sm.ticker_symbol,sm.sector_name,q.close_price
                       FROM security_master sm
                       JOIN LATERAL (SELECT close_price FROM daily_market_quote d WHERE d.security_id=sm.security_id ORDER BY trade_date DESC LIMIT 1) q ON TRUE
                       WHERE NOT (sm.sector_name=ANY(%s))
                         AND NOT EXISTS (
                           SELECT 1 FROM portfolio p JOIN holding h USING(portfolio_id)
                           WHERE p.user_id=%s AND h.security_id=sm.security_id AND h.quantity>0)
                       ORDER BY sm.sector_name,sm.ticker_symbol""",
                    (list(blocked), str(user_id)),
                )
                available_securities = risk_cur.fetchall()
            by_sector = {}
            for candidate in available_securities:
                by_sector.setdefault(candidate["sector_name"], dict(candidate))
            candidates = [by_sector[sector] for sector in sorted(by_sector)[:3]]
            if not candidates or budget <= 0:
                return {"batch_id": str(batch_id), "available_buffer": buffer, "allocation_budget": budget, "recommendations": [], "reason": policy_reason}
            per_candidate = budget / len(candidates)
            explanation = (
                f"Deterministic MVP policy: equal budget across up to three distinct sectors, whole shares, no return prediction. {policy_reason}"
            )
            inserted = []
            total_cost = Decimal("0")
            for candidate in candidates:
                price = Decimal(candidate["close_price"])
                shares = int((per_candidate / price).to_integral_value(rounding=ROUND_FLOOR))
                if shares < 1:
                    continue
                amount = price * shares
                if total_cost + amount > min(budget, buffer):
                    continue
                cur.execute(
                    """INSERT INTO recommendation_log(user_id,stock_ticker,target_allocation_pct,recommended_amount,status_state,batch_id,shares,explanation)
                       VALUES (%s,%s,%s,%s,'PENDING',%s,%s,%s)
                       RETURNING rec_id::text,stock_ticker,target_allocation_pct,recommended_amount,status_state::text,batch_id::text,shares,explanation""",
                    (str(user_id), candidate["ticker_symbol"], amount / buffer * 100, amount, str(batch_id), shares, explanation),
                )
                inserted.append(dict(cur.fetchone()))
                total_cost += amount
            return {
                "batch_id": str(batch_id), "available_buffer": buffer, "allocation_budget": budget,
                "total_recommended_cost": total_cost, "policy_multiplier": multiplier,
                "blocked_sectors": sorted(blocked), "reason": policy_reason,
                "feedback_events_processed": delivery["events_applied"], "recommendations": inserted,
            }


@router.get("/{user_id}")
def list_recommendations(user_id: UUID, status_filter: str | None = Query(default=None, alias="status"), conn=Depends(advisory_connection)):
    if status_filter and status_filter not in {"PENDING", "ACCEPTED", "REJECTED"}:
        raise HTTPException(status_code=422, detail="status must be PENDING, ACCEPTED, or REJECTED")
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        if status_filter:
            cur.execute("""SELECT rec_id::text,user_id::text,stock_ticker,target_allocation_pct,recommended_amount,status_state::text,
                                  batch_id::text,shares,explanation,generated_timestamp
                           FROM recommendation_log WHERE user_id=%s AND status_state=%s ORDER BY generated_timestamp DESC""",
                        (str(user_id), status_filter))
        else:
            cur.execute("""SELECT rec_id::text,user_id::text,stock_ticker,target_allocation_pct,recommended_amount,status_state::text,
                                  batch_id::text,shares,explanation,generated_timestamp
                           FROM recommendation_log WHERE user_id=%s ORDER BY generated_timestamp DESC""", (str(user_id),))
        return [dict(row) for row in cur.fetchall()]


@router.post("/{user_id}/{recommendation_id}/decision")
def decide_recommendation(user_id: UUID, recommendation_id: UUID, body: RecommendationDecision, conn=Depends(advisory_connection)):
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
