"""Environment-driven configuration for ResearchMind."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_env: str = "development"
    log_level: str = "INFO"

    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-3.8-flash"
    gemini_embedding_model: str = "gemini-embedding-2"
    gemini_fallback_model: str = "gemini-3.5-flash-lite"

    telegram_bot_token: SecretStr | None = None
    telegram_allowed_user_ids: str = ""

    gmail_client_secrets_file: Path = Path("secrets/gmail-client-secrets.json")
    gmail_token_file: Path = Path(".local/gmail-token.json")
    gmail_read_only: bool = True
    gmail_allow_draft_creation: bool = False

    database_path: Path = Path(".local/researchmind.sqlite3")
    chroma_path: Path = Path(".local/chroma")
    embedding_cache_path: Path = Path(".local/embedding_cache.sqlite3")
    documents_path: Path = Path("data/raw")

    max_critic_iterations: int = Field(default=3, ge=1, le=3)
    request_timeout_seconds: int = Field(default=45, ge=5, le=180)
    max_requests_per_minute: int = Field(default=8, ge=1, le=60)

    @property
    def allowed_telegram_user_ids(self) -> set[int]:
        """Parse comma-separated Telegram user IDs from configuration."""
        return {
            int(item.strip()) for item in self.telegram_allowed_user_ids.split(",") if item.strip()
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object."""
    return Settings()
