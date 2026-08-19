"""
56M 补充导入脚本：以 GildasLeDrogoff/spotify-huge-track-analysis-dataset 为主源，
与 embeat_45m 按 track_id join 补全流派/艺人ID/ISRC/拍号；
join 不到的曲目用 CJK 启发式（汉字/假名/谚文）猜测流派，作为补充。
去重合并到现有 collection（point id = UUID(track_id)，upsert 天然去重）。

用法:
    python scripts/import_56m.py --cn-only          # 华语子集
    python scripts/import_56m.py --cn-only --jp-only  # 中+日
    python scripts/import_56m.py --cn-only --sample 1000   # 采样测试
"""

import argparse
import logging
import os
import re
import sqlite3
import sys
from pathlib import Path

from datasets import load_dataset
from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, PointStruct, VectorParams
try:
    from qdrant_client.exceptions import UnexpectedResponse
except ImportError:  # qdrant-client < 1.14
    from qdrant_client.http.exceptions import UnexpectedResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.core.model_loader import ModelLoader
from app.core.track_id import track_id_to_uuid

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

GENRES_MAP = {"cn": CN_GENRES, "jp": JP_GENRES, "en": EN_GENRES, "kr": KR_GENRES}

# CJK 字符范围
_RE_HANGUL = re.compile(r"[\uAC00-\uD7AF]")          # 谚文（韩文）
_RE_KANA = re.compile(r"[\u3040-\u30FF\u31F0-\u31FF]")  # 假名（日文）
_RE_HANZI = re.compile(r"[\u4E00-\u9FFF]")           # 汉字


def guess_cjk_genre(artist: str, title: str) -> str | None:
    """CJK 启发式猜流派：韩文 -> k-pop，假名 -> j-pop，汉字 -> mandopop"""
    text = f"{artist} {title}"
    if _RE_HANGUL.search(text):
        return "k-pop"
    if _RE_KANA.search(text):
        return "j-pop"
    if _RE_HANZI.search(text):
        return "mandopop"
    return None


def parse_args():
    parser = argparse.ArgumentParser(description="56M 数据集补充导入")
    parser.add_argument("--dataset", default="GildasLeDrogoff/spotify-huge-track-analysis-dataset")
    parser.add_argument("--join-dataset", default="GD-Studio/embeat_45m_spotify_tracks",
                        help="用于补流派/艺人ID/ISRC/拍号的基础数据集")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--cn-only", action="store_true")
    group.add_argument("--jp-only", action="store_true")
    group.add_argument("--en-only", action="store_true")
    group.add_argument("--kr-only", action="store_true")
    group.add_argument("--sample", type=int, default=0, help="采样条数（测试用，走完整 join 流程）")
    parser.add_argument("--qdrant-host", default=os.environ.get("QDRANT_HOST", "localhost"))
    parser.add_argument("--qdrant-port", type=int, default=int(os.environ.get("QDRANT_PORT", "6333")))
    parser.add_argument("--collection", default="embeat_45m")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--model-path", default="/app/checkpoints/EmbeatMLP")
    parser.add_argument("--join-db", default="/tmp/embeat_join.db", help="join 查询库位置")
    parser.add_argument("--rebuild-join", action="store_true", help="重建 join 查询库")
    parser.add_argument("--no-cjk", action="store_true", help="关闭 CJK 启发式（join 不到就跳过）")
    parser.add_argument("--indexing-threshold", type=int, default=10000)
    parser.add_argument("--memmap-threshold", type=int, default=20000)
    return parser.parse_args()


def build_join_db(args, target_genres: set) -> sqlite3.Connection:
    """把 embeat_45m 中命中目标流派的曲目写进 sqlite 查询库"""
    if not args.rebuild_join and os.path.exists(args.join_db):
        logger.info(f"复用 join 库: {args.join_db}")
        return sqlite3.connect(args.join_db)

    conn = sqlite3.connect(args.join_db)
    conn.execute("CREATE TABLE IF NOT EXISTS join_map ("
                 "track_id TEXT PRIMARY KEY,"
                 "artist_genres TEXT, artist_idx INT, isrc TEXT, time_signature INT)")
    if args.rebuild_join:
        conn.execute("DROP TABLE IF EXISTS join_map")
        conn.execute("CREATE TABLE join_map ("
                     "track_id TEXT PRIMARY KEY,"
                     "artist_genres TEXT, artist_idx INT, isrc TEXT, time_signature INT)")

    ds = load_dataset(args.join_dataset, split="train", streaming=True)
    n = 0
    for item in ds:
        genres = item.get("artist_genres") or ""
        if not any(g in genres for g in target_genres):
            continue
        track_id = str(item.get("track_id", ""))
        if not track_id:
            continue
        conn.execute(
            "INSERT OR IGNORE INTO join_map VALUES (?,?,?,?,?)",
            (track_id, genres, item.get("artist_idx", -1),
             item.get("isrc", ""), item.get("time_signature", 4)),
        )
        n += 1
        if n % 200000 == 0:
            conn.commit()
            logger.info(f"  join 库已写入 {n} 条...")
    conn.commit()
    logger.info(f"✅ join 库构建完成: {n} 条 -> {args.join_db}")
    return conn


