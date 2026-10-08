# Current Portfolio / Capital Map

Updated: 2026-10-08 Asia/Bangkok (CEX screenshots and direct-chain balance refresh)
Timezone: Asia/Bangkok

## Accounting rule

- Include only individual on-chain positions with a reliable marked value of **>= $1.00** in the displayed chain subtotal.
- Positions worth **< $1.00**, spam, claim-bait and unpriced unsolicited receipts are excluded from marked totals.
- User-confirmed CEX balances are classified by purpose; living-expense/rent money is not investment capital.
- Historical/private/pre-TGE rights remain separate from liquid/investable NAV.
- This is an asset-completeness snapshot, not Mission PnL.

## Canonical wallets

- EVM: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Solana: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- Sui: `0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`


## Fresh reference prices

Alchemy market-data snapshot at approximately 2026-10-08 14:13-14:15 Asia/Bangkok (2026-10-08 07:13-07:15 UTC):

- ETH: **$2,569.76**
- SOL: **$115.43**
- USDC: **$1.00049**
- BNB: **$769.65**, MON: **$0.026123**, HYPE: **$87.24**, POL: **$0.10172** (used only for below-$1 checks).

CEX values below are the exchange UI's displayed marks, not quantities inferred from an asset denomination. Price marks are reference only, not trade execution or PnL.

## Current on-chain assets >= $1


### Solana — DIRECT_CHAIN / finalized

- Wallet: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- USDC: **31.094071 USDC** (~**$31.11**). Standard SPL token account, finalized slot 454474225. The already-confirmed GANG 500 USDC sale deposit is excluded from wallet cash.
- Native SOL: **0.038163041 SOL** (~**$4.41**), finalized slot 454474225.
- SPL Token classic program inspected; only nonzero classic SPL holding is canonical USDC. The WSOL account has zero token balance.
- Token-2022 program inspected at finalized slot 454474732: four accounts with 1 unit each; two include `nonTransferableAccount`. No verified liquid >=$1 market mark; excluded.

### Ethereum — DIRECT_CHAIN

- Native ETH: **0.000904693862403571 ETH** (~**$2.32**).
- Canonical Ethereum USDC: **0** (no new verified material stablecoin holding).

### Ink — DIRECT_CHAIN

- Native ETH: **0.010133156790964273 ETH** (~**$26.04**).
- Also found Tydro Ink Points token units without a reliable realizable dollar quote; excluded.
- Known INK NFT rights remain unpriced; no NFT market price/ownership refresh implied by this token/native balance scan.


### Below-$1 chain balances — excluded

Fresh native RPC balances inspected, none reaches $1 at the appropriate native-token reference rate:

- Base: 0.000137238616283283 ETH.
- Unichain: 0.000020589846025254 ETH.
- Arbitrum: 0.000003959328931033 ETH.
- Optimism: 0.000065278581034767 ETH.
- Linea: 0.000283128973717299 ETH.
- World Chain: 0.00010673650432328 ETH.
- BNB Chain: 0.000006838245578456 BNB.
- Polygon: 0.2912959076072843 POL.
- Monad: 0.3817997 MON.
- HyperEVM: 0.000234033730511199 HYPE.
- MegaETH native: 0.000082071511230598 (network-native balance; below $1 on ETH-denominated interpretation, token identity/mark not independently reconfirmed).

Known Base canonical USDC dust and negligible L2 ERC-20 balances remain excluded. Many extra ERC-20/token-account receipts are spam-like or unpriced. The broad multi-chain portfolio API failed once with HTTP 500, and some token inventory reads were truncated; therefore this is a **verified-material-asset subtotal, not a claim of complete all-chain coverage**. Unsupported or unpriced tokens are UNRESOLVED, not zero.

### Sui — USER_CONFIRMED

- **SUI chain assets = 0**

This is the latest explicit user-confirmed state. Do not carry forward any old SUI position.

## CEX / off-chain capital buckets


### Binance — USER_CONFIRMED / PARKED INVESTMENT RESERVE

