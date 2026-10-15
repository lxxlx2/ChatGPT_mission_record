# Mission Portfolio / Current Assets and Capital Classification

Updated: 2026-10-15 Asia/Bangkok (17:46–17:50 CEX screenshot/direct-chain balance refresh; earlier Surf chain evidence retained)
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

## Newest user screenshot and live wallet balance snapshot — 2026-10-15 17:46–17:50 Bangkok

**Evidence/freshness:** Binance USDC flexible Earn user screenshot clock **17:46 Bangkok**, Bybit USDC user screenshot clock **17:48**, both provided by user on **2026-10-15**. The screenshots document quantities and app labels; no CEX API account login was performed. Direct read-only Alchemy Solana finalized native and classic SPL observations at **slot 457210185**, Token-2022 at **457210186**; Alchemy price quotes timestamp **2026-10-15 10:49:40–10:50:02 UTC** (Bangkok **17:49:40–17:50:02**). EVM native reads are latest-block per network, not atomic with Solana or the screenshots. Bybit remains lifestyle/rent only. No inferred transfers or PnL.

### Screenshots: Binance counted, Bybit never counted

| Account and scope | Verified screen quantity | Price/annotation | Investment inclusion |
| --- | ---: | --- | --- |
| Binance Flexible Earn USDC, 1 position | **776.01087688 USDC** | Real-time annual rate **2.09%**, tier annualized yield **2%**, yesterday's reward **0.07794003 USDC**, cumulative **1.34887353 USDC** already included in displayed principal-plus-interest balance | **Included** |
| Bybit Earn USDC | **438.953400 USDC** | User screenshot | Excluded |
| Bybit Funding USDC | **35.385365 USDC** | User screenshot | Excluded |
| Bybit Unified Trading USDC | **0.086456 USDC** | Individually <$1 but kept in exact household-account reconciliation | Excluded |
| **Bybit combined** | **474.425221 USDC** | App screenshot USD indicative NAV **~$474.94**, including all three subaccounts; only record this household expense reserve | **$0 included** |

Compared to prior user screenshots (2026-10-13 21:48), Binance USDC **+30.15542403**, Bybit total USDC **+31.395316**. These are quantity movements, not proven rewards, proceeds, trading gains or attributable transfers. At common Alchemy USDC/USD **1.00106**, Binance marked quantity is **~$776.83**; Binance screenshot displays **USDC amount only**, not the $776.83 independent USD quote.

### Solana direct finalized current ownership

Canonical wallet `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`.

| Asset | Chain quantity | Independent price mark and USD value | Evidence | Included? |
| --- | ---: | --- | --- | --- |
| Classic SPL USDC `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` | **501.630372 USDC** | USDC/USD **1.00106** → **~$502.16** | Finalized `getTokenAccountsByOwner`, slot **457210185**, token account `AaHmxVnUryLCrSr32zxrDGzfafXTvuHATURZbBy6XQ6A` | Yes |
| Native SOL | **0.012905142 SOL** = 12905142 lamports | SOL/USD **102.15** → **~$1.32** | Finalized `getBalance`, slot **457210185** | Yes |
| GANG | **0** | No current inventory | Finalized classic SPL `5XBM2iEibBNAVBMjPYb9Deh8ibm4CCqZrbqk8n7TpGJo` | CLOSED, no asset |
| Other classic SPL | 0 | None included | Five classic accounts total, only USDC positive | Excluded |
| Four Token-2022 mint accounts | **1 raw unit each, decimals 0** | No independently supported executable USD value; two accounts have `nonTransferableAccount` extensions | Finalized token-2022 slot **457210186** | UNPRICED / excluded, not represented as $0 |

Compared to prior 2026-10-13 Solana finalized observation, USDC **+29.913613** and SOL unchanged. Solana marked direct-chain subtotal **~$503.48**, valued only with quoted Alchemy time. Do not double-count OKX screenshot Solana USDC/SOL, old GANG refund or historical realized GANG sale proceeds.

