from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, select

from sentarr.analytics.snapshot import take_snapshot
from sentarr.models.analytics import AnalyticsSnapshot
from sentarr.models.plex import Episode, EpisodeTask, Movie, MovieTask, TaskStatus


def test_take_snapshot() -> None:
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        movie = Movie(
            library_id=1,
            plex_rating_key="1",
            title="Test Movie",
            path="/data/movies/test.mkv",
        )
        session.add(movie)
        session.flush()
        session.add(MovieTask(movie_id=movie.id, task_type="scan", status=TaskStatus.COMPLETED))
        session.add(MovieTask(movie_id=movie.id, task_type="streams", status=TaskStatus.PENDING))

        episode = Episode(
            season_id=1,
            plex_rating_key="2",
            episode_number=1,
            title="Test Episode",
            path="/data/tv/test.mkv",
        )
        session.add(episode)
        session.flush()
        session.add(
            EpisodeTask(episode_id=episode.id, task_type="scan", status=TaskStatus.COMPLETED)
        )
        session.commit()

        now = datetime(2026, 8, 16, 12, 34, 56, tzinfo=UTC)
        take_snapshot(session, now)

        snapshots = session.exec(select(AnalyticsSnapshot)).all()
        metrics = {s.metric: s for s in snapshots}
        assert len(snapshots) == 14  # 7 metrics * 2 granularities

        assert metrics["movie_tasks_total"].value == 2
        assert metrics["movie_tasks_completed"].value == 1
        assert metrics["movie_tasks_error"].value == 0
        assert metrics["episode_tasks_total"].value == 1
        assert metrics["episode_tasks_completed"].value == 1
        assert metrics["episode_tasks_error"].value == 0
        assert metrics["log_events_total"].value == 0

        for snapshot in snapshots:
            assert (
                snapshot.bucket.startswith("hourly:2026-08-16T12")
                or snapshot.bucket == "daily:2026-08-16"
            )

        # Calling again with the same bucket updates the row (upsert)
        take_snapshot(session, now)
        snapshots = session.exec(select(AnalyticsSnapshot)).all()
        assert len(snapshots) == 14
