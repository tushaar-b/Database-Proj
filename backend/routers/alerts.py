from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg2.extras import RealDictCursor

from backend.dependencies import advisory_connection, risk_connection
from backend.services import evaluate_portfolio_risk, require_feedback_delivery, _persist_feedback_snapshot

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def _alert_rows(cur, portfolio_id=None, unresolved=False):
    filters = []
    values = []
    if portfolio_id is not None:
        filters.append("portfolio_id=%s")
        values.append(portfolio_id)
    if unresolved:
        filters.append("resolved_flag=FALSE")
    clause = " WHERE " + " AND ".join(filters) if filters else ""
    cur.execute(
        "SELECT alert_id::text,portfolio_id::text,drift_magnitude_pct,breached_metric::text AS breached_metric,resolved_flag,created_at FROM rebalance_alert" + clause + " ORDER BY created_at DESC",
        values,
    )
    return [dict(row) for row in cur.fetchall()]


@router.get("")
def list_alerts(
    unresolved: bool = Query(default=False),
    portfolio_id: UUID | None = Query(default=None),
    conn=Depends(risk_connection),
):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        return _alert_rows(cur, str(portfolio_id) if portfolio_id else None, unresolved)


@router.get("/portfolio/{portfolio_id}")
def list_portfolio_alerts(portfolio_id: UUID, unresolved: bool = False, conn=Depends(risk_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT 1 FROM portfolio WHERE portfolio_id=%s", (str(portfolio_id),))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Portfolio not found")
        return _alert_rows(cur, str(portfolio_id), unresolved)


@router.post("/evaluate/{portfolio_id}")
def evaluate_alerts(
    portfolio_id: UUID,
    risk=Depends(risk_connection),
    advisory=Depends(advisory_connection),
):
    result = evaluate_portfolio_risk(risk, str(portfolio_id))
    delivery = require_feedback_delivery(risk, advisory)
    return {**result, "feedback_delivery": delivery}


@router.patch("/{alert_id}/resolve")
def resolve_alert(
    alert_id: UUID,
    risk=Depends(risk_connection),
    advisory=Depends(advisory_connection),
):
    with risk:
        with risk.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""SELECT a.portfolio_id::text,p.user_id::text,a.resolved_flag
                           FROM rebalance_alert a JOIN portfolio p USING(portfolio_id)
                           WHERE a.alert_id=%s FOR UPDATE OF a,p""", (str(alert_id),))
            alert = cur.fetchone()
            if not alert:
                raise HTTPException(status_code=404, detail="Alert not found")
            cur.execute("UPDATE rebalance_alert SET resolved_flag=TRUE WHERE alert_id=%s", (str(alert_id),))
            cur.execute("REFRESH MATERIALIZED VIEW mv_daily_sector_concentration")
            event_seq = _persist_feedback_snapshot(cur, alert["user_id"], alert["portfolio_id"])
    delivery = require_feedback_delivery(risk, advisory)
    return {"alert_id": str(alert_id), "resolved_flag": True, "feedback_event_seq": event_seq, "feedback_delivery": delivery}
