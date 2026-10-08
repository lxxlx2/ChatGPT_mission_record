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
RPC_FILE="$APP_SUPPORT/solana_rpc_urls"

LOOP_PLIST="$LAUNCH_DIR/$LOOP_LABEL.plist"
DASH_PLIST="$LAUNCH_DIR/$DASH_LABEL.plist"

die() {
  echo "ERROR: $*" >&2
  exit 1
}

# This installer replaces both active LaunchAgents, including live-delivery loop.
# No writes, PID stops or launchctl mutation without explicit opt-in.
[ "${CONFIRM_MISSION_LOOP_RESTART:-}" = "1" ] || die "MISSION_LOOP_RESTART_NOT_AUTHORIZED: explicit CONFIRM_MISSION_LOOP_RESTART=1 required"

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

# PREPARE AND AUTHORIZE before mutating any installed policy, credential,
# runner, plist or launchd state. No self-approval from a candidate's own hash.
[ -n "${APPROVED_POLICY_SHA256:-}" ] || die "EXTERNAL_POLICY_APPROVAL_REQUIRED"
if [ -n "${SOLANA_RPC_URLS:-}" ]; then
  RPC_URLS_VALUE="$SOLANA_RPC_URLS"
else
  [ -f "$RPC_FILE" ] || die "SOLANA_RPC_URLS_NOT_CONFIGURED"
  RPC_URLS_VALUE="$(cat "$RPC_FILE" 2>/dev/null || true)"
fi
[ -n "$RPC_URLS_VALUE" ] || die "SOLANA_RPC_URLS_EMPTY"

# Copy the policy once into a private temporary snapshot, outside installed
# Application Support. OAuth preflight may delay installation, but editing the
# original policy during this delay cannot alter the approved bytes.
STAGED_POLICY="$(mktemp "${TMPDIR:-/tmp}/frank-meme-policy.XXXXXXXX")"
chmod 600 "$STAGED_POLICY"
trap 'rm -f "$STAGED_POLICY"' EXIT
cat "$POLICY" > "$STAGED_POLICY"

# Use the EXACT authorization predicate also enforced by MissionMemeService.
# The external digest is supplied by the operator via environment; it is
# never derived from the candidate policy by this installer.
PYTHONPATH="$LOCAL_AGENT" "$VENV/bin/python" - "$STAGED_POLICY" "$APPROVED_POLICY_SHA256" <<'PY'
import sys
from mission_agent.mission_control.policy import (
    load_policy, live_delivery_policy_authorized,
)
policy, actual = load_policy(sys.argv[1])
if not live_delivery_policy_authorized(policy, actual, sys.argv[2]):
    raise SystemExit("POLICY_NOT_AUTHORIZED")
print("POLICY_GATE: PASS")
print("policy_sha256:", actual)
PY
POLICY_SHA="$APPROVED_POLICY_SHA256"

# External OAuth/readiness preflight occurs after policy authorization,
# but BEFORE any installed state is altered. This only validates readiness.
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

PORT="8766"
if [ -f "$CONTROL/dashboard.port" ]; then
  CANDIDATE_PORT="$(cat "$CONTROL/dashboard.port" 2>/dev/null || true)"
  if [[ "$CANDIDATE_PORT" =~ ^[0-9]+$ ]]; then
    PORT="$CANDIDATE_PORT"
  fi
fi

# The following writes are permitted only AFTER all policy/preflight gates.
mkdir -p "$APP_SUPPORT" "$LOG_DIR" "$LAUNCH_DIR" "$CONTROL/logs"
chmod 700 "$APP_SUPPORT" "$LOG_DIR"
umask 077
install_atomic() {
  local dest="$1"
  local temp
  temp="$(mktemp "$APP_SUPPORT/.mission-install.XXXXXXXX")"
  cat > "$temp"
  chmod 600 "$temp"
  mv -f "$temp" "$dest"
}

# Two independent atomic replaces. A crash between them fails closed because
# policy bytes and externally approved digest cannot match until both commit.
PREVIOUS_RUNTIME_POLICY=""
if [ -f "$RUNTIME_POLICY" ]; then
  PREVIOUS_RUNTIME_POLICY="$(mktemp "${TMPDIR:-/tmp}/frank-meme-previous.XXXXXXXX")"
  chmod 600 "$PREVIOUS_RUNTIME_POLICY"
  cat "$RUNTIME_POLICY" > "$PREVIOUS_RUNTIME_POLICY"
fi
install_atomic "$RUNTIME_POLICY" < "$STAGED_POLICY"
INSTALLED_POLICY_SHA="$(shasum -a 256 "$RUNTIME_POLICY" | awk '{print $1}')"
if [ "$INSTALLED_POLICY_SHA" != "$POLICY_SHA" ]; then
  if [ -n "$PREVIOUS_RUNTIME_POLICY" ]; then
    install_atomic "$RUNTIME_POLICY" < "$PREVIOUS_RUNTIME_POLICY"
  else
    rm -f "$RUNTIME_POLICY"
  fi
  [ -z "$PREVIOUS_RUNTIME_POLICY" ] || rm -f "$PREVIOUS_RUNTIME_POLICY"
  die "POST_INSTALL_POLICY_HASH_MISMATCH"
fi
[ -z "$PREVIOUS_RUNTIME_POLICY" ] || rm -f "$PREVIOUS_RUNTIME_POLICY"
printf '%s\n' "$POLICY_SHA" | install_atomic "$APPROVED_HASH_FILE"
if [ -n "${SOLANA_RPC_URLS:-}" ]; then
  printf '%s\n' "$SOLANA_RPC_URLS" | install_atomic "$RPC_FILE"
fi
chmod 600 "$RPC_FILE"
printf '%s\n' "$PORT" | install_atomic "$PORT_FILE"

cat > "$LOOP_RUNNER" <<EOF
#!/bin/bash
set -euo pipefail
LOCAL_AGENT="$LOCAL_AGENT"
PROD="$PROD"
VENV="$VENV"
CONTROL_POINTER="$CONTROL_POINTER"
POLICY="$RUNTIME_POLICY"
APPROVED_HASH_FILE="$APPROVED_HASH_FILE"
RPC_FILE="$RPC_FILE"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
CONTROL="\$(cat "\$CONTROL_POINTER")"
APPROVED_HASH="\$(cat "\$APPROVED_HASH_FILE")"
SOLANA_RPC_URLS="\$(cat "\$RPC_FILE")"
[ -n "\$SOLANA_RPC_URLS" ] || { echo "ERROR: SOLANA_RPC_URLS_EMPTY" >&2; exit 1; }
export SOLANA_RPC_URLS
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
RPC_FILE="$RPC_FILE"
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
CONTROL="\$(cat "\$CONTROL_POINTER")"
PORT="\$(cat "\$PORT_FILE")"
SOLANA_RPC_URLS="\$(cat "\$RPC_FILE")"
[ -n "\$SOLANA_RPC_URLS" ] || { echo "ERROR: SOLANA_RPC_URLS_EMPTY" >&2; exit 1; }
export SOLANA_RPC_URLS
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
echo "Authenticated Solana RPC: CONFIGURED (secret not printed)"
echo "AUTO-START: ON AFTER USER LOGIN"
echo "LIVE DELIVERY: policy-gated"
echo "PRODUCTION_TRADING: NO_GO"
