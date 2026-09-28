#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$HOME/ChatGPT_mission_record}"
SCRIPT_REL="crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py"
SCRIPT_PATH="$REPO_DIR/$SCRIPT_REL"
DASHBOARD_PATH="$REPO_DIR/crypto-300-profit-mission/tools/technocore-close-call/dashboard_server.py"
UV_BIN="$(command -v uv || true)"
LABEL="com.lxx.technocore-close-call"
DASH_LABEL="com.lxx.technocore-close-call.dashboard"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
DASH_PLIST="$HOME/Library/LaunchAgents/$DASH_LABEL.plist"
LOG_DIR="$HOME/Library/Logs"
OUT_LOG="$LOG_DIR/technocore-close-call-autopilot.out.log"
ERR_LOG="$LOG_DIR/technocore-close-call-autopilot.err.log"

if [[ -z "$UV_BIN" ]]; then
  echo "uv not found in PATH"
  exit 1
fi

if [[ ! -f "$SCRIPT_PATH" ]]; then
  echo "missing $SCRIPT_PATH"
  echo "usage: $0 [repo_dir]"
  exit 1
fi

if [[ ! -f "$DASHBOARD_PATH" ]]; then
  echo "missing $DASHBOARD_PATH"
  echo "git pull first"
  exit 1
fi

mkdir -p "$HOME/Library/LaunchAgents" "$LOG_DIR"

cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$LABEL</string>

  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/caffeinate</string>
    <string>-dimsu</string>
    <string>$UV_BIN</string>
    <string>run</string>
    <string>$SCRIPT_PATH</string>
    <string>autopilot</string>
    <string>--poll</string>
    <string>30</string>
    <string>--late-minutes</string>
    <string>180</string>
  </array>

  <key>WorkingDirectory</key>
  <string>$REPO_DIR</string>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <dict>
    <key>SuccessfulExit</key>
    <false/>
  </dict>

  <key>ProcessType</key>
  <string>Background</string>

  <key>StandardOutPath</key>
  <string>$OUT_LOG</string>

  <key>StandardErrorPath</key>
  <string>$ERR_LOG</string>
</dict>
</plist>
PLIST

cat > "$DASH_PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>$DASH_LABEL</string>

  <key>ProgramArguments</key>
  <array>
    <string>$UV_BIN</string>
    <string>run</string>
    <string>$DASHBOARD_PATH</string>
    <string>--host</string>
    <string>127.0.0.1</string>
    <string>--port</string>
    <string>8765</string>
  </array>

  <key>WorkingDirectory</key>
  <string>$REPO_DIR</string>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <true/>

  <key>ProcessType</key>
  <string>Background</string>

  <key>StandardOutPath</key>
  <string>$LOG_DIR/technocore-close-call-dashboard.out.log</string>

  <key>StandardErrorPath</key>
  <string>$LOG_DIR/technocore-close-call-dashboard.err.log</string>
</dict>
</plist>
PLIST

plutil -lint "$PLIST"
plutil -lint "$DASH_PLIST"
chmod 0644 "$PLIST" "$DASH_PLIST"
touch "$OUT_LOG" "$ERR_LOG" \
  "$LOG_DIR/technocore-close-call-dashboard.out.log" \
  "$LOG_DIR/technocore-close-call-dashboard.err.log"

GUI_DOMAIN="gui/$(id -u)"

bootout_agent() {
  local label="$1"
  local plist="$2"

  # launchd teardown can lag behind bootout by a fraction of a second. A
  # bootstrap issued during that window commonly reports errno 5 / I/O error.
  launchctl bootout "$GUI_DOMAIN/$label" 2>/dev/null || true
  launchctl bootout "$GUI_DOMAIN" "$plist" 2>/dev/null || true

  for _ in 1 2 3 4 5; do
    if ! launchctl print "$GUI_DOMAIN/$label" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
}

bootstrap_agent() {
  local label="$1"
  local plist="$2"
  local ok=0

  for attempt in 1 2 3 4 5; do
    if launchctl bootstrap "$GUI_DOMAIN" "$plist"; then
      ok=1
      break
    fi

    # If launchd says bootstrap failed but the service actually exists, do not
    # fail the installer. This covers the "already loaded" form of errno 5.
    if launchctl print "$GUI_DOMAIN/$label" >/dev/null 2>&1; then
      echo "$label is already loaded after bootstrap attempt $attempt"
      ok=1
      break
    fi

    echo "bootstrap retry $attempt/5 for $label..."
    sleep 1
  done

  if [[ "$ok" -ne 1 ]]; then
    echo
    echo "ERROR: could not bootstrap $label"
    echo "plist: $plist"
    ls -l "$plist" || true
    echo "program: $(/usr/libexec/PlistBuddy -c 'Print :ProgramArguments:0' "$plist" 2>/dev/null || true)"
    echo "working directory: $(/usr/libexec/PlistBuddy -c 'Print :WorkingDirectory' "$plist" 2>/dev/null || true)"
    echo "launchctl service state:"
    launchctl print "$GUI_DOMAIN/$label" 2>&1 || true
    echo "recent stderr:"
    if [[ "$label" == "$DASH_LABEL" ]]; then
      tail -n 30 "$LOG_DIR/technocore-close-call-dashboard.err.log" 2>/dev/null || true
    else
      tail -n 30 "$ERR_LOG" 2>/dev/null || true
    fi
    return 1
  fi

  launchctl kickstart -k "$GUI_DOMAIN/$label"
}

bootout_agent "$LABEL" "$PLIST"
bootout_agent "$DASH_LABEL" "$DASH_PLIST"

bootstrap_agent "$LABEL" "$PLIST"
bootstrap_agent "$DASH_LABEL" "$DASH_PLIST"

echo "installed: $PLIST"
echo "status: launchctl print gui/$(id -u)/$LABEL"
echo "stdout: $OUT_LOG"
echo "stderr: $ERR_LOG"
echo "dashboard: http://127.0.0.1:8765"
echo "dashboard status: launchctl print gui/$(id -u)/$DASH_LABEL"
echo
echo "Important: the agent restarts after crashes but stays stopped after a clean contest-complete exit."
echo "caffeinate prevents idle sleep while this LaunchAgent is running."
echo "Closing a MacBook lid normally still suspends the machine. Keep the Mac powered, online,"
echo "and physically awake/open for unattended execution."
