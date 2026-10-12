# Frank Loop second Mac read-only preflight — RPC file blocker (2026-10-12)

## Evidence

The user uploaded `frank-loop-upgrade-preflight-20261012-132504.zip` (SHA256 `5993888fd9341c15b294e4710f988f44de72342e0555322243e813f96e32282b`). It contains only `preflight.json`, not any RPC credentials or SQLite data. Timestamp: `2026-10-12T06:25:04.275283+00:00`.

Pinned deployment release target: `6a5b7e8a533f99c871e31f9674329fcb4f929cc2`.

## Actual sanitized machine output

- 9 `PASS` checks, 2 `FAIL` checks, error stage `AUTHORIZATION:RuntimeError`.
- `RUNNERS_PRESENT=PASS`
- `CURRENT_DASHBOARD_IS_MERGED_RELEASE=PASS`
- `DASHBOARD_SOURCE_PINNED_PR34=PASS`
- `RUNNER_MODE_POLICY_UNCHANGED=PASS`
- `RUNNER_POINTS_TO_CONTROL_POINTER=PASS`
- `EXISTING_DB_AND_VENV=PASS`
- `LOOP_AND_DASHBOARD_RUNNING=PASS`
- `POLICY_JSON_PRESENT=PASS`
- `APPROVED_SHA256_FILE_PRESENT=PASS`
- **`SOLANA_RPC_FILE_PRESENT=FAIL`**
- **`APPROVED_POLICY_FILES=FAIL`**

This preflight stopped before actual policy hash validation, mail-credential permission check, SQLite snapshot migration, pending mail classification and any restart or deployment.

The report explicitly states:
`new_mission_loop_deployed=false`, `existing_loop_restarted_by_this_script=false`, `existing_dashboard_restarted_by_this_script=false`, `gmail_send_attempted_by_this_script=false`, `production_database_write_attempted=false`, and `github_push_attempted=false`.

## Operational inference and limits

The currently executing loop and dashboard were both present when this check was made, but a saved runner-dependent RPC file was not readable as a regular file at the path referenced by the **Loop** runner. Do not conflate this with loss of the active in-memory Solana RPC connection, nor assert credential-file deletion timing.

The merged installer code demonstrates that `mission-loop.sh` reads `SOLANA_RPC_URLS` from its `RPC_FILE` before launching its executable. Therefore do **not** restart the active Loop or repeat a general installer while that file is missing.

There are two plausible causes requiring read-only discrimination: Loop and Dashboard reference *different* RPC file paths, or both reference the same missing file (or the expected file was moved/removed). This report has no evidence to choose between them.

## Next step

A separate, read-only `frank_rpc_file_readonly_diagnose_20261012.py` has been placed on the same operations branch to compare named runner references, the canonical application-support file and bounded alternative file locations. It prints only statuses, never RPC URL values, and creates a sanitized diagnostics ZIP. It does **not** generate, copy, repair, or delete any credential, modify approved policy, restart services or query live RPC.

After the actual Mac path diagnosis, use a separate secure corrective procedure appropriate to the verified cause and then rerun the full Loop preflight. Do not bypass the `APPROVED_POLICY_FILES` hard gate.
