"""Read-only production-vs-candidate Frank classifier replay.

Never mutates the source database, never dispatches notifications, and never
uses production trading. Rebuilds baseline and candidate V1 ledgers in a new
isolated workspace so classification, signal and HFT/state deltas can be
reviewed before any migration.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path

from mission_agent.signals.classifier import classify
from mission_agent.signals.engine import Engine
from mission_agent.signals.policy import load_policy
from mission_agent.signals.store import Ledger


def canonical_hash(tx: dict) -> str:
    return hashlib.sha256(
        json.dumps(tx, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def raw_transaction(row: sqlite3.Row, source: Path) -> tuple[dict | None, str | None]:
    reference = row["raw_reference"]
    if not reference:
        return None, "RAW_REFERENCE_MISSING"
    path = Path(reference)
    if not path.is_absolute():
        path = source.parent / path
    if not path.is_file():
        return None, "RAW_FILE_MISSING"
    try:
        tx = json.loads(gzip.decompress(path.read_bytes()))
    except (OSError, EOFError, ValueError, TypeError):
        return None, "RAW_FILE_INVALID"
    if row["raw_hash"] and canonical_hash(tx) != row["raw_hash"]:
        return None, "RAW_HASH_MISMATCH"
    return tx, None


def insert_signature(ledger: Ledger, row: sqlite3.Row, body: dict) -> None:
    ledger.db.execute(
        """INSERT INTO signatures(
             wallet,signature,person_id,slot,block_time,seen_at,classified_at,
             raw_hash,raw_reference,body,alert_state,alert_reason
           ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            row["wallet"], row["signature"], row["person_id"], row["slot"],
            row["block_time"], row["seen_at"], row["classified_at"],
            row["raw_hash"], row["raw_reference"], json.dumps(body, sort_keys=True),
            row["alert_state"], row["alert_reason"],
        ),
    )


def replay(path: Path, rows: list[sqlite3.Row], bodies: dict[str, dict], policy: dict) -> dict:
    ledger = Ledger(path)
    for row in rows:
        insert_signature(ledger, row, bodies[row["signature"]])
    engine = Engine(ledger, policy, dry_run=True)
    engine.drain()
    signals = [json.loads(r[0]) for r in ledger.db.execute(
        "SELECT body FROM signals ORDER BY CAST(created_at AS INTEGER),signal_id"
    )]
    states = {}
    for row in ledger.db.execute("SELECT person_id,mint,body FROM v1_states"):
        body = json.loads(row["body"])
        events = body.get("events") or []
        states[(row["person_id"], row["mint"])] = {
            "state": body.get("state"),
            "hft": bool(body.get("hft")),
            "episode_id": body.get("episode_id"),
            "event_count": len(events),
            "buy_count": sum(e.get("direction") == "BUY" for e in events),
            "sell_count": sum(e.get("direction") == "SELL" for e in events),
            "current_raw": body.get("current_raw"),
        }
    summary = engine.summary()
    assert not ledger.db.execute(
        "SELECT 1 FROM outbox WHERE status!='DRY_RUN_AUDIT'"
    ).fetchone(), "NON_DRY_RUN_OUTBOX"
    ledger.db.close()
    return {"signals": signals, "states": states, "summary": summary}


def signal_key(signal: dict) -> tuple:
    return (
        signal.get("mint"),
        signal.get("signal_type"),
        signal.get("stage"),
        signal.get("triggering_signature"),
    )


def source_signal_keys(db: sqlite3.Connection) -> set[tuple]:
    result = set()
    for row in db.execute("SELECT body FROM signals"):
        try:
            result.add(signal_key(json.loads(row["body"])))
        except (TypeError, ValueError):
            continue
    return result


