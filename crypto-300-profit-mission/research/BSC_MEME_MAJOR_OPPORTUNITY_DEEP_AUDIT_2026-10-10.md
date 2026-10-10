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

## D. Exchange-event timing comparison: MARSCOIN versus 牛来

Official first-party listing times: [MARSCOIN Spot announcement](https://www.binance.com/en/support/announcement/detail/c2eaa763831745b2b1701dab45e20225) (posted 2026-09-04 10:15 UTC, opened 2026-09-04 13:00 UTC); [牛来 Spot announcement](https://www.binance.com/en/support/announcement/detail/6133e417dcfe43a8ad20c0db1b53c7e8) (posted 2026-09-09 11:30, opened 2026-09-09 14:30 UTC).

Main candidate `0x2adf961b40951736bcff3b36b7fb1cd5775475ba` held MARSCOIN from launchpad buys starting 2026-07-28 13:47:15 UTC (block 112636561), long before Binance announced listing. Recomputed **ten native-BNB sell-block net credits** for the MARSCOIN position, with original ERC20 token outgoing transfers:

| MARSCOIN exit stage | Blocks | Native BNB net sale proceeds |
|---|---|---:|
| Before Spot (2026-07/early Aug) | 112645256,112994387 | 0.5214495063109142 |
| **The day after Spot (2026-09-05 09:40:44–12:41:22 UTC)** | 120088241,120095162,120111060,120111216,120111303,120112322 | **6.570086570044018** |
| Later dust | 122582898,122995918 | 0.013590708420522775 |
| ALL these identified sell blocks | ten block-events | **7.105126784775456** |

Thus **92.46966% of audited MARSCOIN BNB sell receipts** occurred in the six sales 20–24 hours after official Binance Spot start. At least the first and last of the 2026-09-05 six transactions independently checked: first tx `0x370051da53af9e7074783d2b70451621537c4ac0a9d57c89187c1fd8994b6c44` and last `0x1a651124e72fac2a01b5361d4265aa916628432d6fdda668ecb3701215f22d33` both have `tx.from` equal to main candidate and `tx.to` equal to Four.meme Token Manager `0x1de460f363af910f51726def188f9004276bf4bc`, and ERC20 split fee/pool transfer out. They are genuine original-wallet swaps, not unrelated recipient movements. The timing is independently confirmed by BSC `ethGetBlockByNumber`.

For **牛来**, earliest main candidate buy `2026-08-14 09:09:32 UTC` (block 115862004) predates Binance Spot 2026-09-09 14:30. Some disposals such as block 119097043 (2026-08-31) and block 119884915 (2026-09-04) predate Spot, while block 122988185 (2026-09-20 12:20) was a **small +0.009770914 BNB** net native sale-block credit afterward. Thus its profits were **not all demonstrated to be concentrated after Spot**. Treat GIGGLE and MARSCOIN as stronger event-related examples, 牛来 as principally early-selection/partial prelisting exit pending full per-event grouping.

**Inference boundary:** confirmed spot-adjacent selling and deposits are not proof of advance knowledge or of Binance-directed manipulation. The GIGGLE Binance deposit cannot be counted as actual CEX sale; MARSCOIN swaps are on-chain and have actual native consideration. Native-block balance accounting still needs quote-asset parity checks for a fully finalized PnL.

This strengthens `0x2adf...` as a repeat **early-selection + exchange-event management** research candidate, but delay-copyability and total-market top-ranking are unverified.


## E. Independent 2026 multi-opportunity EOA expansion (2026-10-10 follow-up)

**Scope and limits:** Using the canonical read-only Alchemy app on `bnb-mainnet`, scanned the **first 120 ERC20 outgoing Transfer rows** from each of the two already verified Four.meme pre-V2 pools: MARSCOIN `0x94f3ed36706c746ad59fadcaf271b7431ab1d8f1`, 牛来 `0x595d70977dff3c841df0bc0138ce89f80c7c9423`. Each sample includes fee/manager movements and token-contract recipients, so 120 rows do **not** mean 120 distinct buyers or 120 complete trades; pools, later trade history and all other token cohorts are not exhaustively indexed. Follow-on wallet discovery additionally queried their direct ERC20 transaction histories in other core 2026 tokens and verified original transaction initiators with `ethGetTransactionByHash`. Every address and cashflow below is a fresh chain read rather than an extrapolated leaderboard.

### New research EOA 1: 0x877af245c61289b24f0c619a4346cdbc68f1aaac

- `ethGetCode` = `0x` (EOA). **Confirmed original transaction signer of buys and sells in both 龙虾 and MARSCOIN.** This is a material cross-token investigation lead, not verified cross-token profitability.
- **龙虾** CA `0xeccbb861c0dda7efd964010085488b69317e4444`: first checked buy at block **83636406**, tx `0x9aec0782d6dc3b2e8e976a38b58bfe4e91e23be43bb475dc8cc78aac4cbdad84`, signed by this EOA to Four.meme Token Manager `0x1de460f363af910f51726def188f9004276bf4bc`, native transaction value **0.14 BNB**, native balance block delta **-0.1400296847 BNB**. Checked sell block **83636583**, tx `0x40b4b78dfc60f8c0bd6769570d31a97bd99735a6052da0dab5f18967bbbd1c7b`, signed by same EOA to same manager, native balance delta **+0.10275648474982932 BNB**. Numerous additional buys and sells exist; latest token balance read showed zero but full realized PnL is not reconstructed.
- **MARSCOIN** CA `0xfe189e97832da1573e4e4ff034f4ffc3a15c7777`: checked buy block **112441460**, tx `0x15141bf698d2c2c4e07efd6c0cb54babfa7421621b1f48e4ace1727cf6be2cfa`, signed by this EOA to manager, native tx value **0.55 BNB**, native balance block delta **-0.55028515608 BNB**. Checked sell block **112441495**, tx `0x1512bc06ea2aa91817cc0606c65fa3f31fbbd3712955cd8bb99eb4bad6c8f1df`, same signer/manager, native balance block delta **+0.5081984633214329 BNB**. Many additional inflows/outflows. Some later MARS exits observed through block 117357672, but no MARS Binance-spot-day trading has been independently demonstrated for this wallet.
- **Classification:** `CORE_DIRECT_TRADE_TOKENS=2`; `EARLY_STAGE_PARTICIPATION=CONFIRMED`; `FULL_POSITION_REALIZED_PNL=UNRESOLVED`; `MATERIAL_REPEAT_WIN=UNVERIFIED`; `BINANCE_EVENT_TIMING=UNVERIFIED`; `PERSON_PATTERN=OBSERVE_ONLY`.

### New research EOA 2: 0x498528e32b04bdaa73d5c8943a09aeffd15bd99a

- `ethGetCode` = `0x`. **Confirmed original transaction signer of buys and sells in both MARSCOIN and 牛来**, via the Four.meme manager. The pair of early buys/sells does not represent complete net-profit accounting.
- **MARSCOIN**: checked first buy tx `0x852eaadad2099c485891d5bbdf4f12c890f6e491eaee2987b6c692595ebc804b`, block **112441470**, tx value **0.2 BNB**. The wallet made multiple purchases in this *same block*, native block balance delta **-0.40010729896 BNB**, so this is a block aggregate, not the cost of the one individual tx. Checked sell tx `0xf95308060af7555e8a16004815c8ef1f9bdc9920ebc873e3b01b1999d7b6388c`, block **112442022**, native balance delta **+0.39931875357852203 BNB**. Many other trades and transfers, including late dust; token balance read currently zero, but a zero EOA balance does not establish that all inventory was sold for native BNB.
- **牛来**: checked first buy tx `0xb0e08365ece6dbcea65873fd5d510dc1a5f2a8ad6fa2c0911d2082f1a295d66e`, block **116468237**, native tx value **1 BNB**, wallet native balance block delta **-1.00006043728 BNB**. Checked subsequent sell tx `0xff8a529ce4fdf98b5f3773ee420b87609c5820cb908c9a2c6474126525b7d764`, block **116468941**, native balance block delta **+1.4654060196666978 BNB**. This **MUST NOT** be interpreted as a +46.5% closed-position profit: numerous other buys, sells, transfers, and possible other quote assets remain unreconciled. Current token balance zero is not sufficient cashflow evidence.
- **Classification:** `CORE_DIRECT_TRADE_TOKENS=2`; `EARLY_STAGE_PARTICIPATION=CONFIRMED`; `FULL_POSITION_REALIZED_PNL=UNRESOLVED`; `MATERIAL_REPEAT_WIN=UNVERIFIED`; `BINANCE_EVENT_TIMING=UNVERIFIED`; `PERSON_PATTERN=OBSERVE_ONLY`.

### Contract/identity false-positive exclusion

- `0x62ccef0b4545166f721caa9fee13c1d3767e27dc` appears among both early pool recipient samples; direct `ethGetCode` confirms a **contract**, not a trader EOA, consistent with section C.
- `0x7a7ad9aa93cd0a2d0255326e5fb145cec14997ff` receives token amounts associated with MARSCOIN and 牛来 routes, but direct `ethGetCode` returns deployed **contract bytecode**, and token transfers show in-and-out movements **within the same transaction** (sample MARS sends on to `0x4a4bea953813c118c260be9a26b2321e57aa62e5`). Classify `ROUTER/INTERMEDIARY_CONTRACT`, exclude from EOA trader ranking and do **not** treat a shared contract recipient as proof of common trader control.
- A shared launchpad manager, route, counterparty, funding infrastructure, or CEX address is never sufficient to link otherwise independent EOAs as one beneficial owner.

### Chain readback of existing primary-wallet thesis

- Reconfirmed GIGGLE intermediary `0x8db3d63708522c2e7775b98203f999184cd461ea` inbound **10** and **186.13496542693022** GIGGLE from lead wallet, and its one outgoing **196.13496542693022** GIGGLE to the previously BscScan-labelled Binance 51 destination. **Transfer/deposit confirmed; CEX sale and realized PnL remain unknown.**
- Refreshed HAJIMI receiving EOA `0x1974d92e8f23cd8d33048171b8114814a185483f`: read-only token balance is **1,207,518.236589756814125673 HAJIMI** and its filtered outgoing HAJIMI transfer query is empty at this read. The original **990,550.5839829644** units transferred to that EOA should not be recorded as a sale; beneficial ownership still unverified.
- Independently recomputed the six MARSCOIN Sep 5, 2026 original-signer Four.meme sell block BNB increases, blocks **120088241, 120095162, 120111060, 120111216, 120111303, 120112322**: **1.599555615756684382 + 1.214484310481295966 + 0.936854336166214088 + 0.703198080075206236 + 0.528063036426099864 + 1.587931191138517556 = 6.570086570044018 BNB**, matching section D. These are native block-balance deltas corroborated with each transaction `from` and ERC20 outgoing transfer, not a complete realized PnL/quote-asset audit.

**Next work:** finish position-level buy/sell/fee/quote receipts (including intermediary and contract routes) for these two EOAs across their two core meme tokens, quantify whether each contains meaningful realized wins and known core losses, then expand from launchpad and other DEX routes to find additional independent multi-event winners. Do not promote based on selected positive blocks; do not assert a complete all-18/19-token top-profit wallet ranking. Unrelated small Meme trades may indicate activity only. No paid API dependency, no monitors, no live validation, no production change.
