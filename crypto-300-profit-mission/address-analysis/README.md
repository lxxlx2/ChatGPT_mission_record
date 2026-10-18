# 地址分析 / oooooyoung EVM 钱包按批盈利审计

Updated: 2026-10-18 Asia/Bangkok
Status: `RESEARCH_ONLY / BATCH_001_TO_006_THREE_CHAIN_SCREENED / WHOLE_WALLET_PNL_INCOMPLETE`
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
- [batches/batch-004.md](batches/batch-004.md): rows061–080, 18/20 signed on at least one of BSC/Ethereum/Base, wallet PnL unresolved. [Nonce evidence](evidence/batch-004-three-chain-30d-nonce-screen.json), [sample transaction methods](evidence/batch-004-low-frequency-transaction-examples.json).
- [batches/batch-005.md](batches/batch-005.md): rows081–100 BSC/Ethereum/Base fixed-window nonce screen, six of twenty signed-active on at least one checked chain, no complete wallet PnL; [raw nonce evidence](evidence/batch-005-three-chain-30d-nonce-screen.json), [actual selected call types](evidence/batch-005-bounded-transaction-method-probe.json).
- [state/coverage-001-100.md](state/coverage-001-100.md) and [normalized first-100 wallet status JSON](evidence/coverage-001-100-standardized-signed-screen.json): unified non-PnL screening result, strict address/source reconciliation and network provenance, including the Batch001 BSC nonce-pair gap.
- [batches/batch-006.md](batches/batch-006.md): rows101–120 signed census complete on BSC/Ethereum/Base, 16/20 active on at least one network, no whole-wallet PnL; [nonce proof](evidence/batch-006-three-chain-30d-nonce-screen.json) and [limited transaction method samples](evidence/batch-006-bounded-transaction-probe.json).
- [Current standardized 120-address screen](state/coverage-001-120.md) and [machine-readable source-matched 120-wallet JSON](evidence/coverage-001-120-normalized.json).
- [Closed-token saved evidence replay](tools/closed_token_index.py), [negative-sample and bad-input tests](tests/test_closed_token_index.py), [QA limits](state/closed-token-source-replay-qa-20261018.md), and [actual-source cross-check JSON](evidence/closed-token-replay-source-check-20261018.json). This **does not** produce wallet PnL, nor verify new onchain transactions.
- [Batch003 low-frequency transaction method evidence](evidence/batch-003-low-frequency-transaction-classification.json): approvals and transfers are excluded from inferred swap count; two router executions remain unknown PnL.
- [Rows 002/004 sauce closed-position accounting](evidence/batch-001-rows-002-004-sauce-roundtrips.json): costs, proceeds, timestamps and limitations.
- Rows 121–449 remain `NOT_STARTED` for fixed-window BSC/Ethereum/Base signed screening. Batches 001–006 rows 001–120 have signed screening, **74/120** at least one checked network signed and **46/120** signed-zero on these three only. All whole-wallet 30d and lifetime PnL incomplete; source identity labels unverified.

## Breadth-first development cadence and user outcome

Final product: **reproducible wallet research with recent signed/trade activity, profit tokens and loss tokens, 30-day and lifetime realized PnL, cost basis, fees, proof links and coverage confidence**. A fully audited wallet ranking is allowed only for complete underlying wallet ledgers. A single winning token roundtrip never makes a winning-wallet score.

1. **Coverage:** process all 449 immutable source rows in original 20-address batch order. Check reproducible fixed-height signed activity on BSC/Ethereum/Base first, label additional network gaps explicitly; a BSC zero must not suppress Ethereum/Base candidates. Keep active, checked-network-zero and RPC-error distinct.
2. **PnL evidence:** prioritize low-volume addresses for demonstrable full profitable and losing token roundtrips. Independently reconcile execution, inventory, quote receipts, fees, prior acquisition and USD marks at execution timestamps; keep 30-day and lifetime wallet total unresolved when incomplete.
3. **Bounded high-frequency work:** restrict any one round to a documented page/transaction budget. When a wallet cannot be completed, leave `DEFERRED` with exact missing pages/cost basis, last cursor, next condition and ownership. Continue to subsequent rows/batches in original order while preserving that queue. Mark `PARTIAL_WITH_DEFERRED` only with existing review and batch-closure gates.
4. **Usable output:** first deliver a coverage and verified-token table (positive *and* negative), then fully-audited-wallet views and historical comparisons. Expose status `VERIFIED`/`PARTIAL`/`UNRESOLVED`, never approximate leaderboard by treating missing data as zero.
5. **Implementation and validation:** after this frozen baseline, add a reusable read-only collector, deterministic ledger replay, tests, failure/negative fixtures and independent review. No claiming that static manual reports constitute an automated, production-ready scanner.

