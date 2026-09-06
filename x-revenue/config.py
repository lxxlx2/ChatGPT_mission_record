#!/usr/bin/env python3
"""Configuration and secure credential management for x-revenue automation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_FILE = ROOT / "config.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "stock_trigger_percent": 1.0,
    "crypto_trigger_percent": 2.5,
    "repeat_delta_percentage_points": 0.75,
    "news_trigger_score": 5.0,
    "breaking_threshold_percent": 3.0,
    "approval_ttl_hours": 24,
}


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load configuration with defaults, config file overrides, and environment variables."""
    cfg = dict(DEFAULT_CONFIG)
    target = config_path or DEFAULT_CONFIG_FILE
    if target.exists():
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                cfg.update(data)
        except Exception:
            pass

    return cfg
