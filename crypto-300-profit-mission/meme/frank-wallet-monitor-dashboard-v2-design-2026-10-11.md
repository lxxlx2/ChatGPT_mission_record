# Frank 链上观察台 V2：真实账本、持续观察池与 GMGN 功能对照技术设计

Date: 2026-10-11 Asia/Bangkok
Status: **DATA_AND_ARCHITECTURE_DESIGN_COMPLETED / IMPLEMENTATION_NOT_STARTED / REAL_REPLAY_NOT_PASSED / PRODUCTION_UNCHANGED**
Parent task: $300 → $3000 Mission, Frank/Meme lane.
Inputs: `frank-wallet-ui-data-audit-2026-10-11.md` (real read-only chain samples, screenshot discrepancies and first-party GMGN research); `ca-analysis-unified-accuracy-acceptance.md` (manual CA comprehensive research); `FRANK_LOCAL_SIGNAL_V1_POLICY.md` (frozen production alert semantics).
Objective: **user can see and understand every materially relevant Frank trade, wallet position and token under observation, while the existing production BUY/WAIT and Gmail rules stay strictly unchanged.** A read-only local dashboard; no signed swap execution or paid GMGN requirement.

## 1. Product boundaries: separate truth from advice

Implement three *independent* domain layers; do not re-use a narrow signal candidate query as the data source of the whole page:

A. **Wallet fact ledger**: all address-touching finalized signatures and decoded wallet-owned economic movements, signed swaps, passive/active transfers, claims/rewards, token account creations, failed transactions and unresolved items, with raw proof and observable slot/time. This layer answers **what Frank actually did / received / transferred**.

B. **Wallet position and observation portfolio**: every relevant mint seen in A (including still-held and exited history) has an inventory ledger, acquisition/disposal facts, duration, watch reason, current market snapshot, optional PnL if cost is reconstructible, review status, last activity and persistence. This layer answers **what tokens must we still look at**.

C. **Frozen follow-signal engine**: consumes only its existing independently confirmed active-swap facts and frozen ACCUMULATION/MULTIPLE/reentry/WAIT/NO_BUY gates, maintains independently sourced wallet-signal observations, live notification, outcome and dedupe; **does not define, suggest or assume any user order amount or execution method**. This layer answers **would a bounded Frank-follow policy trigger**. **No code or threshold change to C without separately approved review.**

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
- Quotes for a specific trade amount must be explicitly requested by the user. Neither the generic CA page nor the Frank follow engine may choose a default order amount, generate a preset execution quote, or decide trade sizing. If no user-defined amount exists, executable entry price, size-dependent impact and hypothetical PnL remain **NOT_ASSESSED**; pattern/source monitoring remains independent.

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

The UI has **three top-level navigation views**, with no extra trading buttons:

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
- Preserve narrative and holder-role evidence. Never inject a default fixed-notional Jupiter quote or transform market data into a user order recommendation.

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

**Design decisions and requirements in this document have been specified, not coded or operationally accepted.** The 300-3000 governing conversation owns data definition and design gate; a separate implementation effort must perform D0→D4 in order. No unrelated code refactor, no automatic duplicate monitor, no paid GMGN API, no local RPC transaction signing, no unapproved runtime modification. Preserve existing user-approved frozen Frank signals and notification conditions unchanged.
