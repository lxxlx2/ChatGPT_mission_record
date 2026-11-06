# Slop Cash / SLOP — Umia auction participation research

## 2026-11-06 USER OVERRIDE: skip SLOP public ICO, evaluate only post-listing spot

**Latest explicit decision (supersedes ALL prior public-only conditional bid proposals):** `ICO_PUBLIC_SKIP_USER_CONFIRMED / ZERO_PUBLIC_BID_INTENT / SPOT_ONLY_IF_POST_TGE_PRICE_LIQUIDITY_JUSTIFY / NO_TRADE`.

- **No SLOP ICO/CCA bidding in the public phase**, including no $100/$150 exploratory limit, no $300 tick28 limit, no early bid, no Market fallback, no permit request or token approval for the auction. Do not present the older $300 USDG/tick28 scenario as still authorized/current. Those figures remain in historical sections **for audit context only**.
- User wishes to **look at actual open-market/TGE trading later** and **buy only if price and conditions are attractive, otherwise abstain**. This expresses a conditional research/decision goal, **not** authorization to execute a spot trade or assume the old $300 ICO budget automatically applies to secondary-market purchases; spot amount and final execution require explicit user direction.
- For any future *user-initiated* spot analysis, read current **actual Uniswap v4/Robinhood Chain pool deployment, token mint and supply, tradable float, executable sell and buy quotes, USDC/ETH reserves, effective sell price impact, holder flows, CCA final clearing/bid basis, claim state and observable volume**. Distinguish live onchain values from webpage indications; never assume a pool, FDV, performance or price exists before verified. A pump, weak depth, high FDV or missing executable quotes can justify **SKIP**; declining price alone is insufficient evidence of value.
- Existing historical $1.464M tick28 cap was for **ICO price discipline**; current spot thresholds are **not automatically executable orders**. Research, wallet and production monitoring/trading remain `NO_GO`, unless the user separately authorizes an operation. Do **not** create monitors, alerts, fallback automations or emails.

---



## 2026-11-06 SLOP public ICO vs secondary-market decision update

**As of 2026-11-06 ~10:20 Asia/Bangkok.** Research only; NO_GO for trading. User still intends at most **300 USDG**, **PUBLIC_ONLY**, never raises the already recorded hard ceiling **tick28 $0.014640705882 / $1.464M FDV** without an independent new user decision. This section is an updated **decision recommendation** to prefer waiting for post-TGE onchain price/exit-liquidity validation rather than chasing the public sale.

### Current actual evidence (not a forward forecast)

- Authenticated official Umia page `https://app.umia.finance/p/slop-cash/auction` displayed **434,486 USDG total bid commitments, 173 bids, ~2,511 per bid**, **$0.00966** indicative clearing price (**~$965.5K FDV**), 45M auction tokens, $400K minimum and $0.02196 maximum token bid price. **0 already cleared** in early phase.
- Top displayed bids: **43,958; 15,000; 15,000; 15,000; 11,000 USDG**; first five sum **99,958 = ~23.0%** of aggregate. Bids != unique bidders and their max-price distribution was **not** independently decoded. Total commitments alone cannot imply a tick28 clear, guarantee sellout or predict a TGE listing price.
- Direct Alchemy Robinhood Chain query near head block **107266142**: CCA `0x901f26b42c61af93f548efa0fdf8df4d342b124c` `currencyRaised()=0`, `isGraduated()=false`; Umia hook `0xb8c877cf6ce506dbc3098cd086e3d4898659bd2d` zk-only committed counter **125,592.096084 USDG**, not total auction commitments because other valid server-permit paths exist. CCA public release remains tied to onchain `startBlock=108530471`; do not replace actual block with an unverified scheduled clock time.
- Official Slop profile snapshot on Nov6 shows approx **4.5K X followers** and early-bid announcements with view counts ranging from a few thousand to ~14K; social impressions **do not prove** conversion to unique buyers or post-TGE liquidity. Sources: https://www.sotwe.com/SlopCash , https://x.com/SlopCash . Team claims **11K+ scored merged PRs since July**; operator's https://record.slop.cash/ reports an October29 compiled prior 35-day sample of **6,150 PRs + 1,697 accepted reviews, 152 contributors, 6 repositories**, and **6,004.98 USDC** from 72 finalized *August* contributor payouts. The figures have different windows and definitions; the payments count is operator-indexed, not independently reproduced with RPC here.

### Crucial primary issuer operating filing published 2026-11-05

