# Frank PR #31 + #32 + #33: pinned four-combination integration acceptance

Date: 2026-10-11 (Asia/Bangkok)

## Scope and precise source provenance

This report records **actual GitHub Actions ephemeral Git merge-tree tests**, not a production release and not an independent other-AI security review. CI checkout has `persist-credentials: false`, `contents: read`; all merge commits are formed on disposable runner branches and are not pushed.

- Baseline main at test start: `383dddf517b221cc5366c6a2b67ca4f6779e597e`
- Latest *tested* PR #31: `2309beab75e890a22cc8483a274dfae1b9cdddcf`
- PR #32: `85f1a792dd7d0fbf354c09ac83872887ed301c10`
- PR #33 including Mac readonly probe: `646a257bae10fe102feed526c905c39134e0d069`
- Isolation workflow branch: `research/frank-pr31-pr32-pr33-integration-20261011`, workflow code SHA `5c8a2e9a1396050e585c5d6d0046846e818a019a`.

The baseline main subsequently advanced to `9754fcf4cfd6cfdec75059f5f90cf78263bd3719` by two commits affecting **only** `research/BSC_MEME_DDAC_MARSCOIN_16_SPCXB_TO_USDT_V3_ROUTE_AUDIT_2026-10-11.json`. That newer main HEAD was **not** the actual tested base; GitHub compare confirms none of the newer changes touched Frank product or tests. Do not confuse them.

## Actual four-combination GitHub CI

[Actions #38157011319](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38157011319): all four jobs **SUCCESS**.

| Temporary pinned Git merge tree | Complete local-agent suite | Result | Ephemeral Git merge SHA (NOT pushed) |
| --- | ---: | --- | --- |
| main + PR32 | **1,055 passed** | PASS | `9cdc44349c918a2089308246dbc9a0a8b9b9fe51` |
| main + PR33 | **1,082 passed** | PASS | `65231e61e6dbdc4bb4f156824df38f19df148fd8` |
| main + PR32 + PR33 | **1,090 passed** | PASS | `964f7b038c322dfe16154e4ead187d00459b5fc2` |
| main + PR32 + PR33 + PR31 | **1,218 passed** | PASS | `0a2e1bf53acd8f484ad8aff7136763b4c8f7d59b` |

Tests ran with `FRANK_EXPECT_REAL_GIT_REPLAY=1`, repository real Git source archive available, Python 3.12 and dev tooling, `numpy>=2,<3`, `pyflakes==3.4.0`. `compileall` and Node `--check` passed. Git diff guard rejected any changes inside frozen `local-agent/mission_agent/frank/` and `local-agent/mission_agent/signals/`.

**One actual merging issue resolved solely on disposable CI runner:** PR32 and PR33 each created `.github/workflows/frank-pr32-pr33-review-tests.yml`, causing an add/add conflict. Test harness only permits this **exact** file, takes the PR33 test workflow, commits resolution *inside the ephemeral runner only*, and explicitly fails all other conflicts. No conflicting runtime Python/JS file was auto-overridden. This conflict must be deliberately resolved when merging those PRs to main.

The earlier matrix [38156869444](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38156869444) tested the older PR31 SHA `c65d04a8...` and reached 1,212; it **must not be cited as a test of the current 2309... code**. The last run above is the current exact corrected snapshot.

## Branch and Mac testing distinction

- [PR32 isolated CI 38155283993](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38155283993): 8 OAuth tests + 1,055 entire suite, no Google account auth.
- [PR33 isolated CI 38156777984](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38156777984): 35 focused tests + 1,082 entire suite, including six additional Mac-readonly synthetic tests. Latest source `scripts/frank_dashboard_readonly_acceptance.py` is a **one-shot** aggregate-only locally executed probe. It uses `mode=ro` and `PRAGMA query_only=ON`, reads three deployed file Git blobs and localhost health endpoint, outputs no wallet/email/paths, and never invokes Gmail, `launchctl`, OAuth or chain trading.
- The deployment helper `scripts/deploy_frank_dashboard_review_badge.py` still pins **PR33-only product** commit `1014c14b4df00757593f7ca4de8cedae0f09afaa` and three blob hashes; GitHub raw GETs independently matched those SHA values. It is **not a combined PR31+PR33 deploy artifact**. Treat any merged installation as a distinct, as-yet-unreleased bundle requiring newly pinned blob hashes, cross-PR source review and Mac test.

## Hard gates remaining — DO NOT MERGE OR DEPLOY

1. Genuine other-AI independent review of the latest PR31 and combined runtime code, using its **exact tested code SHA**, is not completed in this chat. No security PASS can be claimed from this CI alone.
2. User's actual Mac `FrankMeme` Dashboard live source revision, read-only SQLite state, localhost HTTP count parity, `launchctl` health and browser rendering remain unobserved. Synthetic tests are not an actual Mac test. Do not reconfigure or restart production services without a separately authorized release step.
3. PR32's real Gmail OAuth consent, exact intended account and Sent readback not exercised. Prior independent reviewer stated 14/14 simulated Google E2E on an **unavailable local patch**; this CI does not establish those 14 cases.
4. A malformed timestamp can remain visibly `pending` rather than automatically escalating to manual review. No delivery state machine changes were authorized.
5. Immutable evidence / full chain history / acquisition cost research of PR31 is bounded and not full-wallet complete; do not label passive ATA receipts as active BUYs or claim exact realized PnL.

Result: `PINNED_FOUR_MATRIX=PASS`; `OTHER_AI_REVIEW=NOT_DONE`; `REAL_MAC_READONLY_ACCEPTANCE=NOT_DONE`; `PR32_GOOGLE_OAUTH=NOT_DONE`; `MERGE_MAIN=NO`; `MAC_DEPLOY=NO`; `LIVE_GMAIL_SEND=NO`; `PRODUCTION_TRADING=NO_GO`.

No new monitor, schedule, email, wallet operation, database write, Mac restart or production release was performed during this CI work.
