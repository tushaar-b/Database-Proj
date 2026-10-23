"""Daily Market Data Refresh Job for IntelliVest.

Executes incremental daily quote ingestion for all active securities in SECURITY_MASTER,
upserts new and updated OHLCV quotes into DAILY_MARKET_QUOTE, and triggers refresh of
the analytical materialized views (mv_daily_sector_concentration).
"""
import sys
import time
import argparse
import logging
from datetime import date, timedelta
from typing import List, Optional, Dict, Any

from etl.constituents import NIFTY_50_CONSTITUENTS, CONSTITUENTS_BY_TICKER
from etl.db import (
    get_db_connection,
    get_security_master_map,
    upsert_daily_quotes,
    refresh_sector_concentration_view,
)
from etl.pipeline import fetch_symbol_quotes, transform_quotes_for_db

logger = logging.getLogger("etl.daily_refresh")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def run_daily_refresh(
    db_url: Optional[str] = None,
    days: int = 5,
    symbols: Optional[List[str]] = None,
    refresh_mv: bool = True,
    fallback_offline: bool = False,
    conn = None
) -> Dict[str, Any]:
    """Runs incremental daily refresh for Nifty 50 constituents."""
    start_time = time.time()
    logger.info(f"=== Starting Daily Market Data Refresh (lookback={days} days) ===")

    close_conn_at_end = False
    if conn is None:
        conn = get_db_connection(db_url)
        close_conn_at_end = True

    try:
        # Step 1: Read active securities
        security_map = get_security_master_map(conn)
        if not security_map:
            logger.warning("No securities found in SECURITY_MASTER. Running initial setup first...")
            from etl.db import upsert_security_master
            security_map = upsert_security_master(conn, NIFTY_50_CONSTITUENTS)

        target_tickers = symbols if symbols else list(security_map.keys())
        logger.info(f"Refreshing quotes for {len(target_tickers)} securities.")

        start_date = (date.today() - timedelta(days=days)).isoformat()
        end_date = (date.today() + timedelta(days=1)).isoformat()

        all_quotes = []
        updated_count = 0
        errors = []

        for ticker in target_tickers:
            sec_id = security_map.get(ticker)
            if not sec_id:
                logger.warning(f"Ticker {ticker} not found in database registry. Skipping.")
                continue

            yf_sym = f"{ticker}.NS"
            try:
                quotes_df = fetch_symbol_quotes(
                    yf_sym,
                    start=start_date,
                    end=end_date,
                    fallback_offline=fallback_offline
                )
                if not quotes_df.empty:
                    records = transform_quotes_for_db(quotes_df, sec_id)
                    all_quotes.extend(records)
                    updated_count += 1
            except Exception as e:
                logger.error(f"Failed to refresh {ticker}: {e}")
                errors.append(f"{ticker}: {str(e)}")

        # Upsert records
        inserted_rows = 0
        if all_quotes:
            inserted_rows = upsert_daily_quotes(conn, all_quotes)

        # Step 3: Refresh Materialized View
        if refresh_mv:
            refresh_sector_concentration_view(conn)

        elapsed = round(time.time() - start_time, 2)
        logger.info(f"=== Daily Refresh Completed in {elapsed}s: {updated_count} symbols, {inserted_rows} rows ===")

        return {
            "status": "success" if not errors else "partial_success",
            "symbols_refreshed": updated_count,
            "quotes_upserted": inserted_rows,
            "lookback_days": days,
            "elapsed_seconds": elapsed,
            "errors": errors,
        }

    finally:
        if close_conn_at_end and conn is not None:
            conn.close()


def main():
    parser = argparse.ArgumentParser(description="IntelliVest Daily Market Data Refresh Job")
    parser.add_argument("--db-url", type=str, default=None, help="PostgreSQL connection string for risk_db")
    parser.add_argument("--days", type=int, default=5, help="Number of lookback days to refresh (default: 5)")
    parser.add_argument("--symbols", nargs="+", default=None, help="Optional subset of ticker symbols to refresh")
    parser.add_argument("--skip-mv", action="store_true", help="Skip refreshing materialized view")
    parser.add_argument("--no-fallback", action="store_true", help="Disable synthetic offline fallback")

    args = parser.parse_args()

    result = run_daily_refresh(
        db_url=args.db_url,
        days=args.days,
        symbols=args.symbols,
        refresh_mv=not args.skip_mv,
        fallback_offline=False,
    )

    if result["status"] != "success" and result["errors"]:
        logger.warning(f"Refresh completed with errors: {result['errors']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
