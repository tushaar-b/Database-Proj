"""Market data ingestion pipeline for Nifty 50 constituent stocks.

Extracts historical 5-year OHLCV market pricing via yfinance, transforms and cleans
the time series data, and loads it idempotently into PostgreSQL (risk_db)
SECURITY_MASTER and DAILY_MARKET_QUOTE tables.
"""
import os
import time
import math
import logging
import argparse
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

from etl.constituents import (
    NIFTY_50_CONSTITUENTS,
    CONSTITUENTS_BY_TICKER,
    get_all_tickers,
    get_all_yfinance_symbols,
)
from etl.db import (
    get_db_connection,
    upsert_security_master,
    get_security_master_map,
    upsert_daily_quotes,
    refresh_sector_concentration_view,
)

logger = logging.getLogger("etl.pipeline")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def generate_synthetic_quotes(
    ticker: str,
    days: int = 1250,
    base_price: float = 1000.0,
    annual_vol: float = 0.22,
    annual_drift: float = 0.12,
    end_date: Optional[date] = None
) -> pd.DataFrame:
    """Generates realistic synthetic OHLCV data using Geometric Brownian Motion.

    Used when running offline or when external market data APIs are throttled.
    """
    if end_date is None:
        end_date = date.today()

    # Generate business days backwards
    dates = pd.bdate_range(end=end_date, periods=days).date
    n_steps = len(dates)

    dt = 1.0 / 252.0
    drift = (annual_drift - 0.5 * (annual_vol ** 2)) * dt
    shock = annual_vol * math.sqrt(dt)

    # Deterministic seed based on ticker string for reproducible synthetic series
    np.random.seed(abs(hash(ticker)) % (2**32))
    random_normals = np.random.normal(0, 1, n_steps)

    log_returns = drift + shock * random_normals
    log_returns[0] = 0.0  # first day reference
    price_paths = base_price * np.exp(np.cumsum(log_returns))

    quotes_data = []
    for d, close_p in zip(dates, price_paths):
        c = round(float(close_p), 2)
        adj_c = round(c * 0.98, 2)  # slight dividend adjustment
        v = int(np.random.uniform(500000, 5000000))
        quotes_data.append({
            "trade_date": d,
            "close_price": max(1.0, c),
            "adjusted_close": max(1.0, adj_c),
            "volume": v
        })

    return pd.DataFrame(quotes_data)


def fetch_symbol_quotes(
    yfinance_symbol: str,
    period: str = "5y",
    start: Optional[str] = None,
    end: Optional[str] = None,
    fallback_offline: bool = False
) -> pd.DataFrame:
    """Fetches OHLCV time series data for a single symbol with error fallback."""
    clean_ticker = yfinance_symbol.replace(".NS", "")

    if YFINANCE_AVAILABLE:
        try:
            logger.info(f"Downloading {yfinance_symbol} via yfinance (period={period})...")
            ticker_obj = yf.Ticker(yfinance_symbol)
            if start and end:
                df = ticker_obj.history(start=start, end=end, auto_adjust=False)
            else:
                df = ticker_obj.history(period=period, auto_adjust=False)

            if df is not None and not df.empty and "Close" in df.columns:
                df = df.reset_index()
                # Clean and standardize date column
                date_col = "Date" if "Date" in df.columns else df.columns[0]
                df["trade_date"] = pd.to_datetime(df[date_col]).dt.date
                df["close_price"] = df["Close"].round(2)
                df["adjusted_close"] = df["Adj Close"].round(2) if "Adj Close" in df.columns else df["close_price"]
                df["volume"] = df["Volume"].fillna(0).astype(int)

                # Filter valid price records before writing to PostgreSQL.
                valid_df = df[
                    (df["close_price"] > 0)
                    & (df["adjusted_close"] > 0)
                    & (df["volume"] >= 0)
                    & np.isfinite(df["close_price"])
                    & np.isfinite(df["adjusted_close"])
                ][
                    ["trade_date", "close_price", "adjusted_close", "volume"]
                ].drop_duplicates(subset=["trade_date"])

                if not valid_df.empty:
                    logger.info(f"Fetched {len(valid_df)} rows for {yfinance_symbol}.")
                    return valid_df
        except Exception as e:
            logger.warning(f"yfinance download failed for {yfinance_symbol}: {e}")

    if fallback_offline:
        logger.info(f"Generating synthetic fallback quotes for {clean_ticker}...")
        base_prices = {
            "RELIANCE": 2800.0,
            "TCS": 3900.0,
            "HDFCBANK": 1650.0,
            "INFY": 1800.0,
            "ICICIBANK": 1200.0,
            "BHARTIARTL": 1400.0,
            "ITC": 480.0,
            "SBIN": 800.0,
            "LT": 3600.0,
        }
        base_p = base_prices.get(clean_ticker, 1500.0)
        days = 1250 if period in ("5y", "max") else (252 if period == "1y" else 30)
        return generate_synthetic_quotes(clean_ticker, days=days, base_price=base_p)

    return pd.DataFrame()


