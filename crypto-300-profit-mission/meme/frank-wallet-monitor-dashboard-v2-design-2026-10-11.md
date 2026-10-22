# Frank 链上观察台 V2：真实账本、持续观察池与 GMGN 功能对照技术设计

Date: 2026-10-11 Asia/Bangkok
Original 2026-10-11 status (historical): **DATA_AND_ARCHITECTURE_DESIGN_COMPLETED / IMPLEMENTATION_NOT_STARTED / REAL_REPLAY_NOT_PASSED / PRODUCTION_UNCHANGED**
2026-10-22 scoped status: **READONLY_DASHBOARD_PARTIALLY_DEPLOYED / CURRENT_WALLET_INVENTORY_NOT_COMPLETE / CA_QUERY_REGRESSION_OPEN / V3_NOT_IMPLEMENTED** — see sections 10–16
Parent task: $300 → $3000 Mission, Frank/Meme lane.
Inputs: `frank-wallet-ui-data-audit-2026-10-11.md` (real read-only chain samples, screenshot discrepancies and first-party GMGN research); `ca-analysis-unified-accuracy-acceptance.md` (manual CA comprehensive research); `FRANK_LOCAL_SIGNAL_V1_POLICY.md` (frozen production alert semantics).
Objective: **user can see and understand every materially relevant Frank trade, wallet position and token under observation, while the existing production BUY/WAIT and Gmail rules stay strictly unchanged.** A read-only local dashboard; no signed swap execution or paid GMGN requirement.

## 1. Product boundaries: separate truth from advice

Implement three *independent* domain layers; do not re-use a narrow signal candidate query as the data source of the whole page:

A. **Wallet fact ledger**: all address-touching finalized signatures and decoded wallet-owned economic movements, signed swaps, passive/active transfers, claims/rewards, token account creations, failed transactions and unresolved items, with raw proof and observable slot/time. This layer answers **what Frank actually did / received / transferred**.

B. **Wallet position and observation portfolio**: every relevant mint seen in A (including still-held and exited history) has an inventory ledger, acquisition/disposal facts, duration, watch reason, current market snapshot, optional PnL if cost is reconstructible, review status, last activity and persistence. This layer answers **what tokens must we still look at**.

C. **Frozen follow-signal engine**: consumes only its existing independently confirmed active-swap facts and frozen ACCUMULATION/MULTIPLE/reentry/WAIT/NO_BUY gates, maintains existing $30 sizing *only in this separate strategy*, live notification, outcome and dedupe. This layer answers **would a bounded Frank-follow policy trigger**. **No code or threshold change to C without separately approved review.**

A zero in C is not a zero in A or B. Runtime health for the writer/outbox is not data-completeness health. No candidate due to a strategy veto must never delete the observed wallet position from B.

## 2. Data flow and trust boundaries

```text
Solana finalized RPC / licensed optional read-only indexers
   | signatures + cursor, raw getTransaction, token owner accounts
   v
RAW ARCHIVE (signature + payload hash + slot + fetched_at + source)
   | restart-safe cursor, paging, dedupe, exact gap report
   v
FACT NORMALIZER (all account deltas, signer/delegate, CPI/DEX route)
   | immutable event_version and parser_version
   +-----------------> ALL-WALLET ACTIVITY FEED (wallet actions + transfers)
   |
   v
POSITION JOURNAL (per wallet/mint lots + raw remaining + priced status)
   |                      |
   |                      +--> WATCH REGISTRY (observed/pinned/state/next-check)
   |                                |
   |                                v
   +---------------------> Read-only DASHBOARD (Watch / Held / Recent / History)
   |
   +--> VERIFIED ACTIVE SWAPS ONLY -> EXISTING FROZEN FRANK SIGNAL ENGINE
                                      -> existing local/Gmail delivery
                    [No new route from Watch Registry to Gmail]
```

The current `FrankReader` production `forward.sqlite` remains **read-only** to the control/dashboard app. A new versioned **research-sidecar SQLite** at the existing `control_root` must be isolated from the writer/outbox DB; never mutate/replace existing live ledger. Preserve raw archive and source signatures for replays. Avoid creating another LaunchAgent or scheduler; reuse an explicitly approved existing loop only *after* validation/rollout permission. Until then the design is documentation only.

## 3. Data acquisition strategy and honest feasibility

### 3.1 Near-real-time incremental path

