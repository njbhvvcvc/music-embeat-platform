"""
全量/子集导入脚本：将 HF Dataset 导入 Qdrant 向量库。

用法:
    python scripts/import_qdrant.py --full          # 全量 45M
    python scripts/import_qdrant.py --cn-only        # 华语子集
    python scripts/import_qdrant.py --sample 1000    # 采样 1000 条测试
"""

import argparse
import json
import os
import sys
import logging
from pathlib import Path
from typing import Generator

import torch
from datasets import load_dataset
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.core.model_loader import ModelLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CN_GENRES = {
    "c-pop", "mandopop", "taiwan pop", "zhongguo feng",
    "cantopop", "hokkien pop", "chinese r&b", "chinese idol pop",
    "chinese pop", "chinese rock", "c-pop girl group", "c-pop boy group",
    "mandopop dance", "mandopop ballad", "chinese indie",
}

JP_GENRES = {
    "j-pop", "j-rock", "japanese idol", "anime", "japanese vgm",
    "japanese hip hop", "japanese metal", "japanese jazz", "j-idol",
    "city pop", "japanese indie", "japanese punk", "denpa",
}

EN_GENRES = {
    "pop", "rock", "hip hop", "country", "r&b", "soul", "funk",
    "electronic", "house", "techno", "indie", "alternative", "metal",
    "punk", "folk", "blues", "jazz", "classical", "edm", "trap",
}

KR_GENRES = {
    "k-pop", "k-rock", "korean idol", "k-hip hop", "k-ballad",
    "k-indie", "k-r&b", "k-trot",
}

GENRES_MAP = {
    "cn": CN_GENRES,
    "jp": JP_GENRES,
    "en": EN_GENRES,
    "kr": KR_GENRES,
}


def parse_args():
    parser = argparse.ArgumentParser(description="导入 HF Dataset 到 Qdrant")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--full", action="store_true", help="全量导入 45M")
    group.add_argument("--cn-only", action="store_true", help="仅华语子集")
    group.add_argument("--jp-only", action="store_true", help="仅日语子集")
    group.add_argument("--en-only", action="store_true", help="仅英语子集")
    group.add_argument("--kr-only", action="store_true", help="仅韩语子集")
    group.add_argument("--sample", type=int, default=0, help="采样条数（测试用）")
    parser.add_argument("--dataset", default="GD-Studio/embeat_45m_spotify_tracks")
    parser.add_argument("--qdrant-host", default="localhost")
    parser.add_argument("--qdrant-port", type=int, default=6333)
    parser.add_argument("--collection", default="embeat_45m")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--model-path", default="/app/checkpoints/EmbeatMLP", help="模型权重路径 (Docker: /app/checkpoints/EmbeatMLP)")
    # 4GB 优化参数
    parser.add_argument("--indexing-threshold", type=int, default=10000,
                        help="多少条后开始建索引 (4GB 版设很大如 10000000 表示导入时不建)")
    parser.add_argument("--memmap-threshold", type=int, default=20000,
                        help="多少条后改用 mmap 存储 (0 = 始终 mmap, 省内存)")
    return parser.parse_args()


def track_generator(dataset, args) -> Generator[dict, None, None]:
    # 确定筛选语种
    filter_genres = None
    if args.cn_only:
        filter_genres = GENRES_MAP["cn"]
    elif args.jp_only:
        filter_genres = GENRES_MAP["jp"]
    elif args.en_only:
        filter_genres = GENRES_MAP["en"]
    elif args.kr_only:
        filter_genres = GENRES_MAP["kr"]

    for i, item in enumerate(dataset):
        if args.sample and i >= args.sample:
            break
        if filter_genres:
            genres = item.get("artist_genres", "")
            if not any(g in genres for g in filter_genres):
                continue
        yield item


def vectorize(item: dict, model: ModelLoader | None = None) -> list[float]:
    """生成向量：优先使用模型，否则用简单归一化"""
    if model and model.is_loaded:
        return model.encode_from_features(item)

    # 回退：简单归一化
    discrete = torch.tensor([
        item.get("key", 0) / 11.0,
        item.get("mode", 0),
        (item.get("time_signature", 4) - 3) / 4.0,
        min(item.get("tempo", 120) / 200.0, 1.0),
    ] + [0.0] * 16, dtype=torch.float32)
    acoustic = torch.tensor([
        item.get("energy", 0.5),
        item.get("valence", 0.5),
        item.get("danceability", 0.5),
        (item.get("loudness", -10.0) + 60.0) / 60.0,
        item.get("speechiness", 0.0),
        item.get("acousticness", 0.5),
        item.get("instrumentalness", 0.0),
    ], dtype=torch.float32)
    with torch.no_grad():
        d = torch.nn.functional.normalize(discrete.unsqueeze(0), dim=1).squeeze(0)
        a = torch.nn.functional.normalize(acoustic.unsqueeze(0), dim=1).squeeze(0)
        vec = torch.cat([d, a]).tolist()
    return vec


def main():
    args = parse_args()

    # 加载模型
    model = None
    if args.model_path:
        os.environ["EMBEAT_MODEL_PATH"] = args.model_path
        model = ModelLoader()
        model.load()

    client = QdrantClient(
        host=args.qdrant_host,
        port=args.qdrant_port,
        timeout=60,
        prefer_grpc=False,
    )

    # 创建 collection
    collections = [c.name for c in client.get_collections().collections]
    if args.collection not in collections:
        client.create_collection(
            collection_name=args.collection,
            vectors_config=VectorParams(size=64, distance=Distance.COSINE),
            optimizers_config=models.OptimizersConfigDiff(
                indexing_threshold=args.indexing_threshold,
                memmap_threshold=args.memmap_threshold,
            ),
            hnsw_config=models.HnswConfigDiff(
                m=16,
                ef_construct=200,
                full_scan_threshold=10000,
            ),
        )
        logger.info(f"✅ 创建 Collection: {args.collection}")

    ds = load_dataset(args.dataset, split="train", streaming=True)
    points = []
    count = 0
    errors = 0

    for item in track_generator(ds, args):
        track_id = str(item.get("track_id", ""))
        if not track_id:
            continue

        try:
            vec = vectorize(item, model)
            point = PointStruct(
                id=track_id,
                vector=vec,
                payload={
                    "track_name": item.get("track_name", ""),
                    "artist_name": item.get("artist_name", ""),
                    "album_name": item.get("album_name", ""),
                    "popularity": item.get("popularity", 0),
                    "artist_genres": item.get("artist_genres", ""),
                    "artist_idx": item.get("artist_idx", -1),
                    "isrc": item.get("isrc", ""),
                },
            )
            points.append(point)
            count += 1
        except Exception as e:
            logger.warning(f"Vectorize failed for {track_id}: {e}")
            errors += 1
            continue

        if len(points) >= args.batch_size:
            try:
                client.upsert(collection_name=args.collection, points=points)
                logger.info(f"  已导入 {count} 条...")
            except UnexpectedResponse as e:
                logger.error(f"Upsert failed: {e}")
                errors += len(points)
            points = []

    if points:
        try:
            client.upsert(collection_name=args.collection, points=points)
        except UnexpectedResponse as e:
            logger.error(f"Final upsert failed: {e}")
            errors += len(points)

    logger.info(f"✅ 导入完成，共 {count} 条，错误 {errors} 条")
    logger.info(f"   Collection: {args.collection}")
    logger.info(f"   Qdrant 地址: {args.qdrant_host}:{args.qdrant_port}")


if __name__ == "__main__":
    main()