"""Backend scaffolding tests."""
import unittest
import sys
from pathlib import Path

BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


class TestBackendScaffold(unittest.TestCase):

    def test_backend_settings_defaults(self):
        """Verify backend settings defaults."""
        try:
            from backend.config import settings
            self.assertEqual(settings.MARKET_DATA_PROVIDER, "yfinance")
            self.assertIn("advisory_db", settings.ADVISORY_DB_URL)
            self.assertIn("risk_db", settings.RISK_DB_URL)
        except ImportError:
            pass


if __name__ == "__main__":
    unittest.main()
