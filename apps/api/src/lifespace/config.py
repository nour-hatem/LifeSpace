"""Typed runtime settings for the API.

This module only reads configuration from the environment and the repository
root ``.env`` file. It must not import the API or infrastructure layers, and it
must never log or expose the database credentials it holds.
"""

from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[4] / ".env"


class Settings(BaseSettings):
    """Configuration values prefixed with ``LIFESPACE_``."""

    model_config = SettingsConfigDict(
        env_prefix="LIFESPACE_",
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "test", "production"] = "development"
    database_url: str
    test_database_url: str | None = None
    log_level: str = "INFO"
