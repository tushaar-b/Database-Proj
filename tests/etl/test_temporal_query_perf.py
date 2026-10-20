"""Performance benchmark test for temporal quote retrieval on DAILY_MARKET_QUOTE."""
import unittest
import sqlite3
import sys
from pathlib import Path

BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from etl.constituents import NIFTY_50_CONSTITUENTS
from etl.benchmark import benchmark_temporal_query
from etl.pipeline import generate_synthetic_quotes, transform_quotes_for_db
from etl.db import upsert_security_master, upsert_daily_quotes
from tests.etl.test_pipeline import create_mock_risk_db


class TestTemporalQueryPerformance(unittest.TestCase):
    """Verifies that 30-day quote retrieval latency is strictly under 10ms."""

    @classmethod
    def setUpClass(cls):
        """Populate mock database with realistic 5-year data volume (~62,500 records)."""
        cls.conn = create_mock_risk_db()
        sec_map = upsert_security_master(cls.conn, NIFTY_50_CONSTITUENTS, is_sqlite=True)
        cls.sample_sec_id = list(sec_map.values())[0]

        all_quotes = []
        for ticker, sec_id in sec_map.items():
            # 1250 trading days = 5 full years of daily OHLCV
            df = generate_synthetic_quotes(ticker, days=1250, base_price=1000.0)
            records = transform_quotes_for_db(df, sec_id)
            all_quotes.extend(records)

        upsert_daily_quotes(cls.conn, all_quotes, batch_size=10000, is_sqlite=True)

    def test_sub_10ms_latency_target(self):
        """Assert p95 query latency is well below the 10ms non-functional requirement."""
        metrics = benchmark_temporal_query(
            self.conn,
            self.sample_sec_id,
            iterations=100,
            limit=30
        )

        self.assertEqual(metrics["rows_returned"], 30)
        self.assertTrue(
            metrics["target_met_sub_10ms"],
            f"p95 latency {metrics['p95_latency_ms']}ms exceeded 10ms target"
        )
        self.assertLess(
            metrics["p95_latency_ms"],
            10.0,
            f"p95 latency of {metrics['p95_latency_ms']}ms failed sub-10ms requirement"
        )


if __name__ == "__main__":
    unittest.main()
