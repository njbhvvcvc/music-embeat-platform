"""
召回质量评测：验证推荐结果的准确性和多样性。

用法:
    python scripts/validate_recall.py
    python scripts/validate_recall.py --seed "晴天 - Jay Chou" --top-k 10
"""

import argparse
from httpx import Client


def parse_args():
    parser = argparse.ArgumentParser(description="召回质量评测")
    parser.add_argument("--host", default="http://localhost:7860")
    parser.add_argument("--seed", default="5pIcwtJYNJx93l420oR2Vm")
    parser.add_argument("--top-k", type=int, default=10)
    return parser.parse_args()


def main():
    args = parse_args()
    client = Client(base_url=args.host, timeout=30)

    print(f"🎯 召回质量评测")
    print(f"   种子: {args.seed}")
    print()

    resp = client.post(
        "/api/v1/recommend",
        json={"seed": args.seed, "top_k": args.top_k},
    )
    result = resp.json()
    tracks = result.get("data", [])

    print(f"   推荐结果 ({len(tracks)} 条):")
    print(f"   {'#':>3} {'渠道':<16} {'得分':>6} {'歌曲':<24} {'歌手':<20}")
    print(f"   {'-'*72}")
    for i, t in enumerate(tracks, 1):
        print(
            f"   {i:>3} {t.get('channel',''):<16} "
            f"{t.get('score',0):>6.2f} "
            f"{t.get('title','')[:24]:<24} "
            f"{t.get('artist','')[:20]:<20}"
        )

    channels = set(t.get("channel", "") for t in tracks)
    artists = set(t.get("artist", "") for t in tracks)
    print()
    print(f"📊 多样性指标:")
    print(f"   覆盖渠道数: {len(channels)} ({', '.join(channels)})")
    print(f"   不同歌手数: {len(artists)}")


if __name__ == "__main__":
    main()