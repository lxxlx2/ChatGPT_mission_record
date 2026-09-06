#!/usr/bin/env python3
"""Deterministic pre-generation triggering for X revenue workflow."""

from __future__ import annotations

import datetime as dt
import hashlib
from typing import Any


def evaluate_triggers(
    stocks: dict[str, Any],
    crypto: dict[str, Any],
    trends: list[dict[str, Any]],
    analysis: dict[str, Any],
    last_event_values: dict[str, Any],
    config: dict[str, Any],
    now: dt.datetime | None = None,
) -> dict[str, Any]:
    """Evaluate whether current public market and regulatory data warrants a candidate.

    Returns a dict with:
      - triggered: bool
      - action: "GENERATE_CANDIDATE" | "NO_ACTION"
      - active_triggers: list[dict[str, Any]]
      - trigger_summary: str
      - current_event_values: dict[str, Any]
      - reason: str
    """
    now = now or dt.datetime.now(dt.timezone.utc)
    utc_today = now.strftime("%Y-%m-%d")

    stock_threshold = float(config.get("stock_trigger_percent", 1.0))
    crypto_threshold = float(config.get("crypto_trigger_percent", 2.5))
    repeat_delta = float(config.get("repeat_delta_percentage_points", 0.75))
    news_threshold = float(config.get("news_trigger_score", 5.0))
    breaking_threshold = float(config.get("breaking_threshold_percent", 3.0))

    active_triggers: list[dict[str, Any]] = []
    current_event_values: dict[str, Any] = {}

    # 1. US Stock Index Moves
    for symbol, data in stocks.items():
        change = round(float(data.get("change_percent", 0.0)), 2)
        trade_date = str(data.get("trade_date", utc_today))
        key = f"Nasdaq:{symbol}:{trade_date}"
        current_event_values[key] = change

        if abs(change) >= stock_threshold:
            prev = last_event_values.get(key)
            if prev is None or abs(change - float(prev)) >= repeat_delta:
                active_triggers.append({
                    "type": "STOCK_INDEX_MOVE",
                    "source_id": key,
                    "symbol": symbol,
                    "display_name": data.get("display_name", symbol),
                    "change_percent": change,
                    "threshold_percent": stock_threshold,
                    "breaking": abs(change) >= breaking_threshold,
                })

    # 2. Crypto Moves vs UTC Open
    for symbol in ("BTC", "ETH", "SOL"):
        if symbol in crypto:
            change = round(float(crypto[symbol].get("change_percent_vs_utc_open", 0.0)), 2)
            key = f"Kraken:{symbol}:{utc_today}"
            current_event_values[key] = change

            if abs(change) >= crypto_threshold:
                prev = last_event_values.get(key)
                if prev is None or abs(change - float(prev)) >= repeat_delta:
                    active_triggers.append({
                        "type": "CRYPTO_MOVE",
                        "source_id": key,
                        "symbol": symbol,
                        "change_percent": change,
                        "threshold_percent": crypto_threshold,
                        "breaking": abs(change) >= breaking_threshold,
                    })

    # 3. Cross-Asset Divergence
    signal = analysis.get("signal")
    stock_dispersion = float(analysis.get("stock_dispersion_percentage_points", 0.0))
    crypto_dispersion = float(analysis.get("crypto_dispersion_percentage_points", 0.0))
    stock_breadth = int(analysis.get("stock_breadth_up", 0))
    crypto_breadth = int(analysis.get("crypto_breadth_up", 0))

    if signal == "cross_asset_divergence" and (stock_dispersion >= 1.5 or crypto_dispersion >= 2.0):
        trade_dates = [str(v.get("trade_date")) for v in stocks.values() if isinstance(v, dict)]
        session_date = trade_dates[0] if trade_dates else utc_today
        key = f"Divergence:{session_date}:s{stock_breadth}c{crypto_breadth}"
        current_event_values[key] = f"{stock_dispersion}:{crypto_dispersion}"

        if key not in last_event_values:
            active_triggers.append({
                "type": "CROSS_ASSET_DIVERGENCE",
                "source_id": key,
                "stock_breadth_up": stock_breadth,
                "crypto_breadth_up": crypto_breadth,
                "stock_dispersion": stock_dispersion,
                "crypto_dispersion": crypto_dispersion,
                "interpretation": analysis.get("interpretation", ""),
            })

    # 4. Official Regulatory / Central Bank Headlines (Fed & SEC)
    for item in trends:
        age_hours = float(item.get("age_hours", 999.0))
        trend_score = float(item.get("trend_score", 0.0))
        # High-scoring breaking news within 24 hours
        if age_hours <= 24.0 and trend_score >= news_threshold:
            title = str(item.get("title", "")).strip()
            source = str(item.get("source", "")).strip()
            title_hash = hashlib.sha256(f"{source}:{title}".encode("utf-8")).hexdigest()[:16]
            key = f"News:{title_hash}"
            current_event_values[key] = trend_score

            if key not in last_event_values:
                active_triggers.append({
                    "type": "REGULATORY_EVENT",
                    "source_id": key,
                    "source": source,
                    "title": title,
                    "trend_score": trend_score,
                    "published_at": item.get("published_at"),
                })

    if not active_triggers:
        return {
            "triggered": False,
            "action": "NO_ACTION",
            "active_triggers": [],
            "trigger_summary": "No material market shift or breaking regulatory event",
            "current_event_values": current_event_values,
            "reason": "Market state within thresholds or already reported without material delta",
        }

    # Format trigger summary
    parts = []
    for trig in active_triggers:
        ttype = trig["type"]
        if ttype == "STOCK_INDEX_MOVE":
            parts.append(f"{trig['display_name']} {trig['change_percent']:+.2f}%")
        elif ttype == "CRYPTO_MOVE":
            parts.append(f"{trig['symbol']} {trig['change_percent']:+.2f}%")
        elif ttype == "CROSS_ASSET_DIVERGENCE":
            parts.append(f"Divergence stocks {trig['stock_breadth_up']}/3 vs crypto {trig['crypto_breadth_up']}/3")
        elif ttype == "REGULATORY_EVENT":
            parts.append(f"[{trig['source']}] {trig['title'][:50]} (score {trig['trend_score']})")

    summary = "; ".join(parts)
    return {
        "triggered": True,
        "action": "GENERATE_CANDIDATE",
        "active_triggers": active_triggers,
        "trigger_summary": summary,
        "current_event_values": current_event_values,
        "reason": f"Triggered by {len(active_triggers)} active events: {summary}",
    }
