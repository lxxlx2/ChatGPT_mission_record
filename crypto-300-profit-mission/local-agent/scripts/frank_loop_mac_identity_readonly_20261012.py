#!/usr/bin/env python3
"""Frank Mac read-only identity + old/new decision-code delta receipt.

No Loop/LaunchAgent restarts, network requests, Gmail, SQLite connections,
policy repairs, RPC reads, file copies, or production changes. Only emits
non-secret aggregate JSON in Downloads. Do not interpret checkout SHA as
proof of process in-memory code identity.
"""
from __future__ import annotations

from datetime import datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

PIN = "6a5b7e8a533f99c871e31f9674329fcb4f929cc2"
SUPPORT = Path.home() / "Library/Application Support/FrankMeme"
LOOP_RUNNER = SUPPORT / "mission-loop.sh"
DASH_RUNNER = SUPPORT / "dashboard.sh"
LABEL_BASE = f"gui/{os.getuid()}/com.{getpass.getuser()}.frank-meme."
ENTRY = "scripts/mission_meme_v1.py"
PACKAGE = "mission_agent"
LEGACY_DELIVERY = "mission_agent/mission_control/delivery.py"
checks = {}
details = {}


def check(key, passed):
    checks[key] = "PASS" if passed else "FAIL"
    print(f"{key}={checks[key]}", flush=True)


def field(text, name):
    found = re.findall(r'^' + re.escape(name) + r'="([^"\n]+)"\s*$',
                       text, re.M)
    if len(found) != 1 or not found[0]:
        return None
    return Path(found[0]).expanduser().resolve()


def execute(command, *, seconds=12):
    return subprocess.run(command, text=True, capture_output=True, timeout=seconds)


def git_head(path):
    try:
        r = execute(["/usr/bin/git", "-C", str(path), "rev-parse", "HEAD"])
        if r.returncode == 0 and re.fullmatch(r"[a-f0-9]{40}", r.stdout.strip()):
            return r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def launch_pid(kind):
    result = execute(["/bin/launchctl", "print", LABEL_BASE + kind])
    if result.returncode:
        return None
    found = re.search(r"^\s*pid = ([0-9]+)\s*$", result.stdout, re.M)
    return int(found.group(1)) if found else None


def source_digests(root):
    """Every mission_agent Python module plus actual executable entrypoint."""
    found = {}
    package = root / PACKAGE
    if package.is_dir():
        for file in package.rglob("*.py"):
            if file.is_file():
                relative = file.relative_to(root).as_posix()
                found[relative] = hashlib.sha256(file.read_bytes()).hexdigest()
    entry = root / ENTRY
    if entry.is_file():
        found[ENTRY] = hashlib.sha256(entry.read_bytes()).hexdigest()
    return found


def changed_modules(old, new):
    return sorted(k for k in set(old) | set(new) if old.get(k) != new.get(k))


def process_identity(pid, old_agent):
    """Never echo raw process args/cwd; no claim of full in-memory provenance."""
    if not pid:
        return {"process_args_match_loop": False, "process_cwd_matches_runner": False,
                "cwd_checked": False}
    args_match = False
    cwd_match = False
    cwd_checked = False
    try:
        ps = execute(["/bin/ps", "-p", str(pid), "-o", "command="])
        args_match = (ps.returncode == 0 and
                      "mission_meme_v1.py loop" in ps.stdout and
                      "--live-delivery" in ps.stdout)
    except (OSError, subprocess.TimeoutExpired):
        pass
    try:
        proc = execute(["/usr/sbin/lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"])
        names = [line[1:] for line in proc.stdout.splitlines()
                 if line.startswith("n") and len(line) > 1]
        if proc.returncode == 0 and len(names) == 1:
            cwd_checked = True
            cwd_match = Path(names[0]).resolve() == old_agent.resolve()
    except (OSError, subprocess.TimeoutExpired, ValueError):
        pass
    return {"process_args_match_loop": args_match,
            "process_cwd_matches_runner": cwd_match,
            "cwd_checked": cwd_checked}


