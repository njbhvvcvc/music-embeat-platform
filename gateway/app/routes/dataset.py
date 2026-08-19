"""数据集管线：从 ModelScope 导入快照 / 删除集合，网页端完成模型数据切换。

安全设计：
1. 磁盘保护：导入前检查宿主与快照目录剩余空间，不足直接拒绝；
2. 原子性：先下载到临时文件，成功后才删旧库、恢复、清理；
3. 并发保护：同一时间只允许一个导入任务；
4. 进度：下载按字节算，恢复按时间 + 集合状态估算，前端轮询刷新。

Qdrant 快照共享卷：
- 网关容器挂载 /snapshots
- Qdrant 容器挂载 /qdrant/storage/snapshots
（同一个 named volume，网关写文件，Qdrant 从本地路径恢复）
"""
import asyncio
import os
import time

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import settings
from app.core import monitor

router = APIRouter()

_GB = 1024 * 1024 * 1024


def _fmt(n: float) -> str:
    if n >= _GB:
        return f"{n / _GB:.2f} GB"
    if n >= 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    return f"{n / 1024:.0f} KB"


class DatasetTask:
    def __init__(self):
        self._lock = asyncio.Lock()
        self.state = "idle"
        self.stage = ""
        self.percent = 0
        self.message = ""
        self.file = ""
        self.error = None
        self.started_at = 0
        self.updated_at = 0

    async def start(self, file: str):
        async with self._lock:
            self.state = "running"
            self.stage = "checking"
            self.percent = 0
            self.message = "正在检查磁盘空间与数据源..."
            self.file = file
            self.error = None
            self.started_at = int(time.time() * 1000)
            self.updated_at = self.started_at

    async def set(self, stage: str, percent: float, message: str):
        async with self._lock:
            self.stage = stage
            self.percent = max(0.0, min(100.0, round(percent, 1)))
            self.message = message
            self.updated_at = int(time.time() * 1000)

    async def fail(self, message: str):
        async with self._lock:
            self.state = "error"
            self.error = message
            self.message = message
            self.updated_at = int(time.time() * 1000)

    async def done(self, message: str):
        async with self._lock:
            self.state = "done"
            self.stage = "done"
            self.percent = 100
            self.message = message
            self.updated_at = int(time.time() * 1000)

    def snapshot(self) -> dict:
        return {
            "state": self.state,
            "stage": self.stage,
            "percent": self.percent,
            "message": self.message,
            "file": self.file,
            "error": self.error,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
        }


_task = DatasetTask()


async def _qdrant_json(client: httpx.AsyncClient, method: str, path: str, **kw):
    r = await client.request(method, f"{settings.qdrant_base}{path}", **kw)
    return r.status_code, r.json()


class ImportRequest(BaseModel):
    file: str
    delete_existing: bool = True
    namespace: str = ""
    dataset: str = ""


class DeleteRequest(BaseModel):
    confirm: bool = False


@router.get("/dataset/status")
async def dataset_status():
    coll = monitor.qdrant_collection_info()
    files = monitor.modelscope_list_files(settings.modelscope_namespace, settings.modelscope_dataset)
    return {
        "code": 0,
        "collection": coll,
        "collection_name": settings.qdrant_collection,
        "snapshots": [
            {"path": f["path"], "size": f["size"], "size_text": _fmt(f["size"])}
            for f in files
            if f["path"].endswith(".snapshot")
        ],
        "disk": monitor.disk_usage("/"),
        "snapshot_disk": monitor.disk_usage(settings.snapshot_dir),
        "modelscope": {
            "namespace": settings.modelscope_namespace,
            "dataset": settings.modelscope_dataset,
        },
        "task": _task.snapshot(),
        "now": int(time.time() * 1000),
    }


@router.get("/dataset/task")
async def dataset_task():
    return {"code": 0, "data": _task.snapshot()}


@router.post("/dataset/import")
async def dataset_import(req: ImportRequest):
    if _task.state == "running":
        return JSONResponse(status_code=400, content={"code": 400, "msg": "已有导入任务进行中，请稍候"})
    ns = req.namespace or settings.modelscope_namespace
    ds = req.dataset or settings.modelscope_dataset
    asyncio.create_task(_run_import(req.file, ns, ds, req.delete_existing))
    return {"code": 0, "msg": "导入任务已启动", "data": _task.snapshot()}


@router.post("/dataset/delete")
async def dataset_delete(req: DeleteRequest):
    if not req.confirm:
        return JSONResponse(status_code=400, content={"code": 400, "msg": "需要 confirm=true 确认删除"})
    if _task.state == "running":
        return JSONResponse(status_code=400, content={"code": 400, "msg": "有导入任务进行中，禁止删除"})
    coll = settings.qdrant_collection
    async with httpx.AsyncClient(timeout=30) as client:
        status, data = await _qdrant_json(client, "DELETE", f"/collections/{coll}?wait=true")
    if status not in (200, 204):
        return JSONResponse(status_code=502, content={"code": 502, "msg": f"删除失败 HTTP {status}: {data}"})
    return {"code": 0, "msg": f"集合 {coll} 已删除"}


