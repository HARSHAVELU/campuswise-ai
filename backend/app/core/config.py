from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CampusWise AI"
    environment: str = Field(default="development")
    debug: bool = Field(default=True)

    api_prefix: str = "/api/v1"

    database_url: str = Field(
        default="postgresql+psycopg://campuswise:campuswise@localhost:5432/campuswise"
    )
    database_echo: bool = Field(default=False)

    redis_url: str = Field(default="redis://localhost:6379/0")

    jwt_secret_key: str = Field(default="change-me-in-env")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=60 * 24)

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    anthropic_api_key: str | None = Field(default=None)
    anthropic_model: str = Field(default="claude-sonnet-5")

    voyage_api_key: str | None = Field(default=None)
    voyage_embedding_model: str = Field(default="voyage-3-lite")
    voyage_rerank_model: str = Field(default="rerank-2-lite")


@lru_cache
def get_settings() -> Settings:
    return Settings()
