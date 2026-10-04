"""
ResQ-AI Configuration Module.
Handles application settings, environment variables, database connections,
CORS origins, and DEMO MODE configuration using Pydantic v2 BaseSettings.
"""

from functools import lru_cache
from typing import List, Union
import json
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime settings loaded from environment or .env file."""

    # Project Metadata
    PROJECT_NAME: str = "ResQ-AI"
    PROJECT_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"  # development | test | production
    DEBUG: bool = False

    # Server Binding
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database Configuration (Dual-Engine: SQLite local/test fallback, PostgreSQL prod)
    DATABASE_URL: str = "sqlite:///./resq_ai.db"

    # AI / LLM Configuration
    # Deterministic DEMO MODE is enabled by default for reproducible offline operation
    DEMO_MODE: bool = True
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"
    LLM_API_KEY: str = ""
    LLM_PROVIDER: str = ""

    # Startup Automation
    AUTO_SEED_ON_STARTUP: bool = True

    # Security & CORS Origins
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://resq-ai.vercel.app",
    ]

    # Educational Disclaimer (Mandatory Academic Banner)
    DISCLAIMER_TEXT: str = "Educational simulation - not for real-world emergency dispatch."

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: str) -> str:
        """Fix legacy postgres:// URLs from Render/Heroku to postgresql+psycopg2://."""
        if not v:
            return "sqlite:///./resq_ai.db"
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg2://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+"):
            return v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """Convert comma-separated strings or JSON arrays or lists into clean origin lists."""
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                try:
                    parsed = json.loads(v_stripped)
                    if isinstance(parsed, list):
                        return [str(orig).strip() for orig in parsed if str(orig).strip()]
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return ["*"]

    @property
    def is_demo_mode_active(self) -> bool:
        """Returns True if DEMO_MODE is explicitly True or no GEMINI_API_KEY is supplied."""
        return self.DEMO_MODE or not bool(self.GEMINI_API_KEY.strip())


@lru_cache()
def get_settings() -> Settings:
    """Cached singleton instance of application settings."""
    return Settings()
