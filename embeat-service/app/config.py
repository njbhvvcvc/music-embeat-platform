from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    embeat_port: int = 7860
    embeat_model_path: str = "/app/checkpoints/EmbeatMLP"
    embeat_model_url: str = "https://raw.githubusercontent.com/gdstudio-org/Embeat/main/checkpoints/EmbeatMLP/model.pt"
    embeat_disable_track2vec: bool = True
    embeat_top_k: int = 20
    embeat_channels: str = "similar,popular,same_artist,related_artist"
    qdrant_host: str = "qdrant"
    qdrant_port: int = 6333
    qdrant_collection: str = "embeat_45m"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()