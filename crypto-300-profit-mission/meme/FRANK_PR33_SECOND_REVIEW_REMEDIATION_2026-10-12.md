# Frank PR #33 — second independent BLOCK review: research remediation (2026-10-12 Bangkok)

## Review provenance / no silent promotion

The user supplied an **independent Claude Haiku 5.5 second-round review** of PR #33 remote head `48f53a71f692f5dc62f67198f4794e79c45402d2`, verdict **BLOCK** for terminal Gmail outcome invisibility, false-positive readonly acceptance, interrupted deploy without rollback, and incomplete rollback on disk write failure. The reviewing AI separately reported local commits `69c2e8b9`, `573d5d07`, `6906a5e2` and patch files in its own environment. **Those commits and patches were not pushed or provided as readable files for this implementation.** This is a separate, code-reviewed reimplementation based on the supplied report, not an exact copy and **not a new independent other-AI review** of the resulting code.

Actual source branch is `review/frank-pr33-second-round-fix-20261012`, created from exactly `48f53a71...`. No changes pushed to the formal PR #33 head, main or user's Mac.

## Source behavior repaired

1. **H-1**: `delivery_review.py`, read-only `server.py` SQL, `app.js`: `PERMANENT_ERROR` including `MULTIPLE_SENT_IDENTITIES_REQUIRE_REVIEW` / `SENT_IDENTITY_OR_CONTENT_MISMATCH` now appears in actionable review. `CREDENTIAL_BLOCKED`, `RETRYABLE_ERROR`, `RETRY_PENDING` appear in a separate blocking group. The previous `manual_review_total_count` / gmail/local legacy fields still count only true `MANUAL_REVIEW`, not permanent errors or pending sends. All three presentation classes use separate status counts; no retry state or Gmail delivery logic changes.
2. **H-2**: `scripts/frank_dashboard_readonly_acceptance.py`: readonly SQLite aggregation now sees all seven audited status categories and independently checks unknown/non-success state rows. `dashboard_hidden_nonsuccess_rows>0` causes `BLOCKED_DASHBOARD_HIDES_NONSUCCESS_ROWS` with nonzero exit; missing server fields and numerical disagreements have distinct `http_missing_count_fields` and `http_mismatched_count_fields`. Source/version and local HTTP must still match to accept. Database access uses `mode=ro` + `query_only=ON`. A successful count check is explicitly NOT browser/UI release or Gmail Sent verification.
3. **H-3**: deployment install now catches `BaseException` while replacing files, handles SIGTERM/SIGHUP with a temporary handler converting to a rollback-capable exception, and restores original handlers afterward. KeyboardInterrupt and simulated SIGTERM fault injections verify byte-for-byte source rollback. **SIGKILL/power outage remain uncapturable**, and backup name is announced before first modification for manual recovery.
4. **H-4 / M-7**: rollback restores each source independently, collecting failed write errors instead of bailing out on the first ENOSPC. Dashboard restart and byte/HTTP readback are independently attempted after restore. An incomplete rollback is explicitly `ROLLBACK_INCOMPLETE=... MANUAL_ACTION_REQUIRED BACKUP_NAME=...`, never reported as success. Actual disk exhaustion cannot be promised as automatically recoverable.
5. **M-1**: `verify_dashboard` reloads the actual readonly SQLite counts **inside every retry**, avoiding false mismatch after legitimate Mission Loop updates.
6. **M-2/M-3/M-5**: JS now shows runtime blockers, backend schema incompatibility, and heartbeat-stale count warnings when the database or new API is unavailable.
7. **L-1/L-2**: backup files are uniquely named, created mode 0600 and O_EXCL. macOS-compatible nonblocking `fcntl.flock` allows only one explicit `--apply` at a time. Every commit/download hash/permission remains pinned and checked.

## Immutable revised product pin

Actual corrected product files were committed **before** the deployment script was updated. Pin: `1e8fb2a5c89ae8cafba5d07283482b8858583b33`.

| GitHub source file | independently read Git blob SHA | real raw.githubusercontent GET |
| --- | --- | --- |
| `mission_control/server.py` | `03dce99acd5fa3844444f588eb2965bb4a419a75` | byte-equal to GitHub file readback |
| `mission_control/static/app.js` | `8c8071babf34c4174b90a6699e34565575f4b7a8` | byte-equal to GitHub file readback |
| `mission_control/delivery_review.py` | `0f2032b8027f17a7e27da55d92468bbe524bbc14` | byte-equal to GitHub file readback |

