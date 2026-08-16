"""Tests for PlexServerConfig model and /api/servers endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, select

from sentarr.models.plex import Library, LibraryType, PlexServerConfig


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_create_plex_server(session: Session) -> None:
    srv = PlexServerConfig(
        name="main",
        base_url="http://plex:32400",
        token="test-token",
        log_path="/var/log/plex",
    )
    session.add(srv)
    session.commit()
    result = session.exec(select(PlexServerConfig)).first()
    assert result is not None
    assert result.name == "main"
    assert result.base_url == "http://plex:32400"
    assert result.is_active is True


def test_plex_server_library_relationship(session: Session) -> None:
    srv = PlexServerConfig(
        name="test-srv",
        base_url="http://plex:32400",
        token="tok",
    )
    session.add(srv)
    session.flush()

    lib = Library(
        plex_server_id=srv.id,
        plex_library_key="1",
        name="Films",
        type=LibraryType.MOVIE,
    )
    session.add(lib)
    session.commit()

    server = session.exec(select(PlexServerConfig)).first()
    assert server is not None
    assert len(server.libraries) == 1
    assert server.libraries[0].name == "Films"


def test_multiple_servers(session: Session) -> None:
    for i in range(3):
        session.add(
            PlexServerConfig(
                name=f"server-{i}",
                base_url=f"http://plex-{i}:32400",
                token=f"token-{i}",
            )
        )
    session.commit()
    servers = session.exec(select(PlexServerConfig)).all()
    assert len(servers) == 3


def test_api_list_servers() -> None:
    """Test the /api/servers endpoint returns a list."""
    from sentarr.main import app

    client = TestClient(app)
    response = client.get("/api/v1/servers")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data


def test_api_create_and_get_server() -> None:
    """Test creating a server via API and retrieving it."""
    import uuid

    from sentarr.main import app

    client = TestClient(app)
    unique_name = f"api-test-{uuid.uuid4().hex[:8]}"
    # Create
    resp = client.post(
        "/api/v1/servers",
        json={
            "name": unique_name,
            "base_url": "http://plex-test:32400",
            "token": "test-token-123",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == unique_name
    assert data["is_active"] is True
    # Token should NOT be in the response
    assert "token" not in data

    # Get
    server_id = data["id"]
    resp2 = client.get(f"/api/v1/servers/{server_id}")
    assert resp2.status_code == 200
    assert resp2.json()["name"] == unique_name
