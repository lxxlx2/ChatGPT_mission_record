#!/usr/bin/env python3
"""Frank Mission Loop ONLY: opt-in, pinned-code, reversible Mac rollout.

Default: prepare/verify without restarting a daemon. Actual restart requires
both --apply-loop and --approve-fresh-alerts. A separate exact vetted read-only
preflight is required immediately beforehand in either mode.

NEVER replaces production SQLite, approved policy, Gmail tokens or RPC secrets,
and NEVER operates on the existing Dashboard LaunchAgent.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import fcntl
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
from urllib.parse import quote

PIN = "6a5b7e8a533f99c871e31f9674329fcb4f929cc2"
CHECK_BLOB = "757045184a39467e8e33804450fafdc8b475fe6c"
SUPPORT = Path.home() / "Library/Application Support/FrankMeme"
LOOP_RUNNER = SUPPORT / "mission-loop.sh"
DASH_RUNNER = SUPPORT / "dashboard.sh"
CONTROL_POINTER = Path.home() / ".frank_meme_control_root"
LABEL_PREFIX = f"gui/{os.getuid()}/com.{getpass.getuser()}.frank-meme."
LOOP_LABEL = LABEL_PREFIX + "loop"
DASH_LABEL = LABEL_PREFIX + "dashboard"
BACKUPS = SUPPORT / "release-backups"
WAIT_SECONDS = 600
GMAIL_STATES_ACTIVE = {"PENDING", "RETRYABLE_ERROR", "CREDENTIAL_BLOCKED"}
LOCAL_STATES_ACTIVE = {"PENDING", "RETRY_PENDING"}
GMAIL_TERMINAL = {"SENT_VERIFIED", "MANUAL_REVIEW", "DRY_RUN_AUDIT", "PERMANENT_ERROR"}
LOCAL_TERMINAL = {"COMMAND_ACCEPTED", "MANUAL_REVIEW", "DRY_RUN_AUDIT"}
DECISION_SCOPE_ROOT = "mission_agent"
DECISION_ENTRYPOINTS = ("scripts/mission_meme_v1.py",)


def ensure(name, condition):
    if not condition:
        raise RuntimeError(name + "=BLOCKED")
    print(name + "=PASS", flush=True)


def launch_pid(label):
    result = subprocess.run(["/bin/launchctl", "print", label],
                            capture_output=True, text=True, timeout=12)
    if result.returncode:
        raise RuntimeError("EXPECTED_LAUNCH_AGENT_NOT_LOADED")
    found = re.search(r"^\s*pid = (\d+)\s*$", result.stdout, re.M)
    if not found:
        raise RuntimeError("EXPECTED_LAUNCH_AGENT_PID_NOT_RUNNING")
    return int(found.group(1))


def source_var(text, key):
    values = re.findall(r'^' + re.escape(key) + r'="([^"\n]+)"\s*$', text, re.M)
    if len(values) != 1:
        raise RuntimeError("RUNNER_FIELD_MISSING_OR_DUPLICATE_" + key)
    return Path(values[0]).expanduser().resolve()


def decision_scope_diff(old_agent, new_agent):
    """Fail closed: every Python module of the package is decision-relevant until it is
    reviewed. Ledger/store, delivery, frank, wallet and outcome code all feed decisions,
    so any byte difference must be explicitly approved and is listed by path."""
    def digests(base):
        root = base / DECISION_SCOPE_ROOT
        ensure("DECISION_SCOPE_PRESENT", root.is_dir())
        return {p.relative_to(base).as_posix(): file_sha256(p) for p in root.rglob("*.py")}
    old, new = digests(old_agent), digests(new_agent)
    for relative in DECISION_ENTRYPOINTS:
        for base, digest_map in ((old_agent, old), (new_agent, new)):
            candidate = base / relative
            if candidate.is_file():
                digest_map[relative] = file_sha256(candidate)
    return sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))


def require_git_release(path):
    check = subprocess.run(["/usr/bin/git", "-C", str(path), "rev-parse", "HEAD"],
                           capture_output=True, text=True, timeout=12)
    ensure("RELEASE_EXACT_SHA", check.returncode == 0 and check.stdout.strip() == PIN)
    clean = subprocess.run(["/usr/bin/git", "-C", str(path), "status", "--porcelain"],
                           capture_output=True, text=True, timeout=12)
    ensure("RELEASE_CODE_CLEAN", clean.returncode == 0 and not clean.stdout.strip())
    ensure("RELEASE_ENTRYPOINT_FOUND",
           (path / "scripts/mission_meme_v1.py").is_file()
           and (path / "mission_agent/mission_control/service.py").is_file())


def file_sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_strict_preflight(script, python_bin):
    ensure("PREFLIGHT_SCRIPT_PRESENT", script.is_file() and not script.is_symlink())
    data = script.read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    ensure("PREFLIGHT_EXACT_GIT_BLOB", blob == CHECK_BLOB)
    # run exactly the previously verified check on live configuration. It ONLY
    # creates aggregate-only result ZIP in Downloads, never changes the Loop.
    proc = subprocess.run([str(python_bin), str(script)],
                          capture_output=True, text=True, timeout=100)
    if proc.returncode != 0 or "PRECHECK=PASS_NEW_LOOP_NOT_DEPLOYED" not in proc.stdout:
        print("FRESH_LOOP_PREFLIGHT=BLOCKED (read-only report saved to Downloads)", flush=True)
        raise RuntimeError("FRESH_LOOP_PREFLIGHT_FAILED")
    print("FRESH_LOOP_PREFLIGHT=PASS", flush=True)


def sqlite_ro(db_path):
    uri = "file:" + quote(str(db_path.resolve()), safe="/") + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, isolation_level=None, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    return conn


def delivery_state(db_path):
    with closing(sqlite_ro(db_path)) as db:
        result = {}
        for table in ("gmail_delivery", "local_delivery"):
            rows = db.execute("SELECT decision_id,status FROM " + table).fetchall()
            result[table] = {r["decision_id"]: r["status"] for r in rows}
        return result


def assert_legacy_receipts_unchanged(original, new):
    """Permit forward progress; prohibit missing rows or terminal-to-sendable."""
    advanced = 0
    for table in ("gmail_delivery", "local_delivery"):
        now = new[table]
        terminal = GMAIL_TERMINAL if table == "gmail_delivery" else LOCAL_TERMINAL
        for old_id, old_status in original[table].items():
            if old_id not in now:
                raise RuntimeError("LEGACY_DELIVERY_ROW_MISSING_" + table)
            current_status = now[old_id]
            if old_status in terminal and current_status not in terminal:
                raise RuntimeError("LEGACY_TERMINAL_REGRESSED_" + table)
            if old_status != current_status:
                advanced += 1
    print("LEGACY_DELIVERY_TERMINAL_SAFE=PASS", flush=True)
    print("LEGACY_DELIVERY_PROGRESS_OBSERVED=" + str(advanced), flush=True)


def legacy_stale_sendable_count(db_path, max_age_seconds=600):
    """Read-only rollback gate, fail-closed on unparseable ages or SQL errors."""
    now = datetime.now(timezone.utc)
    total = 0
    with closing(sqlite_ro(db_path)) as db:
        for table, eligible in (("gmail_delivery", GMAIL_STATES_ACTIVE),
                                ("local_delivery", LOCAL_STATES_ACTIVE)):
            rows = db.execute("""
                SELECT d.status, e.created_at
                FROM """ + table + """ AS d
                LEFT JOIN decision_events AS e USING(decision_id)
            """).fetchall()
            for row in rows:
                if row["status"] not in eligible:
                    continue
                raw = row["created_at"]
                try:
                    stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                    age = (now - stamp).total_seconds()
                    # Naive, future and malformed ages cannot be established safe.
                    stale = stamp.utcoffset() is None or age < 0 or age > max_age_seconds
                except (ValueError, TypeError, OverflowError, AttributeError):
                    stale = True
                if stale:
                    total += 1
    return total


def confirm_rollback_safe(db_path):
    """Never restart old unverified code if historical sendable rows are present."""
    try:
        count = legacy_stale_sendable_count(db_path)
    except (OSError, sqlite3.Error, RuntimeError, ValueError):
        print("OLD_LOOP_ROLLBACK=BLOCKED_UNREADABLE_DELIVERY_STATE", flush=True)
        raise RuntimeError("ROLLBACK_LEGACY_STATE_UNREADABLE") from None
    print("LEGACY_STALE_SENDABLE_COUNT=" + str(count), flush=True)
    ensure("LEGACY_ROLLBACK_STALE_GATE", count == 0)


def process_alive(pid):
    """Conservative process check: ps failures never certify old Loop exit."""
    if type(pid) is not int or pid <= 0:
        raise RuntimeError("PID_IDENTITY_UNVERIFIED")
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    result = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "stat="],
                            capture_output=True, text=True, timeout=8)
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError("PROCESS_LIVENESS_UNVERIFIED")
    return not result.stdout.strip().startswith("Z")


def legacy_delivery_code_verified(old_agent, new_agent):
    """Only allow automatic old-code rollback when delivery code is byte-identical.

    Older code may lack the 600s stale-mail guard. Source equivalence is a
    conservative fail-closed gate; it does NOT authorize source/API drift.
    """
    relative = "mission_agent/mission_control/delivery.py"
    old = old_agent / relative
    new = new_agent / relative
    return old.is_file() and new.is_file() and file_sha256(old) == file_sha256(new)


def interrupted(_signum, _frame):
    raise KeyboardInterrupt("RELEASE_INTERRUPTED")


def sqlite_backup(src, dest):
    with closing(sqlite_ro(src)) as read:
        with sqlite3.connect(dest) as write:
            read.backup(write)
            ensure("BACKUP_SQLITE_INTEGRITY",
                   write.execute("PRAGMA integrity_check").fetchone()[0] == "ok")
    dest.chmod(0o600)


def heartbeat(control, *, since=None):
    path = control / "mission-control-health.json"
    content = json.loads(path.read_text(encoding="utf-8"))
    observed = datetime.fromisoformat(content["updated_at"].replace("Z", "+00:00"))
    ensure("HEARTBEAT_TIME_ZONE", observed.tzinfo is not None)
    elapsed = (datetime.now(timezone.utc) - observed).total_seconds()
    ensure("HEARTBEAT_FRESH", 0 <= elapsed <= 120)
    if since is not None:
        ensure("HEARTBEAT_AFTER_NEW_LOOP_START", observed.timestamp() > since)
        ensure("HEARTBEAT_ACCEPTABLE_STATUS",
               content.get("status") in {"OK", "DEGRADED"})
    return content


def runner_with_new_agent(original, before_agent, new_agent):
    old = 'LOCAL_AGENT="' + str(before_agent) + '"'
    new = 'LOCAL_AGENT="' + str(new_agent) + '"'
    ensure("EXACT_RUNNER_AGENT_FIELD", original.count(old) == 1)
    changed = original.replace(old, new, 1)
    # An explicit opt-out protects a release against inherited export-enabled
    # LaunchAgent environments without changing policy or delivery semantics.
    sentinel = 'export MISSION_EVIDENCE_EXPORT_ENABLED=0'
    ensure("NO_EXISTING_EXPORT_OVERRIDE",
           'MISSION_EVIDENCE_EXPORT_ENABLED' not in original)
    insert_before = 'exec env PYTHONPATH=.'
    ensure("EXPECTED_RUNNER_EXEC_LAYOUT", original.count(insert_before) == 1)
    changed = changed.replace(insert_before, sentinel + "\n" + insert_before, 1)
    ensure("NO_OTHER_RUNNER_DIFF",
           changed.replace(sentinel + "\n", "", 1).replace(new, old, 1) == original)
    return changed


def atomic_runner(original_path, content, mode):
    fd, tmp = tempfile.mkstemp(prefix=".mission-loop-release-", dir=original_path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, original_path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def loop_restart():
    subprocess.run(["/bin/launchctl", "kickstart", "-k", LOOP_LABEL],
                   check=True, capture_output=True, text=True, timeout=30)


def wait_for_new_loop(old_pid, control, started_at):
    """New PID + old process definitely gone + post-exit heartbeat.

    Never call rollback simply because a new process is alive but its first
    cycle (including Gmail readiness) exceeded the wait window.
    """
    old_gone_at = None
    successor_pid = None
    for _ in range(WAIT_SECONDS):
        try:
            current_pid = launch_pid(LOOP_LABEL)
            if current_pid != old_pid:
                successor_pid = current_pid
                if not process_alive(old_pid):
                    if old_gone_at is None:
                        old_gone_at = time.time()
                    try:
                        state = heartbeat(control, since=max(started_at, old_gone_at))
                        return current_pid, state
                    except (OSError, RuntimeError, ValueError, KeyError):
                        pass
                else:
                    # A slow exit after kickstart -k is normal: keep polling until the
                    # wait window ends. The post-loop check still fails closed if the
                    # old PID never disappears; no rollback is attempted in that case.
                    pass
        except (OSError, ValueError, KeyError):
            pass
        except RuntimeError as exc:
            if str(exc) == "OLD_LOOP_PROCESS_STILL_ALIVE":
                raise
        time.sleep(1)
    if successor_pid is not None and not process_alive(old_pid):
        raise RuntimeError("NEW_LOOP_ALIVE_HEARTBEAT_NOT_OBSERVED")
    if successor_pid is not None and process_alive(old_pid):
        raise RuntimeError("OLD_LOOP_PROCESS_STILL_ALIVE")
    raise RuntimeError("NEW_LOOP_NOT_RUNNING")


def prepare(args):
    ensure("RUNNERS_AND_POINTER", LOOP_RUNNER.is_file() and not LOOP_RUNNER.is_symlink()
           and DASH_RUNNER.is_file() and CONTROL_POINTER.is_file())
    original_bytes = LOOP_RUNNER.read_bytes()
    ensure("RUNNER_LINE_ENDINGS_NORMAL", b"\r" not in original_bytes)
    original = original_bytes.decode("utf-8")
    dashboard = DASH_RUNNER.read_text(encoding="utf-8")
    old_agent = source_var(original, "LOCAL_AGENT")
    new_agent = source_var(dashboard, "LOCAL_AGENT")
    require_git_release(new_agent)
    ensure("RELEASE_NOT_ALREADY_ACTIVE", old_agent != new_agent)
    old_version = subprocess.run(
        ["/usr/bin/git", "-C", str(old_agent), "rev-parse", "HEAD"],
        capture_output=True, text=True, timeout=10)
    ensure("OLD_LOOP_SOURCE_GIT_SHA_PRESENT",
           old_version.returncode == 0 and
           re.fullmatch(r"[0-9a-f]{40}", old_version.stdout.strip()) is not None)
    old_sha = old_version.stdout.strip()
    legacy_delivery_verified = legacy_delivery_code_verified(old_agent, new_agent)
    print("OLD_DELIVERY_CODE_EQUIVALENT=" +
          ("YES" if legacy_delivery_verified else "NO"), flush=True)
    changed_signal_files = decision_scope_diff(old_agent, new_agent)
    print("OLD_LOOP_SOURCE_SHA=" + old_sha, flush=True)
    print("SIGNAL_CODE_CHANGED_COUNT=" + str(len(changed_signal_files)), flush=True)
    for relative in changed_signal_files:
        print("DECISION_MODULE_CHANGED=" + relative, flush=True)
    needed = ("PROD", "VENV", "CONTROL_POINTER", "POLICY", "APPROVED_HASH_FILE", "RPC_FILE")
    old_fields = {key: source_var(original, key) for key in needed}
    ensure("CANONICAL_CONTROL_POINTER_UNCHANGED", old_fields["CONTROL_POINTER"] == CONTROL_POINTER)
    control = Path(CONTROL_POINTER.read_text(encoding="utf-8").strip()).resolve()
    db = control / "mission-control.sqlite"
    prod = old_fields["PROD"] / "forward.sqlite"
    venv_python = old_fields["VENV"] / "bin/python"
    ensure("LIVE_DBS_AND_PYTHON_PRESENT",
           db.is_file() and prod.is_file() and venv_python.is_file())
    ensure("POLICY_AND_RPC_FILES_PRESENT",
           all(old_fields[k].is_file() for k in ("POLICY", "APPROVED_HASH_FILE", "RPC_FILE")))
    ensure("RPC_FILE_PRIVATE",
           old_fields["RPC_FILE"].stat().st_uid == os.getuid()
           and not (old_fields["RPC_FILE"].stat().st_mode & 0o077))
    loop_pid = launch_pid(LOOP_LABEL)
    dash_pid = launch_pid(DASH_LABEL)
    check_dash = file_sha256(DASH_RUNNER)
    old_script_hash = file_sha256(LOOP_RUNNER)
    heartbeat(control)
    run_strict_preflight(args.preflight_script, Path(sys.executable))
    ensure("LOOP_PID_STILL_RUNNING", launch_pid(LOOP_LABEL) == loop_pid)
    ensure("DASHBOARD_PID_UNCHANGED", launch_pid(DASH_LABEL) == dash_pid)
    ensure("DASHBOARD_SCRIPT_UNCHANGED", file_sha256(DASH_RUNNER) == check_dash)
    ensure("LOOP_SCRIPT_UNCHANGED", file_sha256(LOOP_RUNNER) == old_script_hash)
    change = runner_with_new_agent(original, old_agent, new_agent)
    with tempfile.NamedTemporaryFile(prefix="frank-loop-shell-", delete=True) as shell:
        shell.write(change.encode("utf-8"))
        shell.flush()
        subprocess.run(["/bin/bash", "-n", shell.name], check=True,
                       capture_output=True, text=True, timeout=10)
    print("CANDIDATE_RUNNER_SYNTAX=PASS", flush=True)
    return {
        "original": original, "original_bytes": original_bytes,
        "old_sha": old_sha, "changed_signal_files": changed_signal_files,
        "legacy_delivery_verified": legacy_delivery_verified,
        "candidate": change,
        "db": db, "prod": prod, "control": control,
        "old_agent": old_agent, "new_agent": new_agent,
        "loop_pid": loop_pid, "dashboard_pid": dash_pid,
        "dashboard_sha": check_dash,
        "runner_sha": old_script_hash,
        "mode": LOOP_RUNNER.stat().st_mode & 0o777,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--preflight-script", required=True, type=Path,
                   help="Previously verified exact read-only Mission Loop preflight file")
    p.add_argument("--apply-loop", action="store_true",
                   help="Restart the live Mission Loop once, with automatic runner rollback if unhealthy")
    p.add_argument("--approve-signal-code-change", action="store_true",
                   help="Separately approve version-reviewed changes to frozen signal code")
    p.add_argument("--approve-fresh-alerts", action="store_true",
                   help="Acknowledge legitimate NEW decisions may produce Gmail/desktop alerts after restart")
    args = p.parse_args()
    ensure("EXPLICIT_DOUBLE_APPROVAL",
           not args.apply_loop or args.approve_fresh_alerts)
    SUPPORT.mkdir(mode=0o700, parents=True, exist_ok=True)
    BACKUPS.mkdir(mode=0o700, parents=True, exist_ok=True)
    lock_path = SUPPORT / ".mission-loop-release.lock"
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        context = prepare(args)
        if args.apply_loop:
            ensure("SIGNAL_CODE_DELTA_EXPLICITLY_APPROVED",
                   not context["changed_signal_files"] or
                   args.approve_signal_code_change)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        location = BACKUPS / ("mission-loop-" + stamp + "-" + str(os.getpid()))
        location.mkdir(mode=0o700)
        backup_script = location / "mission-loop.sh.before"
        backup_script.write_bytes(context["original_bytes"])
        backup_script.chmod(0o600)
        sqlite_backup(context["db"], location / "mission-control.sqlite")
        sqlite_backup(context["prod"], location / "forward.sqlite")
        ensure("RUNNER_BACKUP_IDENTICAL",
               file_sha256(backup_script) == file_sha256(LOOP_RUNNER))
        print("BACKUP_CREATED_PRIVATE=YES", flush=True)
        print("BACKUP_RECEIPT_ID=" + location.name, flush=True)
        if not args.apply_loop:
            print("LOOP_SWITCH=NOT_ATTEMPTED_DRY_RUN", flush=True)
            print("DASHBOARD_RESTART=NO LOOP_RESTART=NO GMAIL_SEND_INITIATED=NO", flush=True)
            return
        before = delivery_state(context["db"])
        ensure("LIVE_LOOP_PID_UNCHANGED_BEFORE_SWITCH",
               launch_pid(LOOP_LABEL) == context["loop_pid"])
        ensure("DASHBOARD_PID_UNCHANGED_BEFORE_SWITCH",
               launch_pid(DASH_LABEL) == context["dashboard_pid"])
        ensure("LIVE_RUNNER_UNCHANGED_BEFORE_SWITCH",
               file_sha256(LOOP_RUNNER) == context["runner_sha"])
        changed = False
        previous_sigterm = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGTERM, interrupted)
        try:
            # Does not change the SQLite file, policy, secrets, Dashboard runner,
            # LaunchAgent plist or the already approved delivery rules.
            changed = True
            atomic_runner(LOOP_RUNNER, context["candidate"].encode(),
                          context["mode"])
            started_at = time.time()
            loop_restart()
            new_pid, _ = wait_for_new_loop(context["loop_pid"], context["control"], started_at)
            assert_legacy_receipts_unchanged(before, delivery_state(context["db"]))
            ensure("DASHBOARD_PID_UNCHANGED_POST_SWITCH",
                   launch_pid(DASH_LABEL) == context["dashboard_pid"])
            ensure("DASHBOARD_RUNNER_UNCHANGED_POST_SWITCH",
                   file_sha256(DASH_RUNNER) == context["dashboard_sha"])
            print("LOOP_RELEASE=SUCCESS_NEW_PID_VERIFIED", flush=True)
            print("LOOP_NEW_PID=" + str(new_pid), flush=True)
            print("EVIDENCE_EXPORT=FORCED_OFF", flush=True)
            print("HISTORICAL_DELIVERY_RECEIPTS=UNCHANGED", flush=True)
            print("LEGITIMATE_NEW_ALERTS=ALLOWED_BY_EXISTING_APPROVED_POLICY", flush=True)
        except BaseException:
            if changed:
                # Do not restart an older possibly unsafe agent over a live
                # successor, overlapping old PID or stale/retryable mail.
                current = None
                try:
                    current = launch_pid(LOOP_LABEL)
                except (OSError, RuntimeError):
                    pass
                if current is not None and current != context["loop_pid"] and process_alive(current):
                    print("ROLLBACK=MANUAL_NEW_LOOP_STILL_RUNNING", flush=True)
                elif current == context["loop_pid"] and process_alive(context["loop_pid"]):
                    # Interrupted after replacing the runner but before the
                    # existing Loop was terminated: restore original file
                    # bytes ONLY, never kickstart an extra worker.
                    atomic_runner(LOOP_RUNNER, context["original_bytes"], context["mode"])
                    ensure("RUNNER_ROLLBACK_EXACT_BYTES",
                           file_sha256(LOOP_RUNNER) == context["runner_sha"])
                    print("LOOP_RUNNER_ROLLED_BACK=YES_OLD_LOOP_UNTOUCHED", flush=True)
                elif process_alive(context["loop_pid"]):
                    print("ROLLBACK=MANUAL_OLD_LOOP_STILL_RUNNING", flush=True)
                elif not context["legacy_delivery_verified"]:
                    print("ROLLBACK=MANUAL_OLD_DELIVERY_CODE_UNVERIFIED", flush=True)
                else:
                    try:
                        confirm_rollback_safe(context["db"])
                    except (OSError, RuntimeError, sqlite3.Error):
                        print("ROLLBACK=MANUAL_STALE_OR_UNKNOWN_GMAIL", flush=True)
                    else:
                        try:
                            atomic_runner(LOOP_RUNNER, context["original_bytes"], context["mode"])
                            ensure("RUNNER_ROLLBACK_EXACT_BYTES",
                                   file_sha256(LOOP_RUNNER) == context["runner_sha"])
                            print("LOOP_RUNNER_ROLLED_BACK=YES", flush=True)
                            rollback_started = time.time()
                            loop_restart()
                            wait_for_new_loop(
                                current or context["loop_pid"],
                                context["control"], rollback_started)
                            print("LOOP_ROLLBACK_SERVICE=RECOVERED", flush=True)
                        except BaseException:
                            print("LOOP_ROLLBACK_SERVICE=MANUAL_ATTENTION_REQUIRED", flush=True)
            raise
        finally:
            signal.signal(signal.SIGTERM, previous_sigterm)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # Never print exception strings: could contain user home, private
        # service names, credentials or database paths.
        print("LOOP_RELEASE=BLOCKED " + type(exc).__name__, flush=True)
        sys.exit(3)
