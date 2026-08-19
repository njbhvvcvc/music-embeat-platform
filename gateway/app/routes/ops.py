import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import settings
from app.core import ops
from app.core.metrics import metrics

router = APIRouter()


@router.get("/ops/status")
async def ops_status():
    states = await ops.container_states()
    data = [
        {"name": label, "cid": cid, "state": states.get(cid, "absent")}
        for label, cid in ops.SERVICES
    ]
    return {"code": 0, "data": data}


@router.post("/ops/stop")
async def ops_stop():
    stopped = await ops.stop_services(exclude="gateway")
    return {"code": 0, "msg": "站点服务已停止（网关保留）", "data": stopped}


@router.post("/ops/start")
async def ops_start():
    started = await ops.start_services(exclude="gateway")
    return {"code": 0, "msg": "站点服务已启动", "data": started}


@router.get("/ops/logs")
async def ops_logs(service: str = "all", limit: int = 300):
    if service != "all" and service not in ops.SERVICE_NAMES:
        return JSONResponse(status_code=400, content={"code": 400, "msg": "未知服务"})

    targets = [service] if service != "all" else [label for label, _ in ops.SERVICES]
    logs = []
    for s in targets:
        out = await ops.run(["docker", "logs", "--tail", str(limit), ops.SERVICE_NAMES[s]])
        for line in out.splitlines():
            line = ops.strip_ansi(line.strip())
            if not line:
                continue
            logs.append(
                {
                    "service": s,
                    "level": ops.classify_level(line),
                    "msg": line[-400:],
                }
            )
    logs.reverse()
    return {"code": 0, "data": logs}


@router.get("/ops/metrics")
async def ops_metrics():
    from app.core import monitor

    qps, avg_latency = metrics.snapshot()
    try:
        stats = await ops.container_stats()
    except Exception:
        stats = {}
    try:
        states = await ops.container_states()
    except Exception:
        states = {}

    containers = []
    for label, cid in ops.SERVICES:
        st = stats.get(cid, {})
        containers.append({
            "name": label,
            "cid": cid,
            "state": states.get(cid, "unknown"),
            "cpu": st.get("cpu", ""),
            "mem": st.get("mem", ""),
        })

    return {
        "code": 0,
        "cpu_percent": monitor.host_cpu_percent(),
        "memory": monitor.host_memory(),
        "disk": monitor.disk_usage("/"),
        "snapshot_disk": monitor.disk_usage(settings.snapshot_dir),
        "containers": containers,
        "qdrant": monitor.qdrant_collection_info(),
        "qps": qps,
        "avg_latency_ms": avg_latency,
        "now": int(time.time() * 1000),
    }


@router.get("/recommend/stats")
async def recommend_stats():
    qps, avg_latency = metrics.snapshot()

    cpu_percent = 0
    memory_percent = 0
    try:
        stats = await ops.container_stats()
        embeat_stats = stats.get("embeat-embeat-1")
        if embeat_stats:
            cpu_percent = float(embeat_stats.get("cpu", 0) or 0)
            memory_percent = float(embeat_stats.get("mem", 0) or 0)
    except Exception:
        pass

    return {
        "code": 0,
        "cpu_percent": cpu_percent,
        "memory_percent": memory_percent,
        "qps": qps,
        "avg_latency_ms": avg_latency,
    }