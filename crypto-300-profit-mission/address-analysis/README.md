# 地址分析 / oooooyoung EVM 钱包按批盈利审计

Updated: 2026-10-18 Asia/Bangkok
Status: `RESEARCH_ONLY / BATCH_001_002_003_THREE_CHAIN_SCREENED / WHOLE_WALLET_PNL_INCOMPLETE`
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
- [batches/batch-001.md](batches/batch-001.md): first 20 source addresses, BSC/Ethereum/Base screening and 3 closed profitable single-token roundtrips; whole-wallet PnL PARTIAL.
- [batches/batch-002.md](batches/batch-002.md): next 20 addresses, three-chain nonce screening complete; swap/PnL NOT_STARTED. [Fixed-height JSON](evidence/batch-002-three-chain-30d-nonce-screen.json).
- [batches/batch-003.md](batches/batch-003.md): rows041–060 fixed-height BSC/Ethereum/Base nonce coverage; 6/20 signed on at least one checked network and no audited trade PnL. [Raw evidence](evidence/batch-003-three-chain-30d-nonce-screen.json).
- [Batch003 low-frequency transaction method evidence](evidence/batch-003-low-frequency-transaction-classification.json): approvals and transfers are excluded from inferred swap count; two router executions remain unknown PnL.
- [Rows 002/004 sauce closed-position accounting](evidence/batch-001-rows-002-004-sauce-roundtrips.json): costs, proceeds, timestamps and limitations.
- Rows 061–449 remain `NOT_STARTED` for frozen-window BSC/Ethereum/Base signed screening. Batch 001–003 rows 001–060 are screened on those three chains, while all full-wallet PnL and many per-token trade ledgers remain incomplete.

## Breadth-first development cadence and user outcome

Final product: **reproducible wallet research with recent signed/trade activity, profit tokens and loss tokens, 30-day and lifetime realized PnL, cost basis, fees, proof links and coverage confidence**. A fully audited wallet ranking is allowed only for complete underlying wallet ledgers. A single winning token roundtrip never makes a winning-wallet score.

1. **Coverage:** process all 449 immutable source rows in original 20-address batch order. Check reproducible fixed-height signed activity on BSC/Ethereum/Base first, label additional network gaps explicitly; a BSC zero must not suppress Ethereum/Base candidates. Keep active, checked-network-zero and RPC-error distinct.
2. **PnL evidence:** prioritize low-volume addresses for demonstrable full profitable and losing token roundtrips. Independently reconcile execution, inventory, quote receipts, fees, prior acquisition and USD marks at execution timestamps; keep 30-day and lifetime wallet total unresolved when incomplete.
3. **Bounded high-frequency work:** restrict any one round to a documented page/transaction budget. When a wallet cannot be completed, leave `DEFERRED` with exact missing pages/cost basis, last cursor, next condition and ownership. Continue to subsequent rows/batches in original order while preserving that queue. Mark `PARTIAL_WITH_DEFERRED` only with existing review and batch-closure gates.
4. **Usable output:** first deliver a coverage and verified-token table (positive *and* negative), then fully-audited-wallet views and historical comparisons. Expose status `VERIFIED`/`PARTIAL`/`UNRESOLVED`, never approximate leaderboard by treating missing data as zero.
5. **Implementation and validation:** after this frozen baseline, add a reusable read-only collector, deterministic ledger replay, tests, failure/negative fixtures and independent review. No claiming that static manual reports constitute an automated, production-ready scanner.

Keep throughput of the whole 449-wallet universe visible. Do not repeatedly focus on a single unusual wallet or cosmetic edge condition to the detriment of the end-to-end research outcome.

## Read-only deterministic CLI prototype (not yet Mac/network accepted)

The pinned [RPC nonce collector](tools/address_analysis.py) and [offline unittest suite](tests/test_address_analysis.py) are restricted to this independent address-analysis module. Tests: **6/6 passed** in the isolated Python 3 environment on 2026-10-18 (local offline synthetic fixtures + two known sauce cashflow figures). This is a **local developer test**, not a live RPC E2E result or wallet-level PnL audit.

The script uses only the Python standard library. It requires explicit read-only endpoint URLs through environment variables `ADDR_ANALYSIS_RPC_BSC`, `ADDR_ANALYSIS_RPC_ETH`, `ADDR_ANALYSIS_RPC_BASE`. No keys are stored in Git. It uses [immutable block boundaries](sources/frozen-30d-bsc-eth-base-blocks.json) and verifies both boundary block hashes before querying each wallet's nonce. Provider failure is represented as `UNRESOLVED_RPC`, never zero, and exits nonzero when any requested chain has unresolved rows. Per-chain signed deltas and their exact nonce bases are included; no swaps or profits are inferred.

From this module root, once you have access to your own RPC URLs in environment variables:

```zsh
python3 -m unittest discover -s tests -v
python3 tools/address_analysis.py --source sources/oooooyoung-evm-449-source-snapshot.json --windows sources/frozen-30d-bsc-eth-base-blocks.json --batch 3 --output /tmp/address-analysis-batch-003-nonce.json
```

**The command above is a documented example, not a claim Batch 003 has run.** The `replay_closed_token` helper performs exact integer-wei arithmetic for positive, zero and negative closed-token outcomes. Its `basis_verified`, `receipt_success` and `provenance_complete` flags must be independently proven from RPC receipts, price and inventory; the helper only consumes assertions supplied by an analyst and does *not* verify blockchain evidence by itself. A manual token ledger lacking these proofs remains `PNL_UNRESOLVED`; synthetic loss tests are not claims of real-world wallet losses.

Next engineering gate: replay Batch 001/002 snapshots against live historical RPC, validate request retry/failure behavior, decode all executed swap legs plus gas and inventory in an independent ledger, and obtain external review before any claim of automatic profitable-wallet evaluation.

## Boundaries

No wallet signing, swaps, follow trading, live orders, Gmail, LaunchAgent, dashboards or automation. `PRODUCTION_TRADING=NO_GO`, Frank and Monster unchanged. Original Mission PnL and wallet snapshots are separate from this third-party address intelligence research. Keep every failed/negative result, no cherry-picking and no made-up wallet profits. Research is observation-only.
