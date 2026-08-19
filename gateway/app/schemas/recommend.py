from pydantic import BaseModel, Field
from typing import Optional


class RecommendRequest(BaseModel):
    seed: str = Field(default="", description="种子曲目：track_id、'歌名 - 歌手' 或留空(随机)")
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
    seed: str = ""
    seed_track: Optional[RecommendTrack] = None
    msg: str = "ok"


class BatchRecommendRequest(BaseModel):
    seeds: list[str] = Field(..., description="多个种子曲目")
    top_k: int = Field(default=20, ge=1, le=100)
    channels: str = Field(default="similar,popular,same_artist,related_artist")


class BatchRecommendItem(BaseModel):
    seed: str
    seed_track: Optional[RecommendTrack] = None
    tracks: list[RecommendTrack] = []


class BatchRecommendResponse(BaseModel):
    code: int = 0
    data: list[BatchRecommendItem] = []
    total: int = 0
    msg: str = "ok"


class TrackSearchRequest(BaseModel):
    keyword: str
    limit: int = Field(default=20, ge=1, le=100)


class TrackSearchResponse(BaseModel):
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