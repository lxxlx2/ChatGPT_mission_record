# Frank Dashboard — fifth independent review M-13 remediation and immutable verification

Date: 2026-10-12 (Asia/Bangkok)

## Provenance / boundaries

The user supplied Claude's fifth independent review transcript as evidence. Reviewer scrutinized remote source HEAD `10b98ee10d5d84ea187041821cd9fe0d977ecf09`, reported incomplete local-only proposed M-13 patch `581f559a` with **NOT_PUSHED**, and documented that neither the latest production pin nor full-suite test had been finished. That private Claude branch/patch was not accessible from GitHub and **was not copied**. A new, independently implemented correction was committed to remote `review/frank-pr33-r5-classifier-guard-remediation-20261012`, starting from the **exact review baseline** `10b98ee10d5d84ea187041821cd9fe0d977ecf09`.

No modification to main or historical merged PR31/32/33 was performed by this work. No Mac Dashboard deployment, launchctl operation, email auth/send, production SQLite mutation, Frank V1 policy/Writer/signal change, or trading operation was performed. Full current global Mission authority is in `crypto-300-profit-mission/MISSION_SPEC.md`.

## Actual M-13 defect and isolated repair

**Medium — M-13**: In review HEAD, `DashboardState.mission_control_health()` invoked `summarize_manual_reviews(rows)` **outside** its database exception handler and before the subsequent response contract guard. If the classifier itself raised `KeyError`, `ValueError`, or `TypeError`, the production HTTP request ended in `RemoteDisconnected`. The normal dashboard-wide fetch may surface a general offline banner but candidate/decision panels in the same Promise.all batch stop refreshing. This is a real absence of the promised explicit fail-closed status and was independently reproduced below.

Minimal fix: wrap **only the classifier invocation** in `try/except Exception` (intentionally not `BaseException`). Return `manual_review_breakdown_available=false`, `manual_review_breakdown_error=DELIVERY_REVIEW_CLASSIFIER_ERROR`, `manual_review_counts_stale=true`. Do not merge any speculative fresh count fields, emit exception contents/PII, change outbox/Gmail state, or send notifications. A stale heartbeat `manual_review_total_count` may still exist in HTTP payload and **must be interpreted using `counts_stale=true`**, never as independently verified live information. This fix does **not** guarantee recovery if the Python module cannot import or the service cannot start after a SIGKILL/missing dependency.

Product change committed **before** pin/script updates:
- Immutable product Git commit: **`8ed805e90026397ae1b67f35a3a03ca407226106`**
- `mission_control/server.py` Git blob: `916be9bc6862c7fa9d602c6d1dfce26b5af53968`
- `mission_control/static/app.js` Git blob (unchanged): `e3aec8f0e0866cc445406562c10bfb78bb5f28e7`
- `mission_control/delivery_review.py` Git blob (unchanged): `643fa250e9cdb08cec1c851f769c787fa2279741`

All three GitHub raw URL contents, at **exact** `8ed805e9...` ref, matched independent GitHub `fetch_file` readback, and the two existing operations scripts were updated to match the new `server.py` target SHA. The deploy script's `COMMIT` pin points to that immutable product commit. Research branch script pin consistency does **not** prove the later main merge tree has matching product blobs.

## Actual tests: independent red and corrected green

New `tests/research/test_frank_pr33_r5_classifier_exception.py` uses real `ControlDB` SQLite, `DashboardState`, and an ephemeral **live** `ThreadingHTTPServer` on `127.0.0.1`. It checks classifier `KeyError`, `ValueError`, `TypeError`; a normal classifier control; no outbox mutation; no private exception-string leakage; correct stale/unavailable flags.

