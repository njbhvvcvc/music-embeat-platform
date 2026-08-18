from pydantic import BaseModel, Field
from typing import Optional


class MusicItem(BaseModel):
    id: str = Field(..., description="曲目 ID")
    name: str = Field(..., description="歌曲名")
    artist: str = Field(..., description="歌手列表（逗号分隔）")
    album: str = Field(default="", description="专辑名")
    pic_id: str = Field(default="", description="专辑图 ID")
    lyric_id: str = Field(default="", description="歌词 ID")
    source: str = Field(default="netease", description="音乐源")
    duration: Optional[int] = Field(default=None, description="时长（秒）")


class MusicUrl(BaseModel):
    url: str = Field(..., description="播放链接")
    br: int = Field(default=320, description="实际音质")
    size: int = Field(default=0, description="文件大小 KB")


class PicUrl(BaseModel):
    url: str = Field(..., description="图片链接")


class LyricResult(BaseModel):
    lyric: str = Field(default="", description="原语种歌词 LRC")
    tlyric: str = Field(default="", description="翻译歌词 LRC")


class SearchRequest(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200)
    source: str = Field(default="netease")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SearchResponse(BaseModel):
    code: int = 0
    data: list[MusicItem] = []
    total: int = 0
    page: int = 1
    page_size: int = 20
    msg: str = "ok"