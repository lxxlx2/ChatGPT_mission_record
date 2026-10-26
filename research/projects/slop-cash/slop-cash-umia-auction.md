# Slop Cash / SLOP — Umia auction participation research

Updated: 2026-10-27 Asia/Bangkok (official Nov5/7/10 UTC dates corrected, precise early eligibility publication rule, freshly checked USDG balance, token vesting contradiction)
Scope: ICO / pre-launch token auction / Robinhood Chain
State: `USER_INTENDS_TO_PARTICIPATE / WAIT_FOR_FINAL_AUCTION_TERMS / NO_FUNDS_COMMITTED`
Decision classification: `WATCH` (not SETUP or ACTIVE).
Execution: `NO_GO`; the user has expressed interest only, with no authorization for funding, wallet signature, live trading, scheduling or monitoring.

## 2026-10-27 direct Base RPC historical UMIA auction fills and spot-pool backtest + SLOP CA check

**Research objective:** User asks if SLOP token is already silently deployed in Umia UI/source code, and wants prior Umia self-launch **historical actual participant costs, opening price, maximum, and time-to-peak with onchain evidence**. No asset operations requested.

### A. $SLOP canonical token contract identity

- First-party https://app.umia.finance/p/slop-cash **literally says** `Contract address: (added at deploy)` and `Existing token: no`; as of this dated check https://app.umia.finance/p/slop-cash/auction shows `Upcoming`, $0 commitments. **Canonical Robinhood mainnet SLOP ERC20 CA, specific CCA instance and v4 poolId = UNVERIFIED / NOT PRESENT IN FIRST-PARTY DOCUMENTATION**. Does not prove no confidential/precomputed deployment exists.
- Direct latest public `SlopDotCash/slopdotcash` GitHub default branch code search for `0x`, `SLOP token` and review of public EVM contracts finds payment escrow/fee workers, Robinhood **testnet** integration and `contracts/evm/integration/MockReferralToken.sol` (explicit mock); no project-first-party-identified **official** token deployment address. Umia protocol repo search `Slop` returned no identity mapping. Do not mistake Slop's **Ethereum Cyber Corp** `0x6d2e…15e2` legal entity address, Robinhood canonical **USDG** `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`, auction factories, or a fake SLOP for actual SLOP CA. A stray address in a bundle alone is insufficient to authorize spending.
- Current CAs may be added before opening on **2026-11-05 17:00 UTC** gated stage; verify via issuer address and direct `eth_getCode`, `name/symbol/totalSupply` and original deploy tx. Until then state remains `SLOP_CA_UNCONFIRMED`.

### B. UMIA predecessor: auction onchain verified at Base CCA

Primary source https://umia.finance/docs/contract-addresses/base (Umia venture and official pool), plus original sale https://app.umia.finance/p/umia/auction and https://umia.finance/blog/umia-auction-recap .
- Base (8453) `UMIA ERC20 = 0x56ab53b77F07DA3af732150E8aeC4783eB5BbA7D` (18 decimals), USDC `0x833589fcd6edb6e08f4c7c32d4f71b54bda02913` (6 decimals). Original CCA `0x2DDaFa49cdd62864ab2E2aad66CC294CC7ef4A9b`.
- **Direct historical CCA eth_call latest**: `startBlock()=50485328`, `endBlock()=50780530`, `claimBlock()=50780560`, `totalSupply()=17,299,999.308 UMIA`, `remainingSupply()=0`, `totalCleared()=17,299,999.308`, `currencyRaised()=6,112,005.046962 USDC`, `nextBidId()=751`, `isGraduated()=true`, `clearingPrice()=0.36 USDC/UMIA`. `nextBidId=751` is **751 bid IDs not necessarily unique individuals**.
- Direct implied *aggregate VWAP* `6,112,005.046962 / 17,299,999.308 = $0.353295104/UMIA`, ~1.862% below the final $0.36 clearing quote. **Final clearing price not the exact weighted cost basis of every participant**.
- Archived `bids(uint256)` and real `BidExited` logs event topic `0x054fe6469466a0b4d2a6ae4b100e5f9c494c958f04b4000f44d470088dd97930` reveal tokens, refunds and effective costs. Examples:
  | Bid ID | Phase based on start block | Gross budget | Received UMIA | USDC spent | Effective USDC/UMIA | Exit tx |
  | #0 | first gated phase | 5,000 | 14,296.9660 | 4,999.01708 | **0.3496557992** | `0x54185b85fa72a4b7ff7871eb0c5c0c5d51467b3013a856287a63057ae5516ad8` |
  | #100 | first gated phase | 100,000 | 285,939.3204 | 99,980.341586 | **0.3496557991** | `0xb88523e1866b76abf464055317c09df134eec8b186362357fb8f04098c6b33c9` |
  | #200 | public phase | 5,000 | 13,887.2425 | 4,998.965300 | **0.3599681726** | `0x6a74c6699e37fc80cabc662e288915b2e7f3d48eb56b0b2a037b13bf1b9bda98` |
  | #350 | public phase | 5,000 | 13,886.9206 | 4,998.965239 | **0.3599765112** | `0xec2a57b4b38f269111374ce73c4a0257a275518f04bc2e736065228b3e48f06c` |
  | #500 | public phase | 5,000 | 13,886.3879 | 4,998.965079 | **0.3599903087** | `0xcc5e93cd2962fee5214961139c5c9e6c44e934b388fb664644979b9d1fe28cac` |
  | #650 | public phase | 5,000 | 13,886.0722 | 4,998.964894 | **0.3599984795** | `0x80e66fa2c55cc5a1bfbf5d087f391dfdfe31355a05b62d366ab2d404aec83a3d` |
  | #748 | public phase | 1,999.8 | 5,553.84985 | 1,999.385948 | **0.3600000001** | `0xa5827fc59eb8ee96f7cd7fa1f2b0beafca50576853b54845da8ef6b20bb46751` |
  | #749/#750 | public late | 5,000 each | 13,886.013236 each | 4,998.964766 each | **0.3600000001** | respective verified chain events |
  Early sample cost ~$0.34966, not a universal "$0.12 early presale price"; late public sample ~$0.36. **Sample selected by bid ID, not representative sample of all bids.** No user-specific UMIA holding claimed.

