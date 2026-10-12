#!/usr/bin/env python3
"""Mac Mission Loop upgrade safety preflight: STRICTLY READ-ONLY, no switch.

Requires running loop and dashboard. Pins the already-merged Frank PR34 source,
reads the installed live-delivery policy and SQLite via mode=ro, takes SQLite
consistent snapshots to a disposable directory, validates cloned schema with
new source code, and evaluates at-risk old pending Gmail/local notifications.
Never calls live cycle/loop, OAuth ready(), Gmail, RPC, Git push or launchctl
kickstart. Results contain only statuses and aggregate counts (no identities).
"""
from __future__ import annotations

from collections import Counter
from contextlib import closing
import getpass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
from urllib.parse import quote
import zipfile

PIN = "6a5b7e8a533f99c871e31f9674329fcb4f929cc2"
SUPPORT = Path.home() / "Library/Application Support/FrankMeme"
LOOP = SUPPORT / "mission-loop.sh"
DASH = SUPPORT / "dashboard.sh"
CONTROL_POINTER = Path.home() / ".frank_meme_control_root"
OUTPUT_PREFIX = "frank-loop-upgrade-preflight-"
REQUIRED_TABLES = ("decision_outbox", "gmail_delivery", "local_delivery",
                   "decision_events", "decision_snapshots", "candidate_latest")
CLOSED_GMAIL = {"SENT_VERIFIED", "PERMANENT_ERROR", "DRY_RUN_AUDIT", "MANUAL_REVIEW"}
UNCERTAIN_GMAIL = {"SENDING", "SENT_UNVERIFIED"}
CLOSED_LOCAL = {"COMMAND_ACCEPTED", "DRY_RUN_AUDIT", "MANUAL_REVIEW"}
checks = {}
details = {}
phase = "START"


def check(name: str, condition: bool):
    checks[name] = "PASS" if condition else "FAIL"
    print(f"{name}={checks[name]}", flush=True)
    if not condition:
        raise RuntimeError("FAILED_" + name)


def read_kv(text: str, key: str) -> str:
    matches = re.findall(r"^" + re.escape(key) + r'="([^"\n]+)"\s*$', text, flags=re.M)
    if len(matches) != 1 or not matches[0]:
        raise ValueError("RUNNER_FIELD_INVALID_" + key)
    return matches[0]


def launch_pid(label: str) -> int:
    raw = subprocess.run(["/bin/launchctl", "print", label],
                         capture_output=True, text=True, timeout=10)
    if raw.returncode:
        raise RuntimeError("LAUNCH_AGENT_NOT_LOADED")
    match = re.search(r"^\s*pid = ([0-9]+)\s*$", raw.stdout, re.M)
    if not match:
        raise RuntimeError("LAUNCH_AGENT_NOT_RUNNING")
    return int(match.group(1))


def query_ro(path: Path) -> sqlite3.Connection:
    uri = "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, isolation_level=None, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only=ON")
    conn.execute("PRAGMA busy_timeout=1000")
    return conn


def snapshot_sqlite(src: Path, dest: Path):
    with closing(query_ro(src)) as read:
        with sqlite3.connect(dest) as write:
            read.backup(write)
            check("SNAPSHOT_SQLITE_INTEGRITY",
                  write.execute("PRAGMA integrity_check").fetchone()[0] == "ok")
    dest.chmod(0o600)


def counters(db: sqlite3.Connection):
    all_tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    check("CONTROL_SCHEMA_TABLES", set(REQUIRED_TABLES).issubset(all_tables))
    d = {}
    for table in REQUIRED_TABLES:
        d[table] = int(db.execute("SELECT COUNT(*) FROM " + table).fetchone()[0])
    for table in ("decision_outbox", "gmail_delivery", "local_delivery"):
        d[table + "_by_status"] = sorted((
            str(row["status"]), int(row["n"]),
        ) for row in db.execute(f"SELECT status, COUNT(*) AS n FROM {table} GROUP BY status"))
    return d


def decision_age_seconds(raw: str | None, now: datetime) -> float | None:
    if not raw or not isinstance(raw, str):
        return None
    try:
        stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            return None
        return (now - stamp).total_seconds()
    except (ValueError, OverflowError, TypeError):
        return None


def inspect_authorization_artifacts(current: dict[str, Path]) -> bool:
    """Report only file-type presence, never credential bytes or filesystem paths."""
    auth_files = {
        "POLICY_JSON_PRESENT": current["POLICY"].is_file(),
        "APPROVED_SHA256_FILE_PRESENT": current["APPROVED_HASH_FILE"].is_file(),
        "SOLANA_RPC_FILE_PRESENT": current["RPC_FILE"].is_file(),
    }
    for label, present in auth_files.items():
        checks[label] = "PASS" if present else "FAIL"
        print(f"{label}={checks[label]}", flush=True)
    details["missing_authorization_artifacts"] = [
        label for label, present in auth_files.items() if not present
    ]
    return all(auth_files.values())


