import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, select

from sentarr.models.plex import (
    Episode,
    EpisodeTask,
    EpisodeTaskType,
    Library,
    LibraryType,
    Movie,
    MovieTask,
    MovieTaskType,
    Season,
    Show,
    TaskStatus,
)


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_create_library(session: Session) -> None:
    library = Library(plex_library_key="1", name="Films", type=LibraryType.MOVIE)
    session.add(library)
    session.commit()
    result = session.exec(select(Library)).first()
    assert result is not None
    assert result.name == "Films"


def test_create_movie_with_tasks(session: Session) -> None:
    library = Library(plex_library_key="1", name="Films", type=LibraryType.MOVIE)
    session.add(library)
    session.flush()

    movie = Movie(
        library_id=library.id,
        plex_rating_key="100",
        title="Test Movie",
        overall_status=TaskStatus.PENDING,
    )
    session.add(movie)
    session.flush()

    task = MovieTask(movie_id=movie.id, task_type=MovieTaskType.OVERALL)
    session.add(task)
    session.commit()

    result = session.exec(select(Movie)).first()
    assert result is not None
    assert result.title == "Test Movie"
    assert len(result.tasks) == 1


def test_create_show_hierarchy(session: Session) -> None:
    library = Library(plex_library_key="2", name="Séries", type=LibraryType.SHOW)
    session.add(library)
    session.flush()

    show = Show(
        library_id=library.id,
        plex_rating_key="200",
        title="Test Show",
        overall_status=TaskStatus.PENDING,
    )
    session.add(show)
    session.flush()

    season = Season(show_id=show.id, plex_rating_key="201", season_number=1)
    session.add(season)
    session.flush()

    episode = Episode(
        season_id=season.id,
        plex_rating_key="202",
        episode_number=1,
        title="Pilot",
        overall_status=TaskStatus.COMPLETED,
        progress_percent=100,
    )
    session.add(episode)
    session.flush()

    task = EpisodeTask(episode_id=episode.id, task_type=EpisodeTaskType.OVERALL)
    session.add(task)
    session.commit()

    result = session.exec(select(Show)).first()
    assert result is not None
    assert result.title == "Test Show"
    assert len(result.seasons) == 1
    assert len(result.seasons[0].episodes) == 1
    assert len(result.seasons[0].episodes[0].tasks) == 1
