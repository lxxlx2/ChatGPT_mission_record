# 地址分析 / 449 个 EVM 地址研究队列与分批进度

Updated: 2026-10-18 Asia/Bangkok
Research status: `READ_ONLY / PARTIAL_RESULTS / CLI_OFFLINE_TESTED`
Source manifest: [449 addresses](../sources/oooooyoung-evm-449-source-snapshot.json), original blob `954f3aba66be21911dd627fa40dd3dd0a9fd1d26`.

## Canonical queue position

- Total **449** distinct EVM addresses, fixed order; batch size 20; **23** batches.
- **PnL review frontier = Batch 001** (source rows **001–020**); **activity screening frontier = Batch 006 completed, Batch 007 next**. The BNB Chain 30-day signed-activity census for these 20 has been finished, with exact fixed height window `0x74cf256` → `0x7a4ca36`. **13/20** had wallet-signed BSC transactions, **7/20** had none. This alone does not prove who bought/sold or which chains are inactive.
- **2026-10-18 three-chain screening extension:** [machine-readable nonce evidence](../evidence/batch-001-three-chain-30d-nonce-screen.json) covers Ethereum 20/20 (13 active, 1,331 signed), Base 20/20 (10 active, 1,515 signed), alongside BSC 20/20. Three-network union 15/20 signed; rows 008/009/010/011/013 three-network signed-zero. Other EVM chain coverage and all-wallet PnL are **incomplete**.
- **Verified realized token roundtrip = 3:** row016 RTX5090 closed position **+0.226099333116 BNB** (~**+$162.86** using contemporary Binance BNBUSDT candles); see [batch-001](../batches/batch-001.md) and [structured evidence](../evidence/batch-001-row-016-rtx5090-roundtrip.json). This remains a single-token roundtrip, not the entire wallet PnL. Rows002/004 sauce additionally closed with **+0.156828105278687674 BNB** (about +$118.86) and **+0.154215798043203099 BNB** (about +$116.96). [Exact sauce evidence](../evidence/batch-001-rows-002-004-sauce-roundtrips.json). No confirmed negative token roundtrip yet, but losses cannot be assumed zero.
- **2026-10-18 Batch 002 screen:** [three-chain raw nonce evidence](../evidence/batch-002-three-chain-30d-nonce-screen.json) for rows021–040, BSC 12/20 with 18,766 signed transactions, Ethereum 12/20 with 2,884, Base 12/20 with 3,411; union 13/20, three-chain signed-zero 7/20. Batch 002 trade and PnL audit NOT_STARTED.
- **Historical BSC/Ethereum/Base nonce-screen coverage = 120/449 addresses**; Batches 001–006 each covered 20 wallets on all three specified chains. [Standardized first-120 address status](../evidence/coverage-001-120-normalized.json) and [reconciliation report](coverage-001-120.md) replace 100-wallet figures for the current screening frontier; the 100-wallet archive remains unchanged. [Standardized first-100 historical screening roster](../evidence/coverage-001-100-standardized-signed-screen.json) reconciles all five source artifacts against the immutable address list, and [cohort report](coverage-001-100.md) describes the usable screening results and unresolved PnL. These are *signed census* checkpoints only, not end-to-end EVM network coverage or PnL audits.
- **2026-10-18 closed-token source replay:** [standardized three-position evidence](../evidence/closed-token-replay-source-check-20261018.json) and [test/replay status](closed-token-source-replay-qa-20261018.md). New isolated Python replay/negative-fixture tests **5/5 passed** (Git blobs verified). This validates existing source arithmetic and refuses invalid costs/inventory, **not** new onchain receipts or whole-wallet PnL. Real losing positions remain UNRESOLVED.
- **2026-10-18 generalized FIFO ledger V1 offline QA:** [code](../tools/transaction_ledger.py), [20 offline tests](../tests/test_transaction_ledger.py), [historical saved sauce source replay](../evidence/ledger-v1-row002-source-replay.json), [failure/QA details](ledger-v1-fifo-qa-20261018.md). Strictly *SOURCE CLAIM REPLAY*: validates inventory, FIFO, date cutoffs, negative results and fail-closed provenance. No independent onchain receipt verification and no newly realized loss; comprehensive per-wallet PnL remains unresolved. This is the current primary development track, ahead of extending batch counts.
- **Completed full-wallet 30-day multi-EVM PnL = 0/449**; **completed full-wallet lifetime PnL = 0/449**. No ranking / success claim from incomplete source.
- **Read-only CLI:** [nonce census + integer-wei token replay prototype](../tools/address_analysis.py), [tests](../tests/test_address_analysis.py), and [fixed block hashes](../sources/frozen-30d-bsc-eth-base-blocks.json); **Original committed tests FAILED import (exit 1)**; after fixing the test import path, **6 offline tests PASS (exit 0)** on Python 3.13 with exact Git blobs. [Reproduction evidence](../evidence/read-only-cli-unittest-import-qa-20261018.md). Live CLI-to-RPC replay and Mac E2E remain NOT VERIFIED. No wallet PnL promoted.
- **Batch 003 screening completed 2026-10-18:** [exact three-chain historical nonce report](../evidence/batch-003-three-chain-30d-nonce-screen.json) for source rows041–060: BSC 3/20 signed (273), Ethereum 3/20 signed (251), Base 5/20 signed (44). **Three-chain union 6/20 signed**, 14/20 three-chain signed-zero only. No confirmed swap or PnL from this batch, and new CLI was NOT used to collect these provider responses.
- **Batch003 signed-transaction classification probe:** [raw hashes and selectors](../evidence/batch-003-low-frequency-transaction-classification.json) cover direct ERC20/native transfers, approvals, two lending-like calls and two successful but not cashflow-reconciled router executions on Base #051. No additional confirmed profit/loss. These remain PNL_UNRESOLVED pending trade-ledger reconstruction.
- **Batch 004 (rows 061–080) completed three-chain nonce census:** [raw nonce pairs](../evidence/batch-004-three-chain-30d-nonce-screen.json), [report](../batches/batch-004.md). BSC **18/20** signed (4,865 tx), Ethereum **15/20** (1,558), Base **13/20** (956), union **18/20**, rows 061/062 three-chain signed-zero only. [Selected transaction method evidence](../evidence/batch-004-low-frequency-transaction-examples.json) distinguishes approvals and native transfers from undecoded paid contract calls. **No new verified closed token PnL.**
- **Batch 005 rows 081–100 historical three-chain screening complete:** [nonce evidence](../evidence/batch-005-three-chain-30d-nonce-screen.json), [report](../batches/batch-005.md), BSC 3/20 signed (753 tx), Ethereum 5/20 (349), Base 3/20 (168), union 6/20 active on checked networks. [Selected real-method call evidence](../evidence/batch-005-bounded-transaction-method-probe.json) shows ERC20 approvals and undecoded payable calls, with **no confirmed new token gains or losses**.
- **Batch 006 rows 101–120 three-chain signed screen COMPLETE:** [original nonce pairs](../evidence/batch-006-three-chain-30d-nonce-screen.json), [batch report](../batches/batch-006.md). BSC 16/20 signed (19,216 tx), Ethereum 9/20 (155), Base 7/20 (129), union 16/20. [Bounded call-method evidence](../evidence/batch-006-bounded-transaction-probe.json) classifies selected ERC20 transfers and undecoded paid calls, with no verified new PnL.
- **Next coverage batch = 007** (source rows **121–140**, nonce census NOT_STARTED). Batch001–006 trading/cost-basis/loss audits remain open.
- **Next available work:** prioritize bounded true swap and loss-token audit for low-transaction Batch001 rows001/003/006/007/015 and other positions in 002/004, Batch002 low-count addresses, and Batch003 rows044/045/050/051/060. Signed-census coverage next Batch007 121–140. The Batch004 and Batch005 sampled paid contract calls remain PNL_UNRESOLVED until logs, fees, token flow and historical inventory close. Preserve all pending costs and loss candidates for future reconciliation. High-frequency rows014/016–020 and 022/027/029/038 must have bounded pagination and explicit `DEFERRED` reason/cursor/re-entry condition, not block completion of later source rows. Polygon/Arbitrum/other EVM chain discovery pending. Signed nonces are not PnL.