def classify_pending(db: sqlite3.Connection, max_age_seconds: int, now: datetime):
    result = Counter()
    rows = db.execute("""
        SELECT g.status, g.delivery_forbidden, g.gmail_message_id,
               e.created_at AS decision_created_at
        FROM gmail_delivery AS g
        LEFT JOIN decision_events AS e ON e.decision_id=g.decision_id
    """).fetchall()
    for row in rows:
        status = row["status"]
        forbidden = int(row["delivery_forbidden"] or 0)
        if forbidden:
            if status != "DRY_RUN_AUDIT":
                result["gmail_forbidden_non_audit"] += 1
            continue
        if status in CLOSED_GMAIL:
            result["gmail_closed"] += 1
            continue
        age = decision_age_seconds(row["decision_created_at"], now)
        if status in UNCERTAIN_GMAIL or row["gmail_message_id"]:
            result["gmail_uncertain_readback_only"] += 1
        elif age is None:
            result["gmail_unsent_timestamp_unknown"] += 1
        elif age > max_age_seconds:
            result["gmail_unsent_stale_review"] += 1
        else:
            result["gmail_potential_fresh_send"] += 1
    rows = db.execute("""
        SELECT l.status, e.created_at AS decision_created_at
        FROM local_delivery AS l
        LEFT JOIN decision_events AS e ON e.decision_id=l.decision_id
    """).fetchall()
    for row in rows:
        if row["status"] in CLOSED_LOCAL:
            result["local_closed"] += 1
            continue
        age = decision_age_seconds(row["decision_created_at"], now)
        if age is None or age > max_age_seconds:
            result["local_stale_or_unknown"] += 1
        else:
            result["local_potential_fresh_notification"] += 1
    return dict(sorted(result.items()))


def isolated_schema_probe(venv_python: Path, agent: Path, control_snapshot: Path):
    # New code initializes its ControlDB only against a throw-away SQLite copy.
    # No decision cycle, no Gmail credentials, no network clients are created.
    source = """
import json, sqlite3, sys
from mission_agent.mission_control.db import ControlDB
path = sys.argv[1]
db = ControlDB(path)
try:
    print(json.dumps({
        "control_integrity": db.db.execute("PRAGMA integrity_check").fetchone()[0],
        "table_count": db.db.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    }))
finally:
    db.close()
"""
    env = os.environ.copy()
    for key in tuple(env):
        if "GMAIL" in key or "TOKEN" in key or "RPC" in key or "GH_" in key or "GITHUB" in key:
            env.pop(key, None)
    env["PYTHONPATH"] = str(agent)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run([str(venv_python), "-c", source, str(control_snapshot)],
                          capture_output=True, text=True, timeout=25,
                          env=env, cwd=agent)
    check("CLONED_NEW_SCHEMA_BOOTSTRAP", proc.returncode == 0)
    parsed = json.loads(proc.stdout)
    check("CLONED_NEW_SCHEMA_INTEGRITY", parsed.get("control_integrity") == "ok")


def check_post_clone_status(clone_path: Path, before: dict) -> None:
    """Read only disposable copied DB; expose sanitized error codes, not paths."""
    sidecar = clone_path.parent
    details["clone_wal_sidecar_present"] = (
        sidecar / (clone_path.name + "-wal")).is_file()
    details["clone_shm_sidecar_present"] = (
        sidecar / (clone_path.name + "-shm")).is_file()
    details["clone_stage"] = "POST_CLONE_OPEN_READONLY"
    try:
        with closing(query_ro(clone_path)) as db:
            check("POST_CLONE_READONLY_REOPEN", True)
            # The subprocess just validated PRAGMA integrity_check=ok on this
            # exact disposable clone after initializing the new ControlDB.
            # Do not issue a redundant expensive integrity pragma through a
            # new query_only SQLite connection (macOS WAL/read-only edge);
            # validate readable rows and unchanged decision/delivery state.
            details["clone_stage"] = "POST_CLONE_ROW_READABILITY"
            check("POST_CLONE_ROW_READABLE",
                  db.execute("SELECT COUNT(*) FROM sqlite_master").fetchone()[0] > 0)
            details["clone_stage"] = "POST_CLONE_STATUS_COUNTS"
            after = counters(db)
        details["clone_stage"] = "POST_CLONE_COMPARE_COUNTS"
        check("EXISTING_EVENTS_AND_DELIVERY_UNCHANGED",
              all(before[k] == after[k] for k in before))
        details["clone_stage"] = "COMPLETE"
    except sqlite3.Error as exc:
        details["clone_sqlite_error_name"] = getattr(
            exc, "sqlite_errorname", type(exc).__name__)
        details["clone_sqlite_error_code"] = getattr(
            exc, "sqlite_errorcode", None)
        print("CLONE_SQLITE_ERROR_NAME=" +
              str(details["clone_sqlite_error_name"]), flush=True)
        print("CLONE_FAILED_STAGE=" +
              details["clone_stage"], flush=True)
        raise


