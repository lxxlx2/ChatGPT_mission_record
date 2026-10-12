#!/usr/bin/env python3
"""PR #39 release readiness audit. READ-ONLY; never deploys, sends or restarts.

Checks approved product source, Mission Control local queue, live/old Gmail
identities, and frozen Frank BUY-event payment certainty coverage. Does not
output mint/signature, wallet address, token, credential, or database path.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
from urllib.parse import quote

APPROVED_PRODUCT = "bda7ef0dfd89e6c1b11f9020163bf754bed5ae74"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
REVIEWED_DIRS = ("mission_agent", "config", "scripts/mission_meme_v1.py")
LIVE_UNRESOLVED = {
    "PENDING", "RETRYABLE_ERROR", "CREDENTIAL_BLOCKED",
    "SENDING", "SENT_UNVERIFIED",
}
LOCAL_UNRESOLVED = {"PENDING", "RETRY_PENDING"}


def _git(root: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True, text=True, timeout=12, check=True,
    )
    return done.stdout.strip()


def approved_source_check(root: Path) -> dict:
    """Allow release-only evidence files after the APPROVED product SHA."""
    head = _git(root, "rev-parse", "HEAD")
    clean = not _git(root, "status", "--porcelain")
    changes = _git(root, "diff", "--name-only", APPROVED_PRODUCT, head, "--", *REVIEWED_DIRS)
    if not clean or changes:
        raise ValueError("REVIEWED_PRODUCT_DIFF_OR_WORKTREE_DIRTY")
    # Git's <rev>:<path> syntax is always relative to the repository root,
    # even when 'git -C' starts from a nested local-agent directory.
    prefix = _git(root, "rev-parse", "--show-prefix")
    for relative in ("mission_agent/mission_control/frank.py",
                     "mission_agent/mission_control/service.py",
                     "mission_agent/mission_control/delivery.py",
                     "mission_agent/mission_control/static/app.js"):
        expected = _git(root, "rev-parse", APPROVED_PRODUCT + ":" + prefix + relative)
        observed = _git(root, "hash-object", relative)
        if observed != expected:
            raise ValueError("REVIEWED_PRODUCT_BLOB_MISMATCH")
    return {
        "reviewed_product_pin": APPROVED_PRODUCT,
        "reviewed_product_unchanged": True,
        "worktree_clean": clean,
        "release_branch_head": head,
    }


def readonly_connect(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise ValueError("DATABASE_FILE_UNAVAILABLE")
    connection = sqlite3.connect(
        "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro",
        uri=True, timeout=4, isolation_level=None,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def control_audit(path: Path) -> dict:
    db = readonly_connect(path)
    try:
        if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("CONTROL_SQLITE_QUICK_CHECK_FAILED")
        if db.execute("PRAGMA foreign_key_check").fetchone():
            raise ValueError("CONTROL_SQLITE_FOREIGN_KEY_FAILED")
        expected = {"decision_events", "decision_outbox", "gmail_delivery", "local_delivery"}
        actual = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not expected.issubset(actual):
            raise ValueError("CONTROL_SCHEMA_INCOMPLETE")
        gmail = {
            (row["delivery_mode"], row["status"]): int(row["n"])
            for row in db.execute(
                "SELECT delivery_mode,status,COUNT(*) AS n "
                "FROM gmail_delivery GROUP BY delivery_mode,status"
            )
        }
        local = {row["status"]: int(row["n"]) for row in db.execute(
            "SELECT status,COUNT(*) AS n FROM local_delivery GROUP BY status"
        )}
        outbox = {row["channel"] + ":" + row["status"]: int(row["n"])
                  for row in db.execute(
                      "SELECT channel,status,COUNT(*) AS n "
                      "FROM decision_outbox GROUP BY channel,status"
                  )}
        live_total = sum(count for (mode, _), count in gmail.items() if mode == "LIVE")
        live_unresolved = sum(count for (mode, status), count in gmail.items()
                              if mode == "LIVE" and status in LIVE_UNRESOLVED)
        local_unresolved = sum(count for status, count in local.items()
                               if status in LOCAL_UNRESOLVED)
        presentation_table = "local_delivery_presentation" in actual
        if presentation_table:
            columns = {row["name"] for row in db.execute(
                "PRAGMA table_info(local_delivery_presentation)"
            )}
            if not {"decision_id", "title", "summary", "content_hash"}.issubset(columns):
                raise ValueError("LOCAL_PRESENTATION_SCHEMA_UNEXPECTED")
        return {
            "sqlite_integrity": "ok",
            "historical_live_gmail_count": live_total,
            "live_gmail_in_flight": live_unresolved,
            "local_unresolved": local_unresolved,
            "gmail_by_mode_status": {
                mode + ":" + status: n for (mode, status), n in sorted(gmail.items())
            },
            "local_by_status": local,
            "outbox_by_channel_status": outbox,
            "presentation_table": "PRESENT_COMPATIBLE" if presentation_table else "NOT_YET_CREATED",
            "decision_history_rows": db.execute(
                "SELECT COUNT(*) FROM decision_events"
            ).fetchone()[0],
        }
    finally:
        db.close()


def frank_payment_coverage(path: Path) -> dict:
    db = readonly_connect(path)
    try:
        if "v1_states" not in {
            row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }:
            raise ValueError("FRANK_V1_STATE_TABLE_UNAVAILABLE")
        counts = Counter()
        for row in db.execute("SELECT body FROM v1_states WHERE person_id='frank'"):
            counts["indexed_states"] += 1
            state = json.loads(row["body"])
            events = state.get("events") or []
            buys = [event for event in events if isinstance(event, dict)
                    and event.get("direction") == "BUY"]
            if not buys:
                continue
            counts["states_with_buy"] += 1
            last = buys[-1]
            predicate = last.get("amount_predicate")
            if predicate in (None, ""):
                counts["latest_buy_predicate_missing"] += 1
                if last.get("quote_asset") == USDC:
                    counts["legacy_usdc_quote_predicate_missing"] += 1
            elif predicate == "UNDETERMINED":
                counts["latest_buy_explicitly_uncertain"] += 1
            elif predicate == "USDC_DIRECT_NUMERIC":
                counts["latest_buy_direct_usdc_verified"] += 1
            elif predicate == "SOL_EVENT_TIME_USDC_VERIFIED":
                counts["latest_buy_sol_verified_predicate"] += 1
            else:
                counts["latest_buy_other_predicate"] += 1
        return {k: counts[k] for k in (
            "indexed_states", "states_with_buy", "latest_buy_predicate_missing",
            "legacy_usdc_quote_predicate_missing",
            "latest_buy_explicitly_uncertain", "latest_buy_direct_usdc_verified",
            "latest_buy_sol_verified_predicate", "latest_buy_other_predicate",
        )}
    finally:
        db.close()


def _default_control_db() -> Path:
    pointer = Path.home() / ".frank_meme_control_root"
    text = pointer.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("CONTROL_ROOT_POINTER_EMPTY")
    return Path(text).expanduser() / "mission-control.sqlite"


def _default_frank_db() -> Path:
    return (Path.home() / "Documents/ChatGPT/"
            "crypto-monitor-frank-only-evidence-20261003/live-v1/forward.sqlite")


def collect(source_root: Path, control_db: Path, frank_db: Path) -> dict:
    return {
        "audit": "FRANK_PR39_READ_ONLY_PREDEPLOY",
        "product": approved_source_check(source_root),
        "control": control_audit(control_db),
        "frank_amount_coverage": frank_payment_coverage(frank_db),
        "mutated_production": False,
        "sent_gmail": False,
        "restarted_services": False,
        "merge_performed": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control-db", type=Path)
    parser.add_argument("--frank-db", type=Path)
    parser.add_argument("--source-root", type=Path,
                        default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        report = collect(
            args.source_root,
            args.control_db or _default_control_db(),
            args.frank_db or _default_frank_db(),
        )
        control = report["control"]
        # Historical SENT_VERIFIED Gmail is valid and must NOT be treated as
        # an active send. A claimed zero LIVE *total* is not a safety gate.
        if control["live_gmail_in_flight"] or control["local_unresolved"]:
            report["gate"] = "BLOCKED_ACTIVE_DELIVERY_QUEUE"
            code = 3
        elif report["frank_amount_coverage"]["latest_buy_predicate_missing"]:
            report["gate"] = "REVIEW_REQUIRED_LEGACY_BUY_PREDICATES"
            code = 4
        else:
            report["gate"] = "PASS_READ_ONLY_PREDEPLOY"
            code = 0
        print(json.dumps(report, sort_keys=True, ensure_ascii=False))
        return code
    except (OSError, ValueError, sqlite3.Error, subprocess.SubprocessError,
            json.JSONDecodeError, KeyError, TypeError) as exc:
        print(json.dumps({
            "audit": "FRANK_PR39_READ_ONLY_PREDEPLOY",
            "gate": "BLOCKED_INCOMPLETE_EVIDENCE",
            "error_type": type(exc).__name__,
            "mutated_production": False,
            "sent_gmail": False,
            "restarted_services": False,
        }, sort_keys=True))
        return 5


if __name__ == "__main__":
    sys.exit(main())