- Poll the known Frank wallet's finalized `getSignaturesForAddress`, with the existing production cursor and durable batch reconciliation (wallet address, new cursor, sampled head, previous completed signature).
- Every new signature has exactly one `wallet_signature` identity independent of how many token legs it produces. Store transaction status and all matching wallet token movements; dedupe by `wallet,signature,inner_instruction_index/mint/leg`.
- Use `getTransaction` with explicit version compatibility; do not assume token account creation, external signer, creator rewards or airdrops are buys. Reconstruct native SOL delta after gas/rent and WSOL transient ATA including zeroed/closes; treat unexplained legs as `ROUTE_UNRESOLVED` rather than fabricated USD trade.
- Pace RPC requests with a declared per-provider quota, exponential cooldown and alternate legitimately available RPC; full source of truth includes `retry_after`, tx fetch errors, page cursor, outstanding/backfill count. When provider rate limit is exhausted, stop and resume, leaving `coverage_gap=true`.
- No silent dropping of historical signatures to keep a UI green; queue backlog and token-level priorities are auditable.

### 3.2 Historical/backfill path

- Freeze and reuse the prior Frank raw archive and `forward.sqlite` first. Index previously missing time ranges **incrementally**, with signature pagination and persisted before/until cursor.
- Prioritize material known market swaps (the three Oct 9 screenshot transactions), unresolved signed multi-asset routes and active/open tokens; validate gaps with Solana explorers, independently available transaction raw data or user-authorized access to already-installed local archival data. Do not claim entire-wallet GMGN equivalence from a limited public RPC account with 429 limits.
- For huge multi-year wallets, a general `getSignaturesForAddress` + `getTransaction` backfill can be practically impossible on a free/shared RPC at acceptable latency. Prefer cumulative local incremental storage plus selective gap backfill or an allowed read-only indexer with a working free allocation. Historical records that cannot be reached remain `BACKFILL_INCOMPLETE`; no fake 7d/30d totals.
- An alternative public analytic display may be used for **discovery/parity**; do not ingest an undocumented GMGN private endpoint or paid API.

### 3.3 Independent secondary/market context

- DexScreener public token/pair endpoints for timestamped USD reference, mcap/FDV, pair liquidity/volume/txns and social links; Solana raw pool program state where meaningful to verify selected-pair actual reserves. URLs: https://docs.dexscreener.com/api/reference
- Token authority and mint state via finalized RPC; compare with available public explorer/indexer outputs, exact mint and slot where possible.
- GMGN public wallet/token pages, official GMGN documentation, FOMO and OKX Wallet publicly displayed views for **manual independent parity** where accessible. Never equate names alone, or silently assume profit formula/window equality.
- External narrative research belongs to comprehensive single-mode CA detail; Watch list shows the latest sourced summary and a link, never an invented official call.
- Quotes for an exact trade amount must be user-requested separately; the generic CA page has no forced $30 quote. Existing frozen follow engine's $30 Jupiter hypothetical executable quote is a **separate, unchanged system**.

## 4. Exact normalized data contracts

Each record includes provenance (`source_provider`, `chain`, `slot`, `block_time`, `observed_at`, `raw_sha256`, `parser_version`, `tx_signature`, `confidence`) and an idempotent unique key.

### 4.1 wallet_event

`(wallet,signature,slot,block_time,tx_success,wallet_signer,wallet_fee_payer,delegate_authority,program_ids,source_ata,dest_ata,mint,decimals,pre_raw,post_raw,delta_raw,route_quote_asset,quote_delta_raw,native_sol_fee_raw,rent_delta_raw,trade_class,evidence_status,raw_ref)`.

Explicit `trade_class` vocabulary:
- `ACTIVE_MARKET_BUY` / `ACTIVE_MARKET_SELL`: confirmed wallet authorized active DEX exchange and coherent opposing legs, with source signature and verifiable direction.
- `ACTIVE_SWAP_ROUTE_UNRESOLVED`: economically likely wallet-directed route, cannot assign per-token cost or exact market side.
- `SIGNED_TOKEN_TRANSFER_OUT`, `PASSIVE_TOKEN_TRANSFER_IN`, `THIRD_PARTY_DEPOSIT`: genuine movements, **not** swap BUY/SELL.
- `REWARD_OR_CLAIM`, `LP_OR_VAULT_OPERATION`, `ATA_OR_RENT_EVENT`, `FAILED_TX`, `OTHER_NON_TRADE`, `RPC_UNAVAILABLE`.
- `POSITION_AFTER_UNRESOLVED` is an inventory/cost status, **not** permission to invent a completed exit or proceeds.

Do not suppress legitimate delegate-authorized actions by blindly assuming Frank must be fee payer: use validated wallet signer/authority semantics, wallet-owned balances, DEX bound CPI and opposing asset flows. Source classification must distinguish *a transfer out to another wallet* from a *market sell receiving quote*.

### 4.2 token_journal + position_snapshot

