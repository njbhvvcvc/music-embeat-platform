from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import recommend, health
from app.core.model_loader import ModelLoader
from app.core.qdrant_repo import QdrantRepo


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.model_loader = ModelLoader()
    app.state.qdrant = QdrantRepo()
    yield


app = FastAPI(
    title="Embeat Recommendation Engine",
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

app.include_router(health.router, tags=["health"])
app.include_router(recommend.router, prefix="/api/v1", tags=["recommend"])