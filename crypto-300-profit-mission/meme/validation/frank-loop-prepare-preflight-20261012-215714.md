# Frank Loop prepare-only Mac preflight receipt — 2026-10-12 21:57 ICT

## Uploaded evidence
- ZIP `frank-loop-upgrade-preflight-20261012-215714.zip` (SHA256 `7b6c49e9525f9d4e941648229854d8340d6c292d2d2edf90b505d676b3ea5d1d`)
- Single archive member `preflight.json`, 2484 unpacked bytes. ZIP CRC verified.
- Generated: `2026-10-12T14:57:14.925275+00:00`.
- Target: PR34 merge source `6a5b7e8a533f99c871e31f9674329fcb4f929cc2`.
- **30 PASS / 0 FAIL, failure_stage_type=null**; output is from **nested read-only preflight only**.

## Confirmed machine checks
Pinned Dashboard and running Loop, approved policy identity and 600s decision age, RPC files and Gmail OAuth file permissions, live heartbeat, consistent production/control DB snapshots, cloned ControlDB initialization/integrity, exact cloned original event/delivery aggregates, and no old Gmail/local sendable rows all PASS. Both Loop and Dashboard PID unchanged during nested preflight.

Aggregate outbox statuses: `COMMAND_ACCEPTED=16`, `DRY_RUN_AUDIT=2`, `MANUAL_REVIEW=15`, `SENT_VERIFIED=1`.
Gmail statuses: `DRY_RUN_AUDIT=1`, `MANUAL_REVIEW=15`, `SENT_VERIFIED=1`.
Local delivery: `COMMAND_ACCEPTED=16`, `DRY_RUN_AUDIT=1`. Delivery risk classifier `gmail_closed=16`, `local_closed=17`, with no fresh sendable historical rows.

Machine flags: `existing_loop_restarted_by_this_script=false`, `existing_dashboard_restarted_by_this_script=false`, `gmail_send_attempted_by_this_script=false`, `production_database_write_attempted=false`, `new_mission_loop_deployed=false`.

## Important distinction: nested preflight versus outer prepare receipt

The operator's command ran the **outer** opt-in PR36 release tool `frank_loop_only_rollout_20261012.py` in its default prepare-only mode, which **calls the nested preflight before** checking post-preflight PIDs, synthesizing/validating shell runner, and creating local private SQLite/runner backups.

The uploaded ZIP contains **only the nested preflight JSON**, not any outer tool output or backup receipt. Therefore **the result does not independently prove**:
- `FRESH_LOOP_PREFLIGHT=PASS` appeared on stdout;
- `CANDIDATE_RUNNER_SYNTAX=PASS`;
- `BACKUP_CREATED_PRIVATE=YES`, `RUNNER_BACKUP_IDENTICAL=PASS`;
- `LOOP_SWITCH=NOT_ATTEMPTED_DRY_RUN`;
- or the backup files exist with owner-only access.

The actual invocation omitted `--apply-loop` and did not authorize an upgrade. The outer tool's source only calls `launchctl kickstart` inside the opt-in apply mode; still, this ZIP alone cannot attest to any independent actions after nested preflight completed.

## Next read-only step

Request the sanitized **outer terminal output** (no RPC URL, OAuth secret, DB contents), or perform a minimal read-only `BACKUP_CREATED_PRIVATE`/PID/script receipt check on Mac. Do not upload SQLite backups or Gmail credentials. Continue holding **MAC_LOOP_DEPLOY=BLOCKED** until explicit authorization and release-phase validation.

This report is code+machine-evidence analysis, not remote Mac control.
