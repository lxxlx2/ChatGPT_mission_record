# BSC 前向跟单研究 F0：开发准备、数据源选择和有限期技术验收合同

> Status: `F0_PREPARATION_ONLY / F0_RUNTIME_NOT_AUTHORIZED / PENDING_OTHER_AI_REVIEW / RESEARCH_ONLY`  
> Date: 2026-10-19 Asia/Bangkok  
> Architecture authority: [PR #113 APPROVED at fixed SHA](https://github.com/lxxlx2/ChatGPT_mission_record/blob/9134fcd41df49ef836b81c8a040974ad89c1fde1/crypto-300-profit-mission/bsc-forward-follow-model/ARCHITECTURE.md), commit `9134fcd41df49ef836b81c8a040974ad89c1fde1`. This file is an **F0-only test contract**, not a second evolving architecture authority. Review approval was provided as an independent read-only review and authorizes **preparation, not runtime**.
> Source branches: Draft [PR #40](https://github.com/lxxlx2/ChatGPT_mission_record/pull/40) and independent Draft [PR #97](https://github.com/lxxlx2/ChatGPT_mission_record/pull/97) are immutable read-only inputs. No merge or modifications to them.

## 1. F0 target: three hard feasibility questions, not trading performance

F0 is a **24–48-hour, capped, TRIAL-only** technical experiment *only after separate user permission for an actual Mac/local read-only run*. The start of F0 development preparation is NOT permission to launch any local daemon/automations, send alerts, use paid APIs, request wallet signatures or execute trades.

1. **L1**: can available no-cost providers deliver actual BSC wallet signed BUY/SELL identification with preserved first-actionable time, receipt and recoverable gaps?
2. **L2**: can one real-time scheduled, multi-delay quotation pipeline issue and retain requests at `+60/+300/+900s` for both watchlist and live randomized ordinary Router BUY controls? What are quote failure/staleness/queue latency?
3. **L4 comparator feasibility**: can an *unwatched ordinary Router transaction stream* be found and sampled in real time **without exorbitant resource usage**, and can historical chain evidence independently audit event recall?

The trial **does not evaluate realized profit**. No significant true buys during a 24–48 h trial means `INSUFFICIENT_LIVE_EVENTS`, not a fraudulent 100% recall PASS or automatic research failure.

## 2. Frozen source-stratified preselection, not final admissibility

- Input A: PR40 immutable baseline `431c02d1…`, Git blob `e3c8815630878dddc03b7a6e11b8f0d2d89cbf6a`, 23 frozen BSC research candidates. **该原始 blob 含有结果/事后研究字段**：`profit_rank`、`independently_closed_positive_major_count`、`independently_closed_negative_major_count`、`owner_signed_trade_verified_major_count`、`recent_30d_activity_state`、`last_confirmed_true_swap_UTC` 等；**F0 的选取、EOA 检查、替补和运行决策均禁止读取、输出、传入或利用这些字段**。唯一允许解析该原始文件的是独立的来源验证/安全投影过程，只取 `wallet`、固定行号及来源 blob SHA；实际操作者和未来 F0 runner 只能使用不含结果字段的 `F0_COHORT_PRESELECTION.json`。
- Input B: PR97 449 screening `5bca0e8f…`, Git blob `4727b8b53dcd63b350d9e5f27922cd06db8a2a14`; `ACTIVE && first_positive_chain=bsc` = 219 rows, minus 2 duplicate PR40 wallets (#167 A83B and #283 DDAC) = **217 distinct BSC nonce-active candidates**. **该来源含不同的历史扫描协议**：第 1–120 行使用 `FULL_THREE_CHAIN_NONCE_PAIRS`，第 121–449 行使用 `BSC_FIRST_EARLY_EXIT`（BSC 首检见正向签名即停止）。219 条 BSC first-positive 中，前者 65、后者 154；去掉 2 条重复地址后为 65 和 152。**F0 报告必须按 `screening_protocol` 分层标注活动证据覆盖限制，绝不能将这两类视作均经完整三链签名查询**。历史 nonce 活跃 ≠ 当下 Meme swap 或 EOA 身份。
- Deterministic rank: 32-bit unsigned FNV-1a over ASCII `9134fcd41df49ef836b81c8a040974ad89c1fde1|source|lowercase_wallet`, ascending hash then lex wallet. Source-stratified **10 + 10 PRIMARY; 5 + 5 ranked BACKUP**. The full pinned selection is `F0_COHORT_PRESELECTION.json`; `f0_verify_cohort.py` deterministically recomputes against `git cat-file` and verifies source blobs with Git SHA1. Sampling uses only public wallet address, original source row, source ID, pinned blob, fixed seed and permitted historical **BSC nonce** eligibility; it **does not read or carry over any PR40 outcome, historical profitability, trade count, recent-activity score, winner ranking or post-freeze result**. A strict `ALLOWED_COHORT_KEYS` whitelist and `FORBIDDEN_OUTCOME_KEYS` check now enforce this in the offline verifier.
- **No RPC-based EOA check has occurred**. Prior to any authorized trial, eligible primaries require technical validation (`eth_getCode == 0x` at the relevant block, known infrastructure exclusion). **Replace only from the next unconsumed BACKUP within the same source stratum and in fixed rank order**, never using any historical profitability/score or market outcome. A replacement requires an append-only `replacement_audit` row with **all** fields: `rejected_wallet, source_id, replacement_reason_code, checked_block, checked_at_utc, raw_rpc_response_sha256, evidence_source_ref, replacement_wallet, replacement_rank, decision_version`. `replacement_reason_code` is strictly **`NOT_EOA | KNOWN_INFRA | DUPLICATE | SOURCE_ERROR`**. The checked block, raw RPC response hash and technical evidence must be verifiable and predate replacement decision; absent/inconclusive RPC evidence, unknown code or missing field means **`UNDERFILLED_NO_SUBSTITUTION`**, even for DUPLICATE/SOURCE_ERROR unless a supporting RPC response actually exists. This strict F0 rule does **not** permit human judgment as a substitute for evidence. No replacement is preauthorized or executed in this preparation PR.
- All 30 selected public addresses are **preselection**, not permission to query, deploy, monitor or classify profitable. `watch_runtime_enabled=false` for all.

## 3. Data source options and true selection criterion

Official BNB Chain RPC documentation (https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/) states mainnet public endpoints have `eth_getLogs` disabled for certain listed endpoints and advertise a rate cap of 10K per 5 min (endpoint documentation, not a guaranteed user quota). Frequent log discovery is recommended via capable WebSocket providers. The BSC finality JSON-RPC API is documented at https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/bsc-api-list/; support on any chosen provider **must be tested, not assumed**.

| Candidate route | What F0 must confirm, not assume | Main risk / STOP condition |
|---|---|---|
| Connected Alchemy BSC RPC / asset transfers | Explicitly selected authorized app; network BSC actually supported; free read quota; historical receipt; eligible WS/log subscriptions if any | Available app ≠ automatically selected/configured; proprietary `getAssetTransfers` may lag, pagination or fees/quotas; same provider cannot alone prove independent denominator |
| Official BSC mainnet HTTP RPC | Actual calls for chain ID, block, transaction and receipt; health/failure/latency, rate limiting | Cannot rely on `eth_getLogs` for discovery; scanning every transaction in every block may be too expensive |
| Public no-cost WS or trusted documented free tier | `newHeads`/logs/tx or specific subscription semantics, message timestamps, reconnection, limits and SLA | Provider WS availability and completeness currently **UNVERIFIED**; absence of websocket in public endpoint list is not proof it exists |
| Mixed dual-path | Fast-path first-seen capture, archived gap recovery, independent **method** by block/tx/receipt and preferably **provider** | Both paths share upstream failure; huge control-stream cost; inability to construct expected buys yields denominator UNRESOLVED |

This is a shortlist, **not a vendor recommendation or free-tier confirmation**. F0 report must have a provider-by-method matrix with exact authorization state, measured calls, response counts, latency, errors, free unit consumption, cost and failures. No paid/funded GMGN or other payment API. No credentials in Git.

**Control stream has its own cost ledger**: `rpc_watchlist`, `rpc_random_control_discovery`, `rpc_quote_watchlist`, `rpc_quote_control`, `rpc_independent_audit`, `rpc_gap_recovery`, provider-specific free quota remaining. If the ordinary Router control stream dominates cap or cannot be sampled live, F0 must report `BLOCKED_REALTIME_CONTROL`. Do not silently swap it for post-hoc historical control.

## 4. Clock / buyer / seller state machine acceptance contract

- Record original `t_first_received_utc` / monotonic local receive time separately from `t_buy_detected_utc` / `t_sell_detected_utc`, `t_receipt_success_utc`, finality-confirmation UTC, quote scheduled and actual request/response times; clock offset and original message source must survive restart and replay.
- L1 `side=UNKNOWN` is legal: visible hash or transaction without a causally validated trade direction is present in *raw discovery/recognition* denominator and unresolved gap metrics, and **does not** trigger BUY/SELL L2 quote tasks until a live directional candidate with exact CA is identified. E2 is confirmed using price asset and token path causality in frozen rule framework.
- BUY detection **before** finality may schedule `PROVISIONAL_QUOTE` at `t_buy_detected+60/300/900`, even if finality arrives later. If receipt fails, provenance becomes REORGED or finality not met, **all three quotes are REJECTED**, no paper buy and **no control-group pairing** in the final eligible strategy comparison. **Exactly the same applies when a real-time randomly sampled CONTROL transaction fails E1**: exclude that control event from final matched eligible pairs, preserve its rejection and quote attempts in its own completeness denominator, and never change the random draw afterward to cherry-pick a successful alternative. Preserve raw quote and failed/cancelled denominators **in both groups**. Main/control use the identical policy.
- SELL has independent initial receipt, directional signal time, quote flow and exit schedule; non-actionable SELL and failed receipt are retained without pretending a timely executable exit.
- If first BUY+CA discovery occurs too late for a scheduled deadline, preserve `MISSED_DEADLINE`; if request errors or quote expires, `NO_QUOTE` or `STALE_QUOTE`. Do not re-anchor timestamp or backfill real-time quote evidence after the fact.
- `BACKFILL` and `REORGED` data can support completeness auditing but cannot become new E3 realtime detections. Failed E1 must not inflate "capture success"; disjoint ledger columns capture raw discovery and eligible event denominators.
- F1 later chooses the finality N / official `finalized` endpoint policy and E2 Router / quote exact-CA list. F0 must **measure availability** and preserve scenarios of missing finality, not invent a confirmed N.

## 5. Acceptance and stop gates

| Gate | Evidence / metric | Required status |
|---|---|---|
| A: no-cost transport | Per-method 24–48h actual calls, rate limits, errors, auth and network chain ID; no spending | `PASS` or `BLOCKED_SOURCE` |
| B: live actionable events | Raw signed BUY candidate to receipt/CA/quote path E0–E3, provenance; no fake lag | `PASS` if reproducible real forward witness; otherwise `INSUFFICIENT_LIVE_EVENTS` |
| C: quote schedule | Main/control **same pipeline**; live actual request/receive times for all three delays; exact missing/cancel reasons | `PASS` only for actually witnessed events; replay validates mechanics but not live timeliness |
| D: control stream | Real-time ordinary BUY discovery, *pre-registered selection*, cost ledger; quote parity for valid controls | `PASS` or `BLOCKED_REALTIME_CONTROL` |
| E: independent denominator | Separate path/method to reconstruct wallet-signed tx + receipt + causal buy, within a bounded scope; two-path difference report | `PASS` or `DENOMINATOR_UNRESOLVED`; **nonce increments alone cannot count as expected buys** |
| F: recovery/quality | Offline fixtures for WS disconnect, duplicate/late/out-of-order, SELL, E1 fail/reorg, E2 causal mismatch, UNFILLABLE and clock jump | `PASS` or explicit bug severity |
| G: repeatability | Fixed code SHA, source blob SHA, immutable trial ledger/UTC and local resource costs, dry-run CLI tests | `PASS` or `BLOCKED` |

**Do not falsely claim F0 PASS** from offline replay alone. For provider unavailable or inaccessible, F0 stops at `BLOCKED_SOURCE`; for observer no genuine trading events, report `INSUFFICIENT_LIVE_EVENTS`; for control-stream infeasibility, stop rather than bypass comparison. The 95% discovery target in architecture is conditional on an independently auditable adequate denominator, **not a score to be invented from small or biased trial samples**.

**Budget / stop before any runtime**: no RPC, WS, local background service, Mac deployment, automatic alert, purchase, wallet signature, transaction or trade now. F0 run requires a separate explicit go-ahead specifying allowed locally running environment, chosen *free* endpoint/app, account quotas, `MAX_TOTAL_RPC_CALLS` and `MAX_CONTROL_DISCOVERY_CALLS`, storage path/retention and bounded trial window. Any missing field = `NO_RUN`; no automatic retry extension or second provider requiring payment.

## 6. Development preparation completion (this PR only)

The current PR may provide:
- fixed architecture reference and separate F0 contract;
- source-stratified, deterministic sample manifest with raw source SHA, **outcome-field exclusion enforcement and replacement evidence contract**;
- **pure offline** integrity/reproducibility checker;
- read-only/production-deny requirements for a future prototype; no collector yet.

No F0 runner exists, no API calls were made, no source credentials were accessed, no production or existing Mission monitoring was modified. **Two separate unmerged Draft PRs are intentionally used**: approved architecture PR #113 is an external fixed-SHA authority; F0 preparation PR #116 is branched from main and does **not** contain `ARCHITECTURE.md` on its own branch. Merge order, if ever separately authorized, must preserve one architecture authority: review and merge PR #113 first, rebase/reconcile PR #116 against the approved main commit, and re-review affected fixed SHA. **Neither PR may be merged automatically or as a consequence of this review.** F0 runtime is **NOT_AUTHORIZED**. Reviewer gate for changes to this F0 spec remains `PENDING_OTHER_AI_REVIEW`, even though fixed SHA `9134fcd...` of the upstream *architecture* was independently approved.

## 7. Offline reproduction

From a local repo containing the two pinned commits, run:

```zsh
python3 crypto-300-profit-mission/bsc-forward-follow-model/f0/f0_verify_cohort.py --repo . --manifest crypto-300-profit-mission/bsc-forward-follow-model/f0/F0_COHORT_PRESELECTION.json
```

This command only performs `git cat-file` reads plus hash comparisons; it does **not** query BSC or alter Git. Use a separate checkout of this F0 branch and ensure source PR commits are locally fetched.
