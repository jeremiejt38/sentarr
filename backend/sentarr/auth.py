import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from jose import JWTError, jwt  # type: ignore[import-untyped]
from sqlmodel import Session, select
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from sentarr.config import settings
from sentarr.db import engine
from sentarr.models.auth import ApiKey
from sentarr.models.user import User

logger = logging.getLogger(__name__)

security = HTTPBasic(auto_error=False)

PUBLIC_PATHS = frozenset(
    {
        "/health",
        "/metrics",
        "/docs",
        "/openapi.json",
        "/api/v1/users/login",
        "/api/v1/auth/config",
    }
)


def _extract_api_key(request: Request) -> str | None:
    """Extract API key from Authorization header (Bearer) or X-Api-Key header."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:].strip()
    return request.headers.get("X-Api-Key") or request.query_params.get("apikey")


def _verify_api_key(raw_key: str) -> ApiKey | None:
    """Look up an API key by hash and return it if active."""
    key_hash = ApiKey.hash_key(raw_key)
    with Session(engine) as session:
        api_key = session.exec(
            select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)  # noqa: E712
        ).first()
        if api_key:
            api_key.last_used_at = datetime.now(UTC)
            session.add(api_key)
            session.commit()
            session.refresh(api_key)
        return api_key


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if settings.auth_mode == "none":
            return await call_next(request)

        if request.url.path in PUBLIC_PATHS or request.url.path.startswith("/static"):
            return await call_next(request)

        # API key authentication (api_key mode or always accepted as fallback)
        raw_key = _extract_api_key(request)
        if raw_key:
            api_key = _verify_api_key(raw_key)
            if api_key:
                request.state.user = api_key.name
                request.state.role = api_key.role
                return await call_next(request)

        if settings.auth_mode == "api_key":
            raise HTTPException(status_code=401, detail="Invalid or missing API key")

        if settings.auth_mode == "external":
            user = request.headers.get("X-Remote-User")
            if not user:
                raise HTTPException(status_code=401, detail="Missing X-Remote-User header")
            request.state.user = user
            return await call_next(request)

        # forms / JWT
        if settings.auth_mode == "forms":
            payload = _extract_jwt(request)
            if not payload:
                raise HTTPException(status_code=401, detail="Missing or invalid JWT")
            request.state.user = payload["username"]
            request.state.role = payload["role"]
            return await call_next(request)

        # basic
        credentials = await security(request)
        if credentials and _verify_user(credentials):
            request.state.user = credentials.username
            request.state.role = _get_user_role(credentials.username)
            return await call_next(request)

        raise HTTPException(status_code=401, detail="Invalid credentials")


def _extract_jwt(request: Request) -> dict[str, Any] | None:
    """Extract and validate a JWT from Authorization header or cookie."""
    auth = request.headers.get("Authorization", "")
    token = None
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
    if not token:
        token = request.cookies.get("sentarr_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return {
            "user_id": payload["sub"],
            "username": payload["username"],
            "role": payload["role"],
        }
    except (JWTError, KeyError):
        return None


def _verify_user(credentials: HTTPBasicCredentials) -> bool:
    with Session(engine) as session:
        user = session.exec(
            select(User).where(User.username == credentials.username)
        ).first()
        if not user or not user.is_active:
            return False
        return User.verify_password(credentials.password, user.password_hash)


def _get_user_role(username: str) -> str:
    with Session(engine) as session:
        user = session.exec(select(User).where(User.username == username)).first()
        return user.role.value if user else "readonly"
