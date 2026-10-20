"""Small deterministic smoke test for the PostgreSQL Phase 3 analytics."""
import os
import uuid

import numpy as np
import pytest

psycopg2 = pytest.importorskip("psycopg2")


@pytest.fixture
def risk_connection():
    url = os.getenv("RISK_DB_URL")
    if not url:
        pytest.skip("RISK_DB_URL is not configured")
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
            """SELECT historical_var_95,cvar_95,cvar_confidence_level,cvar_horizon_trading_days,
                      cvar_return_basis,cvar_observations,cvar_window,cvar_status
               FROM portfolio_risk_summary_v2(%s)""",
            (portfolio_id,),
        )
        historical_var, cvar, confidence, horizon, basis, cvar_n, window, cvar_status = cur.fetchone()
        cur.execute("SELECT adjusted_close FROM daily_market_quote WHERE security_id=%s ORDER BY trade_date", (security_id,))
        adjusted_prices = np.asarray([float(row[0]) for row in cur.fetchall()])
        independent_returns = adjusted_prices[1:] / adjusted_prices[:-1] - 1.0
        losses = -independent_returns[-252:] * float(valuation)
        threshold = np.quantile(losses, 0.95, method="linear")
        independent_cvar = max(float(historical_var), 0.0, float(losses[losses >= threshold].mean()))
        assert float(cvar) == pytest.approx(independent_cvar, abs=1e-8)
        assert confidence == 0.95 and horizon == 1 and cvar_n == window == 252
        assert basis == "current_market_value_weights_adjusted_close_daily_returns"
        assert cvar_status == "ok_inclusive_ties_at_linear_95th_percentile"
        assert float(cvar) >= float(historical_var)

        cur.execute(
            """SELECT volatility_30d, parametric_var_95, historical_var_95, sharpe_ratio,
                      calculation_status
               FROM portfolio_risk_summary(%s)""",
            (empty_id,),
        )
        empty = cur.fetchone()
        assert empty[:4] == (None, None, None, None)
        assert empty[4] == "insufficient_history_252_required"
        cur.execute("SELECT cvar_95,cvar_observations,cvar_status FROM portfolio_risk_summary_v2(%s)", (empty_id,))
        assert cur.fetchone() == (None, 0, "insufficient_history_252_required")


def test_cvar_numpy_agreement_multisecurity_and_edge_distributions(risk_connection):
    def portfolio_series(label, security_series, missing=None, cash=5000):
        portfolio_id, user_id = str(uuid.uuid4()), str(uuid.uuid4())
        security_ids = [str(uuid.uuid4()) for _ in security_series]
        missing = missing or {}
        with risk_connection.cursor() as cur:
            cur.execute("INSERT INTO portfolio(portfolio_id,user_id,portfolio_name,cash_balance) VALUES (%s,%s,%s,%s)", (portfolio_id, user_id, label, cash))
            for index, (security_id, returns) in enumerate(zip(security_ids, security_series)):
                cur.execute("INSERT INTO security_master(security_id,ticker_symbol,company_name,sector_name) VALUES (%s,%s,%s,%s)", (security_id, f"X{uuid.uuid4().hex[:10]}", label, f"Sector {index}"))
                quantity = 3 + index
                base = 1_000_000.0 + index * 250_000
                cur.execute("INSERT INTO holding(portfolio_id,security_id,quantity,average_buy_price) VALUES (%s,%s,%s,%s)", (portfolio_id, security_id, quantity, base))
                prices = [base]
                for daily_return in returns:
                    prices.append(prices[-1] * (1.0 + daily_return))
                rows = []
                for day, price in enumerate(prices):
                    if day in missing.get(index, set()):
                        continue
                    rows.append((security_id, day, round(price, 2)))
                cur.executemany(
                    "INSERT INTO daily_market_quote(security_id,trade_date,close_price,adjusted_close,volume) VALUES (%s,DATE '2024-01-01'+%s,%s,%s,1000)",
                    [(sid, day, price, price) for sid, day, price in rows],
                )
            cur.execute("REFRESH MATERIALIZED VIEW mv_daily_sector_concentration")
            cur.execute("SELECT * FROM portfolio_risk_summary_v2(%s)", (portfolio_id,))
            summary = dict(zip([d.name for d in cur.description], cur.fetchone()))
        return portfolio_id, security_ids, summary

    # Heavy tail, repeated observations, and current market value weights across
    # two real SQL holdings; the independent NumPy reference uses fetched prices.
    first = [0.004 if day not in {44, 170} else -0.42 for day in range(252)]
    second = [0.001 if day not in {75, 170} else -0.27 for day in range(252)]
    portfolio_id, security_ids, summary = portfolio_series("numpy multi-security", [first, second])
    assert summary["cvar_observations"] == 252
    with risk_connection.cursor() as cur:
        cur.execute("""SELECT h.quantity,q.close_price FROM holding h JOIN LATERAL
                       (SELECT close_price FROM daily_market_quote WHERE security_id=h.security_id ORDER BY trade_date DESC LIMIT 1) q ON TRUE
                       WHERE h.portfolio_id=%s ORDER BY h.security_id""", (portfolio_id,))
        latest_values = np.asarray([float(q) * float(price) for q, price in cur.fetchall()])
        cur.execute("SELECT portfolio_valuation FROM portfolio_risk_summary_v2(%s)", (portfolio_id,))
        valuation = float(cur.fetchone()[0])
        weights = latest_values / valuation
        returns_by_security = []
        for security_id in sorted(security_ids):
            cur.execute("SELECT adjusted_close FROM daily_market_quote WHERE security_id=%s ORDER BY trade_date", (security_id,))
            prices = np.asarray([float(row[0]) for row in cur.fetchall()])
            returns_by_security.append(prices[1:] / prices[:-1] - 1.0)
    portfolio_returns = weights @ np.asarray(returns_by_security)
    losses = -portfolio_returns * valuation
    threshold = np.quantile(losses, 0.95, method="linear")
    reference_var = max(0.0, float(summary["historical_var_95"]))
    reference_cvar = max(reference_var, float(losses[losses >= threshold].mean()))
    assert float(summary["cvar_95"]) == pytest.approx(reference_cvar, abs=0.02)
    assert float(summary["cvar_95"]) >= float(summary["historical_var_95"])

    positive_returns = [0.001] * 252
    _, _, positive = portfolio_series("all gains", [positive_returns], cash=0)
    assert positive["cvar_95"] == pytest.approx(0.0, abs=1e-8)

    constant_returns = [0.0] * 252
    _, _, constant = portfolio_series("constant", [constant_returns], cash=0)
    assert constant["cvar_95"] == pytest.approx(0.0, abs=1e-8)

    incomplete = [0.001] * 252
    _, _, missing = portfolio_series("unaligned dates", [incomplete, incomplete], missing={1: {126}}, cash=0)
    assert missing["cvar_95"] is None
    assert missing["cvar_observations"] < 252
    assert missing["cvar_status"] == "insufficient_history_252_required"
