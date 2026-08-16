from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from sentarr.db import get_session
from sentarr.models.subtitles import SubtitleTrack

router = APIRouter()


@router.get("")
async def list_subtitles(
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    rows = session.exec(select(SubtitleTrack)).all()
    return {
        "items": [
            {
                "id": track.id,
                "episode_id": track.episode_id,
                "language": track.language,
                "hearing_impaired": track.hearing_impaired,
                "forced": track.forced,
                "path": track.path,
                "provider": track.provider,
                "source": track.source_name,
                "downloaded_at": track.downloaded_at,
            }
            for track in rows
        ],
        "total": len(rows),
    }
