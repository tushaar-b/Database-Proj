"""ETL module scaffolding tests."""
import unittest
import sys
from pathlib import Path

BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from etl.pipeline import ingest_nifty_50_history
from tests.etl.test_pipeline import create_mock_risk_db


class TestETLScaffold(unittest.TestCase):

    def test_etl_module_callable(self):
        """Verify ETL scaffold function executes without unhandled exceptions."""
        conn = create_mock_risk_db()
        result = ingest_nifty_50_history(tickers=["RELIANCE"], conn=conn, fallback_offline=True)
        self.assertEqual(result["status"], "success")


if __name__ == "__main__":
    unittest.main()

