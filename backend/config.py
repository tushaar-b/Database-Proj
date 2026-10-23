"""Configuration loader for IntelliVest Backend Application Gateway."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    APP_ENV: str = "development"
    # Keep the authenticated MVP local-only until a deployment review is complete.
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://127.0.0.1:5173,http://localhost:5173"

    # Databases
    ADVISORY_DB_URL: str
    RISK_DB_URL: str

    # Market Data
    MARKET_DATA_PROVIDER: Literal["yfinance"] = "yfinance"

    # Yahoo Finance research data, shared across authenticated consumers.
    MARKET_QUOTE_REFRESH_SECONDS: int = Field(default=300, ge=60, le=3600)
    MARKET_QUOTE_STALE_SECONDS: int = Field(default=1800, ge=60, le=7200)
    MARKET_CLOSE_MAX_AGE_DAYS: int = Field(default=7, ge=1, le=10)
    MARKET_HISTORY_CACHE_SECONDS: int = Field(default=3600, ge=300, le=86400)
    MARKET_PROVIDER_BACKOFF_SECONDS: int = Field(default=300, ge=60, le=3600)
    YFINANCE_TIMEOUT_SECONDS: int = Field(default=8, ge=2, le=30)
    RECOMMENDATION_PRICE_CHANGE_FRACTION: float = Field(default=0.02, gt=0, le=0.25)
    STOCK_ANNUAL_RISK_FREE_RATE: float = Field(default=0.04, ge=0, le=1)

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
