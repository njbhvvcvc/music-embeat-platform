import asyncpg
from app.config import settings


class Database:
    def __init__(self):
        self.pool: asyncpg.Pool | None = None

    async def init(self):
        self.pool = await asyncpg.create_pool(
            user=settings.postgres_user,
            password=settings.postgres_password,
            database=settings.postgres_db,
            host=settings.postgres_host,
            port=settings.postgres_port,
            min_size=2,
            max_size=10,
        )
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS play_history (
                    id SERIAL PRIMARY KEY,
                    track_id TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'netease',
                    duration_sec INTEGER NOT NULL DEFAULT 0,
                    completed BOOLEAN NOT NULL DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_play_history_track
                    ON play_history(track_id);
                CREATE INDEX IF NOT EXISTS idx_play_history_ts
                    ON play_history(created_at DESC);

                CREATE TABLE IF NOT EXISTS favorites (
                    id SERIAL PRIMARY KEY,
                    track_id TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'netease',
                    action TEXT NOT NULL DEFAULT 'add',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_favorites_track
                    ON favorites(track_id);

                CREATE TABLE IF NOT EXISTS skips (
                    id SERIAL PRIMARY KEY,
                    track_id TEXT NOT NULL,
                    source TEXT NOT NULL DEFAULT 'netease',
                    skip_after_sec INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
                CREATE INDEX IF NOT EXISTS idx_skips_track
                    ON skips(track_id);
            """)

    async def record_play(self, track_id: str, source: str, duration_sec: int, completed: bool):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO play_history (track_id, source, duration_sec, completed) VALUES ($1, $2, $3, $4)",
                track_id, source, duration_sec, completed,
            )

    async def record_favorite(self, track_id: str, source: str, action: str):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO favorites (track_id, source, action) VALUES ($1, $2, $3)",
                track_id, source, action,
            )

    async def record_skip(self, track_id: str, source: str, skip_after_sec: int):
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO skips (track_id, source, skip_after_sec) VALUES ($1, $2, $3)",
                track_id, source, skip_after_sec,
            )

    async def get_seeds(self, limit: int = 50) -> list[str]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT track_id FROM (
                    SELECT track_id, COUNT(*) as cnt
                    FROM play_history
                    WHERE completed = TRUE
                    GROUP BY track_id
                    ORDER BY cnt DESC
                    LIMIT $1
                ) sub
                """,
                limit,
            )
            return [row["track_id"] for row in rows]

    async def close(self):
        if self.pool:
            await self.pool.close()