# Current Portfolio / Capital Map

Updated: 2026-10-09 22:18-22:24 Asia/Bangkok (user CEX screenshots + fresh finalized/native token wallet RPC reads)
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

Direct price snapshots 2026-10-09 around 22:20 Asia/Bangkok; reference marks, not execution prices:
- Binance public spot BTC/ETH/SOL/BNB/HYPE tickers consulted; ETH **$2,487.96**, SOL **$109.53**, BNB **$738.30**.
- Alchemy USD token-price API: USDC **$1.00079**, ETH $2,488.68, SOL $109.413, BNB $737.96, MON $0.024592, POL $0.09883, HYPE $85.36.
- This refresh applies SOL $109.53 and ETH $2,487.96 from Binance, USDC $1.00079 and noncore POL/MON from Alchemy. Mixed-second timestamps; approximate marks only.
- CEX USD equivalents below are the exchange **user screenshot's marks**, not recomputed extra principal or PnL.

## Current on-chain assets >= $1


### Solana — DIRECT_CHAIN / finalized

- Canonical wallet: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`.
- **58.047629 USDC** in canonical Solana USDC classic SPL token account `AaHmxVnUryLCrSr32zxrDGzfafXTvuHATURZbBy6XQ6A` (token mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`). Value **~$58.09** using USDC $1.00079. Finalized slot `454907396`, independent token account balance read.
- **0.038163041 SOL** native (~**$4.18** using SOL $109.53). Finalized slot `454906751`. The native SOL amount is unchanged versus 2026-10-08, although its USD mark changed.
- Compared with October 8 Solana USDC 31.094071, balance increased by **26.953558 USDC**. This is a **wallet balance delta only**, not classified as yield, trading PnL, refund or external income without transaction evidence.
- Classic SPL token accounts checked finalized slot `454906753`: canonical USDC is the only positive token amount; WSOL and two others show zero.
- Token-2022 program `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb` queried finalized slot `454906985`: four distinct one-unit token accounts; two carry `nonTransferableAccount` extensions. No independent redeemable price >= $1. Excluded from marked subtotal, **not treated as absent**.
- The previously committed **500 USDC GANG sale escrow** is not part of the 58.047629 wallet USDC balance. No double count.

### Ethereum — DIRECT_CHAIN

- Native ETH: **0.000190807320080339 ETH**, approximately **$0.47** at $2,487.96, **EXCLUDED** under individual position < $1 rule. This replaces the October 8 native balance of 0.000904693862403571 ETH.
- Canonical Ethereum USDC `0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48`: fresh direct ERC-20 balance **0**.
- Token inventory endpoint returned >8KB and truncated in one provider response; some unsolicited/historical ERC-20 records remain **UNRESOLVED**. No unpriced receipt is assigned $0 or included.

### Ink — DIRECT_CHAIN

- Native ETH: **0.000003101575720485 ETH**, approximately **$0.0077** at $2,487.96, **EXCLUDED**. The October 8 previous balance of 0.010133156790964273 ETH (~$25 at current price) is superseded. No cause or destination is inferred from balances alone.
- Tydro Ink Points token `0x40abd730cc9da34a8ee9823feabdba35e50c4ac7` present, but Alchemy contract quote returned **price not found**; **UNPRICED / EXCLUDED**, not zero balance.
- Known INK NFT rights stay unpriced; no refreshed executable NFT sale quote.

### Below-$1 chain balances — excluded

Fresh direct native RPC October 9 confirmed the following individually below $1, prices as listed in reference section:

- Ethereum: 0.000190807320080339 ETH (~$0.47).
- Ink: 0.000003101575720485 ETH (~$0.0077).
- Base: 0.000137238616283283 ETH (~$0.34).
- Unichain: 0.000020589846025254 ETH (~$0.05).
- Arbitrum: 0.000003959328931033 ETH (~$0.01).
- Optimism: 0.000065278581034767 ETH (~$0.16).
- Linea: 0.000283128973717299 ETH (~$0.70).
- World Chain: 0.00010673650432328 ETH (~$0.27).
- BNB Chain: 0.000006838245578456 BNB (~$0.005).
- Polygon: 0.2912959076072843 POL (~$0.029).
- Monad: 0.3817997 MON (~$0.009).
- HyperEVM: 0.000234033730511199 HYPE (~$0.020).
- MegaETH native: 0.000082071511230598 (assuming ETH-equivalent ~$0.20; underlying native denomination not independently re-verified; omit from NAV).
- Arbitrum canonical USDC 1 raw smallest unit (0.000001 USDC); Base canonical USDC 252 raw smallest units (0.000252 USDC). Excluded.
- Some other token accounts were found across networks, but their decimals/asset identities and independently realizable prices are incomplete; they are **UNRESOLVED, NOT ZERO**. Broad Alchemy multichain enumeration and several large per-network lists truncated at response limits. Blockscout sampled Ink/Arbitrum/Optimism and partial Ethereum, but failed on Base/Polygon due to API credits; several chains lack coverage. Do not assert exhaustive no-assets on those chains.
- No individual confirmed ERC-20 holding with independently verifiable value >= $1 was added to this snapshot. Unsupported or unknown ERC-20s/NFTs remain outside marked subtotal pending actual identity/price verification.


### Sui — USER_CONFIRMED

- **SUI chain assets = 0**

