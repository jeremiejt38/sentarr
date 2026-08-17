"""User model for multi-user authentication."""

import enum
from datetime import UTC, datetime

import bcrypt
from sqlmodel import Field, SQLModel


class UserRole(enum.StrEnum):
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"


def _now_utc() -> datetime:
    return datetime.now(UTC)


class User(SQLModel, table=True):
    """Multi-user account model (similar to Radarr/Sonarr)."""

    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, sa_column_kwargs={"unique": True})
    email: str | None = Field(default=None, nullable=True)
    password_hash: str
    role: UserRole = Field(default=UserRole.USER)
    is_active: bool = Field(default=True)
    last_login_at: datetime | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=_now_utc)
    updated_at: datetime = Field(default_factory=_now_utc)

    @staticmethod
    def hash_password(plain: str) -> str:
        """Hash a plaintext password with bcrypt."""
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        """Verify a plaintext password against a bcrypt hash."""
        return bcrypt.checkpw(plain.encode(), hashed.encode())
