import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = settings.gd_api_rate_window
        limit = settings.gd_api_rate_limit

        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if now - t < window
        ]

        if len(self.requests[client_ip]) >= limit:
            return JSONResponse(
                status_code=429,
                content={
                    "code": 429,
                    "msg": f"请求频率超限: {limit}次/{window}秒",
                },
            )

        self.requests[client_ip].append(now)
        response = await call_next(request)
        return response