from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    profile_port: int = 8090
    postgres_db: str = "embeat_profile"
    postgres_user: str = "embeat"
    postgres_password: str = "change-me"
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    embeat_base: str = "http://embeat:7860"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()