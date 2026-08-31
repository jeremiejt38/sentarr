from collections.abc import Generator
from pathlib import Path
from typing import Any

from alembic.config import Config as AlembicConfig
from sqlalchemy import Engine, event
from sqlmodel import Session, SQLModel, create_engine

from alembic import command
from sentarr.config import settings


def make_engine(database_url: str, echo: bool = False) -> Engine:
    """Create a SQLAlchemy engine, with SQLite concurrency safeguards."""
    kwargs: dict[str, Any] = {"echo": echo}
    if database_url.startswith("sqlite:///"):
        kwargs["connect_args"] = {"check_same_thread": False}
        kwargs["pool_pre_ping"] = True

    engine = create_engine(database_url, **kwargs)

    if database_url.startswith("sqlite:///"):

        @event.listens_for(engine, "connect")
        def _configure_sqlite(dbapi_conn: Any, _connection_record: Any) -> None:
            dbapi_conn.execute("PRAGMA journal_mode=WAL")
            dbapi_conn.execute("PRAGMA busy_timeout=30000")

    return engine


# Ensure the directory exists before SQLAlchemy tries to open the DB.
if settings.database_url.startswith("sqlite:///"):
    db_path = Path(settings.database_url.replace("sqlite:///", ""))
    db_path.parent.mkdir(parents=True, exist_ok=True)

engine = make_engine(settings.database_url, echo=settings.log_level.upper() == "DEBUG")


def _alembic_ini_path() -> Path:
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "alembic.ini"


def run_migrations() -> None:
    """Apply Alembic migrations to the current database."""
    alembic_cfg = AlembicConfig(str(_alembic_ini_path()))
    command.upgrade(alembic_cfg, "head")


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
