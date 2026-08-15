import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from sentarr.api import acquisition, alerts, health, logs, metrics, movies, search, shows, summary
from sentarr.api import websocket as ws_module
from sentarr.auth import AuthMiddleware
from sentarr.config import settings
from sentarr.db import init_db
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
app.include_router(ws_module.router, prefix="/ws", tags=["websocket"])


@app.on_event("startup")
async def startup() -> None:
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized.")
    start_scheduler()


@app.get("/health")
async def health_check() -> dict[str, Any]:
    return {"status": "ok", "version": "0.1.0"}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
