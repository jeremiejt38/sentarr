from sentarr.health.score import (
    calculate_health_movie,
    calculate_health_season,
    calculate_health_show,
)
from sentarr.models.plex import (
    Episode,
    EpisodeTask,
    Movie,
    MovieTask,
    Season,
    SeasonTask,
    Show,
    ShowTask,
    TaskStatus,
)


def _movie_task(status: TaskStatus) -> MovieTask:
    return MovieTask(status=status)


def _episode_task(status: TaskStatus) -> EpisodeTask:
    return EpisodeTask(status=status)


def _season_task(status: TaskStatus) -> SeasonTask:
    return SeasonTask(status=status)


def _show_task(status: TaskStatus) -> ShowTask:
    return ShowTask(status=status)


def test_all_tasks_completed_movie() -> None:
    movie = Movie(tasks=[_movie_task(TaskStatus.COMPLETED)])
    health = calculate_health_movie(movie)
    assert health.score == 100
    assert health.completed == 1


def test_no_effective_tasks() -> None:
    movie = Movie(
        tasks=[
            _movie_task(TaskStatus.NOT_APPLICABLE),
            _movie_task(TaskStatus.NOT_APPLICABLE),
        ]
    )
    health = calculate_health_movie(movie)
    assert health.score == 100
    assert health.total == 2
    assert health.completed == 0


def test_half_completed() -> None:
    movie = Movie(
        tasks=[
            _movie_task(TaskStatus.COMPLETED),
            _movie_task(TaskStatus.PENDING),
        ]
    )
    health = calculate_health_movie(movie)
    assert health.score == 50


def test_episode_and_season() -> None:
    episode = Episode(tasks=[_episode_task(TaskStatus.COMPLETED)])
    season = Season(episodes=[episode], tasks=[_season_task(TaskStatus.PENDING)])
    health = calculate_health_season(season)
    assert health.total == 2
    assert health.completed == 1
    assert health.pending == 1


def test_show_aggregates_seasons_and_show_level_tasks() -> None:
    episode1 = Episode(tasks=[_episode_task(TaskStatus.COMPLETED)])
    episode2 = Episode(tasks=[_episode_task(TaskStatus.PENDING)])
    season = Season(episodes=[episode1, episode2])
    show = Show(
        seasons=[season],
        tasks=[
            _show_task(TaskStatus.IN_PROGRESS),
            _show_task(TaskStatus.NOT_APPLICABLE),
        ],
    )
    health = calculate_health_show(show)
    # total = 2 episodes + 2 show tasks (including NOT_APPLICABLE)
    assert health.total == 4
    assert health.completed == 1
    assert health.in_progress == 1
    assert health.pending == 1
    assert health.score == 33  # 1 completed / 3 effective tasks (truncated)


def test_not_applicable_tasks_excluded_from_denominator() -> None:
    movie = Movie(
        tasks=[
            _movie_task(TaskStatus.COMPLETED),
            _movie_task(TaskStatus.NOT_APPLICABLE),
        ]
    )
    health = calculate_health_movie(movie)
    assert health.total == 2
    assert health.completed == 1


def test_health_breakdown_fields_correct() -> None:
    movie = Movie(
        tasks=[
            _movie_task(TaskStatus.COMPLETED),
            _movie_task(TaskStatus.PENDING),
            _movie_task(TaskStatus.IN_PROGRESS),
            _movie_task(TaskStatus.ERROR),
        ]
    )
    health = calculate_health_movie(movie)
    assert health.total == 4
    assert health.completed == 1
    assert health.pending == 1
    assert health.in_progress == 1
    assert health.error == 1
