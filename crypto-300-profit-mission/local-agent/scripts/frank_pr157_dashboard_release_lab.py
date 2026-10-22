"""Frank PR157 release lab. AUDIT reads Mac state; SIMULATE writes temp only.
NEVER changes production, launchd, DB, policy, outbox, mail or trades.
Offline pointer-swap is not proof of real running-service rollback.
"""
import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler

APPROVED = "31dd598df248ca15f731913a5cbf82e88b981874"
ROOT = Path(__file__).resolve().parents[3]
AGENT = "crypto-300-profit-mission/local-agent"
FILES = (
    "mission_agent/mission_control/server.py",
    "mission_agent/mission_control/frank_activity_watch.py",
    "mission_agent/mission_control/intelligence.py",
    "mission_agent/mission_control/intelligence_preview.py",
    "mission_agent/mission_control/static/index.html",
    "mission_agent/mission_control/static/app.js",
    "mission_agent/mission_control/static/styles.css",
    "scripts/mission_meme_v1.py",
)


def run(*args):
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=12)
        return p.returncode, p.stdout
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""


def git(*args):
    rc, s = run("git", "-C", str(ROOT), *args)
    if rc:
        raise RuntimeError("GIT_CHECK_UNAVAILABLE")
    return s.strip()


def digest(path):
    if not isinstance(path, Path) or path.is_symlink() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(path):
    if path is None:
        return {"present": False}
    return {"present": path.exists(), "symlink": path.is_symlink(),
            "path_sha256": hashlib.sha256(str(path).encode()).hexdigest()}


def approved_manifest():
    if git("rev-parse", "--verify", APPROVED + "^{commit}") != APPROVED:
        raise RuntimeError("APPROVED_SOURCE_COMMIT_MISSING")
    if git("status", "--porcelain"):
        raise RuntimeError("RELEASE_LAB_WORKTREE_DIRTY")
    out = {}
    for file in FILES:
        path = ROOT / AGENT / file
        repo_file = AGENT + "/" + file
        if digest(path) is None or git("hash-object", str(path)) != git("rev-parse", APPROVED + ":" + repo_file):
            raise RuntimeError("PRODUCT_SOURCE_DIFFERS_FROM_APPROVED_SHA")
        out[file] = digest(path)
    return out


def inspect_agent(which):
    user = getpass.getuser()
    label = f"com.{user}.frank-meme.{which}"
    plist = Path.home() / "Library/LaunchAgents" / (label + ".plist")
    result = {"plist": identity(plist), "plist_sha256": digest(plist)}
    try:
        if plist.is_symlink():
            raise ValueError()
        data = plistlib.loads(plist.read_bytes())
        if data.get("Label") != label or not isinstance(data.get("ProgramArguments"), list):
            raise ValueError()
        args = data["ProgramArguments"]
        runner = Path(args[0]) if len(args) == 1 else None
        result.update({"plist_read": "VALID", "runner": identity(runner),
                       "runner_sha256": digest(runner)})
    except (OSError, ValueError, TypeError, plistlib.InvalidFileException):
        result["plist_read"] = "UNVERIFIED"
    rc, output = run("launchctl", "print", f"gui/{os.getuid()}/{label}")
    pid = re.findall(r"(?m)^\s*pid = ([1-9][0-9]*)\s*$", output) if rc == 0 else []
    result["launchd_state"] = "RUNNING_PID_IDENTIFIED" if len(pid) == 1 else "UNVERIFIED"
    if len(pid) == 1:
        result["pid"] = int(pid[0])
        status, start = run("ps", "-p", pid[0], "-o", "lstart=")
        result["pid_start"] = start.strip() if status == 0 else "UNVERIFIED"
        status, stdout = run("lsof", "-a", "-p", pid[0], "-d", "cwd", "-Fn")
        dirs = [v[1:] for v in stdout.splitlines() if v.startswith("n")]
        cwd = Path(dirs[0]) if status == 0 and len(dirs) == 1 else None
        result["cwd"] = identity(cwd)
        if which == "dashboard" and cwd is not None:
            result["running_source_sha256"] = {
                f: digest(cwd / f) for f in FILES if f.startswith("mission_agent/")
            }
    return result


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def audit():
    source = approved_manifest()
    result = {which: inspect_agent(which) for which in ("dashboard", "loop")}
    active = result["dashboard"].get("running_source_sha256", {})
    result["approved_product_file_matches_at_running_dashboard"] = {
        name: (value == source[name]) if value is not None else "UNVERIFIED"
        for name, value in active.items()
    }
    first = result["dashboard"].get("cwd", {})
    second = result["loop"].get("cwd", {})
    result["shared_code_root"] = (
        first.get("path_sha256") == second.get("path_sha256")
        if first.get("present") and second.get("present") else "UNVERIFIED"
    )
    opener = build_opener(ProxyHandler({}), NoRedirect)
    result["localhost_status"] = {}
    for path in ("/", "/api/runtime", "/api/frank-intelligence", "/api/frank-activity-watch"):
        try:
            with opener.open(Request("http://127.0.0.1:8766" + path, method="GET"), timeout=4) as response:
                response.read(1)
                result["localhost_status"][path] = response.status
        except Exception as error:
            result["localhost_status"][path] = getattr(error, "code", "UNAVAILABLE")
    result.update({"mode": "READ_ONLY_CURRENT_MAC_STATE", "real_service_touched": False,
                   "production_write": False, "email_sent": False})
    return result


def simulate():
    manifest = approved_manifest()
    with tempfile.TemporaryDirectory(prefix="frank-pr157-release-isolated-") as temp:
        root = Path(temp)
        original, candidate = root / "old-synthetic", root / "candidate-reviewed"
        original.mkdir()
        candidate.mkdir()
        (original / "marker").write_text("SYNTHETIC_NOT_PRODUCTION", encoding="utf-8")
        for file, sha in manifest.items():
            dest = candidate / file
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / AGENT / file, dest)
            if digest(dest) != sha:
                raise RuntimeError("STAGED_APPROVED_HASH_MISMATCH")
        active, pending = root / "active", root / "next"
        for target in (original, candidate, original):
            pending.symlink_to(target, target_is_directory=True)
            os.replace(pending, active)
            if active.resolve() != target.resolve():
                raise RuntimeError("TEMPORARY_POINTER_ROLLBACK_FAILED")
        return {"mode": "TEMP_ONLY_ROLL_FORWARD_FAULT_ROLLBACK",
                "source_sha": APPROVED, "staged_approved_files": len(manifest),
                "synthetic_switch_and_revert": "PASS",
                "actual_running_dashboard_restarted": False,
                "real_release_rollback_proven": False,
                "production_write": False, "email_sent": False}


def main():
    parser = argparse.ArgumentParser()
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--audit", action="store_true")
    g.add_argument("--simulate", action="store_true")
    args = parser.parse_args()
    try:
        data = audit() if args.audit else simulate()
    except Exception as error:
        print("FRANK_PR157_RELEASE_LAB_ERROR=" + type(error).__name__, file=sys.stderr)
        return 2
    print("FRANK_PR157_RELEASE_LAB=" + json.dumps(data, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
