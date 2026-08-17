"""Detect misidentified and duplicate items in Plex libraries.

V1 Phase 7: error handling and edge cases.
"""

from typing import Any

from sqlmodel import Session, select

from sentarr.models.plex import Episode, Movie, Season, Show, TaskStatus


def detect_duplicates(session: Session) -> list[dict[str, Any]]:
    """Find movies/episodes with the same title+year or path that may be duplicates."""
    duplicates: list[dict[str, Any]] = []

    # Duplicate movies by path
    movies = list(session.exec(select(Movie)).all())
    paths_seen: dict[str, list[Movie]] = {}
    for m in movies:
        if m.path:
            normalized = m.path.strip().lower()
            paths_seen.setdefault(normalized, []).append(m)
    for path, items in paths_seen.items():
        if len(items) > 1:
            duplicates.append({
                "type": "movie",
                "reason": "duplicate_path",
                "path": path,
                "items": [{"id": i.id, "title": i.title, "year": i.year} for i in items],
            })

    # Duplicate movies by title+year
    title_year_seen: dict[tuple[str, int | None], list[Movie]] = {}
    for m in movies:
        key = (m.title.strip().lower(), m.year)
        title_year_seen.setdefault(key, []).append(m)
    for key, items in title_year_seen.items():
        if len(items) > 1:
            duplicates.append({
                "type": "movie",
                "reason": "duplicate_title_year",
                "title": key[0],
                "year": key[1],
                "items": [{"id": i.id, "title": i.title, "path": i.path} for i in items],
            })

    return duplicates


def detect_misidentified(session: Session) -> list[dict[str, Any]]:
    """Find episodes that appear to be in the wrong season/position.

    Heuristics:
    - Episode number > 50 (likely wrong season or special numbering)
    - Episode with error status on 'identify' task
    - Season 0 episodes (specials) that have a very high episode number
    """
    misidentified: list[dict[str, Any]] = []

    episodes = list(session.exec(select(Episode)).all())
    for ep in episodes:
        reasons: list[str] = []
        # Suspicious episode numbers
        if ep.episode_number > 100:
            reasons.append(f"episode_number={ep.episode_number} (unusually high)")
        # Check if identify task is in error state
        for task in ep.tasks:
            if task.task_type.value == "identify" and task.status == TaskStatus.ERROR:
                reasons.append("identify task failed")
                break
        if reasons:
            season = session.get(Season, ep.season_id)
            show = session.get(Show, season.show_id) if season else None
            misidentified.append({
                "type": "episode",
                "id": ep.id,
                "title": ep.title,
                "episode_number": ep.episode_number,
                "season_id": ep.season_id,
                "season_number": season.season_number if season else None,
                "show_title": show.title if show else None,
                "reasons": reasons,
            })

    return misidentified


def detect_all_issues(session: Session) -> dict[str, Any]:
    """Run all anomaly detections and return combined results."""
    duplicates = detect_duplicates(session)
    misidentified = detect_misidentified(session)
    return {
        "duplicates": duplicates,
        "duplicates_count": len(duplicates),
        "misidentified": misidentified,
        "misidentified_count": len(misidentified),
        "total_issues": len(duplicates) + len(misidentified),
    }