def vectorize(item: dict, model: ModelLoader | None = None) -> list[float]:
    """生成向量：优先使用模型"""
    if model and model.is_loaded:
        return model.encode_from_features(item)
    raise RuntimeError("Model not loaded")


def main():
    args = parse_args()

    if args.sample:
        target_genres = CN_GENRES | JP_GENRES | KR_GENRES
    elif args.cn_only:
        target_genres = CN_GENRES
    elif args.jp_only:
        target_genres = JP_GENRES
    elif args.en_only:
        target_genres = EN_GENRES
    elif args.kr_only:
        target_genres = KR_GENRES
    else:
        target_genres = CN_GENRES | JP_GENRES | KR_GENRES

    model = ModelLoader()
    model.load()

    client = QdrantClient(host=args.qdrant_host, port=args.qdrant_port, timeout=60, prefer_grpc=False)

    collections = [c.name for c in client.get_collections().collections]
    if args.collection not in collections:
        client.create_collection(
            collection_name=args.collection,
            vectors_config=VectorParams(size=64, distance=Distance.COSINE),
            optimizers_config=models.OptimizersConfigDiff(
                indexing_threshold=args.indexing_threshold,
                memmap_threshold=args.memmap_threshold,
            ),
            hnsw_config=models.HnswConfigDiff(m=16, ef_construct=200, full_scan_threshold=10000),
        )
        logger.info(f"✅ 创建 Collection: {args.collection}")

    join_conn = build_join_db(args, target_genres)
    lookup = join_conn.cursor()

    ds = load_dataset(args.dataset, split="train", streaming=True)
    points = []
    count = 0
    joined = 0
    cjk = 0
    errors = 0

    for i, item in enumerate(ds):
        if args.sample and i >= args.sample:
            break
        track_id = str(item.get("track_id", ""))
        if not track_id:
            continue

        # 从 join 库取基础字段
        lookup.execute(
            "SELECT artist_genres, artist_idx, isrc, time_signature FROM join_map WHERE track_id=?",
            (track_id,),
        )
        row = lookup.fetchone()

        if row:
            artist_genres, artist_idx, isrc, time_signature = row
            joined += 1
        else:
            if args.no_cjk:
                continue
            guessed = guess_cjk_genre(str(item.get("artist_name", "")),
                                      str(item.get("track_name", "")))
            if not guessed:
                continue
            artist_genres = guessed
            artist_idx = -1
            isrc = ""
            time_signature = 4
            cjk += 1

        # 非采样模式下按目标流派过滤（join 库已保证命中；CJK 补充的按 guess 命中）
        if not args.sample and not any(g in artist_genres for g in target_genres):
            continue

        features = {
            "key": item.get("key", 0),
            "mode": item.get("mode", 0),
            "time_signature": time_signature,
            "tempo": item.get("tempo", 120),
            "energy": item.get("energy", 0.5),
            "valence": item.get("valence", 0.5),
            "danceability": item.get("danceability", 0.5),
            "loudness": item.get("loudness", -10.0),
            "speechiness": item.get("speechiness", 0.0),
            "acousticness": item.get("acousticness", 0.5),
            "instrumentalness": item.get("instrumentalness", 0.0),
        }

        try:
            vec = vectorize(features, model)
        except Exception as e:
            logger.warning(f"Vectorize failed for {track_id}: {e}")
            errors += 1
            continue

        point = PointStruct(
            id=track_id_to_uuid(track_id),
            vector=vec,
            payload={
                "track_id": track_id,
                "track_name": item.get("track_name", ""),
                "artist_name": item.get("artist_name", ""),
                "album_name": item.get("album_name", ""),
                "popularity": item.get("track_popularity", 0),
                "artist_genres": artist_genres,
                "artist_idx": artist_idx,
                "isrc": isrc,
            },
        )
        points.append(point)
        count += 1

        if len(points) >= args.batch_size:
            try:
                client.upsert(collection_name=args.collection, points=points)
                logger.info(f"  已导入 {count} 条 (join={joined}, cjk={cjk})...")
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

    join_conn.close()
    logger.info(f"✅ 导入完成: 共 {count} 条, join 补齐 {joined} 条, CJK 补充 {cjk} 条, 错误 {errors} 条")
    logger.info(f"   Collection: {args.collection}")


if __name__ == "__main__":
    main()
