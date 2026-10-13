# Mission Portfolio / Current Assets and Capital Classification

Updated: 2026-10-12 Asia/Bangkok (GANG fully exited, Binance/Bybit/OKX screenshots and finalized Solana holdings)
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

## Latest material assets: GANG fully exited, updated CEX and OKX — 2026-10-12

Snapshot chronology: user screenshots **2026-10-12 around 01:52–01:53 Bangkok**; direct Solana RPC finalized **slot 455757417/455757419**, shortly after the user's full sale. Preserve distinctions `DIRECT_CHAIN` / `USER_CONFIRMED_SCREENSHOT` / `UNRESOLVED`. Per-asset USD value **< $1 EXCLUDED**. No new signing, purchase, transfer or account access.

### Canonical Solana main wallet — direct finalized

- Canonical wallet `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`: **471.716759 USDC** in `AaHmxVnUryLCrSr32zxrDGzfafXTvuHATURZbBy6XQ6A` (Solana SPL classic mainnet), slot 455757417. This **includes the already refunded 19.507520 USDC ICO excess AND the 384.281918 USDC GANG sale proceeds**; do not add either again.
- **0.012905142 SOL** native (12,905,142 lamports), finalized slot 455757419. Approximate independent Alchemy SOL/USD quote **$111.43** at 2026-10-11T18:56Z => **~$1.44**, individually above $1 threshold.
- **0 GANG**, previously held 8,008.208 GANG; former user token account `5XBM2iEibBNAVBMjPYb9Deh8ibm4CCqZrbqk8n7TpGJo` no longer has any positive GANG (classic SPL complete owner inventory).
- GANG full-exit confirmed transaction https://solscan.io/tx/2cGKrncYix2AK2kAqtepgWJ1ipBsuH95TYwPHohRhAEkkbNRiwDbUUzLUyTG5RhA5D1xdi4Cbj9PUajsx8gGJNDk, finalized slot 455756451 at 2026-10-12 01:51:52 Bangkok. Pre-sell finalized slot 455756240: 8,008.208 GANG / 87.434841 USDC; post-sell 0 GANG / 471.716759 USDC. **Realized net cash proceeds 384.281918 USDC**, GANG approved cost **480.492480 USDC**, GANG-specific **realized loss −96.210562 USDC** before SOL network gas. Original $500 total includes separate 19.507520 returned escrow; no outstanding GANG position/escrow. Details in `../positions/gang.md`.

### OKX Web3 account 01 — user screenshot

2026-10-12 ~01:52 account UI shows **$484.64 total** and gain `+$409.69 (+546.69%) / 1 day`; the latter is **wallet-app display statistic NOT verified portfolio investment profit or GANG profit**, and can reflect incoming transfers. Do not copy it to Mission PnL. Displayed items:
- USDC **471.76**, separately confirms the Solana wallet's 471.716759 USDC (not a second 471.76 USDC holding).
- ETH **0.002403 ETH ≈ $6.08** (user screenshot). The canonical EVM wallet's directly queried native balances across previously recorded EVM networks do **not** sum to this amount, therefore **ETH balance ownership/account mapping across OKX Web3 identities is not independently reconciled**. Retain as `USER_CONFIRMED`, do not assert `DIRECT_CHAIN`, and do not add same underlying funds to EVM chain subtotals twice.
- SOL **0.012905 ≈ $1.43**, independently aligns with 0.012905142 SOL on the canonical Solana wallet (not additional SOL).
- TRX **3.3847 ≈ $1.11**, screenshot-confirmed; Tron/native address not independently RPC-verified this turn.
- STRK shows **$0.55**, explicitly **excluded** under < $1 threshold.
- **Identifiable, individually >=$1 screenshot positions sum to approx $480.38** ($471.76 USDC + $6.08 ETH + $1.43 SOL + $1.11 TRX). OKX headline $484.64 exceeds that by $4.26, including visible $0.55 STRK and **$3.71 of undisclosed/cropped components with individual denominations unavailable**. Do **NOT** add that unexplained difference to the filtered investment subtotal, nor claim all are dust or zero.
- OKX Web3 screenshot may aggregate assets from more than the canonical EVM/Solana addresses; only Solana sub-balances are independently matched. Mark extra ETH/TRX as dated `USER_CONFIRMED_SCREENSHOT` until wallet addresses/smart accounts are reconciled.

