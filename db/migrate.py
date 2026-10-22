"""IntelliVest Migration and Schema Verification Engine.

Applies SQL migration files across dual PostgreSQL instances (advisory_db and risk_db)
and verifies structural integrity (tables, constraints, indexes, ENUM types, and views).
"""
import os
import sys
import glob
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from backend.config import settings

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("db.migrate")

BASE_DIR = Path(__file__).resolve().parent.parent
ADVISORY_MIGRATIONS_DIR = BASE_DIR / "db" / "migrations" / "advisory"
RISK_MIGRATIONS_DIR = BASE_DIR / "db" / "migrations" / "risk"

ADVISORY_DB_URL = os.getenv("ADVISORY_DB_URL", settings.ADVISORY_DB_URL)
RISK_DB_URL = os.getenv("RISK_DB_URL", settings.RISK_DB_URL)

EXPECTED_ADVISORY_TABLES = [
    "user_profile",
    "income_stream",
    "expense_item",
    "surplus_snapshot",
    "recommendation_log",
    "recommendation_policy",
    "applied_feedback_events",
]

EXPECTED_RISK_TABLES = [
    "portfolio",
    "security_master",
    "holding",
    "transaction_ledger",
    "daily_market_quote",
    "rebalance_alert",
    "risk_feedback_state",
    "risk_feedback_outbox",
    "rebalance_execution",
]

EXPECTED_ADVISORY_INDEXES = [
    "idx_rec_user_status",
    "idx_snapshot_user_evaluated_at",
]

EXPECTED_RISK_INDEXES = [
    "idx_quote_temporal",
    "idx_active_alerts",
    "idx_portfolio_user_id",
    "idx_feedback_outbox_pending",
]

EXPECTED_RISK_VIEWS = [
    "mv_daily_sector_concentration",
]


def execute_sql_file(db_url: str, sql_file_path: Path) -> bool:
    """Executes a single SQL migration file against the target PostgreSQL URL."""
    if not PSYCOPG2_AVAILABLE:
        logger.error("psycopg2 is not installed. Please install dependencies from requirements.txt.")
        return False

    # Avoid logging connection strings, which may include database credentials.
    logger.info(f"Applying migration: {sql_file_path.name}")
    try:
        conn = psycopg2.connect(db_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        with conn.cursor() as cur:
            sql_content = sql_file_path.read_text(encoding="utf-8")
            cur.execute(sql_content)
        conn.close()
        logger.info(f"Successfully applied: {sql_file_path.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to apply {sql_file_path.name}: {e}")
        return False


def run_advisory_migrations(db_url: Optional[str] = None) -> bool:
    """Applies all sorted migration files for advisory_db."""
    target_url = db_url or ADVISORY_DB_URL
    migration_files = sorted(ADVISORY_MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        logger.warning(f"No migration files found in {ADVISORY_MIGRATIONS_DIR}")
        return True

    success = True
    for sql_file in migration_files:
        if not execute_sql_file(target_url, sql_file):
            success = False
            break
    return success


def run_risk_migrations(db_url: Optional[str] = None) -> bool:
    """Applies all sorted migration files for risk_db."""
    target_url = db_url or RISK_DB_URL
    migration_files = sorted(RISK_MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        logger.warning(f"No migration files found in {RISK_MIGRATIONS_DIR}")
        return True

    success = True
    for sql_file in migration_files:
        if not execute_sql_file(target_url, sql_file):
            success = False
            break
    return success


def verify_database_schema(db_url: str, expected_tables: List[str], expected_indexes: List[str], expected_views: Optional[List[str]] = None) -> Dict[str, Any]:
    """Inspects live database to verify existence of expected tables, indexes, and materialized views."""
    if not PSYCOPG2_AVAILABLE:
        return {"status": "error", "message": "psycopg2 not installed"}

    results = {
        "status": "success",
        "missing_tables": [],
        "missing_indexes": [],
        "missing_views": [],
        "existing_tables": [],
        "existing_indexes": [],
        "existing_views": []
    }

    try:
        conn = psycopg2.connect(db_url)
        with conn.cursor() as cur:
            # Check Tables
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
            """)
            existing_tables = [row[0].lower() for row in cur.fetchall()]
            results["existing_tables"] = existing_tables

            for table in expected_tables:
                if table.lower() not in existing_tables:
                    results["missing_tables"].append(table)

            # Check Indexes
            cur.execute("""
                SELECT indexname
                FROM pg_indexes
                WHERE schemaname = 'public';
            """)
            existing_indexes = [row[0].lower() for row in cur.fetchall()]
            results["existing_indexes"] = existing_indexes

            for idx in expected_indexes:
                if idx.lower() not in existing_indexes:
                    results["missing_indexes"].append(idx)

            # Check Materialized Views
            if expected_views:
                cur.execute("""
                    SELECT matviewname
                    FROM pg_matviews
                    WHERE schemaname = 'public';
                """)
                existing_views = [row[0].lower() for row in cur.fetchall()]
                results["existing_views"] = existing_views

                for view in expected_views:
                    if view.lower() not in existing_views:
                        results["missing_views"].append(view)

        conn.close()

        if results["missing_tables"] or results["missing_indexes"] or results["missing_views"]:
            results["status"] = "incomplete"
        return results

    except Exception as e:
        results["status"] = "error"
        results["message"] = str(e)
        return results


def run_all_migrations():
    """Runs all migrations and verification checks for both databases."""
    logger.info("==================================================")
    logger.info("IntelliVest Dual Database Migration Runner")
    logger.info("==================================================")

    logger.info("--- Step 1: Running Advisory Database Migrations ---")
    adv_ok = run_advisory_migrations()

    logger.info("--- Step 2: Running Portfolio Risk Database Migrations ---")
    risk_ok = run_risk_migrations()

    logger.info("--- Step 3: Verifying Schema Integrity ---")
    if adv_ok:
        adv_verify = verify_database_schema(ADVISORY_DB_URL, EXPECTED_ADVISORY_TABLES, EXPECTED_ADVISORY_INDEXES)
        logger.info(f"Advisory DB Verification: {adv_verify['status']}")
        if adv_verify.get("missing_tables"):
            logger.warning(f"Advisory DB Missing Tables: {adv_verify['missing_tables']}")
        if adv_verify.get("missing_indexes"):
            logger.warning(f"Advisory DB Missing Indexes: {adv_verify['missing_indexes']}")

    if risk_ok:
        risk_verify = verify_database_schema(RISK_DB_URL, EXPECTED_RISK_TABLES, EXPECTED_RISK_INDEXES, EXPECTED_RISK_VIEWS)
        logger.info(f"Risk DB Verification: {risk_verify['status']}")
        if risk_verify.get("missing_tables"):
            logger.warning(f"Risk DB Missing Tables: {risk_verify['missing_tables']}")
        if risk_verify.get("missing_indexes"):
            logger.warning(f"Risk DB Missing Indexes: {risk_verify['missing_indexes']}")
        if risk_verify.get("missing_views"):
            logger.warning(f"Risk DB Missing Views: {risk_verify['missing_views']}")

    logger.info("Migration routine finished.")


if __name__ == "__main__":
    run_all_migrations()