Keep throughput of the whole 449-wallet universe visible. Do not repeatedly focus on a single unusual wallet or cosmetic edge condition to the detriment of the end-to-end research outcome.

## Read-only deterministic CLI prototype (not yet Mac/network accepted)

The pinned [RPC nonce collector](tools/address_analysis.py) and [offline unittest suite](tests/test_address_analysis.py) are restricted to this independent address-analysis module. Tests: original committed test file actually **FAILED** with `ModuleNotFoundError` (exit 1). A one-line correction to test import path (`tools/`) yields a repaired blob `d6b7b8f912846f24d1a88e4168fda7a204553d86` that passed **6/6** offline unit tests with exit 0 on Python 3.13; collector program SHA was unchanged. [Failure/retest evidence](evidence/read-only-cli-unittest-import-qa-20261018.md). This is a **local developer test**, not a live RPC E2E result or wallet-level PnL audit.

The script uses only the Python standard library. It requires explicit read-only endpoint URLs through environment variables `ADDR_ANALYSIS_RPC_BSC`, `ADDR_ANALYSIS_RPC_ETH`, `ADDR_ANALYSIS_RPC_BASE`. No keys are stored in Git. It uses [immutable block boundaries](sources/frozen-30d-bsc-eth-base-blocks.json) and verifies both boundary block hashes before querying each wallet's nonce. Provider failure is represented as `UNRESOLVED_RPC`, never zero, and exits nonzero when any requested chain has unresolved rows. Per-chain signed deltas and their exact nonce bases are included; no swaps or profits are inferred.

From this module root, once you have access to your own RPC URLs in environment variables:

```zsh
python3 -m unittest discover -s tests -v
python3 tools/address_analysis.py --source sources/oooooyoung-evm-449-source-snapshot.json --windows sources/frozen-30d-bsc-eth-base-blocks.json --batch 3 --output /tmp/address-analysis-batch-003-nonce.json
```

**The command above is a documented example, not a claim Batch 003 has run.** The `replay_closed_token` helper performs exact integer-wei arithmetic for positive, zero and negative closed-token outcomes. Its `basis_verified`, `receipt_success` and `provenance_complete` flags must be independently proven from RPC receipts, price and inventory; the helper only consumes assertions supplied by an analyst and does *not* verify blockchain evidence by itself. A manual token ledger lacking these proofs remains `PNL_UNRESOLVED`; synthetic loss tests are not claims of real-world wallet losses.

New offline historical saved-source replay CLI: `python3 tools/closed_token_index.py --manifest sources/oooooyoung-evm-449-source-snapshot.json --rtx evidence/batch-001-row-016-rtx5090-roundtrip.json --sauce evidence/batch-001-rows-002-004-sauce-roundtrips.json`. This prototype only replays the saved three positions, and its 5/5 offline synthetic tests do not count as actual-chain loss discovery. Next engineering gate: independently replay complete token transaction receipts, track open positions and losses, run real historical RPC/CLI E2E and obtain independent external review before claiming a profitable-wallet research tool.

## General FIFO execution-ledger V1 (offline research gate)

