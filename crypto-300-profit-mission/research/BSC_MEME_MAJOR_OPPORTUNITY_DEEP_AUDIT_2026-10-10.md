# BSC Meme material-opportunity follow-up: GIGGLE and 哈基米 (2026-10-10)

Status: **ONCHAIN_RESEARCH_ONLY / OBSERVE_ONLY / PRODUCTION_TRADING_NO_GO**. No paid GMGN, no user-side commands, no monitoring/live action. References: [major-opportunity rescreen](BSC_MEME_MAJOR_OPPORTUNITY_RESCREEN_2026-10-10.md), [wallet chain audit](BSC_MEME_TOP_TRADERS_AUDIT_2026-10-10.md).

## Research question

For repeated large-event candidate `0x2adf961b40951736bcff3b36b7fb1cd5775475ba`, prior record had completed four strong 2026 token positions but unresolved GIGGLE and 哈基米. This pass reconstructs exact token movements and separates **DEX realized cash**, **Binance exchange deposit**, **wallet-to-wallet inventory transfer**, **hypothetical historical DEX mark**, and **unresolved beneficial ownership/PnL**. It does **not** disqualify historical big-event winners for unrelated small-token losses or absence of current activity.

## A. GIGGLE: Binance listing-event cash-out route, not fully observable CEX PnL

- **Token:** Giggle Fund (GIGGLE), BSC CA `0x20d6015660b3fe52e6690a889b5C51F69902cE0e`. V2/WBNB pool `0xd6b652aecb704b0aebec6317315afb90ba641d57`. Verified `token0=GIGGLE`, `token1=WBNB` via read-only `eth_call`; both 18 decimals.
- **Official Binance Spot announcement:** posted **2025-10-25 03:02 UTC**, Spot **2025-10-25 06:00 UTC**, published primary source https://www.binance.com/en/support/announcement/detail/9de462f111c64723ac54331163e2652c . Listing confirmation with exact BSC contract.
- Source wallet had **11 ERC20 inflows totaling 253.22620836712247 GIGGLE**, and **5 outgoing ERC20 Transfer events across 4 tx totaling exactly 253.22620836712247 GIGGLE**; hence original token balance zero. Query `getAssetTransfers` from/to address filtered by verified CA, paged through completion `pageKey absent`.
- **11 position build transactions**, net BNB decreases (including observed native gas via one-block wallet balance deltas) total **5.662143206 BNB**. These trades span blocks 62018591, 62026656, 62029166, 62029591, 62032866, 62153573, 62154321, 62254644, 62281665, 62421790, 63084311.
- **Two DEX sell tx** originally under blocks 62022927 and 62070751 (2 token-flow transfers in second sale due to token fee), net original-wallet BNB increases **0.577692656259089 + 1.0203267518296695 = 1.5980194080887586 BNB**. Original sale hash examples `0x609909d4fb79a96616822a700d54c0c9c21537554a09743f2c8441e8170a5f01`, `0xca0f6d7c936a86eedf50d184926c141283c34235695921c873018bcdbad5fe0e`.
- **The other two outgoing txs are transfers, NOT SALES:** at 2025-10-25 **06:02:22 UTC**, 10 GIGGLE to `0x8db3d63708522c2e7775b98203f999184cd461ea`, tx `0xae6a2b2c4b50d6a26e8065d42bbe81407aad5f30e959102be20500842e91177f`; at **06:03:28 UTC**, 186.13496542693022 GIGGLE to same wallet, tx `0x87d52e0b84f0ba9c0c8ae2c7966d11dcd3a9f4e7caafac45e016080f54563822`. Corresponding original-wallet BNB changes were gas-only (-0.000004220631 and -0.000003018707 BNB); no onchain sale consideration.
- **Deposit path:** the intermediary wallet (EOA) received only these two GIGGLE transfers (196.13496542693022 units) and sent the entire amount **2025-10-25 06:12:57 UTC** at block 65829269 to `0x8894e0a0c962cb723c1976a4421c95949be2d4e3`, tx `0xc4ed86621a961e69e952f9002a0d93715449f186f0d515dd56ede2482f9334b2`. BscScan labels the final recipient **Binance 51 / Binance Exchange deposit address**: https://bscscan.com/address/0x8894e0a0c962cb723c1976a4421c95949be2d4e3 . This is an **onchain Binance deposit immediately after Spot launch**, NOT proof of execution in the exchange account, sale price or ultimate economic owner.
- **Historical spot liquidity benchmark:** `getReserves()` from above Pancake V2 pool at block 65829269 **2025-10-25 06:12:57 UTC**, token0 reserve **5555.675313663404 GIGGLE**, token1 reserve **1117.9672352645366 WBNB**, spot midquote **0.2012297645463645 BNB/GIGGLE**. Thus transferred 196.13496542693022 units had **indicative midquote 39.468192912170515 BNB**. A completely hypothetical V2 constant-product exact-input swap at that instant with an assumed 0.25% pool fee yields **~38.03027584841509 BNB** before gas/other fees. This was **NOT actually executed onchain**. CEX realization is UNKNOWN. **Never sum this hypothetical quote with DEX realized cash to publish 'realized profit'.**
- **Research classification:** `EVENTUAL_LISTED_SELECTION=CONFIRMED`; `BINANCE_SPOT_EVENT_DEPOSIT=CONFIRMED`; `DEX_REALIZED_PROCEEDS=1.5980194080887586 BNB`; `CEX_REALIZED_PNL=UNKNOWN`; `MARK_TO_MARKET_INDICATIVE_ONLY`; `NOT_FULLY_CLOSED_ACCOUNTING`; `FOLLOWABILITY_NOT_TESTED`.
- **Reproducibility:** direct BSC Alchemy RPC `getAssetTransfers`, `ethGetBalance`, `ethGetBlockByNumber`, `ethCall` (token0/token1/getReserves). Binance listing from first-party English announcement and recipient label from BscScan.

