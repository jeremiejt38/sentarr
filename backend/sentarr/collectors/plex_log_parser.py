import hashlib
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from sentarr.config import settings
from sentarr.models.plex import (
    Episode,
    EpisodeTask,
    EpisodeTaskType,
    LogEventRaw,
    Movie,
    MovieTask,
    MovieTaskType,
    TaskStatus,
)

logger = logging.getLogger(__name__)

LOG_LINE_RE = re.compile(
    r"^(?P<month>[A-Za-z]{3})\s+(?P<day>\d{1,2}),\s+"
    r"(?P<year>\d{4})\s+(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
    r"\.(?P<micro>\d{3})\s+\[\d+\]\s+(?P<level>\w+)\s+-\s+(?P<message>.*)$"
)

PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"Analyzing media parts for item\s+(?P<item_id>\d+)"), "analyze_started"),
    (
        re.compile(r"\[ID\s+(?P<part_id>\d+)\]\s+Media part analysis:\s+(?P<path>.+)"),
        "analyze_part",
    ),
    (
        re.compile(r"Updating part with ID=(?P<part_id>\d+)\s+\[(?P<path>[^\]]+)\]"),
        "analyze_part_updated",
    ),
    (
        re.compile(r"Plex Media Scanner\s+--analyze-deeply\s+--item\s+(?P<item_id>\d+)"),
        "deep_analysis_started",
    ),
    (re.compile(r"Exception analyzing media file\s+'(?P<path>[^']+)'"), "deep_analysis_error"),
    (
        re.compile(
            r"Plex Media Scanner\s+--generate\s+--chapter-thumbs-only\s+--item\s+(?P<item_id>\d+)"
        ),
        "chapter_thumbs_started",
    ),
    (
        re.compile(r"Created chapter thumbnail for metadata item\s+(?P<item_id>\d+)"),
        "chapter_thumbs_created",
    ),
    (
        re.compile(r"Plex Media Scanner\s+--generate\s+--credits-only\s+--item\s+(?P<item_id>\d+)"),
        "credits_started",
    ),
    (re.compile(r"Plex Media Scanner\s+--match\s+.*--item\s+(?P<item_id>\d+)"), "matcher_started"),
    (
        re.compile(
            r"Matcher:\s+found\s+(?P<count>\d+)\s+auxiliary files for Season\s+(?P<season>\d+)"
        ),
        "matcher_season",
    ),
    (re.compile(r"Scanning\s+(?P<library>[^\s]+)\s+using"), "library_scan_started"),
    (re.compile(r"Scanner:\s+Processing directory\s+(?P<path>[^\s(]+)"), "scan_directory"),
]


def _parse_timestamp(line: str) -> datetime | None:
    match = LOG_LINE_RE.match(line)
    if not match:
        return None
    try:
        dt = datetime.strptime(
            f"{match.group('year')} {match.group('month')} {match.group('day')} "
            f"{match.group('hour')}:{match.group('minute')}:{match.group('second')}"
            f".{match.group('micro')}",
            "%Y %b %d %H:%M:%S.%f",
        )
        return dt.replace(tzinfo=UTC)
    except ValueError:
        return None


def _match_event(message: str) -> tuple[str | None, dict[str, Any]]:
    for pattern, event_type in PATTERNS:
        match = pattern.search(message)
        if match:
            return event_type, match.groupdict()
    return None, {}


def _resolve_correlation(session: Session, data: dict[str, Any]) -> tuple[str | None, int | None]:
    path = data.get("path")
    item_id = data.get("item_id")

    if path:
        movie = session.exec(select(Movie).where(Movie.path == path)).first()
        if movie:
            return "movie", movie.id
        episode = session.exec(select(Episode).where(Episode.path == path)).first()
        if episode:
            return "episode", episode.id

    if item_id:
        movie = session.exec(select(Movie).where(Movie.plex_rating_key == item_id)).first()
        if movie:
            return "movie", movie.id
        episode = session.exec(select(Episode).where(Episode.plex_rating_key == item_id)).first()
        if episode:
            return "episode", episode.id

    return None, None


def _movie_task_type(event_type: str) -> MovieTaskType | None:
    mapping: dict[str, MovieTaskType] = {
        "analyze_started": MovieTaskType.SCAN,
        "analyze_part": MovieTaskType.STREAMS,
        "analyze_part_updated": MovieTaskType.SCAN,
        "deep_analysis_started": MovieTaskType.BIF,
        "chapter_thumbs_started": MovieTaskType.CHAPTER_MARKERS,
        "chapter_thumbs_created": MovieTaskType.CHAPTER_MARKERS,
        "credits_started": MovieTaskType.INTRO_MARKERS,
        "matcher_started": MovieTaskType.IDENTIFY,
        "library_scan_started": MovieTaskType.SCAN,
        "scan_directory": MovieTaskType.SCAN,
    }
    return mapping.get(event_type)


