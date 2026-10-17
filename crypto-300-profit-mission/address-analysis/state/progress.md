# 地址分析 / 449 个 EVM 地址研究队列与分批进度

Updated: 2026-10-18 Asia/Bangkok
Research status: `READ_ONLY / PARTIAL_RESULTS`
Source manifest: [449 addresses](../sources/oooooyoung-evm-449-source-snapshot.json), original blob `954f3aba66be21911dd627fa40dd3dd0a9fd1d26`.

## Canonical queue position

- Total **449** distinct EVM addresses, fixed order; batch size 20; **23** batches.
- **Current in-progress batch = 001** (source rows **001–020**). The BNB Chain 30-day signed-activity census for these 20 has been finished, with exact fixed height window `0x74cf256` → `0x7a4ca36`. **13/20** had wallet-signed BSC transactions, **7/20** had none. This alone does not prove who bought/sold or which chains are inactive.
- **2026-10-18 three-chain screening extension:** [machine-readable nonce evidence](../evidence/batch-001-three-chain-30d-nonce-screen.json) covers Ethereum 20/20 (13 active, 1,331 signed), Base 20/20 (10 active, 1,515 signed), alongside BSC 20/20. Three-network union 15/20 signed; rows 008/009/010/011/013 three-network signed-zero. Other EVM chain coverage and all-wallet PnL are **incomplete**.
- **Verified realized token roundtrip = 1:** row016 RTX5090 closed position **+0.226099333116 BNB** (~**+$162.86** using contemporary Binance BNBUSDT candles); see [batch-001](../batches/batch-001.md) and [structured evidence](../evidence/batch-001-row-016-rtx5090-roundtrip.json). It is one trade, **not** the wallet's aggregate profit.
- **Completed full-wallet 30-day multi-EVM PnL = 0/449**; **completed full-wallet lifetime PnL = 0/449**. No ranking / success claim from incomplete source.
- **Next available work:** Batch 001 real swap/cost reconstruction for low-count rows 001–004 / 006–007 / 015 across the relevant active chains. For high-frequency 014 / 016–020 bound each research round and record exact unresolved transaction ranges, trade basis and re-entry condition in a `DEFERRED` queue before moving in source order. Polygon/Arbitrum/other EVM chain discovery pending; do not mark zero on three chains as globally inactive. No signed nonce is a confirmed profitable trade.

## Batch registry

| Batch | Source rows | Screening | PnL / completion |
| --- | --- | --- | --- |
| 001 | 001–020 | BSC + Ethereum + Base each 20/20; other EVM pending | PARTIAL: 1 closed token roundtrip, 20 wallet-level PnL unresolved |
| 002 | 021–040 | NOT_STARTED | NOT_STARTED |
| 003 | 041–060 | NOT_STARTED | NOT_STARTED |
| 004 | 061–080 | NOT_STARTED | NOT_STARTED |
| 005 | 081–100 | NOT_STARTED | NOT_STARTED |
| 006 | 101–120 | NOT_STARTED | NOT_STARTED |
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
