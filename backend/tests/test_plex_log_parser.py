from pathlib import Path

from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel

from sentarr.collectors.plex_log_parser import parse_log_directory
from sentarr.models.plex import Episode, LogEventRaw, Movie, Season, Show


def test_parse_log_directory(tmp_path: Path) -> None:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    log_file = tmp_path / "Plex Media Scanner Analysis.log"
    line1 = (
        "Aug 15, 2026 00:07:47.380 [22612577041152] DEBUG - "
        "Analyzing media parts for item 12345 (Test Movie): 111\n"
    )
    line2 = (
        "Aug 15, 2026 00:07:47.527 [22612586757888] DEBUG - "
        "Updating part with ID=172834 [/data/movies/test.mkv]\n"
    )
    line3 = "Aug 15, 2026 00:07:47.600 [22612586757888] DEBUG - Unknown irrelevant line\n"
    log_file.write_text(line1 + line2 + line3, encoding="utf-8")

    with Session(engine) as session:
        movie = Movie(
            library_id=1,
            plex_rating_key="12345",
            title="Test Movie",
            path="/data/movies/test.mkv",
        )
        session.add(movie)
        session.commit()

        count = parse_log_directory(session, tmp_path)
        assert count == 3

        events = session.query(LogEventRaw).all()
        assert len(events) == 3
        parsed = [e for e in events if e.parsed]
        assert len(parsed) == 2
        assert parsed[0].parsed_event_type == "analyze_started"
        assert parsed[0].correlated_to_type == "movie"

        movie_task = movie.tasks[0]
        assert movie_task.status.value == "completed"


def test_parse_log_directory_with_real_fixture() -> None:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    fixture_dir = Path(__file__).parent / "fixtures" / "sample_plex_logs"
    assert fixture_dir.exists()

    with Session(engine) as session:
        show = Show(library_id=1, plex_rating_key="99999", title="Sample Show", year=2026)
        session.add(show)
        session.flush()
        season = Season(show_id=show.id, plex_rating_key="99998", season_number=1)
        session.add(season)
        session.flush()
        episode = Episode(
            season_id=season.id,
            plex_rating_key="99380",
            episode_number=9,
            title="Sample Episode",
            path="/data/tv/Sample Show/Saison 1/Sample Show - S01E09.mkv",
        )
        movie = Movie(
            library_id=1,
            plex_rating_key="12345",
            title="Sample Movie",
            path="/data/movies/Sample Movie.mkv",
        )
        session.add(episode)
        session.add(movie)
        session.commit()

        count = parse_log_directory(session, fixture_dir)
        assert count == 8

        episode_tasks = sorted([t.task_type.value for t in episode.tasks])
        assert "scan" in episode_tasks
        assert "streams" in episode_tasks
