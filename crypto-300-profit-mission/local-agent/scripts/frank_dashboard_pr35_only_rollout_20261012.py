#!/usr/bin/env python3
"""Pinned, transactional DASHBOARD-ONLY Mac rollout of PR35 opportunity-first UI.

Never installs LaunchAgents, replaces mission-loop.sh, changes policy or Gmail config,
restarts the Frank loop, or emits decisions/emails. The existing dashboard service
is restarted only after an independent isolated snapshot read-only acceptance.
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
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.request

PIN = "62697bf98606c19c5709c27006a6a40d9408db97"
PRIOR_DASH_PIN = "6a5b7e8a533f99c871e31f9674329fcb4f929cc2"
REMOTE = "https://github.com/lxxlx2/ChatGPT_mission_record.git"
SUBDIR = "crypto-300-profit-mission/local-agent"
J7 = "J7bhFegCHZAeRzdYDwmbSp1CJ1bDJkutSg26B4SXpump"
BPXX = "BPxxfRCXkUVhig4HS1Lh7kZqV6SPJhzfEk4x6fVBjPCy"
HOME = Path.home()
SUPPORT = HOME / "Library/Application Support/FrankMeme"
DASH_RUNNER = SUPPORT / "dashboard.sh"
LOOP_RUNNER = SUPPORT / "mission-loop.sh"
POINTER = HOME / ".frank_meme_control_root"
UID = os.getuid()
USER = getpass.getuser()
DASH_LABEL = f"gui/{UID}/com.{USER}.frank-meme.dashboard"
LOOP_LABEL = f"gui/{UID}/com.{USER}.frank-meme.loop"
DOWNLOADS = HOME / "Downloads"


def check(label, truth):
    if not truth:
        raise RuntimeError(label + "=BLOCKED")
    print(label + "=PASS", flush=True)


def run(args, *, cwd=None, env=None, timeout=120):
    return subprocess.run(args, cwd=cwd, env=env, timeout=timeout,
                          capture_output=True, text=True, check=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runner_vars(text):
    d = {}
    for k in ("LOCAL_AGENT", "PROD", "VENV", "CONTROL_POINTER"):
        m = re.findall(r"^" + k + r'="([^"\n]+)"\s*$', text, re.M)
        if len(m) != 1:
            raise RuntimeError("RUNNER_MISSING_OR_DUPLICATE_" + k)
        d[k] = Path(m[0]).expanduser().resolve()
    return d


def launch_pid(label):
    result = subprocess.run(["/bin/launchctl", "print", label],
                            capture_output=True, text=True, timeout=10)
    if result.returncode:
        raise RuntimeError("LAUNCH_AGENT_NOT_LOADED:" + label.rsplit(".", 1)[-1])
    m = re.search(r"^\s*pid = (\d+)\s*$", result.stdout, re.M)
    if not m:
        raise RuntimeError("LAUNCH_AGENT_NO_RUNNING_PID:" + label.rsplit(".", 1)[-1])
    return int(m.group(1))


def git_env():
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_ASKPASS"] = "/usr/bin/false"
    return env


def stage_release():
    releases = SUPPORT / "releases"
    releases.mkdir(mode=0o700, parents=True, exist_ok=True)
    release = releases / PIN
    repo = release / "repo"
    if repo.is_dir():
        actual = run(["/usr/bin/git", "-C", str(repo), "rev-parse", "HEAD"]).stdout.strip()
        check("STAGED_SHA", actual == PIN)
        check("STAGED_WORKTREE_CLEAN",
              not run(["/usr/bin/git", "-C", str(repo), "status", "--porcelain"]).stdout.strip())
    else:
        pending = releases / ("." + PIN + "-staging-" + str(os.getpid()))
        pending.mkdir(mode=0o700)
        try:
            run(["/usr/bin/git", "-C", str(pending), "init", "-q"])
            run(["/usr/bin/git", "-C", str(pending), "-c", "credential.helper=",
                 "fetch", "-q", "--depth=1", REMOTE, PIN],
                env=git_env(), timeout=240)
            run(["/usr/bin/git", "-C", str(pending), "checkout", "-q", "--detach", "FETCH_HEAD"])
            head = run(["/usr/bin/git", "-C", str(pending), "rev-parse", "HEAD"]).stdout.strip()
            check("REMOTE_PINNED_SHA", head == PIN)
            release.mkdir(mode=0o700)
            os.replace(pending, repo)
        finally:
            if pending.is_dir():
                shutil.rmtree(pending)
    agent = repo / SUBDIR
    check("RELEASE_AGENT_EXISTS", (agent / "scripts/mission_meme_v1.py").is_file())
    js = agent / "mission_agent/mission_control/static/app.js"
    check("RELEASE_HAS_APPROVED_BADGE", "数据库无发送尝试记录" in js.read_text())
    check("RELEASE_HAS_ATA_WINDOW", "窗口前" in js.read_text())
    html = (agent / "mission_agent/mission_control/static/index.html").read_text(encoding="utf-8")
    check("RELEASE_PR35_LAYOUT_ORDER", layout_order_valid(html))
    check("RELEASE_FOLLOW_OPPORTUNITY_ID", 'id="follow-opportunities"' in html)
    return agent


def layout_order_valid(html):
    """Verify deployed *server* HTML keeps complete DOM IDs in intended order."""
    ids = ("follow-opportunities", "stats", "trades",
           "frank-watch-panel", "decision-history", "coverage-details")
    offsets = [html.find('id="' + ident + '"') for ident in ids]
    return all(position >= 0 for position in offsets) and offsets == sorted(offsets)


def sqlite_backup(source, target):
    with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True, timeout=5) as conn:
        conn.execute("PRAGMA query_only=ON")
        with sqlite3.connect(target) as dest:
            conn.backup(dest)
            check("SQLITE_BACKUP_INTEGRITY",
                  dest.execute("PRAGMA integrity_check").fetchone()[0] == "ok")
    target.chmod(0o600)


def snapshot(vars_, control, path):
    prod = path / "production"
    ctrl = path / "control"
    prod.mkdir(mode=0o700)
    ctrl.mkdir(mode=0o700)
    sqlite_backup(vars_["PROD"] / "forward.sqlite", prod / "forward.sqlite")
    sqlite_backup(control / "mission-control.sqlite", ctrl / "mission-control.sqlite")
    for source, dest in (
        (vars_["PROD"] / "health.json", prod / "health.json"),
        (control / "mission-control-health.json", ctrl / "mission-control-health.json"),
        (control / "frank-inventory-snapshot.json", ctrl / "frank-inventory-snapshot.json"),
    ):
        if source.is_file():
            shutil.copyfile(source, dest)
            dest.chmod(0o600)
    return prod, ctrl


def get(port, endpoint, attempts=1):
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    url = f"http://127.0.0.1:{port}{endpoint}"
    err = None
    for _ in range(attempts):
        try:
            with opener.open(url, timeout=4) as response:
                if response.status != 200:
                    raise RuntimeError("HTTP_STATUS_NOT_200")
                return response.read(4_000_001)
        except (OSError, ValueError, RuntimeError) as ex:
            err = ex
            time.sleep(0.3)
    raise RuntimeError("LOCAL_DASHBOARD_READBACK_UNAVAILABLE") from err


def verify_api(port, *, strict):
    watch = json.loads(get(port, "/api/frank-observed-watchlist", attempts=35))
    check("WATCHLIST_RESPONSE", isinstance(watch, dict) and isinstance(watch.get("rows"), list))
    if strict:
        live_html = get(port, "/", attempts=5).decode("utf-8")
        check("LIVE_PR35_OPPORTUNITY_FIRST", layout_order_valid(live_html))
        check("WINDOW_SCHEMA", watch.get("ata_gap_source_status") == "DATED_ATA_INDEX_SCOPE_V2")
        rows = {x["mint"]: x for x in watch["rows"]}
        for mint, before, inside in ((J7, 0, 2), (BPXX, 63, 3)):
            item = rows.get(mint)
            check("WINDOW_" + ("J7" if mint == J7 else "BPXX"),
                  item is not None and item.get("ata_outside_index_window_signatures") == before
                  and item.get("ata_inside_index_window_signatures") == inside
                  and item.get("pnl_usd") is None)
        source = get(port, "/static/app.js").decode("utf-8")
        check("NEW_UI_BADGE", "数据库无发送尝试记录" in source and "窗口前" in source)
        delivery = json.loads(get(port, "/api/control-health"))
        check("DELIVERY_HEALTH_JSON", isinstance(delivery, dict))
        return {"watchlist_count": len(watch["rows"]),
                "j7": [0, 2], "bpxx": [63, 3]}
    return {"watchlist_count": len(watch["rows"])}


def existing_dashboard_baseline(port: int, expected_pid: int) -> dict:
    """Identify the actual loopback listener before replacement.

    A legacy Dashboard may not yet expose /api/frank-observed-watchlist.
    Missing new-version endpoints are not grounds to interrupt an otherwise
    healthy, identified old UI. Never skip the PID/port binding check.
    """
    executable = shutil.which("lsof")
    check("LSOF_AVAILABLE", executable is not None)
    listener = run([executable, "-nP", f"-iTCP:{port}", "-sTCP:LISTEN", "-Fp"],
                   timeout=12).stdout.splitlines()
    pids = {int(line[1:]) for line in listener
            if re.fullmatch(r"p[0-9]+", line)}
    check("CONFIGURED_PORT_OWNED_BY_DASHBOARD", pids == {expected_pid})
    html = get(port, "/", attempts=3)
    check("EXISTING_DASHBOARD_HTML", b"<html" in html.lower()
          and (b"Frank" in html or b"Meme" in html
               or "研究控制台".encode() in html))
    summary = {"identified_dashboard_pid": expected_pid,
               "identified_port": port,
               "existing_root_html": "VERIFIED"}
    try:
        payload = json.loads(get(port, "/api/frank-observed-watchlist", attempts=1))
        check("EXISTING_WATCHLIST_JSON", isinstance(payload, dict)
              and isinstance(payload.get("rows"), list))
        summary["existing_watchlist_count"] = len(payload["rows"])
        summary["existing_watchlist_api"] = "AVAILABLE"
    except (OSError, ValueError, RuntimeError) as exc:
        # The old application may return 404 or a different JSON schema.
        # Old API presence is not a safety requirement; listener identity is.
        summary["existing_watchlist_api"] = "LEGACY_UNAVAILABLE"
        summary["existing_watchlist_error_type"] = type(exc).__name__
        print("OLD_WATCHLIST_API=LEGACY_UNAVAILABLE (after verified PID and root HTML)")
    return summary


def isolated_accept(agent, python, backup):
    prod = backup / "production"
    ctrl = backup / "control"
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    env = os.environ.copy()
    for name in ("GMAIL_TOKEN", "GH_TOKEN", "GITHUB_TOKEN", "SOLANA_RPC_URL", "SOLANA_RPC_URLS",
                 "ALCHEMY_API_KEY", "JUPITER_API_KEY", "GMAIL_CREDENTIALS"):
        env.pop(name, None)
    env["MISSION_EVIDENCE_EXPORT_ENABLED"] = "0"
    env["PYTHONPATH"] = str(agent)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [str(python), str(agent / "scripts/mission_meme_v1.py"), "serve",
           "--production-root", str(prod), "--control-root", str(ctrl),
           "--host", "127.0.0.1", "--port", str(port)]
    with (backup / "isolated-dashboard.stdout.log").open("wb") as out:
        proc = subprocess.Popen(cmd, cwd=agent, env=env, stdout=out, stderr=subprocess.STDOUT)
        try:
            check("ISOLATED_SERVER_STARTED", proc.poll() is None)
            result = verify_api(port, strict=True)
            check("ISOLATED_SERVER_RUNNING", proc.poll() is None)
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=6)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=6)
        check("ISOLATED_SERVER_STOPPED", proc.poll() is not None)
    return result


def atomic_runner(path, data, mode):
    fd, name = tempfile.mkstemp(prefix=".dashboard-release-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            os.fchmod(f.fileno(), mode)
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def dashboard_restart():
    run(["/bin/launchctl", "kickstart", "-k", DASH_LABEL], timeout=30)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply-dashboard", action="store_true",
                        help="Explicit consent: change only dashboard.sh LOCAL_AGENT and restart dashboard, NOT the live loop.")
    args = parser.parse_args()
    check("CURRENT_MERGE_PIN_CONFIGURED", len(PIN) == 40)
    check("RUNNERS_PRESENT", DASH_RUNNER.is_file() and LOOP_RUNNER.is_file()
          and POINTER.is_file() and not DASH_RUNNER.is_symlink())
    current = DASH_RUNNER.read_text(encoding="utf-8")
    values = runner_vars(current)
    loop_sha_before = sha(LOOP_RUNNER)
    live_loop_pid_before = launch_pid(LOOP_LABEL)
    dash_pid_before = launch_pid(DASH_LABEL)
    control = Path(POINTER.read_text().strip()).expanduser().resolve()
    check("PROD_AND_CONTROL_PRESENT",
          (values["PROD"] / "forward.sqlite").is_file()
          and (control / "mission-control.sqlite").is_file()
          and (values["VENV"] / "bin/python").is_file())
    agent = stage_release()
    backup_root = SUPPORT / "release-backups"
    backup_root.mkdir(mode=0o700, parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + str(os.getpid())
    backup = backup_root / stamp
    backup.mkdir(mode=0o700)
    (backup / "dashboard.sh.before").write_bytes(DASH_RUNNER.read_bytes())
    (backup / "dashboard.sh.before").chmod(0o600)
    check("RUNNER_BACKED_UP", sha(backup / "dashboard.sh.before") == sha(DASH_RUNNER))
    snapshot(values, control, backup)
    check("LOOP_UNCHANGED_BEFORE_SWITCH", sha(LOOP_RUNNER) == loop_sha_before
          and launch_pid(LOOP_LABEL) == live_loop_pid_before)
    result = isolated_accept(agent, values["VENV"] / "bin/python", backup)
    check("PREDEPLOY_LOOP_UNCHANGED", launch_pid(LOOP_LABEL) == live_loop_pid_before
          and sha(LOOP_RUNNER) == loop_sha_before)
    print("ISOLATED_PREFLIGHT=PASS", flush=True)
    print("RELEASE_PIN=" + PIN)
    print("BACKUP_DIRECTORY=" + str(backup))
    if not args.apply_dashboard:
        print("MODE=DRY_RUN_NO_ACTIVE_CHANGES")
        print("DASHBOARD_RESTART=NO MISSION_LOOP_RESTART=NO GMAIL_SEND=NO")
        return
    old_agent = values["LOCAL_AGENT"]
    old_checkout = run(["/usr/bin/git", "-C", str(old_agent), "rev-parse", "HEAD"]).stdout.strip()
    check("CURRENT_DASHBOARD_EXPECTED_PR34", old_checkout in {PRIOR_DASH_PIN, PIN})
    if old_agent == agent:
        print("ALREADY_ACTIVE=YES")
        return
    changed = current.replace('LOCAL_AGENT="' + str(old_agent) + '"',
                              'LOCAL_AGENT="' + str(agent) + '"', 1)
    check("RUNNER_REPLACEMENT_EXACT", changed != current
          and changed.replace('LOCAL_AGENT="' + str(agent) + '"',
                              'LOCAL_AGENT="' + str(old_agent) + '"', 1) == current)
    baseline = None
    port_file = SUPPORT / "dashboard_port"
    check("PRODUCTION_DASHBOARD_PORT_CONFIGURED", port_file.is_file())
    port = int(port_file.read_text().strip())
    check("PRODUCTION_DASHBOARD_PORT_VALID", 1024 <= port <= 65535)
    baseline = existing_dashboard_baseline(port, dash_pid_before)
    mode = DASH_RUNNER.stat().st_mode & 0o777
    switched = False
    try:
        atomic_runner(DASH_RUNNER, changed.encode("utf-8"), mode)
        switched = True
        dashboard_restart()
        active_pid = None
        for _ in range(35):
            try:
                active_pid = launch_pid(DASH_LABEL)
                if active_pid != dash_pid_before:
                    break
            except RuntimeError:
                pass
            time.sleep(0.3)
        check("DASHBOARD_PID_REPLACED", active_pid is not None and active_pid != dash_pid_before)
        live = verify_api(port, strict=True)
        check("DASHBOARD_STILL_LIVE", live["watchlist_count"] > 0)
        check("MISSION_LOOP_PID_UNCHANGED", launch_pid(LOOP_LABEL) == live_loop_pid_before)
        check("MISSION_LOOP_FILE_UNCHANGED", sha(LOOP_RUNNER) == loop_sha_before)
        print("DASHBOARD_PR35_LAYOUT=SUCCESS")
        print("DASHBOARD_RELEASE=SUCCESS")
        print("DASHBOARD_RESTART=YES MISSION_LOOP_RESTART=NO")
        print("NO_GMAIL_SEND_INITIATED=YES LOOP_EXPORT_CONFIGURATION_UNCHANGED=YES")
    except Exception:
        if switched:
            atomic_runner(DASH_RUNNER, current.encode("utf-8"), mode)
            try:
                dashboard_restart()
                print("DASHBOARD_ROLLBACK=RUNNER_RESTORED")
            except Exception:
                print("DASHBOARD_ROLLBACK=MANUAL_ATTENTION_REQUIRED")
        raise
    finally:
        report = {"release": PIN, "backup_dir": str(backup),
                  "dashboard_runner_sha_before": hashlib.sha256(current.encode()).hexdigest(),
                  "loop_runner_sha": loop_sha_before,
                  "snapshot_watchlist": result, "old_watchlist": baseline,
                  "mode": "DASHBOARD_ONLY"}
        (backup / "operation-summary.json").write_text(json.dumps(report, indent=2))
        (backup / "operation-summary.json").chmod(0o600)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("ROLL_OUT=BLOCKED " + type(exc).__name__ + " " + str(exc), file=sys.stderr)
        raise SystemExit(3)