def state_deltas(before: dict, after: dict) -> list[dict]:
    out = []
    for key in sorted(set(before) | set(after)):
        a = before.get(key)
        b = after.get(key)
        if a == b:
            continue
        out.append({
            "person_id": key[0], "mint": key[1],
            "before": a, "after": b,
        })
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--policy", type=Path, required=True)
    p.add_argument("--work", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()

    source = args.source.resolve()
    work = args.work.resolve()
    if work.exists():
        raise ValueError("NEW_ISOLATED_WORKSPACE_REQUIRED")
    if "live" in work.name.lower() or work == source.parent:
        raise ValueError("ISOLATED_NON_LIVE_WORKSPACE_REQUIRED")
    work.mkdir(parents=True, mode=0o700)

    db = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    rows = db.execute(
        "SELECT * FROM signatures ORDER BY block_time,slot,signature"
    ).fetchall()
    stored = {}
    candidate = {}
    transitions = []
    unreclassified = []

    for row in rows:
        try:
            old = json.loads(row["body"])
        except (TypeError, ValueError):
            raise ValueError("SOURCE_BODY_INVALID:" + row["signature"])
        stored[row["signature"]] = old
        tx, error = raw_transaction(row, source)
        if error:
            candidate[row["signature"]] = old
            unreclassified.append({"signature": row["signature"], "reason": error})
            continue
        new = classify(row["signature"], tx, row["wallet"])
        candidate[row["signature"]] = new
        old_pair = (old.get("classification"), old.get("classification_reason"), old.get("trade"))
        new_pair = (new.get("classification"), new.get("classification_reason"), new.get("trade"))
        if old_pair != new_pair:
            transitions.append({
                "signature": row["signature"],
                "block_time": row["block_time"],
                "old_classification": old.get("classification"),
                "old_reason": old.get("classification_reason"),
                "new_classification": new.get("classification"),
                "new_reason": new.get("classification_reason"),
                "old_trade": old.get("trade"),
                "new_trade": new.get("trade"),
                "classification_details": new.get("classification_details"),
            })

    policy = load_policy(args.policy)
    baseline = replay(work / "baseline.sqlite", rows, stored, policy)
    revised = replay(work / "candidate.sqlite", rows, candidate, policy)

    source_keys = source_signal_keys(db)
    baseline_keys = {signal_key(s) for s in baseline["signals"]}
    candidate_keys = {signal_key(s) for s in revised["signals"]}
    baseline_parity = source_keys == baseline_keys

    transition_counts = Counter(
        f"{x['old_classification']}->{x['new_classification']}" for x in transitions
    )
    result = {
        "study": "FRANK_CLASSIFIER_CANDIDATE_REPLAY",
        "source": str(source),
        "source_open_mode": "READ_ONLY",
        "production_files_changed": False,
        "live_signal_sent": False,
        "production_trading": "NO_GO",
        "signature_count": len(rows),
        "reclassified_count": len(rows) - len(unreclassified),
        "unreclassified_count": len(unreclassified),
        "unreclassified": unreclassified,
        "classification_transition_count": len(transitions),
        "classification_transition_counts": dict(sorted(transition_counts.items())),
        "classification_transitions": transitions,
        "baseline": baseline["summary"],
        "candidate": revised["summary"],
        "baseline_signal_parity": baseline_parity,
        "source_signal_count": len(source_keys),
        "baseline_signal_count": len(baseline_keys),
        "candidate_signal_count": len(candidate_keys),
        "new_signals": [
            {"mint": k[0], "signal_type": k[1], "stage": k[2], "triggering_signature": k[3]}
            for k in sorted(candidate_keys - baseline_keys, key=str)
        ],
        "lost_signals": [
            {"mint": k[0], "signal_type": k[1], "stage": k[2], "triggering_signature": k[3]}
            for k in sorted(baseline_keys - candidate_keys, key=str)
        ],
        "state_deltas": state_deltas(baseline["states"], revised["states"]),
        "acceptance": (
            "REVIEW_DELTAS"
            if baseline_parity and not unreclassified
            else "BLOCKED_BASELINE_OR_RAW_COVERAGE"
        ),
    }
    db.close()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "signature_count": result["signature_count"],
        "reclassified_count": result["reclassified_count"],
        "unreclassified_count": result["unreclassified_count"],
        "transition_count": result["classification_transition_count"],
        "transition_counts": result["classification_transition_counts"],
        "baseline_signal_parity": result["baseline_signal_parity"],
        "source_signal_count": result["source_signal_count"],
        "baseline_signal_count": result["baseline_signal_count"],
        "candidate_signal_count": result["candidate_signal_count"],
        "new_signal_count": len(result["new_signals"]),
        "lost_signal_count": len(result["lost_signals"]),
        "state_delta_count": len(result["state_deltas"]),
        "acceptance": result["acceptance"],
        "output": str(args.output),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
