import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from sentarr.api import (
    acquisition,
    alerts,
    analytics,
    download,
    health,
    indexers,
    logs,
    metrics,
    movies,
    notifications,
    search,
    shows,
    subtitles,
    summary,
)
from sentarr.api import websocket as ws_module
from sentarr.auth import AuthMiddleware
from sentarr.config import settings
from sentarr.db import run_migrations
from sentarr.tasks.scheduler import start_scheduler

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sentarr",
    version="0.1.0",
    description=(
        "Dashboard self-hosted de suivi des tâches Plex et de la chaîne d'acquisition *arr."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)

app.include_router(movies.router, prefix="/api/movies", tags=["movies"])
app.include_router(shows.router, prefix="/api/shows", tags=["shows"])
app.include_router(summary.router, prefix="/api/summary", tags=["summary"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(acquisition.router, prefix="/api/acquisition", tags=["acquisition"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(subtitles.router, prefix="/api/subtitles", tags=["subtitles"])
app.include_router(indexers.router, prefix="/api/indexers", tags=["indexers"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(download.router, prefix="/api/download", tags=["download"])
app.include_router(ws_module.router, prefix="/ws", tags=["websocket"])


@app.get("/health")
async def health_check() -> dict[str, Any]:
    return {"status": "ok", "version": "0.3.0"}


static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:

    @app.get("/")
    async def root() -> dict[str, Any]:
        return {"status": "ok", "version": "0.3.0", "message": "Frontend static dir not found"}


@app.on_event("startup")
async def startup() -> None:
    logger.info("Running database migrations...")
    run_migrations()
    logger.info("Database migrations completed.")
    start_scheduler()


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
