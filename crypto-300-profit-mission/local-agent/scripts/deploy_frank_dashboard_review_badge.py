#!/usr/bin/env python3
"""Explicit dashboard-only rollout with pinned Git sources and database-independent verification.

Dry-run by default; never restart Mission Control, change Gmail state, or send mail.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request
from urllib.parse import quote

# Immutable product revision: product source files were finalized before this
# operations script. Squash merges must never silently change this pin.
COMMIT = "4fe1145aa97b6cc4a3ed27b8e2e39d035fc80fb0"
ROOT = "crypto-300-profit-mission/local-agent/mission_agent/mission_control"
PATCHES = {
    "server.py": {
        "baseline": "b5eb4af5c945cc1b62337d48393fe02243f9505f",
        "legacy": "f5e00781ea4af45b4d6b15a09b8cb000f5b744f4",
        "target": "09a0b66b9fc8ea6f8bf0f8137a6b667ad57f24fd",
    },
    "static/app.js": {
        "baseline": "8f0ac1beace94f01894c151576bc276f48f1b4a4",
        "legacy": "14985b35b019054d5ff9871e002c32421345ff17",
        "target": "ade294d383c4b2acc172d257bf6e22051fc43075",
    },
    "delivery_review.py": {
        "baseline": None,
        "legacy": "62f5fa85bf41cd95e4a31a373910f81970368ea6",
        "target": "643fa250e9cdb08cec1c851f769c787fa2279741",
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
    """Independent sqlite-only breakdown; never invokes DashboardState."""
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
            WHERE NOT (
                (o.channel='gmail' AND o.status IN ('SENT_VERIFIED','DRY_RUN_AUDIT'))
                OR (o.channel='local' AND o.status IN ('COMMAND_ACCEPTED','DRY_RUN_AUDIT'))
            )
        """).fetchall()
        unknown = db.execute("""
            SELECT COUNT(*) FROM decision_outbox
            WHERE NOT (
                (channel='gmail' AND status IN ('SENT_VERIFIED','DRY_RUN_AUDIT'))
                OR (channel='local' AND status IN ('COMMAND_ACCEPTED','DRY_RUN_AUDIT'))
                OR status IN (
                    'PENDING','MANUAL_REVIEW','SENDING','SENT_UNVERIFIED',
                    'PERMANENT_ERROR','CREDENTIAL_BLOCKED',
                    'RETRYABLE_ERROR','RETRY_PENDING'
                )
            )
        """).fetchone()[0]
    finally:
        db.close()
    if unknown:
        raise RuntimeError("UNCLASSIFIED_OUTBOX_STATUS_REQUIRES_REVIEW")
    expired = {"gmail": 0, "local": 0}
    actionable = {"gmail": 0, "local": 0, "other": 0}
    pending = {"gmail": 0, "local": 0, "other": 0}
    queued = {"gmail": 0, "local": 0, "other": 0}
    blocked = {"gmail": 0, "local": 0, "other": 0}
    manual = {"gmail": 0, "local": 0, "other": 0}
    for row in rows:
        channel = row["channel"] if row["channel"] in ("gmail", "local") else "other"
        status = row["status"]
        if status in ("SENDING", "SENT_UNVERIFIED"):
            pending[channel] += 1
            continue
        if status == "PENDING":
            queued[channel] += 1
            continue
        if status in ("CREDENTIAL_BLOCKED", "RETRYABLE_ERROR", "RETRY_PENDING"):
            blocked[channel] += 1
            continue
        if status == "PERMANENT_ERROR":
            actionable[channel] += 1
            continue
        if status != "MANUAL_REVIEW":
            raise RuntimeError("UNCLASSIFIED_OUTBOX_STATUS_REQUIRES_REVIEW")
        manual[channel] += 1
        if channel == "other":
            actionable[channel] += 1
            continue
        try:
            attempts = int(row["attempts"] or 0)
            gmail_attempts = int(row["gmail_attempts"] or 0)
        except (TypeError, ValueError, OverflowError):
            actionable[channel] += 1
            continue
        expired_before_send = (
            (channel == "gmail"
             and row["last_error"] == "GMAIL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND"
             and row["gmail_status"] == "MANUAL_REVIEW"
             and attempts == 0 and gmail_attempts == 0
             and not row["sent_at"] and not row["gmail_message_id"])
            or
            (channel == "local"
             and row["last_error"] == "LOCAL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND"
             and row["local_status"] == "MANUAL_REVIEW"
             and attempts == 0 and not row["delivered_at"])
        )
        (expired if expired_before_send else actionable)[channel] += 1
    return {
        "manual_review_total_count": sum(manual.values()),
        "manual_review_expired_unsent_count": sum(expired.values()),
        "manual_review_expired_unsent_gmail_count": expired["gmail"],
        "manual_review_expired_unsent_local_count": expired["local"],
        "manual_review_actionable_count": sum(actionable.values()),
        "manual_review_actionable_gmail_count": actionable["gmail"],
        "manual_review_actionable_local_count": actionable["local"],
        "manual_review_actionable_other_count": actionable["other"],
        "manual_review_manual_only_total_count": sum(manual.values()),
        "manual_review_manual_only_gmail_count": manual["gmail"],
        "manual_review_manual_only_local_count": manual["local"],
        "manual_review_manual_only_other_count": manual["other"],
        "manual_review_pending_count": sum(pending.values()),
        "manual_review_pending_gmail_count": pending["gmail"],
        "manual_review_pending_local_count": pending["local"],
        "manual_review_pending_other_count": pending["other"],
        "manual_review_queued_count": sum(queued.values()),
        "manual_review_queued_gmail_count": queued["gmail"],
        "manual_review_queued_local_count": queued["local"],
        "manual_review_queued_other_count": queued["other"],
        "manual_review_blocked_count": sum(blocked.values()),
        "manual_review_blocked_gmail_count": blocked["gmail"],
        "manual_review_blocked_local_count": blocked["local"],
        "manual_review_blocked_other_count": blocked["other"],
        "manual_review_visible_total_count": len(rows),
    }


