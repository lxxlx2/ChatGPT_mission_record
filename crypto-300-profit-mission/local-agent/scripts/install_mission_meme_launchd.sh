#!/bin/bash
set -euo pipefail

WORKTREE="${WORKTREE:-/Users/jerson/Documents/ChatGPT/frank-meme-main}"
LOCAL_AGENT="${LOCAL_AGENT:-$WORKTREE/crypto-300-profit-mission/local-agent}"
PROD="${PROD:-/Users/jerson/Documents/ChatGPT/crypto-monitor-frank-only-evidence-20261003/live-v1}"
VENV="${VENV:-$HOME/.venvs/frank-meme-review}"
CONTROL_POINTER="${CONTROL_POINTER:-$HOME/.frank_meme_control_root}"
POLICY="${POLICY:-$LOCAL_AGENT/config/follow_policy_v1.approved.json}"

USER_NAME="$(id -un)"
UID_VALUE="$(id -u)"
LOOP_LABEL="com.${USER_NAME}.frank-meme.loop"
DASH_LABEL="com.${USER_NAME}.frank-meme.dashboard"

APP_SUPPORT="$HOME/Library/Application Support/FrankMeme"
LOG_DIR="$HOME/Library/Logs/FrankMeme"
LAUNCH_DIR="$HOME/Library/LaunchAgents"

LOOP_RUNNER="$APP_SUPPORT/mission-loop.sh"
DASH_RUNNER="$APP_SUPPORT/dashboard.sh"
APPROVED_HASH_FILE="$APP_SUPPORT/approved_policy_sha256"
RUNTIME_POLICY="$APP_SUPPORT/follow_policy_v1.approved.json"
PORT_FILE="$APP_SUPPORT/dashboard_port"

LOOP_PLIST="$LAUNCH_DIR/$LOOP_LABEL.plist"
DASH_PLIST="$LAUNCH_DIR/$DASH_LABEL.plist"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

[ -e "$WORKTREE/.git" ] || die "WORKTREE_NOT_GIT: $WORKTREE"
[ -d "$LOCAL_AGENT" ] || die "LOCAL_AGENT_NOT_FOUND: $LOCAL_AGENT"
[ -f "$PROD/forward.sqlite" ] || die "PRODUCTION_DB_NOT_FOUND: $PROD/forward.sqlite"
[ -f "$PROD/health.json" ] || die "PRODUCTION_HEALTH_NOT_FOUND: $PROD/health.json"
[ -x "$VENV/bin/python" ] || die "VENV_PYTHON_NOT_FOUND: $VENV/bin/python"
[ -f "$CONTROL_POINTER" ] || die "CONTROL_POINTER_NOT_FOUND: $CONTROL_POINTER"
[ -f "$POLICY" ] || die "APPROVED_POLICY_NOT_FOUND: $POLICY"

CONTROL="$(cat "$CONTROL_POINTER")"
[ -n "$CONTROL" ] || die "CONTROL_POINTER_EMPTY"
[ -d "$CONTROL" ] || die "CONTROL_ROOT_NOT_FOUND: $CONTROL"

mkdir -p "$APP_SUPPORT" "$LOG_DIR" "$LAUNCH_DIR" "$CONTROL/logs"
chmod 700 "$APP_SUPPORT" "$LOG_DIR"

cp "$POLICY" "$RUNTIME_POLICY"
chmod 600 "$RUNTIME_POLICY"

POLICY_SHA="$(shasum -a 256 "$RUNTIME_POLICY" | awk '{print $1}')"
printf '%s\n' "$POLICY_SHA" > "$APPROVED_HASH_FILE"
chmod 600 "$APPROVED_HASH_FILE"

PORT="8766"
if [ -f "$CONTROL/dashboard.port" ]; then
  CANDIDATE_PORT="$(cat "$CONTROL/dashboard.port" 2>/dev/null || true)"
  if [[ "$CANDIDATE_PORT" =~ ^[0-9]+$ ]]; then
    PORT="$CANDIDATE_PORT"
  fi
fi
printf '%s\n' "$PORT" > "$PORT_FILE"
chmod 600 "$PORT_FILE"

"$VENV/bin/python" - "$RUNTIME_POLICY" "$POLICY_SHA" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
expected = sys.argv[2]
raw = path.read_bytes()
data = json.loads(raw)
actual = hashlib.sha256(raw).hexdigest()

assert actual == expected
assert data.get("status") == "FROZEN_APPROVED"
assert data.get("live_delivery_approved") is True
assert data.get("decision", {}).get("observation_retention_seconds") == 5184000

print("POLICY_GATE: PASS")
print("policy_sha256:", actual)
PY

PYTHONPATH="$LOCAL_AGENT" "$VENV/bin/python" - "$PROD" <<'PY'
import sys
from pathlib import Path
from mission_agent.signals.gmail_api import existing_provider

prod = Path(sys.argv[1])
provider = existing_provider(prod / "gmail-existing-source.json")
if provider is None:
    raise SystemExit("GMAIL_PROVIDER_NOT_CONFIGURED")
provider.ready()
print("GMAIL_PREFLIGHT: PASS")
print("gmail_recipient:", provider.recipient)
print("NO_EMAIL_SENT")
PY

