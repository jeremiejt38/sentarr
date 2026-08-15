import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]
from sqlmodel import Session

from sentarr.collectors.plex_api import sync_libraries
from sentarr.collectors.plex_log_parser import parse_log_directory
from sentarr.config import settings
from sentarr.db import engine, init_db

logger = logging.getLogger(__name__)


async def sync_plex_job() -> None:
    logger.info("Starting scheduled Plex sync")
    try:
        with Session(engine) as session:
            sync_libraries(session)
    except Exception:
        logger.exception("Plex sync failed")


async def parse_plex_logs_job() -> None:
    logger.info("Starting scheduled Plex log parsing")
    try:
        with Session(engine) as session:
            count = parse_log_directory(session)
            logger.info("Parsed %s log lines", count)
    except Exception:
        logger.exception("Plex log parsing failed")


def start_scheduler() -> AsyncIOScheduler:
    init_db()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        lambda: asyncio.create_task(sync_plex_job()),
        "interval",
        seconds=settings.poll_interval_seconds,
        id="plex_sync",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: asyncio.create_task(parse_plex_logs_job()),
        "interval",
        seconds=settings.poll_interval_seconds,
        id="plex_log_parse",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started with interval %ss", settings.poll_interval_seconds)
    return scheduler