- [`tools/transaction_ledger.py`](tools/transaction_ledger.py) implements exact integer/Fraction FIFO for normalized per-token BUY/SELL execution claims. It handles pre-window acquisition with in-window exit, partial exits and losses, reconciles balances after each event, and keeps unspent cost basis separate.
- [`tests/test_transaction_ledger.py`](tests/test_transaction_ledger.py): **20/20 offline tests passed** after fixing an observed same-block ordering defect. These tests include synthetic losses and failures; they do not prove new real-chain profits/losses.
- [Historical row002 sauce normalized input](fixtures/batch001-row002-sauce-executions.json) and [archived source-claim replay result](evidence/ledger-v1-row002-source-replay.json): +0.156828105278687674 BNB, the **same existing** saved roundtrip, not an additional winning position. Real Git row002 and recorded event values were compared against the existing evidence.
- [Exact local QA and limitations](state/ledger-v1-fifo-qa-20261018.md). The CLI in isolation was run with a synthetic manifest for 448 other address rows, so no end-to-end claim of original 449-row manifest ingestion is authorized.
- `CLAIM_REPLAY_ONLY` means event receipts, inventory completeness and fees were **asserted by the normalized evidence**. This tool does not fetch receipts or verify those assertions on chain; it never returns completed wallet PnL or USD estimates.
- Next major delivery gate: independent read-only transaction+receipt normalization, matched gas/native/quote outputs, verified historical inventory, actual positive AND negative closed trades, and complete-wallet accounting. Do not start production or promote a win-only wallet ranking.

## Complete receipt fact extractor V1 (read-only)

The [receipt evidence extractor](tools/receipt_probe.py) is the **first actual RPC/receipt-facing** piece of the transaction-ledger pipeline. It accepts full transaction+receipt JSON either from a user-provided HTTPS RPC environment variable or two local files. It matches the immutable 449-wallet manifest row, EVM chainId, transaction and block identity, successful receipt status, ERC20 Transfer logs and actual gasSpent in native wei.

- [17 offline failure/transfer/gas tests](tests/test_receipt_probe.py) passed in an isolated standard-library Python runtime, exact Git blobs matched the tested files.
- Four **actual authenticated historical RPC receipts** were read fully and checked against wallet addresses/chain/tx hashes: [compact receipt fixtures](fixtures/complete-rpc-receipts-four-transactions.json) and [direct-chain read evidence](evidence/receipt-probe-four-real-rpc-check-20261018.json). They were approval, WBNB transfer, USDC transfer and native ETH transfer; none demonstrates a profitable trade.
- [QA and blocked-swap limitations](state/receipt-facts-v1-qa-20261018.md): the connected provider truncated all three selected sauce BUY/SELL receipts to 8098 characters, so they **could not be independently reverified** this turn. The Python URL RPC code has not passed Mac or live URL E2E, though the historical connected provider reads were real.
- Output status is `RECEIPT_FACTS_ONLY`, **not** `TOKEN_ROUNDTRIP_VERIFIED`. Native internal return value requires additional trace and cashflow proofs; quoted ERC20 transfers require trade intent, correct historical basis, and gas FX evidence. The facts extractor does not automatically promote events into the FIFO ledger.

This development gate is more important than additional signed-nonce screening. Batch007 stays queued as `NOT_STARTED`; all full-wallet PnL remains unresolved.


## Base transaction fee correction and lending classification

- Fixed [receipt facts parser](tools/receipt_probe.py): Base total transaction fee includes **L2 execution gas plus receipt L1 data fee**. Missing or invalid Base `l1Fee` yields `PNL_UNRESOLVED`, not an understated cost. BSC/Ethereum fee handling is unchanged.
- The existing row045 Base USDC-transfer historical audit recorded only L2 gas (382277850000 wei). [Correction](evidence/base-l1-fee-and-lending-facts-20261018.json): L1 fee 3235250376 wei, combined 385513100376 wei ETH. Historical source remains immutable.
- Added [two complete Base row051 lending receipts](fixtures/base-row051-aave-supply-withdraw-receipts.json) and [independently checked token/gas evidence](evidence/base-l1-fee-and-lending-facts-20261018.json). Supply and withdraw on a specific Aave Base pool are classified as **lending, not swaps**; observed underlying USDC net -1 raw unit across these two calls is **not** a verified token loss.
- [25 isolated Python tests pass](tests/test_receipt_probe.py); see [QA limitations](state/base-fee-and-lending-qa-20261018.md). The historical sauce swap receipts remain truncated and independent native cashflow tracing remains unresolved. No new trade PnL or whole-wallet completion claimed.


## Historical sauce transfer-log/BNB block correlation (new independent RPC facts)

