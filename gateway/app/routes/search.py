from fastapi import APIRouter, Query, HTTPException

from app.clients.gdstudio import gd_api
from app.schemas.music import MusicItem, SearchResponse

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
async def search_music(
    keyword: str = Query(..., min_length=1, max_length=200),
    source: str = Query("netease", description="音乐源: netease/tencent/kuwo/joox/bilibili/apple"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    try:
        items = await gd_api.search(keyword, source, page, page_size)
        return SearchResponse(
            code=0,
            data=items,
            total=len(items),
            page=page,
            page_size=page_size,
            msg="ok",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"音乐源请求失败: {str(e)}")