import time

import jwt
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/login")
def login(body: LoginRequest):
    if body.username == "admin" and body.password == settings.admin_password:
        now = int(time.time())
        payload = {"sub": body.username, "iat": now, "exp": now + 86400}
        token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
        return {"token": token, "user": {"username": body.username}}

    return JSONResponse(
        status_code=401,
        content={"code": 401, "msg": "用户名或密码错误"},
    )


@router.get("/auth/me")
def me(request: Request):
    auth = request.headers.get("Authorization", "")
    token = auth[7:] if auth.startswith("Bearer ") else ""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return {"username": payload.get("sub")}
    except jwt.InvalidTokenError:
        return JSONResponse(status_code=401, content={"code": 401, "msg": "Token 无效"})