"""Read-only, concurrency-tolerant scoped invariants for Meme CA acceptance.

Live Frank appends signatures and refreshes health. Compare the existing
signature *identity columns*, schema, explicit stable health configuration and
LaunchAgent definitions. Does not cover mutable signature body/alert fields,
other tables or concurrent non-prefix writes. It is not a full DB audit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

# Both real Frank writers have different health schemas. The production
# Ledger writer is scripts/frank_local_signal_service.py (forward.sqlite
# contains signatures/v1_states); the older Repository writer lives elsewhere.
# An explicit allowlist prevents polling counters from raising false FAIL.
# New/unknown keys remain unchecked until the owning writer is audited.
STABLE_HEALTH_KEYS = frozenset({
    # Ledger (production live-v1)
    "system", "policy", "policy_hash", "code_commit",
    "loaded_source_sha256", "delivery_authority",
    "gpt_in_critical_path", "production_trading", "other_persons",
    "new_automation", "poll_interval_seconds",
    # Repository / frank_shadow_service
    "service_source_sha256", "parser_version", "identifier",
    "historical_network_backfill", "gmail", "app_alert",
    "automation_mutations", "production_writes",
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
    # Only confirmed stable configuration keys. The Ledger writer updates
    # poll_count, last_poll_at, status, model, local/raw pending and retry fields
    # during normal scanning. The Repository writer also advances RPC counters.
    stable = {key: content[key] for key in sorted(STABLE_HEALTH_KEYS)
              if key in content}
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
                "max_rowid": int(limit), "identity_prefix_rows": count,
                "identity_prefix_sha256": hasher.hexdigest()}
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
    return {"status": "PASS", "scope": "SIGNATURE_IDENTITY_PREFIX_AND_STABLE_HEALTH",
            "baseline_rows": before["db"]["identity_prefix_rows"],
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
