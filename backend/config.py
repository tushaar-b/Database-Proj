"""Configuration loader for IntelliVest Backend Application Gateway."""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    SECRET_KEY: str = "intellivest_dev_secret_key"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Databases
    ADVISORY_DB_URL: str = "postgresql://postgres:postgres@localhost:5434/advisory_db"
    RISK_DB_URL: str = "postgresql://postgres:postgres@localhost:5433/risk_db"

    # Market Data
    MARKET_DATA_PROVIDER: str = "yfinance"

    # Defaults
    DEFAULT_LIQUID_SAFETY_RESERVE: float = 50000.00
    DEFAULT_VAR_CONFIDENCE_LEVEL: float = 0.95
    DEFAULT_TARGET_HHI_LIMIT: float = 0.25
    RISK_VAR_LIMIT_PERCENT: float = Field(default=0.10, gt=0)
    RISK_DAILY_VOLATILITY_LIMIT: float = Field(default=0.03, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
