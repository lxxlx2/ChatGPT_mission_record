# Mission Meme macOS LaunchAgent

Purpose: keep the Mission Meme live-notification loop and localhost dashboard running after the macOS user logs back in.

This does not install or modify the Frank production watcher. The existing Frank production service remains separate.

## Safety boundaries

- Production Frank database remains read-only to Mission Control.
- PRODUCTION_TRADING remains NO_GO.
- The installer pins the currently approved policy SHA256. If follow_policy_v1.approved.json changes later, live delivery fails closed until the LaunchAgent is explicitly reinstalled/re-approved.
- Gmail credentials are reused from the existing local OAuth source. The installer performs a read-only readiness check and does not send a test email.
- No historical notification backlog is replayed by the installer.
- LaunchAgents start after the macOS user logs in, not before login.

## Install

From crypto-300-profit-mission/local-agent:

    bash scripts/install_mission_meme_launchd.sh

## Status

    bash scripts/status_mission_meme_launchd.sh

## Uninstall

    bash scripts/uninstall_mission_meme_launchd.sh

Uninstalling does not delete mission-control.sqlite, observation history, or logs.
