"""User management and authentication endpoints."""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from jose import JWTError, jwt  # type: ignore[import-untyped]
from pydantic import BaseModel
from sqlmodel import Session, select

from sentarr.config import settings
from sentarr.db import get_session
from sentarr.models.user import User, UserRole

router = APIRouter()

_ALGORITHM = "HS256"
_TOKEN_EXPIRE_HOURS = 24


class UserCreate(BaseModel):
    username: str
    password: str
    email: str | None = None
    role: UserRole = UserRole.USER


class UserUpdate(BaseModel):
    email: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    id: int
    username: str
    email: str | None
    role: UserRole
    is_active: bool
    last_login_at: str | None = None
    created_at: str | None = None


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    user: UserResponse


def _create_token(user_id: int, username: str, role: str) -> str:
    expire = datetime.now(UTC) + timedelta(hours=_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "exp": expire,
    }
    return str(jwt.encode(payload, settings.secret_key, algorithm=_ALGORITHM))


def get_current_user(request: Request) -> dict[str, Any]:
    """Extract and validate JWT token from Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = auth_header[7:]
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[_ALGORITHM])
        return {
            "user_id": int(payload["sub"]),
            "username": payload["username"],
            "role": payload["role"],
        }
    except (JWTError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc


def require_admin(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    """Dependency that requires admin role."""
    if current_user["role"] != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id or 0,
        username=user.username,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.post("/login")
async def login(body: LoginRequest, session: Session = Depends(get_session)) -> LoginResponse:
    """Authenticate a user and return a JWT token."""
    user = session.exec(select(User).where(User.username == body.username)).first()
    if not user or not User.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")
    user.last_login_at = datetime.now(UTC)
    session.add(user)
    session.commit()
    token = _create_token(user.id or 0, user.username, user.role.value)
    return LoginResponse(token=token, user=_user_response(user))


@router.get("")
async def list_users(
    session: Session = Depends(get_session),
    _admin: dict[str, Any] = Depends(require_admin),
) -> list[UserResponse]:
    """List all users (admin only)."""
    users = session.exec(select(User)).all()
    return [_user_response(u) for u in users]


@router.post("")
async def create_user(
    body: UserCreate,
    session: Session = Depends(get_session),
    _admin: dict[str, Any] = Depends(require_admin),
) -> UserResponse:
    """Create a new user (admin only)."""
    existing = session.exec(select(User).where(User.username == body.username)).first()
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")
    user = User(
        username=body.username,
        email=body.email,
        password_hash=User.hash_password(body.password),
        role=body.role,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return _user_response(user)


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    session: Session = Depends(get_session),
    _current: dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """Get a specific user."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_response(user)


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    body: UserUpdate,
    session: Session = Depends(get_session),
    _admin: dict[str, Any] = Depends(require_admin),
) -> UserResponse:
    """Update a user (admin only)."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.email is not None:
        user.email = body.email
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    user.updated_at = datetime.now(UTC)
    session.add(user)
    session.commit()
    session.refresh(user)
    return _user_response(user)


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: int,
    session: Session = Depends(get_session),
    _admin: dict[str, Any] = Depends(require_admin),
) -> dict[str, str]:
    """Deactivate a user (admin only)."""
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    user.updated_at = datetime.now(UTC)
    session.add(user)
    session.commit()
    return {"status": "deactivated"}
