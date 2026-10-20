from fastapi.testclient import TestClient

from backend.main import app


def test_non_loopback_clients_are_rejected():
    client = TestClient(app, client=("192.0.2.10", 12345))
    response = client.get("/docs")
    assert response.status_code == 403
    assert "local-only" in response.json()["detail"]
