from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    jwt_secret: str = "change-me"
    gd_api_base: str = "https://music-api.gdstudio.xyz/api.php"
    gd_api_rate_limit: int = 50
    gd_api_rate_window: int = 300
    embeat_base: str = "http://embeat:7860"
    profile_base: str = "http://profile:8090"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()