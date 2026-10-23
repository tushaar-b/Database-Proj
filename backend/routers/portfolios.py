from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from psycopg2.extras import RealDictCursor

from backend.dependencies import advisory_connection, risk_connection
from backend.schemas import HoldingInput, PortfolioCreate, PortfolioUpdate
from backend.services import evaluate_portfolio_risk, require_feedback_delivery
from backend.auth import require_authenticated, require_csrf
from backend.ownership import enforce_ownership
from backend.market_data import get_latest_quotes, price_holdings, valuation

router = APIRouter(prefix="/portfolios", tags=["Portfolios"], dependencies=[Depends(require_authenticated), Depends(require_csrf), Depends(enforce_ownership)])


def _ensure_importable(conn, portfolio_id: str):
    """Imported-position edits are allowed only before simulated ledger activity."""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM transaction_ledger WHERE portfolio_id=%s", (portfolio_id,))
        if cur.fetchone()[0]:
            raise HTTPException(status_code=409, detail="Holdings are locked after simulated trades; use rebalance execution")


def _refresh_valuation(cur, portfolio_id: str):
    cur.execute("SELECT cash_balance FROM portfolio WHERE portfolio_id=%s", (portfolio_id,))
    row = cur.fetchone()
    cash = row['cash_balance'] if isinstance(row, dict) else row[0]
    result = valuation(cur.connection, portfolio_id, cash)
    if result['portfolio_valuation'] is not None:
        cur.execute("UPDATE portfolio SET total_valuation=%s WHERE portfolio_id=%s", (result['portfolio_valuation'], portfolio_id))



@router.post("", status_code=status.HTTP_201_CREATED)
def create_portfolio(
    body: PortfolioCreate,
    request: Request,
    conn=Depends(risk_connection),
    advisory=Depends(advisory_connection),
):
    if str(body.user_id) != request.state.user_id:
        raise HTTPException(status_code=404, detail="Record not found")
    with advisory.cursor() as cur:
        cur.execute("SELECT 1 FROM user_profile WHERE user_id=%s", (str(body.user_id),))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="User not found in advisory database")
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""INSERT INTO portfolio(user_id,portfolio_name,cash_balance,target_hhi_limit)
                           VALUES (%s,%s,%s,%s)
                           RETURNING portfolio_id::text,user_id::text,portfolio_name,cash_balance,target_hhi_limit""",
                        (str(body.user_id), body.portfolio_name.strip(), body.cash_balance, body.target_hhi_limit))
            return dict(cur.fetchone())


@router.get("")
def list_portfolios(user_id: UUID, conn=Depends(risk_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SELECT portfolio_id::text,user_id::text,portfolio_name,cash_balance,target_hhi_limit
                       FROM portfolio WHERE user_id=%s ORDER BY portfolio_name,portfolio_id""", (str(user_id),))
        return [dict(row) for row in cur.fetchall()]


