#!/bin/bash
set -euo pipefail
umask 077

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

if ! command -v python3 >/dev/null 2>&1; then
  echo "MACHINE_START_BLOCKED: python3 missing" >&2
  exit 2
fi

if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo "MACHINE_START_BLOCKED: Python 3.11+ required" >&2
  exit 2
fi

if [ "$1" = "check" ]; then
  exec python3 machine_fun_runtime.py check
fi

if [ ! -x "$HERE/.venv/bin/python" ]; then
  python3 -m venv "$HERE/.venv"
fi

if ! "$HERE/.venv/bin/python" -c 'import websockets; assert websockets.__version__ == "15.0.1"' >/dev/null 2>&1; then
  "$HERE/.venv/bin/python" -m pip install --disable-pip-version-check -r "$HERE/requirements.txt"
fi

exec "$HERE/.venv/bin/python" machine_fun_runtime.py "$@"