### C. Actual Base onchain spot opening and subsequent price

- Official **Uniswap v4 poolId** `0xbc6683f3fed27bbfdfb6d9f342a29c5f2c2f02de9f9d65fb35d77d4f43a7b51e`, `PoolManager=0x498581ff718922c3f8e6a244956af099b2652b2b`; `StateView=0xA3c0c9b65baD0b08107Aa264b0f3dB444b867A71`; sourced from https://umia.finance/docs/contract-addresses/base .
- CCA `endBlock=50,780,530` corresponds ~2026-09-02 **12:00:07 UTC**. Direct `getSlot0(poolId)` is zero/uninitialized at Base block **50,780,829** and initialized at **50,780,830**, ~**12:10:07 UTC** (10-min interval after CCA closes). First pool Initialize event topic `0xdd466e674ea557f56295e2d0218a125ea4b4f0f6f3307b95f85e6110838d6438` from mainnet transaction `0x626782219eca0cd8119726c0a2030bdcfb7de06fc42cb4316a22315a6c737e67` confirms **initial pool price $0.36/UMIA** (sqrtPriceX96 converted accounting for 18/6 decimals) **onchain**, independent of marketing claims.
- Same block's closing state already ~$0.58224 due to intra-block swaps. 2026-09-02 at UTC **12:12 ~$0.54581**, **12:15 ~$0.72616** (more than 2x $0.36 launch within ~5 mins), **12:30 ~$0.65117**, **13:00 ~$0.78828** (2.19x), **14:00 ~$0.60694**, **18:00 ~$0.70375**, Sep03 **00:00 ~$0.62778**. These are **sparse timestamp point samples of actual archived onchain pool state**, not OHLC intraperiod H/L nor guaranteed execution prices. Onchain settlement can occur before v4 pool init; claiming liquidity opportunity may still require user transaction and timing.
- External historical **CoinMarketCap** https://coinmarketcap.com/currencies/umia/ lists market aggregate all-time high **$0.9044 on 2026-10-08**, ~**2.512×** $0.36 final clearing, reached about **36 days after 2026-09-02 launch**. **NOT DIRECTLY CHAIN-VERIFIED AS THE ABSOLUTE PEAK OF THE OFFICIAL V4 POOL.** Date is cross-supported by other third-party price sources.
- Direct archived Oct08 pool `getSlot0`: **00:00 UTC ~$0.77788**, **08:00 ~$0.80820**, **11:30 ~$0.88859**, **11:35 ~$0.89043**, **12:00 ~$0.88310**, **14:00 ~$0.87430**, **18:00 ~$0.79943**. Highest observed sampled onchain ~**$0.89043**, and precise intra-swap highest/lowest cannot be proven from sampling alone. Third-party OHLC peak $0.9044 could refer to short-lived or another venue, do not mislabel as verified from onchain.
- Opportunity costs hypothetical: a $1,000 *real filled cost* at early sample $0.3496558 → at reference $0.9044 would mark at ~$2,586.54 (**+158.65%**); late public $0.36 → ~$2,512.22 (**+151.22%**), before fees and sell slippage. Marking assumes token transferable and liquidity for that size, does not prove real sell profit. Early advantage ~$0.01034/token, only ~2.87% lower than $0.36 final.
- **Practical SLOP lesson**: winning first ICO $UMIA did not make first-day sale final price available to all: visible public fill in ~7 minutes, sampled public actual $0.36, not an automatic $0.12; verify Slop early eligibility and public clearing price at Nov08 opening, preserve personal FDV cap rather than chase the sale ceiling. Lower SLOP LP quote-side reserves and weaker revenue vs UMIA means no comparable ROI assumed.

