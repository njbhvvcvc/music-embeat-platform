from httpx import AsyncClient, Limits, Timeout, HTTPStatusError, RequestError

from app.config import settings
from app.schemas.music import MusicItem, MusicUrl, PicUrl, LyricResult


class GDStudioAPI:
    def __init__(self):
        timeout = Timeout(30.0, connect=10.0)
        limits = Limits(max_keepalive_connections=10, max_connections=50)
        self.client = AsyncClient(
            base_url=settings.gd_api_base,
            timeout=timeout,
            limits=limits,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
                "Origin": "https://music.gdstudio.xyz",
                "Referer": "https://music.gdstudio.xyz/",
                "X-Requested-With": "XMLHttpRequest",
                "Accept": "application/json, text/javascript, */*; q=0.01",
            },
        )
        self._max_retries = 3

    async def _request_with_retry(self, params: dict) -> dict:
        last_error = None
        for attempt in range(self._max_retries):
            try:
                resp = await self.client.get("", params=params)
                resp.raise_for_status()
                return resp.json()
            except HTTPStatusError as e:
                if e.response.status_code >= 500:
                    last_error = e
                    await self._sleep(attempt)
                    continue
                raise
            except RequestError as e:
                last_error = e
                await self._sleep(attempt)
                continue
        raise last_error or Exception("Max retries exceeded")

    async def _sleep(self, attempt: int):
        import asyncio
        await asyncio.sleep(0.5 * (2 ** attempt))

    async def search(
        self,
        keyword: str,
        source: str = "netease",
        page: int = 1,
        page_size: int = 20,
    ) -> list[MusicItem]:
        params = {
            "types": "search",
            "source": source,
            "name": keyword,
            "count": page_size,
            "pages": page,
        }
        data = await self._request_with_retry(params)

        # GD Studio API 直接返回 list，不是包含 data 字段的 dict
        items = data if isinstance(data, list) else []

        results = []
        for item in items:
            try:
                results.append(
                    MusicItem(
                        id=str(item.get("id", "")),
                        name=str(item.get("name", "")),
                        artist=str(item.get("artist", "")),
                        album=str(item.get("album", "")),
                        pic_id=str(item.get("pic_id", "")),
                        lyric_id=str(item.get("lyric_id", "")),
                        source=str(item.get("source", source)),
                    )
                )
            except Exception:
                continue  # 跳过格式错误的条目
        return results

    async def get_url(
        self, track_id: str, source: str = "netease", br: int = 320
    ) -> MusicUrl:
        params = {
            "types": "url",
            "source": source,
            "id": track_id,
            "br": br,
        }
        data = await self._request_with_retry(params)
        return MusicUrl(
            url=str(data.get("url", "")),
            br=int(data.get("br", br)),
            size=int(data.get("size", 0)),
        )

    async def get_pic(self, pic_id: str, source: str = "netease", size: int = 300) -> PicUrl:
        params = {
            "types": "pic",
            "source": source,
            "id": pic_id,
            "size": size,
        }
        data = await self._request_with_retry(params)
        return PicUrl(url=str(data.get("url", "")))

    async def get_lyric(self, lyric_id: str, source: str = "netease") -> LyricResult:
        params = {
            "types": "lyric",
            "source": source,
            "id": lyric_id,
        }
        data = await self._request_with_retry(params)
        return LyricResult(
            lyric=str(data.get("lyric", "")),
            tlyric=str(data.get("tlyric", "")),
        )

    async def close(self):
        await self.client.aclose()


gd_api = GDStudioAPI()