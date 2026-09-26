#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${1:-$HOME/ChatGPT_mission_record}"
SCRIPT_REL="crypto-300-profit-mission/tools/technocore-close-call/close_call_fleet.py"
SCRIPT_PATH="$REPO_DIR/$SCRIPT_REL"
UV_BIN="$(command -v uv || true)"
LABEL="com.lxx.technocore-close-call"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
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
    <string>60</string>
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

plutil -lint "$PLIST"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl kickstart -k "gui/$(id -u)/$LABEL"

echo "installed: $PLIST"
echo "status: launchctl print gui/$(id -u)/$LABEL"
echo "stdout: $OUT_LOG"
echo "stderr: $ERR_LOG"
echo
echo "Important: the agent restarts after crashes but stays stopped after a clean contest-complete exit."
echo "caffeinate prevents idle sleep while this LaunchAgent is running."
echo "Closing a MacBook lid normally still suspends the machine. Keep the Mac powered, online,"
echo "and physically awake/open for unattended execution."