### Evidence limits and operational rules

- Direct Base mainnet RPC via Alchemy eth_call archive and exact small-range eth_getLogs, user funds untouched.
- Blockscout PRO API returned **HTTP 402 credits exhausted**; we DID NOT use its output as successful verification. Web source CMC is secondary for exact ATH; docs/source official for deployment addresses.
- Do not infer all 751 bidders have same cost; no exhaustive 751-bid PnL scan, no actual personal wallet attribution. Full max price high-water mark requires exhaustive v4 Swap log indexing, not supported by per-request **10 block eth_getLogs** limit; preserve this limitation.
- User remains `SLOP_1000_USDG_INTENT_ONLY / NO_SLOP_CA_AUTH / NO_BID / NO_AUTOMATION`. Research record only; do not change positions, trading gates or existing monitoring tasks.

---

## 2026-10-27 price discipline for the Nov8 public round (conditional research model)

**User goal**: capital budget **1000 USDG**, public auction from **2026-11-08 00:00 Asia/Bangkok** (November 7 17:00 UTC). Do not mistake intended budget for a bid or actual investment. **No account action performed.** This is a pre-auction *conditional price plan*, subject to actually observable clearing and bidder eligibility at open.

### Evidence and comparables

- 2026-10-27 issuer Umia Tailored Auction docs https://umia.finance/docs/tailored-auctions/: order has **budget + max price**, released supply is distributed by time buckets, live uniform per-bucket clearing with monotonically nondecreasing price. Order stops filling when clearing exceeds bidder's max; unspent funds refundable at close. Earlier qualifying bidders may acquire lower average entry. **The $1000 cannot be guaranteed fully spent while preserving a low limit.** Market default can expose bidder to full auction hard ceiling ($0.02196); change order type to **Limit**, confirm input token amount and final Max FDV before signing. Orders are generally noncancellable until auction close.
- Issuer's own completed **UMIA** auction 2026-08-26 to Sep02 cleared at **$0.36/$18m FDV**; **$6.112m** raised, **751 bids** (site), public available allocation fully filled in about **7 minutes**, secondary reference ~$0.67 per token by Oct 26 (~+86% from initial $0.36), all qualified by differing product/equity/marketmaker economics. Official recap https://umia.finance/blog/umia-auction-recap ; primary https://app.umia.finance/p/umia/auction ; independent historical https://www.coingecko.com/en/coins/umia/historical_data. This is **NOT** forecast that Slop will clear at cap or appreciate, and requires a fast *decision*, not an unbounded high price bid.
- Team/tech evidence: Slop Github https://github.com/SlopDotCash/slopdotcash latest merge `6cdec7ce4b0a3acc17762b853a94434d94e631d8` dated 2026-10-26, substantive Solana expiration recovery, monthly point logic, review independence. Slop repo at read 63 Stars/70 Forks. Founder Shaw Walters' elizaOS code repo https://github.com/elizaOS/eliza approximately 19,653 stars/5,826 forks, genuine prior software ecosystem but **not financial profit proof or Slop demand**. Drew Pierson previous infrastructure venture affiliations are issuer claims, no verified VC financing round or same-day insider token purchases.
- Product's open records https://record.slop.cash/ give 2026 July 4,766 merged PR, August 5,588 merged PR and 2,674 reviews, 72 Solana payout transfers totaling **6,005 USDC** claimed by issuer; source explicitly says August payouts were **sent outside full verified settlement**, and a first completely automated settled month is still pending. Payments are **outbound rewards, not Slop revenue**. Issuer describes Slop as **pre-revenue** and token-free contributor payments. Token controls project treasury and business-policy governance only; no confirmed profit distribution, cash-redemption floor, or guaranteed buyback.
- Official Slop auction page says personnel $25k + infrastructure $3k + growth $4k + administration $3k = **$35k monthly spend**, reserves 20% auction inflows for LP and 80% for treasury. If all 45m offered tokens clear at the *same* hypothetical price `P=FDV/100m`: proceeds = `0.45*FDV`, treasury stablecoins = `0.36*FDV`, LP quote USDG = `0.09*FDV`, paired against 9m project-owned SLOP. Therefore estimated treasury runway at $1.2m/$1.5m/$2.196m FDV = **12.34 / 15.43 / 22.59 months** (ignores gas, refunds, new inflows, costs); **treasury cash not redeemable per token at par**.
- 45m auction plus 2m contributor tokens free at TGE, and 9m Treasury-owned in LP; quote liquidity scenario at $1.5m FDV 9m SLOP + $135k USDG. Illustrative classic `x*y=k` sale of 9m SLOP into **only this pool** without buy support gives ~$67.5k USDG, ~75% lower *marginal* price, not actual Uniswap v4 concentrated-liquidity swap quote. Actual LP position range/other routes unverified; 56% initial liquid allocations may face selling pressure. Do not extrapolate full-maturity DEX exit capacity from FDV.
- Price framework **ANALYSIS NOT VERIFIED FAIR VALUE**: $0.9m-$1.2m favorable, $1.2m-$1.4m speculative-but-defensible, **$1.5m absolute planned ceiling**; $1.5m-$2.196m high-risk chase, >$2.196m secondary-only. Main gate is absence of proven revenue, weak token buy-side economic requirement, limited quote liquidity and legal execution terms unconfirmed. $0.6m-$0.9m is possible *secondary market* downside, under floor $0.889m not a possible auction clearing price.
- **Conditional Nov08 first price observation**: If current PUBLIC clearing FDV <= **$1.2m**, preferred two limits: **700 USDG max FDV $1.3m** (0.013 SLOP) + **300 USDG max FDV $1.5m** (0.015 SLOP). If PUBLIC opens between **$1.2m and $1.35m**, optionally single **1,000 USDG Limit Max FDV $1.5m** only if independent quote, activity, sale validation and size indicate genuine viable fill. If public clearing >= **$1.5m**, **no bid**; preserve stablecoins for post-launch order-book/LP risk check. At the $1.35m-$1.5m intermediate stage avoid reflexive full $1000 due to thin margin; strong independent evidence required before even smaller trades. No automatic market buys, no last-minute chasing to auction cap.
- Worst-priced two-limit illustration assuming both $700 fully used at $0.013 and $300 at $0.015: **~53,846 + 20,000 = 73,846 SLOP**, cost $1000, avg ~$0.013541 per token (~$1.3541m weighted FDV). If all at single $1.5m cap, $1000 / 0.015 = **66,667 SLOP**. **Actual orders may partially fill at lower earlier prices, never guaranteed full budget**; site enforces capped allocation, possible oversubscription and refund.
- Exit stress examples if full $1000 fills at FDV **$1.5m**: FDV $0.5m => $333 token mark (-66.7%), $1m => $667 (-33.3%), $1.5m => $1k, $2m => $1,333 (+33.3%), $3m=>$2k (+100%), $5m=>$3,333 (+233%), **ignores realized liquidity, slippage, fees**. PM SLOP FDV contract and strike odds not verified; no numeric listing odds invented.
- Required live checks before ANY bid: official onchain immutable CCA/hook address and SLOP contract; a project-specific open round and per-wallet cap; latest clearing and latest bidder count/volume; exact USDG balance and ETH gas; formal legal/geography eligibility (Thailand unknown), swap and contract approvals; **no signing/transfer/automation without user request**.
- No public investor access to founder insider discounts, no institution effective cost or verified future CEX listing. If sale is oversubscribed, **the correct outcome under an honest limit may be few or zero tokens and refundable USDG**; this is acceptable and better than breaching valuation discipline.

