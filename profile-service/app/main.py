from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import events, seeds, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.database import Database
    app.state.db = Database()
    await app.state.db.init()
    yield
    await app.state.db.close()


app = FastAPI(
    title="Embeat Profile Service",
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
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(seeds.router, prefix="", tags=["seeds"])