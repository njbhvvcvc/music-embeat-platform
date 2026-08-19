import logging
from app.config import settings
from app.core.qdrant_repo import QdrantRepo
from app.core.model_loader import ModelLoader

logger = logging.getLogger(__name__)


class RecallEngine:
    def __init__(self, qdrant: QdrantRepo, model: ModelLoader):
        self.qdrant = qdrant
        self.model = model
        self.channels = [c.strip() for c in settings.embeat_channels.split(",")]

    async def recommend(self, seed: str, top_k: int = 20) -> list[dict]:
        seed_track = self.qdrant.get_track(seed)
        if not seed_track and " - " in seed:
            title, artist = seed.rsplit(" - ", 1)
            title = title.strip()
            artist = artist.strip()
            matches = self.qdrant.search_by_title(title, artist=artist or None, top_k=1)
            if not matches:
                matches = self.qdrant.search_by_title(title, top_k=3)
            if matches:
                seed_track = matches[0]

        if not seed_track:
            logger.warning(f"Seed track not found: {seed}")
            return []

        seed_id = seed_track.get("track_id", seed)
        artist_genre = seed_track.get("artist_genre", "")
        artist_idx = seed_track.get("artist_idx", -1)
        seed_artist = seed_track.get("artist", "")
        results: list[dict] = []
        seen = set()

        for channel in self.channels:
            channel = channel.strip()
            if not channel:
                continue
            channel_tracks = []

            try:
                if channel == "similar":
                    vec = self.qdrant.get_vector(seed_id)
                    if vec:
                        channel_tracks = self.qdrant.search_similar(
                            vec, top_k, genre_filter=artist_genre or None, artist_exclude=seed_artist
                        )
                        for t in channel_tracks:
                            t["channel"] = "similar"

                elif channel == "popular":
                    if artist_genre:
                        channel_tracks = self.qdrant.search_by_genre_popular(artist_genre, top_k)
                        for t in channel_tracks:
                            t["channel"] = "popular"

                elif channel == "same_artist":
                    if artist_idx >= 0:
                        channel_tracks = self.qdrant.search_by_artist(artist_idx, top_k)
                        for t in channel_tracks:
                            t["channel"] = "same_artist"

                elif channel == "related_artist":
                    vec = self.qdrant.get_vector(seed_id)
                    if vec:
                        raw = self.qdrant.search_similar(vec, top_k * 2)
                        channel_tracks = [
                            t for t in raw
                            if t.get("artist", "") != seed_artist
                        ][:top_k]
                        for t in channel_tracks:
                            t["channel"] = "related_artist"

            except Exception as e:
                logger.error(f"Channel '{channel}' failed: {e}")
                continue

            for t in channel_tracks:
                tid = t.get("track_id", "")
                if tid and tid not in seen and tid != seed_id:
                    seen.add(tid)
                    results.append(t)

        deduped = self._deduplicate_isrc(results)
        reranked = self._rerank(deduped)
        reranked = self._limit_same_artist(reranked, max_ratio=0.3)
        return reranked[:top_k]

    def _deduplicate_isrc(self, tracks: list[dict]) -> list[dict]:
        seen = set()
        result = []
        for t in tracks:
            isrc = t.get("isrc", t.get("track_id", ""))
            if isrc and isrc not in seen:
                seen.add(isrc)
                result.append(t)
        return result

    def _rerank(self, tracks: list[dict]) -> list[dict]:
        return sorted(tracks, key=lambda x: x.get("score", 0), reverse=True)

    def _limit_same_artist(self, tracks: list[dict], max_ratio: float = 0.3) -> list[dict]:
        if not tracks:
            return tracks
        max_count = max(1, int(len(tracks) * max_ratio))
        artist_count: dict = {}
        result = []
        for t in tracks:
            artist = t.get("artist", "")
            if artist_count.get(artist, 0) < max_count:
                artist_count[artist] = artist_count.get(artist, 0) + 1
                result.append(t)
        return result