#!/usr/bin/env python3
"""One-shot Mac local Frank Dashboard evidence check. NO production mutations.

Reads only: dashboard runner's source path, three deployed product source files,
Mission Control SQLite in mode=ro, and localhost /api/control-health.
Never invokes launchctl, Gmail, browser OAuth, RPC, Git, or transactions.
Output contains only aggregate counts and status names (no wallet/email/paths).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sqlite3
from urllib import request
from urllib.parse import quote

PINNED = {
    "server.py": {
        "baseline": "b5eb4af5c945cc1b62337d48393fe02243f9505f",
        "legacy": "f5e00781ea4af45b4d6b15a09b8cb000f5b744f4",
        "target": "8f5124bf46a660fb618371eb113da208b28c775b",
    },
    "static/app.js": {
        "baseline": "8f0ac1beace94f01894c151576bc276f48f1b4a4",
        "legacy": "14985b35b019054d5ff9871e002c32421345ff17",
        "target": "e3aec8f0e0866cc445406562c10bfb78bb5f28e7",
    },
    "delivery_review.py": {
        "baseline": None,
        "legacy": "62f5fa85bf41cd95e4a31a373910f81970368ea6",
        "target": "643fa250e9cdb08cec1c851f769c787fa2279741",
    },
}
STATES = frozenset(("MANUAL_REVIEW", "SENDING", "SENT_UNVERIFIED"))


def blob_sha(value: bytes):
    return hashlib.sha1(b"blob " + str(len(value)).encode() + b"\0" + value).hexdigest()


def dashboard_root():
    runner = Path.home() / "Library/Application Support/FrankMeme/dashboard.sh"
    match = re.search(r'^LOCAL_AGENT="([^"]+)"\s*$', runner.read_text(encoding="utf-8"), re.M)
    if not match:
        raise ValueError("DASHBOARD_SOURCE_UNCONFIGURED")
    root = (Path(match.group(1)).expanduser().resolve()
            / "mission_agent" / "mission_control")
    if not root.is_dir():
        raise ValueError("DASHBOARD_SOURCE_DIRECTORY_UNAVAILABLE")
    return root


def source_state(root: Path):
    blobs = {
        name: blob_sha((root / name).read_bytes()) if (root / name).is_file() else None
        for name in PINNED
    }
    for label in ("target", "legacy", "baseline"):
        if all(blobs[name] == options[label] for name, options in PINNED.items()):
            return label.upper()
    return "UNRECOGNIZED_OR_MIXED"


def control_root():
    pointer = Path.home() / ".frank_meme_control_root"
    root = Path(pointer.read_text(encoding="utf-8").strip()).expanduser().resolve()
    if not root.is_dir():
        raise ValueError("CONTROL_ROOT_UNAVAILABLE")
    return root


def summary_from_database(root: Path):
    path = (root / "mission-control.sqlite").resolve()
    if not path.is_file():
        raise ValueError("CONTROL_SQLITE_UNAVAILABLE")
    uri = "file:" + quote(str(path), safe="/") + "?mode=ro"
    db = sqlite3.connect(uri, uri=True, timeout=2, isolation_level=None)
    try:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        records = [dict(r) for r in db.execute("""
            SELECT o.channel,o.status,o.last_error,o.attempts AS outbox_attempts,
                   g.status AS gmail_status,g.attempt_count AS gmail_attempts,
                   g.sent_at,g.gmail_message_id,
                   l.status AS local_status,l.delivered_at AS local_delivered_at
            FROM decision_outbox o
            LEFT JOIN gmail_delivery g
              ON o.channel='gmail' AND g.decision_id=o.decision_id
            LEFT JOIN local_delivery l
              ON o.channel='local' AND l.decision_id=o.decision_id
            WHERE NOT (
              (o.channel='gmail' AND o.status IN ('SENT_VERIFIED','DRY_RUN_AUDIT'))
              OR (o.channel='local' AND o.status IN ('COMMAND_ACCEPTED','DRY_RUN_AUDIT'))
            )
        """).fetchall()]
        # Group *all* recorded outcomes, not just suspected failures.
        # Status labels are constrained to non-sensitive machine state tokens
        # and unknown channels are aggregated into "other".
        status_rows = db.execute("""
            SELECT channel,status,COUNT(*) AS number
            FROM decision_outbox GROUP BY channel,status
        """).fetchall()
        if len(status_rows) > 128:
            raise ValueError("OUTBOX_STATUS_GROUP_LIMIT_EXCEEDED")
        status_counts = {}
        for row in status_rows:
            channel = row["channel"] if row["channel"] in ("gmail", "local") else "other"
            raw_status = row["status"]
            state = (raw_status if isinstance(raw_status, str) and
                     re.fullmatch(r"[A-Z][A-Z0-9_]{0,63}", raw_status)
                     else "NONSTANDARD_STATUS")
            key = channel + "/" + state
            status_counts[key] = status_counts.get(key, 0) + row["number"]
        hidden = db.execute("""
            SELECT COUNT(*) FROM decision_outbox
            WHERE NOT (
              (channel='gmail' AND status IN ('SENT_VERIFIED','DRY_RUN_AUDIT'))
              OR (channel='local' AND status IN ('COMMAND_ACCEPTED','DRY_RUN_AUDIT'))
              OR status IN (
                'PENDING','MANUAL_REVIEW','SENDING','SENT_UNVERIFIED',
                'PERMANENT_ERROR','CREDENTIAL_BLOCKED','RETRYABLE_ERROR',
                'RETRY_PENDING'
              )
            )
        """).fetchone()[0]
    finally:
        db.close()
    pending = {"gmail": 0, "local": 0, "other": 0}
    queued = {"gmail": 0, "local": 0, "other": 0}
    blocked = {"gmail": 0, "local": 0, "other": 0}
    manual_channels = {"gmail": 0, "local": 0, "other": 0}
    expired = {"gmail": 0, "local": 0}
    actionable = {"gmail": 0, "local": 0, "other": 0}
    for entry in records:
        channel = entry.get("channel")
        if channel not in ("gmail", "local"):
            channel = "other"
        state = entry.get("status")
        if state in ("SENDING", "SENT_UNVERIFIED"):
            pending[channel] += 1
            continue
        if state == "PENDING":
            queued[channel] += 1
            continue
        if state in ("CREDENTIAL_BLOCKED", "RETRYABLE_ERROR", "RETRY_PENDING"):
            blocked[channel] += 1
            continue
        if state == "PERMANENT_ERROR":
            actionable[channel] += 1
            continue
        if state != "MANUAL_REVIEW":
            blocked[channel] += 1
            continue
        manual_channels[channel] += 1
        if channel == "other":
            actionable[channel] += 1
            continue
        try:
            oa = int(entry.get("outbox_attempts") or 0)
            ga = int(entry.get("gmail_attempts") or 0)
        except (TypeError, ValueError, OverflowError):
            actionable[channel] += 1
            continue
        if channel == "gmail":
            old = (entry.get("last_error") ==
                   "GMAIL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND"
                   and entry.get("gmail_status") == "MANUAL_REVIEW"
                   and oa == 0 and ga == 0 and not entry.get("sent_at")
                   and not entry.get("gmail_message_id"))
        else:
            old = (entry.get("last_error") ==
                   "LOCAL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND"
                   and entry.get("local_status") == "MANUAL_REVIEW"
                   and oa == 0 and not entry.get("local_delivered_at"))
        (expired if old else actionable)[channel] += 1
    return {
        "manual_review_total_count": sum(manual_channels.values()),
        "manual_review_expired_unsent_count": sum(expired.values()),
        "manual_review_expired_unsent_gmail_count": expired["gmail"],
        "manual_review_expired_unsent_local_count": expired["local"],
        "manual_review_actionable_count": sum(actionable.values()),
        "manual_review_actionable_gmail_count": actionable["gmail"],
        "manual_review_actionable_local_count": actionable["local"],
        "manual_review_actionable_other_count": actionable["other"],
        "manual_review_manual_only_total_count": sum(manual_channels.values()),
        "manual_review_manual_only_gmail_count": manual_channels["gmail"],
        "manual_review_manual_only_local_count": manual_channels["local"],
        "manual_review_manual_only_other_count": manual_channels["other"],
        "manual_review_blocked_count": sum(blocked.values()),
        "manual_review_blocked_gmail_count": blocked["gmail"],
        "manual_review_blocked_local_count": blocked["local"],
        "manual_review_blocked_other_count": blocked["other"],
        "manual_review_pending_count": sum(pending.values()),
        "manual_review_pending_gmail_count": pending["gmail"],
        "manual_review_pending_local_count": pending["local"],
        "manual_review_pending_other_count": pending["other"],
        "manual_review_queued_count": sum(queued.values()),
        "manual_review_queued_gmail_count": queued["gmail"],
        "manual_review_queued_local_count": queued["local"],
        "manual_review_queued_other_count": queued["other"],
        "manual_review_visible_total_count": len(records),
        "dashboard_hidden_nonsuccess_rows": hidden,
        "outbox_status_counts_by_channel": status_counts,
    }


def local_dashboard_health(root: Path):
    port_file = root / "dashboard.port"
    if not port_file.is_file():
        port_file = Path.home() / "Library/Application Support/FrankMeme/dashboard_port"
    port = int(port_file.read_text(encoding="utf-8").strip())
    if not 1 <= port <= 65535:
        raise ValueError("DASHBOARD_PORT_INVALID")
    uri = f"http://127.0.0.1:{port}/api/control-health"
    with request.urlopen(uri, timeout=3) as result:
        if result.status != 200:
            raise ValueError("DASHBOARD_HTTP_NON_200")
        payload = result.read(200001)
    if len(payload) > 200000:
        raise ValueError("DASHBOARD_HTTP_OVERSIZED")
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError("DASHBOARD_HTTP_INVALID_JSON_ROOT")
    return parsed


def main():
    result = {
        "check": "FRANK_DASHBOARD_ONE_SHOT_READ_ONLY",
        "source_version": "UNAVAILABLE",
        "database_access": "NOT_CHECKED",
        "dashboard_http": "NOT_CHECKED",
        "source_matches_target": False,
        "http_matches_sqlite": False,
        "mac_browser_ui_rendered": False,
        "gmail_sent_readback_verified": False,
        "mac_rollout_performed": False,
        "production_sqlite_modified": False,
        "gmail_sent": False,
        "operational_acceptance": "BLOCKED",
    }
    try:
        result["source_version"] = source_state(dashboard_root())
        result["source_matches_target"] = result["source_version"] == "TARGET"
        control = control_root()
        counts = summary_from_database(control)
        result["database_access"] = "READ_ONLY_OK"
        # This aggregate is diagnostic evidence only, not part of the HTTP
        # contract or its count-parity comparison.
        result["outbox_status_counts_by_channel"] = counts.pop(
            "outbox_status_counts_by_channel")
        result["database_counts"] = counts
        http = local_dashboard_health(control)
        result["dashboard_http"] = "OK"
        result["http_matches_sqlite"] = (
            http.get("manual_review_breakdown_available") is True
            and not http.get("manual_review_breakdown_error")
            and all(type(http.get(key)) is int and http[key] == value
                    for key, value in counts.items()
                    if key != "dashboard_hidden_nonsuccess_rows")
        )
        required_http_fields = [
            k for k in counts if k != "dashboard_hidden_nonsuccess_rows"
        ]
        result["http_missing_count_fields"] = sorted(
            k for k in required_http_fields if type(http.get(k)) is not int
        )
        result["http_mismatched_count_fields"] = sorted(
            k for k in required_http_fields
            if type(http.get(k)) is int and http[k] != counts[k]
        )
        result["dashboard_hidden_nonsuccess_rows"] = counts["dashboard_hidden_nonsuccess_rows"]
        if counts["dashboard_hidden_nonsuccess_rows"]:
            result["operational_acceptance"] = "BLOCKED_DASHBOARD_HIDES_NONSUCCESS_ROWS"
        elif result["source_matches_target"] and result["http_matches_sqlite"]:
            result["operational_acceptance"] = "READ_ONLY_COUNTS_PASS_BROWSER_PENDING"
        elif result["http_missing_count_fields"]:
            result["operational_acceptance"] = "BLOCKED_BACKEND_SCHEMA_MISSING_FIELDS"
        else:
            result["operational_acceptance"] = "BLOCKED_VERSION_OR_COUNTS"
    except (OSError, ValueError, sqlite3.Error, TypeError, KeyError) as exc:
        # No credentials, filenames, wallet, DB row values, or HTTP response
        # bodies in errors. Never disclose raw exception strings.
        result["error_type"] = type(exc).__name__
        result["operational_acceptance"] = "BLOCKED_READ_FAILURE"
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["operational_acceptance"] == "READ_ONLY_COUNTS_PASS_BROWSER_PENDING" else 3


if __name__ == "__main__":
    raise SystemExit(main())
