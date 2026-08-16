import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler  # type: ignore[import-untyped]
from sqlmodel import Session

from sentarr.alerts.engine import evaluate_alerts
from sentarr.analytics.snapshot import purge_old_log_events, take_snapshot
from sentarr.api.websocket import broadcast
from sentarr.collectors.arr_sync import sync_acquisition
from sentarr.collectors.bazarr_sync import sync_bazarr
from sentarr.collectors.plex_api import sync_libraries
from sentarr.collectors.plex_log_parser import parse_log_directory
from sentarr.config import settings
from sentarr.db import engine

logger = logging.getLogger(__name__)


async def sync_plex_job() -> None:
    logger.info("Starting scheduled Plex sync")
    try:
        with Session(engine) as session:
            sync_libraries(session)
        await broadcast({"type": "sync_complete", "source": "plex"})
    except Exception:
        logger.exception("Plex sync failed")


async def parse_plex_logs_job() -> None:
    logger.info("Starting scheduled Plex log parsing")
    try:
        with Session(engine) as session:
            count = parse_log_directory(session)
            logger.info("Parsed %s log lines", count)
        if count:
            await broadcast({"type": "sync_complete", "source": "plex_logs", "count": count})
    except Exception:
        logger.exception("Plex log parsing failed")


async def sync_arr_job() -> None:
    logger.info("Starting scheduled *arr sync")
    try:
        with Session(engine) as session:
            sync_acquisition(session)
            logger.info("*arr sync completed")
        await broadcast({"type": "sync_complete", "source": "arr"})
    except Exception:
        logger.exception("*arr sync failed")


async def evaluate_alerts_job() -> None:
    logger.info("Starting alert evaluation")
    try:
        with Session(engine) as session:
            count = len(evaluate_alerts(session))
            logger.info("Created %s alerts", count)
        if count:
            await broadcast({"type": "alerts_created", "count": count})
    except Exception:
        logger.exception("Alert evaluation failed")


async def sync_bazarr_job() -> None:
    logger.info("Starting Bazarr sync")
    try:
        with Session(engine) as session:
            count = sync_bazarr(session)
            logger.info("Synced %s subtitle tracks", count)
    except Exception:
        logger.exception("Bazarr sync failed")


async def analytics_snapshot_job() -> None:
    logger.info("Starting analytics snapshot")
    try:
        with Session(engine) as session:
            take_snapshot(session)
            purge_old_log_events(session)
    except Exception:
        logger.exception("Analytics snapshot failed")


def start_scheduler() -> AsyncIOScheduler:
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
    scheduler.add_job(
        lambda: asyncio.create_task(sync_arr_job()),
        "interval",
        seconds=settings.arr_poll_interval_seconds,
        id="arr_sync",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: asyncio.create_task(evaluate_alerts_job()),
        "interval",
        seconds=settings.arr_poll_interval_seconds,
        id="alert_engine",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: asyncio.create_task(sync_bazarr_job()),
        "interval",
        seconds=settings.poll_interval_seconds,
        id="bazarr_sync",
        replace_existing=True,
    )
    scheduler.add_job(
        lambda: asyncio.create_task(analytics_snapshot_job()),
        "interval",
        minutes=60,
        id="analytics_snapshot",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started with interval %ss", settings.poll_interval_seconds)
    return scheduler
