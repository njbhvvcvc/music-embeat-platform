from pydantic import BaseModel, Field
from typing import Optional


class RecommendRequest(BaseModel):
    seed: str = Field(..., description="种子曲目：track_id 或 '歌名 - 歌手'")
    top_k: int = Field(default=20, ge=1, le=100)
    channels: str = Field(default="similar,popular,same_artist,related_artist")


class RecommendTrack(BaseModel):
    track_id: str
    title: str
    artist: str
    album: str = ""
    score: float = 0.0
    channel: str = ""
    pic_url: str = ""


class RecommendResponse(BaseModel):
    code: int = 0
    data: list[RecommendTrack] = []
    total: int = 0
    msg: str = "ok"


class VectorRequest(BaseModel):
    track_id: str = Field(..., description="曲目 ID")


class VectorResponse(BaseModel):
    code: int = 0
    data: list[float] = []
    msg: str = "ok"