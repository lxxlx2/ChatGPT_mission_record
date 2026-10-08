#!/bin/bash
# One-entry Mac operator flow: regression -> real RPC coverage -> safe deployment.
# Read-only chain audit is informational and never blocks a UI-only rollout.
set -euo pipefail

AGENT="$(cd "$(dirname "$0")/.." && pwd -P)"
ROOT="$(git -C "$AGENT" rev-parse --show-toplevel)"
EXPECTED="$(printenv EXPECTED_HEAD || true)"

[ -n "$EXPECTED" ] || { echo "STOP: EXPECTED_HEAD not supplied"; exit 1; }
[ "$(git -C "$ROOT" rev-parse HEAD)" = "$EXPECTED" ] || { echo "STOP: Git release HEAD mismatch"; exit 1; }
[ "$(git -C "$ROOT" rev-parse --abbrev-ref HEAD)" = "HEAD" ] || { echo "STOP: Expected detached immutable release worktree"; exit 1; }
[ -z "$(git -C "$ROOT" status --porcelain)" ] || { echo "STOP: Release worktree has modifications"; exit 1; }

TEST_PY=""
for CANDIDATE in \
  "$HOME/.venvs/frank-meme-review/bin/python" \
  "/tmp/pr29-final-9BycDo/venv/bin/python"; do
  if [ -x "$CANDIDATE" ] && "$CANDIDATE" -B -c 'import pytest' >/dev/null 2>&1; then
    TEST_PY="$CANDIDATE"
    break
  fi
done
[ -n "$TEST_PY" ] || { echo "STOP: Tested pytest virtualenv not found"; exit 1; }

echo "===== A. SOURCE VALIDATION ====="
"$TEST_PY" -B - "$AGENT" <<'PY'
from pathlib import Path
import sys
root=Path(sys.argv[1])
for file in ("mission_agent/mission_control/frank.py",
             "mission_agent/mission_control/server.py",
             "scripts/audit_frank_live_24h.py",
             "scripts/deploy_mission_meme_pr29.py"):
    compile((root/file).read_text(encoding="utf-8"), file, "exec")
print("PYTHON_SYNTAX=PASS")
PY

echo "===== B. REGRESSION TESTS ====="
cd "$AGENT"
export PYTHONDONTWRITEBYTECODE=1
PYTHONPATH=. "$TEST_PY" -B -m pytest -q -p no:cacheprovider \
  tests/test_mission_control_dashboard.py \
  tests/test_mission_control_delivery.py
PYTHONPATH=. "$TEST_PY" -B -m pytest -q -p no:cacheprovider
[ -z "$(git -C "$ROOT" status --porcelain)" ] || {
  echo "STOP: Worktree modified by tests"
  exit 1
}

echo "===== C. FRANK FULL-WALLET RPC SIGNATURE AUDIT (24h) ====="
PROD="$HOME/Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/live-v1"
RPC_FILE="$HOME/Library/Application Support/FrankMeme/solana_rpc_urls"
if [ ! -f "$PROD/forward.sqlite" ] || [ ! -f "$RPC_FILE" ]; then
  echo "CHAIN_AUDIT_STATUS=PRECHECK_MISSING"
else
  set +e
  "$TEST_PY" -B scripts/audit_frank_live_24h.py \
    --db "$PROD/forward.sqlite" --rpc-file "$RPC_FILE" --hours 24
  AUDIT_RC=$?
  set -e
  echo "CHAIN_AUDIT_EXIT=$AUDIT_RC"
  if [ "$AUDIT_RC" -eq 0 ]; then
    echo "CHAIN_AUDIT_STATUS=PASS"
  elif [ "$AUDIT_RC" -eq 3 ]; then
    echo "CHAIN_AUDIT_STATUS=COVERAGE_MISMATCH_INVESTIGATE_SOURCE"
  else
    echo "CHAIN_AUDIT_STATUS=UNAVAILABLE_NOT_VERIFIED"
  fi
fi

echo "===== D. SAFE UPDATE OF EXISTING DASHBOARD + MISSION LOOP ====="
"$TEST_PY" -B scripts/deploy_mission_meme_pr29.py \
  --apply --expected-head "$EXPECTED" \
  --confirm YES_RESTART_LOOP_DASHBOARD

echo "===== FINAL ====="
echo "APP_TESTS=PASS"
echo "DASHBOARD_AND_LOOP_DEPLOY=PASS"
echo "FRANK_WRITER=UNTOUCHED"
echo "PRODUCTION_TRADING=NO_GO"
