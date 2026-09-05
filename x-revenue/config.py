#!/usr/bin/env python3
"""Configuration and secure credential management for x-revenue automation."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
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
    "telegram_chat_id": None,
    "telegram_allowed_user_ids": [],
}


def get_telegram_token() -> str | None:
    """Retrieve Telegram bot token safely from macOS Keychain or environment.

    Never prints or logs secret values. Returns None if not configured.
    """
    # 1. Check macOS Keychain
    try:
        r = subprocess.run(
            ["security", "find-generic-password", "-a", "x-revenue", "-s", "x-revenue.telegram-bot", "-w"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0:
            token = r.stdout.strip()
            if token:
                return token
    except Exception:
        pass

    # 2. Check environment variable
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token and token.strip():
        return token.strip()

    return None


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

    # Environment overrides
    if "TELEGRAM_CHAT_ID" in os.environ:
        cfg["telegram_chat_id"] = os.environ["TELEGRAM_CHAT_ID"].strip()
    if "TELEGRAM_ALLOWED_USER_IDS" in os.environ:
        raw = os.environ["TELEGRAM_ALLOWED_USER_IDS"].strip()
        try:
            cfg["telegram_allowed_user_ids"] = json.loads(raw)
        except Exception:
            cfg["telegram_allowed_user_ids"] = [item.strip() for item in raw.split(",") if item.strip()]

    return cfg
