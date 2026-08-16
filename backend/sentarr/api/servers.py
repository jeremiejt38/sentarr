from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from sentarr.db import get_session
from sentarr.models.plex import PlexServerConfig

router = APIRouter()


class PlexServerCreate(BaseModel):
    name: str
    base_url: str
    token: str
    log_path: str | None = None


class PlexServerUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    token: str | None = None
    log_path: str | None = None
    is_active: bool | None = None


def _server_to_dict(srv: PlexServerConfig) -> dict[str, Any]:
    return {
        "id": srv.id,
        "name": srv.name,
        "base_url": srv.base_url,
        "log_path": srv.log_path,
        "is_active": srv.is_active,
        "created_at": srv.created_at.isoformat() if srv.created_at else None,
        "updated_at": srv.updated_at.isoformat() if srv.updated_at else None,
    }


@router.get("")
async def list_servers(
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    rows = session.exec(select(PlexServerConfig)).all()
    return {"items": [_server_to_dict(s) for s in rows], "total": len(rows)}


@router.post("", status_code=201)
async def create_server(
    body: PlexServerCreate,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    existing = session.exec(
        select(PlexServerConfig).where(PlexServerConfig.name == body.name)
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Server '{body.name}' already exists")
    srv = PlexServerConfig(
        name=body.name,
        base_url=body.base_url,
        token=body.token,
        log_path=body.log_path,
    )
    session.add(srv)
    session.commit()
    session.refresh(srv)
    return _server_to_dict(srv)


@router.get("/{server_id}")
async def get_server(
    server_id: int,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    srv = session.get(PlexServerConfig, server_id)
    if not srv:
        raise HTTPException(status_code=404, detail="Server not found")
    return _server_to_dict(srv)


@router.patch("/{server_id}")
async def update_server(
    server_id: int,
    body: PlexServerUpdate,
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    srv = session.get(PlexServerConfig, server_id)
    if not srv:
        raise HTTPException(status_code=404, detail="Server not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(srv, field, value)
    session.add(srv)
    session.commit()
    session.refresh(srv)
    return _server_to_dict(srv)


@router.delete("/{server_id}", status_code=204)
async def delete_server(
    server_id: int,
    session: Session = Depends(get_session),
) -> None:
    srv = session.get(PlexServerConfig, server_id)
    if not srv:
        raise HTTPException(status_code=404, detail="Server not found")
    session.delete(srv)
    session.commit()
