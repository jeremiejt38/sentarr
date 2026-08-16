import logging
import os
from datetime import UTC, datetime

from fastapi import HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlmodel import Session, select
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from sentarr.config import settings
from sentarr.db import engine
from sentarr.models.auth import ApiKey

logger = logging.getLogger(__name__)

security = HTTPBasic(auto_error=False)

PUBLIC_PATHS = frozenset(
    {"/health", "/metrics", "/docs", "/openapi.json", "/api/auth/login"}
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

        # forms / basic fallback
        auth = request.headers.get("Authorization")
        if not auth:
            raise HTTPException(status_code=401, detail="Missing credentials")
        return await call_next(request)


def verify_credentials(credentials: HTTPBasicCredentials) -> bool:
    expected_user = os.environ.get("SENTARR_USERNAME", "admin")
    expected_pass = os.environ.get("SENTARR_PASSWORD", "admin")
    return credentials.username == expected_user and credentials.password == expected_pass
