import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from app.config import settings

router = APIRouter(prefix="/api/v1/webdav", tags=["webdav"])

WEBDAV_BASE = "https://kurio.infini-cloud.net/dav/gdmusic"

async def _proxy(request: Request, path: str):
    """Proxy WebDAV requests to the upstream server, adding CORS headers."""
    url = f"{WEBDAV_BASE}/{path.lstrip('/')}"
    headers = {
        "Authorization": "Basic eHVsaXV5OlRyRjdFTkZab0xuSDcyd3E=",
        "User-Agent": "GDMusic-Gateway/1.0",
    }
    # copy original headers
    for key in ("Depth", "Destination", "Overwrite", "Content-Type", "Range"):
        val = request.headers.get(key)
        if val:
            headers[key] = val

    body = await request.body()
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body or None,
                follow_redirects=True,
            )
            return Response(
                content=resp.content,
                status_code=resp.status_code,
                headers=dict(resp.headers),
            )
        except Exception as e:
            return Response(
                content=f'{{"error":"proxy failed: {e}"}',
                status_code=502,
                media_type="application/json",
            )

@router.api_route("/{path:path}", methods=["GET", "HEAD", "POST", "PUT", "DELETE", "PROPFIND", "MKCOL", "MOVE", "COPY", "OPTIONS"])
async def webdav_proxy(request: Request, path: str = ""):
    return await _proxy(request, path)