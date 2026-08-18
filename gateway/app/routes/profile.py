from fastapi import APIRouter, HTTPException

from app.clients.profile import profile_client
from app.schemas.profile import (
    PlayEvent,
    FavoriteEvent,
    SkipEvent,
    EventResponse,
    SeedsResponse,
)

router = APIRouter()


@router.post("/events/play", response_model=EventResponse)
async def record_play(event: PlayEvent):
    try:
        await profile_client.record_play(
            track_id=event.track_id,
            source=event.source,
            duration_sec=event.duration_sec,
            completed=event.completed,
        )
        return EventResponse(code=0, msg="ok")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"记录播放事件失败: {str(e)}")


@router.post("/events/favorite", response_model=EventResponse)
async def record_favorite(event: FavoriteEvent):
    try:
        await profile_client.record_favorite(
            track_id=event.track_id,
            source=event.source,
            action=event.action,
        )
        return EventResponse(code=0, msg="ok")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"记录收藏事件失败: {str(e)}")


@router.post("/events/skip", response_model=EventResponse)
async def record_skip(event: SkipEvent):
    try:
        await profile_client.record_skip(
            track_id=event.track_id,
            source=event.source,
            skip_after_sec=event.skip_after_sec,
        )
        return EventResponse(code=0, msg="ok")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"记录跳过事件失败: {str(e)}")


@router.get("/seeds", response_model=SeedsResponse)
async def get_seeds():
    try:
        seeds = await profile_client.get_seeds()
        return SeedsResponse(code=0, data=seeds, msg="ok")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"获取种子曲失败: {str(e)}")