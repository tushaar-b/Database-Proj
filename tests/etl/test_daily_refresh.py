"""Tests for Daily Market Data Refresh Job."""
import unittest
import sqlite3
import sys
from pathlib import Path

BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from etl.constituents import NIFTY_50_CONSTITUENTS
from etl.run_daily_refresh import run_daily_refresh
from etl.db import get_cursor
from tests.etl.test_pipeline import create_mock_risk_db


class TestDailyRefresh(unittest.TestCase):
    """Tests incremental daily market data refresh behavior."""

    def test_daily_refresh_execution(self):
        """Assert daily refresh job runs and inserts fresh quotes."""
        conn = create_mock_risk_db()
        target_symbols = ["HDFCBANK", "INFY"]

        result = run_daily_refresh(
            days=5,
            symbols=target_symbols,
            refresh_mv=False,
            fallback_offline=True,
            conn=conn
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["symbols_refreshed"], 2)
        self.assertGreater(result["quotes_upserted"], 0)

        with get_cursor(conn) as cur:
            cur.execute("SELECT COUNT(DISTINCT security_id) FROM DAILY_MARKET_QUOTE;")
            distinct_securities = cur.fetchone()[0]
            self.assertEqual(distinct_securities, 2)


if __name__ == "__main__":
    unittest.main()
