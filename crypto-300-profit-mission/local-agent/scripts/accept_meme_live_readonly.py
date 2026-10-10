#!/usr/bin/env python3
"""Read-only Mac Frank/Control/Dashboard/Sent-receipt state audit.

No LaunchAgent mutations, SQLite writes, HTTP POST, email sends, credentials
reading, network RPC requests, test events, or source deployment.
All timestamps are sampled as observed; never turn historical Sent into live proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import plistlib
import re
import sqlite3
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


HISTORICAL_SENT_DECISION = "30cfdb6f4887953cd05ebaf1ccf8769be85ce74ee7ae23f33f2c5484012a0488"
HISTORICAL_GMAIL_ID = "1a11bbebc6dd49f8"
HTTP_ROUTES = (
    "/api/runtime", "/api/control-health", "/api/candidates",
    "/api/trades", "/api/review-activity", "/api/decisions", "/api/coverage",
)


def read_json(path: Path) -> dict:
    content = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(content, dict):
        raise ValueError("EXPECTED_JSON_OBJECT")
    return content


def seconds_old(value, now: float | None = None):
    if not value:
        return None
    try:
        when = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if when.tzinfo is None:
            return None
        return round((time.time() if now is None else now) - when.timestamp(), 2)
    except (ValueError, TypeError, OverflowError):
        return None


def db_ro(path: Path):
    if not path.is_file():
        raise FileNotFoundError(path.name)
    conn = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True, timeout=3)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    return conn


def launch_state(label: str) -> dict:
    user_id = os.getuid()
    cmd = subprocess.run(
        ["launchctl", "print", "gui/" + str(user_id) + "/" + label],
        text=True, capture_output=True, timeout=5, check=False,
    )
    if cmd.returncode:
        return {"loaded": False, "running": False}
    output = cmd.stdout
    def field(name):
        match = re.search(r"^\s*" + re.escape(name) + r"\s*=\s*([^\n]+)", output, re.M)
        return match.group(1).strip() if match else None
    return {
        "loaded": True,
        "running": field("state") == "running",
        "pid": int(field("pid")) if (field("pid") or "").isdigit() else None,
        "runs": int(field("runs")) if (field("runs") or "").isdigit() else None,
        "last_exit_code": field("last exit code"),
    }


def plist_state(path: Path) -> dict:
    with path.open("rb") as file:
        info = plistlib.load(file)
    return {
        "exists": True,
        "run_at_load": info.get("RunAtLoad") is True,
        "keep_alive": info.get("KeepAlive") is True,
        "label_matches_filename": path.name == str(info.get("Label")) + ".plist",
    }


def dashboard(port: int) -> dict:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    data = {}
    for path in HTTP_ROUTES:
        req = urllib.request.Request(
            "http://127.0.0.1:" + str(port) + path,
            headers={"Accept": "application/json"},
        )
        try:
            with opener.open(req, timeout=5) as response:
                if response.status != 200:
                    raise ValueError("HTTP_NOT_200")
                if "application/json" not in response.headers.get("Content-Type", ""):
                    raise ValueError("INVALID_CONTENT_TYPE")
                payload = json.load(response)
            if path in {"/api/candidates", "/api/trades", "/api/review-activity", "/api/decisions"}:
                data[path] = {"http_ok": isinstance(payload, list),
                              "items": len(payload) if isinstance(payload, list) else None}
            elif isinstance(payload, dict):
                keep = ("status", "runtime_reason", "delivery_allowed", "scope",
                        "policy_hash", "updated_at", "candidate_error_count")
                data[path] = {k: payload[k] for k in keep if k in payload}
                data[path]["http_ok"] = True
                if path == "/api/runtime":
                    data[path]["heartbeat_age_seconds"] = payload.get("heartbeat_age_seconds")
            else:
                data[path] = {"http_ok": False, "type": type(payload).__name__}
        except Exception as exc:
            data[path] = {"http_ok": False, "error_type": type(exc).__name__}
    return data


def receipt_summary(db_path: Path) -> dict:
    with db_ro(db_path) as conn:
        status = dict(conn.execute(
            "SELECT status, count(*) AS n FROM gmail_delivery GROUP BY status"
        ).fetchall())
        outbox = dict(conn.execute(
            "SELECT status, count(*) AS n FROM decision_outbox "
            "WHERE channel='gmail' GROUP BY status"
        ).fetchall())
        decisions = conn.execute("SELECT count(*) FROM decision_events").fetchone()[0]
        recent = conn.execute(
            "SELECT decision_id,decision,created_at FROM decision_events "
            "ORDER BY rowid DESC LIMIT 3"
        ).fetchall()
        match = conn.execute(
            "SELECT status,readback_verified,gmail_message_id,delivery_forbidden,"
            "delivery_mode,content_hash FROM gmail_delivery WHERE decision_id=?",
            (HISTORICAL_SENT_DECISION,),
        ).fetchone()
    check = {
        "historical_mail_2026_10_08_in_local_db": match is not None,
        "gmail_sent_confirmed_outside_mac": True,
        "local_receipt_id_matches_gmail_sent": (
            (match["gmail_message_id"] == HISTORICAL_GMAIL_ID)
            if match is not None else None
        ),
        "local_readback_verified": (
            match["status"] == "SENT_VERIFIED" and
            match["readback_verified"] == 1 and
            match["delivery_forbidden"] == 0 and
            match["delivery_mode"] == "LIVE"
            if match is not None else None
        ),
        "local_receipt_status": match["status"] if match is not None else "NOT_PRESENT",
    }
    return {"gmail_status_counts": status, "outbox_status_counts": outbox,
            "decision_events": decisions,
            "last_three_decisions": [
                {"decision": x["decision"], "at": x["created_at"],
                 "id_prefix": x["decision_id"][:12]} for x in recent
            ], "historical_identity": check}


def writer_summary(health: dict) -> dict:
    return {k: health.get(k) for k in (
        "status", "poll_count", "last_successful_poll", "last_poll_at",
        "source_drift", "production_trading", "consecutive_errors",
        "lag_seconds", "raw_pending", "model_unprocessed",
        "restart_count",
    )} | {"successful_poll_age_seconds": seconds_old(health.get("last_successful_poll"))}


def run(home: Path, wait: float = 36.0) -> dict:
    app = home / "Library/Application Support/FrankMeme"
    prod = home / "Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/live-v1"
    plist_dir = home / "Library/LaunchAgents"
    user = os.environ.get("USER") or subprocess.check_output(
        ["id", "-un"], text=True, timeout=5,
    ).strip()
    root_file = home / ".frank_meme_control_root"
    control = Path(root_file.read_text().strip()).expanduser()
    if not control.is_dir():
        raise ValueError("CONTROL_ROOT_MISSING")
    port_text = (app / "dashboard_port").read_text().strip()
    port = int(port_text)
    if not 1 <= port <= 65535:
        raise ValueError("INVALID_DASHBOARD_PORT")
    label_loop = "com." + user + ".frank-meme.loop"
    label_dash = "com." + user + ".frank-meme.dashboard"
    policy = app / "follow_policy_v1.approved.json"
    pinned = (app / "approved_policy_sha256").read_text().strip()
    policy_match = hashlib.sha256(policy.read_bytes()).hexdigest() == pinned
    result = {
        "check_kind": "READ_ONLY_NO_RESTART_NO_SEND",
        "local_sample_at": datetime.now(timezone.utc).isoformat(),
        "control_exists": True,
        "approved_policy_pin_matches": policy_match,
        "launch_agents": {
            "loop": {**launch_state(label_loop),
                     **plist_state(plist_dir / (label_loop + ".plist"))},
            "dashboard": {**launch_state(label_dash),
                          **plist_state(plist_dir / (label_dash + ".plist"))},
        },
        "dashboard": dashboard(port),
        "local_gmail": receipt_summary(control / "mission-control.sqlite"),
    }
    before_writer = read_json(prod / "health.json")
    before_loop = read_json(control / "mission-control-health.json")
    if wait:
        time.sleep(wait)
    after_writer = read_json(prod / "health.json")
    after_loop = read_json(control / "mission-control-health.json")
    result["writer"] = writer_summary(after_writer)
    result["writer"]["poll_count_increment"] = (
        after_writer.get("poll_count", 0) - before_writer.get("poll_count", 0)
        if isinstance(after_writer.get("poll_count"), int) and
        isinstance(before_writer.get("poll_count"), int) else None
    )
    result["loop_health"] = {
        "status": after_loop.get("status"),
        "age_seconds": seconds_old(after_loop.get("updated_at")),
        "changed_during_sample": after_loop.get("updated_at") != before_loop.get("updated_at"),
        "delivery_allowed": after_loop.get("delivery_allowed"),
        "candidate_error_count": after_loop.get("candidate_error_count"),
    }
    endpoints = result["dashboard"]
    agent_ok = all(v.get("running") and v.get("run_at_load") and
                   v.get("keep_alive") and v.get("label_matches_filename")
                   for v in result["launch_agents"].values())
    api_ok = all(v.get("http_ok") is True for v in endpoints.values())
    runtime_live = (endpoints["/api/runtime"].get("status") == "LIVE")
    control_ok = (after_loop.get("status") == "OK" and
                  after_loop.get("delivery_allowed") is True)
    writer_ok = (after_writer.get("status") == "RUNNING" and
                 after_writer.get("source_drift") is False and
                 after_writer.get("production_trading") == "NO_GO" and
                 (result["writer"]["successful_poll_age_seconds"] is not None and
                  0 <= result["writer"]["successful_poll_age_seconds"] <= 90))
    result["gates"] = {
        "INSTALLED_LAUNCHAGENTS": "PASS" if agent_ok else "FAIL",
        "DASHBOARD_READONLY_API": "PASS" if api_ok else "FAIL",
        "FRANK_RUNTIME_CURRENT": "PASS" if runtime_live and writer_ok else "FAIL",
        "MISSION_CONTROL_CURRENT": "PASS" if control_ok and
            result["loop_health"]["age_seconds"] is not None and
            0 <= result["loop_health"]["age_seconds"] <= 180 else "FAIL",
        "POLICY_PIN": "PASS" if policy_match else "FAIL",
        "WRITER_ADVANCED_DURING_SAMPLE": (
            "PASS" if result["writer"]["poll_count_increment"] is not None and
            result["writer"]["poll_count_increment"] > 0 else
            "NOT_PROVEN" if wait == 0 else "FAIL"
        ),
        "CONTROL_ADVANCED_DURING_SAMPLE": (
            "PASS" if result["loop_health"]["changed_during_sample"] else
            "NOT_PROVEN" if wait == 0 else "FAIL"
        ),
        "GMAIL_SENT_CURRENT_HEAD_END_TO_END": "NOT_RUN_NO_NEW_MAIL_SENT",
        "MAC_REBOOT_LOGIN_RECOVERY": "NOT_RUN_NO_REBOOT",
        "MAIN_MERGE": "NO",
        "PRODUCTION_TRADING": "NO_GO",
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait-seconds", type=float, default=36)
    args = parser.parse_args()
    if not 0 <= args.wait_seconds <= 60:
        parser.error("--wait-seconds must be between 0 and 60")
    try:
        result = run(Path.home(), wait=args.wait_seconds)
    except Exception as exc:
        print(json.dumps({
            "status": "FAIL", "check_kind": "READ_ONLY_NO_RESTART_NO_SEND",
            "error_type": type(exc).__name__,
            "error_code": str(exc) if isinstance(exc, ValueError) else "INSPECTION_FAILED",
        }, ensure_ascii=False))
        raise SystemExit(1)
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    if "FAIL" in result["gates"].values():
        raise SystemExit(1)


if __name__ == "__main__":
    main()