def transform_quotes_for_db(
    df: pd.DataFrame,
    security_id: str
) -> List[Dict[str, Any]]:
    """Transforms a cleaned DataFrame of quotes into DB insertion records."""
    records = []
    for _, row in df.iterrows():
        t_date = row["trade_date"]
        if isinstance(t_date, str):
            t_date = datetime.strptime(t_date, "%Y-%m-%d").date()
        elif isinstance(t_date, datetime):
            t_date = t_date.date()

        records.append({
            "security_id": security_id,
            "trade_date": t_date,
            "close_price": float(row["close_price"]),
            "adjusted_close": float(row.get("adjusted_close", row["close_price"])),
            "volume": int(row["volume"]),
        })
    return records


def ingest_nifty_50_history(
    db_url: Optional[str] = None,
    period: str = "5y",
    tickers: Optional[List[str]] = None,
    fallback_offline: bool = False,
    conn = None
) -> Dict[str, Any]:
    """Orchestrates end-to-end ingestion of Nifty 50 historical market data.

    1. Upserts all Nifty 50 metadata into SECURITY_MASTER.
    2. Retrieves mapped UUIDs.
    3. Fetches 5-year OHLCV for each constituent.
    4. Upserts records into DAILY_MARKET_QUOTE.
    5. Refreshes mv_daily_sector_concentration.
    """
    start_time = time.time()
    logger.info("=== Starting Nifty 50 Market Data Ingestion Pipeline ===")

    close_conn_at_end = False
    if conn is None:
        conn = get_db_connection(db_url)
        close_conn_at_end = True

    try:
        # Step 1: Upsert SECURITY_MASTER
        selected_constituents = NIFTY_50_CONSTITUENTS
        if tickers:
            selected_constituents = [
                c for c in NIFTY_50_CONSTITUENTS
                if c["ticker_symbol"] in tickers or c["yfinance_symbol"] in tickers
            ]

        ticker_map = upsert_security_master(conn, selected_constituents)
        if not ticker_map:
            ticker_map = get_security_master_map(conn)

        logger.info(f"Target securities in registry: {len(ticker_map)}")

        # Step 2: Fetch and upsert quotes for each constituent
        total_quotes_inserted = 0
        symbols_processed = 0
        errors = []

        all_quotes_to_insert = []
        for constituent in selected_constituents:
            ticker = constituent["ticker_symbol"]
            yf_sym = constituent["yfinance_symbol"]
            sec_id = ticker_map.get(ticker)

            if not sec_id:
                logger.error(f"Missing security_id for {ticker}. Skipping.")
                continue

            try:
                quotes_df = fetch_symbol_quotes(
                    yf_sym,
                    period=period,
                    fallback_offline=fallback_offline
                )
                if not quotes_df.empty:
                    quote_records = transform_quotes_for_db(quotes_df, sec_id)
                    all_quotes_to_insert.extend(quote_records)
                    symbols_processed += 1
                else:
                    message = f"{ticker}: no valid quotes retrieved from {yf_sym}"
                    logger.error(message)
                    errors.append(message)
            except Exception as e:
                logger.error(f"Error processing quotes for {ticker}: {e}")
                errors.append(f"{ticker}: {str(e)}")

        # Step 3: Batch upsert into DAILY_MARKET_QUOTE
        if all_quotes_to_insert:
            logger.info(f"Writing {len(all_quotes_to_insert)} total quotes to DAILY_MARKET_QUOTE...")
            total_quotes_inserted = upsert_daily_quotes(conn, all_quotes_to_insert, batch_size=10000)

        # Step 4: Refresh Materialized View
        if not refresh_sector_concentration_view(conn):
            message = "Failed to refresh mv_daily_sector_concentration"
            logger.error(message)
            errors.append(message)

        elapsed = round(time.time() - start_time, 2)
        logger.info(f"=== Ingestion Finished in {elapsed}s: {symbols_processed} symbols, {total_quotes_inserted} quotes ===")

        return {
            "status": "success" if not errors else "partial_success",
            "securities_count": len(selected_constituents),
            "symbols_processed": symbols_processed,
            "quotes_inserted": total_quotes_inserted,
            "elapsed_seconds": elapsed,
            "errors": errors,
        }

    finally:
        if close_conn_at_end and conn is not None:
            conn.close()


def main() -> int:
    """Run the real-data historical ingestion CLI (synthetic fallback is opt-in)."""
    parser = argparse.ArgumentParser(description="Ingest Nifty 50 historical quotes into risk_db")
    parser.add_argument("--db-url", default=None, help="Risk DB URL (defaults to RISK_DB_URL / port 5433)")
    parser.add_argument("--period", default="5y", help="yfinance history period (default: 5y)")
    parser.add_argument("--symbols", nargs="+", help="Optional NSE ticker(s), e.g. RELIANCE TCS")
    parser.add_argument(
        "--allow-synthetic-fallback", action="store_true",
        help="Allow synthetic data if Yahoo Finance has no valid data (not recommended for production)",
    )
    args = parser.parse_args()

    result = ingest_nifty_50_history(
        db_url=args.db_url,
        period=args.period,
        tickers=args.symbols,
        fallback_offline=args.allow_synthetic_fallback,
    )
    logger.info("Ingestion result: %s", result)
    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