Latest user screenshot at approximately 2026-10-08 14:10 Bangkok:
- **631.20 USDT-equivalent estimated total assets** (exchange UI mark, not independently queried).
- Daily PnL screen approximately -0.00000167 USDT; not a basis for Mission PnL.
- Breakdown by coin/product or current Earn APR was **not provided** by this screenshot. Do not copy the old 600.866553 USDC balance or old 2.11% APR forward as if current.
- Accounting: included **$631.20 UI-estimated investment reserve**, subject to venue/account valuation and not necessarily entirely available/withdrawable; not authorized to trade.

### Bybit — USER_CONFIRMED / NON-INVESTMENT PERSONAL CASH

Latest user screenshot at approximately 2026-10-08 14:11 Bangkok:
- **435.948711 USDC** with UI value approximately **$436.12**.
- Account UI total: **$436.16** including near-zero/dust IMU (0.07 units displayed as $0.00), with **$0.13 available** and **$436.03 in use** per UI.
- Purpose: current living expenses and next month's rent.
- **Entire Bybit account excluded from Mission investable capital and portfolio subtotal**, whether available or in-use. No claim that the screenshot proves the in-use amount can be withdrawn on demand.

`BYBIT = EXCLUDED_FROM_INVESTMENT_CAPITAL`

## JUMP / Jumper Legion — REJECTED / REFUND COMPLETE

- application result: **UNSUCCESSFUL / REJECTED**
- final allocation: **0 JUMP / 0 USDC accepted**
- original deposit: **1,000 USDC**
- refund status: **COMPLETE ON-CHAIN**
- refund transaction: `0x3d3264417775aa9cf0bf5d83f69f00b2ada9e01852784bc52897264025c5e0b5`
- refund transfer timestamp: `2026-10-06T17:28:23Z`

Latest direct contract state read after refund:

- `investedCapital = 0`
- `hasSettled = false`
- `hasClaimedExcess = false`
- `hasRefunded = true`
- `vestingAddress = 0x0000000000000000000000000000000000000000`

The sale contract transferred **1,000 USDC** back to the participating wallet. Do not carry a pending JUMP sale asset or JUMP token position forward, and do not add the refund as a separate asset on top of current wallet/CEX balances.


## Current marked capital reference

### Material on-chain subtotal (verified liquid-asset marks only, GANG sale escrow excluded)

- Solana USDC: ~$31.11
- Solana native SOL: ~$4.41
- Ethereum ETH: ~$2.32
- Ink ETH: ~$26.04

**Verified material on-chain subtotal: ~ $63.88.**

### Investable but parked CEX capital

- Binance screenshot UI estimate: **$631.20** (USER_CONFIRMED, exact token allocation/unlock breakdown UNKNOWN).

### Combined known liquid/marked investment reference

**~ $695.08** = $63.88 verified marked on-chain assets + $631.20 Binance screenshot estimate.

This is mixed-freshness, approximate **capital completeness** and **not Mission PnL**. Binance availability is not independently verified. Other unsupported/unpriced holdings remain excluded, not assumed absent.

Separately, the **500 USDC GANG / The Syndicate escrow** remains a verified on-chain committed historical cost with settlement/allocation/refund pending. It was already deducted from wallet USDC and is **not** added to $695.08 as liquid NAV. Including committed cost purely for an exposure/funding-reference view yields approximately **$1,195.08**, which is **not** current realizable NAV.

**Bybit $436.16 account UI total, 435.948711 USDC: excluded personal living/rent funds.**

### GANG / Backable — verified ICO escrow, pending settlement

- Deposit: **500 USDC**, on 2026-10-08 12:57:48 Bangkok from canonical Solana wallet.
- Tx: `LLxbLZNJYKcWGchRt7QNwnx8UKs4gzu5rYC2CFbRWzm9FzjrCjFHaMbKeebKHZAc8gkcympJTqioHGp2f7ifYia`
- Individual FundingRecord: `GgFwSstgG9e6XDEWAc4wrcD8EqVaqHpzo7ScvNGEEQot`, committed=500, approved=0 (pre-settlement), token claim=false, refund=false.
- Token Mint: `syQqkspvb2PRr1meJ5pJDmhgxwc4hUou2TMjjrTmeta`; **no GANG public-sale tokens claimed yet**.
- Scheduled sale end: **2026-10-12 00:30:01 Bangkok**, but exact claim/refund availability remains unknown pending final close and completion.
- Accounting: removed 500 from liquid Solana USDC. The escrowed commitment is cost-basis tracking only; do not mark as a second 500 in NAV.
- Position detail: `crypto-300-profit-mission/positions/gang.md`.


