#!/bin/bash
set -euo pipefail

USER_NAME="$(id -un)"
UID_VALUE="$(id -u)"
LOOP_LABEL="com.${USER_NAME}.frank-meme.loop"
DASH_LABEL="com.${USER_NAME}.frank-meme.dashboard"
LAUNCH_DIR="$HOME/Library/LaunchAgents"
LOOP_PLIST="$LAUNCH_DIR/$LOOP_LABEL.plist"
DASH_PLIST="$LAUNCH_DIR/$DASH_LABEL.plist"
APP_SUPPORT="$HOME/Library/Application Support/FrankMeme"

launchctl bootout "gui/$UID_VALUE" "$LOOP_PLIST" >/dev/null 2>&1 || true
launchctl bootout "gui/$UID_VALUE" "$DASH_PLIST" >/dev/null 2>&1 || true
launchctl disable "gui/$UID_VALUE/$LOOP_LABEL" >/dev/null 2>&1 || true
launchctl disable "gui/$UID_VALUE/$DASH_LABEL" >/dev/null 2>&1 || true

rm -f "$LOOP_PLIST" "$DASH_PLIST"
rm -f "$APP_SUPPORT/mission-loop.sh" "$APP_SUPPORT/dashboard.sh"
rm -f "$APP_SUPPORT/approved_policy_sha256" "$APP_SUPPORT/follow_policy_v1.approved.json" "$APP_SUPPORT/dashboard_port"

echo "Mission Meme LaunchAgents removed."
echo "mission-control.sqlite, observations, and logs were NOT deleted."
