"""Frank PR157 Dashboard-only RELEASE PLANNING LAB -- NEVER install/restart.

audit:  macOS READ-ONLY launchd/plist/runner/ps/lsof and localhost GET.
simulate: only an isolated temporary-directory mock pointer swap and rollback,
          plus a hash manifest of approved PR157 tracked source. This is NOT
          a real production recovery proof or production candidate deployment.

Only standard-library imports; no direct production DB, launchctl modifications,
policy approval, signature, notification, RPC, outbox, installer or trade.
"""
from __future__ import annotations

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

PINNED_PRODUCT_SHA = "31dd598df248ca15f731913a5cbf82e88b981874"
PR146_BASE_SHA = "72cf75c61fdb220a01b98df0abe81ebc5d248fd4"
REL_AGENT = "crypto-300-profit-mission/local-agent"
REPO = Path(__file__).resolve().parents[3]
MUST_MATCH_PRODUCT = (
    "mission_agent/mission_control/server.py",
    "mission_agent/mission_control/frank_activity_watch.py",
    "mission_agent/mission_control/intelligence.py",
    "mission_agent/mission_control/intelligence_preview.py",
    "mission_agent/mission_control/static/index.html",
    "mission_agent/mission_control/static/app.js",
    "mission_agent/mission_control/static/styles.css",
    "scripts/mission_meme_v1.py",
)


def shell(argv: list[str], *, limit: int = 32768) -> tuple[int, str]:
    try:
        result = subprocess.run(argv, check=False, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                timeout=12)
    except (OSError, subprocess.TimeoutExpired):
        return 127, ""
    return result.returncode, result.stdout[:limit]


def git(*args: str) -> str:
    rc, result = shell(["git", "-C", str(REPO), *args], limit=1_000_000)
    if rc:
        raise RuntimeError("GIT_SOURCE_CHECK_UNAVAILABLE")
    return result.strip()


def ensure_product_integrity() -> dict:
    if git("rev-parse", "--verify", PINNED_PRODUCT_SHA + "^{commit}") != PINNED_PRODUCT_SHA:
        raise RuntimeError("PINNED_PRODUCT_COMMIT_UNAVAILABLE")
    if git("status", "--porcelain"):
        raise RuntimeError("RELEASE_LAB_WORKTREE_NOT_CLEAN")
    changed = set(filter(None, git("diff", "--name-only", PINNED_PRODUCT_SHA, "HEAD").splitlines()))
    product_prefix = REL_AGENT + "/"
    watched = {product_prefix + name for name in MUST_MATCH_PRODUCT}
    if changed & watched:
        raise RuntimeError("APPROVED_PRODUCT_FILE_MODIFIED_IN_RELEASE_LAB")
    hashes = {}
    for relative in MUST_MATCH_PRODUCT:
        rel = product_prefix + relative
        working = REPO / rel
        if not working.is_file() or working.is_symlink():
            raise RuntimeError("APPROVED_PRODUCT_FILE_UNAVAILABLE")
        blob = working.read_bytes()
        rc, reviewed_blob = shell(["git", "-C", str(REPO), "show",
                                   PINNED_PRODUCT_SHA + ":" + rel],
                                  limit=max(len(blob) + 500, 2_000_000))
        # git show is decoded by the small shell helper; verify using object id
        expected_sha = git("rev-parse", PINNED_PRODUCT_SHA + ":" + rel)
        actual_sha = git("hash-object", "--", str(working))
        if expected_sha != actual_sha:
            raise RuntimeError("PRODUCT_BLOB_DIFFERS_FROM_APPROVED_SHA")
        hashes[relative] = hashlib.sha256(blob).hexdigest()
    return {
        "approved_product_sha": PINNED_PRODUCT_SHA,
        "unchanged_product_files": len(hashes),
        "approved_file_sha256": hashes,
    }