def health_endpoint(control: Path):
    return f"http://127.0.0.1:{dashboard_port(control)}/api/control-health"


def verify_dashboard():
    root = control_root()
    endpoint = health_endpoint(root)
    for _ in range(30):
        try:
            # The live Mission state can legitimately change while waiting.
            # Re-read sqlite on EVERY retry, not just once before the loop.
            expected = actual_delivery_counts(root)
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
        except (OSError, ValueError, TimeoutError, RuntimeError,
                sqlite3.OperationalError):
            time.sleep(0.5)
    raise RuntimeError("DASHBOARD_DATABASE_READBACK_FAILED")


@contextmanager
def deployment_mutex():
    """One active --apply, with no credential paths or system-wide locks."""
    folder = Path.home() / "Library/Application Support/FrankMeme"
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = folder / ".dashboard-review-deploy.lock"
    fd = os.open(path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError("DASHBOARD_DEPLOY_ALREADY_RUNNING") from None
        yield
    finally:
        os.close(fd)


@contextmanager
def interrupted_install_guard():
    """SIGTERM/SIGHUP become rollback-capable InterruptedError; SIGKILL cannot."""
    handlers = {}
    def interrupted(signal_number, frame):
        raise InterruptedError("DASHBOARD_INSTALL_SIGNAL_INTERRUPTED")
    try:
        for kind in (signal.SIGTERM, signal.SIGHUP):
            handlers[kind] = signal.getsignal(kind)
            signal.signal(kind, interrupted)
        yield
    finally:
        for kind, previous in handlers.items():
            signal.signal(kind, previous)


def verify_rollback(root: Path, saved: dict):
    for relative, previous in saved.items():
        data = (root / relative).read_bytes() if (root / relative).is_file() else None
        if data != previous:
            raise RuntimeError("ROLLBACK_FILE_BYTES_MISMATCH_" + relative)
    control = control_root()
    with urllib.request.urlopen(health_endpoint(control), timeout=5) as response:
        result = json.load(response)
        if (not isinstance(result, dict)
                or result.get("status") in (None, "UNKNOWN", "ERROR")):
            raise RuntimeError("ROLLBACK_HTTP_NOT_HEALTHY")
    print("ROLLBACK_READBACK=PASS")


def _replace_bytes(path: Path, data: bytes):
    fd, temp = tempfile.mkstemp(prefix=".frank-review-write-", dir=path.parent)
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


def install(root: Path, new: dict):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)
    backup = Path.home() / "Library/Application Support/FrankMeme/dashboard-review-backups" / stamp
    backup.mkdir(mode=0o700, parents=True, exist_ok=False)
    saved = {}
    # Finish ALL backups before any live product file can be replaced.
    for relative in PATCHES:
        current = root / relative
        data = current.read_bytes() if current.is_file() else None
        saved[relative] = data
        if data is not None:
            location = backup / relative
            location.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
            fd = os.open(location, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "wb") as out:
                out.write(data)
                out.flush()
                os.fsync(out.fileno())
    print("LOCAL_BACKUP=CREATED BACKUP_NAME=" + backup.name, flush=True)
    with interrupted_install_guard():
        try:
            for relative, data in new.items():
                _replace_bytes(root / relative, data)
            restart_dashboard()
            verify_dashboard()
            print("DASHBOARD_UPDATE=SUCCESS")
            print("MISSION_LOOP_RESTART=NO")
            print("DATABASE_WRITE=NO")
            print("EMAIL_SEND=NO")
        except BaseException:
            failures = []
            # Each restoration attempt is independent. One ENOSPC must NOT
            # prevent the remaining files being put back.
            for relative, previous in saved.items():
                try:
                    path = root / relative
                    if previous is None:
                        path.unlink(missing_ok=True)
                    else:
                        _replace_bytes(path, previous)
                except BaseException as exc:
                    failures.append("restore:" + relative + ":" + type(exc).__name__)
            try:
                restart_dashboard()
            except BaseException as exc:
                failures.append("restart:" + type(exc).__name__)
            try:
                verify_rollback(root, saved)
            except BaseException as exc:
                failures.append("verify:" + type(exc).__name__)
            if failures:
                print("ROLLBACK_INCOMPLETE=" + ",".join(failures)
                      + " MANUAL_ACTION_REQUIRED BACKUP_NAME=" + backup.name,
                      file=sys.stderr, flush=True)
                raise RuntimeError("DASHBOARD_ROLLBACK_INCOMPLETE") from None
            print("ROLLBACK=DASHBOARD_FILES_RESTORED", flush=True)
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
    with deployment_mutex():
        # Recheck after locking, as another process may have changed the
        # source since preflight loaded the original version.
        if local_version(root) != version:
            raise RuntimeError("LOCAL_VERSION_CHANGED_BEFORE_APPLY")
        install(root, new)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("DASHBOARD_UPDATE=FAILED " + type(exc).__name__ + " " + str(exc),
              file=sys.stderr)
        raise SystemExit(1)