## B. 哈基米: wallet-level token balance zero, but ~990k moved to related funded EOA

- **Token:** `0x82ec31d69b3c289e541b50e30681fd1acad24444`.
- `0x2adf...` original wallet has **80 incoming token transfers totaling 2,929,159.3637324134 units** and **11 outgoing transfers also totaling 2,929,159.3637324134 units**, both direction histories fully paged until no `pageKey`. Original balance zero does NOT establish entire position sold.
- Early DEX sells in Oct 2025 included positive native-BNB cash inflows, e.g. blocks 63846885 (+0.03318110 BNB), 63849474 (+0.39574768), 63850424 (+0.41511667), 63850870 (+0.39767906), 63914076 (+1.20175166), 63946891 (+1.06363646), 64008099 (+0.58936968), 68003383 (+0.19813478), 68181790 (+0.35137491). Exact cash profit cannot be stated without matching **all 80 incoming** native/stable quote costs and possible self-transfers; don't infer full realized PnL from only positive sale blocks.
- Large **non-sale transfers** from original wallet on **2026-05-20 14:22:48–14:23:58 UTC**, at blocks 99404364 and 99404519, to `0x1974d92e8f23cd8d33048171b8114814a185483f`:
  - 90,550.583982 HAJIMI, tx `0x2b278e7345db4cbbbe4f9c5a696c95d25ae25621522702e8e26be7ab2f19ed98`.
  - 900,000.0000009644 HAJIMI, tx `0xb40aba1de3f44f2415faaf69da05eb275ff9f762314dc28961f189e1ce7cd272`.
  - Total **990,550.5839829644 HAJIMI** moved with only native gas paid, no evidenced sale consideration.
- New receiving wallet has other HAJIMI inbound transfers 216,967.65260679243 units and **no outward HAJIMI transfers** in full queried ERC20 record. On query date, `getTokenBalances` found **1,207,518.2365897568 HAJIMI still held by recipient**. Do NOT attribute all 1.2075m to original wallet; only 990.55k came from original wallet.
- **Repeated direct BNB transfers also link the two wallets**, including original EOA -> recipient **3 BNB at block 47629675**, **0.8 BNB (63983352)**, **2 BNB (63983581)**, **3 BNB (63984237)**, **3 BNB (64457528)**. These support a wallet network/coordinated funding hypothesis, but cannot conclusively prove one legal owner. Some recipient EOA BNB outgoing flow to another account also occurs.
- **Research classification:** `ORIGINAL_WALLET_POSITION_ZERO=TRUE`; `HOLDINGS_TRANSFER=CONFIRMED`; `RELATED_FUNDING=CONFIRMED`; `SAME_BENEFICIAL_OWNER=UNVERIFIED`; `REPORTED_FULL_REALIZED_PNL=NOT_AVAILABLE`; `NO_CONFIRMED_SELL_OF_TRANSFERRED_990550.58`; `EVENTUAL_BINANCE_PERP_LISTING=2026-09-06` separately from old 2025 entry.
- **Do not claim 80 positive buys or 11 sales**; records are token transfers, some buy/sell, some other. Full receipt-level classification still needed.

