from collections.abc import Generator
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from sentarr.config import settings

# Ensure the directory exists before SQLAlchemy tries to open the DB.
if settings.database_url.startswith("sqlite:///"):
    db_path = Path(settings.database_url.replace("sqlite:///", ""))
    db_path.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(settings.database_url, echo=settings.log_level.upper() == "DEBUG")


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
