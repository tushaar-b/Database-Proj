"""Database connectivity and upsert operations for the Market Data ETL Pipeline.

Supports high-throughput batch upserts for SECURITY_MASTER and DAILY_MARKET_QUOTE
with PostgreSQL ON CONFLICT clauses, UUID generation, and SQLite compatibility.
"""
import os
import uuid
import logging
from contextlib import contextmanager
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import date, datetime

logger = logging.getLogger("etl.db")

try:
    import psycopg2
    from psycopg2.extras import execute_values
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


@contextmanager
def get_cursor(conn):
    """Context manager for obtaining a database cursor across sqlite3 and psycopg2."""
    cur = conn.cursor()
    try:
        yield cur
    finally:
        cur.close()


def get_db_connection(db_url: Optional[str] = None):
    """Establishes a connection to the Risk Database.
    
    Supports PostgreSQL connection strings or sqlite3 connection fallback.
    """
    url = db_url or os.getenv("RISK_DB_URL", "postgresql://postgres:postgres@localhost:5433/risk_db")
    
    if url.startswith("sqlite"):
        import sqlite3
        sqlite_path = url.replace("sqlite:///", "").replace("sqlite://", "")
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    if not PSYCOPG2_AVAILABLE:
        raise ImportError("psycopg2 is required for PostgreSQL connections.")
    
    return psycopg2.connect(url)


def upsert_security_master(
    conn,
    securities: List[Dict[str, Any]],
    is_sqlite: bool = False
) -> Dict[str, str]:
    """Upserts securities into SECURITY_MASTER.
    
    Returns a dictionary mapping ticker_symbol -> security_id (UUID string).
    """
    ticker_to_id = {}
    if not securities:
        return ticker_to_id

    is_sqlite_conn = is_sqlite or type(conn).__module__.startswith("sqlite3")

    with get_cursor(conn) as cur:
        if is_sqlite_conn:
            for sec in securities:
                sec_id = str(uuid.uuid4())
                cur.execute(
                    """
                    INSERT INTO SECURITY_MASTER (security_id, ticker_symbol, company_name, sector_name, exchange_code, beta_index)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(ticker_symbol) DO UPDATE SET
                        company_name = excluded.company_name,
                        sector_name = excluded.sector_name,
                        beta_index = excluded.beta_index
                    RETURNING security_id, ticker_symbol;
                    """,
                    (
                        sec_id,
                        sec["ticker_symbol"],
                        sec["company_name"],
                        sec["sector_name"],
                        sec.get("exchange_code", "NSE"),
                        float(sec.get("beta_index", 1.0)),
                    )
                )
                row = cur.fetchone()
                if row:
                    ticker_to_id[row[1]] = str(row[0])
            conn.commit()
        else:
            # PostgreSQL batch upsert with RETURNING
            records = [
                (
                    str(uuid.uuid4()),
                    sec["ticker_symbol"],
                    sec["company_name"],
                    sec["sector_name"],
                    sec.get("exchange_code", "NSE"),
                    float(sec.get("beta_index", 1.0)),
                )
                for sec in securities
            ]
            query = """
                INSERT INTO SECURITY_MASTER (
                    security_id, ticker_symbol, company_name, sector_name, exchange_code, beta_index
                ) VALUES %s
                ON CONFLICT (ticker_symbol) DO UPDATE SET
                    company_name = EXCLUDED.company_name,
                    sector_name = EXCLUDED.sector_name,
                    beta_index = EXCLUDED.beta_index
                RETURNING security_id, ticker_symbol;
            """
            execute_values(cur, query, records, template="(%s, %s, %s, %s, %s, %s)")
            for row in cur.fetchall():
                ticker_to_id[row[1]] = str(row[0])
            conn.commit()

    logger.info(f"Successfully upserted {len(ticker_to_id)} records in SECURITY_MASTER.")
    return ticker_to_id


def get_security_master_map(conn, is_sqlite: bool = False) -> Dict[str, str]:
    """Fetches all ticker_symbol -> security_id mappings from SECURITY_MASTER."""
    ticker_to_id = {}
    with get_cursor(conn) as cur:
        cur.execute("SELECT security_id, ticker_symbol FROM SECURITY_MASTER;")
        rows = cur.fetchall()
        for row in rows:
            ticker_to_id[row[1]] = str(row[0])
    return ticker_to_id


def upsert_daily_quotes(
    conn,
    quotes: List[Dict[str, Any]],
    batch_size: int = 5000,
    is_sqlite: bool = False
) -> int:
    """Batch upserts historical and daily quotes into DAILY_MARKET_QUOTE.
    
    Respects UNIQUE(security_id, trade_date).
    Returns the total number of records processed.
    """
    if not quotes:
        return 0

    total_inserted = 0
    is_sqlite_conn = is_sqlite or type(conn).__module__.startswith("sqlite3")

    with get_cursor(conn) as cur:
        for i in range(0, len(quotes), batch_size):
            batch = quotes[i : i + batch_size]
            if is_sqlite_conn:
                for q in batch:
                    q_id = q.get("quote_id") or str(uuid.uuid4())
                    cur.execute(
                        """
                        INSERT INTO DAILY_MARKET_QUOTE (
                            quote_id, security_id, trade_date, close_price, adjusted_close, volume
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        ON CONFLICT(security_id, trade_date) DO UPDATE SET
                            close_price = excluded.close_price,
                            adjusted_close = excluded.adjusted_close,
                            volume = excluded.volume;
                        """,
                        (
                            q_id,
                            str(q["security_id"]),
                            str(q["trade_date"]),
                            round(float(q["close_price"]), 2),
                            round(float(q["adjusted_close"]), 2),
                            int(q["volume"]),
                        )
                    )
                conn.commit()
                total_inserted += len(batch)
            else:
                # PostgreSQL batch upsert
                records = [
                    (
                        q.get("quote_id") or str(uuid.uuid4()),
                        str(q["security_id"]),
                        q["trade_date"],
                        round(float(q["close_price"]), 2),
                        round(float(q["adjusted_close"]), 2),
                        int(q["volume"]),
                    )
                    for q in batch
                ]
                query = """
                    INSERT INTO DAILY_MARKET_QUOTE (
                        quote_id, security_id, trade_date, close_price, adjusted_close, volume
                    ) VALUES %s
                    ON CONFLICT (security_id, trade_date) DO UPDATE SET
                        close_price = EXCLUDED.close_price,
                        adjusted_close = EXCLUDED.adjusted_close,
                        volume = EXCLUDED.volume;
                """
                execute_values(cur, query, records, template="(%s, %s, %s, %s, %s, %s)")
                conn.commit()
                total_inserted += len(batch)

    logger.info(f"Upserted {total_inserted} quotes into DAILY_MARKET_QUOTE.")
    return total_inserted


def refresh_sector_concentration_view(conn, is_sqlite: bool = False) -> bool:
    """Refreshes the mv_daily_sector_concentration materialized view in PostgreSQL."""
    if is_sqlite or type(conn).__module__.startswith("sqlite3"):
        logger.debug("Materialized view refresh skipped on SQLite.")
        return True

    try:
        with get_cursor(conn) as cur:
            cur.execute("REFRESH MATERIALIZED VIEW mv_daily_sector_concentration;")
            conn.commit()
        logger.info("Successfully refreshed mv_daily_sector_concentration.")
        return True
    except Exception as e:
        logger.warning(f"Materialized view refresh failed: {e}")
        conn.rollback()
        return False
