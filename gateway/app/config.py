from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str = "change-me"
    admin_password: str = "embeat123"
    gd_api_base: str = "https://music-api.gdstudio.xyz/api.php"
    gd_api_rate_limit: int = 50
    gd_api_rate_window: int = 300
    embeat_base: str = "http://embeat:7860"
    profile_base: str = "http://profile:8090"
    qdrant_base: str = "http://qdrant:6333"
    qdrant_collection: str = "embeat_45m"
    # 数据集管线
    modelscope_namespace: str = "xuliuyangsai"
    modelscope_dataset: str = "embeat-qdrant-backup"
    snapshot_dir: str = "/snapshots"
    # 磁盘保护：剩余空间低于该阈值（字节）禁止导入
    disk_min_free: int = 1 * 1024 * 1024 * 1024
    # 导入任务超时（秒）
    import_timeout: int = 1800

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()