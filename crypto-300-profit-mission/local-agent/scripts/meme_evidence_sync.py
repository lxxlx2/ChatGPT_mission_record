#!/usr/bin/env python3
"""Frank/CA evidence export and GitHub sync, separate from trading/alerts.

Commands do not create a LaunchAgent or poll RPC. No local checkout is pushed.
No private key/API key is printed or stored in a snapshot.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

from mission_agent.mission_control.evidence_sync import EvidenceSpool, GitEvidencePublisher
from mission_agent.mission_control.wallet_watch import from_sqlite as read_frank_watchlist


def _frank_health(prod: Path) -> dict:
    p = prod / "health.json"
    if not p.is_file():
        raise FileNotFoundError("FRANK_HEALTH_MISSING")
    value = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("FRANK_HEALTH_INVALID")
    return value


def _local_coverage(dbpath: Path, now: float) -> dict:
    if not dbpath.is_file():
        return {"status": "UNAVAILABLE", "scope": "LOCAL_INDEX_ONLY"}
    # Do not call the model, scanner, Gmail, or writer.
    from mission_agent.mission_control.frank import FrankReader
    return FrankReader(dbpath.parent).activity_coverage(now=now)


def capture_frank(spool: EvidenceSpool, prod: Path) -> dict:
    health = _frank_health(prod)
    if not isinstance(health.get("poll_count"), int) or health.get("poll_count", 0) < 0:
        raise ValueError("FRANK_POLL_COUNT_MISSING")
    if not health.get("last_poll_at"):
        raise ValueError("FRANK_LAST_POLL_UNKNOWN")
    from datetime import datetime
    t = datetime.fromisoformat(str(health["last_poll_at"]).replace("Z", "+00:00")).timestamp()
    coverage = _local_coverage(prod / "forward.sqlite", t)
    from mission_agent.mission_control.frank import FrankReader
    reader = FrankReader(prod)
    try:
        trades = reader.recent_trades(40)
        candidates = reader.candidates()
    except (OSError, ValueError, sqlite3.Error):
        trades, candidates = [], []
    try:
        watch = read_frank_watchlist(prod / "forward.sqlite")
    except (OSError, ValueError, sqlite3.Error):
        watch = {"summary": {"status": "SOURCE_UNAVAILABLE"}, "rows": []}
    path = spool.frank_scan(
        poll_count=health["poll_count"], health=health, coverage=coverage,
        recent_trades=trades, signal_candidates=candidates,
        observed_watchlist=watch,
    )
    return {"status": "QUEUED_LOCALLY", "kind": "frank", "poll_count": health["poll_count"],
            "spool_file": str(path)}


def capture_ca(spool: EvidenceSpool, *, mint: str, job_id: str, report_path: Path) -> dict:
    if not report_path.is_file():
        raise FileNotFoundError("CA_REPORT_NOT_FOUND")
    report = json.loads(report_path.read_text(encoding="utf-8"))
    path = spool.ca_done(mint=mint, job_id=job_id, report=report)
    return {"status": "QUEUED_LOCALLY", "kind": "ca", "spool_file": str(path)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--control-root", type=Path, required=True)
    sub = ap.add_subparsers(dest="command", required=True)
    frank = sub.add_parser("capture-frank", help="Read already-finished local Frank scan")
    frank.add_argument("--production-root", type=Path, required=True)
    ca = sub.add_parser("capture-ca", help="Read already-saved CA JSON report")
    ca.add_argument("--mint", required=True)
    ca.add_argument("--job-id", required=True)
    ca.add_argument("--report", type=Path, required=True)
    sync = sub.add_parser("sync", help="Upload queued sanitized artifacts via gh, then verify Git readback")
    sync.add_argument("--force", action="store_true", help="Also send current 15-min Frank bucket now")
    args = ap.parse_args(argv)
    spool = EvidenceSpool(args.control_root)
    if args.command == "capture-frank":
        result = capture_frank(spool, args.production_root)
    elif args.command == "capture-ca":
        result = capture_ca(spool, mint=args.mint, job_id=args.job_id, report_path=args.report)
    else:
        result = GitEvidencePublisher(spool).sync(force=args.force)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] in {"QUEUED_LOCALLY", "SYNC_OK"} else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, sqlite3.Error, RuntimeError) as exc:
        # Exception *messages* may contain local private paths or URLs; emit class only.
        print(json.dumps({"status": "FAILED", "error_class": type(exc).__name__}), file=sys.stderr)
        sys.exit(2)
