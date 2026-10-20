"""Scaffolding tests verifying folder structure and baseline project files."""
import unittest
from pathlib import Path


class TestProjectScaffolding(unittest.TestCase):

    def test_directory_structure_exists(self):
        """Assert all required top-level directories exist."""
        base_dir = Path(__file__).parent.parent
        expected_dirs = ["db", "etl", "backend", "frontend", "tests", "docs"]

        for d in expected_dirs:
            dir_path = base_dir / d
            self.assertTrue(dir_path.exists(), f"Required directory '{d}' is missing.")
            self.assertTrue(dir_path.is_dir(), f"'{d}' is not a directory.")

    def test_core_files_exist(self):
        """Assert all required configuration files exist."""
        base_dir = Path(__file__).parent.parent
        expected_files = [
            ".env.example",
            "README.md",
            "requirements.txt",
            "docker-compose.yml",
            "pyproject.toml",
            "pytest.ini",
        ]

        for f in expected_files:
            file_path = base_dir / f
            self.assertTrue(file_path.exists(), f"Required file '{f}' is missing.")
            self.assertTrue(file_path.is_file(), f"'{f}' is not a file.")

    def test_env_example_placeholders(self):
        """Assert .env.example contains all required environment variables."""
        base_dir = Path(__file__).parent.parent
        env_file = base_dir / ".env.example"
        content = env_file.read_text(encoding="utf-8")

        self.assertIn("ADVISORY_DB_URL", content)
        self.assertIn("RISK_DB_URL", content)
        self.assertIn("MARKET_DATA_PROVIDER", content)
        self.assertIn("yfinance", content)


if __name__ == "__main__":
    unittest.main()
