import hashlib
import time
from urllib.parse import quote

import httpx

from app.config import settings
from app.schemas.music import MusicItem, MusicUrl, PicUrl, LyricResult

GD_HOST = "music.gdstudio.xyz"
GD_VERSION = "2026.06.16"
GD_TIME_URL = "https://music.gdstudio.xyz/time"

_BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
    "Origin": "https://music.gdstudio.xyz",
    "Referer": "https://music.gdstudio.xyz/",
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
}


def jsencodeuricomponent(value: str) -> str:
    text = quote(str(value), safe="-_.!~*'()")
    return (text.replace("(", "%28").replace(")", "%29")
                .replace("*", "%2A").replace("'", "%27")
                .replace("!", "%21"))


def _normalize_version(version: str) -> str:
    return "".join(part.zfill(2) if len(part) == 1 else part for part in version.split("."))


def _md5(message: str) -> str:
    return hashlib.md5(message.encode("utf-8")).hexdigest()


def _makesign(payload: str, server_time: int, host: str = GD_HOST, version: str = GD_VERSION) -> str:
    time_prefix = str(server_time)[:9]
    version_text = _normalize_version(version)
    return _md5(f"{time_prefix}|{host}|{version_text}|{payload}")[-8:].upper()


class GDStudioAPI:
    def __init__(self):
        timeout = httpx.Timeout(30.0, connect=10.0)
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=50)
        self.client = httpx.AsyncClient(
            base_url=settings.gd_api_base,
            timeout=timeout,
            limits=limits,
            headers=_BROWSER_HEADERS,
            follow_redirects=True,
        )
        self._max_retries = 3

    async def _server_time(self) -> int:
        try:
            resp = await self.client.get(GD_TIME_URL)
            resp.raise_for_status()
            ts = int(resp.text.strip())
            if ts > 0:
                return ts
        except Exception:
            pass
        return int(time.time())

    async def _sign(self, payload: str) -> str:
        return _makesign(payload=payload, server_time=await self._server_time())

    async def _request(self, params: dict, sign_payload: str) -> dict:
        last_error = None
        params = dict(params)
        params["s"] = await self._sign(sign_payload)
        for attempt in range(self._max_retries):
            try:
                resp = await self.client.post("", data=params)
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    last_error = e
                    await self._sleep(attempt)
                    continue
                raise
            except httpx.RequestError as e:
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
        data = await self._request(params, jsencodeuricomponent(keyword))

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
        data = await self._request(params, jsencodeuricomponent(str(track_id)))
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
        data = await self._request(params, jsencodeuricomponent(str(pic_id)))
        return PicUrl(url=str(data.get("url", "")))

    async def get_lyric(self, lyric_id: str, source: str = "netease") -> LyricResult:
        params = {
            "types": "lyric",
            "source": source,
            "id": lyric_id,
        }
        data = await self._request(params, jsencodeuricomponent(str(lyric_id)))
        return LyricResult(
            lyric=str(data.get("lyric", "")),
            tlyric=str(data.get("tlyric", "")),
        )

    async def close(self):
        await self.client.aclose()


gd_api = GDStudioAPI()