"""Runtime settings, read from environment variables or the repository's .env file."""

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    database_url: str = "postgresql://haver:haver@localhost:5432/haver"
    gemini_api_key: SecretStr | None = None
    groq_api_key: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
