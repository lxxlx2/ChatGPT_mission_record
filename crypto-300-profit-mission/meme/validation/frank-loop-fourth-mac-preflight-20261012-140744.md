# Frank Mission Loop read-only preflight #4 — Mac SQLite diagnostic and fix (2026-10-12)

## User upload and exact observed result

Uploaded artifact: `frank-loop-upgrade-preflight-20261012-140744.zip`; SHA256 `062c584b529cd8f83f422f7b9063e272409a8f8e98e72341d6a0fcdeb3643740`. Contains a single JSON preflight report (no raw SQLite file, signer secret, OAuth token or RPC URL).
Reported timestamp `2026-10-12T07:07:44.366418+00:00`.

Target source is merged PR #34 release `6a5b7e8a533f99c871e31f9674329fcb4f929cc2`. PR #35 layout code was separately merged at `62697bf98606c19c5709c27006a6a40d9408db97` but **not yet deployed** to Mac.

### Machine checks

23 `PASS`, no explicit check returned `FAIL`. The run still ended **BLOCKED**:
`failure_stage_type=UPGRADE_CLONE_COMPATIBILITY:OperationalError`.

Among successful checks: authorized policy identity and SHA, required RPC/credential files, 600-second freshness bound, live Loop heartbeat, two production/control SQLite snapshot integrity checks, cloned-new-schema bootstrap and integrity check, and read-only clone re-open.

Diagnostic isolated the raised `OperationalError` to `POST_CLONE_SQLITE_INTEGRITY`: the additional `PRAGMA integrity_check` called through a *new* `query_only` connection after the same clone had already completed integrity checking inside the new-code ControlDB subprocess. SQLite error code and name could not be extracted beyond `OperationalError` and `null`, so **precise failure cause remains unconfirmed**.

The report indicated no `-wal` nor `-shm` sidecars were present before the post-clone re-open. This alone **does not establish** a WAL error.

## DB/notification evidence, aggregate-only

- `decision_outbox`: 16 COMMAND_ACCEPTED, 2 DRY_RUN_AUDIT, 15 MANUAL_REVIEW, 1 SENT_VERIFIED
- `gmail_delivery`: 1 DRY_RUN_AUDIT, 15 MANUAL_REVIEW, 1 SENT_VERIFIED
- `local_delivery`: 16 COMMAND_ACCEPTED, 1 DRY_RUN_AUDIT
- Risk classifier: `gmail_closed=16`, `local_closed=17`. No fresh-sendable historic Gmail or local entries found **in this snapshot**.

The final hard anti-replay and launch-PID unchanged assertions were not run, hence **LOOP_UPGRADE_NOT_AUTHORIZED**.

The preflight explicitly reports it did not restart either Loop/Dashboard, send Gmail, write the real production database, push Git or deploy the updated Loop.

## Targeted fix and tests

The preflight already obtains database integrity twice (consistent production/control snapshot integrity and the new ControlDB subprocess on a disposable clone). The redundant third `PRAGMA integrity_check` after read-only re-open was replaced by a regular `SELECT COUNT(*) FROM sqlite_master` check and exact pre-/post-clone status/row comparisons. Thus it keeps both earlier integrity guarantees, does not bypass actual clone row reading, and still hard-fails if any event/delivery state diverges. It is only a test-harness change.

Added regressions ensure (a) no second integrity pragma is invoked; (b) read-only table queries work; (c) row-count drift is a hard BLOCK rather than a pass.

[GitHub Actions run 38216274259](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38216274259): **SUCCESS** with **16 standalone safety tests and 1,244 full local-agent tests passed**, 0 skipped/failed, plus syntax and pyflakes checks. No local Mac upgrade was attempted in CI.

## Next

Execute the revised **strictly read-only** Mac preflight once and check that `POST_CLONE_ROW_READABLE`, `EXISTING_EVENTS_AND_DELIVERY_UNCHANGED`, `NO_FRESH_SENDABLE_LEGACY_GMAIL`, `NO_FRESH_SENDABLE_LOCAL_NOTIFICATION`, `EXISTING_LOOP_PID_UNCHANGED` and `EXISTING_DASHBOARD_PID_UNCHANGED` are all PASS.

If Mac SQLite still fails at a simple read, capture the safe error stage and code; do not weaken the checks or restart the Loop. If all pass, this is only a preflight and the live Loop upgrade still requires a separately reviewed reversible Loop-only switch.

No secrets, absolute local paths, wallet addresses or raw DB rows are included in this report.
