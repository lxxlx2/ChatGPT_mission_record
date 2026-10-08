"""Read-only, concurrency-tolerant integrity snapshots for isolated Meme CA acceptance.

The live Frank scanner legitimately appends signatures and updates health ticks.
Check immutable existing ledger rows, schema and stable health configuration.
This is evidence of selected invariants, not proof that no live process wrote.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

VOLATILE_HEALTH_KEYS = frozenset({
    "last_successful_poll", "lag_seconds", "last_chain_signature",
    "last_local_signature", "consecutive_errors", "last_error", "status",
    "last_heartbeat", "last_successful_scan", "updated_at", "checked_at",
    "generated_at", "last_cycle_at", "last_scan_at", "poll_count", "pid",
    "uptime_seconds",
})


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _file_hash(path: Path) -> str:
    if not path.is_file():
        return "MISSING"
    digest = hashlib.sha256()
    with path.open("rb") as src:
        for block in iter(lambda: src.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str).encode("utf-8")


def _health_snapshot(path: Path) -> str:
    content = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        raise ValueError("HEALTH_JSON_NOT_OBJECT")
    # Exclude only expected live progress and heartbeat counters.
    stable = {key: value for key, value in content.items()
              if key not in VOLATILE_HEALTH_KEYS}
    return _digest(_canonical(stable))


def _database_snapshot(path: Path, max_rowid: int | None = None) -> dict:
    if not path.is_file():
        raise ValueError("FORWARD_DB_MISSING")
    uri = path.resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        conn.execute("BEGIN")
        schema = conn.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master "
            "WHERE type IN ('table','index','trigger','view') "
            "AND name NOT LIKE 'sqlite_%' ORDER BY type,name"
        ).fetchall()
        max_seen = conn.execute("SELECT COALESCE(MAX(rowid),0) FROM signatures").fetchone()[0]
        limit = max_seen if max_rowid is None else max_rowid
        if max_seen < limit:
            raise ValueError("SOURCE_LEDGER_ROWS_REMOVED")
        hasher = hashlib.sha256()
        count = 0
        for row in conn.execute(
            "SELECT wallet,signature,person_id,slot,block_time,raw_hash,raw_reference "
            "FROM signatures WHERE rowid<=? ORDER BY rowid", (limit,)
        ):
            hasher.update(_canonical(row) + b"\n")
            count += 1
        return {"schema_sha256": _digest(_canonical(schema)),
                "max_rowid": int(limit), "immutable_prefix_rows": count,
                "immutable_prefix_sha256": hasher.hexdigest()}
    finally:
        conn.close()


def capture(prod: Path, loop_plist: Path, dash_plist: Path,
            *, max_rowid: int | None = None) -> dict:
    return {"version": 1,
            "db": _database_snapshot(prod / "forward.sqlite", max_rowid),
            "health_stable_sha256": _health_snapshot(prod / "health.json"),
            "launchagent_sha256": {
                "loop": _file_hash(loop_plist),
                "dashboard": _file_hash(dash_plist),
            }}


def verify(before: dict, prod: Path, loop_plist: Path, dash_plist: Path) -> dict:
    if before.get("version") != 1:
        raise ValueError("INTEGRITY_BASELINE_INVALID")
    after = capture(prod, loop_plist, dash_plist,
                    max_rowid=int(before["db"]["max_rowid"]))
    if after != before:
        raise RuntimeError("IMMUTABLE_LEDGER_OR_STABLE_HEALTH_OR_PLIST_CHANGED")
    return {"status": "PASS", "scope": "IMMUTABLE_PREFIX_AND_STABLE_HEALTH",
            "baseline_rows": before["db"]["immutable_prefix_rows"],
            "heartbeat_updates_allowed": True,
            "new_live_rows_allowed": True}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("capture", "verify"))
    parser.add_argument("--prod", type=Path, required=True)
    parser.add_argument("--loop-plist", type=Path, required=True)
    parser.add_argument("--dash-plist", type=Path, required=True)
    parser.add_argument("--before", type=Path)
    args = parser.parse_args()
    if args.operation == "capture":
        print(json.dumps(capture(args.prod, args.loop_plist, args.dash_plist),
                         sort_keys=True))
    else:
        if args.before is None:
            parser.error("--before is required for verify")
        before = json.loads(args.before.read_text(encoding="utf-8"))
        print(json.dumps(verify(before, args.prod, args.loop_plist,
                                args.dash_plist), sort_keys=True))


if __name__ == "__main__":
    main()
