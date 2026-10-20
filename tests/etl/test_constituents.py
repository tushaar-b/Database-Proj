"""Unit tests for Nifty 50 constituent dataset and metadata validation."""
import unittest
import sys
from pathlib import Path

BASE_DIR = str(Path(__file__).resolve().parent.parent.parent)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from etl.constituents import (
    NIFTY_50_CONSTITUENTS,
    get_all_tickers,
    get_all_yfinance_symbols,
    get_constituent,
)


class TestConstituents(unittest.TestCase):
    """Validates the structure, completeness, and integrity of Nifty 50 metadata."""

    def test_nifty_50_total_count(self):
        """Assert exactly 50 constituent stocks are defined."""
        self.assertEqual(len(NIFTY_50_CONSTITUENTS), 50)

    def test_unique_tickers(self):
        """Assert all ticker symbols and yfinance symbols are strictly unique."""
        tickers = get_all_tickers()
        yf_symbols = get_all_yfinance_symbols()

        self.assertEqual(len(tickers), 50)
        self.assertEqual(len(set(tickers)), 50, "Duplicate ticker detected in constituents.")
        self.assertEqual(len(set(yf_symbols)), 50, "Duplicate yfinance symbol detected.")

    def test_required_metadata_fields(self):
        """Assert every constituent record contains all non-null required fields."""
        required_fields = ["ticker_symbol", "yfinance_symbol", "company_name", "sector_name", "exchange_code", "beta_index"]
        
        for constituent in NIFTY_50_CONSTITUENTS:
            for field in required_fields:
                self.assertIn(field, constituent, f"Missing {field} in {constituent}")
                self.assertIsNotNone(constituent[field], f"Field {field} is None for {constituent['ticker_symbol']}")

            self.assertEqual(constituent["exchange_code"], "NSE")
            self.assertGreater(constituent["beta_index"], 0.2, f"Beta too low for {constituent['ticker_symbol']}")
            self.assertLess(constituent["beta_index"], 3.0, f"Beta too high for {constituent['ticker_symbol']}")

    def test_constituent_lookup_helpers(self):
        """Test looking up constituents by ticker and by yfinance symbol."""
        reliance = get_constituent("RELIANCE")
        self.assertEqual(reliance["company_name"], "Reliance Industries Limited")
        self.assertEqual(reliance["sector_name"], "Energy")

        tcs_by_yf = get_constituent("TCS.NS")
        self.assertEqual(tcs_by_yf["ticker_symbol"], "TCS")
        self.assertEqual(tcs_by_yf["sector_name"], "Information Technology")

        with self.assertRaises(KeyError):
            get_constituent("INVALID_SYMBOL_123")


if __name__ == "__main__":
    unittest.main()
