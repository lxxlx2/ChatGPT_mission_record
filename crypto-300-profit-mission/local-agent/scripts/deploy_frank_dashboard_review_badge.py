#!/usr/bin/env python3
"""Safe dashboard-only rollout of the pinned historical-review badge change."""
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
import subprocess
import sys
import tempfile
import time
import urllib.request

COMMIT = "dbd2dae5a657cb421c3cc6b579c07a7e88b1ba91"
ROOT = "crypto-300-profit-mission/local-agent/mission_agent/mission_control"
PATCHES = {
    "server.py": ("b5eb4af5c945cc1b62337d48393fe02243f9505f", "f5e00781ea4af45b4d6b15a09b8cb000f5b744f4"),
    "static/app.js": ("8f0ac1beace94f01894c151576bc276f48f1b4a4", "14985b35b019054d5ff9871e002c32421345ff17"),
    "delivery_review.py": (None, "62f5fa85bf41cd95e4a31a373910f81970368ea6"),
}


def blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def local_dashboard_source():
    runner = Path.home() / "Library/Application Support/FrankMeme/dashboard.sh"
    match = re.search(r'^LOCAL_AGENT="([^"]+)"$', runner.read_text(encoding="utf-8"), re.M)
    if not match:
        raise RuntimeError("DASHBOARD_RUNNER_LOCAL_AGENT_NOT_FOUND")
    path = Path(match.group(1)).expanduser().resolve() / "mission_agent" / "mission_control"
    if not path.is_dir():
        raise RuntimeError("LOCAL_AGENT_SOURCE_MISSING")
    return path


def preflight(root):
    for relative, (original, updated) in PATCHES.items():
        path = root / relative
        if not path.exists() and original is None:
            continue
        if not path.is_file():
            raise RuntimeError("MISSING_LOCAL_FILE_" + relative)
        sha = blob_sha(path.read_bytes())
        if sha != original:
            raise RuntimeError(("ALREADY_UPDATED_" if sha == updated else "LOCAL_SOURCE_DIFFERENT_") + relative)
    new = {}
    for relative, (_, expected) in PATCHES.items():
        url = "https://raw.githubusercontent.com/lxxlx2/ChatGPT_mission_record/" + COMMIT + "/" + ROOT + "/" + relative
        with urllib.request.urlopen(url, timeout=20) as response:
            data = response.read(150000)
        if blob_sha(data) != expected:
            raise RuntimeError("REMOTE_GIT_BLOB_MISMATCH_" + relative)
        if relative.endswith(".py"):
            compile(data.decode("utf-8"), relative, "exec")
        new[relative] = data
    return new


def restart_dashboard():
    label = f"gui/{os.getuid()}/com.{getpass.getuser()}.frank-meme.dashboard"
    subprocess.run(["/bin/launchctl", "kickstart", "-k", label], check=True,
                   capture_output=True, text=True, timeout=20)


def verify_dashboard():
    control = Path((Path.home() / ".frank_meme_control_root").read_text().strip())
    port_file = control / "dashboard.port"
    if not port_file.is_file():
        port_file = Path.home() / "Library/Application Support/FrankMeme/dashboard_port"
    port = int(port_file.read_text().strip())
    if not 1 <= port <= 65535:
        raise RuntimeError("INVALID_DASHBOARD_PORT")
    endpoint = f"http://127.0.0.1:{port}/api/control-health"
    for _ in range(30):
        try:
            with urllib.request.urlopen(endpoint, timeout=1.5) as response:
                body = json.load(response)
            if body.get("manual_review_breakdown_available") is True:
                old = int(body["manual_review_expired_unsent_count"])
                active = int(body["manual_review_actionable_count"])
                total = int(body["manual_review_total_count"])
                if old + active != total:
                    raise RuntimeError("REVIEW_COUNTS_INCONSISTENT")
                print(f"DASHBOARD_REVIEW_BREAKDOWN=PASS history={old} active={active} total={total}")
                return
        except (OSError, ValueError, TimeoutError):
            time.sleep(0.5)
    raise RuntimeError("DASHBOARD_READBACK_FAILED")


def install(root, new):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup = Path.home() / "Library/Application Support/FrankMeme/dashboard-review-backups" / stamp
    backup.mkdir(mode=0o700, parents=True, exist_ok=False)
    saved = {}
    for relative in PATCHES:
        path = root / relative
        backup_path = backup / relative
        backup_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if path.is_file():
            shutil.copy2(path, backup_path)
            saved[relative] = backup_path
        else:
            saved[relative] = None
    print("LOCAL_BACKUP=CREATED")
    try:
        for relative, data in new.items():
            path = root / relative
            fd, tmp = tempfile.mkstemp(prefix=".frank-badge-", dir=path.parent)
            try:
                os.fchmod(fd, 0o644)
                with os.fdopen(fd, "wb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(tmp, path)
            finally:
                if os.path.exists(tmp):
                    os.unlink(tmp)
        restart_dashboard()
        verify_dashboard()
        print("DASHBOARD_UPDATE=SUCCESS")
        print("MISSION_LOOP_RESTART=NO")
        print("DATABASE_WRITE=NO")
        print("EMAIL_SEND=NO")
    except Exception:
        for relative, copy in saved.items():
            path = root / relative
            if copy is None:
                path.unlink(missing_ok=True)
            else:
                shutil.copy2(copy, path)
        try:
            restart_dashboard()
            print("ROLLBACK=DASHBOARD_FILES_RESTORED")
        except Exception as exc:
            print("ROLLBACK_RESTART_FAILED=" + type(exc).__name__)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    source = local_dashboard_source()
    new = preflight(source)
    print("REMOTE_BLOBS=VERIFIED")
    print("LOCAL_BASELINE=VERIFIED")
    if not args.apply:
        print("DRY_RUN=PASS")
        return
    install(source, new)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("DASHBOARD_UPDATE=FAILED " + type(exc).__name__ + " " + str(exc), file=sys.stderr)
        sys.exit(1)