- Every token has a chronological append-only ledger of `observed_acquire`, `verified_buy`, `transfer_in`, `transfer_out`, `verified_sell`, `claim_reward`, `burn`, `unknown_cost`, `rebase`, with raw mint quantities and evidence.
- State: `HELD_VERIFIED`, `NO_INVENTORY_VERIFIED`, `POSITION_UNCERTAIN`, each with source slot/time. Reconcile **sum of owned token accounts** against chronological journal and current chain snapshot; if not equal, raise `BALANCE_MISMATCH`, surface to UI and block affected PnL as final.
- For sold tokens with reconstructible original buy lots, use **FIFO realized cost basis** as internal canonical calculation; optionally show weighted-average reference and document when GMGN uses a different method. The method is an *internal design decision requiring matched parity tests*, not a claim GMGN calculates identically.
- `realized_profit = verified_sale_quote_net - attributed_buy_lot_cost - attributed_fees`; `unrealized_profit = current_mark_value_of_known_remaining_lots - remaining_known_cost`. If transfer-in cost is unknown, show `PnL INCOMPLETE` and `known_proceeds` separately, never fabricate $0 basis.
- USD conversions: direct USDC amount where applicable; SOL-denominated trade requires a **timestamp-appropriate observable USD/SOL reference** and citation. Keep quote-token original. Report `USD_ESTIMATED` separately from `USD_DIRECT`.
- Include `earliest_known_acquisition`, `earliest_verified_market_buy`, `latest_buy`, `latest_sell`, `latest_economic_event`, `held_duration_observed` and `lifetime_history_complete`; do not call a bounded earliest found purchase the wallet's first ever trade.
- Lifetime/7D/30D `buy_count/sell_count` count **verified market swaps** only; wallet deposit/transfer metrics are separate. A 7D gross flow is a **window statistic**, PnL must use acquisition lots outside the window if currently sold.

### 4.3 watch_token / watch_event

`(person_id,mint,source_wallet,first_seen,first_verified_buy,last_signed_swap,last_wallet_movement,last_holder_snapshot,watch_state,watch_reason,signal_state,inventory_state,price_reference,price_mark_at,liquidity_usd,market_cap_usd,latest_source,watch_since,manual_pin,manual_group,notes,last_transition,event_id)`.

- Watch list exists even without a formal signal, may be created on **first verified active BUY**, existing silent `WATCH` stage, positive wallet position with chain evidence, or explicit **user pin**. Passive receipt alone defaults to a separate “incoming/unknown acquisition” watch label, **not** buy-conviction.
- State machine (display only): `NEW_ACTIVITY` → `WATCHING` → `ACCUMULATING` → `HIGH_CONVICTION_SIGNAL` → `HOLDING/TRIMMING` → `EXITED` → `ARCHIVED`. Alternate `REENTRY_WATCH`, `HFT_EXCLUDED`, `TRANSFER_ONLY`, `DATA_GAP`, `MANUAL_PIN` are explicitly display/eligibility tags.
- Transitions triggered by **verified journal facts / current inventory** with event signatures, **never** by price-only inference that Frank bought/sold. Internal state names are not new notification thresholds.
- Exit is persistent in history; archived by user action or retention policy without deleting economic ledger. Manual pins and user notes persist across reload, code updates and day boundaries.
- Re-entry after zero inventory reopens a new episode with a new ID, preserving prior realized PnL and old events. If current wallet inventory unknown, never silently close the watch row.

## 5. Dashboard redesign: fit-for-decision, not empty “current following only”

**Historical 2026-10-11 proposal**: three top-level views. Section 12 replaces only that UI navigation layout with five views, without changing any source, safety or watchlist obligations:

### A. 「Frank 观察池」 (default, the primary task)

Header:
- `数据状态`: Frank writer heartbeat **separately** from source ledger completeness (latest indexed slot/lag/backlog/errors).
- `当前有持仓`, `等待观察`, `正式跟随信号`, `减仓/退出`, `数据未完成` counts shown **with their definitions**.
- Daily/7d/30d activity controls show explicitly selected interval, non-overlapping historical facts, and total signed wallet trades vs passive receipts.

Persistent table, sortable by newest **real material Frank action**, with one row per (Frank, mint/episode):
`代币+完整CA链接 | Frank 首买/最近买卖 UTC/BKK | 7d 买/卖金额及次数 | 已知当前持仓 | 买入均价/现价涨跌 | 7d/30d/累计已实现+未实现(若可算) | 资金流及流动性 | WATCH原因/下次检查条件 | 数据可信度 | [观察标记]`.
- Tabs/filters: `全部关注`, `观察中`, `Frank持有`, `强信号`, `减仓/退出`, `已结束`, `用户收藏`, `待复核`. **An inactive current signal must not empty the watch list**.
- Clear badges: `VERIFIED_BUY`, `TRANSFER_IN_ONLY`, `SIGNED_SELL`, `PARTIAL_EXIT`, `REENTRY`, `QUOTE_UNKNOWN`. History is searchable/paginated beyond last 24h; pinned tokens survive old age.
- One-click open **read-only CA report** and external GMGN/FOMO/OKX/Solscan context links, no trade execution.

