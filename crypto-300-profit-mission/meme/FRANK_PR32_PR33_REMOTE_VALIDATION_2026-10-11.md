# Frank Gmail PR #32 / Dashboard PR #33: independent remote Git acceptance (2026-10-11 Bangkok)

## Authority and limits

This is a new implementation against the actual remote PR heads, based on the external review text supplied by the user. Its commits are **not** bit-for-bit copies of the independent reviewer's unpushed `6a581012`, `83356135` or `56cb35a6` patches. No original patch was attached/read by the implementer. No PR was merged; no Mac process or production database was touched; no real Gmail send or OAuth consent took place. `PRODUCTION_TRADING=NO_GO`.

## PR #32 — OAuth helper

Branch `fix/frank-gmail-oauth-recovery-20261011`, original HEAD `e13c46b506016c80d90873def1b191ac838ee43b`.

Actual remotely persisted fixes:
- `a9827cf9788465467f3704ab807b098818ef1236`: abort if recipient missing before browser/OAuth token exchange; exact Gmail profile match, unique randomly suffixed 0600 backup; no stored short-lived access token, including removing a legacy `token` field in the new file.
- `3061ca847483c108c1542907dd588d61fcde8874`: tests for fail-closed missing recipient, repeated same-second backups, and no persisted access bearer.
- GitHub Actions [38155283993](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38155283993), HEAD `85f1a792dd7d0fbf354c09ac83872887ed301c10`: **SUCCESS** with **8 focused tests passed** and **1,055 full local-agent tests passed**, `pyflakes` and syntax gate successful.

Outstanding: independent report's **14/14 local fake-Google E2E is not a GitHub-CI reproduction in this new branch**. No actual Google OAuth reauthorization test or Sent readback; old refresh-token/client-secret backup accumulation policy remains unchanged.

## PR #33 — review UI and safety-only deployment

Branch `fix/frank-dashboard-review-breakdown-20261011`, original HEAD `c325aba57761264adb17369e9ac77ce9e0ad80ad`.

Source changes:
- `delivery_review.py`: show `SENDING` / `SENT_UNVERIFIED` separately in `pending`; unknown channels become reviewable `other` rather than silently discarded.
- `server.py`: read pending and manual statuses through real read-only SQL and add `manual_review_pending_*` plus `manual_review_visible_total_count`; legacy `manual_review_total_count` remains MANUAL_REVIEW-only, **not** including pending; DB failure clearly emits `manual_review_breakdown_error`.
- `app.js`: explicit Chinese `投递结果待确认` line and legacy/fallback meaning. No send retry or state mutation was added.
- 10 classification unit tests plus **7 real ControlDB/SQLite integration tests**. The whole product and tests pinned as **commit A `1014c14b4df00757593f7ca4de8cedae0f09afaa`**.

Manual-only deployment script:
- `scripts/deploy_frank_dashboard_review_badge.py` uses immutable **commit A** and verifies the three actual product Git blobs; supports only complete verified `baseline`, `legacy` and `target` source sets; rejects mixed partial installs.
- Target blobs from actual GitHub remote readback: `server.py=9dcf26fe03dadd43f75c401d38ba0e412101be41`, `static/app.js=f7880daa425d0a286de0c16836794c62965454ed`, `delivery_review.py=afa98794136f48762f15fc3cd627866c7f90386a`.
- An independent connected GitHub raw URL request for every file at commit A succeeded, and each returned content matched `fetch_file` at that SHA exactly. **This is remote file verification, NOT a Mac dry run.**
- Pre-apply `node --check` of downloaded JS and Python compilation; dry-run default; existing pinned bytes backups preserved locally; `--apply` explicitly needed for mutation; byte-exact rollback, Dashboard restart, HTTP check after rollback; idempotent already-installed target.
- `verify_dashboard()` compares Dashboard JSON counts against an independent `sqlite3 mode=ro` query including the 3 pending statuses and category counts, not `old+active=total` tautology.
- Tests use pinned repo Git blobs, fake raw downloads, no launchctl, and a real local ephemeral HTTP service backed by actual `DashboardState` plus ControlDB. It accepts new server counts and rejects legacy/contradictory responses.
- Deployment script first committed at `d0f9a8711f594be5ae4e901f7e560841715ffcf5`; static clean follow-up `8c500d6c60d5c17946f54473331b64e2c87f11f8`. **No deployment was invoked.**

Actual [GitHub Actions 38155665229](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38155665229) on head `520475337226965acbdb8d6758bd782627dde50f`: **SUCCESS**, **29 focused tests passed** (10 classification + 7 SQLite integration + 12 deployment tests), **1,076 full local-agent tests passed**. Static Python, `pyflakes`, Node JS syntax passed.

## Release decision: CONDITIONAL / NOT DEPLOYED

- Branch CI PASS and real GitHub product pin verified.
- **No GitHub PR merged to main**, and current Dashboard on Mac may still be the previously deployed legacy version; not remotely checked.
- Pending sends are made visible, never automatically re-sent. Malformed timestamp remains visible in pending and does **not** auto-promote to MANUAL_REVIEW. Changing the Gmail delivery state machine requires explicit user authorization.
- Real Google Gmail OAuth/headers/Sent-readback, 14-case independent fake-Google E2E, true Mac `launchctl` success/rollback and native-browser UI rendering **NOT VERIFIED**.
- Cross-PR integration with current moving PR #31 was **not independently rerun at this new HEAD** (the supplied local 1,186-pass merge-tree result remains an attributed prior report, not this GitHub CI).
- Deployment requires independent final review plus Mac read-only dry-run and user approval. No real Gmail, production writer, policy thresholds, trading keys, schedules, background agents or live delivery were changed.