def sha256_regular(path: Path) -> str | None:
    try:
        if path.is_symlink() or not path.is_file():
            return None
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def masked_identity(path: Path | None):
    """Do not print the user's private absolute paths, runners or credentials."""
    if path is None:
        return {"present": False}
    return {
        "present": path.exists(),
        "kind": "symlink" if path.is_symlink()
                else "file" if path.is_file()
                else "directory" if path.is_dir()
                else "missing",
        "identity_sha256": hashlib.sha256(str(path).encode()).hexdigest(),
    }


def read_launch_agent(label: str, filename: Path) -> dict:
    try:
        if filename.is_symlink():
            return {"status": "SYMLINK_REJECTED"}
        data = plistlib.loads(filename.read_bytes())
        args = data.get("ProgramArguments")
        if not isinstance(args, list) or not args or data.get("Label") != label:
            return {"status": "PLIST_TARGET_UNVERIFIED"}
        cmd = Path(args[0])
        return {
            "status": "PLIST_READ_ONLY_VALID",
            "runner_identity": masked_identity(cmd),
            "runner_sha256": sha256_regular(cmd),
            "program_arguments_count": len(args),
            "keep_alive": bool(data.get("KeepAlive")),
            "plist_sha256": sha256_regular(filename),
            "runner_path_internal": cmd,
        }
    except (OSError, ValueError, TypeError, plistlib.InvalidFileException):
        return {"status": "PLIST_READ_ERROR"}


def live_service_identity(label: str) -> dict:
    rc, out = shell(["launchctl", "print", f"gui/{os.getuid()}/{label}"])
    if rc:
        return {"status": "LAUNCHCTL_READ_UNAVAILABLE"}
    matches = re.findall(r"(?m)^\s*pid = ([1-9][0-9]*)\s*$", out)
    if len(matches) != 1:
        return {"status": "PID_UNRESOLVED"}
    pid = int(matches[0])
    rc, process_start = shell(["ps", "-p", str(pid), "-o", "lstart="])
    process_start = process_start.strip() if rc == 0 else None
    rc, cwd = shell(["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"])
    cwd_paths = [x[1:] for x in cwd.splitlines() if x.startswith("n")]
    cwd_path = Path(cwd_paths[0]) if rc == 0 and len(cwd_paths) == 1 else None
    return {
        "status": "RUNNING_PID_READ_ONLY" if process_start else "PID_START_UNVERIFIED",
        "pid": pid,
        "process_start": process_start,
        "process_cwd_identity": masked_identity(cwd_path),
        "cwd_internal": cwd_path,
    }


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def localhost_probe() -> dict:
    opener = build_opener(ProxyHandler({}), NoRedirect)
    results = {}
    for endpoint in ("/", "/api/runtime", "/api/coverage",
                     "/api/frank-intelligence", "/api/frank-activity-watch"):
        try:
            with opener.open(Request("http://127.0.0.1:8766" + endpoint,
                                     method="GET"), timeout=5) as resp:
                data = resp.read(8192)
                results[endpoint] = resp.status
                if endpoint == "/api/runtime":
                    try:
                        results["runtime_status"] = json.loads(data).get("status")
                    except (ValueError, AttributeError):
                        results["runtime_status"] = "UNVERIFIED"
        except Exception as exc:
            results[endpoint] = getattr(exc, "code", "UNAVAILABLE")
    return results


