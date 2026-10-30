#!/bin/bash
set -euo pipefail
umask 077

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
PY="$HERE/.venv/bin/python"

if [ "$#" -eq 0 ]; then
  echo "Usage: bash run_machine_fun.sh check|probe|run [--notify-local]" >&2
  exit 2
fi

if [ ! -x "$PY" ]; then
  if ! command -v python3 >/dev/null 2>&1; then
    echo "MACHINE_START_BLOCKED: Python 3.11+ required" >&2
    exit 2
  fi
  if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "MACHINE_START_BLOCKED: Python 3.11+ required" >&2
    exit 2
  fi
  if [ "$1" = "check" ]; then
    exec python3 machine_fun_runtime.py check
  fi
  python3 -m venv "$HERE/.venv"
fi

if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo "MACHINE_START_BLOCKED: Independent Python venv must use 3.11+" >&2
  exit 2
fi

if [ "$1" = "check" ]; then
  exec "$PY" machine_fun_runtime.py check
fi

if ! "$PY" -c 'import websockets; assert websockets.__version__ == "15.0.1"' >/dev/null 2>&1; then
  "$PY" -m pip install --disable-pip-version-check -r "$HERE/requirements.txt"
fi

if [ "$1" = "run" ]; then
  "$PY" -m unittest -q test_machine_launch_detector test_machine_launch_ws test_machine_launch_gmail
fi

exec "$PY" machine_fun_runtime.py "$@"
