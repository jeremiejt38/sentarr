from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from sentarr.db import get_session
from sentarr.models.auth import ApiKey, ApiKeyRole

router = APIRouter()


class ApiKeyCreate(BaseModel):
    name: str
    role: ApiKeyRole = ApiKeyRole.READONLY


class ApiKeyResponse(BaseModel):
    id: int
    name: str
    key_prefix: str
    role: ApiKeyRole
    is_active: bool
    last_used_at: str | None = None
    created_at: str | None = None


class ApiKeyCreated(ApiKeyResponse):
    raw_key: str  # Only returned on creation


def _key_to_dict(key: ApiKey) -> dict[str, Any]:
    return {
        "id": key.id,
        "name": key.name,
        "key_prefix": key.key_prefix,
        "role": key.role,
        "is_active": key.is_active,
        "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
        "created_at": key.created_at.isoformat() if key.created_at else None,
    }


@router.get("/keys")
async def list_api_keys(
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    rows = session.exec(select(ApiKey)).all()
    return {"items": [_key_to_dict(k) for k in rows], "total": len(rows)}


@router.post("/keys", status_code=201)
async def create_api_key(
    body: ApiKeyCreate,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    raw_key = ApiKey.generate_key()
    key = ApiKey(
        name=body.name,
        key_hash=ApiKey.hash_key(raw_key),
        key_prefix=raw_key[:11] + "...",
        role=body.role,
    )
    session.add(key)
    session.commit()
    session.refresh(key)
    result = _key_to_dict(key)
    result["raw_key"] = raw_key
    return result


@router.delete("/keys/{key_id}", status_code=204)
async def revoke_api_key(
    key_id: int,
    session: Session = Depends(get_session),
) -> None:
    key = session.get(ApiKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    key.is_active = False
    session.add(key)
    session.commit()
