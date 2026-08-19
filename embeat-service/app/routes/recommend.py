import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


class RecommendRequest(BaseModel):
    seed: str = Field(default="", description="种子曲目 ID 或 '歌名 - 歌手'，留空则随机抽种子")
    top_k: int = Field(default=20, ge=1, le=100)
    channels: str = Field(default="similar,popular,same_artist,related_artist")


class RecommendTrack(BaseModel):
    track_id: str
    title: str = ""
    artist: str = ""
    album: str = ""
    score: float = 0.0
    channel: str = ""
    pic_url: str = ""


class RecommendResponse(BaseModel):
    code: int = 0
    data: list[RecommendTrack] = []
    total: int = 0
    seed: str = ""
    seed_track: RecommendTrack | None = None
    msg: str = "ok"


class BatchRecommendRequest(BaseModel):
    seeds: list[str] = Field(..., description="多个种子曲目")
    top_k: int = Field(default=20, ge=1, le=100)
    channels: str = Field(default="similar,popular,same_artist,related_artist")


class BatchRecommendItem(BaseModel):
    seed: str
    seed_track: RecommendTrack | None = None
    tracks: list[RecommendTrack] = []


class BatchRecommendResponse(BaseModel):
    code: int = 0
    data: list[BatchRecommendItem] = []
    total: int = 0
    msg: str = "ok"


class TrackSearchRequest(BaseModel):
    keyword: str = Field(..., description="歌名或歌手关键字")
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


def _to_track(t: dict) -> RecommendTrack:
    return RecommendTrack(
        track_id=t.get("track_id", ""),
        title=t.get("title", ""),
        artist=t.get("artist", ""),
        album=t.get("album", ""),
        score=float(t.get("score", 0)),
        channel=t.get("channel", ""),
    )


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest, request: Request):
    qdrant = request.app.state.qdrant
    model = request.app.state.model_loader
    from app.core.recall import RecallEngine

    engine = RecallEngine(qdrant, model)
    if not qdrant.is_ready:
        raise HTTPException(status_code=503, detail="Qdrant 未就绪，请先导入向量库")

    try:
        seed_track = await engine.resolve_seed(req.seed)
        if not seed_track:
            return RecommendResponse(
                code=1, data=[], total=0, seed=req.seed, msg="种子曲目未找到"
            )
        tracks = await engine.recommend(req.seed, req.top_k, req.channels)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐失败: {str(e)}")

    items = [_to_track(t) for t in tracks]
    return RecommendResponse(
        code=0,
        data=items,
        total=len(items),
        seed=req.seed,
        seed_track=_to_track(seed_track),
        msg="ok",
    )


@router.post("/recommend/batch", response_model=BatchRecommendResponse)
async def recommend_batch(req: BatchRecommendRequest, request: Request):
    qdrant = request.app.state.qdrant
    model = request.app.state.model_loader
    from app.core.recall import RecallEngine

    engine = RecallEngine(qdrant, model)
    if not qdrant.is_ready:
        raise HTTPException(status_code=503, detail="Qdrant 未就绪，请先导入向量库")

    items: list[BatchRecommendItem] = []
    for seed in req.seeds:
        try:
            seed_track = await engine.resolve_seed(seed)
            if not seed_track:
                items.append(BatchRecommendItem(seed=seed, tracks=[]))
                continue
            tracks = await engine.recommend(seed, req.top_k, req.channels)
            items.append(
                BatchRecommendItem(
                    seed=seed,
                    seed_track=_to_track(seed_track),
                    tracks=[_to_track(t) for t in tracks],
                )
            )
        except Exception as e:
            logger.error(f"Batch seed '{seed}' failed: {e}")
            items.append(BatchRecommendItem(seed=seed, tracks=[]))

    return BatchRecommendResponse(code=0, data=items, total=len(items), msg="ok")


@router.get("/tracks/search", response_model=TrackSearchResponse)
async def search_tracks(keyword: str, limit: int = 20, request: Request = None):
    qdrant = request.app.state.qdrant
    if not qdrant.is_ready:
        raise HTTPException(status_code=503, detail="Qdrant 未就绪")
    tracks = qdrant.search_tracks(keyword, limit)
    items = [_to_track(t) for t in tracks]
    return TrackSearchResponse(code=0, data=items, total=len(items), msg="ok")


@router.post("/vector", response_model=VectorResponse)
async def get_vector(req: VectorRequest, request: Request):
    qdrant = request.app.state.qdrant
    vec = qdrant.get_vector(req.track_id)
    if vec is None:
        raise HTTPException(status_code=404, detail="曲目未找到")
    return VectorResponse(code=0, data=vec, msg="ok")