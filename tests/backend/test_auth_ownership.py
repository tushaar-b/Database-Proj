"""Live PostgreSQL authentication, session, and cross-user access checks."""
from uuid import uuid4

import psycopg2
import pytest
from fastapi.testclient import TestClient

from backend.config import settings
from backend.auth import rate_limit_key
from backend.main import app


@pytest.fixture
def live_databases():
    opened = []
    try:
        for url in (settings.ADVISORY_DB_URL, settings.RISK_DB_URL):
            opened.append(psycopg2.connect(url, connect_timeout=3))
    except psycopg2.OperationalError as exc:
        for conn in opened:
            conn.close()
        pytest.skip(f"PostgreSQL is unavailable: {exc}")
    for conn in opened:
        conn.close()


def _cleanup_created_users(user_ids):
    if not user_ids:
        return
    risk = psycopg2.connect(settings.RISK_DB_URL)
    advisory = psycopg2.connect(settings.ADVISORY_DB_URL)
    event_ids = []
    try:
        with risk:
            with risk.cursor() as cur:
                cur.execute("SELECT event_id::text FROM risk_feedback_outbox WHERE user_id=ANY(%s::uuid[])", (user_ids,))
                event_ids = [row[0] for row in cur.fetchall()]
                cur.execute("DELETE FROM portfolio WHERE user_id=ANY(%s::uuid[])", (user_ids,))
                cur.execute("DELETE FROM risk_feedback_outbox WHERE user_id=ANY(%s::uuid[])", (user_ids,))
                cur.execute("DELETE FROM risk_feedback_state WHERE user_id=ANY(%s::uuid[])", (user_ids,))
        with advisory:
            with advisory.cursor() as cur:
                if event_ids:
                    cur.execute("DELETE FROM applied_feedback_events WHERE event_id::text=ANY(%s::text[])", (event_ids,))
                cur.execute("DELETE FROM user_profile WHERE user_id=ANY(%s::uuid[])", (user_ids,))
    finally:
        risk.close()
        advisory.close()


@pytest.fixture
def created_users():
    user_ids = []
    yield user_ids
    _cleanup_created_users(user_ids)


def register(client, label, created_users):
    response = client.post("/auth/register", json={
        "full_name": f"Phase 6 {label}",
        "email": f"phase6-{label}-{uuid4().hex}@example.test",
        "risk_tolerance_tier": "MODERATE",
        "password": "Correct-Horse-Battery-2026",
    })
    assert response.status_code == 201, response.text
    body = response.json()
    client.headers.update({"X-CSRF-Token": body["csrf_token"]})
    user_id = body["user"]["user_id"]
    created_users.append(user_id)
    return user_id