[Blockworks Slop Cash B1 v1.4 token transparency filing](https://blockworks.com/token-transparency/filing/slop-cash), **ISSUER-REPORTED**, says:

- **Pre-revenue**, no project-funded vault active / no protocol fee revenue as of filing. Published fees: **2%** from approved contributor payouts, **2%** on unused withdrawn vault funds, and **25%** of private security awards. Historic pilot payouts to contributors are distinct from protocol fee revenue.
- **$35,000/month capped treasury operations draw**, supporting both founders and operating expenses. Of gross auction proceeds **20% is intended for initial treasury-owned LP USDC**, leaving 80% for other treasury uses. At $400K gross, $320K/35K ~= **9.14 months at full monthly cap**; $658.8K gross implies ~$527K/35K ~= **15.06 months**. These are *maximum-draw runway illustrations*, not observed monthly burn. To gross $35K/month entirely from the **2%** contributor fee, absent any other fee channel, would require **$1.75M of monthly fee-bearing approved contributor awards**; this is a mechanical scenario, not currently achieved business volume.
- The native application and contributor payouts are funded in stablecoins and do **not require holding SLOP**; $SLOP provides governance only. Filing disclaims dividends, profit shares, buybacks, rewards/staking or fee-routing to tokenholders. Therefore high PR counts are evidence of product activity, not a mechanical source of SLOP buying demand.
- **56% nominal supply liquid at TGE**: **45M auction**, **9M protocol LP pool**, **2M unlocked contributor allocation**; note that LP-held inventory is not equivalent to all 56M being held by sellers. Of 45M auction, issuer states **9M zkTLS access** and **6.75M whitelisted-funds access** within auction allocation, with no hidden price discount; these are **access tranches**, not verified filled quantities.
- Token supply: direct Robinhood `totalSupply()` read **100M SLOP**, `decimals()=18`, token owner `0x96028de971a9d37404f5030f6284b40640e2d1a2`. Official [Umia VentureToken.sol](https://github.com/umiafinance/protocol/blob/main/src/tokens/VentureToken.sol) has **onlyOwner mint/burn/pause**. The filing states new mint/burn requires a successful governance decision market. Thus 100M is **present supply and no scheduled inflation**, not independently proven an irreversible immutable max supply against future governance; execution control requires further chain verification. This nuance should supersede any older unqualified "hard-capped supply forever" assertions.
- **Funding concentration:** first five early bid display positions ~23% of public aggregate, fairly small number of early bids (173), no realized price discovery for all 45M until public issuance, and market-side future token buyer depth **unknown**.

### Historical actual-mechanism comparisons, not SLOP forecasts

1. **Umia UMIA auction**, official https://umia.finance/tge: cleared **$0.36/UMIA** and sold 17.3M, Aug26–Sep2 2026. CoinMarketCap historical page https://coinmarketcap.com/currencies/umia/ reported **all-time high $0.956 on Oct29, 2026** (~**2.66x** auction clearing); this was ~57 days *after* TGE, not a verified opening-minute return. Distinct platform/governance capitalization and liquidity; not valid to assume SLOP reproduces this.
2. **Jack Butcher BALANCE Uniswap CCA**, official https://jack.art/credits/whitepaper: final close **0.000227 ETH/BALANCE** on Oct21, 2026 (268,750 units = 0.5% supply). Oct21 ETHUSD daily close **$2,470.77** from https://finance.yahoo.com/quote/ETH-USD/history/ implies approximate close-day translated auction price **~$0.56086**. OpenSea https://opensea.io/token/ethereum/0x3620540c994433d7b4a628c46d2ed5f92572ea07 reports **Oct21 ATH $0.1767** whereas Dexonomics https://dexonomics.io/eth/balance/0xd262227cd6ad883b3d85c5138f017f90aaac0ff3ce69136c36a7280dbd009a03 shows **Oct21 daily high $0.3509**. **These vendor high estimates conflict substantially** and should be used only as evidence that observed indexed secondary prices can fall below the CCA close, NOT a single proven onchain global ATH, universal bidder cost basis or realized P/L. BALANCE 0.5% auction float contrasts sharply with SLOP 45% auction; do not fit an empirical return distribution from these two samples.

### Forward decision gate (policy, not a backtested model)

- **Default WAIT / NO ICO bid at the current demand trajectory**, do not FOMO. If the Nov7 public-opening validated clearing is still below **tick24 $0.01254917647** (FDV about **$1.255M**), demand distribution does not imply imminent outbidding, and front-end signed permit works, an **optional small exploratory limit of up to 100–150 USDG** is a *judgment-based risk limit*, not an inferred probability of profit. The remaining overall $300 budget stays unspent for post-launch. The prior tick28 $1.464M remains an absolute maximum, **not a target execution price**. At >=tick24, prefer skipping ICO; >=tick28, DEFINITELY SKIP; no Market order and no raising cap.
- **Post-TGE Nov10/11 only after actual pool exists:** verify true final CCA bid cost/claim, Uniswap v4 pool price and effective executable buy/sell quotes for intended size, LP stablecoin reserves, swaps and sell pressure from early bidders/contributors. No purchase in first minutes solely to catch a presumed pump. If available quotes place **actual FDV at or below 1.0M–1.25M, selling is demonstrably possible and the LP is usable**, consider a small staged spot entry **$50–100 first**, total max $300 without a new user budget decision. These FDV levels are user-risk heuristics derived from prior cap/floor, not validated “fair value”. If market opens >$1.464M FDV, default skip.
- Stop/exit: avoid averaging down without fresh evidence, do not assume advertised 20% LP capital has migrated until check onchain, distinguish liquidity depth from total LP TVL, check price impact for a sell of the actual size. Favor no position if evidence insufficient.

**Source caveats**: Independent direct contract balances and page commitments proven; pre-revenue and fee policies are issuer filing, not an audited financial statement. Post-listing prices, future bid limit distribution and launch volatility are **UNVERIFIED**; scenario thresholds are **ANALYSIS**, not observed market data. No new trade, email, scheduled monitor, wallet action or production change.

---



## 2026-11-06 early commitment threshold vs sellout

**Question:** Can early-stage bids exceed the displayed 200K limit, meet the 400K minimum, or deny a $300 public-only limit bid at ~$1.464M FDV?

**Observed UI read:** 2026-11-05 latest logged browser context displayed *total committed* 208,817 USDG (52.2% of 400K minimum; earlier screenshot 206,817), *total raised so far* 0, clearing display $0.00889, current stage Early Bidding. Direct Alchemy Robinhood Chain read at block **106898408** confirmed `currencyRaised()=0`, `isGraduated()=false`, and validation hook `zkGlobalBidTotal()=39378057648` (39,378.057648 USDG); public release begins at block **108530471**. These figures are a snapshot, not a live orderbook forecast.

**Auction-specific static math, 45M SLOP:**

| Indicative price per token | Static 45M token gross sale amount |
| --- | ---: |
| floor 0.008889 | 400,005 USDG |
| 0.010000 | 450,000 USDG |
| tick24 0.012549176470588 | 564,712.94 USDG |
| tick28 0.014640705882353 | 658,831.76 USDG |
| 0.017000 | 765,000 USDG |
| maximum hook cap 0.021961058823529 | 988,247.65 USDG |

These are **unit price times auctioned token count**, not a mechanical committed-bid sellout threshold or sale forecast. The 400K graduation threshold, 45M total sale amount, and ~2.196M max token FDV are different concepts. A given *aggregate* commitment cannot prove how much supply will fill: per-bid maximum prices, residual emission schedule and entry time matter. Source: [Uniswap CCA docs](https://developers.uniswap.org/docs/liquidity/liquidity-launchpad/concepts/cca) and [technical documentation](https://github.com/Uniswap/continuous-clearing-auction/blob/main/docs/TechnicalDocumentation.md).

**Early-bid crowd-out risk:** Step 0 emits **zero tokens** until block 108530471. Nevertheless early *committed* budget is pre-positioned in the active book and will compete for every future issuance block. Thus early bidders cannot literally buy the 45M before the public issuance begins, yet sufficient price-aggressive early demand might drive the clearing price above our **tick28 $0.01464070588** before a public order can enter; then a new order at or below current clearing is invalid. If the price is already at the max permitted bid tick, the late public bidder may not be able to place any conforming bid. This is a **risk scenario**, not currently observed.

**The alleged 200K global early cap is NOT a universal committed-USDG cap:** Direct hook `zkGlobalBidTotal` reflects the zk credential path, which excludes successful server-permit bids according to [official UmiaValidationHook docs](https://github.com/umiafinance/protocol/blob/4b76b7b13399e440b318d9c479d7fc720b846d7b/docs/contracts/UmiaValidationHook.md). Earlier direct `zkGlobalMaxBidAmount` was 200K USDG, but the UI itself already exceeded 200K in total commitments; server permits are not constrained by this **same zk accumulator**. Cannot infer aggregate total early-stage budget ceiling or buyers' price ticks from page headline alone.

**Decision:** Maintain PUBLIC_ONLY, 300 USDG max, single limit tick28, NO_GO until the user authorizes an actual bid. At public start recheck (1) actual chain block and clearing price, (2) price-tick demand curve and total *valid* active amount at/above tick28, (3) verification permit availability, (4) contract bid price gate, (5) actual wallet approvals, and (6) likely execution slippage/fills. If current onchain clearing >= tick28 price, **do not raise user's ceiling or switch to market**. No bid, transaction, monitoring, email, or automation performed.

---


Updated: 2026-11-05 Asia/Bangkok (fresh official SLOP mint and funded auction contract; conditional early-bid economics; older 2026-10-27 research retained)
Scope: ICO / pre-launch token auction / Robinhood Chain
State: `USER_INTENDS_TO_PARTICIPATE / CURRENT_$300_USDG_PUBLIC_ONLY_PLAN / NO_FUNDS_COMMITTED`
Decision classification: `WATCH` (not SETUP or ACTIVE).
Execution: `NO_GO`; the user has expressed interest only, with no authorization for funding, wallet signature, live trading, scheduling or monitoring.

## 2026-11-05 LATEST USER DECISION: $300 PUBLIC-ONLY, NO EARLY WHITELIST BID

**As-of:** 2026-11-05 ~22:15 Asia/Bangkok, original SLOP CCA has yet to open. The user **explicitly canceled intended early-whitelist participation** after a rule change and specified **public auction only, maximum 300 USDG**. This supersedes the prior $300 early-bid allocation recorded below (which remains visible only as historical context). The user did not give a link or describe the specific rule change; do not invent its substance. **NO BID / NO SIGN / NO MONITOR / NO AUTOMATION**, WATCH, trading NO_GO.

### Verified current status
- Official SLOP page https://app.umia.finance/p/slop-cash/auction still displayed `Upcoming`, default order type `Market`, `Verification` widget, connected `0x3Df4...Ea7C`, 389.42 USDG available, 0 committed. Connected Alchemy direct Robinhood network latest observed head `106836020`, below immutable `startBlock 106868933` and public issuance `108530471`, CCA clearing price `$0.008889`, `currencyRaised()=0`, hook `zkGlobalBidTotal()=0`, current hook cap `$0.0219610588`, wallet `389.420578 USDG`. Zero prelaunch commitments do not establish public demand.
- Latest original Umia FAQ https://x.com/umia_finance/status/2118352696742695355 states public open approximately **Nov 7 16:15 UTC = Nov 7 23:15 Bangkok**, while contract enforces **block 108530471**. Anyone can publicly bid in principle, without a per-wallet max, but currently deployed hook **requires a per-bid amount-bound server permit** on steps 1/2/3. Failure to obtain signed permit or too-late inclusion can prevent execution.
- https://umia.finance/blog/understanding-your-bid: amount + maxPrice limit; price monotone; budget spread over remaining emission steps; arriving later reduces exposure to earlier low clearing prices. A max bid cannot be at or below current clearing; final cost can be below max. Public cap eligibility is not a guaranteed fill.

### New conditional decision proposal, superseding earlier two early-white-list bids
- **Primary public-only scenario:** one `$300 USDG` **Limit** at SLOP CCA price **tick 28**, `$0.0146407058823528/SLOP` (~**$1.46407M FDV**), only if first public onchain clearing is **comfortably below cap** and app confirms onchain max bid before signing. One order reduces per-bid signed permit and execution friction relative to two public bids; does **not** promise 100% fill, and budget may be partially refunded.
- **Opening observation/action thresholds** are subjective, not contractual or statistical probabilities: if live clearing **< $0.011**, prefer full $300 one-limit bid; if **$0.011 to $0.01255**, same bid remains considered but demand/price momentum needs quick review; if **$0.01255 to <$0.01464**, reduce intent to $100 or skip due to poorer prospective risk/reward; if **>= $0.01464**, skip, DO NOT switch to Market or raise cap to maximum permitted price. User's prior risk boundary remains $1.5M FDV.
- At maximum limit, $300 fully spent implies at least `300/0.014640705882 = 20,490.81 SLOP`; at hypothetical exit FDV $1M/$2M/$3M/$5M, mark ~$204.91/$409.82/$614.72/$1,024.54; P&L ~$-95.09/+109.82/+314.72/+724.54, excluding slippage, gas, fees, liquidity depth and unlock/claim execution. Actual CCA price path could improve average tokens-per-dollar or leave USDG unspent. The user can personally sign only after checking the exact tick grid and details.
- **Do not chase to $0.021961** to force budget into tokens; public stage may become congested/closed if clearing reaches max. Requested $300 is a maximum budget, not a guarantee every dollar will be spent.
- No independent fully reproducible evidence of the unspecified user-mentioned "rule change" was established. This update does **not** claim to have investigated that missing text. Confirm final auction terms and onchain hook state at the actual public entry window, and show only the current option.
- Earlier early bid strategies and $1,000 scenarios below remain **historical/superseded**, not executable current-user intent.

---

## 2026-11-05 revised intended early-bid exposure: $300 USDG, tick-aligned $200 + $100 limit plan

**Latest user's explicit allocation intent supersedes the earlier uncommitted $1,000 plan:** user plans **$300 USDG total** for the SLOP whitelist prebid; **no actual bid, approval/signature or transfer authorized by this research request**. Risk objective prioritizes low realized cost while retaining exposure to higher-price emissions; preserve prior **max FDV $1.5M**. Historical $1,000 scenario and source research are retained below only as past assumptions, not current capital allocation.

### Direct current account/auction verification

- Direct connected first-party browser tab https://app.umia.finance/p/slop-cash/auction showed wallet `0x3Df4...Ea7C`, **389.420578 USDG** available, `Market` currently selected, `Verification / Lock in your allocation` (no validated whitelist completion verified), `Upcoming` and price floor **$0.008889**. One source message listed the countdown `1h 26m` but browser snapshots may lag; rely on immutable block.
- On 2026-11-05 late evening Bangkok time direct Alchemy read-only Robinhood Chain returned head **106819891**, `CCA.currencyRaised()=0`, `Hook.zkGlobalBidTotal()=0`, `CCA.clearingPrice()=$0.008888999999999902`, `zkGlobalMaxBidAmount=$200000`. This is before `startBlock=106868933`, so zero prebid is not independent hype evidence. User has sufficient USDG already for current $300 intention; separate native chain ETH gas needs reconfirmation.
- 2026-11-05 official FAQ https://x.com/umia_finance/status/2118352696742695355 says early opening approximately **16:15 UTC / 23:15 Bangkok**; actual first accepted bid determined by block 106868933. No tokens released before public step1 `108530471`.

### Conditional plan for manual user action once verified

- Route: Prefer **verified GitHub/community** if it succeeds; dashboard says `Verification` and current onchain hook step0 verified-wallet limit **$3,000**, enough for $300. A user's unverified 50-star eligibility must not be asserted. Do not confuse with $250 base Umia Pass quota; choosing first route determines this sale's lane.
- First order **$200 USDG, Limit tick24**, onchain max **$0.0125491764705881/SLOP**, implicit **$1,254,917.647 FDV**. Second order **$100 USDG, Limit tick28**, max **$0.0146407058823528/SLOP**, implicit **$1,464,070.588 FDV**.
- Both limits sit at actual tick boundaries computed from live CCA `floorPrice()/tickSpacing()`. **Do not enter approximate rounded literal `$0.01255` or `$0.01464` blindly**: some UIs round upward; use exact tick selections, or FDV value mapping and inspect final transaction confirmation and allowed max before signing. UI currently exposes only `Market` and `Order type` toggle in the read-only DOM; no post-toggle exact labels observed. We cannot claim a successful click or verified details of an unobserved Limit form.
- Submit as **two independent orders only if front-end allows multiple early bids for the same wallet and proof lane**; contract hook permits repeated verified bids while enforcing cumulative `stepMaxBidAmount`. Two tx + possible approvals, check actual order IDs; do not assume both succeeded on first confirmation.
- If the interface prohibits multiple orders or price ticks are not displayed accurately, **safer one-order fallback** for a user prioritizing participation over higher low-cost segment: **$300 Limit tick28 max $0.0146407058823528** (max FDV $1.464M). This is an analytical alternative, not a trade instruction already executed; if the UI cannot guarantee an actual final cap ≤$1.5M, do not submit a Market order as a substitute.
- At both limits completely spent at respective highest allowed prices, token allocation **~15,937.30 + 6,830.27 = 22,767.57 SLOP**, cost **$300**, worst-price average **$0.01317664**. At post-TGE price $0.01/$0.02/$0.03/$0.05, **hypothetical mark** ~$227.68/$455.35/$683.03/$1,138.38, corresponding P&L **-$72.32/+$155.35/+$383.03/+$838.38** before slippage/gas/fees. **No probability or executable sell quote implied; could fill only partially or zero.**
- If both orders clear at earlier lower clearing prices, more tokens per spent USDG may be acquired, or some USDG returned. Early zero issuance, valid-server-permit public, $200K zk pathway and cap-hit no-new-bid all remain binding.
- Verify actual official Robinhood 4663 network, canonical SLOP/CCA/USDG addresses, **verified-access proof**, current `maxBidPrice`, current `zkGlobalMaxBidAmount-zkGlobalBidTotal`, actual USDG and native gas; `Limit` is mandatory to enforce plan, NOT website default `Market`. Check each transaction receipt, BidSubmitted/bid id, budget, encoded max Price, and snapshot demand. No code or wallet changes performed.

## 2026-11-05 Umia first-party SLOP auction FAQ and user-supplied Grok X demand reconnaissance

**Evidence time:** 2026-11-05 Asia/Bangkok after Umia's ~21:40 local X article (before live auction start). Evidence split: first-party Umia article and connected Chrome X browser, independent Alchemy Robinhood 4663 direct read, and **Grok summary supplied by user (not independently verified tweets)**. This section updates/clarifies earlier speculative interpretation but does not authorize trading or project monitoring.

### Confirmed first-party publication (exact URL)

- Official X article https://x.com/umia_finance/status/2118352696742695355 , title **Slop Cash: Auction FAQ**, directly read in connected Chrome account; full text includes early route qualifications, first/public periods, withdraw/refund, cross-chain bid, liquidity/treasury and sale mechanics.
- **Timing revision:** Umia now gives approximate **2026-11-05 16:15 UTC (= Bangkok Nov05 23:15)** at immutable CCA start **block 106868933**, and public opens approx **2026-11-07 16:15 UTC (= Bangkok Nov07 23:15)** at block **108530471**. The earlier Oct announcements said 17:00 UTC, which is a stale *clock estimate*, not the canonical block activation. Actual auction closing remains chain-enforced **endBlock 111022780**, previously advertised around Nov10 17:00 UTC / Bangkok Nov11 00:00; chain timing can drift from clock estimate. `claimBlock=111023357` enforces claim after end; FAQ's "at the close" is an indicative claim workflow, not a promise of an immediate same-block claim.
- **No separate early-sale tranche or independent cheap price:** FAQ explicitly says all bids share same auction, same supply, same price at any given moment; step0 has zero issuance. Verifier early bids become effective for the first public emissions, subject to auction price and eligibility; no guaranteed 9m segregated discounted pot.
- Early route **Umia Pass**: ≥1,000 UMIA held in bidding wallet continuously for seven days; $250 base, up to $2,500 with boosts (5,000 UMIA +1x, 20,000 UMIA +5x, any Echo sale +3x, FOMO holding >5 days +1x, FOMO >30 days +5x, approved clan +2x, capped 10x), verified in Umia Extension.
- Early route **Slop community**: eligible elizaOS/SlopCash contributions or reviews **between Jul1 and Sep30 2026**, **OR owning a public GitHub repo with ≥50 stars**; $3,000 per wallet, original browser live shows $3k and direct step0 `stepMaxBidAmount=3,000` USDG. **FAQ's date phrase grammatically applies to PR/review contributions, not explicitly to the date when a repo obtained 50 stars; no published immutable historical 50-star cutoff confirmed.** Do not claim eligibility for user's repository without a real zkTLS extension proof (as of earlier Git repo check had only 1 star). Extension Chrome desktop only; wrong signed-in GitHub identity causes failure.
- Early **funds/angels** are allowlisted with individual caps, same auction price with no discount; do not assume the $200k zk global cap includes their separate permit lane or represents total early budget capacity. The first path chosen for this sale persists, so selecting $250 UMIA Pass instead of higher-cap $3k community route can be disadvantageous if both are available.
- Official FAQ: **NO per-wallet cap for public stage**; current direct contract hook has steps 1/2/3 `verifyEveryBid=true`, permit enabled, no zk proof providers, therefore a **valid server-signed amount-bound permit is required per PUBLIC bid** even though Umia offers that route to the public. This practical source of admission latency is not disclosed prominently in FAQ. Operator can change verifier gate/cap; check at signature time.
- Bids consist of USDC-equivalent USDG budget and max price, not a fixed token quantity. Per-block fills occur during public phase with clearing prices monotonic nondecreasing, capped by current hook max **~$0.02196105882**. If capped-demand exceeds remaining available tokens, equal-priced orders are reduced pro rata and unused budget refundable. **Bid submit function strictly requires bid maxPrice > current clearing**, so no guarantee later entry at cap if current clearing already equals cap.
- Active bids cannot be canceled; **early exit of a disqualified or partially filled bid after graduation** is available using CCA `exitPartiallyFilledBid` with the required checkpoint proofs, not arbitrary active cancel. Full refunds at close if cleared currency below **$400K** min; successful sale bidders must exit/refund and claim, with gas and execution steps.
- **No minimum bid size.** Official FAQ claims user can initiate cross-chain bidding with *any coin on any chain* in the app; this is a front-end/bridge service claim, and doesn't prove arbitrary ERC20 or chain will complete before exact source block. For time-critical bid, cross-chain timing/exchange rate/bridge failures are additional risks.
- At close, issuer claims 20% actual proceeds pair with 9m SLOP in Uniswap v4 treasury-owned position; 80% treasury, programmatic $35k monthly spend, extra spending via decision markets, no direct team sweep. Until deployment and control verification, this remains **issuer platform claim**. Token buyers do not automatically receive profit sharing or an enforceable claim on payouts.
- Direct original source: https://github.com/umiafinance/protocol/blob/4b76b7b13399e440b318d9c479d7fc720b846d7b/src/periphery/UmiaValidationHook.sol; Uniswap CCA https://github.com/Uniswap/continuous-clearing-auction/blob/main/src/ContinuousClearingAuction.sol ; independent live CCA/hook params documented in preceding section.

### User-provided Grok/X reconnaissance, **not verified independent X corpus**

User supplied a 72h X summary suggesting **medium-low social discussion intensity**, relatively active Chinese ICO reposts, few independently visible explicit budget-size commitments (one $250 public-round expression), no observed prominent fund/KOL size disclosures, and **no verified evidence early $200k is exhausted**. Relevant cited accounts/posts in supplied research: https://x.com/SlopCash/status/2117948704426508554 ; https://x.com/umia_finance/status/2118299013904470161 ; https://x.com/ustyianskyi/status/2118349358819049698 ; https://x.com/zenyield/status/2118304777713148098 . Other handles without URLs in supplied summary are leads, NOT independently counted signals.

- Categorize Grok conclusions strictly as **UNVERIFIED THIRD-PARTY SOCIAL SCAN**; no independent exhaustive original-post count/unique participant sample, impression normalization, wallet linking, bid-signature readbacks or onchain committed budget. Do not take "moderate-low participation" as verified dollar demand.
- The author's X article independently verifies eligibility/timing and exact $3k/$250 base cap; supersedes Grok's uncertain "$5k" suggestion.
- Grok's `$1m/$1.5m/$2.196m FDV requires $450k/$675k/$988k` is simply `45m × static price`: **an all-token-at-one-price valuation illustration**, not a necessary/sufficient demand threshold for a time-weighted CCA with heterogeneous bids and partial fills. Must not convert it into inferred capital commitments or precise outcome probabilities.
- A KOL not disclosing planned amounts does not imply absence of large bidders, and English-language post engagement is not a strong bound on funds/angel permit lanes or cross-chain public participation. We do not infer guaranteed discount or max-price outcome based solely on hype.
- Direct Alchemy prelaunch query latest at **block 106815953** returned `CCA.currencyRaised()=0`, `Hook.zkGlobalBidTotal()=0`, `zkGlobalMaxBidAmount=$200000`, `Hook.maxBidPrice=$0.02196105882352917`. These zero readings are **pre-start**, unsurprising and not evidence of post-open demand.

### Concrete decision relevance and bounded to-dos

1. **Whitespace correction:** previous stated exact Bangkok 00:00 Nov6 is a time estimate now superseded by first-party new approximate **23:15 Nov5**. Use immutable CCA block for actual start and public entry.
2. **Early community** route potentially 50-star repository eligibility does NOT have a clearly published historical star cutoff; previous blanket Sep30 restriction was overbroad. Still require actual ≥50 stars and valid on-device verification before assuming admission.
3. Separate the **two demand questions**: early zk submission remaining under $200k vs exact CCA valid competing limit-price distribution as public phase opens. An overfull zk cap ≠ token sale sold out.
4. Public stage has no formal per-wallet cap but every bid currently requires server-signed permit; public active bids may come from arbitrarily large or quiet accounts; X hype cannot establish high fill or predict exact price.
5. Any intended split order must be tick-aligned: actual <= old ceilings $700 at **$0.01254917647** and $300 at **$0.01464070588**, if both can be submitted by the UI under one eligible route. Do not silently use off-grid exact $0.013/$0.015.
6. Preserve `WATCH / NO_GO` and original max planned exposure $1,000 USDG; user has not authorized bid, wallet funding, automation, monitoring, notifications, or email.

---
## 2026-11-05 SLOP CCA actual immutable steps, hook public-permit gate, bid tick grid and game-theory audit

**Scope:** User requests strict rules-first, contract-second confirmation whether early/public phases must elapse; investigate omitted bidding games. Read-only direct RPC on Robinhood Chain `chainId=4663` before the first prebid block. This is a documentary update only: `WATCH / NO_TRADE / NO_AUTOMATION`. Prior price scenarios remain historical hypotheses; this section supersedes technically invalid off-grid price suggestions without changing the user's **$1.5M FDV risk ceiling**.

### A. Contract identities and directly read immutable time/issuance schedule

- Official first-party https://app.umia.finance/p/slop-cash/auction canonical CCA `0x901f26b42c61af93f548efa0fdf8df4d342b124c`; token `0xfeb4e36fa4a2a494ff25ae4a63491e4c584a67ae`; USDG `0x5fc5360d0400a0fd4f2af552add042d716f1d168`.
- Direct CCA `startBlock()=106868933`; `endBlock()=111022780`; `claimBlock()=111023357`; `pointer()=0x30ed6cbbf5e67e2dd5cc481898242ab6378238a6`; `validationHook()=0xb8c877cf6ce506dbc3098cd086e3d4898659bd2d`.
- Direct `eth_getCode(pointer)` returns SSTORE2 bytecode `0x000000000000195a620000040000173d8400000300000eca100f42400000000001`. After removing the leading 0x00 STOP byte, 8-byte `(uint24 mps,uint40 blockDelta)` steps decode to:
  1. `0 mps/block × 1,661,538 blocks`, `[106868933, 108530471)`, early stage **ZERO issuance**.
  2. `4 mps/block × 1,523,076 blocks`, `[108530471, 110053547)`, **6,092,304/10,000,000 issuance fraction = 60.92304% of auction**, ~27.415M SLOP.
  3. `3 mps/block × 969,232 blocks`, `[110053547, 111022779)`, **2,907,696/10,000,000 = 29.07696%**, ~13.085M SLOP.
  4. `1,000,000 mps/block × 1 block`, `[111022779, 111022780)`, **10% = 4,500,000 SLOP**.
  - The source `StepStorage` verifies `sum(mps × blockDelta)=10,000,000` and `endBlock` matches sum of lengths; the reconstructed values reconcile to a complete 45M auction sale schedule.
- Direct before-open `currencyRaised()=0`, `totalCleared()=0`, `isGraduated()=false`, latest observed chain head about block `106808150`. These are observed-before-open facts, not future predictions.
- According to **actual** Uniswap CCA core `submitBid` rejects only when current block >= END_BLOCK and `sweepCurrency` only after END_BLOCK. CCA `lbpInitializationParams` requires final end-block checkpoint AND graduation. A $400k minimum being reached or bid cap reached does **not** automatically shorten the time interval or permit earlier normal settlement.
- However the right to add NEW bids can vanish BEFORE end: source `_submitBid` rejects when auction has sold out, or when proposed maxPrice is **<= actual current clearing price**. If clearing price reaches hook's maximum permitted price, no new compliant bids can submit while that cap holds. Existing previously submitted bids remain active across future steps.
- Normal early bid cannot be canceled/edited. Uniswap's `exitPartiallyFilledBid` can return unspent funds early **only after the auction is graduated** and the given bid's outbid/partially filled checkpoint proof is accepted; it is not an anytime cancel function. Otherwise settlement/refund occurs after end.
- Time is determined by **block boundary**; published Bangkok clock times remain estimates/communication guidance, whereas each CCA transaction is enforced by block position.

### B. DIRECT_CHAIN hook config, public permit dependence, admin mutability

The deployed CCA points to `0xb8c877cf6ce506dbc3098cd086e3d4898659bd2d`, and hook `cca()` points back to the same CCA.

Observed live calls (all read only):
- `zkGlobalMaxBidAmount()=200,000,000,000` USDG 6-decimal atoms = **$200,000**; `zkGlobalBidTotal()=0` (prelaunch).
- `stepMaxBidAmount(0)=3,000,000,000` atoms = **$3,000** per verified wallet in initial step; steps 1/2/3 configured `stepMaxBidAmount=0` (no zk step cap), but **public steps use per-bid signed permits and are not identical to zk bid admission**. Page's generic $5,000 narrative is not authoritative for currently enforced zk cap.
- `maxBidPrice()=1,739,934,337,455,888` in Q96 units = **$0.0219610588235** SLOP/USDG with 18/6 decimals. `owner()=0x81a1566dddf4ce0705ae6d09571561e3f3825fde`, queried bytecode = `0x`, i.e. **EOA admin** onchain. Actual beneficial controller beyond that EOA is unknown.
- Step 0: `isStepEnabled=true`, `isStepPermitEnabled=true`, `verifiesEveryBid=false`, **5 allowed zk provider hashes**. An eligible wallet may establish registration subject to hook verification; `maxBidPrice` still applies.
- Steps 1/2/3: `isStepEnabled=true`, `isStepPermitEnabled=true`, `verifiesEveryBid=true`, **0 allowed zk provider hashes**. In currently deployed configuration, **ALL publicly admitted bids require an amount-bound valid EIP-712 SERVER PERMIT for that specific step and each bid**. Public qualification may be open via the app's signing service, but sending a direct no-permit CCA bid will revert with `ServerPermitRequired`. This is a real availability/central-permit execution dependency, not proven unfair discrimination or a KYC claim.
- `authorizesWithoutCredential(step,user)` returned false for user canonical `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c` for all four steps at this snapshot. This proves no empty-hook-data admission for this wallet; it does not prove the account cannot be verified or receive an app permit.
- Hook owner-only **mutable** admin functions in official source `UmiaValidationHook.sol`: `setMaxBidPrice`, `setZkGlobalMaxBidAmount`, `setStepMaxBidAmount`, `enableStep/disableStep`, `setStepProviders`, `enableStepPermit/disableStepPermit`, `setSigner`; published max $0.021961/zk $200k/step $3000 should be **rechecked just before any sign**. CCA issuance mps and end block remain immutable core constructor parameters.
- `zkGlobalBidTotal` increments for zk verification/registration path, **not for server-permit bids**, per `_validatePermit` return before `_accrueZkBid`. Thus "zk early $200k full" does not establish full $200k fund allowlist or prevent server-permit bids; count separate access types accurately.

Source: https://github.com/umiafinance/protocol/blob/4b76b7b13399e440b318d9c479d7fc720b846d7b/src/periphery/UmiaValidationHook.sol and https://github.com/umiafinance/protocol/blob/4b76b7b13399e440b318d9c479d7fc720b846d7b/docs/contracts/UmiaValidationHook.md. Uniswap core: https://github.com/Uniswap/continuous-clearing-auction/blob/main/src/ContinuousClearingAuction.sol ; state: https://github.com/Uniswap/continuous-clearing-auction/blob/main/src/StepStorage.sol .

### C. Actual accepted max-bid price grid (corrects prior proposed price literals)

Direct CCA `floorPrice()=704,259,136,589,288` Q96; `tickSpacing()=41,427,008,034,664` Q96. USDG 6 decimals, SLOP 18 decimals. Converts to:
- floor `17 ticks = $0.00888899999999990` per token;
- **single price tick $0.00052288235294117**, which corresponds to ~$52,288.2353 FDV per step at 100M tokens;
- hard current hook max **42 ticks = $0.02196105882352917**.
- **Allowed below prior $0.013 max:** tick 24 at **$0.01254917647 (~$1,254,918 FDV)**; the next tick 25 is **$0.01307205882**, EXCEEDS $0.013.
- **Allowed below prior $0.015 max:** tick 28 at **$0.01464070588 (~$1,464,071 FDV)**; next tick 29 **$0.01516358824**, EXCEEDS $0.015.
- The prior $700 @ exactly `$0.013` + $300 @ exactly `$0.015` were **not tick-aligned**. Any exact EVM bid with those Q96 prices fails `TickPriceNotAtBoundary`; a frontend could convert/round, which must be independently inspected before signature. Strictly keep original dollar caps by selecting lower valid ticks **$700 at tick24** and **$300 at tick28**, if the GUI accepts two entries. This is a **technical consistency correction** not fresh permission to trade or an expansion of risk limits.
- At least one tick ABOVE existing clearing price is required for a new bid; a limit equal to floor when current clearing is floor fails `BidMustBeAboveClearingPrice`.

### D. Newly identified economic and operational game points

1. **Early time inside a zero-issuance step:** placing on Nov6 first block versus Nov7 near the end (both before first public issuance) does **not** buy earlier low-price tokens because `step0 mps=0`. With identical budget/max price, both present for the full release schedule if both were accepted before public issuance. Racing the first day primarily protects **scarce early zk $200k admission capacity**, verification reliability and avoiding later increased clearing price/permit hurdles, NOT a locked cheaper token price.
2. **CAP full vs actual fills:** $200k is a cap on qualifying zk commitments, not a distinct $200k public funding tranche or guaranteed 9M token reserve. Entire CCA issuance schedule contains **zero tokens sold in initial zk step**. The issuer's "9M for community early" is marketing allocation framing, not an onchain fixed-price 9M pool evidenced by these CCA steps. No direct token-specific reserve identified.
3. **Public permits:** the purported open round has a permissionless *audience* but a permissioned onchain execution path that needs individual valid signed permits. Server API outage, permit rejection/expiry and signing delay are separate risks from gas/chain congestion. Prior zk registration does not bypass verifyEveryBid in later permit-only stages.
4. **Sustained offer vs effective bid:** setting maximum allowed price makes the order eligible to compete for later emissions if price rises, but does not guarantee full fill or same-block priority; zero-emission early precommits cannot be canceled, and all price constraints may be updated by the EOA hook owner.
5. **If price reaches current hook max, NO compliant new bid** can be placed under the CCA's strict `maxPrice > clearingPrice` condition (as long as hook cap is unchanged). This can happen before `endBlock`. Yet the auction itself still reaches the final block and previous bids can continue being allocated.
6. **Last bucket 10%:** **4.5M SLOP at single block** forms an unusually large final auction settlement quantum. Final price is used in LP initialization, and does not assure genuine liquidity at that mark; if late bidders cannot submit due to cap, prior bids compete for the bucket. Need independent real swap quote after LP deployment for ROI.
7. **Threshold nuance:** `minRaise=$400k` refers to actual cleared currency `currencyRaised()`, NOT `Total committed` or unexecuted budgets. A gross-committed UI number over $400k is not proof of graduation; `isGraduated` and final checkpoint matter.
8. **Split bids:** multiple eligible bids under one wallet do not evade `stepMaxBidAmount` because it accrues per wallet and step. Different limit ticks create a planned effective-price ladder, but one cannot simply assume two orders guarantee more accepted quantity.
9. **Ticket feasibility:** live earlier connected canonical wallet had about **389.420578 USDG** and **0.002152 ETH**; prior $1,000 plan remains *intent only*, not funded. No wallet transactions authorized.
10. **Operational risk:** `setMaxBidPrice`, server permit policy, proof providers, caps and signer are upgradeable by live hook admin, unlike core immutable issuance schedule. A pre-start read is a dated snapshot, not an assurance of future consistency.

### Decision impact

- Stage dates/bounds **are immutable in the sampled onchain CCA**; `startBlock=106868933` / public release `108530471` / `endBlock=111022780` / `claimBlock=111023357`.
- Early-qualification work has positive **option value** when low cost, because $200k zk cap could be exhausted. It does not grant guaranteed cheaper token price, nor does waiting to submit during early 0-mps stage necessarily lower token fill.
- Public-phase "same result as early" is a conditional outcome **only if signed permit is obtained and transaction accepted before first issuance, and same valid maximum price/budget and demand schedule**. Public permit signature/latency can erase the parity.
- Preserve **WATCH** and **NO_GO**. Original price ceilings should be corrected to actual below-cap valid tick levels if a later user-authorized bid is contemplated. No change to production monitoring, Gmail, automation, other Mission modules, or order placement.

### Verification and limitations

Direct `eth_call`: 11 CCA getters, 15+ Umia hook getters; `eth_getCode` SSTORE2 schedule pointer and owner account; GitHub fixed official Umia source `4b76b7b13399e440b318d9c479d7fc720b846d7b` and Uniswap CCA files. **Did not independently reproduce a build-bytecode match of deployed hook/core to GitHub source**, so runtime states plus published source are distinct proof levels. No true live bid yet; no direct auction receipt at this snapshot; no empirical probability of sell-side depth. No functional browser click / onchain writable method invoked.

---

## 2026-11-05 historical comparables and full-fill versus cost tradeoff

**Scope:** user asks to review Umia's previous $UMIA auction and Slop Cash CTO Shaw Walters' prior ai16z/ELIZAOS token, estimate SLOP post-TGE FDV, and decide early-whitelist limit bids. **Research only; no committed bid; no change to previously approved $1.5m FDV risk boundary.** Historical comparisons are not calibrated outcome probabilities.

### Independent historical sample 1: Umia's own UMIA

- First-party https://app.umia.finance/p/umia/auction and https://umia.finance/blog/umia-auction-recap: Aug26 to Sep02 2026 auction, 17.3M UMIA sale, final cap/clearing price $0.36 on 50M total supply = **$18M FDV**, ~$6.112M raised, **751 bid IDs** on first-party auction page (not verified distinct persons). Umia's official recap says available allocation *was fully committed* in roughly seven minutes during the open phase; this is **not** proof all sale tokens physically settled in those seven minutes. All bidders bought through CCA at per-block clearing, not necessarily $0.36 weighted average.
- Older archived Base CCA first-party/offchain/reproducible evidence in this same research document: $6,112,005.046962 actually raised / 17,299,999.308 UMIA clearing = aggregate historical **$0.3532951** per token. Example early bid #0 had effective $0.3496557992 per UMIA and selected late bids approached $0.36. These are sampled bid costs and do not establish the complete distribution.
- Actual historical direct Base v4 sparse spot samples in Oct27 section: official pool initialized at $0.36 at Sep02 ~12:10 UTC; observed ~$0.7262 at 12:15 and ~$0.7883 at 13:00. These are discrete state observations, **not executable highs** or guaranteed realizable profits.
- Current Nov05 CoinMarketCap English https://coinmarketcap.com/currencies/umia/ reports approximately **$0.759** (about +111% vs $0.36 final sale), reported **Oct29 ATH $0.956**, i.e. theoretical **$47.8M FDV / 2.66x** versus $18M auction. DefiLlama reports a somewhat lower $0.92 ATH due to methodology/venue; treat peak band $0.92–$0.956 as third-party, not exact chain-verified global tick. The old October 8 ATH $0.9044 in the prior research is an *older historical snapshot* superseded for date-based peak.
- UMIA had about **$6.1m auction funding**, 20% proceeds to LP plus $120k/mo operating allowance, materially deeper capitalization than SLOP's **$400k to $988,245 accepted auction** and $35k/mo draw. **Copying UMIA 2.66x into SLOP yields ~$5.84M FDV when entered at SLOP max auction FDV $2.1961m, but is a mechanical counterfactual, NOT a forecast.**

### Independent historical sample 2: Shaw Walters' previous ai16z/ELIZAOS token

- Slop Cash first-party https://app.umia.finance/p/slop-cash/auction identifies CTO **Shaw Walters** as developer of elizaOS and previously of ai16z ecosystem, cofounder Drew Pierson CEO; business and IP are distinct.
- Independent dated reporting Aug05 2026: https://www.theblock.co/news/defi/2026-08-05-eliza-labs-native-token-dead-410774 ; https://www.coindesk.com/markets/2026/08/05/ai-agent-token-once-worth-usd2-4-billion-ends-with-founder-calling-it-dead . Walters explicitly declared the successor ELIZAOS **token dead**, foundation winding down and no further buyback/supply support after lawsuit settlement; the open-source AI agent software was to continue. This is not a court finding that he defrauded anyone; allegations of lawsuit remain allegations.
- Historical AI16Z original token reached about **$2.4b–$2.5b peak capitalization in Jan 2025**; 2026 successor ELIZAOS was reported at approximately **$2.3m market cap** around Aug05 shutdown. Old AI16Z and post-migration ELIZAOS have DIFFERENT token supply/denomination and cannot be used for a simplistic price-percent return calculation. Multiple current trackers around Nov05 still show successor market cap low single-digit millions, but data sources differ.
- **Investment implication:** demonstrated capacity for retail speculative hype and major **long-term token-holder loss / governance and reputational risk**. Neither the multi-billion ai16z peak nor historical UMIA success is a transferable SLOP valuation anchor. This must be disclosed in any participation decision.

### SLOP price scenarios, without invented odds

- Known original first-party fundamentals Nov05: 100M total, 45M sale, $0.008889 floor (FDV $0.8889m), $0.021961 bid ceiling (FDV $2.1961m), 9M SLOP treasury-owned LP backed by 20% actual auction receipts (~$80k–$197.649k USDG if auction succeeds at the min or fills all 45M at hard ceiling). Full auction 45% of supply liquid at TGE plus 2% contributor allocation; 9% LP token float is **pool inventory, not discretionary investor sell-side**. Pre-revenue issuer and $SLOP does not provide a mandatory dividend/buyback or per-transaction use requirement.
- **Subjective stress bands, NOT probability forecast or live prices:** bearish secondary $0.5m–$1m FDV (price $0.005–0.01), middling $1m–$2m ($0.01–0.02), strong trading $2m–$3m ($0.02–0.03), speculative $3m–$5m ($0.03–0.05), exceptional $5m–$10m ($0.05–0.10) contingent on meaningful additional buy-side demand. Core trading stress comparator **$2m–$3m**, rather than a claim of most-likely FDV.
- At max-price **$0.021961**, if $1,000 fully fills at that worst price: **45,535.2671 SLOP**; exit mark at $0.01 = $455.35 (-54.5%), $0.02 = $910.71 (-8.9%), $0.03 = $1,366.06 (+36.6%), $0.05 = $2,276.76 (+127.7%). Requires actual liquidity/claim; excludes gas/slippage/fees. At actual avg $0.012, fully spent $1,000 obtains 83,333 tokens and would mark $2,500 (+150%) at $0.03.
- **Crucial CCA correction:** `max_price` is a ceiling, **NOT** automatic purchase cost. Official https://umia.finance/blog/understanding-your-bid explicitly says early bids get spread over remaining emissions and each block executes at actual clearing <= max; if demand arrives late, early bidders benefit; if early demand already saturates each block, high limit may fill near the max and offer **NO early discount**. Slop-specific **no emission Nov6–Nov8**, so early eligibility is early order placement only; all emission Nov8–Nov11. If at cap, same-price bid allocation is **pro rata** and full $1,000 can never be guaranteed. Full-fill certainty and best ROI simultaneously **cannot be guaranteed** at any limit.
- Priority A **maximise acceptance** (new unapproved conditional scenario): place **$1,000 `Limit` max $0.021961** at first eligible opening; admits worst-case $2.1961M entry and does not guarantee full fill if total demand > supply or window cap hit. **This violates the prior $1.5M FDV participation ceiling and requires an explicit change decision rather than silently becoming the recommended setting.**
- Priority B **risk-adjusted ROI / existing recorded plan**: two early `Limit` budgets **$700 capped $0.013 + $300 capped $0.015**, *provided Ui and hook permit 2 bid IDs*; $1k fully filled at maxima buys at least **73,846 SLOP**, worst weighted average ~$0.0135417; if competitors rapidly force clearing >$0.015 before first emission, fills may be **zero**, not a broken promise. No need to ask user to repeat budget; $1000 remains intended max, not already funded.
- No liquid SLOP market yet and no verified SLOP-specific PM contracts; do not fabricate FDV probabilities, sale quotes, first-hour achievable sell prices or demand volume from comments about everyone maxing.
- Required pre-sign: verify early extension claim status, onchain CCA parameters, `Limit` versus UI default Market, recorded maxPriceQ96/FDV, verified Robinhood USDG and native gas, available contribution headroom under global $200k early cap, actual successful order receipt, claim state. User wallet only held **389.420578 USDG** as of earlier Nov05 direct chain read, not the intended $1,000.

### Evidence categorization

1. **DIRECT_CHAIN** Nov05 prior section proves SLOP supply, auction inventory, USDG/gas balance before launch.
2. **FIRST_PARTY** Umia auction docs and Slop project page prove bid mechanics, immutable limits, team identity, price ceiling, LP allocation. They are launchpad/issuer statements for future business outcomes.
3. **ARCHIVED_CHAIN** pre-existing original UMIA sample calculations are supplied above with source pointers, cannot certify future SLOP fill.
4. **THIRD_PARTY** CoinMarketCap/DefiLlama ATH, CoinDesk/TheBlock documented founder token shut-down.
5. **ANALYSIS** FDV ranges, payoff math and conditional bidding alternatives are uncalibrated scenarios only; no trade, no whitelist verification, no protocol action.

---

## 2026-11-05 PRE-AUCTION update: verified live $SLOP mint, funded CCA and conditional early-bid discipline

**As-of:** 2026-11-05 approximately 20:15 Asia/Bangkok, before opening. **State: WATCH / eligible early bidder hypothetical / no bid authorized / no funds committed**. This subsection supersedes the 2026-10-27 `SLOP_CA_UNCONFIRMED` historical status, but does not rewrite that historical audit.

### Original first-party current launch parameters

- Connected user's already-open first-party page, https://app.umia.finance/p/slop-cash/auction, now displays canonical Robinhood Chain (chain ID 4663) **$SLOP mint `0xfeb4e36fa4a2a494ff25ae4a63491e4c584a67ae`**, **CCA `0x901f26b42c61af93f548efa0fdf8df4d342b124c`**, **USDG `0x5fc5360d0400a0fd4f2af552add042d716f1d168`**.
- CCA start Nov 6 00:00 Bangkok (Nov5 17:00 UTC); public Nov 8 00:00; close Nov11 00:00 (UTC 17:00 Nov10). **No tokens emit in first 2 gated days; early bids start filling only when public-round supply starts to emit.** There is no automatic cheap early presale fill. All bids cannot be canceled mid-auction; unused budget refunded at close.
- Current official floor **$0.008889**, hard max **$0.021961**, corresponding $888,900 to $2,196,100 FDV given 100M supply. Auction **45M SLOP**; minimum raise **$400,000**, hard maximum theoretical accepted proceeds if all 45M priced at $0.021961 **$988,245**. Gross committed (possibly millions) is NOT the same as actually accepted/cleared funds or all holders' average cost.
- Early contributor/zkTLS route: **$200,000 window-wide budget cap; $5,000 max per eligible wallet**. Independent ecosystem fund quota described as around $200,000. Separate UMIA Pass rules for prior holder wallet. A user possessing qualifying GitHub repo/eligibility has not yet been verified here and this report makes **no verified whitelist pass claim**.
- The button currently displays order type `Market` on page. **Budget must be coupled with intentional explicit `Limit` max price / max FDV if available, and signed transaction checked before submission; never submit default market/high cap by accident**.
- Token schedule from on-page: 45M auction fully liquid, 9M LP treasury-owned, 2M contributors unlock, 8M treasury locked, 14M ecosystem locked, 10M 12-month-cliff team time-vested, 10M price TWAP performance, 2M Umia. Thus nominal initial **56% circulation** includes **9M locked-in LP holdings**, not 56M independent sell-side wallet float. LP stablecoin = **20% actual auction proceeds**, range $80K at min $400K raised up to theoretical $197,649 at max $988,245 raised; exact v4 executable depth, LP range and slippage **NOT VERIFIED**.
- Company claims current operating budget approximately **$35K/month**, product **pre-revenue**, on-chain contributor payouts are outgoing program costs, **not company revenue**. Product users do not need SLOP to interact; token grants protocol treasury/governance power, no verified dividends, buyback or enforced profit sharing. One factor reducing speculative 5x/10x confidence.

### Direct chain read-only evidence, RPC via connected Alchemy

Network `robinhood-mainnet`, no signatures/sends, as of Nov5:
- SLOP `name()`: `Slop Cash`; `symbol()`: `SLOP`; `decimals()`: 18; `totalSupply()`: **100,000,000.000000000000000000 SLOP**. Official page matches this contract address. Mint creation & admin rights still require separate audited inspection.
- `balanceOf(auction)`: **45,000,000.699999900000000000 SLOP** at the canonical sale contract, **enough for announced 45M auction supply**, with ~0.7 excess unexplained and immaterial here. Contract `totalSupply()` read returned **45M sale allocation**. No inference of user allocation or auction already succeeded.
- `USDG.balanceOf(auction)` = **0** before launch. First-party page total committed = $0. No evidence of an active bidder fill yet.
- User canonical EVM `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`: **389.420578 USDG** and **0.002152148618870669 native ETH** at this instant (real chain reads, not account net worth). User's planned $1,000 budget cannot currently be entirely placed from this wallet without additional funds; no transfer authorized.
- These chain calls prove contract existence, token supply, inventory and current escrow balance, **not** a tested quote/CCA auction fill, actual live launch completion, top holders, security audit or Claim.

### Early-white-list **hypothetical** investment strategy under frozen $1,000 user budget

Use $1,000 only as a **max commitment** contingent on user actually acquiring whitelist and funding the wallet; this is a recommendation, no trading authorization. Preserve the already documented user price ceiling of **$1.5M FDV**, rather than increasing it after hearing others may max the auction.

- Preferred **two max-price limit bids at first eligible start**, only if confirmed onchain launch and the UI supports multiple bids: **$700 USDG capped at $0.013 per SLOP ($1.3M FDV)**; **$300 USDG capped at $0.015 ($1.5M FDV)**. Verify USDG chain, seller/CCA/hook address, max-price encoded before signing. NO default market order.
- If all two portions **fully fill at their respective maximum allowed price**, acquired at least $700/0.013 + $300/0.015 = **73,846.153846 SLOP**, aggregate worst-price average approximately **$0.01354167**; because CCA fills different blocks at *at-or-below* each limit, actual accepted tokens could be **more** for same deployed $1,000, or accepted USDG could be **less**, even **zero**, if competition pushes price beyond limits before any emission fills.
- This portfolio's fully filled upper-price-mark sensitivities (fee/slippage excluded): at FDV $0.5M (price $0.005), approx $369 and loss $631; at FDV $1M (price $0.01), ~$738, loss ~$262; FDV $2M (price $0.02), ~$1,477, profit ~$477; FDV $3M (price $0.03), ~$2,215, profit ~$1,215; FDV $5M (price $0.05), ~$3,692, profit ~$2,692. **Scenarios not probabilities or executable sell quotes.**
- An unconditional **$1,000 max at hard ceiling $0.021961** would buy only **45,535 SLOP** if fully spent at that price, requiring FDV >$2.196M to break even. At $3M post-launch FDV, paper profit only **~$366**; at $1M FDV paper loss **~$545**. Such a cap makes the auction increasingly an unprofitable chase relative to cash-real business; no credible ROI advantage from merely being whitelisted when no supply releases in early 2 days.
- In a **pure same-max-price same-time proportional thought experiment** (NOT actual CCA fill simulation), with max accepted theoretical proceeds $988,245, gross commitments $2M/$5M/$10M leave a $1,000 bid ~$494/$198/$99 accepted, rest refunded. Actual fills depend on bucket timing, previous price, same-block pro-rata, allowable caps and varying limit prices. Do **not** present these theoretical fills as forecast.
- The issuer's max price is a protocol ceiling, not any evidence of post-listing fair value. If the market bid demand reprices the auction above the user's $0.015 cap, accept **zero allocation** rather than raise the limit without fresh independently verified economics.
- The previous 2026-10-27 public-round $700/$300 split and $1.5M FDV ceiling are **preserved**. Early-access improvements relate to order acceptance timeline, not a higher acceptable valuation.

### PM status and evidence limits

- Actual Nov5 web query included exact `Slop Cash`/`SLOP` project identity with venue-targeted Polymarket, Kalshi, Limitless, Predict.fun and relevant MetaDAO decision-market checks; **未检索到可验证的项目专属 PM 市场**. No liquidity, probabilities or FDV strike thresholds are available to cite. Ignore token ticker collisions.
- No live bid, no wallet signature, no swap, no approval, no notifications/automation, no production change. Project `WATCH` remains in effect. $SLOP's underlying product metrics, PM absence, actual initial DEX price and order execution outcomes remain unresolved.
- Evidence: https://app.umia.finance/p/slop-cash/auction ; https://umia.finance/docs/tailored-auctions ; https://umia.finance/blog/understanding-your-bid ; https://app.umia.finance/p/slop-cash ; read-only Alchemy Robinhood mainnet on canonical token/auction/USDG.

---

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


---

## 2026-10-27 direct contract bidding interface verification (2026-10-27)

**Status: public source/API documentation inspection, NOT browser packet capture; NO_SLOP_CA / NO_ORDER / NO_WALLET_ACTION.** This supplements the identity check at the top. The authenticated auction browser network panel and production JS bundle were not accessible in this environment, so no claim that packets were captured or that hidden SLOP addresses were ruled out. Official Slop project page continues to say \`Contract address: (added at deploy)\`; current auction page labels SLOP \`Upcoming\`.

### Contract interface and read-only addresses

- Uniswap upstream \`IContinuousClearingAuction.submitBid(uint256 maxPriceQ96, uint128 amount, address owner, uint256 prevTickPriceQ96, bytes hookData)\` and overload \`submitBid(uint256,uint128,address,bytes)\` are present in published official source: https://github.com/Uniswap/continuous-clearing-auction/blob/main/docs/TechnicalDocumentation.md and https://github.com/Uniswap/continuous-clearing-auction/blob/main/src/ContinuousClearingAuction.sol . **These are protocol ABI surfaces, NOT proof of a SLOP deployment.**
- \`maxPriceQ96\` uses Q96 price encoding and tick-grid alignment; it must be strictly **above current clearing price**. A UI display of \`$0.013\` is NOT directly transferable as a uint256. A bid \`amount\` is in 6-decimal USDG units for Robinhood Chain, and bidder token/refund recipient is \`owner\`. ERC20 transfers from sender through **Permit2**; approval/signing is a distinct operation.
- Official Robinhood infrastructure page: https://umia.finance/docs/contract-addresses/robinhood-chain . Shared CCA **factory** \`0x000000001F26a0044BaA66024e7b6599c61963F8\`, CCALens \`0xc3C65F5453A3674aDb693cbdA3C842545cD30f53\`, Permit2 \`0x000000000022D473030F116dDEE9F6B43aC78BA3\`, USDG \`0x5fc5360D0400a0Fd4f2af552ADD042D716F1d168\`, chain ID \`4663\`. **Factory/Lens/Permit2/USDG are NOT SLOP token CA or SLOP auction instance**. Never submit bid calldata to the factory.
- Factory can predict CREATE2 instance from token address, amount, full \`configData\`, salt and deployer, but these SLOP-specific inputs are not all confirmed. Do not invent a precomputed auction CA.
- Per Umia official https://umia.finance/docs/technical-reference/validation-hook and https://umia.finance/docs/technical-reference/bid-validation , each CCA may use \`validationHook()\` with \`expirationBlock()\`, \`isStepEnabled(step)\`, \`isStepPermitEnabled(step)\`, \`getStepProviders(step)\`, \`verifiesEveryBid(step)\`, \`stepMaxBidAmount(step)\`, and \`maxBidPrice()\`. \`hookData\` may require inline zkTLS proof or **EIP-712 server permit**, exact step and cap enforcement. Invalid credentials or exceedance revert. **Public bidding does not by itself prove a raw no-credential \`submitBid\` succeeds.** The project's actually deployed hook and current step must be inspected at the time.
- Umia's official https://umia.finance/docs/technical-reference/base-mcp-plugin explicitly documents \`npx umia-cli@latest\` and unsigned \`/api/v1/calldata/*\` transaction builders, plus **auction bids on permissionless steps**, Permit2 batching and tick-grid alignment. Gated steps are routed back to Umia app. This is a potentially better direct/onchain-preparation route than hand-encoding calldata, once a SLOP auction instance is public and CLI/RPC responses can actually be verified. No request against production \`POST /api/v1/calldata/*\` succeeded in this research environment.
- Time priority: compare current clearing price, floor, configured max, per-step gate and bid cap, actual \`startBlock/endBlock\`, USDG balance/allowances, gas, direct transaction simulation, and \`BidSubmitted\` receipt before claiming success. The historical UMIA sale reached public cap quickly, but a raw transaction cannot defeat early-step eligibility, an exhausted auction, or a personal max valuation. Avoid open-ended/market bids.

**Review status**: \`WATCH/PREPARE\`. Needed to upgrade: official SLOP ERC20 token CA + SLOP-specific CCA instance + hook + actual deployed gate/price schedule + valid unsigned calldata readback/simulation + legal wallet eligibility. No Git/production task changes except this research note.