## Batch registry

| Batch | Source rows | Screening | PnL / completion |
| --- | --- | --- | --- |
| 001 | 001–020 | BSC + Ethereum + Base each 20/20; other EVM pending | PARTIAL: 3 closed profitable token roundtrips, 20 wallet-level PnL unresolved |
| 002 | 021–040 | BSC + Ethereum + Base each 20/20; other EVM pending | PARTIAL: three-chain screen complete, trading/PnL NOT_STARTED |
| 003 | 041–060 | BSC + Ethereum + Base each 20/20; other EVM pending | PARTIAL: signed screen complete; trade and PnL NOT_STARTED |
| 004 | 061–080 | BSC + Ethereum + Base each 20/20; other EVM pending | PARTIAL: signed census complete; token and wallet PnL unresolved |
| 005 | 081–100 | BSC + Ethereum + Base each 20/20; other EVM pending | PARTIAL: three-chain nonce screen complete, wallet PnL unresolved |
| 006 | 101–120 | BSC + Ethereum + Base each 20/20; other EVM pending | PARTIAL: signed activity screened; executed trades and wallet PnL unresolved |
| 007 | 121–140 | NOT_STARTED | NOT_STARTED |
| 008 | 141–160 | NOT_STARTED | NOT_STARTED |
| 009 | 161–180 | NOT_STARTED | NOT_STARTED |
| 010 | 181–200 | NOT_STARTED | NOT_STARTED |
| 011 | 201–220 | NOT_STARTED | NOT_STARTED |
| 012 | 221–240 | NOT_STARTED | NOT_STARTED |
| 013 | 241–260 | NOT_STARTED | NOT_STARTED |
| 014 | 261–280 | NOT_STARTED | NOT_STARTED |
| 015 | 281–300 | NOT_STARTED | NOT_STARTED |
| 016 | 301–320 | NOT_STARTED | NOT_STARTED |
| 017 | 321–340 | NOT_STARTED | NOT_STARTED |
| 018 | 341–360 | NOT_STARTED | NOT_STARTED |
| 019 | 361–380 | NOT_STARTED | NOT_STARTED |
| 020 | 381–400 | NOT_STARTED | NOT_STARTED |
| 021 | 401–420 | NOT_STARTED | NOT_STARTED |
| 022 | 421–440 | NOT_STARTED | NOT_STARTED |
| 023 | 441–449 | NOT_STARTED | NOT_STARTED |

