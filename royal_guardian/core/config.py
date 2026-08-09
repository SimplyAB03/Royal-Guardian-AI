from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("RG_APP_NAME", "Royal Guardian")
    environment: str = os.getenv("RG_ENV", "development")
    database_url: str = os.getenv("RG_DATABASE_URL", f"sqlite:///{ROOT / 'data' / 'royal_guardian.db'}")
    session_secret: str = os.getenv("RG_SESSION_SECRET", "change-me-in-production")
    encryption_secret: str = os.getenv("RG_ENCRYPTION_SECRET", os.getenv("RG_SESSION_SECRET", "change-me-in-production"))
    session_ttl_seconds: int = int(os.getenv("RG_SESSION_TTL_SECONDS", "86400"))
    allow_registration: bool = _bool("RG_ALLOW_REGISTRATION", True)
    public_base_url: str = os.getenv("RG_PUBLIC_BASE_URL", "http://127.0.0.1:8000")
    endpoint_poll_seconds: int = int(os.getenv("RG_ENDPOINT_POLL_SECONDS", "20"))
    device_api_key: str = os.getenv("RG_DEVICE_API_KEY", "")

    @property
    def production(self) -> bool:
        return self.environment.lower() == "production"


settings = Settings()