def audit() -> dict:
    approval = ensure_product_integrity()
    user = getpass.getuser()
    agents = Path.home() / "Library/LaunchAgents"
    records = {}
    for name, short in (("dashboard", "dashboard"), ("loop", "loop")):
        label = f"com.{user}.frank-meme.{short}"
        plist = agents / (label + ".plist")
        launch = read_launch_agent(label, plist)
        running = live_service_identity(label)
        runner = launch.pop("runner_path_internal", None)
        cwd = running.pop("cwd_internal", None)
        runner_bytes_sha = sha256_regular(runner) if runner else None
        if cwd is not None:
            candidate_files = {
                x: sha256_regular(cwd / x)
                for x in MUST_MATCH_PRODUCT
                if name == "dashboard" and x.startswith("mission_agent/")
            }
        else:
            candidate_files = {}
        records[name] = {
            **launch, **running,
            "runner_sha256": runner_bytes_sha,
            "installed_product_hash_matches": {
                name: (val == approval["approved_file_sha256"][name])
                if val is not None else None
                for name, val in candidate_files.items()
            },
        }
    dash = records["dashboard"]
    loop = records["loop"]
    return {
        "mode": "READ_ONLY_MAC_LAUNCHD_AND_SNAPSHOT_AUDIT",
        "read_only": True,
        "source_approved_product_sha": PINNED_PRODUCT_SHA,
        "dashboard": dash,
        "loop": loop,
        "dashboard_loop_shared_process_cwd": (
            dash["process_cwd_identity"].get("identity_sha256") ==
            loop["process_cwd_identity"].get("identity_sha256")
            if dash["process_cwd_identity"].get("present")
            and loop["process_cwd_identity"].get("present") else "UNVERIFIED"
        ),
        "http": localhost_probe(),
        "current_production_release_exact_identity_proven": False,
        "launchd_changes": False,
        "production_files_written": False,
        "new_notifications_sent": False,
    }


def simulate() -> dict:
    """Dry-run pointer rollback in temp only. NOT actual Mac service rollback."""
    approved = ensure_product_integrity()
    candidate_source = REPO / REL_AGENT
    with tempfile.TemporaryDirectory(prefix="frank-pr157-dashboard-lab-") as raw:
        root = Path(raw)
        old = root / "archived-dashboard-placeholder"
        candidate = root / "new-dashboard-staged"
        old.mkdir()
        candidate.mkdir()
        (old / "marker").write_text("OLD_SIMULATED_RELEASE", encoding="utf-8")
        count = 0
        for rel, expected in approved["approved_file_sha256"].items():
            source = candidate_source / rel
            target = candidate / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            if sha256_regular(target) != expected:
                raise RuntimeError("STAGED_PRODUCT_HASH_MISMATCH")
            count += 1
        active = root / "active-dashboard"
        pending = root / "pending-dashboard"
        pending.symlink_to(old, target_is_directory=True)
        os.replace(pending, active)
        if active.resolve() != old.resolve():
            raise RuntimeError("BASELINE_SIMULATION_UNAVAILABLE")
        pending.symlink_to(candidate, target_is_directory=True)
        os.replace(pending, active)
        if active.resolve() != candidate.resolve():
            raise RuntimeError("ISOLATED_POINTER_SWITCH_FAILED")
        # Fault injection: reject the new candidate; rollback pointer only.
        pending.symlink_to(old, target_is_directory=True)
        os.replace(pending, active)
        if active.resolve() != old.resolve():
            raise RuntimeError("ISOLATED_ROLLBACK_FAILED")
        return {
            "mode": "ISOLATED_TEMPORARY_FILES_ONLY",
            "approved_product_sha": PINNED_PRODUCT_SHA,
            "staged_product_files_hash_verified": count,
            "synthetic_pointer_switch": "PASS",
            "synthetic_fault_injection_and_pointer_rollback": "PASS",
            "actual_8766_process_change": False,
            "real_dashboard_restart_or_recovery_verified": False,
            "actual_existing_release_backed_up": False,
            "production_files_written": False,
            "real_notification_sent": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--audit", action="store_true",
                       help="Read live Mac process/plists and localhost GET ONLY")
    group.add_argument("--simulate", action="store_true",
                       help="Synthetic swap/rollback under temporary directory only")
    args = parser.parse_args()
    try:
        result = audit() if args.audit else simulate()
        print("FRANK_DASHBOARD_ONLY_RELEASE_LAB=" +
              json.dumps(result, ensure_ascii=False, sort_keys=True), flush=True)
        return 0
    except Exception as error:
        print("FRANK_DASHBOARD_ONLY_RELEASE_LAB_ERROR=" +
              type(error).__name__, file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
