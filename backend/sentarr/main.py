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
    auth,
    download,
    health,
    indexers,
    logs,
    metrics,
    movies,
    notifications,
    search,
    servers,
    shows,
    subtitles,
    summary,
    users,
)
from sentarr.api import (
    plugins as plugins_api,
)
from sentarr.api import websocket as ws_module
from sentarr.auth import AuthMiddleware
from sentarr.config import settings
from sentarr.db import engine, run_migrations
from sentarr.plugins.manager import plugin_manager
from sentarr.tasks.scheduler import start_scheduler

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sentarr",
    version="0.5.0",
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

app.include_router(movies.router, prefix="/api/v1/movies", tags=["movies"])
app.include_router(shows.router, prefix="/api/v1/shows", tags=["shows"])
app.include_router(summary.router, prefix="/api/v1/summary", tags=["summary"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(logs.router, prefix="/api/v1/logs", tags=["logs"])
app.include_router(acquisition.router, prefix="/api/v1/acquisition", tags=["acquisition"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(subtitles.router, prefix="/api/v1/subtitles", tags=["subtitles"])
app.include_router(indexers.router, prefix="/api/v1/indexers", tags=["indexers"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(download.router, prefix="/api/v1/download", tags=["download"])
app.include_router(servers.router, prefix="/api/v1/servers", tags=["servers"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(plugins_api.router, prefix="/api/v1/plugins", tags=["plugins"])
app.include_router(ws_module.router, prefix="/ws", tags=["websocket"])


@app.get("/health")
async def health_check() -> dict[str, Any]:
    return {"status": "ok", "version": "0.5.0"}


static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
else:

    @app.get("/")
    async def root() -> dict[str, Any]:
        return {"status": "ok", "version": "0.5.0", "message": "Frontend static dir not found"}


def _bootstrap_admin_api_key() -> None:
    """Create the initial admin API key from env if not already present."""
    from sqlmodel import Session, select

    from sentarr.models.auth import ApiKey, ApiKeyRole

    raw_key = settings.sentarr_admin_api_key
    if not raw_key:
        return
    key_hash = ApiKey.hash_key(raw_key)
    with Session(engine) as session:
        existing = session.exec(
            select(ApiKey).where(ApiKey.key_hash == key_hash)
        ).first()
        if not existing:
            session.add(
                ApiKey(
                    name="admin-bootstrap",
                    key_hash=key_hash,
                    key_prefix=raw_key[:11] + "..." if len(raw_key) > 11 else raw_key,
                    role=ApiKeyRole.ADMIN,
                )
            )
            session.commit()
            logger.info("Bootstrap admin API key created")


@app.on_event("startup")
async def startup() -> None:
    try:
        logger.info("Running database migrations...")
        run_migrations()
        logger.info("Database migrations completed.")
        _bootstrap_admin_api_key()
        # Plugin system
        discovered = plugin_manager.discover()
        if discovered:
            logger.info("Discovered %d plugin(s): %s", len(discovered), ", ".join(discovered))
        plugin_manager.activate_all(app)
        start_scheduler()
        logger.info("Startup complete.")
    except Exception:
        logger.exception("Startup failed")
        raise


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
