from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import search, playback, recommend, profile as profile_routes, health, auth, ops, dataset
from app.middleware.ratelimit import RateLimitMiddleware
from app.middleware.auth import AuthMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Embeat API Gateway",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(AuthMiddleware)

app.include_router(health.router, tags=["health"])
app.include_router(search.router, prefix="/api/v1", tags=["search"])
app.include_router(playback.router, prefix="/api/v1", tags=["playback"])
app.include_router(recommend.router, prefix="/api/v1", tags=["recommend"])
app.include_router(profile_routes.router, prefix="/api/v1", tags=["profile"])
app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(ops.router, prefix="/api/v1", tags=["ops"])
app.include_router(dataset.router, prefix="/api/v1", tags=["dataset"])