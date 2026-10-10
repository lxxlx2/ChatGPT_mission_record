#!/bin/bash
# RH-only evidence replay; no LaunchAgents, Gmail, live DBs or trade signing.
set -euo pipefail
umask 077

ROOT="$(cd "$(dirname "$0")/.." && pwd -P)"
GIT_ROOT="$(git -C "$ROOT" rev-parse --show-toplevel)"
[ "$(git -C "$GIT_ROOT" rev-parse --abbrev-ref HEAD)" = "HEAD" ] || {
  echo "STOP: Run from pinned detached review worktree"
  exit 1
}
[ -z "$(git -C "$GIT_ROOT" status --porcelain)" ] || {
  echo "STOP: Review worktree modified"
  exit 1
}

PY="$HOME/.venvs/frank-meme-review/bin/python"
[ -x "$PY" ] || PY="/tmp/pr29-final-9BycDo/venv/bin/python"
[ -x "$PY" ] || { echo "STOP: No verified Python venv"; exit 1; }
export PYTHONPATH="$ROOT"
export PYTHONDONTWRITEBYTECODE=1
cd "$ROOT"

RESEARCH="$HOME/Documents/ChatGPT/frank-fomo-research"
RPC_FILE="$RESEARCH/rh_rpc_urls"
OLD_REPORT="$HOME/Documents/ChatGPT/frank-fomo-fixed-20261009-054846.json"
SOL_RPC="$HOME/Library/Application Support/FrankMeme/solana_rpc_urls"
[ -f "$OLD_REPORT" ] || {
  echo "STOP: Previously completed SOL evidence report not found"
  echo "EXPECTED_SOL_REPORT=$OLD_REPORT"
  exit 1
}
mkdir -p "$RESEARCH"
chmod 700 "$RESEARCH"

echo "===== RH AUTHENTICATED RPC PREFLIGHT ====="
if ! RPC_FILE="$RPC_FILE" SOL_RPC="$SOL_RPC" "$PY" -B -c '
import os
from pathlib import Path
from scripts.audit_frank_fomo_crosschain import (
  configured_robinhood_rpc_file, configured_solana_endpoints,
  derive_robinhood_alchemy_rpcs
)
rh_file=Path(os.environ["RPC_FILE"])
sol_file=Path(os.environ["SOL_RPC"])
providers=configured_robinhood_rpc_file(rh_file)
providers+=derive_robinhood_alchemy_rpcs(configured_solana_endpoints(sol_file))
providers+=[os.environ["ROBINHOOD_RPC_URL"]] if os.environ.get("ROBINHOOD_RPC_URL") else []
if providers:
    print("AUTHENTICATED_RH_RPC_CONFIGURED=YES")
else:
    print("AUTHENTICATED_RH_RPC_CONFIGURED=NO")
    raise SystemExit(3)
'; then
  echo "No reusable authenticated Robinhood RPC found."
  echo "Open your existing Alchemy app and copy its API KEY (not the wallet private key):"
  echo "https://dashboard.alchemy.com/apps/h6m5pairkgzet7vz"
  echo "The API key stays on this Mac in a private 0600 research-only file."
  read -r -s -p "Paste Alchemy API Key (hidden, Enter cancels): " KEY
  echo ""
  if [ -z "$KEY" ]; then echo "CANCELLED_NO_CHANGES"; exit 2; fi
  printf '%s' "$KEY" | RPC_FILE="$RPC_FILE" "$PY" -B -c '
import os, re, sys
from pathlib import Path
key=sys.stdin.read().strip()
if not re.fullmatch(r"[A-Za-z0-9_-]{8,256}",key):
    raise SystemExit("INVALID_ALCHEMY_API_KEY_FORMAT")
path=Path(os.environ["RPC_FILE"])
if path.exists() or path.is_symlink():
    raise SystemExit("RPC_CONFIG_ALREADY_EXISTS")
with path.open("x",encoding="utf-8") as out:
    out.write("https://robinhood-mainnet.g.alchemy.com/v2/"+key+"\n")
os.chmod(path,0o600)
print("PRIVATE_ALCHEMY_RH_RPC_STORED=YES")
'
  unset KEY
fi

echo "===== RH-ONLY HISTORICAL AUDIT ====="
REPORT="$RESEARCH/frank-rh-recheck-$(date +%Y%m%d-%H%M%S).json"
set +e
"$PY" -B scripts/audit_frank_fomo_crosschain.py \
  --hours 24 \
  --as-of-epoch 1791472854 \
  --solana-evidence-file "$OLD_REPORT" \
  --robinhood-rpc-file "$RPC_FILE" \
  --output "$REPORT"
RC=$?
set -e
echo "===== FINAL ====="
echo "AUDIT_EXIT=$RC"
echo "RESEARCH_REPORT=$REPORT"
echo "SOLANA_REUSED_PRIOR_COMPLETE_REPORT=YES"
echo "PRODUCTION_UNTOUCHED=YES"
exit "$RC"
