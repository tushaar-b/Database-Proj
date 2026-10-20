"""Unit and integration tests for the Market Data Ingestion Pipeline."""
import unittest
import sqlite3
import uuid
from datetime import date
from pathlib import Path
import sys

BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from etl.constituents import NIFTY_50_CONSTITUENTS
from etl.pipeline import (
    generate_synthetic_quotes,
    transform_quotes_for_db,
    ingest_nifty_50_history,
)
from etl.db import (
    upsert_security_master,
    upsert_daily_quotes,
    get_security_master_map,
    get_cursor,
)


def create_mock_risk_db():
    """Initializes an in-memory SQLite database matching risk_db schema."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute("""
            CREATE TABLE SECURITY_MASTER (
                security_id TEXT PRIMARY KEY,
                ticker_symbol TEXT UNIQUE NOT NULL,
                company_name TEXT NOT NULL,
                sector_name TEXT NOT NULL,
                exchange_code TEXT NOT NULL DEFAULT 'NSE',
                beta_index REAL DEFAULT 1.00
            );
        """)
        conn.execute("""
            CREATE TABLE DAILY_MARKET_QUOTE (
                quote_id TEXT PRIMARY KEY,
                security_id TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                close_price REAL NOT NULL CHECK (close_price > 0),
                adjusted_close REAL NOT NULL CHECK (adjusted_close > 0),
                volume INTEGER NOT NULL CHECK (volume >= 0),
                CONSTRAINT uq_security_trade_date UNIQUE (security_id, trade_date),
                FOREIGN KEY (security_id) REFERENCES SECURITY_MASTER(security_id)
            );
        """)
        conn.execute("""
            CREATE INDEX idx_quote_temporal 
            ON DAILY_MARKET_QUOTE (security_id, trade_date DESC);
        """)
    return conn


class TestMarketDataPipeline(unittest.TestCase):
    """Tests the data transformation and ingestion pipeline routines."""

    def test_generate_synthetic_quotes(self):
        """Assert synthetic quote generation creates valid OHLCV series."""
        days = 250
        df = generate_synthetic_quotes("TCS", days=days, base_price=3500.0)
        self.assertEqual(len(df), days)
        self.assertIn("trade_date", df.columns)
        self.assertIn("close_price", df.columns)
        self.assertIn("adjusted_close", df.columns)
        self.assertIn("volume", df.columns)
        
        # Check valid value bounds
        self.assertTrue((df["close_price"] > 0).all())
        self.assertTrue((df["adjusted_close"] > 0).all())
        self.assertTrue((df["volume"] >= 0).all())

    def test_transform_quotes_for_db(self):
        """Assert transformation generates valid database record dicts."""
        df = generate_synthetic_quotes("INFY", days=10, base_price=1500.0)
        mock_sec_id = str(uuid.uuid4())
        records = transform_quotes_for_db(df, mock_sec_id)
        
        self.assertEqual(len(records), 10)
        first = records[0]
        self.assertEqual(first["security_id"], mock_sec_id)
        self.assertIsInstance(first["trade_date"], date)
        self.assertGreater(first["close_price"], 0)
        self.assertGreater(first["adjusted_close"], 0)
        self.assertGreaterEqual(first["volume"], 0)

    def test_upsert_security_master_and_quotes(self):
        """Test upserting securities and quotes into database."""
        conn = create_mock_risk_db()
        sample_securities = NIFTY_50_CONSTITUENTS[:5]
        
        # Step 1: Upsert Security Master
        sec_map = upsert_security_master(conn, sample_securities, is_sqlite=True)
        self.assertEqual(len(sec_map), 5)
        self.assertIn("RELIANCE", sec_map)
        
        # Step 2: Generate and upsert quotes
        rel_id = sec_map["RELIANCE"]
        quotes_df = generate_synthetic_quotes("RELIANCE", days=50, base_price=2800.0)
        records = transform_quotes_for_db(quotes_df, rel_id)
        inserted = upsert_daily_quotes(conn, records, is_sqlite=True)
        self.assertEqual(inserted, 50)

        # Step 3: Verify row count in DB
        with get_cursor(conn) as cur:
            cur.execute("SELECT COUNT(*) FROM DAILY_MARKET_QUOTE WHERE security_id = ?", (rel_id,))
            count = cur.fetchone()[0]
            self.assertEqual(count, 50)

    def test_idempotency_of_pipeline_upserts(self):
        """Assert running ingestion twice does not create duplicate rows or errors."""
        conn = create_mock_risk_db()
        sample_tickers = ["RELIANCE", "TCS"]
        
        # Run 1
        res1 = ingest_nifty_50_history(
            period="1y",
            tickers=sample_tickers,
            fallback_offline=True,
            conn=conn
        )
        self.assertEqual(res1["status"], "success")

        with get_cursor(conn) as cur:
            cur.execute("SELECT COUNT(*) FROM DAILY_MARKET_QUOTE;")
            count_after_run1 = cur.fetchone()[0]
            self.assertGreater(count_after_run1, 0)

        # Run 2 (Same dataset)
        res2 = ingest_nifty_50_history(
            period="1y",
            tickers=sample_tickers,
            fallback_offline=True,
            conn=conn
        )
        self.assertEqual(res2["status"], "success")

        with get_cursor(conn) as cur:
            cur.execute("SELECT COUNT(*) FROM DAILY_MARKET_QUOTE;")
            count_after_run2 = cur.fetchone()[0]
            # Must be strictly equal due to ON CONFLICT upsert
            self.assertEqual(count_after_run1, count_after_run2)


if __name__ == "__main__":
    unittest.main()
