"""Machine.fun dedicated macOS user LaunchAgent management.

Only manages this module's own Label/plist and private stdout/stderr files.
Never modifies, boots out, reloads, or imports Frank or other services.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import plistlib
import platform
import pwd
import stat
import subprocess
import sys
import tempfile

USER = pwd.getpwuid(os.getuid()).pw_name
LABEL = f"com.{USER}.machine-fun-first-launch"
PLIST = Path.home() / "Library" / "LaunchAgents" / (LABEL + ".plist")
STATE = Path.home() / ".local" / "state" / "machine-fun"
RUNNER = Path(__file__).resolve().parent / "run_machine_fun.sh"
EXPECTED_DIR = RUNNER.parent
DOMAIN = f"gui/{os.getuid()}"
TARGET = f"{DOMAIN}/{LABEL}"


class ServiceFailure(Exception):
    pass


def is_private(path: Path) -> bool:
    return bool(path.exists() and not path.is_symlink() and
                stat.S_IMODE(path.stat().st_mode) & 0o077 == 0)


def prepared_state() -> None:
    if STATE.is_symlink():
        raise ServiceFailure("STATE_SYMLINK_REJECTED")
    STATE.mkdir(parents=True, mode=0o700, exist_ok=True)
    if not is_private(STATE) or not STATE.is_dir():
        raise ServiceFailure("STATE_DIRECTORY_MUST_BE_700")
    for name in ("service.stdout.log", "service.stderr.log"):
        file = STATE / name
        if file.is_symlink():
            raise ServiceFailure("LOG_SYMLINK_REJECTED")
        fd = os.open(file, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600)
        os.close(fd)
        if not is_private(file):
            raise ServiceFailure("LOG_FILE_MUST_BE_600")


def plist_object() -> dict:
    if not RUNNER.is_file() or RUNNER.is_symlink():
        raise ServiceFailure("LAUNCHER_NOT_FOUND")
    if not (EXPECTED_DIR / ".venv" / "bin" / "python").is_file():
        raise ServiceFailure("INDEPENDENT_VENV_NOT_READY")
    return {
        "Label": LABEL,
        "ProgramArguments": ["/bin/bash", str(RUNNER), "run"],
        "WorkingDirectory": str(EXPECTED_DIR),
        "RunAtLoad": True,
        "KeepAlive": {"SuccessfulExit": False},
        "ThrottleInterval": 120,
        "ProcessType": "Background",
        "StandardOutPath": str(STATE / "service.stdout.log"),
        "StandardErrorPath": str(STATE / "service.stderr.log"),
        "Umask": 0o077,
    }


def launchctl(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["/bin/launchctl", *args], capture_output=True,
                          text=True, timeout=20, check=False)


def installation_status() -> int:
    if not PLIST.is_file() or PLIST.is_symlink():
        print("MACHINE_AGENT=NOT_INSTALLED")
        return 1
    try:
        current = plistlib.loads(PLIST.read_bytes())
    except (OSError, ValueError, plistlib.InvalidFileException):
        print("MACHINE_AGENT=PLIST_INVALID")
        return 2
    if current.get("Label") != LABEL or not str(current.get("WorkingDirectory", "")).endswith(
        "/research/projects/machine-fun/detector"
    ):
        print("MACHINE_AGENT=PLIST_IDENTITY_CONFLICT")
        return 2
    status = launchctl("print", TARGET)
    if status.returncode:
        print("MACHINE_AGENT=PLIST_PRESENT_BUT_NOT_LOADED")
        return 1
    print("MACHINE_AGENT=REGISTERED_WITH_LAUNCHD")
    for line in status.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("pid = ") or stripped.startswith("state = ") or stripped.startswith("last exit code = "):
            print(stripped)
    return 0


def install() -> int:
    if platform.system() != "Darwin":
        raise ServiceFailure("MACOS_REQUIRED")
    if PLIST.exists() or PLIST.is_symlink():
        raise ServiceFailure("AGENT_ALREADY_EXISTS_RUN_STATUS_OR_UNINSTALL")
    prepared_state()
    PLIST.parent.mkdir(parents=True, exist_ok=True)
    if PLIST.parent.is_symlink():
        raise ServiceFailure("LAUNCHAGENTS_SYMLINK_REJECTED")
    payload = plistlib.dumps(plist_object(), fmt=plistlib.FMT_XML, sort_keys=True)
    filename: str | None = None
    try:
        fd, filename = tempfile.mkstemp(prefix="." + LABEL + ".", suffix=".plist", dir=PLIST.parent)
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as out:
            out.write(payload)
            out.flush()
            os.fsync(out.fileno())
        os.replace(filename, PLIST)
        filename = None
        load = launchctl("bootstrap", DOMAIN, str(PLIST))
        if load.returncode:
            PLIST.unlink(missing_ok=True)
            raise ServiceFailure("LAUNCHCTL_BOOTSTRAP_FAILED_CHECK_GUI_LOGIN_SESSION")
    finally:
        if filename:
            Path(filename).unlink(missing_ok=True)
    print("MACHINE_AGENT=INSTALLED_AND_STARTED")
    print("MACHINE_AGENT_AUTOSTART=ON_USER_LOGIN")
    print("MACHINE_AGENT_KEEPALIVE=YES")
    print("FRANK=UNTOUCHED")
    print("LOG_DIRECTORY=" + str(STATE))
    return 0


def uninstall() -> int:
    if platform.system() != "Darwin":
        raise ServiceFailure("MACOS_REQUIRED")
    if not PLIST.exists():
        print("MACHINE_AGENT=ALREADY_ABSENT")
        return 0
    if PLIST.is_symlink():
        raise ServiceFailure("PLIST_SYMLINK_REJECTED")
    try:
        current = plistlib.loads(PLIST.read_bytes())
    except (OSError, ValueError, plistlib.InvalidFileException):
        raise ServiceFailure("PLIST_UNREADABLE_MANUAL_REVIEW_REQUIRED")
    if current.get("Label") != LABEL:
        raise ServiceFailure("REFUSE_UNINSTALL_WRONG_SERVICE")
    result = launchctl("bootout", TARGET)
    if result.returncode != 0:
        # Fail closed: if bootout failed but the job still exists, do NOT
        # claim an uninstall or remove the service's only control plist.
        still_loaded = launchctl("print", TARGET)
        if still_loaded.returncode == 0:
            raise ServiceFailure("LAUNCHCTL_BOOTOUT_FAILED_SERVICE_STILL_LOADED")
    PLIST.unlink(missing_ok=True)
    print("MACHINE_AGENT=UNINSTALLED")
    print("LAUNCHCTL_BOOTOUT=" + ("OK" if result.returncode == 0 else "ALREADY_UNLOADED"))
    print("FRANK=UNTOUCHED")
    print("DATABASE_AND_LOGS_PRESERVED=YES")
    return 0


def logs() -> int:
    if not STATE.exists():
        print("MACHINE_LOGS=NOT_CREATED")
        return 0
    for name in ("service.stderr.log", "service.stdout.log"):
        file = STATE / name
        print("LOG=" + name)
        if not file.is_file() or file.is_symlink():
            print("EMPTY")
            continue
        try:
            lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            print("UNREADABLE")
            continue
        for line in lines[-40:]:
            print(line)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Manage only the independent Machine.fun user LaunchAgent")
    parser.add_argument("command", choices=["install", "status", "uninstall", "logs"])
    args = parser.parse_args(argv)
    if args.command == "install":
        return install()
    if args.command == "status":
        return installation_status()
    if args.command == "uninstall":
        return uninstall()
    return logs()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ServiceFailure, OSError, subprocess.TimeoutExpired) as exc:
        description = str(exc) if isinstance(exc, ServiceFailure) else type(exc).__name__
        print("MACHINE_SERVICE_BLOCKED=" + description, file=sys.stderr)
        raise SystemExit(2) from None
