import uuid

_EMBEAT_NS = uuid.UUID("7b1a5b2e-0000-4000-8000-0000000000eb")


def track_id_to_uuid(track_id: str) -> str:
    """Spotify 22 位 base62 track_id 确定性映射为 Qdrant 接受的 UUID。"""
    return str(uuid.uuid5(_EMBEAT_NS, track_id))