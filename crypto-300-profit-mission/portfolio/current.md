# Mission Portfolio / Current Assets and Capital Classification

Updated: 2026-10-10 Asia/Bangkok (read-only wallet refresh; price observations around 2026-10-10 16:14 UTC)
Timezone: Asia/Bangkok
Portfolio authority: this file; operational status: `../state/latest.md`; performance attribution: `../performance/current.md`.

## Accounting and display policy (user-approved)

- **Include a separately identifiable asset in the displayed USD asset subtotal only when its independently supportable USD mark is >= $1.00.** Exactly $1.00 is included; less than $1.00 is excluded. Apply per asset/position, not by pooling unrelated dust.
- A balance lacking an independently supportable price is **UNPRICED / UNRESOLVED**, not proved to be worth zero or less than $1. Spam, impersonation and unsolicited claim-bait are excluded regardless of apparent face value.
- Keep quantities and evidence for tiny assets in historical/source records when relevant; do not display them as material holdings or sum them into the subtotal.
- Only directly confirmed wallet balances are `DIRECT_CHAIN`; CEX account figures are `USER_CONFIRMED` with their screenshot date. Unknown coverage or a failed provider is `UNAVAILABLE/UNRESOLVED`, never zero.
- Binance flexible USDC is parked investment reserve; **the entire Bybit account is personal living/rent cash and excluded from the Mission investment subtotal.**
- Pending escrow, token-sale rights, private assets, points and NFTs without an executable mark remain separate from liquid marked NAV; do not equate historical costs with current liquidation values.
- Wallet movements, CEX transfers, token unlocks, refunds and gross sale proceeds are not automatically PnL; do not double-count them or historical exited NFTs. No signing, redemption, exchange transfer or trading was performed.

## Canonical user wallets

- EVM across supported networks: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Solana: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- Sui: `0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`

Only these already authorized canonical wallets are in the present sweep. Wallet discovery/other accounts have **not** been asserted complete.

## 2026-10-10 independently rechecked on-chain material balances

### Solana / finalized RPC

