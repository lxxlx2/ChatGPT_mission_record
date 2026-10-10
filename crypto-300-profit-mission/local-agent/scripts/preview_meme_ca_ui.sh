#!/bin/bash
set -euo pipefail

AGENT="$(cd "$(dirname "$0")/.." && pwd -P)"
ROOT="$(git -C "$AGENT" rev-parse --show-toplevel)"
[ "$(git -C "$ROOT" rev-parse --abbrev-ref HEAD)" = "HEAD" ] || {
  echo "STOP: preview requires an immutable detached worktree"
  exit 2
}

PY="$HOME/.venvs/frank-meme-review/bin/python"
if [ ! -x "$PY" ]; then PY="$(command -v python3)"; fi
"$PY" -B -c 'import sys; assert sys.version_info >= (3,11)' || {
  echo "STOP: Python 3.11+ required"
  exit 2
}

RESEARCH_ROOT="$(mktemp -d /tmp/frank-meme-ca-preview.XXXXXXXX)"
trap 'rm -rf "$RESEARCH_ROOT"' EXIT
mkdir -m 700 "$RESEARCH_ROOT/isolated-control" "$RESEARCH_ROOT/empty-prod"

RPC_FILE="$HOME/Library/Application Support/FrankMeme/solana_rpc_urls"
if [ -f "$RPC_FILE" ]; then
  "$PY" -B - "$RPC_FILE" <<'PY'
import os,sys
p=sys.argv[1]
if os.path.islink(p) or os.stat(p).st_mode & 0o077:
    raise SystemExit("STOP: Solana RPC file is not private 0600")
PY
  export SOLANA_RPC_URLS="$(cat "$RPC_FILE")"
fi

echo "REVIEW_ONLY_CA_PREVIEW=YES"
echo "LIVE_FRANK_MONITOR=UNTOUCHED"
echo "LIVE_FOLLOW_POLICY=UNTOUCHED"
echo "PRODUCTION_DB_WRITES=0"
echo "EMAILS_SENT=0"
echo "Open http://127.0.0.1:8877/#cluster"
echo "Press Ctrl-C after reviewing the CA page"

cd "$AGENT"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=.
"$PY" -B - "$RESEARCH_ROOT" <<'PY'
from pathlib import Path
import sys
from mission_agent.mission_control.server import serve
root=Path(sys.argv[1])
serve(root/"empty-prod",root/"isolated-control",host="127.0.0.1",port=8877)
PY
