#!/usr/bin/env python3
"""Explicit local macOS Monster V4 shadow service manager; never touches Frank.

All install/uninstall actions require a direct user's local CLI invocation.
No trading, email sending, ports, credentials, network listeners, or sudo.
"""
import argparse
import hashlib
import json
import os
import plistlib
import shutil
import subprocess
import sys
import time
from pathlib import Path

LABEL = "com.chatgpt.crypto-mission.monster-v4.shadow"
SCRIPT_NAMES = ("monster_v4_shadow.py", "monster_v4_d2.py")
DEFAULT_ROOT = Path.home() / "Library/Application Support/MonsterV4Shadow"
DEFAULT_PLIST = Path.home() / "Library/LaunchAgents" / (LABEL + ".plist")


def source_files():
    scripts = Path(__file__).resolve().parent
    return [scripts / x for x in SCRIPT_NAMES]


def release_id(paths):
    h = hashlib.sha256()
    for p in paths:
        h.update(p.name.encode("utf-8"))
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def service_plist(python_binary, installed_script, database, logs):
    return {"Label": LABEL, "ProgramArguments": [
                str(python_binary), "-B", str(installed_script), "shadow-loop",
                "--db", str(database), "--interval-seconds", "180"],
            "RunAtLoad": True,
            "KeepAlive": True,
            "ThrottleInterval": 60,
            "ProcessType": "Background",
            "WorkingDirectory": str(installed_script.parent),
            "EnvironmentVariables": {"PYTHONUNBUFFERED": "1"},
            "StandardOutPath": str(logs / "shadow.stdout.log"),
            "StandardErrorPath": str(logs / "shadow.stderr.log")}


def run_launchctl(args, check=True):
    return subprocess.run(["launchctl"] + args, text=True,
                          capture_output=True, check=check)


def domain():
    return "gui/" + str(os.getuid())


def inspect(root=DEFAULT_ROOT, plist=DEFAULT_PLIST):
    result = {"module": "Monster V4 shadow", "label": LABEL,
              "frank_untouched": True, "trading_enabled": False,
              "gmail_enabled": False, "plist_exists": plist.is_file(),
              "runtime_exists": root.is_dir(),
              "database_exists": (root / "state/monster.sqlite").is_file(),
              "status": "NOT_INSTALLED"}
    if plist.exists():
        try:
            data = plistlib.loads(plist.read_bytes())
            if data.get("Label") != LABEL:
                result["status"] = "FOREIGN_PLIST_DO_NOT_TOUCH"
                return result
            result["program"] = data.get("ProgramArguments")
        except (ValueError, TypeError):
            result["status"] = "INVALID_PLIST_DO_NOT_TOUCH"
            return result
        try:
            cmd = run_launchctl(["print", domain() + "/" + LABEL], check=False)
            result["launchctl_exit_code"] = cmd.returncode
            result["status"] = "LOADED" if cmd.returncode == 0 else "INSTALLED_NOT_LOADED"
            if cmd.returncode == 0:
                import re
                m = re.search(r"state = ([^\n]+)", cmd.stdout)
                if m:
                    result["launchctl_state"] = m.group(1).strip()
        except OSError as exc:
            result["status"] = "CANNOT_INSPECT_LAUNCHCTL"
            result["error_type"] = type(exc).__name__
    health_file = root / "state/monster.sqlite"
    if health_file.is_file():
        try:
            import sqlite3
            db = sqlite3.connect(f"file:{health_file}?mode=ro", uri=True)
            try:
                result["poll_count"] = db.execute("SELECT COUNT(*) FROM polls").fetchone()[0]
                result["last_poll_observed_ms"] = db.execute(
                    "SELECT MAX(observed_ms) FROM polls").fetchone()[0]
                result["pending_d1"] = db.execute(
                    "SELECT COUNT(*) FROM candidate_queue WHERE status='PENDING'").fetchone()[0]
                result["pending_d2"] = db.execute(
                    "SELECT COUNT(*) FROM d2_reviews WHERE status='PENDING'").fetchone()[0]
            finally:
                db.close()
        except (OSError, sqlite3.DatabaseError) as exc:
            result["db_error_type"] = type(exc).__name__
    return result