### Binance flexible USDC Earn — current user screenshot (investment capital)

- **695.70724404 USDC in Flexible Earn**, one position. Binance screenshot estimated account total **696.34 USDT-equivalent (~$696.34)**. These refer to **one asset**, not 695.70724404 + $696.34.
- Product rate banner up to **4.01% variable APR**, screenshot cumulative interest **1.04524069 USDC**, already contained in the current USDC holding; do not double count.
- Difference from prior 2026-10-09 Binance snapshot 655.55477225 USDC is **+40.15247179 USDC balance change** (UI USD total changes 656.07 → 696.34, +40.27 estimated dollars). No claim it was all interest, GANG proceeds or investment PnL.

### Bybit personal living/rent money — excluded (2026-10-12 user screenshot)

- **445.724250 USDC**, UI valuation **~$446.12**, components Earn **397.147100**, funding **48.490694**, unified trading **0.086456**, sum reconciles.
- Screenshot Bybit PnL +$0.40 is account's display, not Mission profit; life/rent funds **fully excluded from investable funds and all subtotal calculations**.
- Previous screenshot 353.173611 is historical only, no attribution of increase to investment return.
- `BYBIT = EXCLUDED_FROM_INVESTMENT_CAPITAL` unchanged.

### Current defensible filtered investment reference (mixed evidence)

- **Binance screenshot UI mark ~$696.34** plus **OKX screenshot visible individually-qualified assets ~$480.38** = **~$1,176.72 identified investment holdings** at 2026-10-12 around 01:52–01:53 Bangkok.
- **Not a complete wallet NAV**: additional OKX balance discrepancy $4.26 has not been attributed by denomination; unidentified tokens/NFTs and unsupported chain inventory excluded. Screenshot source mixed with directly confirmed Solana USDC/SOL. Do not add canonical direct Solana holdings again to OKX screenshot subtotal.
- OKX headline $484.64 + Binance headline $696.34 = $1,180.98 of two *UI totals*, but **cannot use this $1,180.98 figure as strict >=$1 verified holdings** until the OKX $4.26 discrepancy is attributed.
- Bybit personal funds excluded entirely. GANG closed realized loss **−96.210562 USDC** recorded at position level, *not* original Mission performance PnL. Historical investments/private rights remain outside liquid-NAV.


## Historical snapshot: 2026-10-12 GANG initially distributed, BEFORE sale

Source: direct finalized Solana RPC observations around **01:31–01:41 Asia/Bangkok**, main account details in `../positions/gang.md`. This section **supersedes the older October 10 GANG escrow and 58.047629 USDC wallet snapshot below**; other historical asset sections remain their original dated evidence.

| Wallet holding | Fresh direct balance | Mark treatment |
| --- | ---: | --- |
| Solana canonical USDC `AaHmxVnUryLCrSr32zxrDGzfafXTvuHATURZbBy6XQ6A` | **85.102445 USDC** (slot 455753009) | ≥$1, included in known direct chain wallet subtotal; not all change since Oct 10 is sale refund |
| Solana GANG `5XBM2iEibBNAVBMjPYb9Deh8ibm4CCqZrbqk8n7TpGJo` | **8,008.208 GANG** (slot 455753009) | **ACTUAL OWNED**; real Futarchy reserve-ratio mark ~$0.05451837/GANG at ~slot 455753008, not a verified net-sell execution quote; *indicative* value ~$436.59 |
| Solana SOL | 0.038163041 SOL **last checked October 10** | Stale quantity/price, needs fresh read before a complete current-NAV claim |
| Binance Earn | 655.55477225 USDC; screenshot USDT-equivalent ~$656.07, **2026-10-09** | Historical user-confirmed, not reverified October 12 |
| Bybit | 353.173611 USDC; screenshot 2026-10-09 | **EXCLUDED** personal living/rent cash |

