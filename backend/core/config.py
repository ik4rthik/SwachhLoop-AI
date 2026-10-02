"""
SwachhLoop AI — Core Configuration
===================================
Loads all application settings from environment variables / .env file.
Using pydantic-settings ensures type safety and clear documentation
of every knob the application exposes.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Central settings object for SwachhLoop AI.

    Values are loaded in this order (highest priority first):
      1. Actual environment variables
      2. .env file (if present)
      3. Default values defined here
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",        # silently ignore unknown env vars
    )

    # --- Application ---
    app_name: str = Field(default="SwachhLoop AI")
    app_version: str = Field(default="0.3.0")
    app_env: str = Field(default="development")  # development | staging | production
    debug: bool = Field(default=True)

    # --- Backend Server ---
    backend_host: str = Field(default="0.0.0.0")
    backend_port: int = Field(default=8000)

    # --- Frontend ---
    frontend_port: int = Field(default=8501)
    api_base_url: str = Field(default="http://localhost:8000")

    # --- Database ---
    # For local development use SQLite:   sqlite+aiosqlite:///./swachhloop.db
    # For production use PostgreSQL:      postgresql+asyncpg://user:pass@host:5432/db
    database_url: str = Field(
        default="sqlite+aiosqlite:///./swachhloop.db"
    )

    # --- Security (Phase 3) ---
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    secret_key: str = Field(default="CHANGE_ME_generate_a_secure_random_key_32_chars")
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60)

    # --- Storage (Phase 3+) ---
    # local: store uploads on disk under uploads/
    # s3:    store on AWS S3 (Phase 4+)
    storage_backend: str = Field(default="local")
    upload_dir: str = Field(default="uploads")

    # --- Logging ---
    log_level: str = Field(default="INFO")


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere instead of re-instantiating
# ---------------------------------------------------------------------------
settings = Settings()
