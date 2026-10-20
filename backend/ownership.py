"""Reject cross-user access using IDs resolved from the authenticated cookie."""
from fastapi import Depends, HTTPException, Request

from backend.auth import current_session
from backend.dependencies import advisory_connection, risk_connection


def enforce_ownership(
    request: Request,
    session=Depends(current_session),
    advisory=Depends(advisory_connection),
    risk=Depends(risk_connection),
):
    owner = session["user_id"]
    path_user = request.path_params.get("user_id") or request.query_params.get("user_id")
    if path_user and str(path_user) != owner:
        raise HTTPException(status_code=404, detail="Record not found")

    portfolio_id = request.path_params.get("portfolio_id") or request.query_params.get("portfolio_id")
    if portfolio_id:
        with risk.cursor() as cur:
            cur.execute("SELECT 1 FROM portfolio WHERE portfolio_id=%s AND user_id=%s", (portfolio_id, owner))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Record not found")

    for key, table, column in (
        ("income_id", "income_stream", "income_id"),
        ("expense_id", "expense_item", "expense_id"),
        ("recommendation_id", "recommendation_log", "rec_id"),
    ):
        record_id = request.path_params.get(key)
        if record_id:
            with advisory.cursor() as cur:
                cur.execute(f"SELECT 1 FROM {table} WHERE {column}=%s AND user_id=%s", (record_id, owner))
                if not cur.fetchone():
                    raise HTTPException(status_code=404, detail="Record not found")

    alert_id = request.path_params.get("alert_id")
    if alert_id:
        with risk.cursor() as cur:
            cur.execute("""SELECT 1 FROM rebalance_alert a JOIN portfolio p USING(portfolio_id)
                           WHERE a.alert_id=%s AND p.user_id=%s""", (alert_id, owner))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Record not found")

    # Ownership dependencies execute before endpoint code. Return these pooled
    # connections to the idle state so SERIALIZABLE paths can choose isolation.
    advisory.commit()
    risk.commit()
