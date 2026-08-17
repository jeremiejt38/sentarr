"""Tests for the anomaly detection module (duplicates, misidentified items)."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from sentarr.db import get_session
from sentarr.health.anomalies import detect_all_issues, detect_duplicates, detect_misidentified
from sentarr.main import app
from sentarr.models.plex import (
    Episode,
    EpisodeTask,
    EpisodeTaskType,
    Library,
    LibraryType,
    Movie,
    Season,
    Show,
    TaskStatus,
)

client = TestClient(app)


def _get_db_session() -> Session:
    """Get the test DB session via FastAPI dependency."""
    return next(get_session())


def test_detect_no_issues_empty_db():
    """Empty DB should report no issues."""
    session = _get_db_session()
    results = detect_all_issues(session)
    assert results["total_issues"] == 0
    assert results["duplicates_count"] == 0
    assert results["misidentified_count"] == 0


def test_detect_duplicate_movies_by_path():
    """Two movies with the same path should be flagged as duplicates."""
    session = _get_db_session()

    lib = Library(plex_library_key="dup1", name="DupTest", type=LibraryType.MOVIE)
    session.add(lib)
    session.flush()

    m1 = Movie(
        library_id=lib.id,
        plex_rating_key="dup100",
        title="Inception",
        year=2010,
        path="/movies/inception.mkv",
    )
    m2 = Movie(
        library_id=lib.id,
        plex_rating_key="dup101",
        title="Inception (copy)",
        year=2010,
        path="/movies/inception.mkv",
    )
    session.add_all([m1, m2])
    session.commit()

    try:
        results = detect_duplicates(session)
        path_dups = [r for r in results if r["reason"] == "duplicate_path"]
        assert len(path_dups) >= 1
        assert len(path_dups[0]["items"]) == 2
    finally:
        session.delete(m1)
        session.delete(m2)
        session.delete(lib)
        session.commit()


def test_detect_duplicate_movies_by_title_year():
    """Two movies with the same title+year should be flagged."""
    session = _get_db_session()

    lib = Library(plex_library_key="dup2", name="DupTest2", type=LibraryType.MOVIE)
    session.add(lib)
    session.flush()

    m1 = Movie(
        library_id=lib.id,
        plex_rating_key="dup200",
        title="The Matrix",
        year=1999,
        path="/movies/matrix-1.mkv",
    )
    m2 = Movie(
        library_id=lib.id,
        plex_rating_key="dup201",
        title="The Matrix",
        year=1999,
        path="/movies/matrix-2.mkv",
    )
    session.add_all([m1, m2])
    session.commit()

    try:
        results = detect_duplicates(session)
        title_dups = [r for r in results if r["reason"] == "duplicate_title_year"]
        assert len(title_dups) >= 1
        assert len(title_dups[0]["items"]) == 2
    finally:
        session.delete(m1)
        session.delete(m2)
        session.delete(lib)
        session.commit()


def test_detect_misidentified_high_episode_number():
    """An episode with number > 100 should be flagged."""
    session = _get_db_session()

    lib = Library(plex_library_key="mis1", name="MisTest", type=LibraryType.SHOW)
    session.add(lib)
    session.flush()

    show = Show(library_id=lib.id, plex_rating_key="mis300", title="Test Show", year=2020)
    session.add(show)
    session.flush()

    season = Season(show_id=show.id, plex_rating_key="mis301", season_number=1)
    session.add(season)
    session.flush()

    ep = Episode(
        season_id=season.id,
        plex_rating_key="mis302",
        episode_number=999,
        title="Weird Episode",
    )
    session.add(ep)
    session.commit()

    try:
        results = detect_misidentified(session)
        assert len(results) >= 1
        match = [r for r in results if r["episode_number"] == 999]
        assert len(match) == 1
    finally:
        session.delete(ep)
        session.delete(season)
        session.delete(show)
        session.delete(lib)
        session.commit()


def test_detect_misidentified_identify_error():
    """An episode with a failed identify task should be flagged."""
    session = _get_db_session()

    lib = Library(plex_library_key="mis2", name="MisTest2", type=LibraryType.SHOW)
    session.add(lib)
    session.flush()

    show = Show(library_id=lib.id, plex_rating_key="mis400", title="Show2", year=2021)
    session.add(show)
    session.flush()

    season = Season(show_id=show.id, plex_rating_key="mis401", season_number=1)
    session.add(season)
    session.flush()

    ep = Episode(
        season_id=season.id,
        plex_rating_key="mis402",
        episode_number=5,
        title="Normal Episode",
    )
    session.add(ep)
    session.flush()

    task = EpisodeTask(
        episode_id=ep.id,
        task_type=EpisodeTaskType.IDENTIFY,
        status=TaskStatus.ERROR,
        error_message="Failed to identify",
    )
    session.add(task)
    session.commit()

    try:
        results = detect_misidentified(session)
        match = [r for r in results if r.get("id") == ep.id]
        assert len(match) >= 1
        assert "identify task failed" in match[0]["reasons"]
    finally:
        session.delete(task)
        session.delete(ep)
        session.delete(season)
        session.delete(show)
        session.delete(lib)
        session.commit()


def test_health_issues_endpoint():
    """The /api/v1/health/issues endpoint should return the anomaly report."""
    resp = client.get("/api/v1/health/issues")
    assert resp.status_code == 200
    data = resp.json()
    assert "duplicates" in data
    assert "misidentified" in data
    assert "total_issues" in data
