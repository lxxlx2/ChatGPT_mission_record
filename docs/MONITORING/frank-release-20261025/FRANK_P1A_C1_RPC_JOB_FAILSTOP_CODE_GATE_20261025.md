# Frank P1-A C1 — RPC job-level failstop code candidate (2026-10-25)

**CODE_ONLY / NO_PRODUCTION_DEPLOYMENT / NO_REAL_RPC / NO_NEW_CA_JOB / NO_MAC_RUNTIME_ACTION / NO_MERGE / NO_TRADES.**

## Verified original issue and baseline

- [Issue #165 current C0 Mac GET receipt #6400369303](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165#issuecomment-6400369303): actual old cache API GET HTTP200/70ms, old job ID unavailable, browser not verified, old Deep report partial `special_normalization_complete=false`; no fresh POST/RPC.
- C1 plan: [PR #203](https://github.com/lxxlx2/ChatGPT_mission_record/pull/203) pinned `8fb880e7479172af2f2e5cda25eed16fd213aabb`.
- Feature starts directly from **Mac-reported installed product source** `914e9e47fed2e60bc24690fcb083413a64d4e681`; separate baseline branch is pinned to that immutable commit. No changes to installed Mac product or D2 private JSON.
- Existing source before this candidate retries each **logical** Solana JSON RPC up to `max(6,3×len(endpoints))` network attempts (normally up to 12), without job-total cap; Deep limits 20 holders, 100 history signatures, and 50 fund signatures per owner, **not a whole-job RPC call count**. Historical Deep report self-recorded 1,733 calls, no guarantee of complete normalization.

## Candidate changes (NOT authorized for production)

- `mission_agent/meme/cluster.py` accepts optional strictly positive `max_wire_attempts` and finite positive `max_elapsed_seconds` for one RPC adapter lifetime, injecting monotonic clock for deterministic fake tests. Entire `SolanaReadOnlyRPC.call` uses single instance across analysis. Cache hits do not consume wire attempts. Before any network attempt, including retry/fallback, enforce total attempts and elapsed budget; after backoff check again; clamp each URLopen socket timeout to remaining RPC deadline; recheck after response. Budget exception is non-secret fixed `RPCJobBudgetExceeded`.
- Prevent `WalletClusterAnalyzer.token_profile` / holder signatures / transaction reads / funder signatures / funding transaction handlers from swallowing **budget** exceptions and degrading silently to `UNAVAILABLE` or transaction_errors. Budget exhaust stops analysis.
- `mission_control/server.py` proposes conservative **hard ceiling** tuples for deployment only **after separate review**: Quick: 300 on-wire attempts / 600s, Standard: 1,200 / 1,800s, Deep: 2,500 / 3,600s. These are policy *candidate values* to approve against real provider quota and expected coverage, **not observed real run requirements, quote/cost claims or authorization to send requests**. No env override to silently disable ceilings in the current Dashboard API.
- `ClusterJobManager._run` catches `RPCJobBudgetExceeded` separately: job `status=ERROR`, `progress.stage=RPC_BUDGET_EXHAUSTED`, explicit `CLUSTER_ANALYSIS_INCOMPLETE_BUDGET_EXHAUSTED` and on-wire count/budget, **without writing latest.json, new success report, or triggering CA DONE evidence notifier**. Existing last saved report stays historical; browser displays “分析未完成” instead of complete or generic RPC error.
- The normal non-budget exception path remains unchanged. Existing manual GET-only retry and same-mint historic cache logic are not rewritten. Presets and scanner algorithms are not enlarged.

## Important remaining limitations for reviewer and follow-up C2

1. **No claim of complete per-job wall-clock timeout outside RPC boundaries.** The elapsed cap is enforced on RPC-call entry/after in-adapter backoff and once a response completes, with per-socket timeout. Non-RPC DexScreener/Jupiter or report serialization/SQLite operations do not all share this deadline, and read streaming may exceed an OS socket inactivity timeout. If a hard *whole-worker* wall-clock guarantee is required before live C2, design and independently validate a separate cooperative cancellation/watchdog method without killing production services.
2. The budget tracks **adapter on-wire RPC attempts, retries/fallback**, not upstream request charge units, third-party market quote HTTP calls or token transaction fetch cost. No automatic paid account or provider changes. Provider quotas and prices remain **UNVERIFIED** for deployment.
3. Partial in-memory material from exhausted runs is intentionally **not saved as a complete report**; only bounded job error counters and any existing preview remain until job pruning. Avoid claiming persistent partial analysis. A durable partial-report mechanism requires separate privacy/security review before implementation.
4. Preset ceiling values require independent cost/coverage audit against a representative local synthetic fixture and historical 1,733 report before actual POST/RPC; historical result is not a guaranteed lower bound. A budget error correctly blocks success, even if only one more cache/RPC lookup would have finished.
5. Existing `RPCJobBudgetExceeded` handling must be independently reviewed for all broad exception handlers, cache behavior, fake clock monotonic invariants, and HTTP URL timeout. Other modules constructing `SolanaReadOnlyRPC` without budget retain preexisting behavior; **only Dashboard CA _run passes the fixed limits**.
6. Baseline for this review is a **special-purpose pinned release-source branch**, not `main`, because main has a separate long-running line and would introduce unrelated hundreds of files into diff. Do not merge that baseline branch. Feature PR must show ONLY this C1 delta against pinned installed SHA.

## Offline-only verification gates

- CI must run Python syntax, Node syntax, pytest synthetic quota/fallback/429, elapsed timeout, cache hits, negative inputs, token-profile/holder/funder exceptions, `_run` no report persistence/ERROR, existing cluster tests, and existing GET-only UI recovery tests. CI is **not** Mac, a paid endpoint, real RPC, or real browser acceptance.
- An independent reviewer must verify fixed SHA and test actual branch diff against `914e9e47fed2e60bc24690fcb083413a64d4e681`; cannot approve by reading this document alone.
- If no CI run/failed run, leave `CI_UNVERIFIED` or `REQUEST_CHANGES` rather than asserting test PASS.
- After independent source review and a separate explicit Mac sandbox authorization, optional exact-SHA offline Mac test only; do **not** start production 8766 calls or new CA POST.
- Actual deployment and each later new Quick/Standard/Deep request need **separate explicit user permission**, fixed budget, active-provider quota assessment, no repeated submissions, and rollback plan.

**Status:** `C1_CODE_CANDIDATE / INDEPENDENT_REVIEW_PENDING / PROD_UNCHANGED / C2_NOT_AUTHORIZED / ISSUE165_OPEN`.
