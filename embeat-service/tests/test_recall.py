import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.recall import RecallEngine
from app.core.qdrant_repo import QdrantRepo
from app.core.model_loader import ModelLoader


@pytest.fixture
def mock_qdrant():
    qdrant = MagicMock(spec=QdrantRepo)
    qdrant.is_ready = True
    qdrant.get_track.return_value = {
        "track_id": "test_001",
        "title": "Test Song",
        "artist": "Test Artist",
        "album": "Test Album",
        "popularity": 80,
        "artist_genre": "c-pop",
        "artist_idx": 42,
    }
    qdrant.get_vector.return_value = [0.1] * 64
    qdrant.search_similar.return_value = [
        {"track_id": f"sim_{i}", "title": f"Similar {i}", "artist": "Artist A",
         "score": 0.9 - i * 0.1, "channel": "similar"}
        for i in range(5)
    ]
    qdrant.search_by_genre_popular.return_value = [
        {"track_id": f"pop_{i}", "title": f"Popular {i}", "artist": "Artist B",
         "score": 0.8 - i * 0.1, "channel": "popular"}
        for i in range(5)
    ]
    qdrant.search_by_artist.return_value = [
        {"track_id": f"artist_{i}", "title": f"Artist Track {i}", "artist": "Test Artist",
         "score": 0.7 - i * 0.1, "channel": "same_artist"}
        for i in range(5)
    ]
    return qdrant


@pytest.fixture
def mock_model():
    model = MagicMock(spec=ModelLoader)
    model.is_loaded = True
    return model


@pytest.fixture
def engine(mock_qdrant, mock_model):
    return RecallEngine(mock_qdrant, mock_model)


@pytest.mark.asyncio
async def test_recommend_returns_tracks(engine):
    results = await engine.recommend("test_001", top_k=10)
    assert len(results) > 0
    assert all("track_id" in t for t in results)
    assert all("channel" in t for t in results)
    assert all("score" in t for t in results)


@pytest.mark.asyncio
async def test_recommend_deduplicates(engine):
    results = await engine.recommend("test_001", top_k=10)
    track_ids = [t["track_id"] for t in results]
    assert len(track_ids) == len(set(track_ids))


@pytest.mark.asyncio
async def test_recommend_limits_same_artist(engine, mock_qdrant):
    mock_qdrant.search_by_artist.return_value = [
        {"track_id": f"sa_{i}", "title": f"Same Artist {i}", "artist": "Test Artist",
         "score": 0.9, "channel": "same_artist"}
        for i in range(10)
    ]
    results = await engine.recommend("test_001", top_k=20)
    same_artist_count = sum(1 for t in results if t.get("artist") == "Test Artist")
    total = len(results)
    assert same_artist_count <= max(1, int(total * 0.3))


@pytest.mark.asyncio
async def test_recommend_empty_when_no_seed(engine, mock_qdrant):
    mock_qdrant.get_track.return_value = None
    results = await engine.recommend("nonexistent", top_k=10)
    assert results == []


@pytest.mark.asyncio
async def test_recommend_multiple_channels_covered(engine):
    results = await engine.recommend("test_001", top_k=20)
    channels = set(t["channel"] for t in results)
    assert len(channels) >= 2


def test_deduplicate_isrc(engine):
    tracks = [
        {"track_id": "a", "isrc": "ISRC1"},
        {"track_id": "b", "isrc": "ISRC1"},
        {"track_id": "c", "isrc": "ISRC2"},
    ]
    result = engine._deduplicate_isrc(tracks)
    assert len(result) == 2
    assert result[0]["track_id"] == "a"
    assert result[1]["track_id"] == "c"


def test_limit_same_artist(engine):
    tracks = [
        {"artist": "A", "track_id": "1"},
        {"artist": "A", "track_id": "2"},
        {"artist": "A", "track_id": "3"},
        {"artist": "A", "track_id": "4"},
        {"artist": "B", "track_id": "5"},
    ]
    result = engine._limit_same_artist(tracks, max_ratio=0.3)
    a_count = sum(1 for t in result if t["artist"] == "A")
    assert a_count <= 1