### EVM/NFT/Sui follow-up coverage

- **EVM native latest-block read-only observed:** canonical `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c` holds Ethereum **0.000190807320080339 ETH**, Base **0.000067914430044193 ETH**, Arbitrum **0.000003959328931033 ETH**, Optimism **0.000065278581034767 ETH**, BNB Chain **0.000188510040720439 BNB**, Polygon **0.291295907607284273 POL**, Unichain **0.000020589846025254 ETH**, Ink **0.000003101575720485 ETH**, Linea **0.000078994423394387 ETH**, World Chain **0.000106736504323280 ETH**, Monad **0.3817997 MON**, HyperEVM **0.000234033730511199 HYPE**, and Robinhood Chain **0.000252742161494798 ETH**. Using Alchemy 2026-10-15 10:50 UTC ETH **2361.36**, BNB **718.95**, POL **0.09324**, MON **0.02246**, HYPE **78.89**, every one of these **separately priced native positions is <$1** and excluded; Binance/OKX balances are not inferred from these on-chain native holdings.
- **EVM ERC-20:** Arbitrum (26 result entries), Unichain (3), Ink (4), Robinhood Chain (16) token owner-balance calls returned positive and spam/unpriced tokens; important token price lookups showed no independently priced >=$1 owned ERC-20. For example Unichain USDC **0.021286** (~$0.02), Robinhood PONS **0.000953441979624353** at independent ~$0.30825/PONS (~$0.00029), both <$1. Ethereum, Base, Optimism, BNB, Polygon results exceeded tool response truncation (not complete) and therefore remain **ERC20_INVENTORY_PARTIAL_UNRESOLVED**. No unpriced token is asserted zero or negligible without price evidence.
- **SurfBoard NFT #5396:** `getOwnersForNFT` on Robinhood Chain for ERC721 `0x18c9719AB6AE4E1a6f95F281eF288e3AF5d58602`, tokenId **5396**, returned only the canonical wallet. Ownership **DIRECT_CHAIN confirmed again**, with **UNPRICED** executable NFT value. Earlier 2026-10-15 chain opened tier 1, NVDA pending 0.000745771759040394, and absence of directly transferable series tokens remain *historical measurements*, not revalidated today at 17:50. See separate Surf research entry below. NFT and prior < $1 accrued rights excluded from cashlike marked subtotal.
- **Sui** `0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`: no direct fresh Sui mainnet balances could be returned by available actions (official Sui owner balance lookup requires an unsupported RPC request). Prior user-confirmed zero is dated historical only. Do **not** claim Sui asset inventory complete.
- **OKX Web3 dated history (2026-10-12 screenshot):** **0.002403 ETH** and **3.3847 TRX** quantities *not rechecked on 2026-10-15*. Using 2026-10-15 prices ETH **2361.36** and TRX **0.3333** implies **~$5.67 and ~$1.13**, conditional on still owning those historical quantities. Keep separate from direct-chain identified wallet balances and do not double-add OKX screenshot Solana.

### Filtered USD reference, accounting rules unchanged

| Basis | Priced separate asset breakdown | USD |
| --- | --- | ---: |
| **Newly verified holdings reference** | Binance 776.01087688 USDC at 1.00106 (~776.83) + direct Solana 501.630372 USDC at 1.00106 (~502.16) + 0.012905142 SOL at 102.15 (~1.32) | **~$1,280.31** |
| **Mixed-freshness conditional reference** | Verified reference + *unreverified 2026-10-12* OKX 0.002403 ETH (~5.67) + 3.3847 TRX (~1.13) | **~$1,287.12** |
| **Bybit household/reserved** | Screenshot 474.425221 USDC; application appraised at ~$474.94 | **$0 included** |
| **Unpriced/uncertain inventory** | SurfBoard NFT #5396 + Token-2022/non-priced EVM assets, possible unsurveyed Sui/EVM assets | **UNRESOLVED** |

