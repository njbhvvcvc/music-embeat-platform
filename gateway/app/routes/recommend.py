from fastapi import APIRouter, HTTPException

from app.clients.embeat import embeat_client
from app.schemas.recommend import (
    RecommendRequest,
    RecommendResponse,
    VectorRequest,
    VectorResponse,
)

router = APIRouter()


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest):
    try:
        tracks = await embeat_client.recommend(
            seed=req.seed,
            top_k=req.top_k,
            channels=req.channels,
        )
        return RecommendResponse(
            code=0,
            data=tracks,
            total=len(tracks),
            msg="ok",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"推荐请求失败: {str(e)}")


@router.post("/vector", response_model=VectorResponse)
async def get_vector(req: VectorRequest):
    try:
        vec = await embeat_client.vector(req.track_id)
        return VectorResponse(code=0, data=vec, msg="ok")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"向量查询失败: {str(e)}")