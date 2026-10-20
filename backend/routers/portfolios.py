from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from psycopg2.extras import RealDictCursor

from backend.dependencies import advisory_connection, risk_connection
from backend.schemas import PortfolioCreate
from backend.services import evaluate_portfolio_risk, require_feedback_delivery

router = APIRouter(prefix="/portfolios", tags=["Portfolios"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_portfolio(
    body: PortfolioCreate,
    conn=Depends(risk_connection),
    advisory=Depends(advisory_connection),
):
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


@router.get("/{portfolio_id}")
def get_portfolio(portfolio_id: UUID, conn=Depends(risk_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""WITH latest AS (
                         SELECT DISTINCT ON (security_id) security_id,close_price,trade_date
                         FROM daily_market_quote ORDER BY security_id,trade_date DESC
                       )
                       SELECT p.portfolio_id::text,p.user_id::text,p.portfolio_name,p.cash_balance,p.target_hhi_limit,
                              p.cash_balance+COALESCE(SUM(h.quantity*latest.close_price),0) AS portfolio_valuation,
                              MAX(latest.trade_date) AS calculation_date
                       FROM portfolio p LEFT JOIN holding h USING(portfolio_id)
                       LEFT JOIN latest ON latest.security_id=h.security_id
                       WHERE p.portfolio_id=%s
                       GROUP BY p.portfolio_id""", (str(portfolio_id),))
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return dict(row)


@router.get("/{portfolio_id}/holdings")
def list_holdings(portfolio_id: UUID, conn=Depends(risk_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT 1 FROM portfolio WHERE portfolio_id=%s", (str(portfolio_id),))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Portfolio not found")
        cur.execute("""WITH latest AS (
                         SELECT DISTINCT ON (security_id) security_id,close_price,trade_date
                         FROM daily_market_quote ORDER BY security_id,trade_date DESC
                       )
                       SELECT h.holding_id::text,h.security_id::text,sm.ticker_symbol,sm.company_name,sm.sector_name,
                              h.quantity,h.average_buy_price,latest.close_price AS latest_price,
                              h.quantity*latest.close_price AS market_value,latest.trade_date AS price_date
                       FROM holding h JOIN security_master sm USING(security_id)
                       LEFT JOIN latest USING(security_id) WHERE h.portfolio_id=%s
                       ORDER BY sm.ticker_symbol""", (str(portfolio_id),))
        return [dict(row) for row in cur.fetchall()]


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
