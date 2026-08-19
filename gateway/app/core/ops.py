import asyncio
import re

SERVICES = [
    ("nginx", "embeat-nginx-1"),
    ("gateway", "embeat-gateway-1"),
    ("embeat", "embeat-embeat-1"),
    ("profile", "embeat-profile-1"),
    ("postgres", "embeat-postgres-1"),
    ("qdrant", "embeat-qdrant-1"),
]

SERVICE_NAMES = {label: cid for label, cid in SERVICES}


async def run(cmd: list[str]) -> str:
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    return out.decode(errors="replace")


async def container_states() -> dict[str, str]:
    out = await run(["docker", "ps", "-a", "--format", "{{.Names}}|{{.State}}"])
    states = {}
    for line in out.strip().splitlines():
        parts = line.split("|", 1)
        if len(parts) == 2:
            states[parts[0]] = parts[1]
    return states


async def stop_services(exclude: str = "gateway") -> list[str]:
    targets = [cid for label, cid in SERVICES if label != exclude]
    out = await run(["docker", "stop"] + targets)
    return [l for l in out.strip().splitlines() if l]


async def start_services(exclude: str = "gateway") -> list[str]:
    targets = [cid for label, cid in SERVICES if label != exclude]
    out = await run(["docker", "start"] + targets)
    return [l for l in out.strip().splitlines() if l]


async def container_stats() -> dict[str, dict]:
    """docker stats --no-stream，返回 {容器名: {cpu, mem}}"""
    out = await run(
        ["docker", "stats", "--no-stream", "--format", "{{.Name}}|{{.CPUPerc}}|{{.MemPerc}}"]
    )
    result = {}
    for line in out.strip().splitlines():
        parts = line.split("|")
        if len(parts) == 3:
            result[parts[0]] = {
                "cpu": parts[1].strip().rstrip("%"),
                "mem": parts[2].strip().rstrip("%"),
            }
    return result


def strip_ansi(line: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", line)


def classify_level(line: str) -> str:
    up = line.upper()
    if "ERROR" in up or "TRACEBACK" in up or "FATAL" in up:
        return "ERROR"
    if "WARN" in up or "WARNING" in up:
        return "WARN"
    return "INFO"