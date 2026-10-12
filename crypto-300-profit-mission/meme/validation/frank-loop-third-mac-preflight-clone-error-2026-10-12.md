# Frank Mission Loop — third Mac read-only upgrade preflight and SQLite clone follow-up

## Source and scope

User supplied `frank-loop-upgrade-preflight-20261012-135251.zip`.
- SHA256: `a6c57173f8f6788cb0c664c16d59e588e678f592cc2e17a6d0d1a5bf6ac02cdd`
- Archive: `preflight.json` only (939 bytes total ZIP).
- Report timestamp: `2026-10-12T06:52:51.539030+00:00`
- Target merged PR34 release: `6a5b7e8a533f99c871e31f9674329fcb4f929cc2`

The artifact itself does not contain raw SQLite databases, local absolute paths, wallet identifiers, Gmail credential material or RPC values.

## Verified preflight signals

**SUCCESSFUL BEFORE THE ERROR**
- Legacy Loop and already-upgraded Dashboard were both running.
- Both policy JSON and approved SHA file and `RPC_FILE` now exist.
- The currently running Dashboard source exactly matches the pinned PR34 merge.
- Approved policy identity and 600-second notification maximum-age guard passed.
- OAuth credential-file permissions passed (file content/provider authentication not tested).
- Loop heartbeat existed and was fresh.
- Both production and control SQLite snapshots passed integrity checks.
- Control required tables and cloned new `ControlDB` schema initialization passed.
- The new-schema clone integrity check passed.

**EXACT OUTCOME:** `failure_stage_type=UPGRADE_CLONE_COMPATIBILITY:OperationalError` occurred after `CLONED_NEW_SCHEMA_INTEGRITY=PASS` and before `EXISTING_EVENTS_AND_DELIVERY_UNCHANGED`. The previous tool version did not capture SQLite error code or exact read substage; **cause currently UNCONFIRMED** (do not guess WAL, permissions, database corruption, or a real production failure).

## Snapshot counts (aggregate-only)

| Table | Persisted status | Count |
|---|---|---:|
| decision_outbox | COMMAND_ACCEPTED | 16 |
| decision_outbox | DRY_RUN_AUDIT | 2 |
| decision_outbox | MANUAL_REVIEW | 15 |
| decision_outbox | SENT_VERIFIED | 1 |
| gmail_delivery | DRY_RUN_AUDIT | 1 |
| gmail_delivery | MANUAL_REVIEW | 15 |
| gmail_delivery | SENT_VERIFIED | 1 |
| local_delivery | COMMAND_ACCEPTED | 16 |
| local_delivery | DRY_RUN_AUDIT | 1 |

The snapshot risk classifier reported `gmail_closed=16`, `local_closed=17` and did not report fresh sendable states. However, since the preflight stopped before its final replay gate, **do not claim upgrade-approved, full live-provider delivery verification or cross-time no-replay guarantee**.

Machine-result booleans indicate no Loop/Dashboard restart, Gmail-send attempt, production SQLite write, Git push or Loop deployment caused by this preflight.

## Remediation plan and restrictions

- Continue with a **diagnostic-only** revision of the same preflight that reports the exact SQLite substage and only the sqlite3 error code/name after clone initialization; never include the exception message since it may embed a private local file path.
- Reproduce the read-only reopened clone behavior using synthetic SQLite fixtures in isolated CI.
- Do not change the real Mac data, policy, restart controls, Gmail queue or RPC values. Do not bypass any final no-replay and PID gates.
- Any failing preflight must remain a blocker before live Loop restart.

Separate Dashboard UI change PR #35 is code-merged as `62697bf98606c19c5709c27006a6a40d9408db97`, not installed on Mac at this point.