def metadata_of_runtime(loop_raw, dash_raw):
    old_agent, release = field(loop_raw, "LOCAL_AGENT"), field(dash_raw, "LOCAL_AGENT")
    check("RUNNER_AGENT_FIELDS_PRESENT", old_agent is not None and release is not None)
    if old_agent is None or release is None:
        return
    check("CURRENT_LOOP_SOURCE_EXISTS", (old_agent / ENTRY).is_file())
    check("REVIEWED_DASHBOARD_RELEASE_EXISTS", (release / ENTRY).is_file())
    old_sha, new_sha = git_head(old_agent), git_head(release)
    details["old_loop_checkout_sha"] = old_sha or "UNKNOWN"
    details["dashboard_checkout_sha"] = new_sha or "UNKNOWN"
    check("OLD_LOOP_CHECKOUT_SHA_IDENTIFIED", old_sha is not None)
    check("RELEASE_PINNED_PR34", new_sha == PIN)
    old_files, new_files = source_digests(old_agent), source_digests(release)
    all_delta = changed_modules(old_files, new_files)
    details["old_python_file_count"] = len(old_files)
    details["new_python_file_count"] = len(new_files)
    details["changed_code_files"] = all_delta
    details["changed_code_file_count"] = len(all_delta)
    details["legacy_delivery_identical"] = (
        LEGACY_DELIVERY in old_files and LEGACY_DELIVERY in new_files
        and old_files[LEGACY_DELIVERY] == new_files[LEGACY_DELIVERY]
    )
    check("COMPLETE_MODULE_LIST_PRESENT",
          bool(old_files) and bool(new_files) and
          ENTRY in old_files and ENTRY in new_files)
    details["signal_code_change_requires_explicit_approval"] = bool(all_delta)
    details["automatic_old_loop_rollback_eligible_by_code"] = (
        details["legacy_delivery_identical"])
    details["automatic_rollback_still_requires_fresh_delivery_state_check"] = True

    for filename in all_delta:
        print("DECISION_MODULE_CHANGED=" + filename, flush=True)
    print("DECISION_MODULE_CHANGED_COUNT=" + str(len(all_delta)), flush=True)
    print("OLD_LOOP_CHECKOUT_SHA=" + details["old_loop_checkout_sha"], flush=True)
    print("LEGACY_DELIVERY_IDENTICAL=" +
          str(details["legacy_delivery_identical"]).upper(), flush=True)


def main():
    check("RUNNERS_PRESENT", LOOP_RUNNER.is_file() and DASH_RUNNER.is_file()
          and not LOOP_RUNNER.is_symlink() and not DASH_RUNNER.is_symlink())
    if checks["RUNNERS_PRESENT"] != "PASS":
        return
    loop_raw = LOOP_RUNNER.read_text(encoding="utf-8")
    dash_raw = DASH_RUNNER.read_text(encoding="utf-8")
    loop_hash = hashlib.sha256(loop_raw.encode("utf-8")).hexdigest()
    dash_hash = hashlib.sha256(dash_raw.encode("utf-8")).hexdigest()
    old_agent = field(loop_raw, "LOCAL_AGENT")
    loop_start = launch_pid("loop")
    dash_start = launch_pid("dashboard")
    check("BOTH_LAUNCH_AGENTS_RUNNING", loop_start is not None and dash_start is not None)
    check("LOOP_RUNNER_HAS_LIVE_DELIVERY", "--live-delivery" in loop_raw
          and "--approved-policy-sha256" in loop_raw
          and "mission_meme_v1.py loop" in loop_raw)
    metadata_of_runtime(loop_raw, dash_raw)
    ident = process_identity(loop_start, old_agent) if old_agent else {}
    details["process_identity"] = ident
    check("LOOP_PROCESS_ARGUMENTS_MATCH", ident.get("process_args_match_loop") is True)
    check("LOOP_CWD_RESOLVED", ident.get("cwd_checked") is True)
    check("LOOP_CWD_MATCHES_RUNNER", ident.get("process_cwd_matches_runner") is True)
    details["running_python_code_bytes_proven"] = False
    details["code_provenance_limit"] = (
        "Runner checkout SHA, process args and cwd do not attest to imported "
        "Python module bytes loaded at process start.")
    check("LOOP_PID_UNCHANGED", loop_start is not None and loop_start == launch_pid("loop"))
    check("DASHBOARD_PID_UNCHANGED", dash_start is not None and dash_start == launch_pid("dashboard"))
    check("LOOP_RUNNER_UNCHANGED",
          hashlib.sha256(LOOP_RUNNER.read_bytes()).hexdigest() == loop_hash)
    check("DASHBOARD_RUNNER_UNCHANGED",
          hashlib.sha256(DASH_RUNNER.read_bytes()).hexdigest() == dash_hash)
    print("AUDIT_ONLY=YES LOOP_RESTART=NO GMAIL_SEND=NO DATABASE_WRITE=NO", flush=True)


if __name__ == "__main__":
    error = None
    try:
        main()
    except Exception as exc:
        error = type(exc).__name__
        print("READONLY_AUDIT_ERROR_TYPE=" + error, flush=True)
    finally:
        payload = {"schema": 1,
                   "checked_at_utc": datetime.now(timezone.utc).isoformat(),
                   "release_pin": PIN, "checks": checks, "details": details,
                   "error_type": error,
                   "production_loop_restart_attempted": False,
                   "dashboard_restart_attempted": False,
                   "gmail_send_attempted": False,
                   "production_database_modified": False,
                   "rpc_secret_contents_read": False}
        output_dir = Path.home() / "Downloads"
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = output_dir / (
            "frank-loop-identity-readonly-" +
            datetime.now().strftime("%Y%m%d-%H%M%S") + ".zip")
        with zipfile.ZipFile(destination, "x", zipfile.ZIP_DEFLATED) as z:
            z.writestr("identity.json", json.dumps(
                payload, ensure_ascii=False, indent=2) + "\n")
        print("RESULT_ARCHIVE=" + str(destination), flush=True)
        if Path("/usr/bin/open").exists():
            subprocess.run(["/usr/bin/open", "-R", str(destination)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           check=False)
        sys.exit(0 if error is None and all(
            status == "PASS" for status in checks.values()) else 3)