### B. 「Frank 钱包」 (GMGN-style transparent book)

- Portfolio top: current observed inventory with snapshot slot and reconciliation coverage; token cost, current value, realized/unrealized/total with evidence confidence, 7D/30D/lifetime *where data is complete*. Never let a historical screenshot’s scope silently become 24h.
- Token drilldown: chronological real buys/sells plus transfers/rewards, batch grouping, exact transaction link, wallet signer, original SOL/USDC paid/received and independent USD reference; latest activity and cost-basis status.
- *Activity filters:* `全部签名`, `真实市场买入`, `真实市场卖出`, `转入`, `转出`, `奖励/其他`, `失败/待复核`; time range `24h/7d/30d/全部可用`, with source completeness reported for chosen range.
- Show HFT behavior, sold > bought (only with comparable accounting), received-without-buy, and owner/delegate actions as **diagnostic risk labels**, not automatic claims of fraud.

### C. 「CA 链上查询」 (existing manual CA feature)

- Follow separate canonical one-mode, accurate evidence requirements `ca-analysis-unified-accuracy-acceptance.md`. Cross-navigation from every observed mint.
- Preserve narrative and holder-role evidence; do not inject the follow policy's fixed Jupiter $30 quote.

### Empty/error states

- If formal signals = 0 but historical economic events exist: **「目前没有符合提醒门槛的强信号；观察池有 N 个代币」**. Never imply “Frank 未交易”.
- If current 24h market swaps = 0 while Oct9 records exist: **「近24h已验证主动交易0（数据覆盖状态）；以下为更早的历史交易」**.
- If RPC incomplete: **「已索引 X / 独立确认完整性：否，待回填 ...」**; no green `analysis done` or wallet PnL total implying full ledger.

## 6. Endpoint and physical storage design

Implementation names are provisional (do not assume created):
- `GET /api/frank/wallet/coverage?window=24h|7d|30d|all`: source freshness, last signature, window start/end, archival completeness, missing count when measurable, backlog, RPC 429/retries.
- `GET /api/frank/wallet/activity?window=&kind=&cursor=&limit=`: all economic activities, with signed swap vs passive classification.
- `GET /api/frank/wallet/positions?window=&sort=&cursor=`: token owner inventory, matched journal, per-mint realized/unrealized where cost known, status.
- `GET /api/frank/watchlist?state=&sort=&cursor=`: durable observation rows independent of follow candidates.
- `GET /api/frank/watchlist/:mint/history`: event/evidence timeline + recorded user notes/pins.
- `GET /api/frank/signals`: existing frozen signal read-only overlay from prior `/api/candidates`; no changes to decision semantics.
- Optional deliberate `POST /api/frank/watchlist/pin`: **local metadata only**, user interaction with a write-audit and CSRF defense, never an external transaction or notification.
- `GET /api/ca/... `: existing research endpoint, separate earlier requirements.

Sidecar SQLite proposed:
`source_checkpoint`, `raw_tx_index`, `normalized_wallet_event`, `mint_inventory_lots`, `position_snapshot`, `watch_token`, `watch_history`, `market_mark`, `coverage_gap`, `source_attempt`, `reconciliation_run`.
Invariants: unique tx signature, immutable raw hash, versioned parser, normalized raw integer units, foreign-key mint/owner, persisted backfill cursors; market marks versioned by source observed time and stale expiry. A failed latest fetch does not erase prior verified state.

## 7. Acceptance gates and execution order

**Stage D0: baseline and current deployed data forensic**
- Preserve the live `forward.sqlite` and current dashboard DB by a **read-only verified snapshot**; gather deployed version; obtain exact tx signatures for the three Oct9 screenshot trades, confirm with raw finalized `getTransaction` and 24h filter, and match 24h/7d/30d selection.
- Reproduce 132-signature + 429 limited sample from the independent audit using controlled non-abusive retries; compare all eligible sample signatures to local classification (external signed passive transfers must remain passive). Record source gaps, do not hide them.

**Stage D1: data ledger correctness (before UI)**
- Build isolated extractor and replay using immutable raw archive, no production edits. Categorize active buys/sells vs transfer/fee/reward/LP/unknown; ensure every wallet-owned token movement accounts for a journal delta or documented exception.
- Verify **Oct9 $3,300 buy, $2,232.34 sell, $7,031.56 sell** signatures and exact original quote legs. Those amounts are **user screenshot examples until raw signatures are verified**, not an accuracy benchmark already passed.
- Reconcile sample mint inventory against chain, signal engine's frozen classifications and transaction flow; no sell inferred from token outflow only. Distinguish incomplete PnL from genuine zero.

