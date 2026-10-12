# Mission Loop sixth Mac preflight — all gates passed (2026-10-12)

## Raw evidence
- User-provided ZIP: `frank-loop-upgrade-preflight-20261012-174743.zip`
- SHA256: `43009f88c9765a5470acea5a345f7793c5a9f1be41ed940e99bfcda1dc0c390d`
- Single archive member: `preflight.json` (sanitized aggregate-only, not raw DB or secrets)
- Report time UTC: `2026-10-12T10:47:43.661927+00:00`
- Target source: `6a5b7e8a533f99c871e31f9674329fcb4f929cc2`
- Machine result: **31 PASS / 0 FAIL / failure_stage_type = null**.
- Stage summary printed by program: `PRECHECK=PASS_NEW_LOOP_NOT_DEPLOYED`.

## Important completed checks
`CURRENT_DASHBOARD_IS_MERGED_RELEASE`, `DASHBOARD_SOURCE_PINNED_PR34`, `RUNNER_MODE_POLICY_UNCHANGED`, `APPROVED_POLICY_FILES`, `APPROVED_POLICY_IDENTITY`, `DECISION_AGE_GATE`, `OAUTH_FILE_OWNER_ONLY_PERMISSION`, `LIVE_LOOP_HEALTH_FRESH`, `SNAPSHOT_SQLITE_INTEGRITY`, `CLONED_NEW_SCHEMA_BOOTSTRAP`, `CLONED_NEW_SCHEMA_INTEGRITY`, `CLONED_AGGREGATES_READ`, `EXISTING_EVENTS_AND_DELIVERY_UNCHANGED`, `NO_FRESH_SENDABLE_LEGACY_GMAIL`, `NO_FRESH_SENDABLE_LOCAL_NOTIFICATION`, `EXISTING_LOOP_PID_UNCHANGED` and `EXISTING_DASHBOARD_PID_UNCHANGED` all **PASS**.

Age gate: 600 seconds. Gmail delivery states: MANUAL_REVIEW=15, SENT_VERIFIED=1, DRY_RUN_AUDIT=1. Local delivery: COMMAND_ACCEPTED=16, DRY_RUN_AUDIT=1. All Gmail/local records were categorized as closed, with **no fresh sendable prior rows in this snapshot**. Original outbox: COMMAND_ACCEPTED=16, DRY_RUN_AUDIT=2, MANUAL_REVIEW=15, SENT_VERIFIED=1.

## Scope and limitations
The Mac user ran a strictly read-only preflight. The report explicitly states both Loop/Dashboard remained running and no Loop restart, new Loop deployment, Gmail send attempt, production database write, or Git push was initiated by this script. It does **not** verify provider Gmail Sent records independently or the future ability to send new Gmail notifications.

**LOOP_RELEASE_GATES:** preflight PASSED, code-only combined PR34 CI PASSED. A separately reviewed loop-only **transactional rollout & rollback script** and explicit operator opt-in are still required before touching the live Loop. Keep the previously deployed Dashboard intact and do not silently enable `MISSION_EVIDENCE_EXPORT_ENABLED=1`, retry stale Gmail, reset the SQLite database, or change approved policy, RPC URLs or live trading logic.

PR35 follow-opportunities-first HTML/CSS is separately merged but **not deployed to Mac** at this stage.
