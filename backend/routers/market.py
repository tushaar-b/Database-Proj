"""Bounded public research quote reads. No investor tables or session access.

The quote table has no provenance field and the importer supports synthetic
fallback. Expose these conservatively as illustrative research data, never as
verified market observations or live prices.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor

from backend.database import connection

router = APIRouter(prefix="/market", tags=["Public research market data"])
CLASSIFICATION = "illustrative_research"


def public_quote_connection():
    # SET TRANSACTION is local to this transaction; pool cleanup rolls it back
    # and leaves authenticated users' connection/session settings unchanged.
    with connection("risk") as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            cur.execute("SET LOCAL statement_timeout = '5s'")
        yield conn


class SecurityQuote(BaseModel):
    ticker: str
    company_name: str
    close_price: Decimal
    price_date: date
    previous_close: Decimal | None
    previous_date: date | None
    change_percent: Decimal | None


class QuoteCatalogue(BaseModel):
    classification: Literal["illustrative_research"] = CLASSIFICATION
    securities: list[SecurityQuote]


class DailyClose(BaseModel):
    date: date
    close: Decimal


class SecurityHistory(BaseModel):
    classification: Literal["illustrative_research"] = CLASSIFICATION
    ticker: str
    company_name: str
    as_of: date
    history_start: date
    currency: Literal["INR"] = "INR"
    price_basis: Literal["unadjusted_close"] = "unadjusted_close"
    points: list[DailyClose]


@router.get("/securities", response_model=QuoteCatalogue)
def public_securities(response: Response, limit: int = Query(default=50, ge=1, le=200), conn=Depends(public_quote_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT sm.ticker_symbol AS ticker,sm.company_name,
                      latest.close_price,latest.trade_date AS price_date,
                      previous.close_price AS previous_close,previous.trade_date AS previous_date
               FROM security_master sm
               JOIN LATERAL (
                   SELECT q.close_price,q.trade_date FROM daily_market_quote q
                   WHERE q.security_id=sm.security_id AND q.close_price>0
                   ORDER BY q.trade_date DESC LIMIT 1
               ) latest ON TRUE
               LEFT JOIN LATERAL (
                   SELECT q.close_price,q.trade_date FROM daily_market_quote q
                   WHERE q.security_id=sm.security_id AND q.close_price>0
                     AND q.trade_date<latest.trade_date
                   ORDER BY q.trade_date DESC LIMIT 1
               ) previous ON TRUE
               ORDER BY sm.ticker_symbol LIMIT %s""", (limit,),
        )
        rows = []
        for record in cur.fetchall():
            row = dict(record)
            row["change_percent"] = ((row["close_price"] / row["previous_close"] - 1) * 100
                                     if row["previous_close"] else None)
            rows.append(row)
    response.headers["Cache-Control"] = "public, max-age=60"
    return {"classification": CLASSIFICATION, "securities": rows}


@router.get("/securities/{ticker}/history", response_model=SecurityHistory)
def public_history(response: Response, ticker: str = Path(pattern=r"^[A-Za-z0-9&_.-]{1,30}$"), conn=Depends(public_quote_connection)):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """SELECT sm.security_id,sm.ticker_symbol AS ticker,sm.company_name,
                      latest.trade_date AS as_of,earliest.trade_date AS history_start
               FROM security_master sm
               JOIN LATERAL (
                   SELECT trade_date FROM daily_market_quote q
                   WHERE q.security_id=sm.security_id AND close_price>0
                   ORDER BY trade_date DESC LIMIT 1
               ) latest ON TRUE
               JOIN LATERAL (
                   SELECT trade_date FROM daily_market_quote q
                   WHERE q.security_id=sm.security_id AND close_price>0
                   ORDER BY trade_date ASC LIMIT 1
               ) earliest ON TRUE
               WHERE sm.ticker_symbol=%s LIMIT 1""", (ticker.upper(),),
        )
        security = cur.fetchone()
        if not security:
            raise HTTPException(status_code=404, detail="Stored research history is unavailable for this security")
        cur.execute(
            """SELECT trade_date AS date,close_price AS close FROM daily_market_quote
               WHERE security_id=%s AND trade_date BETWEEN %s AND %s AND close_price>0
               ORDER BY trade_date LIMIT 366""",
            (str(security["security_id"]), security["as_of"] - timedelta(days=365), security["as_of"]),
        )
        points = [dict(row) for row in cur.fetchall()]
    response.headers["Cache-Control"] = "public, max-age=60"
    return {"classification": CLASSIFICATION, "ticker": security["ticker"],
            "company_name": security["company_name"], "as_of": security["as_of"],
            "history_start": security["history_start"], "points": points}
