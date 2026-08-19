import logging
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, Filter, FieldCondition, MatchValue, MatchText,
    OrderBy
)
try:
    from qdrant_client.exceptions import UnexpectedResponse
except ImportError:  # qdrant-client < 1.14
    from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings
from app.core.track_id import track_id_to_uuid

logger = logging.getLogger(__name__)


class QdrantRepo:
    def __init__(self):
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            timeout=30,
            prefer_grpc=False,
        )
        self.collection = settings.qdrant_collection
        self._ready_cache = False

    @property
    def is_ready(self) -> bool:
        if self._ready_cache:
            return True
        try:
            collections = self.client.get_collections()
            names = [c.name for c in collections.collections]
            self._ready_cache = self.collection in names
            return self._ready_cache
        except Exception as e:
            logger.warning(f"Qdrant readiness check failed: {e}")
            return False

    def invalidate_ready_cache(self):
        self._ready_cache = False

    def search_similar(
        self,
        vector: list[float],
        top_k: int = 20,
        genre_filter: str | None = None,
        artist_exclude: str | None = None,
    ) -> list[dict]:
        """向量相似度搜索，支持流派过滤和艺人排除"""
        try:
            must_conditions = []
            if genre_filter:
                # 支持多流派，用逗号分隔
                for g in genre_filter.split(","):
                    g = g.strip()
                    if g:
                        must_conditions.append(
                            FieldCondition(key="artist_genres", match=MatchValue(value=g))
                        )

            query_filter = Filter(must=must_conditions) if must_conditions else None

            # 如果需要排除某个艺人
            if artist_exclude:
                if query_filter is None:
                    query_filter = Filter(
                        must_not=[FieldCondition(key="artist_name", match=MatchValue(value=artist_exclude))]
                    )
                else:
                    query_filter.must_not = [
                        FieldCondition(key="artist_name", match=MatchValue(value=artist_exclude))
                    ]

            hits = self.client.search(
                collection_name=self.collection,
                query_vector=vector,
                limit=top_k * 3,  # 多取一些用于后续去重
                query_filter=query_filter,
                with_payload=True,
            )
            return [self._hit_to_dict(h) for h in hits]
        except UnexpectedResponse as e:
            logger.error(f"Qdrant search failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            return []

    def search_by_artist(self, artist_idx: int, top_k: int = 20) -> list[dict]:
        """同艺人搜索"""
        try:
            query_filter = Filter(
                must=[FieldCondition(key="artist_idx", match=MatchValue(value=artist_idx))]
            )
            resp = self.client.query_points(
                collection_name=self.collection,
                query=OrderBy(key="popularity"),
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            )
            return [self._hit_to_dict(h) for h in resp.points]
        except Exception as e:
            logger.error(f"Qdrant search_by_artist failed: {e}")
            return []

    def search_by_genre_popular(self, genre: str, top_k: int = 20) -> list[dict]:
        """同流派热门搜索 - 使用 Query API + OrderBy 排序"""
        try:
            # 支持多流派
            must_conditions = []
            for g in genre.split(","):
                g = g.strip()
                if g:
                    must_conditions.append(
                        FieldCondition(key="artist_genres", match=MatchValue(value=g))
                    )
            query_filter = Filter(must=must_conditions) if must_conditions else None

            resp = self.client.query_points(
                collection_name=self.collection,
                query=OrderBy(key="popularity"),
                query_filter=query_filter,
                limit=top_k,
                with_payload=True,
            )
            return [self._hit_to_dict(h) for h in resp.points]
        except Exception as e:
            logger.error(f"Qdrant search_by_genre_popular failed: {e}")
            return []

    def search_by_title(
        self, title: str, artist: str | None = None, top_k: int = 5
    ) -> list[dict]:
        """按歌名（+歌手）查找曲目，支持 '歌名 - 歌手' 形式的种子"""
        try:
            artist_cond = None
            if artist:
                artist_cond = FieldCondition(
                    key="artist_name", match=MatchValue(value=artist)
                )

            exact = [FieldCondition(key="track_name", match=MatchValue(value=title))]
            if artist_cond:
                exact.append(artist_cond)
            points, _ = self.client.scroll(
                collection_name=self.collection,
                scroll_filter=Filter(must=exact),
                limit=top_k,
                with_payload=True,
            )
            if points:
                return [self._hit_to_dict(p) for p in points]

            text = [FieldCondition(key="track_name", match=MatchText(text=title))]
            if artist_cond:
                text.append(artist_cond)
            points, _ = self.client.scroll(
                collection_name=self.collection,
                scroll_filter=Filter(must=text),
                limit=top_k,
                with_payload=True,
            )
            return [self._hit_to_dict(p) for p in points]
        except Exception as e:
            logger.error(f"Qdrant search_by_title failed: {e}")
            return []

    def get_track(self, track_id: str) -> Optional[dict]:
        """获取单个曲目"""
        try:
            hits = self.client.retrieve(
                collection_name=self.collection,
                ids=[track_id_to_uuid(track_id)],
                with_payload=True,
            )
            if hits:
                return self._hit_to_dict(hits[0])
            return None
        except Exception as e:
            logger.error(f"Qdrant get_track failed: {e}")
            return None

    def get_vector(self, track_id: str) -> Optional[list[float]]:
        """获取曲目向量"""
        try:
            hits = self.client.retrieve(
                collection_name=self.collection,
                ids=[track_id_to_uuid(track_id)],
                with_vectors=True,
            )
            if hits:
                return hits[0].vector
            return None
        except Exception as e:
            logger.error(f"Qdrant get_vector failed: {e}")
            return None

    def _hit_to_dict(self, hit) -> dict:
        return {
            "track_id": hit.payload.get("track_id", hit.id),
            "title": hit.payload.get("track_name", ""),
            "artist": hit.payload.get("artist_name", ""),
            "album": hit.payload.get("album_name", ""),
            "popularity": hit.payload.get("popularity", 0),
            "artist_genre": hit.payload.get("artist_genres", ""),
            "artist_idx": hit.payload.get("artist_idx", -1),
            "isrc": hit.payload.get("isrc", ""),
            "score": hit.score if hasattr(hit, "score") else 0.0,
        }