- `getBalance` returned **38,163,041 lamports = 0.038163041 SOL**, slot **455317409**; at Binance Spot SOLUSDT **110.44** the indicative mark is **~$4.21** (USDT proxy, approximate USD).
- `getTokenAccountsByOwner` (classic SPL) returned **58.047629 USDC**, canonical mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`, account `AaHmxVnUryLCrSr32zxrDGzfafXTvuHATURZbBy6XQ6A`, finalized slot **455317412**. Alchemy independently reported USDC/USD **1.00082** at 2026-10-10 16:10 UTC, indicative mark **~$58.10**.
- Other three classic SPL accounts showed zero token balance (including one wrapped SOL account). Token-2022 returned **four accounts each holding one indivisible token**, two marked `nonTransferableAccount`; no independently verifiable >=$1 executable market value. Keep them **UNPRICED/EXCLUDED**, not absent.
- Confirmed **material, separately marked Solana subtotal: ~$62.31**. Price-level proxies are not trade fills or available liquidity.

### EVM / latest native RPC

On October 10, the canonical EVM wallet's native balances remain individually below $1 using contemporaneous Binance Spot ETHUSDT **2510.52**, BNBUSDT **750.93**, and Alchemy POL/USD **0.10174**, MON/USD **0.024658**, HYPE/USD **85.81**:

| Chain | Fresh native balance | Treatment |
| --- | ---: | --- |
| Ethereum | 0.000190807320080339 ETH | < $1; excluded |
| Base | 0.000137238616283283 ETH | < $1; excluded |
| Arbitrum | 0.000003959328931033 ETH | < $1; excluded |
| Optimism | 0.000065278581034767 ETH | < $1; excluded |
| Unichain | 0.000020589846025254 ETH | < $1; excluded |
| Ink | 0.000003101575720485 ETH | < $1; excluded |
| Linea | 0.000283128973717299 ETH | < $1; excluded |
| World Chain | 0.000106736504323280 ETH | < $1; excluded |
| BNB Chain | 0.000006838245578456 BNB | < $1; excluded |
| Polygon | 0.2912959076072843 POL | < $1; excluded |
| Monad | 0.3817997 MON | < $1; excluded |
| HyperEVM | 0.000234033730511199 HYPE | < $1; excluded |
| MegaETH | 0.000082071511230598 native units | denomination/mark unresolved; excluded |

- Ethereum canonical USDC balance confirmed **0** by direct filtered `getTokenBalances`.
- EVM ERC-20 coverage is **INCOMPLETE**: Alchemy full listings for Ethereum/Base/Optimism/BNB/Polygon exceeded response limits; Blockscout returned partial priced pages for Ethereum, Optimism and Arbitrum (none independently verified at >=$1 in those checked pages), with Base/Polygon blocked by exhausted PRO credits. Several other networks contain unpriced ERC-20 receipts. No exhaustive token-portfolio zero or no-other-assets assertion.
- Ink Tydro Ink Points remain present, but lack a reliable executable quote; no invented USD value.
- Ethereum Credits collection `0x97630aA70AB14ed9883B41dAfccBc11349723043` **0 NFTs held**, Alchemy owner-specific read at block **26163166**, 2026-10-10 16:15:59 UTC.
- Unichain UNICRED contract `0xf60de24F228dc7Ca6fF025958d2eE3A956ED88E5` **0 NFTs held**, Alchemy owner-specific read at block **60900610**, 2026-10-10 16:16:09 UTC.
- Other Ethereum NFTs/Ink NFT rights lack an independently verified sale quote and are excluded from USD NAV, **not asserted zero inventory**. Solana enhanced owner-asset enumeration failed; classic SPL/Token-2022 RPC checks above succeeded.

### Sui / user-confirmed, not chain verified

The latest explicit user-confirmed Sui account state remains **0**, with no fresh supported Sui-native RPC result in this refresh. Label `USER_CONFIRMED`, never `DIRECT_CHAIN`.

## Off-chain accounts and capital classification

### Binance / last user screenshot, 2026-10-09 22:18 Bangkok

- Screenshot account total **~656.07 USDT-equivalent**; **655.55477225 USDC flexible Earn** is the underlying holding, not a second asset. Accrued displayed interest **0.8927689 USDC is already included**.
- `USER_CONFIRMED_HISTORICAL_2026-10-09`. No connected private Binance read on October 10, so today's real balance/withdrawability **UNVERIFIED**. The cited promo APR is variable and not used to accrue invented earnings.
- Classified `INVESTMENT_RESERVE`, but parked in Earn, subject to withdrawal and platform conditions.

### Bybit / last user screenshot, 2026-10-09 22:18 Bangkok

- Historical screenshot **353.173611 USDC (~$353.42 displayed)**, including 353.087100 Earn / 0.086456 unified / 0.000055 funding.
- `USER_CONFIRMED_HISTORICAL_2026-10-09`. No live account read.
- **BYBIT = EXCLUDED_FROM_INVESTMENT_CAPITAL** in its entirety, even if an individual position would otherwise exceed $1. Reserved for personal living and rent.

## Material capital reference (not realized profit)

| Bucket | USD reference | Freshness / status |
| --- | ---: | --- |
| Solana USDC + SOL (each >= $1) | **~$62.31** | 2026-10-10 finalized chain, contemporaneous approximate quotes |
| Binance flexible Earn | **~$656.07** | 2026-10-09 user screenshot, NOT 2026-10-10 live |
| **Cross-source indicative investment reference** | **~$718.38** | mixed freshness; **not** audited full NAV or Mission PnL |
| GANG / The Syndicate escrow | **500 USDC historical commitment** | 2026-10-10 FundingRecord account re-read; illiquid/pending and excluded from above |
| Bybit living/rent cash | **~$353.42 historical UI mark** | excluded completely |

The GANG FundingRecord `GgFwSstgG9e6XDEWAc4wrcD8EqVaqHpzo7ScvNGEEQot` was still present, owner `moontUzsdepotRGe5xsfip7vLPTJnVuafqdUWexVnPM`, at Solana finalized slot **455317963**. The stored funding amount's little-endian 8-byte field remains **500,000,000 raw USDC units = 500 USDC**. This confirms committed historical escrow; **final allocation/claim/refund and recoverability still UNCONFIRMED** pending the raise's settlement. The scheduled close remains **2026-10-12 00:30:01 Asia/Bangkok** per prior recorded launch contract, not a guaranteed claim time. See `positions/gang.md`.

JUMP / Jumper Legion **rejected / 0 allocated / 1,000 USDC already refunded**, per existing on-chain settlement record `positions/jump.md`. Do not add its refund or expected token position again. The refund transaction was previously verified, **not re-executed/re-fetched in this October 10 snapshot**.

## Current status vs historic provenance

The original six Credits NFT positions are **all exited** and UNICRED #230 is **not owned**. PONS, XRP/Variational and old meme trading sleeves remain historical/closed; do not report them as open holdings. Other private/ICO/points rights below are a separate **historical rights and cost register**, not an immediately liquid wallet or a claim of October 10 re-verification.

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