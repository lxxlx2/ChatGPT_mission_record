# Frank PR #33 — third independent BLOCK findings: isolated research remediation

**Date:** 2026-10-12 (Bangkok)
**Official PR:** [#33](https://github.com/lxxlx2/ChatGPT_mission_record/pull/33), unchanged Draft head `48f53a71f692f5dc62f67198f4794e79c45402d2`.
**Reviewer source HEAD:** `ae854ef8653cb94d6f804b04c83df66fb14cddef` on `review/frank-pr33-second-round-fix-20261012`.
**Implementation branch:** `review/frank-pr33-third-blockers-fix-20261012`, based on exactly `ae854ef...`.
**Context:** The user provided a third independent reviewer report whose unpushed patch `b1ca2824` and evidence folder were not available as files to this implementation. This independently reimplements its H-5/M-8 fixes and extends them to fix H-6/M-9/M-10. It is **not a byte-for-byte import of reviewer patch** and **not an independent fourth-AI review** of this implementation.

## Original findings and disposition

| Finding | Severity | Actual research code disposition |
|---|---|---|
| H-5: real Mac `local/COMMAND_ACCEPTED=16` causes deploy validator to fail incorrectly | High | **FIXED in research branch:** channel-appropriate successful status pairs are excluded from the independent deployment SQL unknown-state detector. Verified against actual SQLite fixtures (not live Mac deployment). |
| H-6: stale `PENDING` outbox rows not shown by Dashboard or either validator | High | **FIXED in research branch:** all `PENDING` rows, including old/unsent ones, appear in new separate `manual_review_queued_*` bucket. Server, probe, deployment independent SQL and UI agree. No delivery state change or retries are authorized. Fresh queued rows are also included; this is visibility, **not proof every PENDING is expired**. |
| M-8: channel-independent status whitelist accepts `gmail/COMMAND_ACCEPTED`, `local/SENT_VERIFIED` | Medium | **FIXED:** only Gmail `SENT_VERIFIED` / `DRY_RUN_AUDIT` and local `COMMAND_ACCEPTED` / `DRY_RUN_AUDIT` are excluded as known successes. Unknown or channel-mismatched statuses remain visible as blocked in server, and conservatively reject the independent deploy/probe validation. |
| M-9: new UI with legacy backend labels historical 15 MANUAL_REVIEW as actionable 15 | Medium | **FIXED:** a missing new contract never derives `actionable` from legacy total; it shows explicit unavailable/mismatched-contract warning. JS rendering function is exercised with real source, not just strings. |
| M-10: transient SQLite WAL busy causes immediate deploy verification failure/rollback | Medium | **RETRY SAFE:** `verify_dashboard()` now retries `sqlite3.OperationalError` and re-reads SQLite on every attempt. Failure after bounded retries still blocks deployment. |

No changes to `mission_agent/mission_control/delivery.py`, Gmail sending state machine, Frank V1, strategy, trading, production SQLite, or LaunchAgent.

## Frozen product, immutability, and remote proof

Corrected **product** commit is **`4fe1145aa97b6cc4a3ed27b8e2e39d035fc80fb0`**. Deployment script `COMMIT` and `PATCHES[*].target` point to this immutable commit and these Git blobs; the one-shot Mac readonly probe `PINNED[*].target` also matches:

| Product file | Git blob SHA | Real remote readback |
|---|---|---|
| `mission_control/server.py` | `09a0b66b9fc8ea6f8bf0f8137a6b667ad57f24fd` | raw.githubusercontent.com content matched GitHub file content |
| `mission_control/static/app.js` | `ade294d383c4b2acc172d257bf6e22051fc43075` | matched |
| `mission_control/delivery_review.py` | `643fa250e9cdb08cec1c851f769c787fa2279741` | matched |

Old deployment allowlisted baselines and byte restore remain unchanged. The actual raw GET validation is **remote-source evidence, not a Mac dry-run, launchctl rollout, or production readback**. If product is rebased/squashed after this version, repin/revalidate before deploy.

## Independent actual CI

- [Focused and full isolated code CI 38189089104](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38189089104): **SUCCESS** on tested source `884ed7cd5b4ba6b480e9ad8dfac908b8e1facf42`:
  - **76 focused tests passed**; includes real SQLite, channel/status pair proof, actual `app.js` `renderRuntime` JS execution for new and mixed-version backends, real live loopback `Handler` HTTP and independent SQLite/dashboard validator parity on old `PENDING`, rollback/signal fault injection, SQLite lock retry;
  - **1,123 entire local-agent tests passed**;
  - Python compileall/pyflakes and Node syntax checks passed.
- [Red baseline run 38189268014](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38189268014): **SUCCESS as expected-red proof** on baseline product `ae854ef8653cb94d6f804b04c83df66fb14cddef`: new `test_old_pending_and_manual_history_do_not_double_count` failed with actual missing `manual_review_queued_count`; the actual JS runtime renderer M9 test returned CalledProcessError on old source; workflow required two failing cases and exited success only after seeing expected-red results. The test was green on repaired source. The traceback does not independently prove which JS assertion caused the old-source CalledProcessError; do not overstate its attribution.
- [Latest pinned four-matrix integration CI 38189178969](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38189178969): **all four SUCCESS**, based on exactly pinned:
  - main base `380a2d5aa2310c6f41915fdc1ed8ad68686bfc7a`
  - PR31 `c50e7e2259e85ce89e14641a4e1e98ca3e4a4bc7`
  - PR32 `85f1a792dd7d0fbf354c09ac83872887ed301c10`
  - research PR33 `884ed7cd5b4ba6b480e9ad8dfac908b8e1facf42`
  - main+PR32: **1,055 passed**;
  - main+PR33 fixed: **1,123 passed**;
  - main+PR32+PR33 fixed: **1,131 passed**;
  - main+PR31+PR32+PR33 fixed: **1,262 passed**.

CI merge trees exist only on ephemeral runners. PR32 and PR33 still have the previously documented duplicate workflow file add/add conflict, resolved only for that exact path in the matrix. No runtime-code conflict was auto-overridden; **main was not merged or pushed**.

## Why existing real Mac evidence is not a release PASS

The last real user Mac readonly DB observation showed 34 outbox entries: 15 Gmail MANUAL_REVIEW stale-before-send, 1 Gmail SENT_VERIFIED (DB state only), 1 Gmail DRY_RUN_AUDIT, 16 local COMMAND_ACCEPTED (successful macOS command returns only), 1 local DRY_RUN_AUDIT. There were 0 known SENDING/SENT_UNVERIFIED and 0 unknown status rows then; this does **not** establish actual Gmail Sent mail-head readback or future PENDING counts.

Mac still had **LEGACY** three-source Dashboard with missing new HTTP contract fields. The new research product is **NOT INSTALLED ON MAC**. A real Mac browser and actual `launchctl` success/rollback have not been run against corrected code. No live actual `--apply` was executed. User did not authorize any deployment or Gmail send.

## Decision and next gates

**Research-level automated code testing: PASS** for the pinned SHA combinations above. **Production gate: BLOCK**.

1. Another independent AI should review these exact new source/script/test SHAs, specifically PENDING freshness vs stale labeling, unknown status-pair fail-close, count-equivalence and rollback safety. This implementation is not a substitute for external review.
2. Under explicit user authorization, apply reviewed fixes to the formal PR33 branch, resolve duplicate workflow path conflict, then run **new** CI at actual final PR HEAD; do not treat ephemeral merge SHA as persisted or currently running on Mac.
3. A new user Mac **read-only** dry-run/acceptance must confirm actual local old source/DB/HTTP state. Only then consider a separately authorized manual Dashboard-only upgrade, real `launchctl` health and browser smoke test.
4. Actual independent Gmail Sent readback, malformed timestamp escalation policy, SIGKILL/power failure, filesystem fsync and partial ENOSPC recovery remain unresolved or outside scope. Unconfirmed older-than-600s count is not claimed; all PENDING are shown regardless of age.

**Flags:** `THIRD_RESEARCH_H6_M9_M8_H5=CI_PASS`; `REAL_GITHUB_BLOB_PIN=VERIFIED`; `JOINT_MERGE_TREE_CI=PASS_1262`; `OTHER_AI_NEW_HEAD_REVIEW=NOT_DONE`; `OFFICIAL_PR33_HEAD=UNCHANGED`; `MAC_PRODUCT_DEPLOYED=NO`; `MERGE_MAIN=NO`; `LIVE_GMAIL_SEND=NO`; `PRODUCTION_TRADING=NO_GO`.
