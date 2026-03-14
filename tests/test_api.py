from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from backend.api.main import app, state


client = TestClient(app)


def auth_header() -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"username": "admin", "password": "admin123"})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ingestion_requires_api_key() -> None:
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "auth-service",
        "level": "ERROR",
        "message": "Login failed",
        "metadata": {"user_id": "U123"},
    }
    response = client.post("/api/v1/ingest", json=payload)
    assert response.status_code == 401


def test_ingest_and_search() -> None:
    payload = {
        "timestamp": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
        "service": "payment-service",
        "level": "ERROR",
        "message": "Charge failed",
        "metadata": {"order_id": "ORD-1"},
    }
    response = client.post("/api/v1/ingest", json=payload, headers={"X-API-Key": "demo-ingest-key"})
    assert response.status_code == 202

    # allow background worker loop to process queue
    import time

    time.sleep(0.1)

    search = client.get(
        "/api/v1/logs/search",
        params={"service": "payment-service", "level": "ERROR"},
        headers=auth_header(),
    )
    assert search.status_code == 200
    assert search.json()["total"] >= 1


def test_alerts_endpoint_requires_role() -> None:
    login = client.post("/api/v1/auth/login", json={"username": "viewer", "password": "viewer123"})
    token = login.json()["access_token"]
    response = client.get("/api/v1/alerts", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_alert_rule_triggers() -> None:
    # Lower threshold for deterministic test
    state.alert_manager.error_threshold = 2
    now = datetime.now(timezone.utc)
    for i in range(3):
        client.post(
            "/api/v1/ingest",
            json={
                "timestamp": now.isoformat(),
                "service": "auth-service",
                "level": "ERROR",
                "message": f"error-{i}",
                "metadata": {},
            },
            headers={"X-API-Key": "demo-ingest-key"},
        )

    import time

    time.sleep(0.2)

    response = client.get("/api/v1/alerts", headers=auth_header())
    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1
