import jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.config import settings

PUBLIC_PATHS = {"/health", "/api/auth/login", "/api/v1/search", "/api/v1/url", "/api/v1/pic", "/api/v1/lyric"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path in PUBLIC_PATHS or request.url.path.startswith("/docs"):
            return await call_next(request)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            auth = f"Bearer {request.query_params.get('token', '')}"
        if auth.startswith("Bearer "):
            token = auth[7:]
            try:
                jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
                return await call_next(request)
            except jwt.ExpiredSignatureError:
                return JSONResponse(
                    status_code=401, content={"code": 401, "msg": "Token 已过期"}
                )
            except jwt.InvalidTokenError:
                return JSONResponse(
                    status_code=401, content={"code": 401, "msg": "Token 无效"}
                )

        return JSONResponse(
            status_code=401,
            content={"code": 401, "msg": "缺少 Authorization: Bearer <token>"},
        )