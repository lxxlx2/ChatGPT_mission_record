#!/usr/bin/env python3
"""Explicit dashboard-only rollout with pinned Git sources and database-independent verification.

Dry-run by default; never restart Mission Control, change Gmail state, or send mail.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from urllib.parse import quote

# Immutable product revision: product source files were finalized before this
# operations script. Squash merges must never silently change this pin.
COMMIT = "1014c14b4df00757593f7ca4de8cedae0f09afaa"
ROOT = "crypto-300-profit-mission/local-agent/mission_agent/mission_control"
PATCHES = {
    "server.py": {
        "baseline": "b5eb4af5c945cc1b62337d48393fe02243f9505f",
        "legacy": "f5e00781ea4af45b4d6b15a09b8cb000f5b744f4",
        "target": "9dcf26fe03dadd43f75c401d38ba0e412101be41",
    },
    "static/app.js": {
        "baseline": "8f0ac1beace94f01894c151576bc276f48f1b4a4",
        "legacy": "14985b35b019054d5ff9871e002c32421345ff17",
        "target": "f7880daa425d0a286de0c16836794c62965454ed",
    },
    "delivery_review.py": {
        "baseline": None,
        "legacy": "62f5fa85bf41cd95e4a31a373910f81970368ea6",
        "target": "afa98794136f48762f15fc3cd627866c7f90386a",
    },
}


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def local_dashboard_source():
    runner = Path.home() / "Library/Application Support/FrankMeme/dashboard.sh"
    match = re.search(r'^LOCAL_AGENT="([^"]+)"$', runner.read_text(encoding="utf-8"), re.M)
    if not match:
        raise RuntimeError("DASHBOARD_RUNNER_LOCAL_AGENT_NOT_FOUND")
    root = Path(match.group(1)).expanduser().resolve() / "mission_agent" / "mission_control"
    if not root.is_dir():
        raise RuntimeError("LOCAL_AGENT_SOURCE_MISSING")
    return root


def local_version(root: Path) -> str:
    observed = {
        relative: blob_sha((root / relative).read_bytes()) if (root / relative).is_file() else None
        for relative in PATCHES
    }
    for version in ("target", "legacy", "baseline"):
        if all(observed[relative] == values[version]
               for relative, values in PATCHES.items()):
            return version
    raise RuntimeError("LOCAL_SOURCE_DIFFERENT_OR_PARTIAL_INSTALL")


def verify_javascript(data: bytes):
    fd, path = tempfile.mkstemp(prefix=".frank-review-js-", suffix=".js")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
        subprocess.run(["node", "--check", path], capture_output=True,
                       text=True, timeout=15, check=True)
    finally:
        if os.path.exists(path):
            os.unlink(path)


def preflight(root: Path):
    version = local_version(root)
    verified = {}
    for relative, versions in PATCHES.items():
        uri = ("https://raw.githubusercontent.com/lxxlx2/ChatGPT_mission_record/"
               + COMMIT + "/" + ROOT + "/" + relative)
        with urllib.request.urlopen(uri, timeout=20) as response:
            payload = response.read(150_001)
        if len(payload) > 150_000 or blob_sha(payload) != versions["target"]:
            raise RuntimeError("REMOTE_GIT_BLOB_MISMATCH_" + relative)
        if relative.endswith(".py"):
            compile(payload.decode("utf-8"), relative, "exec")
        if relative.endswith(".js"):
            verify_javascript(payload)
        verified[relative] = payload
    return version, verified


def restart_dashboard():
    label = f"gui/{os.getuid()}/com.{getpass.getuser()}.frank-meme.dashboard"
    subprocess.run(["/bin/launchctl", "kickstart", "-k", label],
                   check=True, capture_output=True, text=True, timeout=20)


def control_root():
    pointer = Path.home() / ".frank_meme_control_root"
    path = Path(pointer.read_text(encoding="utf-8").strip()).expanduser().resolve()
    if not path.is_dir():
        raise RuntimeError("CONTROL_ROOT_NOT_FOUND")
    return path


def dashboard_port(control: Path):
    port_file = control / "dashboard.port"
    if not port_file.is_file():
        port_file = Path.home() / "Library/Application Support/FrankMeme/dashboard_port"
    port = int(port_file.read_text(encoding="utf-8").strip())
    if not 1 <= port <= 65535:
        raise RuntimeError("INVALID_DASHBOARD_PORT")
    return port


def actual_delivery_counts(control: Path):
    path = (control / "mission-control.sqlite").resolve()
    if not path.is_file():
        raise RuntimeError("CONTROL_DB_NOT_FOUND")
    db = sqlite3.connect("file:" + quote(str(path), safe="/") + "?mode=ro",
                         uri=True, timeout=2)
    try:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA query_only=ON")
        rows = db.execute("""
            SELECT o.channel, o.status, o.last_error, o.attempts AS attempts,
                   g.status AS gmail_status, g.attempt_count AS gmail_attempts,
                   g.sent_at, g.gmail_message_id,
                   l.status AS local_status, l.delivered_at
            FROM decision_outbox AS o
            LEFT JOIN gmail_delivery AS g
              ON o.channel='gmail' AND o.decision_id=g.decision_id
            LEFT JOIN local_delivery AS l
              ON o.channel='local' AND o.decision_id=l.decision_id
            WHERE o.status IN ('MANUAL_REVIEW','SENDING','SENT_UNVERIFIED')
        """).fetchall()
    finally:
        db.close()
    expired = 0
    manual = 0
    pending = 0
    by_pending = {"gmail": 0, "local": 0, "other": 0}
    by_actionable = {"gmail": 0, "local": 0, "other": 0}
    by_expired = {"gmail": 0, "local": 0}
    for row in rows:
        channel = row["channel"] if row["channel"] in ("gmail", "local") else "other"
        if row["status"] != "MANUAL_REVIEW":
            pending += 1
            by_pending[channel] += 1
            continue
        manual += 1
        unsent = (
            (channel == "gmail" and row["last_error"] ==
             "GMAIL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND"
             and row["gmail_status"] == "MANUAL_REVIEW"
             and row["attempts"] == 0 and row["gmail_attempts"] == 0
             and not row["sent_at"] and not row["gmail_message_id"])
            or
            (channel == "local" and row["last_error"] ==
             "LOCAL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND"
             and row["local_status"] == "MANUAL_REVIEW"
             and row["attempts"] == 0 and not row["delivered_at"])
        )
        if unsent:
            expired += 1
            by_expired[channel] += 1
        else:
            by_actionable[channel] += 1
    return {
        "manual_review_total_count": manual,
        "manual_review_expired_unsent_count": expired,
        "manual_review_expired_unsent_gmail_count": by_expired["gmail"],
        "manual_review_expired_unsent_local_count": by_expired["local"],
        "manual_review_actionable_count": manual - expired,
        "manual_review_actionable_gmail_count": by_actionable["gmail"],
        "manual_review_actionable_local_count": by_actionable["local"],
        "manual_review_actionable_other_count": by_actionable["other"],
        "manual_review_pending_count": pending,
        "manual_review_pending_gmail_count": by_pending["gmail"],
        "manual_review_pending_local_count": by_pending["local"],
        "manual_review_pending_other_count": by_pending["other"],
        "manual_review_visible_total_count": manual + pending,
    }


def health_endpoint(control: Path):
    return f"http://127.0.0.1:{dashboard_port(control)}/api/control-health"


def verify_dashboard():
    root = control_root()
    expected = actual_delivery_counts(root)
    endpoint = health_endpoint(root)
    for _ in range(30):
        try:
            with urllib.request.urlopen(endpoint, timeout=1.5) as response:
                body = json.load(response)
            if (body.get("manual_review_breakdown_available") is not True
                    or body.get("manual_review_breakdown_error")):
                raise RuntimeError("DASHBOARD_REVIEW_BREAKDOWN_UNAVAILABLE")
            if any(type(body.get(key)) is not int or body[key] != value
                   for key, value in expected.items()):
                raise RuntimeError("DASHBOARD_DATABASE_COUNT_MISMATCH")
            print("DASHBOARD_REVIEW_BREAKDOWN=PASS "
                  f"historical={expected['manual_review_expired_unsent_count']} "
                  f"actionable={expected['manual_review_actionable_count']} "
                  f"pending={expected['manual_review_pending_count']} "
                  f"visible_total={expected['manual_review_visible_total_count']}")
            return
        except (OSError, ValueError, TimeoutError, RuntimeError):
            time.sleep(0.5)
    raise RuntimeError("DASHBOARD_DATABASE_READBACK_FAILED")


def verify_rollback(root: Path, saved: dict):
    for relative, previous in saved.items():
        data = (root / relative).read_bytes() if (root / relative).is_file() else None
        if data != previous:
            raise RuntimeError("ROLLBACK_FILE_BYTES_MISMATCH_" + relative)
    control = control_root()
    with urllib.request.urlopen(health_endpoint(control), timeout=5) as response:
        if not isinstance(json.load(response), dict):
            raise RuntimeError("ROLLBACK_HTTP_NOT_HEALTHY")
    print("ROLLBACK_READBACK=PASS")


def install(root: Path, new: dict):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)
    backup = Path.home() / "Library/Application Support/FrankMeme/dashboard-review-backups" / stamp
    backup.mkdir(mode=0o700, parents=True, exist_ok=False)
    saved = {}
    for relative in PATCHES:
        current = root / relative
        data = current.read_bytes() if current.is_file() else None
        saved[relative] = data
        if data is not None:
            location = backup / relative
            location.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
            with location.open("xb") as out:
                out.write(data)
                out.flush()
                os.fsync(out.fileno())
    print("LOCAL_BACKUP=CREATED")
    try:
        for relative, data in new.items():
            path = root / relative
            fd, temp = tempfile.mkstemp(prefix=".frank-review-", dir=path.parent)
            try:
                os.fchmod(fd, 0o644)
                with os.fdopen(fd, "wb") as out:
                    out.write(data)
                    out.flush()
                    os.fsync(out.fileno())
                os.replace(temp, path)
            finally:
                if os.path.exists(temp):
                    os.unlink(temp)
        restart_dashboard()
        verify_dashboard()
        print("DASHBOARD_UPDATE=SUCCESS")
        print("MISSION_LOOP_RESTART=NO")
        print("DATABASE_WRITE=NO")
        print("EMAIL_SEND=NO")
    except Exception:
        for relative, data in saved.items():
            path = root / relative
            if data is None:
                path.unlink(missing_ok=True)
            else:
                fd, temp = tempfile.mkstemp(prefix=".frank-restore-", dir=path.parent)
                try:
                    with os.fdopen(fd, "wb") as out:
                        out.write(data)
                        out.flush()
                        os.fsync(out.fileno())
                    os.replace(temp, path)
                finally:
                    if os.path.exists(temp):
                        os.unlink(temp)
        restart_dashboard()
        verify_rollback(root, saved)
        print("ROLLBACK=DASHBOARD_FILES_RESTORED")
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Explicitly replace only the three pinned Dashboard product files")
    args = parser.parse_args(argv)
    root = local_dashboard_source()
    version, new = preflight(root)
    print("REMOTE_BLOBS=VERIFIED")
    print("LOCAL_BASELINE=" + version.upper())
    if version == "target":
        if args.apply:
            verify_dashboard()
        print("ALREADY_DEPLOYED=YES")
        return 0
    if not args.apply:
        print("DRY_RUN=PASS")
        return 0
    install(root, new)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("DASHBOARD_UPDATE=FAILED " + type(exc).__name__ + " " + str(exc),
              file=sys.stderr)
        raise SystemExit(1)
