import hashlib
import json
import time
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg2 import errors
from psycopg2.extras import RealDictCursor

from backend.dependencies import advisory_connection, risk_connection
from backend.schemas import RebalanceExecute
from backend.services import evaluate_portfolio_risk, process_feedback_outbox
from backend.auth import require_authenticated, require_csrf
from backend.ownership import enforce_ownership
from backend.market_data import get_latest_quotes, price_holdings, valuation as market_valuation

router = APIRouter(prefix="/rebalance", tags=["Rebalance"], dependencies=[Depends(require_authenticated), Depends(require_csrf), Depends(enforce_ownership)])


@router.post("/{portfolio_id}/propose")
def propose_rebalance(
    portfolio_id: UUID,
    risk=Depends(risk_connection),
    advisory=Depends(advisory_connection),
):
    evaluation = evaluate_portfolio_risk(risk, str(portfolio_id))
    summary = evaluation["summary"]
    with risk.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT user_id FROM portfolio WHERE portfolio_id=%s", (str(portfolio_id),))
        portfolio = cur.fetchone()
        cur.execute("""SELECT h.security_id::text,sm.ticker_symbol,sm.sector_name,h.quantity,q.close_price
                       FROM holding h JOIN security_master sm USING(security_id)
                       JOIN LATERAL (SELECT close_price FROM daily_market_quote d WHERE d.security_id=h.security_id ORDER BY trade_date DESC LIMIT 1) q ON TRUE
                       WHERE h.portfolio_id=%s AND h.quantity>0
                       ORDER BY h.quantity*q.close_price DESC,sm.ticker_symbol""", (str(portfolio_id),))
        holdings = [dict(row) for row in cur.fetchall()]
        cur.execute("SELECT sector_name FROM mv_daily_sector_concentration WHERE portfolio_id=%s ORDER BY sector_weight DESC LIMIT 1", (str(portfolio_id),))
        top_sector_row = cur.fetchone()
    priced = price_holdings(risk, str(portfolio_id))
    holdings = sorted([{**h, 'close_price': h['latest_price']} for h in priced if h['latest_price'] is not None and h['quantity'] > 0], key=lambda h: -h['market_value'])
    active_breaches = [row["metric"] for row in evaluation["new_alerts"]]
    with risk.cursor() as cur:
        cur.execute("SELECT breached_metric::text FROM rebalance_alert WHERE portfolio_id=%s AND resolved_flag=FALSE", (str(portfolio_id),))
        active_breaches = sorted(set(active_breaches + [row[0] for row in cur.fetchall()]))
    if not active_breaches or not holdings:
        operations = []
        reason = "No active breach or no priced holdings; no simulated trades proposed."
    else:
        target_sector = top_sector_row["sector_name"] if "SECTOR_HHI_EXCEEDED" in active_breaches and top_sector_row else None
        candidate = next((row for row in holdings if target_sector is None or row["sector_name"] == target_sector), holdings[0])
        operations = [{
            "security_id": candidate["security_id"], "ticker_symbol": candidate["ticker_symbol"],
            "side": "SELL", "units": 1, "current_price": candidate["close_price"],
            "estimated_proceeds": candidate["close_price"], "quote": candidate["quote"],
        }]
        reason = (
            f"Active risk breaches: {', '.join(active_breaches)}. Propose selling one share of the largest priced holding"
            + (f" in the most concentrated sector ({target_sector})." if target_sector else ".")
        )
    delivery = process_feedback_outbox(risk, advisory)
    return {
        "portfolio_id": str(portfolio_id), "summary": summary, "active_breaches": active_breaches,
        "operations": operations, "reason": reason, "simulation_only": True,
        "feedback_delivery": delivery,
    }