def test_password_hash_cookie_csrf_logout_and_expiry(live_databases, created_users):
    with TestClient(app, client=("127.0.0.1", 53401)) as client:
        user_id = register(client, "sessions", created_users)
        progress = client.get(f"/users/{user_id}/onboarding")
        assert progress.status_code == 200
        assert progress.json()["step"] == "income"
        updated_progress = client.put(f"/users/{user_id}/onboarding", json={"step": "expenses"})
        assert updated_progress.status_code == 200
        assert client.get(f"/users/{user_id}/onboarding").json()["step"] == "expenses"
        email = client.get(f"/users/{user_id}").json()["email"]
        duplicate = client.post("/auth/register", json={
            "full_name": "Another account", "email": email,
            "risk_tolerance_tier": "MODERATE", "password": "Correct-Horse-Battery-2026",
        })
        assert duplicate.status_code == 409
        assert email not in duplicate.text
        invalid_registration = client.post("/auth/register", json={
            "full_name": "Invalid account", "email": f"invalid-{uuid4().hex}@example.test",
            "password": "short",
        })
        assert invalid_registration.status_code == 422
        pan_registration = client.post("/auth/register", json={
            "full_name": "PAN field should be rejected", "email": f"pan-{uuid4().hex}@example.test",
            "pan_hash": "a" * 64, "password": "Correct-Horse-Battery-2026",
        })
        assert pan_registration.status_code == 422
        cookie = next(cookie for cookie in client.cookies.jar if cookie.name == "intellivest_session")
        assert cookie.has_nonstandard_attr("HttpOnly")
        assert cookie.get_nonstandard_attr("SameSite") == "lax"
        assert cookie.secure is False  # local HTTP development
        assert "pan_hash" not in client.get(f"/users/{user_id}").json()

        conn = psycopg2.connect(settings.ADVISORY_DB_URL)
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT password_hash FROM user_profile WHERE user_id=%s", (user_id,))
                stored = cur.fetchone()[0]
                assert stored.startswith("$argon2id$")
                assert "Correct-Horse-Battery-2026" not in stored
        finally:
            conn.close()

        with TestClient(app, client=("127.0.0.2", 53405)) as login_client:
            logged_in = login_client.post("/auth/login", json={"email": email, "password": "Correct-Horse-Battery-2026"})
            assert logged_in.status_code == 200, logged_in.text
            assert login_client.get("/auth/me").json()["user"]["user_id"] == user_id
            wrong_password = login_client.post("/auth/login", json={"email": email, "password": "not-the-password"})
            assert wrong_password.status_code == 401
            unknown_user = login_client.post("/auth/login", json={"email": f"unknown-{uuid4().hex}@example.test", "password": "not-the-password"})
            assert unknown_user.status_code == 401
            assert unknown_user.json()["detail"] == wrong_password.json()["detail"]
            attempt_conn = psycopg2.connect(settings.ADVISORY_DB_URL)
            try:
                with attempt_conn:
                    with attempt_conn.cursor() as cur:
                        cur.execute("DELETE FROM auth_login_attempt WHERE client_hash=%s",
                                    (rate_limit_key("127.0.0.2"),))
            finally:
                attempt_conn.close()
        assert client.post("/auth/logout").status_code == 200
        assert client.get("/auth/me").status_code == 401
        user_id = register(client, "expires", created_users)
        conn = psycopg2.connect(settings.ADVISORY_DB_URL)
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE auth_session SET expires_at=now()-interval '1 second' WHERE user_id=%s", (user_id,))
        finally:
            conn.close()
        assert client.get("/auth/me").status_code == 401
        assert client.get(f"/users/{user_id}").status_code == 401


def test_login_rate_limit(live_databases):
    address = "127.0.0.3"
    identifier_hash = rate_limit_key("limit-test@example.test")
    client_hash = rate_limit_key(address)
    try:
        with TestClient(app, client=(address, 53404)) as client:
            for _ in range(5):
                response = client.post("/auth/login", json={"email": "limit-test@example.test", "password": "invalid"})
                assert response.status_code == 401
            limited = client.post("/auth/login", json={"email": "limit-test@example.test", "password": "invalid"})
            assert limited.status_code == 429
    finally:
        conn = psycopg2.connect(settings.ADVISORY_DB_URL)
        try:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM auth_login_attempt WHERE identifier_hash=%s OR client_hash=%s", (identifier_hash, client_hash))
        finally:
            conn.close()

