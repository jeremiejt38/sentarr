import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from sentarr.collectors.download_client import TorrentInfo
from sentarr.collectors.download_sync import update_download_progress
from sentarr.models.arr import AcquisitionItem, ArrClientType, ArrInstance


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_update_download_progress_matches_by_hash(session: Session, monkeypatch) -> None:
    instance = ArrInstance(
        name="radarr-test",
        client_type=ArrClientType.RADARR,
        base_url="http://radarr",
        api_key="key",
    )
    session.add(instance)
    session.flush()

    item = AcquisitionItem(
        source_id=instance.id,
        external_id="123",
        client_type=ArrClientType.RADARR,
        title="Test Movie",
        status="downloading",
        download_id="ABC123",
    )
    session.add(item)
    session.commit()

    torrent = TorrentInfo(
        name="Test.Movie.2024",
        hash="abc123",
        progress=0.425,
        status="downloading",
        download_speed=1_000_000,
        eta_seconds=3600,
        save_path="/downloads",
        labels=None,
    )
    monkeypatch.setattr(
        "sentarr.collectors.download_sync.list_all_torrents", lambda: [torrent]
    )

    matches = update_download_progress(session)

    assert len(matches) == 1
    assert matches[0]["progress_percent"] == 42.5
    refreshed = session.get(AcquisitionItem, item.id)
    assert refreshed is not None
    assert refreshed.download_progress == 42


def test_update_download_progress_falls_back_to_title(session: Session, monkeypatch) -> None:
    instance = ArrInstance(
        name="radarr-test",
        client_type=ArrClientType.RADARR,
        base_url="http://radarr",
        api_key="key",
    )
    session.add(instance)
    session.flush()

    item = AcquisitionItem(
        source_id=instance.id,
        external_id="456",
        client_type=ArrClientType.RADARR,
        title="Test Movie",
        status="downloading",
    )
    session.add(item)
    session.commit()

    torrent = TorrentInfo(
        name="Test.Movie.2024.1080p",
        hash="def456",
        progress=0.88,
        status="downloading",
        download_speed=2_000_000,
        eta_seconds=600,
        save_path="/downloads",
        labels=None,
    )
    monkeypatch.setattr(
        "sentarr.collectors.download_sync.list_all_torrents", lambda: [torrent]
    )

    matches = update_download_progress(session)

    assert len(matches) == 1
    assert matches[0]["progress_percent"] == 88.0
    refreshed = session.get(AcquisitionItem, item.id)
    assert refreshed is not None
    assert refreshed.download_progress == 88


def test_update_download_progress_clears_on_no_match(session: Session, monkeypatch) -> None:
    instance = ArrInstance(
        name="radarr-test",
        client_type=ArrClientType.RADARR,
        base_url="http://radarr",
        api_key="key",
    )
    session.add(instance)
    session.flush()

    item = AcquisitionItem(
        source_id=instance.id,
        external_id="789",
        client_type=ArrClientType.RADARR,
        title="Unrelated Title",
        status="downloading",
        download_progress=50,
    )
    session.add(item)
    session.commit()

    monkeypatch.setattr("sentarr.collectors.download_sync.list_all_torrents", lambda: [])

    matches = update_download_progress(session)

    assert matches == []
    refreshed = session.get(AcquisitionItem, item.id)
    assert refreshed is not None
    assert refreshed.download_progress is None