def main():
    global phase
    phase = "LIVE_READONLY_PREFLIGHT"
    check("RUNNERS_PRESENT", LOOP.is_file() and DASH.is_file() and CONTROL_POINTER.is_file())
    loop_raw = LOOP.read_text(encoding="utf-8")
    dash_raw = DASH.read_text(encoding="utf-8")
    current = {k: Path(read_kv(loop_raw, k)).expanduser().resolve()
               for k in ("LOCAL_AGENT", "PROD", "VENV", "CONTROL_POINTER", "POLICY",
                         "APPROVED_HASH_FILE", "RPC_FILE")}
    active_dashboard_agent = Path(read_kv(dash_raw, "LOCAL_AGENT")).expanduser().resolve()
    check("CURRENT_DASHBOARD_IS_MERGED_RELEASE",
          (active_dashboard_agent / "mission_agent/mission_control/static/app.js").is_file()
          and "数据库无发送尝试记录" in
          (active_dashboard_agent / "mission_agent/mission_control/static/app.js").read_text(encoding="utf-8"))
    rev = subprocess.run(["/usr/bin/git", "-C", str(active_dashboard_agent),
                          "rev-parse", "HEAD"], capture_output=True, text=True, timeout=8)
    check("DASHBOARD_SOURCE_PINNED_PR34",
          rev.returncode == 0 and rev.stdout.strip() == PIN)
    check("RUNNER_MODE_POLICY_UNCHANGED",
          "mission_meme_v1.py loop" in loop_raw and
          "--live-delivery" in loop_raw and
          "--approved-policy-sha256" in loop_raw)
    control = Path(CONTROL_POINTER.read_text(encoding="utf-8").strip()).expanduser().resolve()
    check("RUNNER_POINTS_TO_CONTROL_POINTER", current["CONTROL_POINTER"] == CONTROL_POINTER)
    check("EXISTING_DB_AND_VENV",
          (current["PROD"] / "forward.sqlite").is_file()
          and (control / "mission-control.sqlite").is_file()
          and (current["VENV"] / "bin/python").is_file())
    label = f"gui/{os.getuid()}/com.{getpass.getuser()}.frank-meme.loop"
    dash_label = f"gui/{os.getuid()}/com.{getpass.getuser()}.frank-meme.dashboard"
    loop_start_pid = launch_pid(label)
    dash_start_pid = launch_pid(dash_label)
    check("LOOP_AND_DASHBOARD_RUNNING", loop_start_pid > 0 and dash_start_pid > 0)
    phase = "AUTHORIZATION"
    check("APPROVED_POLICY_FILES", inspect_authorization_artifacts(current))
    from_source = active_dashboard_agent
    check("MERGED_RELEASE_SOURCE", (from_source / "mission_agent/mission_control/service.py").is_file()
          and (from_source / "mission_agent/mission_control/policy.py").is_file())
    authorized = """
import json, sys
from pathlib import Path
from mission_agent.mission_control.policy import load_policy, live_delivery_policy_authorized
p, h = load_policy(Path(sys.argv[1]))
expected = Path(sys.argv[2]).read_text().strip()
print(json.dumps({"authorized":live_delivery_policy_authorized(p,h,expected),
                  "max_age":p["decision"].get("initial_notification_max_age_seconds"),
                  "policy_schema":p.get("schema_version")}))
"""
    env = os.environ.copy()
    for k in tuple(env):
        if "GMAIL" in k or "TOKEN" in k or "RPC" in k or "GH_" in k or "GITHUB" in k:
            env.pop(k, None)
    env["PYTHONPATH"] = str(from_source)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run([str(current["VENV"] / "bin/python"), "-c", authorized,
                           str(current["POLICY"]), str(current["APPROVED_HASH_FILE"])],
                          capture_output=True, text=True, timeout=20, env=env, cwd=from_source)
    check("MERGED_POLICY_IMPORT", proc.returncode == 0)
    assessment = json.loads(proc.stdout)
    check("APPROVED_POLICY_IDENTITY", assessment.get("authorized") is True)
    max_age = assessment.get("max_age")
    check("DECISION_AGE_GATE", type(max_age) is int and 60 <= max_age <= 3600)
    details["decision_max_age_seconds"] = max_age
    # Check file permission and presence, not credential content or OAuth refresh.
    try:
        config = json.loads((current["PROD"] / "gmail-existing-source.json").read_text(encoding="utf-8"))
        credential = Path(config["existing_oauth_file"]).expanduser().resolve()
        allowed = credential.is_file() and credential.stat().st_mode & 0o077 == 0
    except (OSError, ValueError, KeyError, TypeError):
        allowed = False
    check("OAUTH_FILE_OWNER_ONLY_PERMISSION", allowed)
    health = control / "mission-control-health.json"
    check("LIVE_LOOP_HEALTH_PRESENT", health.is_file())
    try:
        health_info = json.loads(health.read_text(encoding="utf-8"))
        heartbeat_age = decision_age_seconds(
            health_info.get("updated_at"), datetime.now(timezone.utc))
    except (OSError, ValueError, TypeError, AttributeError):
        heartbeat_age = None
        health_info = {}
    check("LIVE_LOOP_HEALTH_FRESH",
          heartbeat_age is not None and 0 <= heartbeat_age <= 120
          and health_info.get("status") in {"OK", "DEGRADED"})
    phase = "CONSISTENT_SQLITE_SNAPSHOTS"
    with tempfile.TemporaryDirectory(prefix="frank-loop-preflight-") as td:
        tmp = Path(td)
        snapshot_sqlite(current["PROD"] / "forward.sqlite", tmp / "forward.sqlite")
        snapshot_sqlite(control / "mission-control.sqlite", tmp / "mission-control.sqlite")
        with closing(query_ro(tmp / "mission-control.sqlite")) as db:
            before = counters(db)
            risk = classify_pending(db, max_age, datetime.now(timezone.utc))
        details["outbox_status_totals"] = before["decision_outbox_by_status"]
        details["gmail_status_totals"] = before["gmail_delivery_by_status"]
        details["local_status_totals"] = before["local_delivery_by_status"]
        details["delivery_risk_totals"] = risk
        phase = "UPGRADE_CLONE_COMPATIBILITY"
        isolated_schema_probe(current["VENV"] / "bin/python", from_source, tmp / "mission-control.sqlite")
        check_post_clone_status(tmp / "mission-control.sqlite", before)
    phase = "NOTIFICATION_REPLAY_GATE"
    check("NO_FRESH_SENDABLE_LEGACY_GMAIL",
          risk.get("gmail_potential_fresh_send", 0) == 0
          and risk.get("gmail_forbidden_non_audit", 0) == 0)
    check("NO_FRESH_SENDABLE_LOCAL_NOTIFICATION",
          risk.get("local_potential_fresh_notification", 0) == 0)
    phase = "NO_RESTART_ASSERTIONS"
    check("EXISTING_LOOP_PID_UNCHANGED", launch_pid(label) == loop_start_pid)
    check("EXISTING_DASHBOARD_PID_UNCHANGED", launch_pid(dash_label) == dash_start_pid)
    print("PRECHECK=PASS_NEW_LOOP_NOT_DEPLOYED", flush=True)