**Stage D2: portfolio/watch-state accuracy**
- Build watch states from broader facts, preserve all signal-eligible mint positions, retain older exits and pins. Construct 24h/7d/30d/all queries with explicit source completeness.
- Positive wallet position without formal ACCUMULATION/MULTIPLE **must** appear on Watch or Held. Frank signal 0 must not imply Watch 0.
- Independent wallet positions: sample 10+ diverse tokens including transfer-in only, late sold, active current, HFT excluded, reentry, unknown quote, routed SOL, historic trade older than 24h; freeze transaction case IDs and expected economic deltas.

**Stage D3: actual independent GMGN parity and useful UI**
- Capture same wallet/mint/time window for GMGN visible PnL/trades/hold count and local observations; independently compare at least 5 material tokens, record exact native signatures when possible, window and cost-method mismatches and unresolved causes.
- Test source/time definitions for current vs lifetime PnL; never force equality if GMGN rules are opaque. Reproduce scrollable Watch/Position lists, searches, persistent notes and up-to-date state. Check long-lived exit appears >24h.
- Code review by separate AI of raw classification, accounting, sidecar data model and frontend data semantics. Save review/findings and fix them. Unit tests alone are insufficient.

**Stage D4: real Mac read-only acceptance, explicitly authorized release**
- Prior to any live install, pass full isolated CI, real chain replay, independent AI review, rollback restore drill and version/source pin.
- Actual Mac acceptance must verify the 10/9 sample transfers/market swaps, display persistent watchlist independent of buy alerts, classify known passive transfers correctly, show 24h vs 7d/30d with accurate range, and leave Frank delivery/outbox/policy fingerprints unchanged.
- No new task/LaunchAgent/Gmail or automatic trade. No production deployment or restart until user explicitly authorizes it. `PRODUCTION_TRADING = NO_GO`.

## 8. Measurable success and rejection criteria

**Pass** only when: representative stored trades have raw-signature attribution; current chain inventory/journal balances reconcile; watch rows persist for any qualifying observed mint even if formal signal is zero; all displayed counts have selected time windows and source completeness; paid GMGN is unused; user can compare the same wallet/token actions to public GMGN/FOMO/OKX; independent review and actual local verification complete.

**Fail** if: 24h zero masquerades as lifetime zero; passive token receipt counted as Frank buy; outgoing transfer mislabeled sale; first purchase is inferred from bounded history; unsupported historical PnL is $0; any known traded/held token disappears solely due to signal policy; a missing paginated source is hidden behind “运行正常”; operational writer/notification is modified while merely implementing a new dashboard.

## 9. Delivery boundaries and current execution state

**Historical statement valid on 2026-10-11 only:** Design decisions and requirements in this document have been specified, not coded or operationally accepted. The 300-3000 governing conversation owns data definition and design gate; a separate implementation effort must perform D0→D4 in order. No unrelated code refactor, no automatic duplicate monitor, no paid GMGN API, no local RPC transaction signing, no unapproved runtime modification. Preserve existing user-approved frozen Frank signals and notification conditions unchanged.

---

## 10. 2026-10-22 V3 修订：先遵守已批准原则

