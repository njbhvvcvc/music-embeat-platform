from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter()


class PlayEvent(BaseModel):
    track_id: str = Field(..., description="曲目 ID")
    source: str = Field(default="netease")
    duration_sec: int = Field(default=0)
    completed: bool = Field(default=False)


class FavoriteEvent(BaseModel):
    track_id: str = Field(..., description="曲目 ID")
    source: str = Field(default="netease")
    action: str = Field(default="add", pattern="^(add|remove)$")


class SkipEvent(BaseModel):
    track_id: str = Field(..., description="曲目 ID")
    source: str = Field(default="netease")
    skip_after_sec: int = Field(default=0)


class EventResponse(BaseModel):
    code: int = 0
    msg: str = "ok"


@router.post("/play", response_model=EventResponse)
async def record_play(event: PlayEvent, request: Request):
    db = request.app.state.db
    await db.record_play(event.track_id, event.source, event.duration_sec, event.completed)
    return EventResponse(code=0, msg="ok")


@router.post("/favorite", response_model=EventResponse)
async def record_favorite(event: FavoriteEvent, request: Request):
    db = request.app.state.db
    await db.record_favorite(event.track_id, event.source, event.action)
    return EventResponse(code=0, msg="ok")


@router.post("/skip", response_model=EventResponse)
async def record_skip(event: SkipEvent, request: Request):
    db = request.app.state.db
    await db.record_skip(event.track_id, event.source, event.skip_after_sec)
    return EventResponse(code=0, msg="ok")