def install(root=DEFAULT_ROOT, plist=DEFAULT_PLIST, do_launch=True):
    if sys.platform != "darwin":
        raise RuntimeError("INSTALL_REQUIRES_MACOS")
    if sys.version_info < (3, 9):
        raise RuntimeError("PYTHON_3_9_REQUIRED")
    paths = source_files()
    for p in paths:
        if not p.is_file():
            raise FileNotFoundError(str(p))
    for p in (root, plist):
        if p.is_symlink():
            raise ValueError("SYMLINK_TARGET_REFUSED")
    if plist.exists():
        data = plistlib.loads(plist.read_bytes())
        if data.get("Label") != LABEL:
            raise ValueError("FOREIGN_PLIST_REFUSED")
    existing_plist = plist.read_bytes() if plist.is_file() else None
    root.mkdir(parents=True, exist_ok=True)
    for folder in ("state", "logs", "releases"):
        (root / folder).mkdir(parents=True, exist_ok=True)
    rid = release_id(paths)
    release = root / "releases" / rid
    release.mkdir(exist_ok=True)
    for p in paths:
        destination = release / p.name
        if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() != (
            hashlib.sha256(p.read_bytes()).hexdigest()):
            raise ValueError("RELEASE_FILE_TAMPERED")
        if not destination.exists():
            shutil.copyfile(p, destination)
    planned = service_plist(Path(sys.executable),release/SCRIPT_NAMES[0],
                            root/"state/monster.sqlite",root/"logs")
    data = plistlib.dumps(planned)
    previous = inspect(root,plist)
    if existing_plist == data:
        return {"result":"UNCHANGED", "release":rid,"status":previous}
    plist.parent.mkdir(parents=True, exist_ok=True)
    if do_launch:
        loaded = previous["status"] == "LOADED"
        if loaded:
            run_launchctl(["bootout", domain()+"/"+LABEL])
        try:
            plist.write_bytes(data)
            run_launchctl(["bootstrap",domain(),str(plist)])
        except Exception:
            if existing_plist is None:
                plist.unlink(missing_ok=True)
            else:
                plist.write_bytes(existing_plist)
                if loaded:
                    run_launchctl(["bootstrap",domain(),str(plist)],check=False)
            raise
    else:
        # Tests and explicit local dry-runs never mutate launchd.
        return {"result":"DRY_RUN", "release":rid, "plist":planned}
    return {"result":"INSTALLED", "release":rid,
            "status":inspect(root,plist),
            "state_directory":str(root/"state"),
            "log_directory":str(root/"logs")}


def uninstall(root=DEFAULT_ROOT, plist=DEFAULT_PLIST):
    if sys.platform != "darwin":
        raise RuntimeError("UNINSTALL_REQUIRES_MACOS")
    if not plist.is_file():
        return {"result":"NOT_INSTALLED"}
    data = plistlib.loads(plist.read_bytes())
    if data.get("Label") != LABEL:
        raise ValueError("FOREIGN_PLIST_REFUSED")
    if inspect(root,plist)["status"] == "LOADED":
        run_launchctl(["bootout",domain()+"/"+LABEL])
    plist.unlink()
    return {"result":"REMOVED_SERVICE_ONLY",
            "data_preserved":str(root),
            "frank_untouched":True}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("command",choices=("preflight","install","status","uninstall"))
    a=parser.parse_args()
    if a.command=="preflight":
        result={"platform":sys.platform,"python":sys.version.split()[0],
                "python_path":sys.executable,
                "release":release_id(source_files()),
                "label":LABEL,"frank_untouched":True,
                "ready_for_install":sys.platform=="darwin" and sys.version_info >= (3,9)}
    elif a.command=="install":
        result=install()
    elif a.command=="uninstall":
        result=uninstall()
    else:
        result=inspect()
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str))


if __name__=="__main__":
    main()