def _episode_task_type(event_type: str) -> EpisodeTaskType | None:
    mapping: dict[str, EpisodeTaskType] = {
        "analyze_started": EpisodeTaskType.SCAN,
        "analyze_part": EpisodeTaskType.STREAMS,
        "analyze_part_updated": EpisodeTaskType.SCAN,
        "deep_analysis_started": EpisodeTaskType.BIF,
        "chapter_thumbs_started": EpisodeTaskType.CHAPTER_MARKERS,
        "chapter_thumbs_created": EpisodeTaskType.CHAPTER_MARKERS,
        "credits_started": EpisodeTaskType.INTRO_MARKERS,
        "matcher_started": EpisodeTaskType.IDENTIFY,
        "library_scan_started": EpisodeTaskType.SCAN,
        "scan_directory": EpisodeTaskType.SCAN,
    }
    return mapping.get(event_type)


def _update_task(task: MovieTask | EpisodeTask, event_type: str, timestamp: datetime) -> None:
    if task.status in (TaskStatus.PENDING, TaskStatus.NOT_APPLICABLE):
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = timestamp
    if "created" in event_type or "updated" in event_type:
        task.status = TaskStatus.COMPLETED
        task.completed_at = timestamp
    if "error" in event_type:
        task.status = TaskStatus.ERROR
        task.completed_at = timestamp
        task.error_message = event_type
    task.updated_at = timestamp


def _update_movie_task(
    session: Session, movie_id: int, event_type: str, timestamp: datetime
) -> None:
    task_type = _movie_task_type(event_type)
    if not task_type:
        return
    task = session.exec(
        select(MovieTask).where(MovieTask.movie_id == movie_id, MovieTask.task_type == task_type)
    ).first()
    if not task:
        task = MovieTask(movie_id=movie_id, task_type=task_type)
        session.add(task)
    _update_task(task, event_type, timestamp)


def _update_episode_task(
    session: Session, episode_id: int, event_type: str, timestamp: datetime
) -> None:
    task_type = _episode_task_type(event_type)
    if not task_type:
        return
    task = session.exec(
        select(EpisodeTask).where(
            EpisodeTask.episode_id == episode_id,
            EpisodeTask.task_type == task_type,
        )
    ).first()
    if not task:
        task = EpisodeTask(episode_id=episode_id, task_type=task_type)
        session.add(task)
    _update_task(task, event_type, timestamp)


def _update_task_status(
    session: Session,
    target_type: str,
    target_id: int,
    event_type: str,
    timestamp: datetime,
) -> None:
    if target_type == "movie":
        _update_movie_task(session, target_id, event_type, timestamp)
    elif target_type == "episode":
        _update_episode_task(session, target_id, event_type, timestamp)


def _already_seen(session: Session, line_hash: str) -> bool:
    existing = session.exec(select(LogEventRaw).where(LogEventRaw.line_hash == line_hash)).first()
    return existing is not None


def parse_log_directory(session: Session, log_dir: Path | None = None) -> int:
    if log_dir:
        base_dir = Path(log_dir)
    else:
        configured = Path(settings.plex_log_path)
        base_dir = configured.parent if configured.is_file() else configured
    if not base_dir.exists():
        logger.warning("Log directory not found: %s", base_dir)
        return 0

    log_files = sorted(
        p
        for p in base_dir.iterdir()
        if p.is_file() and "Plex Media" in p.name and p.suffix in (".log", "")
    )

    inserted = 0
    for log_file in log_files:
        try:
            inserted += _parse_file(session, log_file)
        except Exception:
            logger.exception("Failed to parse log file: %s", log_file)
    session.commit()
    return inserted


def _parse_file(session: Session, log_file: Path) -> int:
    inserted = 0
    event_type: str | None = None
    data: dict[str, Any] = {}
    with log_file.open("r", encoding="utf-8", errors="replace") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n")
            line_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()
            if _already_seen(session, line_hash):
                continue

            timestamp = _parse_timestamp(line)
            event_type = None
            data = {}
            if timestamp:
                event_type, data = _match_event(line)

            correlated_type: str | None = None
            correlated_id: int | None = None
            if event_type and timestamp:
                correlated_type, correlated_id = _resolve_correlation(session, data)
                if correlated_type and correlated_id:
                    _update_task_status(
                        session,
                        correlated_type,
                        correlated_id,
                        event_type,
                        timestamp,
                    )

            session.add(
                LogEventRaw(
                    timestamp=timestamp,
                    raw_line=line,
                    line_hash=line_hash,
                    parsed=event_type is not None,
                    parsed_event_type=event_type,
                    correlated_to_type=correlated_type,
                    correlated_to_id=correlated_id,
                )
            )
            inserted += 1

            if inserted % 1000 == 0:
                session.flush()
    return inserted
