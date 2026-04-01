from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development")
    google_api_key: str | None = Field(default=None, validation_alias="GOOGLE_API_KEY")
    database_url: str = Field(default="sqlite+aiosqlite:///./infographix.db")
    storage_path: Path = Field(default=Path("./storage"))
    default_model: str = Field(default="models/gemini-2.5-flash-image")
    low_latency_models: List[str] = Field(default_factory=lambda: ["models/gemini-2.5-flash-image"])
    high_fidelity_models: List[str] = Field(
        default_factory=lambda: ["models/gemini-3.1-flash-image-preview"]
    )
    max_upload_bytes: int = Field(default=5 * 1024 * 1024)  # 5 MB
    chat_router_model: str = Field(default="models/gemini-2.0-flash")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_path.mkdir(parents=True, exist_ok=True)
    (settings.storage_path / "outputs").mkdir(parents=True, exist_ok=True)
    (settings.storage_path / "reference").mkdir(parents=True, exist_ok=True)
    (settings.storage_path / "chat_uploads").mkdir(parents=True, exist_ok=True)
    return settings