## Phase-based closure criteria

- `SCREENED_BSC`: all fixed-bounded BSC nonce checks done and recorded.
- `SCREENED_EVM`: target-chain discovery adequately covered with explicit limitations, and outgoing signed swaps separated from passive inbounds.
- `PNL_PER_TOKEN_VERIFIED`: every labeled closed trade includes contract and exact buy/sell quantity, acquisition cost, quote receipts, fees, reference FX price, verified chain hashes; losses included equally with gains.
- `BATCH_FINAL`: each wallet either has complete audited 30d+long-term ledger or an explicit `DEFERRED` status with a *bounded reason and re-entry condition*. A batch may only close as `PARTIAL_WITH_DEFERRED` if the outstanding item list is explicit and carried forward; it must never disappear.
- This run is **NOT `BATCH_FINAL`** and no automatically generated final artifact exists. It was a manual read-only research checkpoint and not a Mission $300 trade task success claim.

## Source, accounting and safety invariants

The original file's '聪明钱', developer, high-profit, early/insider tags are unverified claims; no endorsement or strategy approval. Wallet funding is not profit, passive ERC20 airdrop not trading, one profitable token not wallet PnL. Multi-chain transfers and opening inventory are necessary for lifetime / rolling PnL; unsupported price gets `UNRESOLVED`. Use official Binance historical price only for FX mark at the contemporaneous minute, report indicative USD separately. No production trading, monitor activation, automation, Mac deployment or Gmail changes authorized.
