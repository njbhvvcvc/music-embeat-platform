"""
导入完成后触发 Qdrant 索引构建。
RAW 4GB 版导入时设了很高的 indexing_threshold（不建索引），
导入完成后用本脚本降低阈值，触发后台建索引。

用法:
    python scripts/build_index.py --collection embeat_45m --threshold 10000
"""
import argparse
import os

from qdrant_client import QdrantClient
from qdrant_client.models import OptimizersConfigDiff


def parse_args():
    parser = argparse.ArgumentParser(description="触发 Qdrant 索引构建")
    parser.add_argument("--qdrant-host", default=os.environ.get("QDRANT_HOST", "localhost"))
    parser.add_argument("--qdrant-port", type=int, default=int(os.environ.get("QDRANT_PORT", 6333)))
    parser.add_argument("--collection", default="embeat_45m")
    parser.add_argument("--threshold", type=int, default=10000, help="降低此阈值触发建索引")
    return parser.parse_args()


def main():
    args = parse_args()
    client = QdrantClient(host=args.qdrant_host, port=args.qdrant_port, timeout=300)

    print(f"🔨 触发集合 {args.collection} 的索引构建 (threshold={args.threshold})...")
    client.update_collection(
        collection_name=args.collection,
        optimizers_config=OptimizersConfigDiff(
            indexing_threshold=args.threshold,
        ),
    )
    print("✅ 已触发，Qdrant 会在后台异步构建索引（视数据量需数分钟到数十分钟）")
    print("   可通过 http://<host>:6333/collections/<name> 查看索引进度")


if __name__ == "__main__":
    main()
