"""Configuration utilities for the OS performance scanner."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass(slots=True)
class Settings:
    """Application settings loaded from config file and environment."""

    refresh_interval_seconds: int = 5
    top_process_count: int = 10
    network_sample_seconds: float = 1.0
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    api_base_url: str = "http://127.0.0.1:8000"


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


def _read_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def get_settings() -> Settings:
    """Return merged settings from defaults, config file, and env vars."""

    config_path = Path(os.getenv("CONFIG_PATH", str(DEFAULT_CONFIG_PATH)))
    file_config = _read_config(config_path)

    return Settings(
        refresh_interval_seconds=int(
            os.getenv(
                "REFRESH_INTERVAL_SECONDS",
                file_config.get("refresh_interval_seconds", 5),
            )
        ),
        top_process_count=int(
            os.getenv("TOP_PROCESS_COUNT", file_config.get("top_process_count", 10))
        ),
        network_sample_seconds=float(
            os.getenv(
                "NETWORK_SAMPLE_SECONDS",
                file_config.get("network_sample_seconds", 1.0),
            )
        ),
        api_host=os.getenv("API_HOST", file_config.get("api_host", "127.0.0.1")),
        api_port=int(os.getenv("API_PORT", file_config.get("api_port", 8000))),
        api_base_url=os.getenv(
            "API_BASE_URL", file_config.get("api_base_url", "http://127.0.0.1:8000")
        ),
    )
