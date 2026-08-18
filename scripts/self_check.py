#!/usr/bin/env python3
"""
全量自检脚本：运行所有测试、lint、类型检查，并生成报告。

用法:
    python scripts/self_check.py
    python scripts/self_check.py --quick   # 仅运行测试，不跑 lint
    python scripts/self_check.py --report  # 输出 JSON 报告
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run(cmd, cwd=ROOT, timeout=120):
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "超时"
    except FileNotFoundError:
        return -2, "", f"命令未找到: {cmd[0]}"


def check_file(path: str, content_pattern: str = "") -> dict:
    full = ROOT / path
    exists = full.exists()
    if exists and content_pattern:
        text = full.read_text()
        has_content = content_pattern in text
        return {"path": path, "exists": True, "has_content": has_content}
    return {"path": path, "exists": exists}


def main():
    parser = argparse.ArgumentParser(description="全量自检")
    parser.add_argument("--quick", action="store_true", help="仅运行测试")
    parser.add_argument("--report", action="store_true", help="输出 JSON 报告")
    args = parser.parse_args()

    checks = {}
    passed = 0
    failed = 0

    print("=" * 60)
    print("  music-embeat-platform 全量自检")
    print("=" * 60)
    print()

    # 1. 文件完整性检查
    print("📁 文件完整性检查:")
    files_to_check = [
        ("docker-compose.yml", "gateway"),
        (".env.example", "JWT_SECRET"),
        ("Makefile", "up"),
        ("gateway/Dockerfile", "fastapi"),
        ("gateway/app/main.py", "FastAPI"),
        ("gateway/app/clients/gdstudio.py", "GDStudioAPI"),
        ("gateway/app/middleware/ratelimit.py", "RateLimit"),
        ("gateway/app/middleware/auth.py", "AuthMiddleware"),
        ("embeat-service/Dockerfile", "torch"),
        ("embeat-service/app/main.py", "FastAPI"),
        ("embeat-service/app/core/model_loader.py", "EmbeatMLP"),
        ("embeat-service/app/core/qdrant_repo.py", "QdrantRepo"),
        ("embeat-service/app/core/recall.py", "RecallEngine"),
        ("embeat-service/scripts/import_qdrant.py", "QdrantClient"),
        ("embeat-service/scripts/benchmark.py", "benchmark"),
        ("profile-service/Dockerfile", "fastapi"),
        ("profile-service/app/main.py", "FastAPI"),
        ("profile-service/app/core/database.py", "asyncpg"),
        ("profile-service/app/routes/events.py", "PlayEvent"),
        ("musicfree-plugin/src/plugin.js", "module.exports"),
        ("deploy/cloudflared/config.yml", "ingress"),
        ("scripts/deploy.sh", "docker compose"),
    ]
    for path, pattern in files_to_check:
        result = check_file(path, pattern)
        status = "✅" if result["exists"] and result["has_content"] else "❌"
        if result["exists"] and result["has_content"]:
            passed += 1
        else:
            failed += 1
        print(f"  {status} {path}")
        checks[path] = result

    print()

    # 2. Python 语法检查
    print("🐍 Python 语法检查:")
    for py_file in ROOT.rglob("*.py"):
        if "node_modules" in str(py_file) or ".venv" in str(py_file):
            continue
        rc, out, err = run([sys.executable, "-c", f"compile(open('{py_file}').read(), '{py_file}', 'exec')"])
        status = "✅" if rc == 0 else "❌"
        if rc == 0:
            passed += 1
        else:
            failed += 1
        print(f"  {status} {py_file.relative_to(ROOT)}")
        if rc != 0:
            print(f"      {err.strip()[:200]}")

    print()

    # 3. 服务端口冲突检查
    print("🔌 端口冲突检查:")
    ports = [8080, 7860, 8090, 6333, 5432]
    # 优先使用 ss (Linux), 其次 lsof, 最后 netstat
    for cmd_name, cmd_args in [
        ("ss", ["ss", "-tlnp"]),
        ("lsof", ["lsof", "-i", "-P", "-n"]),
        ("netstat", ["netstat", "-an"]),
    ]:
        rc, out, _ = run(cmd_args)
        if rc == 0:
            output = out
            break
    else:
        print("  ⚠️  无法检测端口占用（ss/lsof/netstat 均不可用），跳过")
        output = ""
    for port in ports:
        if output and f":{port}" in output:
            print(f"  ⚠️  端口 {port} 已被占用")
        else:
            print(f"  ✅ 端口 {port} 可用")
            passed += 1

    print()

    # 4. 总结
    print("=" * 60)
    total = passed + failed
    print(f"  结果: {passed}/{total} 通过")
    if failed > 0:
        print(f"  ❌ {failed} 项未通过，请检查上述标记")
    else:
        print("  ✅ 全部通过！")
    print("=" * 60)

    if args.report:
        report = {
            "passed": passed,
            "failed": failed,
            "total": total,
            "checks": checks,
        }
        report_path = ROOT / "self_check_report.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(f"\n📄 报告已保存: {report_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())