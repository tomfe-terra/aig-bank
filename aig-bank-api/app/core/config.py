"""Application configuration settings."""

import secrets

from pydantic import Field
from pydantic_settings import BaseSettings

from .enums import DocsVerbosity


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    debug: bool = Field(default=False, validation_alias="DEBUG")

    host: str = Field(default="127.0.0.1", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")

    database_url: str = Field(default="sqlite+aiosqlite:///./bank.db", validation_alias="DATABASE_URL")

    jwt_secret_key: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_expiration_minutes: int = Field(default=60, validation_alias="JWT_EXPIRATION_MINUTES")
    jwt_refresh_expiration_days: int = Field(default=30, validation_alias="JWT_REFRESH_EXPIRATION_DAYS")

    cors_origins: list[str] = Field(
        default=["http://localhost:1312", "http://127.0.0.1:1312"],
        validation_alias="CORS_ORIGINS",
    )
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]

    trusted_hosts: list[str] = Field(
        default=["*"],
        validation_alias="TRUSTED_HOSTS",
    )

    aes_key: str = Field(default_factory=lambda: secrets.token_hex(32), validation_alias="AES_KEY")
    hmac_key: str = Field(default_factory=lambda: secrets.token_hex(32), validation_alias="HMAC_KEY")

    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    logs_directory: str = Field(default="logs", validation_alias="LOGS_DIRECTORY")

    docs_verbosity: DocsVerbosity = Field(
        default=DocsVerbosity.FULL,
        validation_alias="DOCS_VERBOSITY",
        description="OpenAPI documentation verbosity level (full, medium, minimal)",
    )

    repayment_check_interval_seconds: int = Field(
        default=3600,
        validation_alias="REPAYMENT_CHECK_INTERVAL_SECONDS",
        description="Interval in seconds for checking and processing loan repayments",
    )

    model_config = {"env_file": ".env", "case_sensitive": False, "extra": "ignore"}


settings = Settings()