---

## 2026-10-27 independently reconciled OFFICIAL X timing, Slop-specific Early Bid source and wallet balance

### 1. Dated official X announcement: exact times, UTC vs Bangkok

- **Source: screenshot user provided 2026-10-27 of first-party @umia_finance X** https://x.com/umia_finance/status/2114764262619120103 . The X text itself was blocked by web tooling; screenshot shows unambiguously **pre-bid opens Nov 5 2026 17:00 UTC**, **bidding opens Nov 7 2026 17:00 UTC**, **auction closes Nov 10 2026 17:00 UTC**, bid currency USDG, Robinhood Chain. This supersedes the inaccurate Oct26 countdown-derived date guesses below.
- **Correct Bangkok UTC+7 conversion**: gated start **Nov 6 00:00**; open/public start **Nov 8 00:00**; close **Nov 11 00:00**. Early **2 days**; public **3 days**; **5-day** aggregate window. Previously indexed Umia '4-day auction' Q4 teaser **STALE/INCONSISTENT** vs later specific first-party X.
- X Spaces with @SlopCash Oct 29 **14:00 UTC** -> Bangkok **Oct 29 21:00**. Useful for clarifying early cap, exact GitHub proof and legal terms.
- **TGE/claim/DEX**: Umia mechanism plans auction finalization and immediate seed of treasury-owned Uniswap v4 pool **if** minimum raise reached. Precise claim timestamp and tradable pool creation transaction, routing, gas, chain switch, specific $SLOP CA **not confirmed until deploy/close**, so don't promise tradability the instant clock strikes 00:00.

### 2. Exact original SLOP-specific Early Bid terms recovered in connected authenticated auction page

