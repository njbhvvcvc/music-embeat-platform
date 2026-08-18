import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["service"] == "profile"


@pytest.mark.asyncio
async def test_play_event_validation(client):
    resp = await client.post("/events/play", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_play_event_valid(client):
    resp = await client.post(
        "/events/play",
        json={
            "track_id": "test_001",
            "source": "netease",
            "duration_sec": 120,
            "completed": True,
        },
    )
    assert resp.status_code in (200, 503)  # 503 是 PG 未就绪


@pytest.mark.asyncio
async def test_favorite_validation(client):
    resp = await client.post("/events/favorite", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_favorite_invalid_action(client):
    resp = await client.post(
        "/events/favorite",
        json={"track_id": "test_001", "action": "invalid"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_skip_validation(client):
    resp = await client.post("/events/skip", json={})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_seeds(client):
    resp = await client.get("/seeds")
    assert resp.status_code in (200, 503)
    if resp.status_code == 200:
        data = resp.json()
        assert "code" in data
        assert "data" in data
        assert isinstance(data["data"], list)