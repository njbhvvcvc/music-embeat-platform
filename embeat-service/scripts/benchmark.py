"""
性能基准测试：测试 Embeat 推荐引擎的延迟和吞吐量。

用法:
    python scripts/benchmark.py
    python scripts/benchmark.py --seed 5pIcwtJYNJx93l420oR2Vm --top-k 20
"""

import argparse
import time
import statistics
from httpx import Client


def parse_args():
    parser = argparse.ArgumentParser(description="Embeat 基准测试")
    parser.add_argument("--host", default="http://localhost:7860")
    parser.add_argument("--seed", default="5pIcwtJYNJx93l420oR2Vm")
    parser.add_argument("--top-k", type=int, default=20)
    parser.add_argument("--runs", type=int, default=10)
    return parser.parse_args()


def main():
    args = parse_args()
    client = Client(base_url=args.host, timeout=30)

    print(f"📊 Embeat 基准测试")
    print(f"   目标: {args.host}")
    print(f"   种子: {args.seed}")
    print(f"   Top-K: {args.top_k}")
    print(f"   测试次数: {args.runs}")
    print()

    # 1. 健康检查
    resp = client.get("/health")
    assert resp.status_code == 200, f"健康检查失败: {resp.text}"
    print("✅ 健康检查通过")

    # 2. 延迟测试
    latencies = []
    for i in range(args.runs):
        start = time.time()
        resp = client.post(
            "/api/v1/recommend",
            json={"seed": args.seed, "top_k": args.top_k},
        )
        elapsed = (time.time() - start) * 1000
        latencies.append(elapsed)
        result = resp.json()
        tracks = result.get("data", [])
        print(f"   第 {i+1:2d} 次: {elapsed:6.0f}ms, 返回 {len(tracks)} 条")

    print()
    print(f"📈 延迟统计 (ms):")
    print(f"   最小:  {min(latencies):.0f}")
    print(f"   最大:  {max(latencies):.0f}")
    print(f"   平均:  {statistics.mean(latencies):.0f}")
    if len(latencies) > 1:
        print(f"   P50:   {statistics.median(latencies):.0f}")
        print(f"   P99:   {sorted(latencies)[int(args.runs * 0.99) - 1]:.0f}")

    # 3. 向量查询测试
    print()
    start = time.time()
    resp = client.post("/api/v1/vector", json={"track_id": args.seed})
    vec_elapsed = (time.time() - start) * 1000
    vec = resp.json().get("data", [])
    print(f"📈 向量查询: {vec_elapsed:.0f}ms, 维度: {len(vec)}")

    print()
    print("✅ 基准测试完成")


if __name__ == "__main__":
    main()