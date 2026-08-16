"""Tests for core API endpoints."""

from fastapi.testclient import TestClient

from sentarr.main import app

client = TestClient(app)


def test_summary_endpoint() -> None:
    resp = client.get("/api/v1/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_movies" in data
    assert "total_shows" in data
    assert "errors" in data


def test_movies_list() -> None:
    resp = client.get("/api/v1/movies")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_shows_list() -> None:
    resp = client.get("/api/v1/shows")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_search_endpoint() -> None:
    resp = client.get("/api/v1/search?q=test")
    assert resp.status_code == 200
    data = resp.json()
    assert "movies" in data or "items" in data or isinstance(data, list)


def test_logs_events() -> None:
    resp = client.get("/api/v1/logs/events")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data or isinstance(data, list)


def test_acquisition_list() -> None:
    resp = client.get("/api/v1/acquisition")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, (list, dict))


def test_alerts_list() -> None:
    resp = client.get("/api/v1/alerts")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data


def test_download_list() -> None:
    resp = client.get("/api/v1/download")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, (list, dict))


def test_subtitles_list() -> None:
    resp = client.get("/api/v1/subtitles")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


def test_indexers_list() -> None:
    resp = client.get("/api/v1/indexers")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


def test_analytics_list() -> None:
    resp = client.get("/api/v1/analytics")
    assert resp.status_code == 200


def test_servers_list() -> None:
    resp = client.get("/api/v1/servers")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data


def test_auth_keys_list() -> None:
    resp = client.get("/api/v1/auth/keys")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data


def test_health_endpoint_v2() -> None:
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200


def test_404_movie() -> None:
    resp = client.get("/api/v1/movies/99999")
    assert resp.status_code == 404


def test_404_show() -> None:
    resp = client.get("/api/v1/shows/99999")
    assert resp.status_code == 404
