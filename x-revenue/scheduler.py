#!/usr/bin/env python3
"""Production 15-minute scheduler runner for x-revenue workflow."""

from __future__ import annotations

import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
RUNTIME_DIR = ROOT / "runtime"
LOG_FILE = RUNTIME_DIR / "scheduler.log"
LOCK_FILE = ROOT / "state" / "scheduler.lock"
MAX_LOG_BYTES = 64 * 1024


def append_bounded_log(entry: str) -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    old = b""
    if LOG_FILE.exists():
        try:
            old = LOG_FILE.read_bytes()[-MAX_LOG_BYTES:]
        except Exception:
            old = b""
    new_bytes = entry.encode("utf-8", errors="replace")
    combined = (old + new_bytes)[-MAX_LOG_BYTES:]
    tmp = LOG_FILE.with_suffix(f".tmp.{os.getpid()}")
    try:
        tmp.write_bytes(combined)
        os.chmod(tmp, 0o600)
        tmp.replace(LOG_FILE)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def run_cycle() -> int:
    os.chdir(REPO_ROOT)
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()

    # 1. Single-instance process lock
    with LOCK_FILE.open("a+") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            append_bounded_log(f"[{now_iso}] SKIPPED: previous scheduler run still active\n")
            return 0

        # 2. Execute pipeline run with 300s bound
        pipeline_script = ROOT / "pipeline.py"
        python_bin = sys.executable
        start_t = dt.datetime.now(dt.timezone.utc)
        exit_code = 0
        output_summary = ""

        try:
            r = subprocess.run(
                [python_bin, str(pipeline_script), "run"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(REPO_ROOT),
            )
            exit_code = r.returncode
            raw_stdout = r.stdout.strip()
            if raw_stdout:
                try:
                    data = json.loads(raw_stdout)
                    output_summary = json.dumps({
                        "status": data.get("status"),
                        "reason": data.get("reason"),
                        "artifact": data.get("artifact"),
                        "candidate_sha256": data.get("candidate_sha256"),
                        "telegram_delivery": data.get("telegram_delivery"),
                    })
                except Exception:
                    output_summary = raw_stdout[-500:]
            elif r.stderr:
                # Mask potential secrets from stderr
                clean_err = r.stderr.strip().splitlines()[-1] if r.stderr.strip() else "unknown error"
                output_summary = f"ERROR: exit={exit_code}, detail={clean_err[:200]}"
            else:
                output_summary = f"EXIT: {exit_code}"
        except subprocess.TimeoutExpired:
            exit_code = 124
            output_summary = "TIMEOUT: run exceeded 300s"
        except Exception as exc:
            exit_code = 1
            output_summary = f"EXCEPTION: {type(exc).__name__}"

        duration = (dt.datetime.now(dt.timezone.utc) - start_t).total_seconds()
        log_line = f"[{now_iso}] exit={exit_code} duration={duration:.2f}s result={output_summary}\n"
        append_bounded_log(log_line)

        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        return exit_code


if __name__ == "__main__":
    sys.exit(run_cycle())
