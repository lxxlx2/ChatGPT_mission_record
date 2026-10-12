# Frank PR #33: fourth independent review findings — M-11/M-12/L-9 remediation

Date: 2026-10-12 (Bangkok). **This is a separate research-branch implementation**, not the independent reviewer's lost local report or a claimed independent review of new modifications.

## Provenance and frozen Git identity

The user supplied an independent fourth-round review transcript concluding **CONDITIONAL_PASS only for review**, with unresolved **M-11**, **M-12**, **L-9**, **L-10–L-13**. Its external reviewer said the local report was **not committed**, no JSON was produced, and no source patch was pushed. Do **not** claim its files or exact unpublished results are available on GitHub.

Before remediation, the actual connected GitHub source `review/frank-pr33-third-blockers-fix-20261012` HEAD was `7d4c3972b3a2f86c794057f1b915e407763417ab`; official PR #33 original head `48f53a71f692f5dc62f67198f4794e79c45402d2` (merged by another actor at 2026-10-12 04:47:28 UTC, **without the newer research fixes**). Research fix branch: `review/frank-pr33-r4-medium-remediation-20261012` based on exactly `7d4c3972...`.

## What was reproduced

- **M-11 (Medium):** an outbox status not recognized by the current state machine, or a successful status associated with the wrong channel, is deliberately visible in `manual_review_blocked_count`. Original UI incorrectly described the entire group as credential/retry errors; it did not mean that the unknown record is automatically retrying.
- **M-12 (Medium):** putting the **actual old** `delivery_review.py` Git blob `62f5fa85bf41cd95e4a31a373910f81970368ea6` alongside the newer `server.py` makes `mission_control_health()` index nonexistent fields, closing a live HTTP request without a normal response instead of returning an explicit incompatible-version error.
- **L-9:** the database-unavailable UI warning referred to "numbers below" although the current safe rendering no longer displays those stale counters.

The old source is retained as an exact-blob readonly test fixture at `local-agent/tests/research/fixtures/frank_delivery_review_legacy_dbd2dae5.py`, verified against the actual GitHub historical file. New tests use a **real ControlDB SQLite file**, real `DashboardState`, a **live ephemeral 127.0.0.1 ThreadingHTTPServer**, and the actual `app.js` runtime renderer executed under Node.

## Changes in the isolated fix

1. **M-12 (guard before use):** the new server validates the entire delivery-review breakdown contract (the exact `manual_review_manual_only_total_count` legacy field name, nonnegative integer counts, per-channel sums and visible total identity) before putting values into heartbeat output or indexing them. Incompatible/mixed module versions return HTTP 200 with `manual_review_breakdown_available=false`, `manual_review_breakdown_error=DELIVERY_REVIEW_CONTRACT_MISMATCH`, `manual_review_counts_stale=true`. No half-populated fresh counts are emitted, and no private DB/credentials are written.
2. **M-11:** frontend label changed to `运行阻塞或状态异常待核查`, with a tooltip explicitly covering unknown/mismatched states and explaining it **does not mean automatic retry**.
3. **L-9:** database-unavailable text no longer claims nonexistent numeric output follows; it states heartbeat statistics may be stale and unverified values are not displayed.
4. Added actual legacy module fixture, real HTTP, real SQLite, malformed-contract rejection, and actual JS rendering tests. No changes to `delivery.py`, Gmail send/retry state machine, Frank V1 signal thresholds, Writer, trader, production DB or launchd.

An intermediate test run failed because the new guard mistakenly expected `manual_review_manual_only_count` instead of real `manual_review_manual_only_total_count`. **This was a real code defect introduced during repair**, and was corrected. The successful CI below is run **after** this correction. Do not cite the failed initial run as accepted.

## Product pin and real GitHub source proof

Corrected product frozen at `fb4c7318febec899dc01afc08ad1ba29aaa3407c`; GitHub `fetch_file` and `raw.githubusercontent.com` returned identical contents per file.

| Product | Verified Git blob SHA |
| --- | --- |
| `mission_agent/mission_control/server.py` | `8f5124bf46a660fb618371eb113da208b28c775b` |
| `mission_agent/mission_control/static/app.js` | `e3aec8f0e0866cc445406562c10bfb78bb5f28e7` |
| `mission_agent/mission_control/delivery_review.py` (unchanged) | `643fa250e9cdb08cec1c851f769c787fa2279741` |

The research branch's dry-run/deploy script now pins this full Git commit and three target Git blobs, as does its Mac readonly source validator. **Remote GitHub blob match is not real Mac rollout verification.** Rebase/squash/change product content requires repinning and independent validation.

## Actual source-based automated test evidence