### Personal cash excluded from investment

- Bybit: **435.948711 USDC** (account UI value ~**$436.16** including dust) for living expenses and next month's rent. Entire account excluded.

## Pre-TGE / private / points rights inventory

These entries preserve unresolved economic rights/cost bases and are not added to liquid NAV without a reliable current mark.

### Confirmed capital / acquisition-cost exposures still unresolved

| Project | User right / position | Historical cost / committed capital | Current state | Accounting treatment |
|---|---|---:|---|---|
| GANG / The Syndicate | Backable Solana v0.7 sale escrow, actual chain-verified 500 USDC committed on 2026-10-08; final GANG allocation and refundable excess pending sale completion | **$500** | Live until 2026-10-12 00:30:01 Bangkok; claim/refund only after contract state permits | Illiquid pre-settlement commitment; separate from wallet cash. See `positions/gang.md` |
| Reya | CoinList token-sale allocation | **$5,000** | pre-TGE / unresolved distribution | cost basis only; exclude from liquid NAV |
| Makina | Legion / ICO token allocation | **$1,000** | pre-TGE | cost basis only; exclude from liquid NAV |
| Block Stranding | presale / future token rights | **100 SOL** | pre-TGE | preserve native-unit cost; do not convert without explicit valuation refresh |
| Fortytwo | Echo seed / token-related rights | **$250** | pre-TGE / illiquid | cost basis only |
| OhBabyGames | Echo private / token-related rights | **$250** | unresolved liquidity / token event | cost basis only |
| 01.xyz / N1 | Echo investment rights plus legacy ecosystem rights | **$1,000** | final user-level conversion/liquidity unconfirmed | cost basis only |
| ForecastFDN | private / token-related entitlement | **$100** | pre-TGE / unresolved | cost basis only |
| Crusoe | Echo private equity / SPV rights | **$100** | illiquid private-market right | cost basis only |
| Apptronik | Echo private equity / SPV rights | **$100** | illiquid private-market right | cost basis only |
| Aalo Atomics | Echo private equity / SPV rights | **$100** | illiquid private-market right | cost basis only |
| Thalassa | Echo private equity / SPV rights | **$500** | illiquid private-market right | cost basis only |
| Figure | Echo private equity / SPV rights | **$1,000** | illiquid private-market right | cost basis only |
| 1X | Echo private equity / SPV rights | **$2,000** | illiquid private-market right | cost basis only |
| RepublicX / rTTOK / ByteDance economic exposure | 5,000 contingent payout notes, $1 principal each | **$5,000** | illiquid contractual note exposure | not direct ByteDance stock ownership; cost basis only |
| Surf Limited Edition NFT #691 | 1 NFT, pending delivery / airdrop | **$228** | delivery not independently verified | historical acquisition cost only |

Known dollar-denominated historical acquisition cost above: **$17,128**, plus **100 SOL** Block Stranding historical cost. JUMP is no longer included because the application was rejected and the 1,000 USDC deposit was refunded.

### Points / rewards / potential token rights

- StandX: **51,129.8 Final Points**
- Surf: **28,600 Points**
- Pond / JoinPond: **12,000 Points**
- TurboFlow: **12,000 Points; 2-account participation noted**
- MetaMask Rewards: **Season 1 Level 5**
- N1 / legacy 01, OpenSea, Polymarket, Base, Perena, Rho, Hylo, Tydro: historical participation/points rights exist; no current liquid value is assigned here.

## Explicit closed / excluded positions

- JUMP / Jumper Legion public sale: **rejected, 0 allocation, 1,000 USDC refunded**.
- humans& / Echo-Alpen: **CLOSED_FULLY_REFUNDED**.
- Credits / Visualize Value: fully cleared.
- UNICRED #230: no longer owned.
- SUI: 0 / fully cleared.
- PONS futures/spot: closed.
- XRP / Variational: closed.
- Assets below $1, spam, unknown/unpriced receipts: excluded under current rule.

## Monitoring policy

Routine wallet polling remains disabled.

Refresh this file only on explicit user request, after a material user-reported action, or when a verified event requires an ownership/balance check. Do not infer authorization for additional monitoring tasks.