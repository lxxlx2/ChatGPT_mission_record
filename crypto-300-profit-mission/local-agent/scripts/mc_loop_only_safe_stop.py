#!/usr/bin/env python3
"""Explicit, operator-only stop of the MC LOOP (not Dashboard or V1).

Defaults to dry-run. This STOPS MC evaluation entirely, not just its
delivery; Dashboard continues serving previously persisted MC observations.
No old $30 runner is restored or restarted. Never invoke without
separate user approval of this exact production operation.
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import plistlib
import re
import subprocess
import sys
from pathlib import Path


def stop_plan(home: Path, uid: int, user: str) -> dict:
    support = home / "Library" / "Application Support" / "FrankMeme"
    loop_runner = support / "mission-loop.sh"
    agent = home / "Library" / "LaunchAgents" / f"com.{user}.frank-meme.loop.plist"
    label = f"com.{user}.frank-meme.loop"
    if agent.is_symlink() or loop_runner.is_symlink():
        raise ValueError("LOOP_ONLY_TARGET_SYMLINK_REJECTED")
    with agent.open("rb") as fh:
        entry = plistlib.load(fh)
    if (not isinstance(entry, dict) or entry.get("Label") != label
            or entry.get("ProgramArguments") != [str(loop_runner)]
            or not loop_runner.is_file()):
        raise ValueError("LOOP_ONLY_TARGET_MISMATCH")
    return {
        "target_label": f"gui/{uid}/{label}",
        "bootout_domain": f"gui/{uid}",
        "loop_plist": str(agent),
        "dashboard_touched": False,
        "v1_source_touched": False,
        "mc_evaluation_will_stop": True,
        "old_live_policy_not_restarted": True,
    }


def _registered_loop_pid(plan: dict, *, run) -> int:
    """Read-only proof of which launchd-managed loop is about to be stopped."""
    result = run(["launchctl", "print", plan["target_label"]],
                 check=False, capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        raise RuntimeError("MC_LOOP_PRESTOP_LAUNCHCTL_STATE_UNKNOWN")
    # Must capture one concrete managed process, not merely a launchd label.
    match = re.search(r"(?m)^\\s*pid = ([1-9][0-9]*)\\s*$", result.stdout or "")
    if match is None:
        raise RuntimeError("MC_LOOP_PRESTOP_PID_UNKNOWN")
    return int(match.group(1))


def _assert_loop_absent(plan: dict, *, old_pid: int, run, probe_pid) -> None:
    """Never report a stop as successful while launchd or its old PID remains."""
    result = run(["launchctl", "print", plan["target_label"]],
                 check=False, capture_output=True, text=True, timeout=15)
    diagnostic = (result.stderr or "") + (result.stdout or "")
    if result.returncode == 0:
        raise RuntimeError("MC_LOOP_STILL_REGISTERED_AFTER_BOOTOUT")
    if "Could not find service" not in diagnostic:
        raise RuntimeError("MC_LOOP_POSTSTOP_LAUNCHCTL_READBACK_UNKNOWN")
    try:
        probe_pid(old_pid, 0)  # Signal 0 only; never sends a terminating signal.
    except ProcessLookupError:
        return
    except PermissionError as exc:
        raise RuntimeError("MC_LOOP_POSTSTOP_PID_PERMISSION_UNKNOWN") from exc
    raise RuntimeError("MC_LOOP_ORIGINAL_PID_STILL_RUNNING_OR_REUSED")


def stop_loop_only(plan: dict, *, run=subprocess.run, probe_pid=os.kill) -> dict:
    # The sequence disables automatic launch BEFORE stopping the running loop.
    # Never issue bootout/bootstrap/kickstart for the dashboard or V1.
    old_pid = _registered_loop_pid(plan, run=run)
    try:
        run(["launchctl", "disable", plan["target_label"]],
            check=True, capture_output=True, text=True, timeout=15)
        run(["launchctl", "bootout", plan["bootout_domain"], plan["loop_plist"]],
            check=True, capture_output=True, text=True, timeout=15)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        # A successful disable followed by failed bootout may leave a LIVE
        # process. The caller must not treat a partial command sequence as a stop.
        raise RuntimeError("MC_LOOP_STOP_PARTIAL_OR_UNKNOWN_READBACK_REQUIRED") from exc
    _assert_loop_absent(plan, old_pid=old_pid, run=run, probe_pid=probe_pid)
    return {"status": "MC_LOOP_STOP_VERIFIED",
            "old_pid": old_pid, "dashboard_touched": False,
            "v1_source_touched": False}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true",
                        help="Requires separate explicit user deployment authorization")
    opts = parser.parse_args()
    if sys.platform != "darwin":
        raise SystemExit("MACOS_REQUIRED")
    plan = stop_plan(Path.home(), os.getuid(), getpass.getuser())
    print(json.dumps({"mode": "PREVIEW", **plan}, sort_keys=True))
    if not opts.apply:
        return
    if os.environ.get("CONFIRM_MC_LOOP_ONLY_STOP") != "1":
        raise SystemExit("LOOP_ONLY_STOP_NOT_AUTHORIZED")
    proof = stop_loop_only(plan)
    print(json.dumps(proof, sort_keys=True))
    print("MC_LOOP_DISABLED_DASHBOARD_UNTOUCHED")
    print("NO_AUTOMATIC_ROLLBACK_TO_OLD_LIVE_POLICY")


if __name__ == "__main__":
    main()
