from fastapi import APIRouter, Query, HTTPException

from app.clients.gdstudio import gd_api
from app.schemas.music import MusicUrl, PicUrl, LyricResult

router = APIRouter()


@router.get("/url", response_model=MusicUrl)
async def get_url(
    id: str = Query(..., description="曲目 ID"),
    source: str = Query("netease"),
    br: int = Query(320, ge=128, le=999),
):
    try:
        return await gd_api.get_url(id, source, br)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"获取播放链接失败: {str(e)}")


@router.get("/pic", response_model=PicUrl)
async def get_pic(
    id: str = Query(..., description="专辑图 ID"),
    source: str = Query("netease"),
    size: int = Query(300, ge=100, le=500),
):
    try:
        return await gd_api.get_pic(id, source, size)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"获取专辑图失败: {str(e)}")


@router.get("/lyric", response_model=LyricResult)
async def get_lyric(
    id: str = Query(..., description="歌词 ID"),
    source: str = Query("netease"),
):
    try:
        return await gd_api.get_lyric(id, source)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"获取歌词失败: {str(e)}")