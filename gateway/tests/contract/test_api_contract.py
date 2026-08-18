"""
契约测试：验证 API 响应格式符合约定。

运行:
    pytest tests/contract/ -v
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client():
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


@pytest.mark.asyncio
async def test_health_contract(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "service" in data
    assert data["status"] == "ok"
    assert data["service"] == "gateway"


@pytest.mark.asyncio
async def test_search_contract(client):
    resp = await client.get("/api/v1/search?keyword=周杰伦")
    assert resp.status_code == 200
    data = resp.json()
    assert "code" in data
    assert "data" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "msg" in data
    assert isinstance(data["code"], int)
    assert isinstance(data["data"], list)
    if data["data"]:
        item = data["data"][0]
        assert "id" in item
        assert "name" in item
        assert "artist" in item
        assert "source" in item


@pytest.mark.asyncio
async def test_search_validation_contract(client):
    """验证参数校验错误返回格式"""
    resp = await client.get("/api/v1/search")
    assert resp.status_code == 422
    data = resp.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_url_contract(client):
    resp = await client.get("/api/v1/url?id=test_001&source=netease&br=320")
    assert resp.status_code in (200, 502)
    if resp.status_code == 200:
        data = resp.json()
        assert "url" in data
        assert "br" in data
        assert "size" in data


@pytest.mark.asyncio
async def test_pic_contract(client):
    resp = await client.get("/api/v1/pic?id=test_001&size=300")
    assert resp.status_code in (200, 502)
    if resp.status_code == 200:
        data = resp.json()
        assert "url" in data


@pytest.mark.asyncio
async def test_lyric_contract(client):
    resp = await client.get("/api/v1/lyric?id=test_001")
    assert resp.status_code in (200, 502)
    if resp.status_code == 200:
        data = resp.json()
        assert "lyric" in data
        assert "tlyric" in data


@pytest.mark.asyncio
async def test_recommend_auth_contract(client):
    """验证推荐接口需要鉴权"""
    resp = await client.post("/api/v1/recommend", json={"seed": "test"})
    assert resp.status_code == 401
    data = resp.json()
    assert "code" in data
    assert "msg" in data
    assert data["code"] == 401


@pytest.mark.asyncio
async def test_recommend_no_auth_contract(client):
    """验证搜索接口无需鉴权"""
    resp = await client.get("/api/v1/search?keyword=test")
    assert resp.status_code in (200, 502)  # 502 是 GD API 连不上，但契约没问题


@pytest.mark.asyncio
async def test_rate_limit_contract(client):
    """验证限流返回格式"""
    for _ in range(10):
        await client.get("/api/v1/search?keyword=test")
    resp = await client.get("/api/v1/search?keyword=test")
    if resp.status_code == 429:
        data = resp.json()
        assert "code" in data
        assert "msg" in data
        assert data["code"] == 429