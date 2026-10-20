"""Small deterministic smoke test for the PostgreSQL Phase 3 analytics."""
import os
import uuid

import pytest

psycopg2 = pytest.importorskip("psycopg2")


@pytest.fixture
def risk_connection():
    url = os.getenv(
        "RISK_DB_URL",
        "postgresql://postgres:postgres@localhost:5433/risk_db",
    )
    try:
        connection = psycopg2.connect(url, connect_timeout=2)
    except psycopg2.OperationalError as exc:
        pytest.skip(f"risk PostgreSQL is unavailable: {exc}")
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


def test_risk_summary_deterministic_series_and_empty_portfolio(risk_connection):
    portfolio_id, empty_id, security_id, user_id = [str(uuid.uuid4()) for _ in range(4)]
    with risk_connection.cursor() as cur:
        cur.execute(
            "INSERT INTO portfolio (portfolio_id, user_id, portfolio_name) VALUES (%s, %s, 'analytics smoke')",
            (portfolio_id, user_id),
        )
        cur.execute(
            "INSERT INTO portfolio (portfolio_id, user_id, portfolio_name, cash_balance) VALUES (%s, %s, 'empty smoke', 250)",
            (empty_id, user_id),
        )
        cur.execute(
            "INSERT INTO security_master (security_id, ticker_symbol, company_name, sector_name) VALUES (%s, %s, 'Smoke Security', 'Technology')",
            (security_id, f"T{uuid.uuid4().hex[:10]}",),
        )
        cur.execute(
            "INSERT INTO holding (portfolio_id, security_id, quantity, average_buy_price) VALUES (%s, %s, 10, 100)",
            (portfolio_id, security_id),
        )
        cur.execute(
            """INSERT INTO daily_market_quote (security_id, trade_date, close_price, adjusted_close, volume)
               SELECT %s, DATE '2025-01-01' + n,
                      CASE WHEN n %% 2 = 0 THEN 100 ELSE 110 END,
                      CASE WHEN n %% 2 = 0 THEN 100 ELSE 110 END, 1000
               FROM generate_series(0, 252) AS n""",
            (security_id,),
        )
        cur.execute("REFRESH MATERIALIZED VIEW mv_daily_sector_concentration")
        cur.execute(
            """SELECT daily_return, rolling_volatility_30d, return_observations_30d
               FROM daily_security_returns WHERE security_id = %s ORDER BY trade_date ASC LIMIT 1""",
            (security_id,),
        )
        first_return, first_volatility, first_count = cur.fetchone()
        assert first_return is None
        assert first_volatility is None
        assert first_count == 0
        cur.execute(
            """SELECT daily_return, rolling_volatility_30d, return_observations_30d
               FROM daily_security_returns WHERE security_id = %s ORDER BY trade_date DESC LIMIT 1""",
            (security_id,),
        )
        latest_return, latest_volatility, latest_count = cur.fetchone()
        assert latest_return == pytest.approx(-1 / 11)
        assert latest_volatility == pytest.approx(0.0970863653, rel=1e-8)
        assert latest_count == 30
        cur.execute(
            """SELECT portfolio_valuation, volatility_30d, parametric_var_95,
                      historical_var_95, sharpe_ratio, sector_hhi,
                      historical_observations, calculation_status
               FROM portfolio_risk_summary(%s)""",
            (portfolio_id,),
        )
        valuation, volatility, parametric_var, historical_var, sharpe, hhi, observations, status = cur.fetchone()
        assert float(valuation) == pytest.approx(1000.0)
        assert volatility == pytest.approx(0.0970863653, rel=1e-8)
        assert float(parametric_var) == pytest.approx(159.7070709, rel=1e-8)
        assert float(historical_var) == pytest.approx(90.9090909, rel=1e-8)
        assert sharpe == pytest.approx(0.7280825054, rel=1e-8)
        assert float(hhi) == pytest.approx(1.0)
        assert observations == 252
        assert status == "ok"

        cur.execute(
            """SELECT volatility_30d, parametric_var_95, historical_var_95, sharpe_ratio,
                      calculation_status
               FROM portfolio_risk_summary(%s)""",
            (empty_id,),
        )
        empty = cur.fetchone()
        assert empty[:4] == (None, None, None, None)
        assert empty[4] == "insufficient_history_252_required"
