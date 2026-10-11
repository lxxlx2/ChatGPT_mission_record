# Frank V2 PR #31 — Mac isolated read-only acceptance result
Date: 2026-10-12, Bangkok. Execution result timestamp UTC: 2026-10-11T17:56:59.122498+00:00.

## Scope and provenance
- **Tested PR #31 code commit:** `c50e7e2259e85ce89e14641a4e1e98ca3e4a4bc7`, exact `EXACT_SOURCE_SHA=PASS`.
- **Runner** committed to review-only branch `review/frank-pr31-mac-isolated-readonly-acceptance-20261012`, commit `617b5b2afda9c5ad4c0e5e677bc7d265beca3810`. It was run from an isolated temporary Git checkout.
- **User supplied original result archive:** `frank-pr31-mac-readonly-20261012-005659.zip`; SHA256 `6544344b3a4fa733c1f17335f4a5339d8e75478874f1cc8f5d27a0c0ea266e1e`; contains `mac-readonly-acceptance.json`.
- Two user-supplied screenshots were separately reviewed in the conversation:
  - J7 screenshot image hash SHA256 `a5b4ff2dfb7ad00cb0b06d8771fa31d0e102320b1fab2f97234866b6367d073b`.
  - BPxx screenshot image hash SHA256 `f01134abca514c657aaa7b57ed3774c624548d47d7f8df0e39252f478d186ad7`.
- This Git record does **not** include or modify the original ZIP or screenshots; hashes are for later evidence matching.

## Raw acceptance result (preserve without rewriting)
- `mac_readonly_acceptance=PARTIAL`
- `failed_stage_type=null`
- `checks`: **28 PASS, 1 SKIPPED, 0 FAIL**.
- The sole `SKIPPED` is `BROWSER_RENDER`. The command's interactive browser confirmation was not entered as PASS.
- `watchlist_row_count=228` and `target_sha=c50e7e2259e85ce89e14641a4e1e98ca3e4a4bc7`.

## Automated observations
- `EXACT_SOURCE_SHA`, `ISOLATED_SOURCE_COMPLETE`, `SQLITE_SNAPSHOT_INTEGRITY` x2, `NO_LIVE_DB_IN_ISOLATION`, `ISOLATED_DASHBOARD_HTTP_200`, `NO_PRODUCTION_PORT_COLLISION`: PASS.
- `WATCH_SCHEMA_V2`, `J7_AND_BPXX_PRESENT`, `NO_OLD_GAP_LABELS`, `NEW_AT_A_GLANCE_WINDOW_LABEL`: PASS.
- `J7_ATA_WINDOW`: (before=0, during=2, failed=0, success_unverified=0, verified_passive=2): PASS.
- `BPXX_ATA_WINDOW`: (before=63, during=3, failed=1, success_unverified=1, verified_passive=1): PASS.
- `J7_NOT_INFERRED_BUY`, `BPXX_NOT_INFERRED_BUY`, `J7_TRADES_UNCHANGED`, `BPXX_TRADES_UNCHANGED`, `ALL_LOCAL_TRADE_COUNTS_UNCHANGED`, `PASSIVE_NO_BUY`: PASS.
- `RPC_PARTIAL_STATUS`, `RPC_PARTIAL_PRESERVES_PRIOR_VALID`, `RPC_NOT_COMPLETE`: PASS.
- `EXPORT_FAILURE_REPORTED`, `EXPORT_PENDING_RETAINED`, `EXPORT_NO_NETWORK`: PASS.
- `ISOLATED_DASHBOARD_STOPPED`, `LAUNCHAGENTS_UNCHANGED`: PASS.
- Script reports no attempted production database writes, Mission Loop restart, Gmail send, Git push, or live Solana RPC. These are script recorded flags, not independent disk-write or network traffic tracing.

## Separate screenshot review (subsequent to ZIP)
The chat-provided images show the **isolated** Dashboard correctly rendered:
- J7 row `J7bhFegCH...SXpump`: 0 previous-index-window and 2 within-window, passive receipts 2, local recognized buys 0, sells 1; no active BUY implied.
- BPxx row `BPxxfRCX...VBjPCy`: 63 before-index and 3 within-index, failed 1, successful unverified 1, verified passive receipt 1; local buys 0, sells 4.
- Review result for the specific visible J7/BPxx ATA window and passive-receipt labels: **MANUAL_SCREENSHOT_REVIEW=PASS**. This is a supplementary visual check, **not** a retroactive change to the original ZIP's `BROWSER_RENDER=SKIPPED` or `mac_readonly_acceptance=PARTIAL`.
- The browser header temporarily shows `Frank 监控离线` because the isolated service uses a frozen heartbeat JSON snapshot whose age increases. That screenshot is not evidence that the separate live production Frank loop went offline.

## Gate assessment
- **Isolated Mac functional/data checks:** PASS (automated 28/28; screenshot text reviewed separately).
- **Original execution's interactive browser gate:** SKIPPED, original ZIP remains PARTIAL.
- **Combined PR #31/#32/#33 against then-current main:** NOT CHECKED by this run.
- **Production deployment, Gmail delivery, trading policy, and main merge:** NOT TESTED/NOT AUTHORIZED.
- **PR #31 should remain Draft.** Do not conflate this research acceptance with production release approval.
