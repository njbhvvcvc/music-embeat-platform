from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()


class RecommendRequest(BaseModel):
    seed: str = Field(..., description="种子曲目 ID 或 '歌名 - 歌手'")
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
    msg: str = "ok"


class VectorRequest(BaseModel):
    track_id: str = Field(..., description="曲目 ID")


class VectorResponse(BaseModel):
    code: int = 0
    data: list[float] = []
    msg: str = "ok"


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest, request: Request):
    qdrant = request.app.state.qdrant
    model = request.app.state.model_loader
    from app.core.recall import RecallEngine

    engine = RecallEngine(qdrant, model)
    if not qdrant.is_ready:
        raise HTTPException(status_code=503, detail="Qdrant 未就绪，请先导入向量库")

    try:
        tracks = await engine.recommend(req.seed, req.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推荐失败: {str(e)}")

    items = [
        RecommendTrack(
            track_id=t.get("track_id", ""),
            title=t.get("title", ""),
            artist=t.get("artist", ""),
            album=t.get("album", ""),
            score=float(t.get("score", 0)),
            channel=t.get("channel", ""),
        )
        for t in tracks
    ]
    return RecommendResponse(code=0, data=items, total=len(items), msg="ok")


@router.post("/vector", response_model=VectorResponse)
async def get_vector(req: VectorRequest, request: Request):
    qdrant = request.app.state.qdrant
    vec = qdrant.get_vector(req.track_id)
    if vec is None:
        raise HTTPException(status_code=404, detail="曲目未找到")
    return VectorResponse(code=0, data=vec, msg="ok")