"""Application configuration and environment settings."""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for WhatsApp Appointment Scheduler."""

    # Server configuration
    APP_NAME: str = "WhatsApp Appointment Scheduler"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database configuration
    DATABASE_URL: str = "sqlite:///./appointments.db"

    @classmethod
    def _normalize_database_url(cls, v: str) -> str:
        if v and v.startswith("sqlite:///./"):
            rel_name = v[12:]
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            abs_path = os.path.join(backend_dir, rel_name).replace("\\", "/")
            return f"sqlite:///{abs_path}"
        return v

    def __init__(self, **values):
        super().__init__(**values)
        self.DATABASE_URL = self._normalize_database_url(self.DATABASE_URL)

    # Business Rules
    APP_TIMEZONE: str = "UTC"
    SLOT_DURATION_MINUTES: int = 30
    WORK_START_HOUR: int = 9   # 09:00 AM
    WORK_END_HOUR: int = 17    # 05:00 PM (17:00, last appointment at 16:30)

    # WhatsApp Integration
    WHATSAPP_PROVIDER: str = "mock"  # "mock" or "meta"
    META_WHATSAPP_TOKEN: Optional[str] = None
    META_PHONE_NUMBER_ID: Optional[str] = None
    META_VERIFY_TOKEN: str = "appointment_scheduler_verify_token"
    META_APP_SECRET: Optional[str] = None

    # CORS configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ]

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