async def _run_import(file: str, ns: str, ds: str, delete_existing: bool):
    await _task.start(file)
    coll = settings.qdrant_collection
    snapshot_dir = settings.snapshot_dir
    dest = os.path.join(snapshot_dir, os.path.basename(file))
    tmp = dest + ".part"

    try:
        # 1. 校验数据源文件
        await _task.set("checking", 1, f"正在获取 {ns}/{ds} 文件清单...")
        files = await asyncio.to_thread(monitor.modelscope_list_files, ns, ds)
        match = None
        for f in files:
            if f["path"] == file or f["path"].endswith("/" + file):
                match = f
                break
        if match is None:
            raise RuntimeError(f"ModelScope 数据集中找不到 {file}")
        size = int(match["size"] or 0)

        # 2. 磁盘保护：宿主 + 快照目录都要够
        host_disk = await asyncio.to_thread(monitor.disk_usage, "/")
        snap_disk = await asyncio.to_thread(monitor.disk_usage, snapshot_dir)
        needed_host = size + size * 1.5 + settings.disk_min_free
        needed_snap = size + settings.disk_min_free
        if host_disk["free"] < needed_host:
            raise RuntimeError(
                f"磁盘空间不足：宿主剩余 {_fmt(host_disk['free'])}，导入需约 {_fmt(needed_host)}。"
                "请先删除旧数据或在 ModelScope 上清理备份"
            )
        if snap_disk["free"] < needed_snap:
            raise RuntimeError(
                f"快照目录空间不足：剩余 {_fmt(snap_disk['free'])}，需要 {_fmt(needed_snap)}"
            )
        await _task.set("checking", 5, f"空间充足（宿主剩余 {_fmt(host_disk['free'])}），开始下载 {file}")

        # 3. 下载（流式，带进度）
        await _task.set("downloading", 8, f"下载中 0 / {_fmt(size)}...")
        url = monitor.modelscope_download_url(ns, ds, match["path"])
        done = 0
        async with httpx.AsyncClient(timeout=httpx.Timeout(900.0, connect=30.0), follow_redirects=True) as client:
            async with client.stream("GET", url) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length") or size or 0) or size
                if not total:
                    total = size
                with open(tmp, "wb") as f:
                    async for chunk in r.aiter_bytes(256 * 1024):
                        f.write(chunk)
                        done += len(chunk)
                        if total:
                            pct = 8 + (done / total) * 72
                            await _task.set("downloading", pct, f"下载中 {_fmt(done)} / {_fmt(total)}")
        if done < size * 0.9:
            raise RuntimeError(f"下载不完整：{_fmt(done)} / {_fmt(size)}")
        os.replace(tmp, dest)
        await _task.set("downloading", 82, f"下载完成（{_fmt(size)}），快照已就位")

        # 4. 删除旧库（可选）
        if delete_existing:
            await _task.set("deleting", 85, f"正在删除旧集合 {coll}...")
            async with httpx.AsyncClient(timeout=30) as client:
                status, data = await _qdrant_json(client, "DELETE", f"/collections/{coll}?wait=true")
            if status not in (200, 204):
                raise RuntimeError(f"删除旧集合失败 HTTP {status}")

        # 5. 恢复快照（wait=false，后台轮询）
        await _task.set("restoring", 88, "正在恢复快照，通常需要 3-10 分钟...")
        location = f"/qdrant/storage/snapshots/{os.path.basename(dest)}"
        async with httpx.AsyncClient(timeout=30) as client:
            status, data = await _qdrant_json(
                client, "POST", f"/collections/{coll}/snapshots/restore?wait=false&priority=snapshot",
                json={"location": location},
            )
        if status not in (200, 202):
            raise RuntimeError(f"发起恢复失败 HTTP {status}: {data}")

        # 6. 轮询集合状态直到可用
        deadline = time.time() + settings.import_timeout
        last_count = 0
        stable = 0
        while time.time() < deadline:
            await asyncio.sleep(5)
            info = await asyncio.to_thread(monitor.qdrant_collection_info, coll)
            count = info.get("points_count", 0) if info.get("exists") else 0
            if count > 0:
                if count == last_count:
                    stable += 1
                else:
                    stable = 0
                last_count = count
                elapsed_pct = min(90.0, 88 + (time.time() - (deadline - settings.import_timeout)) / settings.import_timeout * 8)
                await _task.set("restoring", elapsed_pct, f"恢复中，当前 {count} 条...")
                if stable >= 2:
                    break
            else:
                await _task.set("restoring", 88, "恢复中（Qdrant 正在加载快照）...")
        else:
            raise RuntimeError("恢复超时，请查看服务器日志")

        # 7. 清理临时快照，释放磁盘
        await _task.set("cleaning", 96, "清理临时快照文件...")
        try:
            if os.path.exists(dest):
                os.remove(dest)
            for name in os.listdir(snapshot_dir):
                if name.endswith(".snapshot"):
                    os.remove(os.path.join(snapshot_dir, name))
        except Exception:
            pass

        info = await asyncio.to_thread(monitor.qdrant_collection_info, coll)
        await _task.done(
            f"导入完成：{coll} 现有 {info.get('points_count', 0)} 条向量，"
            f"磁盘剩余 {_fmt((await asyncio.to_thread(monitor.disk_usage, '/'))['free'])}"
        )
    except Exception as e:
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except Exception:
            pass
        await _task.fail(str(e))
