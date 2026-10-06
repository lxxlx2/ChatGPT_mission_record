"""Replay Frank V1 with durable SOL->USDC event-time normalization.

REVIEW/RESEARCH ONLY. This script never edits the source forward.sqlite, never
sends notifications, and always runs Engine(dry_run=True). Historical SOL/USDC
references are persisted in the target DB before they are consumed by the model.
Transient source failures are retried and are never cached as durable evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections import Counter
from pathlib import Path

from mission_agent.market.sol_usd import (
    BinanceSolUsdcHistoryClient,
    SOL_QUOTE_ASSETS,
    normalize_classification,
    reference_epoch,
    reference_key,
)
from mission_agent.mission_control.db import open_production_ro, utc
from mission_agent.signals.engine import Engine
from mission_agent.signals.policy import load_policy
from mission_agent.signals.store import Ledger

ROOT = Path(__file__).parents[1]
DEFAULT_POLICY = ROOT / "config" / "frank_local_signal_v1.json"
CACHEABLE_UNAVAILABLE = frozenset({"BINANCE_KLINE_NOT_FOUND"})


def _ensure_reference_table(db):
    db.execute(
        """CREATE TABLE IF NOT EXISTS sol_usdc_references(
            reference_key TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            status TEXT NOT NULL,
            reference_epoch INTEGER NOT NULL,
            content_hash TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        )"""
    )


def _hash(value) -> str:
    stable = {k: v for k, v in value.items() if k != "observed_at"}
    return hashlib.sha256(
        json.dumps(stable, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


def _cacheable(value: dict) -> bool:
    return value.get("status") == "VERIFIED" or value.get("reason") in CACHEABLE_UNAVAILABLE


def _reference(db, client, block_time: int, *, attempts: int = 3, sleep=time.sleep):
    """Return one candle reference without permanently caching transient failures."""
    key = reference_key(block_time)
    row = db.execute("SELECT body FROM sol_usdc_references WHERE reference_key=?", (key,)).fetchone()
    if row:
        return json.loads(row[0])

    value = None
    for attempt in range(max(1, int(attempts))):
        value = client.reference(block_time)
        if _cacheable(value) or not value.get("retryable", False):
            break
        if attempt + 1 < attempts:
            sleep(min(1.0, 0.25 * (2**attempt)))

    if value is None:
        value = {"status": "UNAVAILABLE", "reason": "REFERENCE_CLIENT_RETURNED_NONE", "retryable": True}
    if _cacheable(value):
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"))
        db.execute(
            "INSERT INTO sol_usdc_references VALUES(?,?,?,?,?,?,?)",
            (
                key,
                value.get("source", "UNAVAILABLE"),
                value.get("status", "UNAVAILABLE"),
                reference_epoch(block_time),
                _hash(value),
                encoded,
                utc(),
            ),
        )
    return value


def _signal_index(db):
    rows = db.execute(
        "SELECT person_id,mint,episode_id,signal_type,stage,triggered_at,body "
        "FROM (SELECT person_id,mint,episode_id,signal_type,stage,CAST(created_at AS INTEGER) triggered_at,body FROM signals) "
        "ORDER BY triggered_at,signal_type"
    ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        body = json.loads(item.pop("body"))
        item["triggering_signature"] = body.get("triggering_signature") or body.get("latest_trade_signature")
        result.append(item)
    return result


def _signal_key(value):
    return (
        value["person_id"],
        value["mint"],
        value["episode_id"],
        value["signal_type"],
        value["stage"],
        value.get("triggering_signature"),
    )


def replay(source_path: Path, target_path: Path, policy_path: Path, client=None):
    source = open_production_ro(source_path)
    target = Ledger(target_path)
    _ensure_reference_table(target.db)
    engine = Engine(target, load_policy(policy_path), dry_run=True)
    client = client or BinanceSolUsdcHistoryClient()
    counters = {
        "signatures": 0,
        "active_trades": 0,
        "sol_trades": 0,
        "sol_resolved": 0,
        "sol_unresolved": 0,
        "usdc_trades": 0,
    }
    reference_failures = Counter()

    rows = source.execute(
        "SELECT wallet,signature,person_id,slot,block_time,raw_hash,raw_reference,body "
        "FROM signatures ORDER BY block_time,slot,signature"
    ).fetchall()
    for row in rows:
        counters["signatures"] += 1
        classified = json.loads(row["body"])
        trade = classified.get("trade") or {}
        if classified.get("classification") == "ACTIVE_TRADE":
            counters["active_trades"] += 1
            if trade.get("quote_asset") in SOL_QUOTE_ASSETS:
                counters["sol_trades"] += 1
                if row["block_time"] is None:
                    ref = {"status": "UNAVAILABLE", "reason": "BLOCK_TIME_MISSING", "retryable": False}
                else:
                    ref = _reference(target.db, client, int(row["block_time"]))
                classified = normalize_classification(classified, ref, for_model=True)
                if (classified.get("trade") or {}).get("quote_normalization") == "SOL_TO_USDC_SHADOW_EQUIVALENT":
                    counters["sol_resolved"] += 1
                else:
                    counters["sol_unresolved"] += 1
                    reference_failures[ref.get("reason", "UNKNOWN_REFERENCE_FAILURE")] += 1
            else:
                counters["usdc_trades"] += 1
        target.put(
            row["person_id"],
            classified,
            row["raw_hash"] or row["signature"],
            row["raw_reference"] or "SOURCE_FORWARD_SQLITE",
            dry_run=True,
        )
        engine.drain()

    source_signals = _signal_index(source)
    shadow_signals = _signal_index(target.db)
    source_keys = {_signal_key(x) for x in source_signals}
    shadow_keys = {_signal_key(x) for x in shadow_signals}
    added = [x for x in shadow_signals if _signal_key(x) not in source_keys]
    missing = [x for x in source_signals if _signal_key(x) not in shadow_keys]

    # Strict regression gate: every previously emitted source signal must still be
    # present with the same stage and triggering signature. Mixed SOL/USDC mints are
    # intentionally NOT excluded from this comparison.
    strict_regression_pass = len(missing) == 0
    report = {
        "schema_version": 2,
        "mode": "SHADOW_REPLAY_ONLY",
        "reference_source": "BINANCE_OFFICIAL_SPOT_SOLUSDC",
        "source_db": str(source_path),
        "target_db": str(target_path),
        "policy_path": str(policy_path),
        "counters": counters,
        "reference_failure_counts": dict(sorted(reference_failures.items())),
        "source_signal_count": len(source_signals),
        "shadow_signal_count": len(shadow_signals),
        "sol_added_signals": added,
        "missing_source_signals": missing,
        "source_signal_regression_pass": strict_regression_pass,
        # Backward-compatible field name, now deliberately strict rather than mint-filtered.
        "usdc_regression_pass": strict_regression_pass,
        "production_trading": "NO_GO",
    }
    source.close()
    target.db.commit()
    target.db.close()
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--target", type=Path, required=True)
    p.add_argument("--report", type=Path, required=True)
    p.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    a = p.parse_args()
    if a.target.exists():
        raise SystemExit("TARGET_MUST_NOT_EXIST")
    a.target.parent.mkdir(parents=True, exist_ok=True)
    result = replay(a.source, a.target, a.policy)
    a.report.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
