from httpx import AsyncClient, Limits, Timeout, HTTPStatusError, RequestError

from app.config import settings
from app.schemas.recommend import RecommendTrack, RecommendResponse


class EmbeatClient:
    def __init__(self):
        self.base_url = settings.embeat_base
        timeout = Timeout(60.0, connect=10.0)
        limits = Limits(max_keepalive_connections=5, max_connections=20)
        self.client = AsyncClient(timeout=timeout, limits=limits)
        self._max_retries = 3

    async def _request_with_retry(self, method: str, path: str, **kwargs) -> dict:
        last_error = None
        for attempt in range(self._max_retries):
            try:
                resp = await self.client.request(method, f"{self.base_url}{path}", **kwargs)
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

    async def recommend(
        self,
        seed: str,
        top_k: int = 20,
        channels: str = "similar,popular,same_artist,related_artist",
    ) -> list[RecommendTrack]:
        data = await self._request_with_retry(
            "POST",
            "/api/v1/recommend",
            json={"seed": seed, "top_k": top_k, "channels": channels},
        )
        tracks = []
        for item in data.get("data", []):
            try:
                tracks.append(RecommendTrack(**item))
            except Exception:
                continue
        return tracks

    async def vector(self, track_id: str) -> list[float]:
        data = await self._request_with_retry(
            "POST", "/api/v1/vector", json={"track_id": track_id}
        )
        return data.get("data", [])

    async def health(self) -> bool:
        try:
            resp = await self.client.get(f"{self.base_url}/health", timeout=5.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def close(self):
        await self.client.aclose()


embeat_client = EmbeatClient()