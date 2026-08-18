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
    assert data["service"] == "gateway"


@pytest.mark.asyncio
async def test_search_missing_keyword(client):
    resp = await client.get("/api/v1/search")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_search_invalid_page(client):
    resp = await client.get("/api/v1/search?keyword=test&page=0")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_url_missing_id(client):
    resp = await client.get("/api/v1/url")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_pic_missing_id(client):
    resp = await client.get("/api/v1/pic")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_lyric_missing_id(client):
    resp = await client.get("/api/v1/lyric")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_recommend_no_auth(client):
    resp = await client.post("/api/v1/recommend", json={"seed": "test"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_recommend_invalid_token(client):
    resp = await client.post(
        "/api/v1/recommend",
        json={"seed": "test"},
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert resp.status_code == 401