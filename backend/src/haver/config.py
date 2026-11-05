"""Runtime settings, read from environment variables or a .env file.

Environment variables win. For local runs from `backend/`, the repository's `../.env` is read.
In Docker, Compose injects the variables and no file is needed.
"""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), env_ignore_empty=True, extra="ignore"
    )

    database_url: str = "postgresql://haver:haver@localhost:5432/haver"
    gemini_api_key: SecretStr | None = None
    groq_api_key: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
