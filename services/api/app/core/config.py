"""Application settings loaded from environment (never commit secrets)."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "TicketHound API"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg://tickethound:tickethound@localhost:5432/tickethound"

    # CORS — local Next.js default; override via CORS_ORIGINS comma-separated
    cors_origins: str = "http://localhost:43123,http://127.0.0.1:43123"

    # Data-mode flags (Phase 0)
    demo_mode: bool = True
    provider_demo_enabled: bool = True
    provider_ticketmaster_enabled: bool = False

    # Reserved for Phase 1+ (loaded only when enabled; never log the value)
    ticketmaster_api_key: str | None = None

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
