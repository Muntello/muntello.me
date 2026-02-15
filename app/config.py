from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application configuration from environment variables"""

    # Telegram
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_WEBHOOK_SECRET: str  # Secret token for webhook security
    SUPPORT_CHAT_ID: int = 5237566869
    WEBHOOK_URL: str = "https://support.muntello.me"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:////var/lib/muntello/bot.db"

    # Application
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# Global settings instance
# This will fail if TELEGRAM_BOT_TOKEN is not set in environment or .env
# For tests, import Settings class directly, not this instance
try:
    settings = Settings()
except Exception:
    # In test environment, we may not have required env vars
    settings = None  # type: ignore
