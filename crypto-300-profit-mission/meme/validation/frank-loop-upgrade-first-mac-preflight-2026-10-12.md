# Frank live Mission Loop preflight — first Mac result, 2026-10-12

## User-uploaded evidence and verified contents

Upload: `frank-loop-upgrade-preflight-20261012-131532.zip`, opened directly from the conversation attachment. It contains exactly one `preflight.json` and no production DB bytes or credentials. Recorded time: `2026-10-12T06:15:32.971853+00:00`.

Target pinned merge commit: `6a5b7e8a533f99c871e31f9674329fcb4f929cc2`.

**Result: STOP / NOT AUTHORIZED TO RESTART OR DEPLOY THE LOOP.**

### Machine-generated flags

```text
RUNNERS_PRESENT=PASS
CURRENT_DASHBOARD_IS_MERGED_RELEASE=PASS
DASHBOARD_SOURCE_PINNED_PR34=PASS
RUNNER_MODE_POLICY_UNCHANGED=PASS
RUNNER_POINTS_TO_CONTROL_POINTER=PASS
EXISTING_DB_AND_VENV=PASS
LOOP_AND_DASHBOARD_RUNNING=PASS
APPROVED_POLICY_FILES=FAIL
failure_stage_type=AUTHORIZATION:RuntimeError
new_mission_loop_deployed=false
existing_loop_restarted_by_this_script=false
existing_dashboard_restarted_by_this_script=false
gmail_send_attempted_by_this_script=false
production_database_write_attempted=false
github_push_attempted=false
```

The `APPROVED_POLICY_FILES` predicate initially required **all three** to exist:
`POLICY`, `APPROVED_HASH_FILE`, `RPC_FILE`, as extracted from the installed `mission-loop.sh` via read-only parsing. The original report does not distinguish which path(s) are missing.

Because this check failed before the `APPROVED_POLICY_IDENTITY`, read-only SQLite snapshots, or pending notification classification phases, **no claims are made** about policy SHA approval, Gmail credential readiness, queued historical notifications, or database schema compatibility from this upload.

## Response / code improvement

The strictly read-only preflight on branch `ops/frank-mission-loop-readonly-preflight-20261012` was updated to emit three separate presence flags and a non-secret `missing_authorization_artifacts` list in the sanitized JSON report while keeping the same aggregate **hard FAIL** if anything required is missing. This has no auto-repair, credential creation, policy auto-approval, Loop restart, or DB write path.

Next step: rerun the new read-only diagnostic to identify the missing artifact; fix only the confirmed configuration problem after separate safe review and repeat the full preflight. Do not blindly regenerate an approved digest from whatever policy happens to be present, or bypass the authorization test.

**Production Loop running at the time of original preflight** is supported by `LOOP_AND_DASHBOARD_RUNNING=PASS`; continued future liveness is not established.
