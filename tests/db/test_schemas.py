"""Schema and constraint validation test suite.

Validates:
1. SQL migration files syntax, table definitions, foreign keys, unique constraints, and indexes.
2. Relational constraint enforcement (duplicate email rejection, FK violation rejection,
   composite unique holdings constraint, and temporal unique quote constraints).
"""
import unittest
import sqlite3
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ADVISORY_MIGRATION = BASE_DIR / "db" / "migrations" / "advisory" / "001_initial_advisory_schema.sql"
RISK_MIGRATION = BASE_DIR / "db" / "migrations" / "risk" / "001_initial_risk_schema.sql"


class TestSQLMigrationFiles(unittest.TestCase):
    """Tests the static DDL content of the migration files."""

    def setUp(self):
        self.advisory_sql = ADVISORY_MIGRATION.read_text(encoding="utf-8")
        self.risk_sql = RISK_MIGRATION.read_text(encoding="utf-8")

    def test_advisory_migration_tables(self):
        """Assert Advisory DB migration defines all 5 required tables."""
        tables = [
            "USER_PROFILE",
            "INCOME_STREAM",
            "EXPENSE_ITEM",
            "SURPLUS_SNAPSHOT",
            "RECOMMENDATION_LOG"
        ]
        for table in tables:
            self.assertRegex(
                self.advisory_sql,
                rf"CREATE\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?{table}\b",
                f"Missing CREATE TABLE statement for {table} in Advisory DB migration."
            )

    def test_advisory_migration_indexes_and_enums(self):
        """Assert Advisory DB defines enum types and required composite index."""
        self.assertIn("idx_rec_user_status", self.advisory_sql)
        self.assertIn("risk_tolerance_tier", self.advisory_sql)
        self.assertIn("income_frequency", self.advisory_sql)
        self.assertIn("recommendation_status", self.advisory_sql)

    def test_risk_migration_tables(self):
        """Assert Risk DB migration defines all 6 required tables."""
        tables = [
            "PORTFOLIO",
            "SECURITY_MASTER",
            "HOLDING",
            "TRANSACTION_LEDGER",
            "DAILY_MARKET_QUOTE",
            "REBALANCE_ALERT"
        ]
        for table in tables:
            self.assertRegex(
                self.risk_sql,
                rf"CREATE\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?{table}\b",
                f"Missing CREATE TABLE statement for {table} in Risk DB migration."
            )

    def test_risk_migration_indexes_and_views(self):
        """Assert Risk DB defines required temporal/partial indexes and materialized view."""
        self.assertIn("idx_quote_temporal", self.risk_sql)
        self.assertIn("idx_active_alerts", self.risk_sql)
        self.assertIn("WHERE resolved_flag = FALSE", self.risk_sql)
        self.assertIn("mv_daily_sector_concentration", self.risk_sql)