if __name__ == "__main__":
    failure = None
    try:
        main()
    except Exception as e:
        failure = phase + ":" + type(e).__name__
        print("PRECHECK=BLOCKED:" + failure, flush=True)
    finally:
        result = {
            "schema": 1,
            "target_release": PIN,
            "run_at_utc": datetime.now(timezone.utc).isoformat(),
            "checks": checks,
            "details": details,
            "failure_stage_type": failure,
            "existing_loop_restarted_by_this_script": False,
            "existing_dashboard_restarted_by_this_script": False,
            "gmail_send_attempted_by_this_script": False,
            "production_database_write_attempted": False,
            "github_push_attempted": False,
            "new_mission_loop_deployed": False,
        }
        out = Path.home() / "Downloads"
        out.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = out / f"{OUTPUT_PREFIX}{stamp}.zip"
        with zipfile.ZipFile(filename, mode="x", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("preflight.json", json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        print("RESULT_ARCHIVE=" + str(filename), flush=True)
        print("MISSION_LOOP_RESTART=NO GMAIL_SEND=NO POLICY_CHANGE=NO GIT_PUSH=NO", flush=True)
        if Path("/usr/bin/open").is_file():
            subprocess.run(["/usr/bin/open", "-R", str(filename)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sys.exit(0 if failure is None else 3)