def test_cross_user_reads_and_mutations_are_rejected(live_databases, created_users):
    a_id = b_id = portfolio_id = None
    event_ids = []
    with TestClient(app, client=("127.0.0.1", 53402)) as a, TestClient(app, client=("127.0.0.1", 53403)) as b:
        a_id = register(a, "owner", created_users)
        b_id = register(b, "other", created_users)
        assert b.get(f"/users/{a_id}/onboarding").status_code == 404
        income = a.post(f"/cashflow/{a_id}/income", json={
            "source_category": "Salary", "gross_amount": "1000000", "frequency": "MONTHLY",
        }).json()
        expense = a.post(f"/cashflow/{a_id}/expenses", json={
            "category": "Housing", "amount": "10000", "is_mandatory": True,
        }).json()
        assert a.post(f"/cashflow/{a_id}/evaluate", json={"liquid_safety_reserve": "0"}).status_code == 200
        generated = a.post(f"/recommendations/{a_id}/generate")
        assert generated.status_code == 201, generated.text
        recs = generated.json()["recommendations"]
        assert recs

        created = a.post("/portfolios", json={"user_id": a_id, "portfolio_name": "Private portfolio", "cash_balance": "0"})
        assert created.status_code == 201, created.text
        portfolio_id = created.json()["portfolio_id"]
        risk_conn = psycopg2.connect(settings.RISK_DB_URL)
        try:
            with risk_conn.cursor() as cur:
                cur.execute("SELECT security_id,close_price FROM security_master JOIN LATERAL (SELECT close_price FROM daily_market_quote WHERE security_id=security_master.security_id ORDER BY trade_date DESC LIMIT 1) q ON TRUE LIMIT 1")
                security_id, price = cur.fetchone()
        finally:
            risk_conn.close()
        holding = a.post(f"/portfolios/{portfolio_id}/holdings", json={
            "security_id": str(security_id), "quantity": 1, "average_buy_price": str(price),
        })
        assert holding.status_code == 201, holding.text
        risk_result = a.get(f"/portfolios/{portfolio_id}/risk")
        assert risk_result.status_code == 200, risk_result.text

        risk_conn = psycopg2.connect(settings.RISK_DB_URL)
        try:
            with risk_conn:
                with risk_conn.cursor() as cur:
                    cur.execute("INSERT INTO rebalance_alert(portfolio_id,drift_magnitude_pct,breached_metric) VALUES (%s,25,'VAR_95_BREACH') RETURNING alert_id::text", (portfolio_id,))
                    alert_id = cur.fetchone()[0]
                    cur.execute("SELECT event_id::text FROM risk_feedback_outbox WHERE user_id=%s", (a_id,))
                    event_ids = [row[0] for row in cur.fetchall()]
        finally:
            risk_conn.close()

        checks = [
            b.get(f"/users/{a_id}"),
            b.get(f"/cashflow/{a_id}/income"),
            b.get(f"/cashflow/{a_id}/expenses"),
            b.get(f"/cashflow/{a_id}/summary"),
            b.get(f"/recommendations/{a_id}"),
            b.put(f"/cashflow/income/{income['income_id']}", json={"source_category": "Stolen", "gross_amount": "1", "frequency": "MONTHLY"}),
            b.delete(f"/cashflow/income/{income['income_id']}"),
            b.put(f"/cashflow/expenses/{expense['expense_id']}", json={"category": "Stolen", "amount": "1", "is_mandatory": True}),
            b.post(f"/recommendations/{a_id}/{recs[0]['rec_id']}/decision", json={"decision": "ACCEPTED"}),
            b.get(f"/portfolios/{portfolio_id}"),
            b.get(f"/portfolios/{portfolio_id}/holdings"),
            b.get(f"/portfolios/{portfolio_id}/risk"),
            b.patch(f"/portfolios/{portfolio_id}", json={"portfolio_name": "Stolen"}),
            b.delete(f"/portfolios/{portfolio_id}"),
            b.put(f"/portfolios/{portfolio_id}/holdings/{security_id}", json={"security_id": str(security_id), "quantity": 2, "average_buy_price": str(price)}),
            b.delete(f"/portfolios/{portfolio_id}/holdings/{security_id}"),
            b.get("/alerts", params={"portfolio_id": portfolio_id}),
            b.get(f"/alerts/portfolio/{portfolio_id}"),
            b.patch(f"/alerts/{alert_id}/resolve"),
            b.post(f"/rebalance/{portfolio_id}/propose"),
        ]
        assert all(response.status_code == 404 for response in checks), [
            (response.request.url, response.status_code, response.text) for response in checks if response.status_code != 404
        ]
        assert a.get(f"/alerts/portfolio/{portfolio_id}").json()[0]["alert_id"] == alert_id
