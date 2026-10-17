# 地址分析 / oooooyoung EVM 钱包按批盈利审计

Updated: 2026-10-18 Asia/Bangkok
Status: `RESEARCH_ONLY / FIRST_BATCH_BSC_ACTIVITY_SCREENED / PNL_INCOMPLETE`
Scope: independent Mission research module, no connection to the existing PR #40 BSC address modeling or live Frank/Monster signals.

## Objective and fixed universe

- Source: [nopapername/oooooyoung, oooooyoung evm聪明钱.json](https://github.com/nopapername/oooooyoung/blob/main/oooooyoung%20evm%E8%81%AA%E6%98%8E%E9%92%B1.json).
- Source Git blob SHA `954f3aba66be21911dd627fa40dd3dd0a9fd1d26`, as read on 2026-10-18; **449 unique, syntactically valid EVM addresses**, original labels are *unverified source annotations*.
- Stable imported manifest: [sources/oooooyoung-evm-449-source-snapshot.json](sources/oooooyoung-evm-449-source-snapshot.json). All subsequent batches MUST use this immutable snapshot and its original source ordering, not any new version of the external repository.
- Batch size **20**, rows 1–20 = batch 001, rows 21–40 = batch 002, ..., rows 441–449 = batch 023. No skipped candidates and no reordering to manufacture a high-PnL sample. At most one immutable batch final artifact per genuinely completed research round; preliminary screens are explicitly `PARTIAL`.
- Frozen BSC 30d window uses blocks `0x74cf256 → 0x7a4ca36` (2026-09-17T21:12:12Z to 2026-10-17T21:12:13Z). The Ethereum and Base matched historical block/nonce windows appear in [three-chain evidence](evidence/batch-001-three-chain-30d-nonce-screen.json). This supersedes the preliminary lower block `0x74ced05` and its unfrozen latest upper bound. Cross-network window timestamps differ by at most 2 seconds.
- Long-term window means **all verifiable history of the identical address**, beginning at its first funding/nonce and involving its opening inventory cost. Do not pretend source-list addition date is acquisition date.

## Research stages and explicit gates

1. **Roster / batch freeze:** source name, address, group, chain. Never promote nickname tags such as '内幕', '高盈利' or '开发者' to verified identity.
2. **Recent activity:** query EVM signed transaction nonce at fixed start and end blocks separately on BNB, Ethereum, Base and any other chain relevant to the address. Native/ERC-20 passive transfers, approval-only transactions and spam-token airdrops are never counted as trade evidence. `signed_nonces>0` means *signed transaction activity* only, not proven profitable DEX trades. Avoid labeling another EVM chain inactive from BSC alone.
3. **Per-token trade ledger:** decode actual router/pair logs and net quote assets in successful receipts, reconcile exact token contract+decimals, token in/out, gas, buy tax, sell tax, source/destination. Match opening inventory from pre-window trades and cross-wallet funding. Detect and separate deployment allocations, mint, self-transfers, dust bait, farm or airdrop.
4. **PnL:** `realized = verified executed exit proceeds - attributable opening/acquisition cost of tokens sold - direct swap/gas expenses`; separate WBNB/native BNB, USDT/USDC/USD1 and output in USD **at each transaction timestamp**, not today's price. Unspent inventory remains open; mark unrealized only when supported by current executable liquidity. Long-term and 30-day realized PnL use the same actual opening cost and cross-period rules; selling pre-window inventory during the window counts only with its historic basis.
5. **Independent review and closure:** report explicit profit tokens *and loss tokens*, total trading count, completed position count, unknown balances, double-counting checks, historical proof links and all block range/source cutoffs. If pagination, RPC limits, non-standard tokens or inconsistent balances prevent completion, mark `PNL_UNRESOLVED` and keep a deferred queue, never generate a false number.

Coverage status codes: `NOT_STARTED`, `BSC_SIGNED_ACTIVE`, `BSC_SIGNED_ZERO`, `TRADE_CONFIRMED`, `TOKEN_ROUNDTRIP_VERIFIED`, `PNL_UNRESOLVED`, `CHALLENGED`, `COMPLETE`. A `BSC_SIGNED_ZERO` label does **not** imply EVM-wide inactivity.

## Progress

- [state/progress.md](state/progress.md): single resumable queue pointer, per batch completion truth.
- [batches/batch-001.md](batches/batch-001.md): first 20 source addresses, fixed-height signed activity census on BSC, Ethereum and Base, plus one audited token roundtrip; other EVM and full-wallet PnL pending. Its status is **PARTIAL** until all multi-chain coverage and cost-basis checks pass.
- Rows 21–449 retain `NOT_STARTED`, including wallets whose ad-hoc checks occurred in old chats; prior unstructured examples do not count as audited batch results until independently re-entered.

## Breadth-first development cadence and user outcome

Final product: **reproducible wallet research with recent signed/trade activity, profit tokens and loss tokens, 30-day and lifetime realized PnL, cost basis, fees, proof links and coverage confidence**. A fully audited wallet ranking is allowed only for complete underlying wallet ledgers. A single winning token roundtrip never makes a winning-wallet score.

1. **Coverage:** process all 449 immutable source rows in original 20-address batch order. Check reproducible fixed-height signed activity on BSC/Ethereum/Base first, label additional network gaps explicitly; a BSC zero must not suppress Ethereum/Base candidates. Keep active, checked-network-zero and RPC-error distinct.
2. **PnL evidence:** prioritize low-volume addresses for demonstrable full profitable and losing token roundtrips. Independently reconcile execution, inventory, quote receipts, fees, prior acquisition and USD marks at execution timestamps; keep 30-day and lifetime wallet total unresolved when incomplete.
3. **Bounded high-frequency work:** restrict any one round to a documented page/transaction budget. When a wallet cannot be completed, leave `DEFERRED` with exact missing pages/cost basis, last cursor, next condition and ownership. Continue to subsequent rows/batches in original order while preserving that queue. Mark `PARTIAL_WITH_DEFERRED` only with existing review and batch-closure gates.
4. **Usable output:** first deliver a coverage and verified-token table (positive *and* negative), then fully-audited-wallet views and historical comparisons. Expose status `VERIFIED`/`PARTIAL`/`UNRESOLVED`, never approximate leaderboard by treating missing data as zero.
5. **Implementation and validation:** after this frozen baseline, add a reusable read-only collector, deterministic ledger replay, tests, failure/negative fixtures and independent review. No claiming that static manual reports constitute an automated, production-ready scanner.

Keep throughput of the whole 449-wallet universe visible. Do not repeatedly focus on a single unusual wallet or cosmetic edge condition to the detriment of the end-to-end research outcome.

## Boundaries

No wallet signing, swaps, follow trading, live orders, Gmail, LaunchAgent, dashboards or automation. `PRODUCTION_TRADING=NO_GO`, Frank and Monster unchanged. Original Mission PnL and wallet snapshots are separate from this third-party address intelligence research. Keep every failed/negative result, no cherry-picking and no made-up wallet profits. Research is observation-only.
