"""Configuration loader for IntelliVest Backend Application Gateway."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    APP_ENV: str = "development"
    # Keep the authenticated MVP local-only until a deployment review is complete.
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173"

    # Databases
    ADVISORY_DB_URL: str
    RISK_DB_URL: str

    # Market Data
    MARKET_DATA_PROVIDER: str = "yfinance"

    # Defaults
    DEFAULT_LIQUID_SAFETY_RESERVE: float = 50000.00
    DEFAULT_VAR_CONFIDENCE_LEVEL: float = 0.95
    DEFAULT_TARGET_HHI_LIMIT: float = 0.25
    RISK_VAR_LIMIT_PERCENT: float = Field(default=0.10, gt=0)
    RISK_DAILY_VOLATILITY_LIMIT: float = Field(default=0.03, gt=0)
    # A rejected batch can be reconsidered after this interval even if inputs
    # have not changed. A changed input fingerprint permits earlier review.
    RECOMMENDATION_RECONSIDER_DAYS: int = Field(default=30, ge=1, le=365)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