cat > "$LOOP_RUNNER" <<EOF
#!/bin/bash
set -euo pipefail
LOCAL_AGENT="$LOCAL_AGENT"
PROD="$PROD"
VENV="$VENV"
CONTROL_POINTER="$CONTROL_POINTER"
POLICY="$RUNTIME_POLICY"
APPROVED_HASH_FILE="$APPROVED_HASH_FILE"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
CONTROL="\$(cat "\$CONTROL_POINTER")"
APPROVED_HASH="\$(cat "\$APPROVED_HASH_FILE")"
mkdir -p "\$CONTROL/logs"
cd "\$LOCAL_AGENT"
echo "\$\$" > "\$CONTROL/loop.pid"
exec env PYTHONPATH=. "\$VENV/bin/python" scripts/mission_meme_v1.py loop \
  --production-root "\$PROD" \
  --control-root "\$CONTROL" \
  --policy "\$POLICY" \
  --live-delivery \
  --approved-policy-sha256 "\$APPROVED_HASH" \
  --interval 5
EOF

cat > "$DASH_RUNNER" <<EOF
#!/bin/bash
set -euo pipefail
LOCAL_AGENT="$LOCAL_AGENT"
PROD="$PROD"
VENV="$VENV"
CONTROL_POINTER="$CONTROL_POINTER"
PORT_FILE="$PORT_FILE"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
CONTROL="\$(cat "\$CONTROL_POINTER")"
PORT="\$(cat "\$PORT_FILE")"
mkdir -p "\$CONTROL/logs"
cd "\$LOCAL_AGENT"
echo "\$\$" > "\$CONTROL/dashboard.pid"
printf '%s\n' "\$PORT" > "\$CONTROL/dashboard.port"
exec env PYTHONPATH=. "\$VENV/bin/python" scripts/mission_meme_v1.py serve \
  --production-root "\$PROD" \
  --control-root "\$CONTROL" \
  --host 127.0.0.1 \
  --port "\$PORT"
EOF

chmod 700 "$LOOP_RUNNER" "$DASH_RUNNER"

cat > "$LOOP_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LOOP_LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$LOOP_RUNNER</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>ProcessType</key>
  <string>Background</string>
  <key>ThrottleInterval</key>
  <integer>10</integer>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/loop.stdout.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/loop.stderr.log</string>
</dict>
</plist>
EOF

cat > "$DASH_PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$DASH_LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$DASH_RUNNER</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>ProcessType</key>
  <string>Background</string>
  <key>ThrottleInterval</key>
  <integer>10</integer>
  <key>StandardOutPath</key>
  <string>$LOG_DIR/dashboard.stdout.log</string>
  <key>StandardErrorPath</key>
  <string>$LOG_DIR/dashboard.stderr.log</string>
</dict>
</plist>
EOF

chmod 600 "$LOOP_PLIST" "$DASH_PLIST"

stop_manual_pid() {
  local pidfile="$1"
  local marker="$2"
  local pid=""
  local cmd=""
  [ -f "$pidfile" ] || return 0
  pid="$(cat "$pidfile" 2>/dev/null || true)"
  [[ "$pid" =~ ^[0-9]+$ ]] || return 0
  kill -0 "$pid" 2>/dev/null || return 0
  cmd="$(ps -p "$pid" -o command= 2>/dev/null || true)"
  if [[ "$cmd" == *"mission_meme_v1.py $marker"* ]]; then
    echo "Stopping manual $marker PID $pid"
    kill "$pid" 2>/dev/null || true
    for _ in 1 2 3 4 5; do
      kill -0 "$pid" 2>/dev/null || break
      sleep 1
    done
  fi
}

stop_manual_pid "$CONTROL/loop.pid" "loop"
stop_manual_pid "$CONTROL/dashboard.pid" "serve"

launchctl bootout "gui/$UID_VALUE" "$LOOP_PLIST" >/dev/null 2>&1 || true
launchctl bootout "gui/$UID_VALUE" "$DASH_PLIST" >/dev/null 2>&1 || true

launchctl bootstrap "gui/$UID_VALUE" "$LOOP_PLIST"
launchctl bootstrap "gui/$UID_VALUE" "$DASH_PLIST"
launchctl enable "gui/$UID_VALUE/$LOOP_LABEL"
launchctl enable "gui/$UID_VALUE/$DASH_LABEL"
launchctl kickstart -k "gui/$UID_VALUE/$LOOP_LABEL"
launchctl kickstart -k "gui/$UID_VALUE/$DASH_LABEL"

sleep 5

echo
echo "=== LaunchAgent status ==="
for label in "$LOOP_LABEL" "$DASH_LABEL"; do
  echo "--- $label ---"
  launchctl print "gui/$UID_VALUE/$label" 2>/dev/null | grep -E 'state =|pid =|last exit code =' | head -10 || true
done

echo
echo "=== Mission Control health ==="
cat "$CONTROL/mission-control-health.json" 2>/dev/null || true

echo
HTTP="$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/" || true)"
echo "Dashboard HTTP=$HTTP"
echo "Dashboard=http://127.0.0.1:$PORT"
echo "Approved policy SHA256=$POLICY_SHA"
echo "Runtime policy=$RUNTIME_POLICY"
echo "AUTO-START: ON AFTER USER LOGIN"
echo "LIVE DELIVERY: policy-gated"
echo "PRODUCTION_TRADING: NO_GO"