Never label either reference as complete contemporaneous NAV, actual Mission portfolio profit or return on the original $300 and Credits NFT starting set. Prior October 13 newly marked reference **~$1,220.34** differs by **~+$59.97**, substantially explained by the aggregate stablecoin quantity increases and valuation differences, but causes/cashflows **UNVERIFIED**. Original GANG realized loss **−96.210562 USDC before SOL gas** remains historical, not recomputed; `MISSION_PNL_UNRESOLVED` and `PRODUCTION_TRADING=NO_GO` remain unchanged. Research actions were read-only, no wallet authorization, claim, trade, service restart, Gmail/notification/automation or spending transaction.

---

## Verified SurfBoard NFT #5396 position — 2026-10-15 11:43:55 Asia/Bangkok

Source `DIRECT_CHAIN`: Robinhood Chain `4663`, Alchemy NFT ownership, original chain transaction receipts and pinned `eth_call` block **88947414** (2026-10-15 04:43:55 UTC); detailed evidence and series counts in [SurfBoard live research](../../research/nfts/surf-genesis-nft-chain-valuation-2026-10-12.md#9-surfboard-5396-开包后主钱包分配资金池及系列活动链上实证2026-10-15).

- Canonical EVM wallet `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c` owns **one SurfBoard NFT #5396** from ERC721 `0x18c9719AB6AE4E1a6f95F281eF288e3AF5d58602`. Initial on-chain Airdropped + ERC721 Mint receipt **`0xfaffd46a5a7da9854b2a28262e54ef275cf4251a7686324f61b3bd17cfb6c104`** at **04:20:28 UTC**.
- `0xc84f1bfb8594d5dd1c2804066f74d766d39b5560ab875e53ef91bf9653ea9fd3` **open(5396)** and burn 1 SurfBoard ERC20 at 04:22:11Z; `0x85c98979c86fd217cd2fbf3fe6709ef42d63f6d80b77f46761426298fd77a0bc` **Revealed tier=1** at 04:22:18Z. Direct on-chain Core states `isOpened=true`, `isRedeemed=false`, `tierOf=1`; Mirror `tokenURI` points to `metadata.asksurf.ai/nfts/surfboard/opened/5396.json`. User screenshot matches **Common / NVDA / weight x1**.
- `SurfReflections` `0xF1ddD8eE0ABab932d9394E138beF2D4ca945C64e` `pending(5396)` = **0.000745771759040394 NVDA** (token `0xd0601CE157Db5bdC3162BbaC2a2C8aF5320D9EEC`, 18 decimals) at block **88947414**. **The canonical wallet owns 0 directly transferable units of all five checked stock tokens**; accrued NVDA remains a contract-bound NFT right until redeem. At the screenshot's **$219.3/NVDA reference**, this is **~$0.164**, **below $1 and excluded from displayed USD marked totals**, not a true live executable market quote. NFT market bid/executable price **UNRESOLVED**, NFT remains **UNPRICED / excluded from liquid NAV**; do not count future accrual as realized PnL.
- Financial provenance: $228 was paid for **Surf PRO annual membership** in 2025, verified by official receipt; an eligible annual membership provided one **free NFT claim**. The older `Surf Limited Edition #691` number identified the historical subscription/entitlement, **not the ultimate minted ERC721 token ID**; #5396 is the actual NFT. Preserve the $228 historical service expense exactly once. Do not add $228 as a separate cost-basis liquid asset, nor remove the recorded historical expense.
- **All other portfolio rows and earlier 2026-10-13 Binance/Bybit/Solana/OKX snapshots below are unchanged in amount** and must not be relabeled fresh 2026-10-15. No user's transaction was initiated or signed by this research, no monitoring/task created and no NFT liquidation or redeems executed by ChatGPT.


## Historical independently checked investment snapshot — 2026-10-13 21:48–21:50 Bangkok

**Freshness/source separation:** user Binance and Bybit screenshots show phone time 21:48 Bangkok on 2026-10-13; Alchemy Solana RPC finalized observations are slots **456480952** (native and classic SPL) and **456481206** (Token-2022); Alchemy USD price samples are 2026-10-13T14:48:59–14:50:31Z. EVM balances are newly queried latest-provider results, not a complete ERC-20/NFT inventory. The existing OKX ETH and TRX quantities were last user-confirmed by screenshot on **2026-10-12**, not rechecked as current chain balances. No exchanges were authenticated or mutated.

### Exchange user screenshots (only Binance counts)

- **Binance Earn:** **745.85545285 USDC** in one Flexible Earn position, screenshot total **~$746.73 USDT-equivalent**. Screenshot cumulative interest **1.1934495 USDC**, **already included** in the current USDC position; rate displays **up to 4.39% variable annualized**, not guaranteed income. Source class `USER_CONFIRMED_SCREENSHOT_2026-10-13_21:48_BKK`. Do not sum token quantity plus UI USD estimate.
- **Bybit personal expenses/rent:** **443.029905 USDC**, screenshot estimated **~$443.51 USD**, consisting of Earn **413.602000 USDC**, Funding **29.341449 USDC**, Unified **0.086456 USDC**. Whole account is **EXCLUDED** from every investment subtotal, including its individual under-$1 component. The complete Bybit balance is recorded separately for household bookkeeping; no change to classification.
- Relative to the last 2026-10-12 screenshot, Binance underlying USDC changed from **695.70724404** to **745.85545285**, difference **+50.14820881 USDC**, with **no inferred deposit/interest/PnL attribution**. Bybit changed from **445.724250** to **443.029905 USDC**, difference **−2.694345**, equally not Mission profit or loss.

### Solana canonical wallet: finalized raw balances and value

Wallet `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`, source Alchemy Solana mainnet `getBalance` and `getTokenAccountsByOwner` classic/Token-2022 with finalized commitment:

| Asset | Verified chain quantity | Source / price evidence | Inclusion |
| --- | ---: | --- | ---: |
| USDC, mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` | **471.716759 USDC** | Classic SPL owner account `AaHmxVnUryLCrSr32zxrDGzfafXTvuHATURZbBy6XQ6A`, finalized slot **456480952**; Alchemy USDC/USD **1.00107** at 2026-10-13T14:48:59Z | **~$472.22** |
| SOL | **0.012905142 SOL** (12,905,142 lamports) | `getBalance`, finalized slot **456480952**; Alchemy SOL/USD **107.94** at 2026-10-13T14:50:30Z | **~$1.39** |
| GANG / old acquired mint held in `5XBM2iEibBNAVBMjPYb9Deh8ibm4CCqZrbqk8n7TpGJo` | **0** | Classic SPL `getTokenAccountsByOwner` finalized slot 456480952. Previous user-executed GANG sale and separately recorded realized loss remain historical | **$0, CLOSED, not a current holding** |
| Other classic SPL accounts | **0 token units** | All 5 returned owner classic SPL accounts at same finalized slot: only USDC has positive units | Excluded |
| Token-2022, 4 distinct mint accounts | **1 raw unit each, decimals 0** | Four positive accounts at finalized slot **456481206**, two with `nonTransferableAccount`; no independently supported realizable USD marks | **UNPRICED/EXCLUDED**, do not claim zero value |

**Direct-chain, independently marked >=$1 Solana subtotal: ~$473.61** using the sampled prices. USDC and SOL quantities match October 12, and GANG remains fully exited; price-dependent USD value changes do not prove transfers or realized PnL. USDC contains any old GANG proceeds/refunds already received, with no second addition.

### EVM / Sui / NFT coverage and dated OKX holdings

- Alchemy `getTokenBalancesByAddress` returned current native balances on Ethereum **0.000190807320080339 ETH**, Base **0.000136480596689642 ETH**, Arbitrum **0.000003959328931033 ETH**, Optimism **0.000065278581034767 ETH**, Unichain **0.000020589846025254 ETH**, Ink **0.000003101575720485 ETH**, BNB Chain **0.00000385774262336 BNB**, Polygon **0.291295907607284273 POL**. Dedicated latest native reads: Linea **0.000078994423394387 ETH**, World Chain **0.000106736504323280 ETH**, Monad **0.3817997 MON**, HyperEVM **0.000234033730511199 HYPE**. Each separately priced native position is **< $1**, excluded individually using Alchemy USD references sampled 2026-10-13 around 14:50Z.
- Blockscout owner-token holdings returned fully paged Ethereum (**70 rows**), Arbitrum (**15**), Optimism (**23**), Unichain (**2**), with **no independently priced >=$1 ERC-20 holding** in the returned rows. **Coverage remains incomplete**: Base/Polygon yielded PRO-credit HTTP 402, BNB Chain ID 56 unsupported by that endpoint, and Alchemy token-balance aggregation was truncated. Unpriced/spam balances are not counted as dollars or conclusively called dust. No paid fallback required.
- Solana enhanced owner asset enumeration returned provider `RPC -32001`; classic and Token-2022 SPL RPC above succeeded. Do not infer exhaustive NFT/nonfungible absence.
- Sui canonical wallet `0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`: no new Sui-native balance obtained. Last user-confirmed zero remains **historical USER_CONFIRMED**, not fresh DIRECT_CHAIN. EVM NFTs/current executable bids not freshly rechecked; UNPRICED holdings/rights remain outside marked NAV.
- The October 12 OKX Web3 screenshot listed **0.002403 ETH** and **3.3847 TRX** on account 01. These quantities were **not freshly reverified** nor mapped to the canonical EVM/Tron addresses on October 13. Alchemy 2026-10-13 USD quotes ETH **2527.16**, TRX **0.32716** imply **~$6.07 ETH** and **~$1.11 TRX** conditional on still owning exactly those older displayed amounts. Keep these separate as **DATED_SCREENSHOT_QUANTITY + CURRENT_MARK**, not DIRECT_CHAIN; do not double-count screenshot OKX Solana USDC/SOL.

### Asset totals: strict source labels, no false Mission ROI

| Basis | Included individually priced assets | Reference USD |
| --- | --- | ---: |
| **Freshly observed, separately priced minimum reference** | Binance screenshot $746.73 + Solana direct ~472.22 USDC + ~1.39 SOL | **~$1,220.34** |
| **Mixed-freshness indicative investment reference** | Above plus Oct 12 OKX ETH ~6.07 and TRX ~1.11 quantities valued using Oct 13 prices | **~$1,227.52** |
| Bybit personal/living assets, excluded | 443.029905 USDC, screenshot ~$443.51 USD | **$0 included** |

The October 12 comparable filtered reference was **~$1,176.72**, so mixed-dated reference-to-reference change is **~+$50.80**, **NOT trading PnL**, not a same-time audited NAV and not progress on the original $300 + six Credits NFT cohort. GANG separately realized **−96.210562 USDC before SOL gas** as previously proved; no new GANG transaction or cost accounting change is asserted. Original Mission PnL still `MISSION_PNL_UNRESOLVED`.

No wallet signing, order, claim, transfer, Gmail, LaunchAgent, scanner, monitoring or production runtime changes were made during this research-only asset update.

---

## Historical snapshot: GANG fully exited, CEX/OKX screenshots — 2026-10-12

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
| Surf PRO Annual #691 → SurfBoard #5396 (Robinhood 4663) | **1 directly verified ERC-721 NFT, opened Common/NVDA; owned by canonical EVM wallet as of 2026-10-15** | **$228** | historical PRO annual subscription service expense (2025-08-31), generated free NFT claim; not a separate $228 NFT mint | **NFT unpriced/no verified executable bid**; pending 0.000745771759040394 NVDA is accrued in protocol (<$1 at screenshot reference), not standalone wallet token or liquid marked NAV |

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