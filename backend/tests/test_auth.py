"""Tests for API key authentication model and middleware."""

import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, select

from sentarr.models.auth import ApiKey, ApiKeyRole


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_generate_key_format() -> None:
    key = ApiKey.generate_key()
    assert key.startswith("sk-")
    assert len(key) > 20


def test_hash_key_deterministic() -> None:
    key = "sk-test-key-123"
    h1 = ApiKey.hash_key(key)
    h2 = ApiKey.hash_key(key)
    assert h1 == h2
    assert len(h1) == 64  # SHA-256 hex


def test_hash_key_different_keys() -> None:
    h1 = ApiKey.hash_key("key-a")
    h2 = ApiKey.hash_key("key-b")
    assert h1 != h2


def test_create_api_key(session: Session) -> None:
    raw_key = ApiKey.generate_key()
    key = ApiKey(
        name="test-key",
        key_hash=ApiKey.hash_key(raw_key),
        key_prefix=raw_key[:11] + "...",
        role=ApiKeyRole.ADMIN,
    )
    session.add(key)
    session.commit()

    result = session.exec(select(ApiKey)).first()
    assert result is not None
    assert result.name == "test-key"
    assert result.role == ApiKeyRole.ADMIN
    assert result.is_active is True
    assert result.key_prefix.startswith("sk-")


def test_lookup_by_hash(session: Session) -> None:
    raw_key = ApiKey.generate_key()
    key_hash = ApiKey.hash_key(raw_key)
    session.add(
        ApiKey(
            name="lookup-test",
            key_hash=key_hash,
            key_prefix=raw_key[:11] + "...",
            role=ApiKeyRole.READONLY,
        )
    )
    session.commit()

    found = session.exec(
        select(ApiKey).where(ApiKey.key_hash == key_hash)
    ).first()
    assert found is not None
    assert found.name == "lookup-test"

    not_found = session.exec(
        select(ApiKey).where(ApiKey.key_hash == ApiKey.hash_key("wrong-key"))
    ).first()
    assert not_found is None


def test_api_keys_crud() -> None:
    """Test /api/auth/keys endpoint via TestClient."""
    from fastapi.testclient import TestClient

    from sentarr.main import app

    client = TestClient(app)

    # Create
    resp = client.post(
        "/api/v1/auth/keys",
        json={"name": "ci-test-key", "role": "admin"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "ci-test-key"
    assert data["role"] == "admin"
    assert "raw_key" in data
    raw_key = data["raw_key"]
    assert raw_key.startswith("sk-")

    # List
    resp2 = client.get("/api/v1/auth/keys")
    assert resp2.status_code == 200
    items = resp2.json()["items"]
    assert any(k["name"] == "ci-test-key" for k in items)

    # Revoke
    key_id = data["id"]
    resp3 = client.delete(f"/api/v1/auth/keys/{key_id}")
    assert resp3.status_code == 204


def test_auth_middleware_none_mode() -> None:
    """When AUTH_MODE=none, all requests pass through."""
    from fastapi.testclient import TestClient

    from sentarr.main import app

    client = TestClient(app)
    # /api/summary should be accessible without auth in none mode
    resp = client.get("/api/v1/summary")
    assert resp.status_code == 200