**First-party authenticated page text** https://app.umia.finance/p/slop-cash/auction, dated original 2026-10-26 browser tab (read-only), section "Early access":
> "The early bid is not a separate presale. It is the first 2 days of one 5-day auction, reserved for people already doing the work in open source and for Umia ecosystem participants. Open-source eligibility is proved privately on your own device through the Umia extension, using zkTLS proofs over your GitHub activity ... The exact criteria, with their cutoff dates, are published the day the early bid opens. The cutoff was set before any public announcement, so eligibility cannot be farmed after the fact."

Other exact same primary passage:
- **9m SLOP** for zkTLS contributor/reviewer/maintainer early round = 20% of 45m auction.
- **6.75m** tokens up to **15% of auction** for whitelisted ecosystem funds, **same clearing price** as everyone, no allocation discount, no side letters.
- "Other early access criteria, for **UMIA holders**, will be announced soon": **NOT YET ANNOUNCED**, holding UMIA alone not a guaranteed criterion.
- The precise minimum GitHub merged PRs, accepted reviews, maintainership, repository scope, account age, activity cutoff and wallet individual cap **ARE NOT PUBLIC YET**; the issuer says they are **published the day early bidding begins**. Avoid hallucinating a Sept30 cutoff, fixed number of PRs, or eligibility conclusion for user's GitHub.
- Per public <https://umia.finance/docs/tailored-auctions>, Umia verification can be through **any ONE** accepted zkTLS credential OR an explicit allowlist. Project-specific compatible provider for GitHub is determined by step configuration. Onchain validation hook enforces credential and bidding limits. Verified-wallet caps and whitelisted-fund individual limits may differ, and some wallet allowlist caps are not public. Public round starts Nov8 00:00 Bangkok and does **not require GitHub credential**; final sale legal/geographic eligibility still applies.
- Proof steps: install **official** Umia Chrome extension from project or https://umia.finance/docs/zktls-extension ; open signed-in Github in own browser; verify shown accepted credential when live; bind proof to connected wallet and submit permitted USDG bid. Do not provide GitHub password, private keys or screenshots containing bearer tokens. Proof self-validation does NOT count as a confirmed early allocation.

### 3. Wallet balance directly read (updated)

Read-only direct Alchemy RPC Robinhood mainnet chainId 4663 on **2026-10-27** for canonical EVM `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`:
- Native **0.002152148618870669 ETH** available for gas.
- Canonical USDG `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168` has **12.961754 USDG** (6 decimals), corroborates signed-in browser UI "12.96 USDG". **Older earlier same-day RPC reading of 0 USDG was superseded**, do not repeat that historical figure as live status.
- $1,000 USDG bid capital is currently **short 987.038246 USDG** if the intended amount is exactly 1,000 USDG. Existing ETH may suffice for some network actions but gas sufficiency must be simulated and bridge fees separately budgeted. No bid or transfer performed.

### 4. New important terms contradictions and business quality signal

- Main first-party Slop project page https://app.umia.finance/p/slop-cash currently claims 10m team time-vested **12-month cliff then monthly to month 36**, while longer authenticated auction **"Token terms"** states 10m time-vested **12-month cliff, 25% catch-up then continuous vesting to month 48**, and then 10m separate performance tranche. **OFFICIAL DOCUMENTS DISAGREE**; lock-up schedule remains **INCONSISTENT / VERIFY DEPLOYED META-VEST CONTRACT**. Never silently choose one.
- Profile also refers to "ecosystem and contributor programs" as **11%** in a descriptive paragraph while its binding-looking table lists 14%. Audit final legal/tokenomics configuration at deploy; percentage table sums to 100%.
- Slop authenticated auction page says **$35,000 monthly treasury operating budget**, staff $25,000, infrastructure $3,000, marketing $4,000, admin/legal $3,000; treasury funds after 20% LP => $320k at $400k minimum (about **9.14 months** of monthly draws), $800k at $1m raised (about **22.86 months**). **Issuer stated proposed budget**, subject to contract enforcement and income; NOT current audited profit.
- 2026-10-02 issuer press https://chainwire.org/2026/10/02/umia-opens-its-platform-to-outside-projects-with-slop-cash-from-elizaos-creator-shaw-walters-the-first-to-be-announced/ asserts August 2026 contributor payout **6,005 USDC / 72 transfers**. Independent read-only public index https://record.slop.cash/ explicitly states **August payouts sent outside verified final settlement flow** and cycle still shows August as not formally settled. This is an important real payment versus full product workflow distinction: actual Solana payment signatures exist, but **first complete automated verified settlement cycle remains pending**.
- IPO pre-TGE style market: **NO independently identified SLOP-specific liquid prediction market** with historical probabilities or TGE FDV settlement. Found Polymarket `Umia FDV above...` relates to **$UMIA platform token**, which has ALREADY launched and settled; **do not transfer those event probabilities to $SLOP**.
- Geo/legal gate: browser page lists 7 sale terms, including "Eligibility; Sanctions and Geographical Restrictions", but expanded text and specific excluded nations not fully read. The issuer's public page says final T&C published before early bidding. **Thailand eligibility UNVERIFIED**, do not claim permission or restriction without first-party text.
- Source classification: dates from firsthand user screenshot of official X, detailed gated policy and operating budget from read-only original Umia auction page, USDG/ETH from direct chain RPC, main first-party profile https://app.umia.finance/p/slop-cash, project operations from public GitHub/reconciliation. Future allocation, final claim, listing and live token contracts **UNVERIFIED**.