@router.get("/securities")
def list_securities(q: str | None = Query(default=None, max_length=50), conn=Depends(risk_connection)):
    search = f"%{q.strip()}%" if q and q.strip() else "%"
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""SELECT sm.security_id::text,sm.ticker_symbol,sm.company_name,sm.sector_name,
                              quote.close_price AS latest_price,quote.trade_date AS price_date
                       FROM security_master sm
                       LEFT JOIN LATERAL (SELECT close_price,trade_date FROM daily_market_quote d
                                     WHERE d.security_id=sm.security_id ORDER BY trade_date DESC LIMIT 1) quote ON TRUE
                       WHERE sm.ticker_symbol ILIKE %s OR sm.company_name ILIKE %s
                       ORDER BY sm.ticker_symbol LIMIT 100""", (search, search))
        rows = [dict(row) for row in cur.fetchall()]
    quotes = get_latest_quotes(conn, [r['security_id'] for r in rows])
    return [{**r, 'latest_price': quotes[r['security_id']]['price'], 'price_date': quotes[r['security_id']]['price_date'],
             'quote': quotes[r['security_id']]} for r in rows]


@router.get("/{portfolio_id}")
def get_portfolio(portfolio_id: UUID, conn=Depends(risk_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT portfolio_id::text,user_id::text,portfolio_name,cash_balance,target_hhi_limit FROM portfolio WHERE portfolio_id=%s", (str(portfolio_id),))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return {**dict(row), **valuation(conn, str(portfolio_id), row['cash_balance'])}


@router.get("/{portfolio_id}/holdings")
def list_holdings(portfolio_id: UUID, conn=Depends(risk_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT 1 FROM portfolio WHERE portfolio_id=%s", (str(portfolio_id),))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Portfolio not found")
    return price_holdings(conn, str(portfolio_id))


@router.patch("/{portfolio_id}")
def update_portfolio(portfolio_id: UUID, body: PortfolioUpdate, conn=Depends(risk_connection)):
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    if not changes:
        raise HTTPException(status_code=422, detail="At least one portfolio field is required")
    if "portfolio_name" in changes:
        changes["portfolio_name"] = changes["portfolio_name"].strip()
        if not changes["portfolio_name"]:
            raise HTTPException(status_code=422, detail="Portfolio name cannot be blank")
    assignments = ",".join(f"{key}=%s" for key in changes)
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(f"UPDATE portfolio SET {assignments} WHERE portfolio_id=%s RETURNING portfolio_id::text,user_id::text,portfolio_name,cash_balance,target_hhi_limit",
                        (*changes.values(), str(portfolio_id)))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Portfolio not found")
            return dict(row)


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(portfolio_id: UUID, conn=Depends(risk_connection)):
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM portfolio WHERE portfolio_id=%s FOR UPDATE", (str(portfolio_id),))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Portfolio not found")
            cur.execute("SELECT 1 FROM transaction_ledger WHERE portfolio_id=%s LIMIT 1", (str(portfolio_id),))
            has_ledger = cur.fetchone()
            cur.execute("SELECT 1 FROM rebalance_alert WHERE portfolio_id=%s LIMIT 1", (str(portfolio_id),))
            has_alert_history = cur.fetchone()
            cur.execute("SELECT 1 FROM risk_feedback_outbox WHERE portfolio_id=%s LIMIT 1", (str(portfolio_id),))
            has_feedback_history = cur.fetchone()
            if has_ledger or has_alert_history or has_feedback_history:
                raise HTTPException(status_code=409, detail="Portfolio with trade, alert, or feedback history cannot be deleted")
            cur.execute("DELETE FROM portfolio WHERE portfolio_id=%s", (str(portfolio_id),))
    return None


@router.post("/{portfolio_id}/holdings", status_code=status.HTTP_201_CREATED)
def add_holding(portfolio_id: UUID, body: HoldingInput, conn=Depends(risk_connection)):
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT 1 FROM portfolio WHERE portfolio_id=%s FOR UPDATE", (str(portfolio_id),))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Portfolio not found")
            _ensure_importable(conn, str(portfolio_id))
            cur.execute("""SELECT 1 FROM security_master sm
                           WHERE sm.security_id=%s AND EXISTS (
                             SELECT 1 FROM daily_market_quote q WHERE q.security_id=sm.security_id)""", (str(body.security_id),))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Security not found or has no market quote")
            cur.execute("INSERT INTO holding(portfolio_id,security_id,quantity,average_buy_price) VALUES (%s,%s,%s,%s) RETURNING holding_id::text,security_id::text,quantity,average_buy_price",
                        (str(portfolio_id), str(body.security_id), body.quantity, body.average_buy_price))
            row = dict(cur.fetchone())
            _refresh_valuation(cur, str(portfolio_id))
            row["position_source"] = "imported"
            return row


@router.put("/{portfolio_id}/holdings/{security_id}")
def update_holding(portfolio_id: UUID, security_id: UUID, body: HoldingInput, conn=Depends(risk_connection)):
    if body.security_id != security_id:
        raise HTTPException(status_code=422, detail="Path and body security IDs must match")
    with conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT 1 FROM portfolio WHERE portfolio_id=%s FOR UPDATE", (str(portfolio_id),))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Portfolio not found")
            _ensure_importable(conn, str(portfolio_id))
            cur.execute("UPDATE holding SET quantity=%s,average_buy_price=%s,last_updated_at=now() WHERE portfolio_id=%s AND security_id=%s RETURNING holding_id::text,security_id::text,quantity,average_buy_price",
                        (body.quantity, body.average_buy_price, str(portfolio_id), str(security_id)))
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Holding not found")
            _refresh_valuation(cur, str(portfolio_id))
            return dict(row)


@router.delete("/{portfolio_id}/holdings/{security_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_holding(portfolio_id: UUID, security_id: UUID, conn=Depends(risk_connection)):
    with conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM portfolio WHERE portfolio_id=%s FOR UPDATE", (str(portfolio_id),))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Portfolio not found")
            _ensure_importable(conn, str(portfolio_id))
            cur.execute("DELETE FROM holding WHERE portfolio_id=%s AND security_id=%s", (str(portfolio_id), str(security_id)))
            if not cur.rowcount:
                raise HTTPException(status_code=404, detail="Holding not found")
            _refresh_valuation(cur, str(portfolio_id))
    return None


@router.get("/{portfolio_id}/risk")
def get_portfolio_risk(
    portfolio_id: UUID,
    risk=Depends(risk_connection),
    advisory=Depends(advisory_connection),
):
    evaluation = evaluate_portfolio_risk(risk, str(portfolio_id))
    delivery = require_feedback_delivery(risk, advisory)
    return {
        **evaluation["summary"],
        "new_alerts": evaluation["new_alerts"],
        "feedback_event_seq": evaluation["feedback_event_seq"],
        "feedback_delivery": delivery,
    }
