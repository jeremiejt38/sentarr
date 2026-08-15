import os

from fastapi import HTTPException, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from sentarr.config import settings

security = HTTPBasic(auto_error=False)


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if settings.auth_mode == "none":
            return await call_next(request)

        if request.url.path in ("/health", "/metrics", "/docs", "/openapi.json"):
            return await call_next(request)

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
