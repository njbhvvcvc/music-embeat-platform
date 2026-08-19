"""主机监控：CPU / 内存 / 磁盘 / 容器 / Qdrant 集合实时数据。

网关容器内读 /proc 拿到宿主机级 CPU 与内存；磁盘用 /proc/mounts + os.statvfs；
容器级指标走 docker socket（compose 已把 /var/run/docker.sock 挂进网关）。
"""
import os
import shutil
import time

import httpx

from app.config import settings

_cpu_last: tuple[float, int, int] | None = None


def _read_cpu_times() -> tuple[int, int]:
    """从 /proc/stat 读取宿主 CPU 计数，返回 (idle, total)。"""
    try:
        with open("/proc/stat") as f:
            for line in f:
                if line.startswith("cpu "):
                    parts = line.split()
                    nums = [int(x) for x in parts[1:9]]
                    idle = nums[3] + nums[4]
                    return idle, sum(nums)
    except Exception:
        pass
    return 0, 0


def host_cpu_percent() -> float:
    """基于上次采样的 CPU 使用率（0-100）。"""
    global _cpu_last
    now = time.time()
    idle, total = _read_cpu_times()
    if _cpu_last:
        t0, idle0, total0 = _cpu_last
        dt = now - t0
        if dt >= 0.2 and total > total0:
            d_total = total - total0
            d_idle = idle - idle0
            pct = (d_total - d_idle) / d_total * 100
            _cpu_last = (now, idle, total)
            return round(max(0.0, min(100.0, pct)), 1)
    _cpu_last = (now, idle, total)
    return 0.0


def host_memory() -> dict:
    """宿主内存占用（KB + 百分比）。"""
    info: dict[str, int] = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if ":" in line:
                    key, rest = line.split(":", 1)
                    parts = rest.split()
                    if parts:
                        try:
                            info[key.strip()] = int(parts[0])
                        except ValueError:
                            pass
    except Exception:
        pass
    total = info.get("MemTotal", 0)
    available = info.get("MemAvailable", info.get("MemFree", 0))
    used = max(0, total - available)
    return {
        "total_kb": total,
        "used_kb": used,
        "free_kb": available,
        "percent": round(used / total * 100, 1) if total else 0.0,
    }


def disk_usage(path: str = "/") -> dict:
    """磁盘占用（字节 + 百分比）。"""
    try:
        u = shutil.disk_usage(path)
        return {
            "path": path,
            "total": u.total,
            "used": u.used,
            "free": u.free,
            "percent": round(u.used / u.total * 100, 1) if u.total else 0.0,
        }
    except Exception:
        return {"path": path, "total": 0, "used": 0, "free": 0, "percent": 0.0}


def qdrant_collection_info(collection: str | None = None) -> dict:
    """查询 Qdrant 集合信息。"""
    name = collection or settings.qdrant_collection
    base = settings.qdrant_base
    try:
        with httpx.Client(timeout=8) as client:
            r = client.get(f"{base}/collections/{name}")
            if r.status_code == 404:
                return {"name": name, "exists": False}
            r.raise_for_status()
            result = r.json().get("result", {})
            config = result.get("config", {}).get("params", {})
            return {
                "name": name,
                "exists": True,
                "status": result.get("status", ""),
                "points_count": result.get("points_count", 0),
                "vectors_count": result.get("vectors_count", 0),
                "segments_count": result.get("segments_count", 0),
                "dimension": (config.get("vectors", {}) or {}).get("size", 0),
            }
    except httpx.HTTPError as e:
        return {"name": name, "exists": False, "error": f"qdrant 不可达: {e}"}
    except Exception as e:
        return {"name": name, "exists": False, "error": str(e)}


def modelscope_list_files(namespace: str, dataset: str) -> list[dict]:
    """列出 ModelScope 数据集根目录下的文件（含大小）。"""
    url = f"https://modelscope.cn/api/v1/datasets/{namespace}/{dataset}/repo/tree?Revision=master&Recursive=true"
    try:
        with httpx.Client(timeout=15) as client:
            r = client.get(url)
            r.raise_for_status()
            data = r.json()
            files = data.get("Data", {}).get("Files", data.get("data", {}).get("Files", []))
            if not isinstance(files, list):
                files = data.get("Files", []) or []
            result = []
            for f in files:
                if f.get("Type", f.get("type", "")) == "blob":
                    result.append({
                        "path": f.get("Path", f.get("path", "")),
                        "size": f.get("Size", f.get("size", 0)) or 0,
                    })
            return result
    except Exception:
        return []


def modelscope_download_url(namespace: str, dataset: str, file_path: str) -> str:
    """构造 ModelScope 文件下载地址。"""
    from urllib.parse import quote
    return (
        f"https://modelscope.cn/api/v1/datasets/{namespace}/{dataset}/repo"
        f"?Revision=master&FilePath={quote(file_path)}"
    )
