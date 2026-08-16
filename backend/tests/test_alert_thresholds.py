"""Tests for alert threshold API and per-step configuration."""

from fastapi.testclient import TestClient

from sentarr.main import app

client = TestClient(app)


def test_get_thresholds() -> None:
    resp = client.get("/api/v1/alerts/thresholds")
    assert resp.status_code == 200
    data = resp.json()
    assert "searched" in data
    assert "downloading" in data
    assert "importing" in data
    assert "plex_overall" in data


def test_update_thresholds() -> None:
    resp = client.post(
        "/api/v1/alerts/thresholds",
        json={"searched": 90, "downloading": 45},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["searched"] == 90
    assert data["downloading"] == 45


def test_health_includes_alert_thresholds() -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "alert_thresholds" in data
    assert "active_alerts" in data
    assert "active_alerts_count" in data
    assert "arr_instances" in data
    assert "thresholds" in data


def test_health_delays_endpoint() -> None:
    resp = client.get("/api/v1/health/delays")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "count" in data
    assert "avg_delay_seconds" in data
