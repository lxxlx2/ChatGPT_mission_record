#!/usr/bin/env python3
"""Read-only Mac Frank RPC runner configuration diagnosis; never prints RPC values.

Never changes credentials, launchd, runtime files, policy or databases.
Prints only names of boolean checks and publishes a sanitized one-JSON ZIP.
"""
from __future__ import annotations

import datetime as dt
import getpass
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import zipfile

SUPPORT = Path.home() / "Library/Application Support/FrankMeme"
LOOP = SUPPORT / "mission-loop.sh"
DASH = SUPPORT / "dashboard.sh"
POINTER = Path.home() / ".frank_meme_control_root"
RESULT = {}
STATES = {}


def field(raw: str, name: str):
    matches = re.findall(r'^' + re.escape(name) + r'="([^"\n]+)"\s*$', raw, flags=re.M)
    if len(matches) != 1 or not matches[0]:
        return None
    return Path(matches[0]).expanduser()


def inspect(path: Path | None):
    if path is None:
        return {"field_present": False}
    try:
        known = path.exists()
        is_regular = path.is_file()
        symlink = path.is_symlink()
        parent_available = path.parent.is_dir()
        owner_only = bool(is_regular and not (path.stat().st_mode & 0o077))
        owner_is_current_user = bool(is_regular and path.stat().st_uid == os.getuid())
    except OSError:
        return {"field_present": True, "stat_error": True}
    return {
        "field_present": True,
        "exists": known,
        "regular_file": is_regular,
        "symlink": symlink,
        "parent_directory_exists": parent_available,
        "owner_only_permissions": owner_only,
        "owned_by_user": owner_is_current_user,
    }


def launch_pid(kind: str):
    label = f"gui/{os.getuid()}/com.{getpass.getuser()}.frank-meme.{kind}"
    out = subprocess.run(["/bin/launchctl", "print", label],
                         capture_output=True, text=True, timeout=12)
    found = re.search(r"^\s*pid = (\d+)\s*$", out.stdout, re.M)
    return int(found.group(1)) if out.returncode == 0 and found else None


def check(key, ok):
    STATES[key] = "PASS" if ok else "FAIL"
    print(f"{key}={STATES[key]}", flush=True)


def main():
    check("RUNNERS_PRESENT", LOOP.is_file() and DASH.is_file())
    if STATES["RUNNERS_PRESENT"] != "PASS":
        return
    loop = LOOP.read_text(encoding="utf-8")
    dash = DASH.read_text(encoding="utf-8")
    loop_path = field(loop, "RPC_FILE")
    dash_path = field(dash, "RPC_FILE")
    loop_info = inspect(loop_path)
    dash_info = inspect(dash_path)
    RESULT["loop_rpc"] = loop_info
    RESULT["dashboard_rpc"] = dash_info
    check("LOOP_RPC_PATH_CONFIGURED", loop_path is not None)
    check("DASHBOARD_RPC_PATH_CONFIGURED", dash_path is not None)
    check("LOOP_RPC_FILE_EXISTS", loop_info.get("regular_file") is True)
    check("DASHBOARD_RPC_FILE_EXISTS", dash_info.get("regular_file") is True)
    check("LOOP_DASHBOARD_RPC_PATHS_MATCH", bool(
        loop_path and dash_path and loop_path.resolve() == dash_path.resolve()
    ))
    expected = SUPPORT / "solana_rpc_urls"
    RESULT["canonical_support_rpc"] = inspect(expected)
    check("CANONICAL_SUPPORT_RPC_EXISTS", expected.is_file())
    check("LOOP_RPC_PATH_IS_CANONICAL", bool(
        loop_path and loop_path.resolve() == expected.resolve()
    ))
    check("DASHBOARD_RPC_PATH_IS_CANONICAL", bool(
        dash_path and dash_path.resolve() == expected.resolve()
    ))
    user_control = None
    if POINTER.is_file():
        control_string = POINTER.read_text(encoding="utf-8").strip()
        if control_string:
            user_control = Path(control_string).expanduser()
    RESULT["control_candidate_rpc"] = inspect(
        user_control / "solana_rpc_urls" if user_control else None
    )
    prod_path = field(loop, "PROD")
    RESULT["production_candidate_rpc"] = inspect(
        prod_path / "solana_rpc_urls" if prod_path else None
    )
    check("LIVE_MISSION_LOOP_PID_FOUND", launch_pid("loop") is not None)
    check("LIVE_DASHBOARD_PID_FOUND", launch_pid("dashboard") is not None)
    # Do not read file contents or hash the endpoint; permission bits and the
    # existence of a private regular file are the only credential checks.
    RESULTS = {
        "LOOP_PATH_DIFFERS_FROM_DASHBOARD": bool(
            loop_path and dash_path and loop_path.resolve() != dash_path.resolve()
        ),
        "DASHBOARD_HAS_PRIVATE_RPC_CANDIDATE": bool(
            dash_info.get("regular_file") and dash_info.get("owner_only_permissions")
            and dash_info.get("owned_by_user")
        ),
        "CANONICAL_HAS_PRIVATE_RPC_CANDIDATE": bool(
            RESULT["canonical_support_rpc"].get("regular_file")
            and RESULT["canonical_support_rpc"].get("owner_only_permissions")
            and RESULT["canonical_support_rpc"].get("owned_by_user")
        ),
    }
    RESULT["classification"] = RESULTS
    print("LOOP_PATH_DIFFERS_FROM_DASHBOARD=" + str(RESULTS["LOOP_PATH_DIFFERS_FROM_DASHBOARD"]).upper())
    print("DASHBOARD_HAS_PRIVATE_RPC_CANDIDATE=" + str(RESULTS["DASHBOARD_HAS_PRIVATE_RPC_CANDIDATE"]).upper())
    print("CANONICAL_HAS_PRIVATE_RPC_CANDIDATE=" + str(RESULTS["CANONICAL_HAS_PRIVATE_RPC_CANDIDATE"]).upper())
    print("DIAGNOSIS_COMPLETE=YES NO_CREDENTIALS_READ=YES NO_RESTART=YES")


if __name__ == "__main__":
    error_type = None
    try:
        main()
    except Exception as ex:
        error_type = type(ex).__name__
        print("DIAGNOSIS_ERROR_TYPE=" + error_type)
    finally:
        report = {
            "version": 1,
            "recorded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "checks": STATES, "details": RESULT,
            "error_type": error_type,
            "rpc_values_read": False,
            "mail_or_rpc_network_called": False,
            "launchagent_restarted": False,
            "files_or_databases_modified": False,
        }
        downloads = Path.home() / "Downloads"
        if downloads.is_dir():
            stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            output = downloads / f"frank-loop-rpc-diagnosis-{stamp}.zip"
            with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED) as z:
                z.writestr("diagnosis.json",
                    json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
            print("RESULT_ARCHIVE=" + str(output))
            if Path("/usr/bin/open").exists():
                subprocess.run(["/usr/bin/open", "-R", str(output)], check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sys.exit(0 if error_type is None else 2)