Backable GANG **finalized sale**: 500 USDC originally committed, 480.492480 USDC approved cost for 8008.208 now held, **19.507520 USDC unused funds refunded** as `FundingRecord.is_usdc_refunded=true`. `is_tokens_claimed=true`. Both user GANG wallet receipt and current USDC holding independently verified. **Do not add the old 500 USDC escrow as a separate asset or add the 19.507520 refund again on top of the wallet's 85.102445 USDC.** No manual claim/refund action taken by ChatGPT.

Actual marked value of GANG depends on pool choice, fees and price impact; the ~0.05451837 price is the **Futarchy AMM reserve ratio**, not an actionable Jupiter/DEX exact-input quote. Because Binance/SOL/NFT snapshots are from different dates and some token inventories incomplete, **a fully current all-platform investment NAV remains UNVERIFIED**. For scale only, 85.102445 USDC + 8008.208 GANG at this spot reference is approximately **$521.70**, excluding stale SOL balance, other assets and CEX. The dated October 10 $718.38 table below is a **historical pre-settlement reference**; it must not be presented as the current portfolio total.

User per-position **< $1 exclusion** remains in force. GANG is above the threshold and is now a real transferable SPL balance; it is no longer an unissued/pre-TGE right.


## Historical snapshot: 2026-10-10 independently rechecked on-chain material balances

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
- The Ethereum owner NFT inventory query returned **20 token instances** (including spam/soulbound/airdrops), not zero overall. Among explicitly owned examples: `Cap Proof of Participation` token #0 (`0xCCCC5100D45432F49ed9bACc4A9CDfC77618cccC`) and `Okay Gamer Bear #169` (`0xa499f4bF71f9378A5a9DF58cB3bD263a9CDe823E`). Both ownership rows were shown by Alchemy; these are separate from the already exited Credits/UNICRED collections.
- Alchemy/OpenSea collection **floor listing asks** on 2026-10-10T16:25 UTC: Cap Pop **0.00042 ETH** (~$1.05 at Binance ETHUSDT 2510.52), while Okay Gamer Bears has a **stale** floor reference 0.001 ETH from 2026-03-21 (~$2.51 if naively repriced, **not** a current quote). Cap Pop's ~1.05 is an **asking-price indication**, not an executable bid for this specific token, sale receipt or proven liquidation price. **Both NFT cash realizations remain UNRESOLVED; neither is included in the $62.31 on-chain subtotal** under the credible-price requirement.
- Other Ethereum NFTs/Ink NFT rights similarly lack a fresh independent executable sale quote and are excluded from marked USD NAV, **not asserted zero inventory**. Solana enhanced owner-asset enumeration failed; classic SPL/Token-2022 RPC checks above succeeded.

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

## Historical pre-GANG-settlement material capital reference (2026-10-10; NOT today's NAV)

| Bucket | USD reference | Freshness / status |
| --- | ---: | --- |
| Solana USDC + SOL (each >= $1) | **~$62.31** | 2026-10-10 finalized chain, contemporaneous approximate quotes |
| Binance flexible Earn | **~$656.07** | 2026-10-09 user screenshot, NOT 2026-10-10 live |
| **Cross-source indicative investment reference** | **~$718.38** | mixed freshness; **not** audited full NAV or Mission PnL |
| GANG / The Syndicate escrow (HISTORICAL ONLY) | **500 USDC originally committed** | Superseded by 2026-10-12 claimed 8008.208 GANG and 19.507520 refund above; not outstanding escrow |
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
| Surf PRO Annual #691 / Genesis SurfBoard claim | 1 free NFT entitlement (PRO annual member; delivery/claim pending) | **$228** | verified historical PRO annual subscription expense; NFT incremental purchase fee $0 under 2026-10-13 announced mechanics | not an already minted/marked NFT; do not double count service expense as separately purchased NFT |

Known dollar-denominated historical acquisition/outlay reference above: **$16,628** (including the **$228 Surf PRO annual subscription service expense**, which earned one **free** Genesis NFT claim entitlement under the October 13 rules, **not** a standalone $228 NFT purchase; if excluding that service expense from the same subtotal, the other historical outlays equal **$16,400**). The historical $500 GANG commitment has become an actual wallet holding and refund recorded in the current section; plus **100 SOL** Block Stranding historical cost. **No change to the liquid-NAV calculation or user's cash-transfer history.** JUMP is no longer included because the application was rejected and the 1,000 USDC deposit was refunded.

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