## Implications for selecting repeat major-opportunity wallets

This one EOA has four previously audited material 2026 profitable Binance-related token positions (我踏马来了, 龙虾, MARSCOIN, 牛来), **plus** two major tokens with significant *more complex* behavior:

- GIGGLE: verified spot-listing event fund transfer to Binance CEX shortly after 06:00 UTC open, with sizable historic indicative quote; **realized CEX PnL unknown**. The evidence makes this a strong **event-timing research lead**, not a fifth verified net profitable position.
- HAJIMI: partial exits and almost 1m tokens transferred into an EOA with repeated direct funding links; still held there in the last snapshot; **total cluster-level PnL unknown**, not a negative mark nor a fifth win.
- Previously sampled random small-coin win rate or the lack thereof must not change this major-token evidence ranking.
- Next priority is cross-token DEX+Binance timing comparisons for other high performers and verifying true signer vs same-user cluster, not paid API leaderboards.
- Avoid treating an early buyer who exits a token a year before Futures launch as a Binance announcement insider. For the GIGGLE deposit, the event link is directly corroborated with official Binance spot timing.

No user commands, Git production modifications, monitoring, live validator or trading actions.

## C. Four.meme pre-V2 wallet cohort

Primary RPC finding: the 2026 MARSCOIN and 牛来 early purchases of `0x2adf961b40951736bcff3b36b7fb1cd5775475ba` both sent BNB to `0x1de460f363af910f51726def188f9004276bf4bc`, labelled Four.meme Token Manager on BscScan, via selector `0x4d819a2a`. Their first tokens came from **pre-V2 pools**, respectively `0x94f3ed36706c746ad59fadcaf271b7431ab1d8f1` and `0x595d70977dff3c841df0bc0138ce89f80c7c9423`. This validates that V2-only wallet selection misses major early traders.

From each of those pools 100 ERC20 outgoing entries (50 distinct tx hashes) were queried in 10x10 Alchemy pages, yielding 35/44 non-manager recipient addresses for MARSCOIN/牛来. Two overlap: `0x62ccef0b4545166f721caa9fee13c1d3767e27dc` is a smart contract (exclude from person-level results); `0xadffbebbd2d9141cff80f8a905846ba8f9e3946d` is EOA with trades on both.

Early-trading-episode EOA `0xadffbebbd2d9141cff80f8a905846ba8f9e3946d`, based on original token-transfer blocks and before/after BNB balances:

| Token | Sampled buy-block BNB debit | Sampled sell-block credit | Episode estimated net |
|---|---:|---:|---:|
| MARSCOIN | 0.72204141168 | 0.8307888200814364 | +0.10874740840143637 BNB (15.06%) |
| 牛来 | 0.62594698856 | 0.6798050121190302 | +0.053858023559030244 BNB (8.60%) |

MARS episode: buys at blocks 112441470, 112441471, 112441578, 112442297; exits at 112441493, 112441511, 112441518, 112441533, 112441542, 112441661, 112442409, 112442414. 牛来 episode: buys at 115829267, 115853809, 115854032, 115854994; sells 115829502, 115833784, 115853817, 115854094, 115855119.

Both token wallet transfer histories were independently paged to completion: 43 in /37 out transfer rows (MARSCOIN), 41 in /35 out (牛来), many later transactions. Therefore **the early episode returns are not full-token or lifetime PnL**. With only modest wins, candidate state is SECONDARY_OBSERVE_ONLY, not promoted as a repeatedly material big-opportunity winner. Historical balances may include non-native settlement. No paid GMGN, monitors or trading.