The manual deploy tool's `COMMIT` and `PATCHES[*].target` and readonly Mac probe's `PINNED[*].target` use this new revision. All previous baseline/legacy sources remain in the strict allowlist, and mixed product versions reject before write. **Raw URL proof is a remote source proof, not a real Mac dry-run.**

## Actually executed CI

- [Isolated research fix run 38160485193](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38160485193): **SUCCESS**, 52 focused tests, **1,099 complete local-agent tests**, pyflakes, compileall, `node --check`, and full Git evidence replay. Tested code/head `b8b50d0624b5f746ee527e6b49b0a4aa8ac5814a`.
- [Pinned four-matrix run 38160650858](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38160650858): four ephemeral merge-tree jobs all **SUCCESS** against main baseline `cdff373be343d5e61f21c17329aeaeca32651529`, PR31 `c50e7e2259e85ce89e14641a4e1e98ca3e4a4bc7`, PR32 `85f1a792dd7d0fbf354c09ac83872887ed301c10`, PR33 research fix `b8b50d0624b5f746ee527e6b49b0a4aa8ac5814a`.
  - PR32: **1,055 passed**, ephemeral SHA `01148f4ec76d159630ac33f44f0f14411c840bb4`.
  - PR33 research fix: **1,099 passed**, ephemeral SHA `9222e13b9161d94169ffefcda2fdaca4724d481d`.
  - PR32+PR33 fix: **1,107 passed**, ephemeral SHA `554cb77b040ea78bceb9dad21888f0d6f8e49115`.
  - PR31+PR32+PR33 fix: **1,238 passed**, ephemeral SHA `8a8926af2db2497c384a0fe86bf687ca0b636fc4`.
- Tests include current repair-specific real `ControlDB` SQLite checks for PERMANENT_ERROR and blocked states, unknown category loss prevention, no-outbox-write assertions, `KeyboardInterrupt`, injected SIGTERM, ENOSPC partial rollback disclosure, fresh SQLite re-read, simulated second concurrent deploy refusal, and source/account/browser contract checks.

## Limitations and release gate

- **Neither the official PR #33 branch nor main is changed by this fix.** The changes are remote only on the isolated `review/...` branch. The ephemeral matrix merge commits have not been pushed.
- Current user Mac remains **LEGACY**, per prior actual read-only run: 15 stale-before-send MANUAL_REVIEW, 0 SENDING/SENT_UNVERIFIED pending at that time. That previous readonly probe did **not** check PERMANENT_ERROR or blocked statuses. Their **current actual counts are UNKNOWN until a NEW Mac readonly probe is run**.
- **No Mac deploy, no launchctl restart, no actual GitHub-origin --apply dry-run on user's Mac, no native browser visual smoke test, and no real Gmail Sent readback**.
- No source or sqlite state was changed in frozen Frank V1, Gmail `delivery.py`, live trading, Mission Loop, strategy thresholds or OAuth secrets.
- Reviewer candidate `6906a5e2` had CONDITIONAL_PASS *in its local environment*, but this separate reconstruction **requires another independent review against its actual new HEAD**. Current release remains **BLOCK**, not production PASS.
- SIGKILL, disk write failure mid-rollback, backup file retention, weak no-Git/Mac SSH availability, and malformed Gmail timestamp escalation remain clearly disclosed.
- The user did **not** authorize Mac production deployment, real Gmail sending, changes to the Gmail state machine, or merge to main. Leave all disabled.

**Research delivery:** `RESEARCH_CODE_CI=PASS_1099`, `LATEST_PINNED_MATRIX=PASS_1238`, `REAL_GITHUB_TARGET_RAW=VERIFIED`, `OTHER_AI_REVIEW_NEW_HEAD=NOT_DONE`, `MAC_READONLY_TERMINAL_STATUS_SAMPLING=NOT_DONE`, `MERGE_MAIN=NO`, `OFFICIAL_PR33_HEAD_UNCHANGED`, `MAC_DEPLOY=NO`, `PRODUCTION_TRADING=NO_GO`.
