from pydantic import BaseModel, Field
from typing import Optional


class PlayEvent(BaseModel):
    track_id: str = Field(..., description="曲目 ID")
    source: str = Field(default="netease", description="音乐源")
    duration_sec: int = Field(default=0, description="听歌时长秒")
    completed: bool = Field(default=False, description="是否听完")


class FavoriteEvent(BaseModel):
    track_id: str = Field(..., description="曲目 ID")
    source: str = Field(default="netease")
    action: str = Field(default="add", pattern="^(add|remove)$")


class SkipEvent(BaseModel):
    track_id: str = Field(..., description="曲目 ID")
    source: str = Field(default="netease")
    skip_after_sec: int = Field(default=0, description="跳过前听了多久")


class EventResponse(BaseModel):
    code: int = 0
    msg: str = "ok"


class SeedsResponse(BaseModel):
    code: int = 0
    data: list[str] = []
    msg: str = "ok"


class ProfileResponse(BaseModel):
    code: int = 0
    data: dict = {}
    msg: str = "ok"