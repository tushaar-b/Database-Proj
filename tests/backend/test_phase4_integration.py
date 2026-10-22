"""Focused live-PostgreSQL verification of the Phase 4 closed loop."""
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from uuid import uuid4

import psycopg2
import pytest
from fastapi.testclient import TestClient

from backend.config import settings
from backend.main import app


@pytest.fixture
def live_databases():
    connections = []
    try:
        for url in (settings.ADVISORY_DB_URL, settings.RISK_DB_URL):
            connections.append(psycopg2.connect(url, connect_timeout=3))
    except psycopg2.OperationalError as exc:
        for connection in connections:
            connection.close()
        pytest.skip(f"Phase 4 PostgreSQL integration databases are unavailable: {exc}")
    for connection in connections:
        connection.close()


def test_phase4_end_to_end_affordability_risk_feedback_and_rebalance(monkeypatch, live_databases):
    # Force repeatable VaR feedback while retaining real prices and SQL metrics.
    monkeypatch.setattr(settings, "RISK_VAR_LIMIT_PERCENT", 0.000001)
    monkeypatch.setattr(settings, "RISK_DAILY_VOLATILITY_LIMIT", 1.0)
    user_id = None
    portfolio_id = None
    empty_portfolio_id = None
    applied_event_ids = []

    try:
        with TestClient(app, client=("127.0.0.1", 50000)) as client:
            create = client.post("/users", json={
                "full_name": "Phase 4 disposable user",
                "email": f"phase4-{uuid4().hex}@example.test",
                "risk_tolerance_tier": "MODERATE",
            })
            assert create.status_code == 201, create.text
            user_id = create.json()["user_id"]
            assert "pan_hash" not in create.json()
            rejected_pan = client.post("/users", json={
                "full_name": "PAN field should be rejected",
                "email": f"phase4-pan-{uuid4().hex}@example.test",
                "pan_hash": "a" * 64,
                "risk_tolerance_tier": "MODERATE",
            })
            assert rejected_pan.status_code == 422
            assert client.get(f"/users/{user_id}").status_code == 200
            assert client.patch(f"/users/{user_id}", json={"full_name": "Phase 4 updated user"}).status_code == 200
            assert client.put(f"/users/{user_id}/risk-tolerance", json={"risk_tolerance_tier": "MODERATE"}).status_code == 200

            income1 = client.post(f"/cashflow/{user_id}/income", json={
                "source_category": "Salary", "gross_amount": "100000.00", "frequency": "MONTHLY",
            })
            income2 = client.post(f"/cashflow/{user_id}/income", json={
                "source_category": "Annual bonus", "gross_amount": "120000.00", "frequency": "YEARLY",
            })
            assert income1.status_code == income2.status_code == 201
            assert len(client.get(f"/cashflow/{user_id}/income").json()) == 2
            updated_income = client.put(f"/cashflow/income/{income2.json()['income_id']}", json={
                "source_category": "Annual bonus", "gross_amount": "120000.00", "frequency": "YEARLY",
            })
            assert updated_income.status_code == 200
            temporary_income = client.post(f"/cashflow/{user_id}/income", json={
                "source_category": "Temporary", "gross_amount": "1.00", "frequency": "MONTHLY",
            })
            assert client.delete(f"/cashflow/income/{temporary_income.json()['income_id']}").status_code == 204
            assert client.post(f"/cashflow/{user_id}/expenses", json={
                "category": "Rent", "amount": "35000.00", "is_mandatory": True, "recurrence_interval": "MONTHLY",
            }).status_code == 201
            assert len(client.get(f"/cashflow/{user_id}/expenses").json()) == 1
            assert client.post(f"/cashflow/{user_id}/expenses", json={
                "category": "Annual insurance", "amount": "120000.00", "is_mandatory": True, "recurrence_interval": "YEARLY",
            }).status_code == 201
            assert client.post(f"/cashflow/{user_id}/expenses", json={
                "category": "Dining", "amount": "12000.00", "is_mandatory": False, "recurrence_interval": "MONTHLY",
            }).status_code == 201
            unsupported = client.post(f"/cashflow/{user_id}/expenses", json={
                "category": "Unsupported", "amount": "100.00", "is_mandatory": True, "recurrence_interval": "WEEKLY",
            })
            assert unsupported.status_code == 422
            evaluation = client.post(f"/cashflow/{user_id}/evaluate", json={"liquid_safety_reserve": "10000.00"})
            assert evaluation.status_code == 200, evaluation.text
            cashflow = evaluation.json()
            assert Decimal(str(cashflow["monthly_income"])) == Decimal("110000.00")
            assert Decimal(str(cashflow["monthly_mandatory_expenses"])) == Decimal("45000.00")
            assert Decimal(str(cashflow["monthly_discretionary_expenses"])) == Decimal("12000.00")
            assert Decimal(str(cashflow["computed_surplus"])) == Decimal("65000.00")
            assert Decimal(str(cashflow["investable_buffer"])) == Decimal("55000.00")
            summary = client.get(f"/cashflow/{user_id}/summary")
            assert summary.status_code == 200, summary.text
            assert Decimal(str(summary.json()["liquid_safety_reserve"])) == Decimal("10000.00")
            assert Decimal(str(summary.json()["investable_buffer"])) == Decimal("55000.00")

            initial = client.post(f"/recommendations/{user_id}/generate")
            assert initial.status_code == 201, initial.text
            first_batch = initial.json()
            assert Decimal(str(first_batch["total_recommended_cost"])) <= Decimal("55000.00")
            assert sum(item["shares"] for item in first_batch["recommendations"]) > 0
            assert client.get(f"/recommendations/{user_id}").status_code == 200
            # Acceptance records intent only. Verify it creates no ledger operation.
            before_ledger = _ledger_count()
            for index, recommendation in enumerate(first_batch["recommendations"]):
                decision = "ACCEPTED" if index == 0 else "REJECTED"
                response = client.post(
                    f"/recommendations/{user_id}/{recommendation['rec_id']}/decision",
                    json={"decision": decision},
                )
                assert response.status_code == 200, response.text
                if decision == "ACCEPTED":
                    assert response.json()["trade_execution"].startswith("not_executed")
            assert _ledger_count() == before_ledger

            # Use a real, currently quoted constituent; only fixture rows are inserted.
            risk_conn = psycopg2.connect(settings.RISK_DB_URL)
            try:
                with risk_conn.cursor() as cur:
                    cur.execute("SELECT security_id,close_price FROM security_master JOIN LATERAL (SELECT close_price FROM daily_market_quote WHERE security_id=security_master.security_id ORDER BY trade_date DESC LIMIT 1) q ON TRUE WHERE ticker_symbol='RELIANCE'")
                    security_id, latest_price = cur.fetchone()
                    cur.execute("SELECT security_id,close_price FROM security_master JOIN LATERAL (SELECT close_price FROM daily_market_quote WHERE security_id=security_master.security_id ORDER BY trade_date DESC LIMIT 1) q ON TRUE WHERE ticker_symbol='INFY'")
                    second_security_id, second_price = cur.fetchone()
            finally:
                risk_conn.close()
            created_portfolio = client.post("/portfolios", json={
                "user_id": user_id, "portfolio_name": "PHASE4_DISPOSABLE_TEST",
                "cash_balance": str(latest_price), "target_hhi_limit": "0.250",
            })
            assert created_portfolio.status_code == 201, created_portfolio.text
            portfolio_id = created_portfolio.json()["portfolio_id"]
            imported_holding = client.post(f"/portfolios/{portfolio_id}/holdings", json={
                "security_id": str(security_id), "quantity": 1, "average_buy_price": str(latest_price),
            })
            assert imported_holding.status_code == 201, imported_holding.text
            assert imported_holding.json()["position_source"] == "imported"
            assert client.put(f"/portfolios/{portfolio_id}/holdings/{security_id}", json={
                "security_id": str(security_id), "quantity": 1, "average_buy_price": str(latest_price),
            }).status_code == 200
            assert len(client.get("/portfolios/securities", params={"q": "INFY"}).json()) >= 1
            temporary_holding = client.post(f"/portfolios/{portfolio_id}/holdings", json={
                "security_id": str(second_security_id), "quantity": 1, "average_buy_price": str(second_price),
            })
            assert temporary_holding.status_code == 201, temporary_holding.text
            assert client.delete(f"/portfolios/{portfolio_id}/holdings/{second_security_id}").status_code == 204
            assert client.patch(f"/portfolios/{portfolio_id}", json={"portfolio_name": "Phase 4 verification"}).status_code == 200
            empty_portfolio = client.post("/portfolios", json={
                "user_id": user_id, "portfolio_name": "PHASE4_EMPTY_DELETE_TEST", "cash_balance": "0.00",
            })
            assert empty_portfolio.status_code == 201, empty_portfolio.text
            empty_portfolio_id = empty_portfolio.json()["portfolio_id"]
            assert client.delete(f"/portfolios/{empty_portfolio_id}").status_code == 204
            empty_portfolio_id = None
            assert len(client.get("/portfolios", params={"user_id": user_id}).json()) == 1

            risk = client.get(f"/portfolios/{portfolio_id}/risk")
            assert risk.status_code == 200, risk.text
            metrics = risk.json()
            for metric in ("volatility_30d", "parametric_var_95", "historical_var_95", "sharpe_ratio", "sector_hhi"):
                assert metrics[metric] is not None, (metric, metrics)
            assert metrics["historical_observations"] == 252
            assert metrics["calculation_status"] == "ok"

            first_alert_eval = client.post(f"/alerts/evaluate/{portfolio_id}")
            second_alert_eval = client.post(f"/alerts/evaluate/{portfolio_id}")
            assert first_alert_eval.status_code == second_alert_eval.status_code == 200
            alert_rows = client.get(f"/alerts/portfolio/{portfolio_id}?unresolved=true")
            assert alert_rows.status_code == 200
            open_metrics = [row["breached_metric"] for row in alert_rows.json()]
            assert "VAR_95_BREACH" in open_metrics
            assert "SECTOR_HHI_EXCEEDED" in open_metrics
            assert len(open_metrics) == len(set(open_metrics))
            proposal = client.post(f"/rebalance/{portfolio_id}/propose")
            assert proposal.status_code == 200, proposal.text
            assert proposal.json()["simulation_only"] is True
            assert proposal.json()["operations"]

            # Feedback was delivered before the next generation; it halves the moderate cap
            # and blocks the currently concentrated sector.
            tightened = client.post(f"/recommendations/{user_id}/generate")
            assert tightened.status_code == 201, tightened.text
            tightened_body = tightened.json()
            assert Decimal(str(tightened_body["policy_multiplier"])) == Decimal("0.5")
            assert "Energy" in tightened_body["blocked_sectors"]
            assert Decimal(str(tightened_body["allocation_budget"])) == Decimal("13750.00")
            assert "VaR" in tightened_body["reason"]
            assert all(item["explanation"] and "VaR" in item["explanation"] for item in tightened_body["recommendations"])
            assert all(item["stock_ticker"] != "RELIANCE" for item in tightened_body["recommendations"])
            hhi_alert = next(row for row in alert_rows.json() if row["breached_metric"] == "SECTOR_HHI_EXCEEDED")
            resolved = client.patch(f"/alerts/{hhi_alert['alert_id']}/resolve")
            assert resolved.status_code == 200, resolved.text

            # Concurrent identical BUYs debit only once; an oversell race permits one request only.
            security_id_text = str(security_id)
            key = str(uuid4())
            buy_body = {"idempotency_key": key, "approved": True,
                        "operations": [{"security_id": security_id_text, "side": "BUY", "units": 1}]}
            with ThreadPoolExecutor(max_workers=2) as executor:
                responses = list(executor.map(lambda _: client.post(f"/rebalance/{portfolio_id}/execute", json=buy_body), range(2)))
            assert all(response.status_code == 200 for response in responses), [r.text for r in responses]
            assert sum(not response.json()["duplicate_execution"] for response in responses) == 1
            assert sum(response.json()["duplicate_execution"] for response in responses) == 1
            oversell_body = lambda: {"idempotency_key": str(uuid4()), "approved": True,
                                     "operations": [{"security_id": security_id_text, "side": "SELL", "units": 2}]}
            with ThreadPoolExecutor(max_workers=2) as executor:
                oversells = list(executor.map(lambda body: client.post(f"/rebalance/{portfolio_id}/execute", json=body), [oversell_body(), oversell_body()]))
            assert sorted(response.status_code for response in oversells) == [200, 409]
            portfolio = client.get(f"/portfolios/{portfolio_id}")
            holdings = client.get(f"/portfolios/{portfolio_id}/holdings")
            assert portfolio.status_code == holdings.status_code == 200
            assert Decimal(str(portfolio.json()["cash_balance"])) >= 0
            assert all(row["quantity"] >= 0 for row in holdings.json())
            assert client.put(f"/portfolios/{portfolio_id}/holdings/{security_id}", json={
                "security_id": str(security_id), "quantity": 1, "average_buy_price": str(latest_price),
            }).status_code == 409
            assert client.delete(f"/portfolios/{portfolio_id}").status_code == 409
            ledger_conn = psycopg2.connect(settings.RISK_DB_URL)
            try:
                with ledger_conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*),COALESCE(SUM(units),0) FROM transaction_ledger WHERE portfolio_id=%s", (portfolio_id,))
                    assert cur.fetchone() == (2, 3)
            finally:
                ledger_conn.close()
            advisory_check = psycopg2.connect(settings.ADVISORY_DB_URL)
            try:
                with advisory_check.cursor() as cur:
                    cur.execute("SELECT capacity_multiplier,blocked_sectors FROM recommendation_policy WHERE user_id=%s", (user_id,))
                    cleared_policy = cur.fetchone()
                    assert Decimal(cleared_policy[0]) == Decimal("1.0000")
                    assert cleared_policy[1] == []
            finally:
                advisory_check.close()

            # Swagger/OpenAPI routes are part of the deployed surface.
            assert client.get("/docs").status_code == 200
            assert client.get("/openapi.json").status_code == 200
    finally:
        if user_id:
            risk_conn = psycopg2.connect(settings.RISK_DB_URL)
            advisory_conn = psycopg2.connect(settings.ADVISORY_DB_URL)
            try:
                with risk_conn:
                    with risk_conn.cursor() as cur:
                        cur.execute("SELECT event_id FROM risk_feedback_outbox WHERE user_id=%s", (user_id,))
                        applied_event_ids = [str(row[0]) for row in cur.fetchall()]
                        if portfolio_id or empty_portfolio_id:
                            cur.execute("DELETE FROM portfolio WHERE portfolio_id=ANY(%s::uuid[])", ([value for value in (portfolio_id, empty_portfolio_id) if value],))
                        cur.execute("DELETE FROM risk_feedback_outbox WHERE user_id=%s", (user_id,))
                        cur.execute("DELETE FROM risk_feedback_state WHERE user_id=%s", (user_id,))
                with advisory_conn:
                    with advisory_conn.cursor() as cur:
                        if applied_event_ids:
                            cur.execute("DELETE FROM applied_feedback_events WHERE event_id::text=ANY(%s::text[])", (applied_event_ids,))
                        cur.execute("DELETE FROM user_profile WHERE user_id=%s", (user_id,))
            finally:
                risk_conn.close()
                advisory_conn.close()


def _ledger_count():
    conn = psycopg2.connect(settings.RISK_DB_URL)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM transaction_ledger WHERE portfolio_id IN (SELECT portfolio_id FROM portfolio WHERE portfolio_name='PHASE4_DISPOSABLE_TEST')")
            return cur.fetchone()[0]
    finally:
        conn.close()