For fixed-source rows **002/004**, the [narrow Transfer-event + historic balance/nonce evidence](evidence/batch001-sauce-rows002-004-narrow-transfer-native-block-20261018.json) now independently corroborates both sauce token closed cycles. Instead of relying on truncated whole receipts, Alchemy read-only `eth_getLogs` used the token address plus indexed wallet from/to topics and exact heights; `eth_call(balanceOf)`, `eth_getBalance`, and `eth_getTransactionCount` also verified the same relevant historical block states. Each sale emits **two** outgoing token Transfer logs that must be summed. The two wallets have block-level BNB differences matching the saved values, not new paid wins.

**Critical:** native receipt-by-transaction attribution remains `UNRESOLVED_WITHOUT_INTERNAL_TRACE`. Block-level wallet BNB changes may include external same-block receipts, and complete router receipt JSON is truncated through the current provider. Do not change their PnL evidence to fully transaction-audited or promote either wallet to a ranked profitable-wallet candidate.

[Read-only saved-evidence verifier](tools/verify_block_roundtrip.py) + [12/12 isolated offline regression tests](tests/test_verify_block_roundtrip.py) check original row identities, historical nonce deltas, ERC20 event signatures and hashes, both sell logs, zero reverse filter results, balance snapshots and block-level arithmetic. [Evidence limits](state/sauce-rows-002-004-independent-log-block-recheck-20261018.md) note that Python's real-original-449-manifest CLI E2E has not yet been demonstrated. This is an **evidence corroboration**, not new whole-wallet PnL.


## Transfer-cost provenance gate (Batch001 #002/#007/#015)

The [complete bounded BSC/ERC20 transfer observations](evidence/batch001-rows002-007-015-erc20-cost-origin-20261018.json) confirm two *externally received then fully transferred* token positions and one *partly distributed, still held* position. Row015 HODL and row007 BSC-ETH both have unknown original economic acquisition costs. Row002 FTR has five inbound transfers, **six Transfer events in one outbound transaction**, and an open balance. Two recipients correspond to frozen source rows001/006; this proves a flow, not common control.

The [saved-evidence gate](tools/verify_transfer_provenance.py) and [10 offline synthetic/invariant tests](tests/test_verify_transfer_provenance.py) match original source identities, transfer direction/pages, integer token balances, native-block/nonce snapshots and known source-list recipients; outcomes remain `ARCHIVED_FLOW_CONSISTENT_ONLY`, not profit/loss. [Actual-source analysis and next requirements](state/batch001-erc20-cost-origin-20261018.md). Focus next on real basis and proceeds proof, not further nonce expansion or edge-case-only work.


## Cost-bearing origin and distribution provenance gate (HODL rows015/016)

[Upstream BSC distribution evidence](evidence/batch001-hodl-funded-distributor-lineage-20261018.json) tracks **two paid router inputs**, one distributor transaction with **six recipients**, and the full HODL token outflow of **source rows015/016**, plus the distributor's undistributed inventory. The upstream address spent a total native `value` of **0.425046148539676102 BNB** across buys; observed native block balance decrease **0.426177349239676102 BNB**. These are **group-origin facts**, *not a valid per-recipient cost basis or proof of shared control*. Row016's first HODL exit height includes **four wallet-signed operations**, so the block BNB delta is not specific sale proceeds.

[Saved-event group conservation gate](tools/lineage_gate.py) / [10 tested fail-closed scenarios](tests/test_lineage_gate.py) never allocate upstream cost or produce recipient profit without economic-ownership and transaction-level quote proofs. [Audit and queued missing evidence](state/batch001-hodl-funded-distribution-20261018.md). Reusable primitive for recipient transfers; do **not** keep expanding hand-coded token edge cases in place of building the general true-PnL ledger.

## Boundaries

No wallet signing, swaps, follow trading, live orders, Gmail, LaunchAgent, dashboards or automation. `PRODUCTION_TRADING=NO_GO`, Frank and Monster unchanged. Original Mission PnL and wallet snapshots are separate from this third-party address intelligence research. Keep every failed/negative result, no cherry-picking and no made-up wallet profits. Research is observation-only.