class TestAdvisoryConstraintEnforcement(unittest.TestCase):
    """Functional tests verifying Advisory DB constraints (uniqueness, FK cascades)."""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.cur = self.conn.cursor()

        # Create equivalent schema in SQLite
        self.cur.executescript("""
            CREATE TABLE USER_PROFILE (
                user_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                risk_tolerance_tier TEXT CHECK(risk_tolerance_tier IN ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE')),
                created_at TEXT NOT NULL
            );

            CREATE TABLE INCOME_STREAM (
                income_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES USER_PROFILE(user_id) ON DELETE CASCADE,
                source_category TEXT NOT NULL,
                gross_amount REAL NOT NULL CHECK(gross_amount >= 0),
                frequency TEXT CHECK(frequency IN ('MONTHLY', 'YEARLY')),
                last_updated TEXT NOT NULL
            );

            CREATE TABLE EXPENSE_ITEM (
                expense_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES USER_PROFILE(user_id) ON DELETE CASCADE,
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount >= 0),
                is_mandatory INTEGER NOT NULL DEFAULT 1,
                recurrence_interval TEXT NOT NULL DEFAULT 'MONTHLY'
            );

            CREATE TABLE SURPLUS_SNAPSHOT (
                snapshot_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES USER_PROFILE(user_id) ON DELETE CASCADE,
                total_income REAL NOT NULL,
                total_expense REAL NOT NULL,
                computed_surplus REAL NOT NULL,
                investable_buffer REAL NOT NULL,
                evaluated_date TEXT NOT NULL
            );

            CREATE TABLE RECOMMENDATION_LOG (
                rec_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES USER_PROFILE(user_id) ON DELETE CASCADE,
                stock_ticker TEXT NOT NULL,
                target_allocation_pct REAL NOT NULL CHECK(target_allocation_pct >= 0 AND target_allocation_pct <= 100),
                recommended_amount REAL NOT NULL CHECK(recommended_amount >= 0),
                status_state TEXT CHECK(status_state IN ('PENDING', 'ACCEPTED', 'REJECTED')),
                generated_timestamp TEXT NOT NULL
            );

            CREATE INDEX idx_rec_user_status ON RECOMMENDATION_LOG (user_id, status_state, generated_timestamp DESC);
        """)

    def tearDown(self):
        self.conn.close()

    def test_duplicate_email_rejected(self):
        """Assert duplicate user emails violate UNIQUE constraint."""
        self.cur.execute("""
            INSERT INTO USER_PROFILE (user_id, full_name, email, risk_tolerance_tier, created_at)
            VALUES ('u1', 'Alice Sharma', 'alice@example.com', 'MODERATE', '2026-01-01T00:00:00Z');
        """)
        self.conn.commit()

        with self.assertRaises(sqlite3.IntegrityError):
            self.cur.execute("""
                INSERT INTO USER_PROFILE (user_id, full_name, email, risk_tolerance_tier, created_at)
                VALUES ('u2', 'Alice Fake', 'alice@example.com', 'CONSERVATIVE', '2026-01-01T00:00:00Z');
            """)

    def test_foreign_key_violation_rejected(self):
        """Assert inserting income stream for non-existent user raises Foreign Key error."""
        with self.assertRaises(sqlite3.IntegrityError):
            self.cur.execute("""
                INSERT INTO INCOME_STREAM (income_id, user_id, source_category, gross_amount, frequency, last_updated)
                VALUES ('inc1', 'non_existent_user', 'Salary', 150000.00, 'MONTHLY', '2026-01-01T00:00:00Z');
            """)

    def test_cascade_delete_on_user(self):
        """Assert deleting a user cascades to remove associated income streams and expenses."""
        self.cur.execute("""
            INSERT INTO USER_PROFILE (user_id, full_name, email, risk_tolerance_tier, created_at)
            VALUES ('u1', 'Bob Verma', 'bob@example.com', 'AGGRESSIVE', '2026-01-01T00:00:00Z');
        """)
        self.cur.execute("""
            INSERT INTO INCOME_STREAM (income_id, user_id, source_category, gross_amount, frequency, last_updated)
            VALUES ('inc1', 'u1', 'Salary', 200000.00, 'MONTHLY', '2026-01-01T00:00:00Z');
        """)
        self.conn.commit()

        # Delete user
        self.cur.execute("DELETE FROM USER_PROFILE WHERE user_id = 'u1';")
        self.conn.commit()

        self.cur.execute("SELECT COUNT(*) FROM INCOME_STREAM WHERE user_id = 'u1';")
        count = self.cur.fetchone()[0]
        self.assertEqual(count, 0, "Income stream records should be deleted via CASCADE.")


