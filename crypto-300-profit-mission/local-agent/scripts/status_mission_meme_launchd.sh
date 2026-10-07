#!/bin/bash
set -euo pipefail

USER_NAME="$(id -un)"
UID_VALUE="$(id -u)"
LOOP_LABEL="com.${USER_NAME}.frank-meme.loop"
DASH_LABEL="com.${USER_NAME}.frank-meme.dashboard"
CONTROL_POINTER="${CONTROL_POINTER:-$HOME/.frank_meme_control_root}"
APP_SUPPORT="$HOME/Library/Application Support/FrankMeme"

TMP="/tmp/frank-meme-launchctl-$$.txt"
trap 'rm -f "$TMP"' EXIT

echo "=== Mission Meme LaunchAgent status ==="
for label in "$LOOP_LABEL" "$DASH_LABEL"; do
  echo
  echo "--- $label ---"
  if launchctl print "gui/$UID_VALUE/$label" >"$TMP" 2>/dev/null; then
    grep -E 'state =|pid =|last exit code =|runs =' "$TMP" | head -12 || true
  else
    echo "NOT_LOADED"
  fi
done

if [ -f "$CONTROL_POINTER" ]; then
  CONTROL="$(cat "$CONTROL_POINTER")"
  echo
  echo "Control root: $CONTROL"
  if [ -f "$CONTROL/mission-control-health.json" ]; then
    echo "Health:"
    cat "$CONTROL/mission-control-health.json"
    echo
  fi
fi

PORT="8766"
if [ -f "$APP_SUPPORT/dashboard_port" ]; then
  PORT="$(cat "$APP_SUPPORT/dashboard_port")"
fi

HTTP="$(curl -sS -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/" || true)"
echo "Dashboard HTTP=$HTTP"
echo "Dashboard=http://127.0.0.1:$PORT"

if [ -f "$APP_SUPPORT/approved_policy_sha256" ]; then
  echo "Pinned approved policy SHA256=$(cat "$APP_SUPPORT/approved_policy_sha256")"
fi