- [Isolated code CI #38205251411](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38205251411): **SUCCESS** after pin updates; **82 focused passed**, **1,129 full local-agent tests passed**; compileall, pyflakes, JS syntax checks.
- [Expected RED #38205179258](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38205179258): **SUCCESS only as negative-test proof**. New M-11/M-12 tests run against actual unmodified `7d4c3972...` baseline both failed as expected: real HTTP `RemoteDisconnected` and JS `UNKNOWN_STATE_LABEL_HIDDEN`. The two cases are green against corrected research source. Not a claim that the old product passed.
- [Pinned four-matrix CI #38205314620](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38205314620): **four SUCCESS jobs**, based on exact `main=c730b70965330a4ccf6eaecb0af22f31a28faa69`, `PR31=c50e7e2259e85ce89e14641a4e1e98ca3e4a4bc7`, `PR32=85f1a792dd7d0fbf354c09ac83872887ed301c10`, `fourth-research-fix=35d627b35105cd3c26c52e14ad3991bc2bc0f989`.
  - main + PR32: **1,223 passed**;
  - main + research fix: **1,270 passed**;
  - main + PR32 + research fix: **1,270 passed**;
  - main + PR31 + PR32 + research fix: **1,270 passed**.
  - CI merge trees are ephemeral, generated with read-only checkout permissions; no live agent deployment, Gmail, write to main or production SQLite.

**IMPORTANT CHANGE TO MAIN:** The main baseline `c730b709...` **already contains PR31, PR32, PR33 old commits as ancestors**. GitHub compare: each original PR head was **behind** this main SHA with `ahead_by=0`. GitHub PR metadata nevertheless marks each PR Draft/unmerged. Thus the 1,270 matrix is principally a test of main + new research fix, **not** proof of first-time merger of three independent outstanding PRs. This main state arose independently of these research branch changes. Future integrators must inspect current main and avoid replaying or overwriting existing product files.

## Subsequent verified upstream PR merges — independent of this work

At the beginning of this research work, PR #31, #32 and #33 were still reported Draft/unmerged, although their commits were already ancestors of the tested main branch. During this work, **GitHub PR metadata changed externally**: all three were actually marked merged and closed at **2026-10-12T04:47:28Z**:
- PR31 head `c50e7e2259e85ce89e14641a4e1e98ca3e4a4bc7`, merge_commit_sha `b16dcbcb7afb056b8afe0b80c82cf28e01e79abf`
- PR32 head `85f1a792dd7d0fbf354c09ac83872887ed301c10`, merge_commit_sha `7df82057f3cab7dd85d4c076dd49b86db3e93fb8`
- PR33 head `48f53a71f692f5dc62f67198f4794e79c45402d2`, merge_commit_sha `dafb126e33338523630bb48d4fe838ddd9c7fb95`

None of these merges was executed by this fourth-round research fix. Current main was observed at `472be406a66468b52e9b5b3319c867b0ad7485eb` after these remote merges. **Merged official PR33 is older source**, not the present M-11/M-12 fix branch; the formal PR is closed, so integrating the repaired product now means a **new** carefully reviewed follow-up PR against current main, not simply updating the old PR33 branch. It also must account for previous H-5/H-6/M-8/M-9 work that was only on research branches. Do not assume any user Mac deployment resulted from GitHub merges.

## Residual issues and release gate

- User-provided external reviewer classified the previous version as CONDITIONAL_PASS, but this **new code revision has not received another independent outside-AI review**. Its automated research validation is PASS; **production release is still BLOCK**.
- Source-modification conflict after SIGKILL/power outage still requires backup-based recovery. New guard prevents crashing HTTP in the examined mixed server/legacy classifier scenario; it does not make a mixed deployment fully operable or self-healing.
- **L-10:** readonly diagnostic `dashboard_hidden_nonsuccess_rows` name effectively refers to unrecognized status rather than all invisible non-success rows; label could be clarified in a later scoped revision.
- **L-11:** deployment validator may retry some unknown-status errors until the bound instead of immediately aborting; low risk/slow fail, not yet separately reproduced for this latest fix.
- **L-12:** `PENDING` queue display is visibility-only and does not split fresh vs aged queue; never claim all queued items are expired.
- **L-13:** missing table may be retried before hard failure; fail closed but slow.
- No actual Mac dry-run or native browser observation of the new product, no launchctl recovery test on user Mac, no independent Gmail Sent mailbox inspection, no real Google OAuth, and no SIGKILL-proof automatic rollback. Historic actual Mac readonly results showed a **LEGACY** backend and 34 outbox records including 16 `local/COMMAND_ACCEPTED`; it is **not** evidence of this latest product being installed.

**Decision:** `RESEARCH_CI=PASS_1129`; `FOUR_MATRIX=PASS_1270`; `PRE_FIX_EXPECTED_RED=PASS`; `RAW_PRODUCT_BLOBS=VERIFIED`; `EXTERNAL_INDEPENDENT_REVIEW_NEW_HEAD=NOT_DONE`; `FORMAL_PR33_INTEGRATION=NO_BY_THIS_WORK`; `MAIN_MODIFIED_BY_THIS_WORK=NO`; `MAC_DEPLOY=NO`; `LIVE_GMAIL=NO`; `PRODUCTION_TRADING=NO_GO`. Continue review/integration only in an explicitly approved release process.