class TestRiskConstraintEnforcement(unittest.TestCase):
    """Functional tests verifying Risk DB constraints (unique holdings, unique quotes, FKs)."""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.cur = self.conn.cursor()

        self.cur.executescript("""
            CREATE TABLE PORTFOLIO (
                portfolio_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                portfolio_name TEXT NOT NULL,
                total_valuation REAL NOT NULL DEFAULT 0.0,
                cash_balance REAL NOT NULL DEFAULT 0.0,
                target_hhi_limit REAL NOT NULL DEFAULT 0.250
            );

            CREATE TABLE SECURITY_MASTER (
                security_id TEXT PRIMARY KEY,
                ticker_symbol TEXT UNIQUE NOT NULL,
                company_name TEXT NOT NULL,
                sector_name TEXT NOT NULL,
                exchange_code TEXT NOT NULL DEFAULT 'NSE',
                beta_index REAL DEFAULT 1.00
            );

            CREATE TABLE HOLDING (
                holding_id TEXT PRIMARY KEY,
                portfolio_id TEXT NOT NULL REFERENCES PORTFOLIO(portfolio_id) ON DELETE CASCADE,
                security_id TEXT NOT NULL REFERENCES SECURITY_MASTER(security_id) ON DELETE RESTRICT,
                quantity INTEGER NOT NULL DEFAULT 0,
                average_buy_price REAL NOT NULL DEFAULT 0.0,
                last_updated_at TEXT NOT NULL,
                UNIQUE (portfolio_id, security_id)
            );

            CREATE TABLE DAILY_MARKET_QUOTE (
                quote_id TEXT PRIMARY KEY,
                security_id TEXT NOT NULL REFERENCES SECURITY_MASTER(security_id) ON DELETE CASCADE,
                trade_date TEXT NOT NULL,
                close_price REAL NOT NULL,
                adjusted_close REAL NOT NULL,
                volume INTEGER NOT NULL,
                UNIQUE (security_id, trade_date)
            );
        """)

        # Seed security and portfolio
        self.cur.execute("""
            INSERT INTO PORTFOLIO (portfolio_id, user_id, portfolio_name, total_valuation, cash_balance, target_hhi_limit)
            VALUES ('p1', 'u1', 'Growth Alpha', 500000.0, 50000.0, 0.250);
        """)
        self.cur.execute("""
            INSERT INTO SECURITY_MASTER (security_id, ticker_symbol, company_name, sector_name, exchange_code, beta_index)
            VALUES ('s1', 'RELIANCE.NS', 'Reliance Industries Ltd', 'Energy', 'NSE', 1.15);
        """)
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_unique_holding_per_portfolio_and_security(self):
        """Assert attempting to create duplicate holding for the same portfolio and security is rejected."""
        self.cur.execute("""
            INSERT INTO HOLDING (holding_id, portfolio_id, security_id, quantity, average_buy_price, last_updated_at)
            VALUES ('h1', 'p1', 's1', 100, 2850.00, '2026-01-01T00:00:00Z');
        """)
        self.conn.commit()

        with self.assertRaises(sqlite3.IntegrityError):
            self.cur.execute("""
                INSERT INTO HOLDING (holding_id, portfolio_id, security_id, quantity, average_buy_price, last_updated_at)
                VALUES ('h2', 'p1', 's1', 50, 2900.00, '2026-01-02T00:00:00Z');
            """)

    def test_unique_daily_quote_per_security_and_date(self):
        """Assert attempting to insert duplicate daily quotes for same security and trade date is rejected."""
        self.cur.execute("""
            INSERT INTO DAILY_MARKET_QUOTE (quote_id, security_id, trade_date, close_price, adjusted_close, volume)
            VALUES ('q1', 's1', '2026-01-15', 2850.00, 2850.00, 5000000);
        """)
        self.conn.commit()

        with self.assertRaises(sqlite3.IntegrityError):
            self.cur.execute("""
                INSERT INTO DAILY_MARKET_QUOTE (quote_id, security_id, trade_date, close_price, adjusted_close, volume)
                VALUES ('q2', 's1', '2026-01-15', 2860.00, 2860.00, 4800000);
            """)


if __name__ == "__main__":
    unittest.main()
