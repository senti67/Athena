"""
ATHENA Centralized Application Configuration (INR / Indian Markets Enabled)
"""

from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    APP_ENV: str = "development"
    APP_NAME: str = "ATHENA"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Currency & Localization
    CURRENCY_CODE: str = "INR"
    CURRENCY_SYMBOL: str = "₹"

    # Execution & Safety Controls (Live trading disabled by default)
    LIVE_TRADING_ENABLED: bool = Field(
        default=False,
        description="Master live execution switch. MUST remain false by default.",
    )
    EXECUTION_MODE: str = Field(
        default="PAPER",
        description="Execution mode: PAPER or LIVE. Paper is default.",
    )
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.75
    MIN_DATA_QUALITY_SCORE: float = 0.80

    # Risk Management Limits (Calibrated in INR)
    MAX_DAILY_LOSS: float = 50000.00          # ₹50,000 max daily loss
    MAX_POSITION_SIZE: float = 500000.00      # ₹5,00,000 max per position
    MAX_PORTFOLIO_EXPOSURE: float = 1.00
    MAX_LEVERAGE: float = 1.00
    MAX_SECTOR_CONCENTRATION: float = 0.30
    MAX_SINGLE_ASSET_EXPOSURE: float = 0.20
    MAX_DRAWDOWN_LIMIT: float = 0.15
    VAR_95_LIMIT: float = 0.03
    CVAR_95_LIMIT: float = 0.05
    CIRCUIT_BREAKER_TRIGGERED: bool = False

    # Security & Auth
    JWT_SECRET_KEY: str = "athena-institutional-super-secret-jwt-key-change-in-prod-2026!"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    API_KEY_HEADER: str = "X-Athena-API-Key"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./athena.db"
    DATABASE_SYNC_URL: str = "sqlite:///./athena.db"
    SQL_ECHO: bool = False

    # Redis Cache & Ephemeral State
    REDIS_URL: str = "redis://localhost:6379/0"

    # Messaging (Kafka / Local Event Bus)
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_USE_LOCAL_BUS: bool = True

    # AI / LLM Providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    LLM_DEFAULT_PROVIDER: str = "mock"
    LLM_PRIMARY_MODEL: str = "gpt-4o"
    LLM_FALLBACK_MODEL: str = "claude-3-5-sonnet-20241022"
    LLM_FAST_MODEL: str = "gemini-1.5-flash"
    LLM_TEMPERATURE: float = 0.1
    LLM_TIMEOUT_SECONDS: int = 30

    # Market Data Providers
    MARKET_DATA_PROVIDER: str = "nse_yfinance"
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    POLYGON_API_KEY: Optional[str] = None
    FMP_API_KEY: Optional[str] = None

    # Broker Integrations
    BROKER_PROVIDER: str = "paper"
    BROKER_API_KEY: Optional[str] = None
    BROKER_API_SECRET: Optional[str] = None
    BROKER_BASE_URL: str = "https://paper-api.alpaca.markets"

    # Paper Trading Simulation Parameters (Starting Paper Balance in INR: ₹10,00,000 / 10 Lakhs)
    PAPER_STARTING_CASH: float = 1000000.00
    PAPER_SLIPPAGE_BPS: float = 5.0
    PAPER_COMMISSION_PER_SHARE: float = 0.05
    PAPER_LATENCY_MS: int = 50

    # Observability
    PROMETHEUS_METRICS_ENABLED: bool = True
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = "http://localhost:4317"


settings = Settings()