本节修订现有 V2 产品原文档，不另开平行需求；严格依照已冻结的 [G1 五层架构 PR #114](https://github.com/lxxlx2/ChatGPT_mission_record/pull/114)（原批准正文 SHA e4d61d1c8f246a7b04ea46ba674855346625a243）、Mission 规范、既有 D0→D4 开发主线和用户已明确排除的固定交易金额。若任何设计触及冻结 G1 的硬边界，需先经用户对架构差异重新审批；本轮仅供 Claude 独立复核，非实施或部署许可。

**一处需纠正的旧 V3 草案冲突**：CA 已有 [统一准确性文档](ca-analysis-unified-accuracy-acceptance.md) 明确规定用户只有一个 CA 查询入口，内部渐进深入，不再让用户选择快速、标准或深度。上次 V3 草案中的“三档继续保留”与原用户批准的准确性原则冲突，以原文档的**单模式**为准。

**里程碑不改名**：V2 D0→D4 是业务开发顺序；G1 G0→G4 是研究、审查、独立验收及上线门禁；Option 3 P0→P5 属智能通知子项目。V3 仅调整既有 A/B 数据完整性与 D 层可用性，**不是新开第四套开发流程**。

### 10.1 功能完成状态必须按证据分级

- PRODUCTION_ACCEPTED：精确代码 SHA、运行产物及 Mac 实际验收明确通过，仅对该功能范围
- CODE_REVIEWED_NOT_DEPLOYED：代码和独立审查存在，但未证明当前生产安装
- EVIDENCE_ONLY：历史样本、快照、离线回放，不是当前在线功能
- DESIGNED_NOT_BUILT：仅有设计，尚无代码及真实功能验收
- BLOCKED_BY_SOURCE：真实源、授权、时效、完整性或价格可比条件缺失
- REGRESSION_OPEN：用户截图证实出现问题，但真实故障归因、修复验收未完成

| 原阶段及功能 | 已经实现且有证据 | 未实现或阻断 | 状态 |
|---|---|---|---|
| V1 原信号及提醒 | 原 ACCUMULATION/MULTIPLE 继续按既有授权运行 | 不批准本轮改信号和真实通知 | PRODUCTION_ACCEPTED（旧 V1） |
| 智能分析及买卖观察 | PR #146/#157 产品 SHA 31dd598df248ca15f731913a5cbf82e88b981874，8766 真 Mac Dashboard-only 上线验证 | 这不等于链上完整余额、可靠新鲜市场价或 V3 五区导航 | PRODUCTION_ACCEPTED（只读子集） |
| 签名流水/观察池 | 可看已索引 BUY/SELL、转入和 ATA，历史模型存在 | 交易分类混合枚举不清楚、多个模块重复、源非完整链 | PARTIAL_PRODUCT_DEPLOYED |
| 历史持仓快照 | PR #110 2026-10-11 32 Mint 样本，10 非零/22 零 | 无法证明 2026-10-22 当前余额，双 Token Program 全账户完整性未达 | EVIDENCE_ONLY / BLOCKED_BY_SOURCE |
| G2 正式集成候选 | PR #119 原范围的代码/CI 曾有验证 | Draft 未部署；不得当作已安装 | CODE_REVIEWED_NOT_DEPLOYED |
| CA 查询 | 用户 Mac 截图先得到部分基础行情，随后 Failed to fetch | POST/轮询/Worker/RPC/报告保存失败阶段尚未定位，见 Issue #165 | REGRESSION_OPEN |
| 清理“历史过期 15” | 旧显示源于历史未发 outbox；PR #164 有浏览器收起代码 | 尚未审核部署；逐条与 Gmail 对账及跨浏览器审计归档未实现 | CODE_ONLY / BLOCKED |
| 价格与盈利 | 仅有原始历史交易、部分市场样本 | 无完整新鲜同口径价格，不能显示当前价格变化或真实可跟收益 | BLOCKED_BY_SOURCE / NEED_MORE_DATA |
| 新智能风险消息 | 历史 fake unsent 示例 | 未完成送达/去重/通道审批，不允许真发 | DESIGNED_NOT_BUILT |
| V3 32 条交互改进 | 本节架构和页面验收规则 | 均未按 V3 完整 Mac 测试和发布，不得称 32/32 完成 | DESIGNED_NOT_BUILT |
| 旧 MC 的 30 美元报价及“小仓跟”邮件 | 旧 MC Loop 仍在原进程，曾有真实 Gmail 旧式内容 | 属独立通知/策略治理，Dashboard-only 未修复 | 独立风险 OPEN |

[PR #157 生产证据](https://github.com/lxxlx2/ChatGPT_mission_record/blob/cb6187a8df2c611693d4030555b194501006b24d/docs/MONITORING/frank-release-20261022/production-cutover/REPORT.md) 和 [Issue #165](https://github.com/lxxlx2/ChatGPT_mission_record/issues/165) 为本次状态快照依据。生产样本中的买卖数量和旧 PID 只对当天有效，不能当作恒定值。

## 11. 架构：严格复用 G1 A/B/C1/C2/D/E

| 层 | 真正职责 | 保持不变 |
|---|---|---|
| A 收集与原始证据 | 原钱包身份、签名/slot、原始响应 hash、获取时间、两类 Token Program 覆盖 | 原采集/原始数据不可被 UI 或衍生规则改写；无审批不加 RPC/常驻任务 |
| B 可审计事实 | 原始交易腿、主动 swap、被动收付、ATA、余额快照、价格时点和来源、纠错版本 | 同一签名可多腿，不能把转账冒充买卖；新纠错以版本/supersedes 留痕 |
| C1 研究/回放 | GMGN/FOMO/OKX 同窗对照、覆盖率、价格和潜在回报、独立 OOS | 未达到 G0-B 前为 NEED_MORE_DATA，不暗示获利 |
| C2 原信号引擎 | 原 V1 信号/轮次/通知生成与发送身份 | 不因 V3 页面改变阈值、出买卖建议或重发 |
| D 已有 Dashboard | 中文表示、来源链接、模块导航、筛选/分页、数据问题中心 | 前端不能自行生成 BUY/SELL、余额、收益或修复缺失的链上事实 |
| E 用户决策 | 买、卖、交易金额、实际操作 | 无默认金额、交易签名或自动执行 |

复用实际 FrankReader、wallet_activity、wallet_watch、wallet_inventory、CA cluster 的已有能力，先做源契约对齐，不复制新的并行账本。最小事实合同：

- 交易：wallet、Mint、signature、slot、事件时间、首次索引时间、原始 hash、解析器版本、分类、方向、token/quote 数量、交易腿序号、完整度
- 持仓：Frank owner、Mint、SPL 与 Token-2022 的全部相关账户、raw integer amount、decimals、获取时点、实际返回 slots、finalized 状态及账户覆盖
- 市场价：Mint/chain/pool/quote asset、价格种类、来源、价格时点、抓取时点、失效规则；实际 Frank 成交价、池子参考价和可执行报价不可混用
- 来源信号：触发签名、信号 ID、episode、冻结策略 hash、生成时间和另行证明的送达 ID；生成不等于收件
- CA 作业：job ID、CA、提交与阶段时间、已保存阶段、轮询错误/来源错误/保存错误、可读回报告
- 历史清理：原 decision ID、渠道、尝试/回执事实、另行追加的归档动作和可回查审计；原 outbox 不删改

不能证明账户在统一 slot 读取，就不能虚构一个共同 slot 余额。必须记录各程序读回 slot 与一致性差异；当前余额只能在**真实完整证据和适当时效**下有数值，历史 10 月 11 日快照不得升格为当前值。没有来源不等于零，余额为零不等于卖出，交易卖出不等于已清仓。

## 12. D 层布局：五个独立页面，保留 V2 业务能力

| 一级导航 | 首屏回答 | 合并旧模块 / 数据规则 |
|---|---|---|
| 当前机会 | 现在有无真实可查看的源信号 | 旧跟单候选与历史 WAIT/NO_BUY 分离，现有信号不因缺报价被消去；无执行报价时不可叫“可以成交” |
| Frank 持仓 | 截至哪一个证实 slot 持币多少 | 合并智能卡/持续观察池资产视图，历史模型只在历史详情，余额缺口集中一次列出 |
| 交易流水 | 哪天买卖、转入转出、创建账户或交易失败 | 合并买卖观察、最近交易、签名活动；只把源证明的 swap 称为买卖 |
| CA 分析 | 该代币基础、权限、持有人、LP、资金关系和外部叙事是否真正完成 | 一个 CA + 分析入口，内部渐进阶段；局部结果不是完成 |
| 历史与通知 | 历史退出/决策、邮件已发送/待确认、过期已拦截 | 原最近结束数量只出现一次，归档和收件分开审计 |

五页有可辨识标题/留白/表格，Tab 直达、统一 Mint 联动、返回顶端和移动端菜单，不再把多个同质模块排成长页。旧 V2 观察池独立于当前信号：即使没有 ACC/MULT，也必须继续保留持仓/历史/收藏，退出历史不能因 24h 窗口消失。

首页只显示真实有用的字段：Mint、动作/时间、真正信号及证据，不用历史 WAIT/NO_BUY、“重新建仓观察”长段占首屏。价格缺失不隐去原信号，但不能生产假定可执行结论。持仓只显示可靠 slot 数量或单处“当前余额尚未完成同步”及数据问题入口，不在每张卡片重复未核实。列表支持筛选、匹配总数和加载更多；技术限制写在帮助面板。

## 13. 中文词典、零假事实和简明文案

| 内部状态 | 展示 | 硬性条件 |
|---|---|---|
| ACTIVE_TRADE | 已确认买入 / 已确认卖出 | 签名、钱包与 swap 资产方向可复核 |
| PASSIVE_TRANSFER | 收到代币 / 转出代币 | 不当作主动买卖 |
| ATA_CREATE | 创建代币账户 | 不代表买入 |
| FAILED_TX | 交易失败 | 不计入成功买卖 |
| UNKNOWN_NEEDS_REVIEW | 待核查的账户活动 | 不算确认买卖 |
| MATCHED_OR_NOT_APPLICABLE | 不显示合并代码 | 必须拆成“交易记录一致”和“无需匹配交易”，不能默认匹配成功 |
| SELL_POSITION_UNRESOLVED | 已确认卖出，剩余持有数量待查 | 单独的真实余额才能证明卖后数量 |
| MODEL_OPEN | 历史模型记录为持有 | 不能作为当前链上持仓 |
| PRICE_UNAVAILABLE | 暂无符合要求的当前行情 | 不能填零、虚构涨幅或盈亏 |

“已识别经济腿”改成“代币买卖明细”，转入/转出另表述；只有真实买卖腿时才显示。所有面向用户的标题、说明、Toast、列表状态**句末不加句号**；英文 enum 不进主表格。删除同样的“研究提醒”及自我免责声明，不能删除其背后的权限校验或来源证据。缺口统一进入可展开“数据问题”，逐项记源、时点和未完成原因；不能因为用户希望页面干净就把未知填成 0、已清仓或可以买。

## 14. CA 统一准确性与故障恢复

原 CA 文档仍为权威：单入口+内部进度（基础、权限、持有人/LP、钱包资金源、报告），完成须保留 Token-2022、真正 Owner Top10、资金归因、可信外部叙事、完整度验收。当前 Issue #165 的浏览器 Failed to fetch 必须先一次性只读核对 POST 接受、GET 轮询状态、Dashboard PID/worker、源 RPC、现有缓存/报告是否写入，不能没证据就判 RPC 429。

目标为有凭据的阶段性部分结果、持久任务身份和可读回已完成报告，区分连接中断、轮询中断、worker 错误、源 RPC 限额、报告保存错误。GET 失败不能触发新 POST 或无上限 RPC 重试；任何新增生产持久写入须单独授权，离线临时 fixture 先验收。同一真实 CA 在 Mac 完成一次从失败复现到根因、恢复后完整结果或有证据的 INCOMPLETE_EVIDENCE，不能仅把“Failed to fetch”换成“稍后重试”。

## 15. 顶部状态与真正的清理

顶栏只放 Frank 心跳、最后同步、当前异常和待处理通知、通知中心/清理入口。过去未发的“过期拦截15”放到历史通知，不能一直污染“监控正常”。成功发送的 V1/MC 邮件与历史 15 是不同集合，逐 ID 对账前不抵扣。

短期是经严格身份识别的、可逆浏览器级收起（PR #164 仍 Draft，尚未上线），不得视为数据库清理；长期归档先对账过期原因、attempts、回执和 Gmail message identity，经用户单独许可追加审计归档，不删除/重写原 outbox、不重放旧通知。旧 MC $30/小仓跟路径必须在独立通知授权范围处理，不能因 UI 隐藏而自称修复。

## 16. 用户 32 项逐条对应（状态均为 V3 未完成）

| 编号 | 承诺及原阶段 |
|---|---|
| 1、23 | 顶栏明确健康/异常与可逆清理，历史与当前分开 — D/通知审计 |
| 2、3、4 | 旧 WAIT、NO_BUY、重复结论不占“当前机会” — D |
| 5、6、8、9、11、13、14 | 删除冗长副标题/研究提醒/无用自述而保留后台规则 — D |
| 7、10、26、27 | 当前持仓和价差须可靠余额/slot/市场来源，历史模型进历史 — A/B |
| 12 | 五导航、明显分区和 Mint 联动 — D |
| 15、16、17 | 卖出事实 vs 卖后余额、分页而非每行“未核实” — B/D |
| 18 | 中文文案/Toast 句末无句号 — D |
| 19、24 | 统一钱包签名与交易流水、加载更多/帮助替代实现阈值长句 — B/D |
| 20、21、22 | 经济腿/混合核验状态/ATA/PASSIVE 中文化且分型严格 — B/D |
| 25、28、29 | 持仓与观察池整合、转账与市场交易分开 — B/D |
| 30、31 | 结束次数去重，历史和待核交易合并 — D |
| 32 | CA 单模式可恢复的真实失败处理 — CA/A/B |

这些是**设计归属**，不是宣称32项已编码或已验收。每一项最后须有固定源码 SHA、源证据和 Mac 实际结果，缺数据时应标 BLOCKED_BY_SOURCE。

## 17. D0→D4 开发顺序、业务出口与停止规则不变

| 单轮交付 | 实际用户问题 / 最小证据 | 对应原门禁 |
|---|---|---|
| 1 CA 真故障调查 | Mac 一次复现并取得 Failed to fetch 发生阶段与真实原因 | D0 + G2 |
| 2 CA 完整可恢复查询 | 单模式完成一例真实 Mint，断线能读回已有结果，不重复昂贵调用 | D3 + G2/G3 |
| 3 钱包当前真实余额 | 一个 Mint 两类 Token Program 全账户与 slots/时间、真实数量；若无获批来源则明确 blocker | D1/D2 + G2 |
| 4 交易事实修正 | 同一真实签名准确区分买卖/转账/ATA/混合状态 | D1/D2 + G2 |
| 5 V3 页面 | 五区导航与可信字段、中文/分页/去重，真实 Mac 一次有界验收 | D2/D3 + G3 |
| 6 通知历史清理 | 真实邮件对账、可逆收起；真归档另行授权和复核 | D/通知独立门禁 |
| 7 整体验收 | 固定 SHA、Claude 独立审查、生产依赖/回滚、用户单独授权后再安装 | D4 + G3 |

业务源事实的 P0/P1 缺口优先于视觉微调，P5 新风险真发送暂后置；已验收的 PR157 只读页面不能因本轮设计自动被替换。不得扩 RPC/付费 GMGN/增常驻服务、变更 V1/Loop/Gmail/outbox、签名或下单。

本节状态：DOCS_ONLY_FOR_CLAUDE_REVIEW / NO_MERGE / NO_DEPLOY / NO_NEW_RPC / NO_TRADES
