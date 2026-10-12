# Frank live Mission Loop: fifth Mac read-only preflight, 2026-10-12

## Provenance

User uploaded `frank-loop-upgrade-preflight-20261012-141337.zip`.
- SHA256: `c128ebfd6db6fcb30fef20a03a47ddca4aa7d5e742186b493161d6a53c7b6ab3`
- Contains only `preflight.json` (2416 bytes), no credentials or raw SQLite files.
- Target release: `6a5b7e8a533f99c871e31f9674329fcb4f929cc2`
- Report UTC: `2026-10-12T07:13:37.478266+00:00`

## Verified status

**PRECHECK BLOCKED. Live Mission Loop was NOT updated or restarted.**

This report contains **23 PASS** flags, no explicit check marked FAIL; the script caught an exception before later gates:
`failure_stage_type=UPGRADE_CLONE_COMPATIBILITY:OperationalError`.

The exact sanitized detail is:
- `clone_stage=POST_CLONE_ROW_READABILITY`;
- `clone_sqlite_error_name=OperationalError`;
- `clone_sqlite_error_code=null`;
- `clone_wal_sidecar_present=false`, `clone_shm_sidecar_present=false`.

The `null` extended code is **not evidence that the error is harmless**; this macOS Python/SQLite combination did not provide it. There is no reliable message category. Do not assert WAL corruption, missing schema, or the reason for the read-only SELECT failure.

**Passed**: runner presence and version pin, policy/RPC/approved digest presence and policy approval identity, 600s age policy, OAuth file owner-only permissions, live heartbeat, two production/control SQLite snapshots with integrity checks, `CLONED_NEW_SCHEMA_BOOTSTRAP`, `CLONED_NEW_SCHEMA_INTEGRITY`, and `POST_CLONE_READONLY_REOPEN`.

**Not run**: `EXISTING_EVENTS_AND_DELIVERY_UNCHANGED`, `NO_FRESH_SENDABLE_LEGACY_GMAIL`, `NO_FRESH_SENDABLE_LOCAL_NOTIFICATION`, final live Loop and Dashboard PID checks. Consequently, no authorization to restart.

## Aggregate notification observations (frozen snapshot, not provider Sent evidence)

- Outbox: `COMMAND_ACCEPTED=16`, `DRY_RUN_AUDIT=2`, `MANUAL_REVIEW=15`, `SENT_VERIFIED=1`.
- Gmail: `DRY_RUN_AUDIT=1`, `MANUAL_REVIEW=15`, `SENT_VERIFIED=1`.
- Local: `COMMAND_ACCEPTED=16`, `DRY_RUN_AUDIT=1`.
- Classifier: `gmail_closed=16`, `local_closed=17`. No fresh preexisting pending notifications indicated in this snapshot, but the final hard checks did not execute.

## Corrective architectural change (only to disposable preflight)

The old harness opened a copied control SQLite as a new writable `ControlDB` in a child process, verified it was internally integral, **closed that connection**, and then opened the copied DB `mode=ro/query_only` from the parent. Both a duplicate `PRAGMA integrity_check` and a simple read of `sqlite_master` through this **second** connection raised `OperationalError` on the Mac; this is the observed behavior, not a proven root cause.

The new harness keeps the same consistent original SQLite snapshots and original aggregate reads. It initializes the new `ControlDB` **only against the disposable copied DB**, validates SQLite integrity, reads all required table counts and exact delivery-status aggregates **inside that same child connection**, and returns a JSON count-only result to the parent for strict equality checks. It eliminates the second reader of a just-closed writable WAL-mode clone. The final anti-replay and stable process-PID checks remain unchanged.

## Independent CI evidence

- New test/preflight commit: `e3fffcd4dffbf6be82694f6efbf64d6df95aef5e`
- Preflight Git blob: `757045184a39467e8e33804450fafdc8b475fe6c`
- [GitHub Actions 38216935138](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38216935138) **SUCCESS**; 16 focused tests passed, 1244 full local-agent tests passed, 0 skipped or failed, static gate passed. Test includes a real subprocess opening an isolated synthetic SQLite clone and checking all rows and status aggregates; tampering with counts/status is a hard FAIL.
- This does **not** establish success on a real Mac until an actual strict read-only rerun.

## Next gate

Run exactly this vetted `e3fffcd4` preflight on Mac. Only if all state-equality, fresh-notification and PID checks pass can an independently reviewed loop-only reversible deployment be considered. No automatic `launchctl` restart, Gmail resend, main merge or CA evidence export enablement is allowed in this step.

PR #35 Dashboard layout source is code-merged but not Mac-deployed; it remains separate from this Loop gate.