1. **Pre-fix true RED:** [GitHub CI run 38212141503](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38212141503) concluded SUCCESS **only because it demanded expected failures** when new tests ran against genuine unmodified review HEAD `10b98ee1...`. Two real loopback HTTP failure variants emitted `http.client.RemoteDisconnected`, while the normal positive-control case passed: **2 failed, 1 passed**, followed by `M13_OLD_CODE_RED_TWO_LIVE_HTTP_FAILURES=PASS`.
2. **Corrected isolated GREEN:** [CI run 38212099772](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38212099772) on research source snapshot `0b6a77c05c14760c11a10239b48c9b90b9e60b03`: **88 focused tests passed** and **1,135 complete local-agent tests passed**. Python compileall and pyflakes, Node syntax checks, and real Git replay all succeeded. These are actual remote CI logs, not projections. No tests changed product output to fake a success.
3. **Pinned existing-main compatibility:** [CI run 38212349915](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38212349915) created two isolated ephemeral Git trees against precise `BASE_SHA=8aca0b3ff558e17ca1cbce13ceba27aaf9fad8d4` and `R5_SHA=a64d4c2010091574ec6280e140cfa6d06369e743`. Both Git trees merged without a source conflict, passed syntax/lint/Node checks and real replay:
   - main baseline: **1,223 full tests passed**.
   - main + R5: **1,276 full tests passed**.
   No git merge commit was pushed, no PR was merged, and no main file was modified by this pipeline. The CI merge commit was local to the ephemeral runner.

## Critical integration pin caveat

**No automatic deployment based on ephemeral merge.** The Git merge-tree product blob hashes after main+R5 integration were:

| Product | `8ed805e9` research target | Actual ephemeral main+R5 merge product blob |
| --- | --- | --- |
| `server.py` | `916be9bc6862c7fa9d602c6d1dfce26b5af53968` | **`1057800fa3d515177c8a820de26e2c60737e8f9a`** |
| `static/app.js` | `e3aec8f0e0866cc445406562c10bfb78bb5f28e7` | **`14c21487bab0234fc45270dd759b641d4f9f05e3`** |
| `delivery_review.py` | `643fa250e9cdb08cec1c851f769c787fa2279741` | `643fa250e9cdb08cec1c851f769c787fa2279741` |

The existing main baseline itself had `server.py=f2976007abca4934dc9766b75ca3667635930f89`, `static/app.js=61e37dfe5ce74e1a11c8a70b72624e7b2de417eb`, `delivery_review.py=afa98794136f48762f15fc3cd627866c7f90386a`. Main already contains the old (previously merged) PR31/32/33 source and has materially diverged from the hardened research product.

**Before a follow-up release PR against latest main:** build a real persisted integration branch/commit retaining main's unrelated changes and UI provenance; compute its new product blobs; repin the deployment and readonly scripts to **that exact integration product commit and its blob SHA**; independently fetch its remote GitHub raw contents; rerun all CI against the resulting immutable SHA; obtain another independent review of the final integrated diff and explicit user authorization before any Mac install. No GitHub raw URL exists for the ephemeral merged product commit because it was not pushed.

## Residual and release decision

- Source-level M-13: **FIXED in remote research branch**; H-1/H-5/H-6/M-8/M-9/M-10/M-11/M-12/L-9 tests remained green in the full isolated and merged suites. This is automated regression evidence, not a fresh independent source review of the resulting R5 HEAD.
- Historical Mac readonly data from the user had 34 outbox records (15 Gmail MANUAL_REVIEW, 1 Gmail SENT_VERIFIED as local DB status, 1 Gmail DRY_RUN_AUDIT, 16 local COMMAND_ACCEPTED, 1 local DRY_RUN_AUDIT). **Mac was LEGACY** and this is not evidence that any R5 code is deployed, any independent Gmail Sent readback occurred or any actual pending count is current.
- SIGKILL, power loss, incomplete recovery, import-time syntax error, real launchctl/GUI behavior, independent Gmail Sent mailbox readback, plus current main's still-unfixed hardening remain outside this isolated research proof.
- As of the pinned merge CI, production compatibility is **BLOCKED by final-product pin mismatch**. Do not modify live Mac source, no merge main, no auto-email resend, no production trades.
- This report itself, and its associated JSON evidence, were committed to the isolated branch and remote-readback verified. **`R5_RESEARCH_CI=PASS_1135`**, **`PINNED_MAIN_INTEGRATION_CI=PASS_1276`**, **`FINAL_MAIN_PRODUCT_DEPLOY_PIN=NOT_READY`**, **`EXTERNAL_INDEPENDENT_REVIEW_NEW_MERGED_HEAD=NOT_DONE`**, **`MAC_PRODUCTION_DEPLOY=NO`**, **`PRODUCTION_TRADING=NO_GO`**.