### Decision and fund protection

`INTENT_1000_USDG / NOT_BID / USDG_BALANCE_12_961754 / EARLY_ELIGIBILITY_PENDING / PUBLIC_OPEN_NOV8_00_BANGKOK / TOKENS_NOT_LIVE / NO_TRADE`. Do not modify active portfolio for merely announced intent; no new alerts/automation requested. This record corrects **dated factual mistakes** and adds durable gating and later primary policy, rather than a redundant project record.

---

## 2026-10-27 refreshed auction configuration and user $1,000 participation research

**Evidence status:** Important previous `WAIT_FOR_FINAL_AUCTION_TERMS` gaps partially resolved by official Umia project/auction pages. This update supersedes old 2026-10-09 `TBA` prices, supply, tokenomics and minimum raise. **User plans to bid ~$1,000, not yet funded, approved or placed.** No new monitor, automation, wallet transaction, or actual user qualification established.

### Current official sale parameters

- Auction primary https://app.umia.finance/p/slop-cash/auction , first-party Slop profile https://app.umia.finance/p/slop-cash , auction mechanics https://umia.finance/docs/tailored-auctions .
- Chain: **Robinhood Chain MAINNET, chain_id=4663**, native gas **ETH**. Official docs https://docs.robinhood.com/chain/connecting/ .
- Currency **USDG**, shown directly on user's official sale-page screenshot 2026-10-26 ~17:12 Bangkok, *not* Base USDC; canonical **Paxos Robinhood USDG** `0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168`, 6 decimals, corroborated by Paxos https://docs.paxos.com/guides/stablecoin/usdg/mainnet and Robinhood docs https://docs.robinhood.com/chain/contracts/ . Never fund Binance/Base USDC directly to sale address or substitute fake USDG token.
- 100,000,000 SLOP fixed, early clearing price floor **$0.00889/SLOP** (FDV $889K), auction max price **$0.02196** (FDV $2.196M), **$400K minimum raise**, **45,000,000 auction SLOP = 45% supply**. On official site and screenshot committed **$0**, NOT YET OPEN / no sales at time.
- Early access = first **2 days**, proof/allowlist; all others can bid after first 2 days, according to official auction page. Overall project auction **4 days** (launchpad page).
- User screenshot countdown `Auction starts in 9d 23h` dated filename `20261026-171259`. **INFERRED schedule**, start ~2026-11-05 ~17:00 Asia/Bangkok (10:00 UTC); public after ~2026-11-07 ~17:00; completion ~2026-11-09 ~17:00. Exact confirmed UTC date/time and deployed contract block times **UNVERIFIED**, static official launch card still says `Q4 2026`. Do NOT send exact-time alerts / assert exact launch from inference.
- Successful close → migration to Uniswap v4 **Robinhood Chain** with 20% auction proceeds paired with **9,000,000 LP token allocation**, remainder to guarded project treasury; token buyers are 100% **unlocked at TGE**, and claim after close via Umia. **No independently verified SLOP canonical ERC20 CA, auction CCA address, actual LP address, confirmed launch transaction, claim timestamp, detailed user fee/cap or transfer availability yet**; project's public page explicitly says `Contract address: (added at deploy)`.
- Failure below $400k at close → all bids refundable in full by documented contract mechanism; during sale, bids generally locked/not freely cancelable; unspent amounts refundable, not an assurance against network fees/temporary unavailable claims. At auction cap 45m*$0.02196=$988,200 max gross if all tokens placed at max price; floor sell-through 45m*$0.00889=$400,050, approximately the soft minimum. Actual total raised depends fills and paid price.
- Sale tokenomics official first-party current page: Auction 45m (45%, **9m of these early zkTLS**, **6.75m reserved for whitelisted funds**, **remaining nominal 29.25m other public**, all priced by relevant clearing mechanisms; not fixed early discount), team 10m (10%, 12-month cliff then monthly vest to month 36), ecosystem/contributor programmes 14m (14%, governed/locked at TGE), contributors 2m (2%, unlocked TGE), protocol LP 9m (9%, protocol owned), treasury 8m (8%, governed), Umia provider 2m (2%, status not included in platform's declared TGE liquid 56%), performance reserve 10m (10%, five 2m tranches on 30d TWAP achieving 2x/5x/10x/20x/50x auction price); official first-party explicitly **56m (56%) TGE liquid** = auction 45m+LP 9m+contributor 2m. **Verify whether particular private/early allocations can be bid by this user and distinguish total liquid vs free-floating market sell supply**.
- Founders named by issuer: **Drew Pierson CEO, Shaw Walters CTO (elizaOS)**. Original Slop main site has public scored merged PRs and some actual payouts, but launchpad acknowledges **pre-revenue** business: project sponsors pay contributors in stablecoins without requiring SLOP, token governs treasury and fee schedule, not direct contributor payment rights. No issuer-verified ICO tokenholder dividends or rights to redeem treasury at par.
- Umia **general** Tailored Auctions allow extension verified proofs, named fund/angel allowlists, capped open rounds and open rounds. Actual **Slop eligibility criteria and per-wallet cap have NOT been independently reconstructed from immutable hook configuration or an exact issuer criterion sheet**. Project social posts reportedly refer to GitHub contribution/reviews/maintainer history through **2026-09-30** as early access; **UNCONFIRMED exact GitHub threshold**; cannot assert a single merged PR qualifies or that this user is eligible. Full Slop sale legal T&C and jurisdiction/geoblock list still pending; general platform documents require legal eligibility, no public Thailand-specific exemption established.
- User canonical EVM `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`, directly queried Robinhood mainnet with Alchemy `eth_getBalance=0.0000207854087808 ETH`, direct canonical USDG `balanceOf=0`, `decimals()=6`, on 2026-10-27. **Not funded for proposed $1000 USDG bid**. Gas ETH tiny; check actual fees when funding. This observation does not address Binance/CEX or other wallet funds.
- Uniswap v4 sale/auction infrastructure mainnet verified in Umia docs https://umia.finance/docs/contract-addresses/robinhood-chain ; Certora audited core Umia infrastructure per issuer (https://umia.finance/docs/security); Slop own payout contracts mainnet production/audit scopes differ and are **NOT a clean token launch final-code audit guarantee**.

### $1,000 hypothetical full-fill reference, no allocation guarantee

`filledTokenQuantity ≈ 1000 / actualAverageUsdPerSLOP` (before refunds/fees and only if entire budget spent), FDV at 100m fixed supply.
- At floor **$0.00889** ⇒ **~112,485.94 SLOP**.
- At $0.012 ⇒ **83,333.33 SLOP**, FDV $1.2m.
- At $0.015 ⇒ **66,666.67 SLOP**, FDV $1.5m.
- At $0.018 ⇒ **55,555.56 SLOP**, FDV $1.8m.
- At cap **$0.02196** ⇒ **~45,537.34 SLOP**.
- Clear price monotonic and variable by block; earlier eligible bids may obtain lower time-weighted paid price than public, but **one cannot assert all $1000 fills, profit, exact end price or guaranteed claim at an inferred calendar time**. Public and gated per-wallet caps may restrict $1000. More expensive later spot or cheaper spot both possible.
- **Value-risk**: 56% initial token liquidity vs only 20% proceeds USDG LP collateral; minimum raise $400k → ~80k USDG pool side, upper boundary $988.2k → ~$197.64k, *scenario—not funded TVL*. Token fee capture from platform contributions is yet unproven, because funders/contributors use stablecoins and $SLOP governs only Slop treasury.
- **Operational gate**: `USER_INTENT_ONLY / NO_BID / NO_FUNDS_COMMITTED / NO_EXECUTION`; before action: confirm exact dates/claim, approve verified USDG token, gas, exact deployed Slop issuer contract, capped eligibility, legal terms/geography and withdrawal/refund rights. Do not add this prospective purchase to active portfolio yet.

---

## Historical research snapshot, 2026-10-09 (superseded where terms now known)

## Identity and first-party sources

- Project: Slop Cash (open-source contributor reward/funding platform).
- Website: https://slop.cash/
- Product/score rules: https://slop.cash/verification
- Umia issuer/auction: https://app.umia.finance/p/slop-cash/auction
- Umia launchpad: https://app.umia.finance/
- Umia auction mechanism: https://www.umia.finance/docs/tailored-auctions
- Public source repository identified for follow-up ownership/commit verification: https://github.com/SlopDotCash/slopdotcash (published as `slop.cash`; official website/GitHub ownership attribution not independently chain verified).
- Umia contract source: https://github.com/umiafinance/protocol
- Launch announcement (press release; organizer claims, not independent product/revenue proof): https://chainwire.org/2026/10/02/umia-opens-its-platform-to-outside-projects-with-slop-cash-from-elizaos-creator-shaw-walters-the-first-to-be-announced/

## Current first-party launch page (retrieved 2026-10-09)

| Field | Status / value | Evidence |
|---|---|---|
| Token ticker | `SLOP` | Umia Slop Cash auction page |
| Planned issuance chain | Robinhood Chain (launch card) | Umia launch page |
| Total supply | **100,000,000 SLOP** | Umia auction |
| Auction tokens | **45,000,000 SLOP = 45%** | Umia auction |
| Liquidity financing | **20% of auction proceeds** to seed market liquidity; remainder to project treasury | Umia auction |
| Auction date | **Q4 2026**, **4-day** sale shown; exact start/end TBA | Umia launch card |
| Clearing price / price range | **TBA** | Umia auction |
| Sale FDV / launch valuation | **TBA** | Umia auction |
| Minimum successful raise | **TBA** | Umia launch card |
| Per-wallet min/max | **UNCONFIRMED** for Slop Cash | No Slop-specific published binding details verified |
| Actual early-bid qualification | **UNCONFIRMED** for Slop Cash | Early access is gated, but Slop-specific proof parameters not yet validated |
| Canonical SLOP token CA | **UNCONFIRMED / not verified** | Do not trust lookalike tickers or assume token live |
| TGE / actual LP listing / claim | **UNCONFIRMED / not live-verified** | Launch is still upcoming |
| Insider allocation / unlock schedule | **UNCONFIRMED**, do not import Umia's own tokenomics | Slop-specific binding schedule not verified |

## Early Bid mechanics and qualification gate

- Slop launch page says verified wallets can bid before public wallets; **everyone may participate after the first two days** of the displayed four-day auction. Dates are not yet given.
- Umia Tailored Auction uses Uniswap Continuous Clearing Auction buckets: eligible early bidders may receive earlier/lower average execution prices but **no guaranteed fill or guaranteed profit**. Each bid specifies budget and max price. Unspent bid budgets are refundable in the described mechanism.
- Possible general authorization modes include Umia Extension zkTLS and organizer allowlist. These are **framework-level methods**, not a confirmed Slop Cash criterion.
- A previous conversation mentioned detailed GitHub qualifications from another assistant. Treat as an **investigation lead**, **not verified Slop Cash Early Bid rules**, until the exact Slop auction credential schema or official proof UI appears.
- Official docs: https://www.umia.finance/docs/tailored-auctions
- Critical pre-bid checks: verify exact zkTLS credential and eligible GitHub account, wallet caps, chain USDC requirements, max-price cap, minimum raise, effective FDV, liquidity seeding, deployer/owner privileges, TGE/token-claim mechanics and refund path.

## Product and team reality

- Announced founders: **Shaw Walters** (elizaOS framework founder) and **Drew Pierson** (previously Arweave, Orderly Network, Ava Labs). **Issuer/press statement**, not independent proof of their employment histories.
- Public Slop site and open repository document a GitHub-based flow: contributor submits PR, maintainer approves/merges, scores are accounted for, proposed payouts and receipts are publicly tracked. This supports a real developed application rather than a one-page token narrative.
- Published site states contribution scores are **not balances or guaranteed wages**, and payments require separate organizer funding, approval and actual settlement. Do not infer recurring paid customers, sustainable revenue or token demand solely from scoring data.
- Product stage: **at least Level 1 (public source/software)**; a higher business/fee stage is **NOT independently quantified** as of this review.
- Token/readiness stage: launch intent and platform prelisting page confirmed; canonical deployment/claim/market execution **not verified**.

## Token value / risks

- Slop site says funding pools/payouts operate in USDC; SLOP is for the venture treasury/decision-market layer. **Token usage must not be confused with a requirement to earn contribution rewards**.
- Without final price and cash budget, FDV and number of SLOP for any proposed bid **cannot be calculated**.
- Founder/team/insider allocation/vesting, legal claim to treasury proceeds, smart contract roles, Uniswap v4 pool depth, max cap, actual early-bid rules and buyer claim/unlocks are gating risks.
- Proposed decision: `WATCH`, with no capital committed or investment capital earmarked. User has stated intention to participate once conditions are acceptable; this does **not** establish any purchased/allotted position.

## Exact next manual review gates

1. Open the canonical Umia Slop Cash page; capture the early-bid `Verify` requirements and check actual account eligibility, with redaction of private login data.
2. Obtain the final immutable auction configuration: chain ID, USDC contract, min raise, sale dates, price floor/cap, exact allocations, wallet cap, locked/unlocked percentages and verified SLOP contract.
3. Calculate executable bid quantity/expected launch FDV from the actual max-price/auction curve; compare with comparable launches and concentration/liquidity.
4. Independently verify the token address, launch contracts, refund mechanics, liquidity and permissions before any user-signed transaction.
5. Only after actual user-authorized participation and on-chain evidence, create a `positions/` operational position and update `portfolio/current.md`. Do not count intent as an investment.

Source classification: issuer/launchpad first-party statements `OFFICIAL_CLAIM`; public code/product observations `PRIMARY_SOFTWARE`; valuation and early-bid upside `UNRESOLVED`/future analysis.
