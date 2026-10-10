#!/usr/bin/env python3
"""Safely patch existing FrankMeme launchd runner shells to load local Solana RPC.

Does not touch LaunchAgents, launchctl, the production DB, or any running process.
Run without --apply to print a no-write preflight. --apply creates timestamped
backups and updates only runner shells in Application Support/FrankMeme.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
from datetime import datetime, timezone

RPC_EXPORT = r'''RPC_FILE="$HOME/Library/Application Support/FrankMeme/solana_rpc_urls"
[ -s "$RPC_FILE" ] || { echo "ERROR: AUTHENTICATED_SOLANA_RPC_NOT_CONFIGURED" >&2; exit 1; }
SOLANA_RPC_URLS="$(cat "$RPC_FILE")"
[ -n "$SOLANA_RPC_URLS" ] || { echo "ERROR: AUTHENTICATED_SOLANA_RPC_EMPTY" >&2; exit 1; }
export SOLANA_RPC_URLS
'''


def patch_runner(body: str, command: str) -> tuple[str, bool]:
    """Accept only the known loop/dashboard runner template; never replace logic."""
    launch = f"scripts/mission_meme_v1.py {command}"
    if body.count(launch) != 1:
        raise ValueError(f"RUNNER_COMMAND_MISMATCH:{command}")
    if body.count('cd "$LOCAL_AGENT"') != 1:
        raise ValueError("RUNNER_WORKDIR_ANCHOR_MISMATCH")
    if "export SOLANA_RPC_URLS" in body:
        if 'SOLANA_RPC_URLS="$(cat "$RPC_FILE")"' not in body:
            raise ValueError("UNRECOGNIZED_EXISTING_RPC_EXPORT")
        return body, False
    if 'SOLANA_RPC_URLS=' in body or "RPC_FILE=" in body:
        raise ValueError("PARTIAL_RPC_CONFIG_NEEDS_MANUAL_REVIEW")
    return body.replace('cd "$LOCAL_AGENT"', RPC_EXPORT + 'cd "$LOCAL_AGENT"', 1), True


def shell_syntax_ok(text: str) -> bool:
    proc = subprocess.run(
        ["bash", "-n"],
        input=text,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


def file_is_safe(path: Path) -> bool:
    return path.is_file() and not path.is_symlink() and path.stat().st_nlink == 1


def update_runner(path: Path, content: str, stamp: str) -> Path:
    backup = path.with_name(f"{path.name}.before-rpc-{stamp}")
    if backup.exists():
        raise FileExistsError(f"BACKUP_EXISTS:{backup.name}")
    shutil.copy2(path, backup)
    backup.chmod(0o600)

    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.rpc-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.chmod(temp_name, stat.S_IMODE(path.stat().st_mode))
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
    return backup


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Modify runner scripts only (no services)")
    parser.add_argument(
        "--app-support",
        type=Path,
        default=Path.home() / "Library/Application Support/FrankMeme",
    )
    args = parser.parse_args()

    root = args.app_support
    rpc_file = root / "solana_rpc_urls"
    if not file_is_safe(rpc_file) or rpc_file.stat().st_size == 0:
        raise SystemExit("ERROR: AUTHENTICATED_SOLANA_RPC_NOT_CONFIGURED")
    if stat.S_IMODE(rpc_file.stat().st_mode) != 0o600:
        raise SystemExit("ERROR: RPC_FILE_PERMISSIONS_NOT_0600")

    staged: list[tuple[Path, str, bool]] = []
    for name, cmd in (("dashboard.sh", "serve"), ("mission-loop.sh", "loop")):
        path = root / name
        if not file_is_safe(path):
            raise SystemExit(f"ERROR: RUNNER_NOT_REGULAR_FILE:{name}")
        body = path.read_text(encoding="utf-8")
        try:
            result, changed = patch_runner(body, cmd)
        except ValueError as exc:
            raise SystemExit(f"ERROR: {name}:{exc}") from exc
        if not shell_syntax_ok(result):
            raise SystemExit(f"ERROR: RUNNER_BASH_SYNTAX_INVALID:{name}")
        staged.append((path, result, changed))

    print("PERSISTENT_RPC_FILE: PASS (0600; secret not printed)")
    print("BOTH_RUNNERS_BASH_SYNTAX: PASS")
    for path, _, changed in staged:
        print(f"{path.name}: {'NEEDS_PATCH' if changed else 'ALREADY_CONFIGURED'}")

    if args.apply:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        for path, result, changed in staged:
            if not changed:
                continue
            backup = update_runner(path, result, stamp)
            print(f"{path.name}: PATCHED; backup={backup.name}")
        print("RUNNER_PATCH: PASS")
    else:
        print("DRY_RUN: NO_FILES_MODIFIED")
    print("RUNNING_SERVICES: UNTOUCHED")
    print("LAUNCHAGENTS: UNTOUCHED")
    print("PRODUCTION_DB: UNTOUCHED")
    print("PRODUCTION_TRADING: NO_GO")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