This is the latest explicit user-confirmed state. Do not carry forward any old SUI position.

## CEX / off-chain capital buckets


### Binance — USER_CONFIRMED / PARKED INVESTMENT RESERVE

Latest user screenshots: **2026-10-09 approximately 22:18 Bangkok**, Savings/Earn screen:
- **656.07 USDT estimated TOTAL ASSETS** (exchange's display mark, approximately USD $656.07), superseding October 8 UI estimate of 631.20.
- Actual position: **655.55477225 USDC**, one **Flexible Earn** holding (one product).
- App shows **annual rate up to 4.22%**, variable and not guaranteed; cumulative interest displayed **0.8927689 USDC** (included in held USDC; **DO NOT add again**).
- The separate **BFUSD auto-subscription enabled, APR 2.58%** banner is **not a separate proved BFUSD holding**. Do not add notional BFUSD assets.
- UI-implied USDC-to-USDT mark is embedded in the displayed 656.07; do not treat 655.55477225 USDC plus 656.07 USDT as separate assets.
- Previous October 8 UI reference: 631.20; this screen increases UI-estimated value by **24.87 USDT**. Difference is not proof of interest/trading profit or external transfer.
- Categorization: **USER_CONFIRMED / INVESTMENT RESERVE IN EARN**. Entire displayed mark included in investable reference, subject to current platform availability/withdrawal terms. No orders, Earn redemption, subscriptions or transfers authorized by screenshot.

### Bybit — USER_CONFIRMED / NON-INVESTMENT PERSONAL CASH

Latest user screenshot: **2026-10-09 approximately 22:18 Bangkok**:
- USDC total **353.173611 USDC**, UI net valuation approximately **$353.42** at indicated index price $1.0007.
- Savings/Earn **353.087100 USDC** (99.97% on UI).
- Unified trading **0.086456 USDC** (~$0.08, excluded by < $1 policy if displayed separately).
- Funding account **0.000055 USDC** (~$0.00, excluded).
- Displayed cumulative PnL **+$0.24 (+0.07%)** is Bybit's UI account data, not Mission PnL and not counted as additional asset.
- Previous screenshot showed 435.948711 USDC ($436.16 UI account); changed amount is **not** inferred to be an investment transfer or realized loss.
- **The ENTIRE Bybit wallet/account is explicitly excluded** from Mission investment capital, liquid NAV, $300 budget, and capital reference. Retained solely as living-expense and next-month rent capital.

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

### Verified individual liquid assets >= $1 on-chain (direct RPC, GANG sale escrow excluded)

- Solana USDC: **58.047629 USDC** (~**$58.09**).
- Solana SOL: **0.038163041 SOL** (~**$4.18**).
- Ethereum ETH, Ink ETH and all other individually confirmed native balances have fallen below the $1 rule; excluded.
- No freshly price-verified ERC-20/Token-2022 asset >= $1 added. Unpriced tokens/NFTs remain unresolved, not presumed valueless.

**Verified material on-chain subtotal: ~$62.27.**

### Binance investment reserve

- Binance screenshot UI total: **~$656.07**.
- Underlying asset: **655.55477225 USDC in flexible Earn**, cumulative interest already included.

### Combined known marked investment reference

**~$718.34 = ~$62.27 direct chain material positions + $656.07 Binance exchange UI valuation.**

This is mixed-source, mixed-freshness, **not Mission PnL**. It is not a guarantee that the full Earn position is immediately withdrawable. Any unsupported/unpriced tokens, illiquid NFTs and pre-TGE/private rights remain outside this marked reference.

**Separately**, the original **500 USDC GANG / The Syndicate** commitment remains an illiquid pre-settlement historical cost and is already absent from current wallet USDC. An exposure-plus-historical-cost view is **~$1,218.34 = ~$718.34 + $500**, **NOT current liquidation NAV** and not two separate 500 USDC assets.

**Excluded Bybit personal cash: 353.173611 USDC (~$353.42 UI valuation), investment contribution $0.**


### GANG / Backable — verified ICO escrow, pending settlement

- Deposit: **500 USDC**, on 2026-10-08 12:57:48 Bangkok from canonical Solana wallet.
- Tx: `LLxbLZNJYKcWGchRt7QNwnx8UKs4gzu5rYC2CFbRWzm9FzjrCjFHaMbKeebKHZAc8gkcympJTqioHGp2f7ifYia`
- Individual FundingRecord: `GgFwSstgG9e6XDEWAc4wrcD8EqVaqHpzo7ScvNGEEQot`, committed=500, approved=0 (pre-settlement), token claim=false, refund=false.
- Token Mint: `syQqkspvb2PRr1meJ5pJDmhgxwc4hUou2TMjjrTmeta`; **no GANG public-sale tokens claimed yet**.
- Scheduled sale end: **2026-10-12 00:30:01 Bangkok**, but exact claim/refund availability remains unknown pending final close and completion.
- Accounting: removed 500 from liquid Solana USDC. The escrowed commitment is cost-basis tracking only; do not mark as a second 500 in NAV.
- Position detail: `crypto-300-profit-mission/positions/gang.md`.


### Personal cash excluded from investment

- Bybit: **353.173611 USDC** (2026-10-09 screenshot UI value ~**$353.42**) for living expenses and next month's rent. Entire account excluded.

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