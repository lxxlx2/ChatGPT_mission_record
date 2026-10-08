#!/usr/bin/env python3
"""Transactional-ish Mac Mission Meme PR deployment.

Switches ONLY the installed Mission Loop and Dashboard runner's LOCAL_AGENT
to this immutable detached Git worktree. Does not install/merge Git branches,
edit Frank writer service, mutate frozen policy/RPC secrets, or send mail itself.
The existing live Mission Loop MAY send mail as it normally runs after restart.
On failed startup, runner scripts are restored and both jobs restarted.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASELINE_SHA = "49d5d3b7122efa41dd74ba6ede0c5d225309988c"
CONFIRM = "YES_RESTART_LOOP_DASHBOARD"
TIMEOUT_SECONDS = 90


def abort(code):
    raise RuntimeError(code)


def run(cmd, *, cwd=None, env=None, timeout=20):
    result = subprocess.run(
        cmd, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout
    )
    if result.returncode:
        abort("COMMAND_FAILED:" + str(cmd[0]) + ":" + str(result.returncode))
    return result.stdout


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe_read(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        abort("EXPECTED_REGULAR_FILE_MISSING:" + path.name)
    return path.read_text(encoding="utf-8")


def read_runner_value(script, key):
    hits = re.findall(r"^" + re.escape(key) + r'="([^"\n]+)"$', script, re.M)
    if len(hits) != 1:
        abort("RUNNER_ANCHOR_UNSUPPORTED:" + key)
    return hits[0]


def atomic_text(path, value, mode=0o700):
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix=".frank-deploy-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def sqlite_snapshot(source, output):
    source = Path(source)
    if not source.is_file():
        return False
    reader = sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True, timeout=10)
    reader.execute("PRAGMA query_only=ON")
    writer = sqlite3.connect(output)
    try:
        reader.backup(writer, pages=200, sleep=0.05)
        status = writer.execute("PRAGMA quick_check").fetchone()[0]
        if status != "ok":
            abort("SQLITE_BACKUP_INTEGRITY_FAILED:" + source.name)
    finally:
        writer.close()
        reader.close()
    os.chmod(output, 0o600)
    return True


def loaded_job(label):
    output = run(["launchctl", "print", f"gui/{os.getuid()}/{label}"])
    if not re.search(r"^\s*state = running\s*$", output, re.M):
        abort("SERVICE_NOT_RUNNING:" + label)
    match = re.search(r"^\s*pid = (\d+)\s*$", output, re.M)
    if not match:
        abort("SERVICE_PID_MISSING:" + label)
    return int(match.group(1))


def restart(label):
    run(["launchctl", "kickstart", "-k", f"gui/{os.getuid()}/{label}"])


def http_json(port, path):
    url = f"http://127.0.0.1:{port}" + path
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with opener.open(request, timeout=4) as response:
        if response.status != 200:
            abort("DASHBOARD_HTTP_NOT_200:" + path)
        return json.load(response)


def cwd_for_pid(pid):
    output = run(["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"])
    hits = [line[1:] for line in output.splitlines() if line.startswith("n/")]
    return Path(hits[-1]).resolve() if hits else None


def integration_health(port, loop_label, dash_label, agent, previous_updated=None):
    last_error = "UNAVAILABLE"
    until = time.monotonic() + TIMEOUT_SECONDS
    while time.monotonic() < until:
        try:
            loop_pid = loaded_job(loop_label)
            dash_pid = loaded_job(dash_label)
            if cwd_for_pid(loop_pid) != agent or cwd_for_pid(dash_pid) != agent:
                abort("PROCESS_RUNNING_FROM_WRONG_SOURCE")
            paths = (
                "/api/runtime", "/api/control-health", "/api/candidates",
                "/api/trades", "/api/review-activity", "/api/decisions", "/api/coverage",
            )
            results = {p: http_json(port, p) for p in paths}
            control = results["/api/control-health"]
            runtime = results["/api/runtime"]
            if runtime.get("status") != "LIVE" or control.get("status") != "OK":
                abort("HEALTH_NOT_OK")
            if control.get("delivery_allowed") is not True:
                abort("LIVE_DELIVERY_UNEXPECTEDLY_DISABLED")
            if previous_updated and control.get("updated_at") == previous_updated:
                abort("OLD_CONTROL_HEALTH_STILL_VISIBLE")
            for path in ("/api/candidates", "/api/trades", "/api/review-activity", "/api/decisions"):
                if not isinstance(results[path], list):
                    abort("DASHBOARD_JSON_INVALID:" + path)
            coverage = results["/api/coverage"]
            if not isinstance(coverage, dict) or coverage.get("scope") != "LOCAL_INDEX_ONLY" or coverage.get("status") != "OK":
                abort("FRANK_COVERAGE_API_UNAVAILABLE")
            return {"dashboard_port":port, "loop_pid":loop_pid, "dashboard_pid":dash_pid,
                    "dashboard_routes":len(paths), "delivery_allowed":True,
                    "control_status":control["status"], "runtime_status":runtime["status"]}
        except (RuntimeError, subprocess.TimeoutExpired, OSError, ValueError, KeyError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = type(exc).__name__ + ":" + str(exc)[:150]
            time.sleep(2)
    abort("INTEGRATION_CHECK_TIMEOUT:" + last_error)


def ensure_git_release(agent, expected_head):
    root = Path(run(["git", "-C", str(agent), "rev-parse", "--show-toplevel"]).strip()).resolve()
    head = run(["git", "-C", str(root), "rev-parse", "HEAD"]).strip()
    if head != expected_head:
        abort("GIT_HEAD_NOT_PINNED")
    if run(["git", "-C", str(root), "status", "--porcelain"]).strip():
        abort("RELEASE_WORKTREE_NOT_CLEAN")
    if run(["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"]).strip() != "HEAD":
        abort("RELEASE_NOT_DETACHED")
    run(["git", "-C", str(root), "merge-base", "--is-ancestor", BASELINE_SHA, head])
    return root


def verify_policy(app):
    path = app / "follow_policy_v1.approved.json"
    pin = app / "approved_policy_sha256"
    policy = json.loads(safe_read(path))
    value = safe_read(pin).strip()
    if value != digest(path):
        abort("POLICY_PIN_MISMATCH")
    if (policy.get("status") != "FROZEN_APPROVED"
        or policy.get("live_delivery_approved") is not True
        or (policy.get("decision") or {}).get("observation_retention_seconds") != 5184000):
        abort("POLICY_LIVE_DELIVERY_GATE_MISMATCH")
    return value


def restore(backup, app, loop_label, dash_label):
    for name in ("dashboard.sh", "mission-loop.sh"):
        old = safe_read(backup / name)
        atomic_text(app / name, old)
    # Do not restore SQLite: newer delivery receipts could exist. Never risk duplicates.
    restart(dash_label)
    restart(loop_label)
    print("RUNNERS_RESTORED=YES")
    print("CONTROL_SQLITE_RESTORED=NO_SAFE_APPEND_ONLY")
    print("BACKUP_DIR=" + str(backup))


def preflight_import(agent, venv):
    py = venv / "bin/python"
    if not py.is_file():
        abort("INSTALLED_VENV_PYTHON_NOT_FOUND")
    env = dict(os.environ)
    env["PYTHONPATH"] = str(agent)
    run([str(py), "-B", "-c",
         "from mission_agent.mission_control.server import Handler; "
         "from mission_agent.mission_control.delivery import render; "
         "assert b'/api/review-activity' in "
         "open('mission_agent/mission_control/server.py','rb').read(); "
         "assert callable(render)"],
        cwd=agent, env=env, timeout=20)


def check_frank_stable(agent, prod, app, plist_dir):
    script = agent / "scripts/meme_acceptance_integrity.py"
    spec = importlib.util.spec_from_file_location("frank_deploy_integrity", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    user = os.environ["USER"]
    return module, module.capture(
        prod, plist_dir / f"com.{user}.frank-meme.loop.plist",
        plist_dir / f"com.{user}.frank-meme.dashboard.plist"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--expected-head")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args()
    if args.apply == args.rollback or args.confirm != CONFIRM:
        abort("USAGE_REQUIRES_EXPLICIT_APPLY_OR_ROLLBACK_CONFIRMATION")
    home = Path.home()
    app = home / "Library/Application Support/FrankMeme"
    plist_dir = home / "Library/LaunchAgents"
    control_pointer = home / ".frank_meme_control_root"
    prod = home / "Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/live-v1"
    user = os.environ.get("USER") or run(["id", "-un"]).strip()
    os.environ["USER"] = user
    loop_label = f"com.{user}.frank-meme.loop"
    dash_label = f"com.{user}.frank-meme.dashboard"
    if not app.is_dir() or not plist_dir.is_dir():
        abort("FRANK_INSTALLATION_MISSING")

    lock_path = app / ".pr29-deploy.lock"
    with open(lock_path, "a+") as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.rollback:
            if not args.backup:
                abort("ROLLBACK_BACKUP_REQUIRED")
            backup = args.backup.resolve(strict=True)
            parent = (app / "deploy-backups").resolve(strict=True)
            if backup.parent != parent:
                abort("ROLLBACK_BACKUP_OUTSIDE_APPROVED_LOCATION")
            restore(backup, app, loop_label, dash_label)
            return
        if not args.expected_head or not re.fullmatch(r"[0-9a-f]{40}", args.expected_head):
            abort("EXPECTED_HEAD_REQUIRED")

        agent = Path(__file__).resolve().parent.parent
        ensure_git_release(agent, args.expected_head)
        if not (prod / "forward.sqlite").is_file() or not (prod / "health.json").is_file():
            abort("FRANK_LEDGER_MISSING")
        control = Path(safe_read(control_pointer).strip()).resolve(strict=True)
        if not (control / "mission-control.sqlite").is_file():
            abort("EXISTING_CONTROL_DB_MISSING")

        runner_names = ("mission-loop.sh", "dashboard.sh")
        original = {name:safe_read(app / name) for name in runner_names}
        previous_agents = {read_runner_value(original[name], "LOCAL_AGENT") for name in runner_names}
        if len(previous_agents) != 1:
            abort("RUNNER_SOURCE_MISMATCH")
        old_agent = Path(next(iter(previous_agents))).resolve(strict=True)
        safe_install_root = home / "Documents/ChatGPT"
        try:
            relative_old = old_agent.relative_to(safe_install_root)
        except ValueError:
            abort("UNEXPECTED_INSTALLED_SOURCE")
        allowed_old_repo = relative_old.parts and (
            relative_old.parts[0] == "frank-meme-main"
            or relative_old.parts[0].startswith("frank-meme-pr29-")
        )
        if (old_agent == agent or not allowed_old_repo or
                tuple(relative_old.parts[-2:]) != ("crypto-300-profit-mission","local-agent")):
            abort("UNEXPECTED_INSTALLED_SOURCE")
        venv_values = {read_runner_value(original[name], "VENV") for name in runner_names}
        if len(venv_values) != 1:
            abort("RUNNER_VENV_MISMATCH")
        venv = Path(next(iter(venv_values))).expanduser().resolve(strict=True)
        expected_pointer = read_runner_value(original["mission-loop.sh"], "CONTROL_POINTER")
        if Path(expected_pointer) != control_pointer:
            abort("CONTROL_POINTER_RUNNER_MISMATCH")
        if "--live-delivery" not in original["mission-loop.sh"]:
            abort("EXISTING_DELIVERY_MODE_NOT_LIVE")
        port = int(safe_read(app / "dashboard_port").strip())
        if not 1 <= port <= 65535:
            abort("PORT_INVALID")
        for name in runner_names:
            value = original[name]
            if value.count('LOCAL_AGENT="' + str(old_agent) + '"') != 1:
                abort("RUNNER_OLD_AGENT_ANCHOR_INVALID:" + name)
        verify_policy(app)
        preflight_import(agent, venv)
        old_loop_pid = loaded_job(loop_label)
        old_dash_pid = loaded_job(dash_label)
        if cwd_for_pid(old_loop_pid) != old_agent or cwd_for_pid(old_dash_pid) != old_agent:
            abort("INSTALLED_PROCESS_CWD_UNEXPECTED")
        old_health = http_json(port, "/api/control-health")
        if old_health.get("delivery_allowed") is not True:
            abort("EXISTING_LIVE_DELIVERY_NOT_AUTHORIZED")
        module, stable = check_frank_stable(agent, prod, app, plist_dir)
        old_writer_plist = plist_dir / f"com.{user}.crypto-monitor-frank-local.plist"
        writer_plist_sha = digest(old_writer_plist) if old_writer_plist.is_file() else None

        backups = app / "deploy-backups"
        backups.mkdir(mode=0o700, exist_ok=True)
        backup = Path(tempfile.mkdtemp(prefix="pr29-", dir=backups))
        os.chmod(backup, 0o700)
        for name in runner_names:
            shutil.copy2(app / name, backup / name)
            os.chmod(backup / name, 0o600)
        sqlite_snapshot(control / "mission-control.sqlite", backup / "mission-control.sqlite")
        sqlite_snapshot(control / "sol-normalized-v1.sqlite", backup / "sol-normalized-v1.sqlite")
        (backup / "manifest.json").write_text(json.dumps(
            {"new_head":args.expected_head, "old_agent":str(old_agent), "new_agent":str(agent),
             "control_root":str(control), "port":port,
             "created_at":datetime.now(timezone.utc).isoformat(),
             "mail_delivery_previous_status":old_health.get("delivery_allowed")},
            ensure_ascii=False, indent=2
        ) + "\n")
        os.chmod(backup / "manifest.json", 0o600)
        print("BACKUP_COMPLETE=" + str(backup), flush=True)
        print("LIVE_GMAIL_DELIVERY_ALREADY_AUTHORIZED=YES", flush=True)

        changed = False
        try:
            for name in runner_names:
                prior = original[name]
                updated = prior.replace('LOCAL_AGENT="' + str(old_agent) + '"',
                                        'LOCAL_AGENT="' + str(agent) + '"', 1)
                if prior == updated:
                    abort("RUNNER_NOT_CHANGED:" + name)
                atomic_text(app / name, updated)
                changed = True
            restart(dash_label)
            restart(loop_label)
            report = integration_health(
                port, loop_label, dash_label, agent,
                previous_updated=old_health.get("updated_at")
            )
            module.verify(
                stable, prod, plist_dir / f"com.{user}.frank-meme.loop.plist",
                plist_dir / f"com.{user}.frank-meme.dashboard.plist"
            )
            if writer_plist_sha and digest(old_writer_plist) != writer_plist_sha:
                abort("FRANK_WRITER_PLIST_CHANGED")
            if digest(app / "follow_policy_v1.approved.json") != safe_read(
                app / "approved_policy_sha256"
            ).strip():
                abort("POLICY_CHANGED_DURING_DEPLOY")
        except Exception:
            if changed:
                print("DEPLOY_FAILED_AUTO_ROLLBACK_START", flush=True)
                restore(backup, app, loop_label, dash_label)
            raise

        print("===== RELEASE DEPLOY FINAL =====")
        print("DEPLOY_PASS=YES")
        print("NEW_HEAD=" + args.expected_head)
        print("BACKUP_DIR=" + str(backup))
        print("DASHBOARD_URL=http://127.0.0.1:" + str(port))
        print("DASHBOARD_ROUTES_PASS=" + str(report["dashboard_routes"]))
        print("LOOP_AND_DASHBOARD_FROM_RELEASE=YES")
        print("LIVE_DELIVERY_ALLOWED=YES")
        print("FRANK_WRITER_PLIST_UNTOUCHED=YES")
        print("PRODUCTION_DB_REPLACED=NO")
        print("PR_MERGED=NO")
        print("PRODUCTION_TRADING=NO_GO")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print("DEPLOY_ERROR=" + type(error).__name__ + ":" + str(error), file=sys.stderr)
        raise SystemExit(1)