def _execute_once(conn, portfolio_id: str, body: RebalanceExecute, request_hash: str) -> dict:
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT result,request_hash,portfolio_id::text FROM rebalance_execution WHERE idempotency_key=%s", (str(body.idempotency_key),))
        prior = cur.fetchone()
        if prior:
            if prior["portfolio_id"] != portfolio_id or prior["request_hash"] != request_hash:
                raise HTTPException(status_code=409, detail="Idempotency key was already used for a different request")
            result = prior["result"] if isinstance(prior["result"], dict) else json.loads(prior["result"])
            return {**result, "duplicate_execution": True}

        cur.execute("SELECT portfolio_id::text,user_id::text,cash_balance FROM portfolio WHERE portfolio_id=%s FOR UPDATE", (portfolio_id,))
        portfolio = cur.fetchone()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        cash = Decimal(portfolio["cash_balance"])
        touched = set()
        ledger_entries = []
        quotes = get_latest_quotes(conn)
        for operation in body.operations:
            security_id = str(operation.security_id)
            if security_id in touched:
                raise HTTPException(status_code=422, detail="A security may appear only once in one rebalance request")
            touched.add(security_id)
            cur.execute("SELECT ticker_symbol FROM security_master WHERE security_id=%s FOR SHARE", (security_id,))
            security = cur.fetchone()
            if not security:
                raise HTTPException(status_code=404, detail=f"Security {security_id} not found")
            quote = quotes.get(security_id)
            if not quote or not quote['price'] or not quote.get('fresh_enough_for_operation', False):
                raise HTTPException(status_code=409, detail='A sufficiently recent yfinance observation or latest dated market close is required for simulated execution; dated fallback prices cannot execute.')
            price = Decimal(quote['price'])
            cur.execute("SELECT holding_id::text,quantity,average_buy_price FROM holding WHERE portfolio_id=%s AND security_id=%s FOR UPDATE", (portfolio_id, security_id))
            holding = cur.fetchone()
            quantity = int(holding["quantity"]) if holding else 0
            delta = int(operation.units)
            gross = price * delta
            if operation.side == "BUY":
                if gross > cash:
                    raise HTTPException(status_code=409, detail="Insufficient portfolio cash for simulated BUY")
                updated_quantity = quantity + delta
                avg_price = ((Decimal(holding["average_buy_price"]) * quantity + gross) / updated_quantity) if holding else price
                if holding:
                    cur.execute("UPDATE holding SET quantity=%s,average_buy_price=%s,last_updated_at=now() WHERE holding_id=%s", (updated_quantity, avg_price, holding["holding_id"]))
                else:
                    cur.execute("INSERT INTO holding(portfolio_id,security_id,quantity,average_buy_price) VALUES (%s,%s,%s,%s)", (portfolio_id, security_id, updated_quantity, avg_price))
                cash -= gross
                tx_type = "BUY"
            else:
                if not holding or quantity < delta:
                    raise HTTPException(status_code=409, detail=f"Insufficient shares to sell {security['ticker_symbol']}")
                updated_quantity = quantity - delta
                cur.execute("UPDATE holding SET quantity=%s,last_updated_at=now() WHERE holding_id=%s", (updated_quantity, holding["holding_id"]))
                cash += gross
                tx_type = "SELL"
            cur.execute("UPDATE portfolio SET cash_balance=%s WHERE portfolio_id=%s", (cash, portfolio_id))
            cur.execute("""INSERT INTO transaction_ledger(portfolio_id,security_id,tx_type,units,execution_price)
                           VALUES (%s,%s,%s,%s,%s) RETURNING tx_id::text""",
                        (portfolio_id, security_id, tx_type, delta, price))
            tx_id = cur.fetchone()["tx_id"]
            ledger_entries.append({"tx_id": tx_id, "ticker_symbol": security["ticker_symbol"], "side": operation.side, "units": delta, "price": price})
        valuation = market_valuation(conn, portfolio_id, cash)['portfolio_valuation']
        if valuation is None:
            raise HTTPException(409, 'Portfolio valuation is incomplete; simulated execution was not committed.')
        cur.execute("UPDATE portfolio SET total_valuation=%s WHERE portfolio_id=%s", (valuation, portfolio_id))
        result = {
            "portfolio_id": portfolio_id, "idempotency_key": str(body.idempotency_key),
            "simulation_only": True, "brokerage_order_sent": False,
            "cash_balance": float(cash), "portfolio_valuation": float(valuation), "ledger_entries": [
                {**entry, "price": float(entry["price"])} for entry in ledger_entries
            ],
            "duplicate_execution": False,
        }
        cur.execute(
            "INSERT INTO rebalance_execution(idempotency_key,portfolio_id,request_hash,result) VALUES (%s,%s,%s,%s::jsonb)",
            (str(body.idempotency_key), portfolio_id, request_hash, json.dumps(result, default=str)),
        )
        return result


@router.post("/{portfolio_id}/execute")
def execute_rebalance(
    portfolio_id: UUID,
    body: RebalanceExecute,
    risk=Depends(risk_connection),
    advisory=Depends(advisory_connection),
):
    if not body.approved:
        raise HTTPException(status_code=400, detail="Explicit approval is required for simulated execution")
    request_data = [operation.model_dump(mode="json") for operation in body.operations]
    request_hash = hashlib.sha256(json.dumps(request_data, sort_keys=True).encode()).hexdigest()
    for attempt in range(3):
        try:
            risk.set_session(isolation_level="SERIALIZABLE")
            with risk:
                result = _execute_once(risk, str(portfolio_id), body, request_hash)
            risk.set_session(isolation_level="READ COMMITTED")
            break
        except (errors.SerializationFailure, errors.DeadlockDetected):
            risk.rollback()
            risk.set_session(isolation_level="READ COMMITTED")
            if attempt == 2:
                raise HTTPException(status_code=409, detail="Concurrent rebalance conflict; retry with the same idempotency key")
            time.sleep(0.03 * (attempt + 1))
        except errors.UniqueViolation:
            risk.rollback()
            risk.set_session(isolation_level="READ COMMITTED")
            with risk.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT result,request_hash,portfolio_id::text FROM rebalance_execution WHERE idempotency_key=%s", (str(body.idempotency_key),))
                prior = cur.fetchone()
            if prior and prior["portfolio_id"] == str(portfolio_id) and prior["request_hash"] == request_hash:
                result = prior["result"] if isinstance(prior["result"], dict) else json.loads(prior["result"])
                result["duplicate_execution"] = True
                break
            raise HTTPException(status_code=409, detail="Idempotency key was already used for a different request")
        except Exception:
            risk.rollback()
            risk.set_session(isolation_level="READ COMMITTED")
            raise
    evaluation = evaluate_portfolio_risk(risk, str(portfolio_id))
    delivery = process_feedback_outbox(risk, advisory)
    result["post_trade_risk_status"] = evaluation["summary"]["calculation_status"]
    result["feedback_delivery"] = delivery
    return result
