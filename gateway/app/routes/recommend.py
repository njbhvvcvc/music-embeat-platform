import time

from fastapi import APIRouter, HTTPException, Query

from app.clients.embeat import embeat_client
from app.core.metrics import metrics
from app.schemas.recommend import (
    BatchRecommendRequest,
    BatchRecommendResponse,
    BatchRecommendItem,
    RecommendRequest,
    RecommendResponse,
    TrackSearchResponse,
    VectorRequest,
    VectorResponse,
)

router = APIRouter()


@router.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest):
    start = time.perf_counter()
    try:
        result = await embeat_client.recommend(
            seed=req.seed,
            top_k=req.top_k,
            channels=req.channels,
        )
        metrics.record((time.perf_counter() - start) * 1000)
        return RecommendResponse(
            code=result.get("code", 0),
            data=result.get("data", []),
            total=result.get("total", 0),
            seed=result.get("seed", ""),
            seed_track=result.get("seed_track"),
            msg=result.get("msg", "ok"),
        )
    except Exception as e:
        metrics.record((time.perf_counter() - start) * 1000)
        raise HTTPException(status_code=502, detail=f"推荐请求失败: {str(e)}")


@router.post("/recommend/batch", response_model=BatchRecommendResponse)
async def recommend_batch(req: BatchRecommendRequest):
    try:
        items = await embeat_client.recommend_batch(
            seeds=req.seeds,
            top_k=req.top_k,
            channels=req.channels,
        )
        data = [
            BatchRecommendItem(
                seed=item.get("seed", ""),
                seed_track=item.get("seed_track"),
                tracks=item.get("tracks", []),
            )
            for item in items
        ]
        return BatchRecommendResponse(code=0, data=data, total=len(data), msg="ok")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"批量推荐失败: {str(e)}")


@router.get("/tracks/search", response_model=TrackSearchResponse)
async def search_tracks(
    keyword: str = Query(..., min_length=1, max_length=200),
    limit: int = Query(20, ge=1, le=100),
):
    try:
        tracks = await embeat_client.search_tracks(keyword, limit)
        return TrackSearchResponse(code=0, data=tracks, total=len(tracks), msg="ok")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"曲库搜索失败: {str(e)}")


@router.post("/vector", response_model=VectorResponse)
async def get_vector(req: VectorRequest):
    try:
        vec = await embeat_client.vector(req.track_id)
        return VectorResponse(code=0, data=vec, msg="ok")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"向量查询失败: {str(e)}")