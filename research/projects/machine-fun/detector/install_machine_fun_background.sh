#!/bin/bash
set -euo pipefail
umask 077

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

if [ "$(uname -s)" != "Darwin" ]; then
  echo "MACHINE_BACKGROUND_BLOCKED: macOS required" >&2
  exit 2
fi

if ! command -v python3 >/dev/null 2>&1; then
  echo "MACHINE_BACKGROUND_BLOCKED: python3 missing" >&2
  exit 2
fi

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo "MACHINE_BACKGROUND_BLOCKED: Python 3.11+ required" >&2
  exit 2
fi

if [ -f "$HOME/Library/LaunchAgents/com.$(id -un).machine-fun-first-launch.plist" ]; then
  echo "MACHINE_BACKGROUND_ALREADY_INSTALLED: use machine_fun_service.py status/uninstall" >&2
  exit 2
fi

echo "MACHINE_PREFLIGHT=FRANK_CONFIG_READ_ONLY"
python3 machine_fun_runtime.py check

if [ ! -x "$HERE/.venv/bin/python" ]; then
  python3 -m venv "$HERE/.venv"
fi

if ! "$HERE/.venv/bin/python" -c 'import websockets; assert websockets.__version__ == "15.0.1"' >/dev/null 2>&1; then
  "$HERE/.venv/bin/python" -m pip install --disable-pip-version-check -r "$HERE/requirements.txt"
fi

echo "MACHINE_PREFLIGHT=OFFLINE_TESTS"
"$HERE/.venv/bin/python" -m unittest -q test_machine_launch_detector test_machine_launch_ws test_machine_launch_gmail test_machine_fun_service
"$HERE/.venv/bin/python" -m py_compile machine_launch_detector.py machine_launch_gmail.py machine_fun_runtime.py machine_fun_service.py

echo "MACHINE_PREFLIGHT=ALCHEMY_GMAIL_READ_ONLY_NETWORK"
"$HERE/.venv/bin/python" machine_fun_runtime.py probe

echo "MACHINE_PREFLIGHT=PASSED"
"$HERE/.venv/bin/python" machine_fun_service.py install
"$HERE/.venv/bin/python" machine_fun_service.py status

echo "MACHINE_BACKGROUND_INSTALL=COMPLETE"
echo "SERVICE=LOGIN_AUTOSTART_KEEPALIVE; GMAIL=EVENT_ONLY; FRANK=UNTOUCHED"
