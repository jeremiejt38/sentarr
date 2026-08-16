import enum
import hashlib
import secrets
from datetime import UTC, datetime

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


def now_utc() -> datetime:
    return datetime.now(UTC)


class ApiKeyRole(enum.StrEnum):
    ADMIN = "admin"
    READONLY = "readonly"


class ApiKey(SQLModel, table=True):
    __tablename__ = "api_keys"
    __table_args__ = (
        Index("ix_api_keys_key_hash", "key_hash", unique=True),
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    key_hash: str  # SHA-256 hash of the key
    key_prefix: str  # First 8 chars for display: "sk-xxxx..."
    role: ApiKeyRole = Field(default=ApiKeyRole.READONLY)
    is_active: bool = Field(default=True)
    last_used_at: datetime | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=now_utc)

    @staticmethod
    def hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_key() -> str:
        return f"sk-{secrets.token_urlsafe(32)}"
