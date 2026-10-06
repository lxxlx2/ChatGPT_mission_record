"""Read-only Frank production adapter for Mission Meme V1."""
from __future__ import annotations

import json
import os
import sqlite3
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .db import open_production_ro

USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
WSOL = "So11111111111111111111111111111111111111112"


def _pid_alive(pid: int | str | None) -> bool:
    try:
        pid = int(pid)
    except (TypeError, ValueError):
        return False
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except (TypeError, ValueError, OverflowError):
        return False


def _token_quantity(event: dict) -> Decimal | None:
    try:
        return Decimal(event["token_amount_raw"]) / (Decimal(10) ** int(event["token_decimals"]))
    except (KeyError, InvalidOperation, ValueError, TypeError):
        return None


def _event_price_usdc(event: dict) -> Decimal | None:
    """Return event-time USDC/token only from durable event-time evidence.

    Direct USDC trades use their quote quantity. SOL/WSOL trades are accepted only
    when upstream replay/normalization attached verified event-time SOL/USDC
    evidence. A current SOL price is never substituted for a historical trade.
    """
    quantity = _token_quantity(event)
    if not quantity:
        return None
    try:
        if event.get("quote_asset") == USDC:
            return Decimal(str(event["quote_quantity"])) / quantity
        if event.get("quote_usdc_status") == "SOL_EVENT_TIME_USDC_VERIFIED" and event.get("quote_usdc_equivalent") is not None:
            return Decimal(str(event["quote_usdc_equivalent"])) / quantity
    except (KeyError, InvalidOperation, ZeroDivisionError, TypeError):
        return None
    return None


class FrankReader:
    def __init__(self, production_root: Path):
        self.root = Path(production_root)
        self.database = self.root / "forward.sqlite"
        self.health_path = self.root / "health.json"

    def runtime(self, now: float | None = None) -> dict:
        now = time.time() if now is None else now
        if not self.health_path.is_file():
            return {"status": "UNKNOWN", "reason": "HEALTH_FILE_MISSING"}
        try:
            health = json.loads(self.health_path.read_text())
        except (OSError, ValueError):
            return {"status": "UNKNOWN", "reason": "HEALTH_FILE_UNREADABLE"}
        raw_status = health.get("status")
        pid = health.get("pid")
        alive = _pid_alive(pid)
        last = health.get("last_successful_poll")
        poll_interval = int(health.get("poll_interval_seconds") or 30)
        age = None
        if last:
            try:
                age = max(0.0, now - __import__("datetime").datetime.fromisoformat(last).timestamp())
            except (ValueError, TypeError):
                age = None
        db_ok = False
        try:
            db = open_production_ro(self.database)
            db.execute("SELECT 1").fetchone()
            db.close()
            db_ok = True
        except (OSError, ValueError, sqlite3.Error):
            db_ok = False
        if not alive:
            status, reason = "OFFLINE", "PID_NOT_ALIVE"
        elif age is None:
            status, reason = "UNKNOWN", "LAST_SUCCESSFUL_POLL_UNKNOWN"
        elif age > poll_interval * 3:
            status, reason = "OFFLINE", "HEARTBEAT_STALE"
        elif not db_ok:
            status, reason = "DEGRADED", "PRODUCTION_DB_UNREADABLE"
        elif health.get("source_drift"):
            status, reason = "DEGRADED", "SOURCE_DRIFT"
        elif raw_status != "RUNNING":
            status, reason = "DEGRADED", "SERVICE_" + str(raw_status or "UNKNOWN")
        elif int(health.get("consecutive_errors") or 0) > 0:
            status, reason = "DEGRADED", "CONSECUTIVE_ERRORS"
        else:
            status, reason = "LIVE", "OK"
        return {**health, "status": status, "runtime_reason": reason, "pid_alive": alive, "heartbeat_age_seconds": age, "production_db_readable": db_ok}

    def candidates(self) -> list[dict]:
        db = open_production_ro(self.database)
        try:
            rows = db.execute("SELECT person_id,mint,body FROM v1_states").fetchall()
            result = []
            for row in rows:
                try:
                    state = json.loads(row["body"])
                except (TypeError, ValueError):
                    continue
                signals = db.execute(
                    "SELECT signal_id,signal_type,created_at,body FROM signals WHERE person_id=? AND mint=? AND episode_id=? ORDER BY CAST(created_at AS INTEGER),rowid",
                    (row["person_id"], row["mint"], state.get("episode_id")),
                ).fetchall()
                if not signals:
                    continue
                signal_row = signals[-1]
                source_signal_type = signal_row["signal_type"]
                if source_signal_type == "FRANK_MULTIPLE_SIGNAL":
                    pattern = "MULTIPLE"
                elif source_signal_type == "FRANK_ACCUMULATION_SIGNAL":
                    pattern = "ACCUMULATION"
                else:
                    # Unknown/new signal kinds are never silently treated as accumulation.
                    continue
                source_signal_id = signal_row["signal_id"]
                source_signal_at = signal_row["created_at"]
                events = state.get("events") or []
                latest = events[-1] if events else None
                buys = [e for e in events if e.get("direction") == "BUY"]
                latest_buy = buys[-1] if buys else None
                latest_buy_price = _event_price_usdc(latest_buy) if latest_buy else None
                latest_quote_asset = latest_buy.get("quote_asset") if latest_buy else None
                if latest_buy_price is not None:
                    price_status = "SOL_EVENT_TIME_USDC_VERIFIED" if latest_buy and latest_buy.get("quote_usdc_status") == "SOL_EVENT_TIME_USDC_VERIFIED" else "USDC_DIRECT"
                elif latest_quote_asset in {"SOL", WSOL}:
                    price_status = "SOL_EVENT_TIME_USDC_UNAVAILABLE"
                else:
                    price_status = "QUOTE_PRICE_UNAVAILABLE"
                result.append({
                    "person_id": row["person_id"], "mint": row["mint"], "episode_id": state.get("episode_id"),
                    "pattern": pattern, "source_signal_id": source_signal_id, "source_signal_type": source_signal_type,
                    "source_signal_at": source_signal_at,
                    "position_state": state.get("state"), "current_raw": state.get("current_raw"),
                    "buy_count": len(buys), "sell_count": sum(e.get("direction") == "SELL" for e in events),
                    "latest_side": latest.get("direction") if latest else None, "latest_signature": latest.get("signature") if latest else None,
                    "latest_at": latest.get("at") if latest else None, "latest_buy_at": latest_buy.get("at") if latest_buy else None,
                    "latest_buy_price_usdc": str(latest_buy_price) if latest_buy_price is not None else None,
                    "latest_buy_price_status": price_status,
                    "latest_buy_quote_asset": latest_quote_asset,
                    "latest_buy_quote_quantity": latest_buy.get("quote_quantity") if latest_buy else None,
                    "token_decimals": int(latest_buy.get("token_decimals")) if latest_buy and latest_buy.get("token_decimals") is not None else None,
                    "events": events,
                })
            result.sort(key=lambda x: int(x.get("latest_at") or 0), reverse=True)
            return result
        finally:
            db.close()

    def recent_trades(self, limit: int = 100) -> list[dict]:
        db = open_production_ro(self.database)
        try:
            rows = db.execute("SELECT wallet,signature,mint,episode_id,block_time,side,body FROM trades ORDER BY block_time DESC LIMIT ?", (limit,)).fetchall()
            result = []
            for row in rows:
                item = dict(row)
                item["body"] = json.loads(item["body"])
                result.append(item)
            return result
        finally:
            db.close()
