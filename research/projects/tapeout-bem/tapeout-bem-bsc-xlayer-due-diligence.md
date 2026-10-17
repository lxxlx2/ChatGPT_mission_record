# TapeOut Protocol / BEM / Circuit Mining — BSC, X Layer and Base due diligence

Updated: **2026-10-17**, research snapshot ~2026-10-17 05:25–07:00 UTC (Asia/Bangkok UTC+7).
Class: `ONCHAIN_CIRCUIT_NFT / BEM_PROOF_OF_DESIGN_MINING / CROSS_CHAIN_ASSET / DEWEB_INFRA / SECONDARY_HARDWARE_RIGHTS`
Stage: `PRODUCT_L4_ONCHAIN / INDEPENDENT_RECURRING_EXTERNAL_REVENUE_UNVERIFIED`
Trade authority: `RESEARCH_ONLY / NO_BUY / NO_AUTOMATION / PRODUCTION_TRADING=NO_GO`.
User position: **none established; do not create an active position**.
Applicable Mission rules: `crypto-300-profit-mission/PROJECT_ANALYSIS_FRAMEWORK.md`, `token_trading_principles.md`, `PROJECT_ANALYSIS_EVIDENCE_WORKFLOW.md`, `MISSION_SPEC.md`. Separate CONFIRMED direct data, official/issuer statements, independent market terminal observations, model assumptions and speculation.

## 0. Why this research was requested

2026-10-17 user showed X/KOL post by `@Deibajie` (https://x.com/Deibajie/status/2111160033782489587) claiming on that day three circuit/miner NFT purchases `190+190+200=580 BNB` (**NOTE: arithmetic correction: 190+190+200=580 BNB, NOT 600!** Author rounded "加起来600bnb" to 600); position that BEM ~$38, ~240d simple gross NFT ROI; if token traded from $39 to $50, mining-equipment valuation could reprice to 16.6 BNB per 1 BEM/day. **Original post is a trading opinion, not raw transaction proof**, published around 01:19 2026-10-17 Thailand per screenshot, ~8,384 views/24 likes at screenshot time. The three individual transaction hashes are NOT independently verified. One displayed 190 BNB secondary-market trade has corroboration from a marketplace indexer, without verified underlying tx hash and independent counterparty attribution. Do not claim 3 independent buyers.

## 1. Canonical identities and links

- Official product https://tapeout.net/ ; official project account `@TapeOutWorld`; principal public developer `@Blonskr`.
- BSC BEM ERC20 **`0x5ce033B2bFCa3Af30b3e8C8457DeaF776A8b695a`**, BNB Chain ID **56**, decimals **8** confirmed BSC direct eth_call on 2026-10-17.
- BSC BEM Proof of Design mining contract `0x7e2e0dc66a3bd9103e69b766afa62d9f7b697b46`.
- BSC Bridge locked BEM `0xa84b8d3893de6e9922f2b29be1e1b115845f5e72`; X Layer representation `0x60e62Efa9405d6873C5deaBD4E6CC91c25363952`, chain ID **196**. A backed BEM on X Layer is the mapped representation; never double-count bridge collateral plus X Layer minted supply.
- BSC original Factory `0x68224F668083c29e9800Be2a646d42d18cedF7e2`; genesis NFT `0x50A994E71615474b55559fF4F500928fbc339DD9`; transistor ERC1155 `0x1d23Bf70ec6bAAD95f396Ea38f8A8415119dFDE6`.
- Official mining processors in marketplace: Behemoth `0x1F5Cb4aeaE1807Bf60c3b9C0D8aDBCC14e91f12C`; TapeOut `0xb1024b89886B9a34Aa4ff5F31C411D708b20a14C`.
- PancakeSwap v3 BEM/USDT 1% fee main verified pool `0x3098d7a051045000d68ec0360753a40c8cabea31`; quote price is pool-specific, not guaranteed execution price.
- OKX **Web3 marketplace** is a market/aggregator frontend; **X Layer** is a separate blockchain, both are NOT evidence of OKX equity investment or official centralized-exchange listing.
- Additional Base deployment reported at independent protocol registry. Do not assume BEM is mined separately on Base/X Layer without token supply and mining-contract proof.

## 2. Actual maturity / production

- On-chain design: NAND/LATCH building blocks burn/consume toward on-chain circuit NFT; design verification and optimized computation controls PoD mining weight; NFT can be sold transferring access to future emissions if valid and owned. This is chain software circuit/tapeout, not physical semiconductor fabrication.
- 2026-10-17 independent registry source https://tapeout.work/api/v1/chains counts **BNB Chain 1,279 processors / 59,593 circuits**, **X Layer 355 / 9,536**, **Base 103 / 249**. BSC metric may include nonmining circuits and inactive CPUs; not independent customer accounts.
- Official website crawl ~BNB Chain **1,279 processors / 59,639 minted circuits**. Registry differs by timing; no contradiction in product existence.
- Independent monitor https://tapeout-public-monitor.tapeout-labs.workers.dev/ ~2026-10-17 05:25 UTC: **20,187 mining-machine entries, 97.5% verified pool weight, verified weight 1,576,724 vs unverified 40,755, total mined 371,838.33 BEM, ~10,320 BEM holding addresses**. 20k entries are NOT 20k unique persons or fully active mining rigs; source date/coverage matters.
- Firsto trading terminal https://firsto.ai/data had an **earlier 2026-10-15 13:00 UTC** reading **1,721 active miners** and total mining weight 1,612,076; different units and timestamps. Top 5 marked miner wallet weight at that snapshot: 5.29%, 4.31%, 2.58%, 2.40%, 2.04% (combined 16.62%); exclude LP/admin addresses from any BEM token holder concentration analysis. Treat terminals as secondary until direct indexer source reproduced.
- Paid external real-world customers, third-party operational compute demand, audited recurring product revenue, non-incentivized active user cohort, operational profit, identifiable legal organization **UNVERIFIED**. Internal NAND token volume and NFT turnover reflect ecosystem participation, not necessarily independent cash revenue.

## 3. Git and protocol standards

- Canonical publicly attributable org: https://github.com/TapeOutProtocol .
- `TapeKit` https://github.com/TapeOutProtocol/TapeKit README describes an on-chain website kernel, Service Worker gateway, page integrity, browser extension/desktop and multi-RPC read validation. Confirmed main last commit **2026-10-11T07:08:10Z `40994bd65baedbda4df72cb0985031a5f082f606`**, app embedded-browser fallback fix. Sep 19 `489956eadad6f41b0d2c17f6c4694a9a6a6bdd45`: X Layer/Base support; Sep 20 `f1831a44160e7a5a31385c05f1cdf64f25619516`: security/cache repair. Engineering deliverables beyond static promotional pages, but no independently verified paid customer counts.
- `TAPs` https://github.com/TapeOutProtocol/TAPs, normative English spec proposals TAP-01/02/10/11/12/13, mostly marked Draft, latest merged main **2026-10-05T05:44:22Z `075dd834a72c4c5b251d97f183cac9d42d8ccd66`**. TAPs documents do not prove deployed paid functionality. Repo `TapeKit` and `TAPs` are not sufficient to attribute every closed-source mining/bridge smart contract development change to official Git authors.
- TapeKit design sample: https://4246-0.tapekit.org/ is a live URL for byte-verified demo claims; independent uptime/payments not audited.
- One third-party GitHub list of projects https://github.com/trytotapeout/awesome-tapeout has examples including X Layer games, not equal to officially adopted paying customers.

## 4. Team / finance / parties

- Public project handles `@TapeOutWorld` and `@Blonskr`, independent fully legal name, jurisdiction, entity and team size **UNCONFIRMED**.
- No independently confirmed venture round, institutional investor, equity valuation, SAFT/VC BEM cost or IPO plans at this research cutoff. **Do not call BNB Chain, PancakeSwap, OKX X Layer or an X Layer hackathon sponsor an investor.**
- Partnerships and integrations are classified: deployed chain network, venue, app and sponsor, not financing. No independently audited financial accounts/annual filings.
- No first-party verifiable founding team's prior exit/performance history established. Do not invent résumé links.

## 5. Token economics, fixed miner owner, and bridge administration

- BSC **direct latest `totalSupply() = 372,510.69714122 BEM`**, `decimals()=8`, via ERC20 `0x18160ddd`, `0x313ce567`. Token's `owner()` read reverted; do not interpret as owner zero/renounced. 
- PoD miner direct BSC `owner()=0x0000000000000000000000000000000000000000`, `isSealed()=true` via function selector `0x631f9852`. This is **on-chain source-supported narrow status**, not a proof all ecosystem contracts immutable.
- Claimed token total economic cap **21 million**, planned start **7,200 BEM/day**, four-year halvings. Token holders dilute with future emission; after ~372.5k minted, a 2.628m annual production at full rate is huge versus current minted stock. Reward eligibility governed by dynamic verified/unverified pools and future network weight. Avoid treating the day's nominal issuance as sale volume.
- At secondary onchain BEM/USDT mid **$37.38** (~2026-10-17 05:25 UTC): minted-supply notional cap **$13.924m**, *not confirmed free-float MC*; 21m maximum-supply FDV **$784.98m**. Initial minted supply only ~1.774% eventual maximum; no near-term linear float equality. Daily nominal new issuance **$269,136**, neither treasury revenue nor proof of selling.
- Bridge third-party onchain observer https://tapeout.work/api/v1/bridge at ~06:00 UTC showed **8,620.445885 BEM locked on BSC bridge** and **8,620.445885 X Layer minted**, matched at that time, 3-of-5 multi-signers, upgrade authority not fully renounced, LayerZero/config validity incomplete. Later independent **BSC direct `BEM.balanceOf(0xa84b8d3893de6e9922f2b29be1e1b115845f5e72)=8,586.810277 BEM`**, a different time: delta (~33.635608) is **NOT a proven bridge shortfall** absent same-block dual-ledger reading. X Layer raw Blockscout connection fails chainId196 unsupported; mark latest synchronized supply **UNVERIFIED** rather than asserting mismatch.
- Platform TapeHub `0xb7e8392c82ee55706465cc4d9b173e9c9af124fe` observer reports upgradeable by EOA `0x844676f2f13a3178b6d908a1ce18630ad15bfc51`. This does not directly imply sealed PoD emitter can be changed, but applies to wider product/security surfaces.
- Claimed fee buybacks/burn percentages from marketing/docs need onchain treasury attribution, actual swap events, burn-vs-transfer distinction, revenues and effective beneficiary before treating as proven yield. A transfer to `0xdead` reduces effective usable float but does NOT decrease ERC20 totalSupply unless burn changes contract supply.
- Salus Security has a 2026-09-04 TapeOut PDF audit in auditor's public reports repo https://github.com/Salusec/Salus-audit/blob/main/2026/Tapeout_audit_report_2026-09-04.pdf ; exact version/scope/findings and X Layer/bridge inclusion **NOT VALIDATED**, so publication alone is not universal clean bill.

## 6. Market structure, observed spot price, real exit

- Most liquid observed BSC PancakeSwap v3 BEM/USDT 1% fee pool `0x3098d7a051045000d68ec0360753a40c8cabea31`; a concentrated-liquidity pool mid quote is NOT guaranteed execution price; fee and depth range matter.
- Independent monitor at ~2026-10-17 05:25 UTC: deepest BEM/USDT pool **$37.38 mid**, 24h reported low ~$36.41, high ~$41.10; aggregated 8 monitored BEM/USDT pool liquidity **~$592,199**, monitored ~235 pools 24h traded **~$1,059,097**; separate wider DEX aggregators differ by inclusion and freshness. Keep scopes separate.
- Earlier secondary quotes ~Oct 10 $28.44; ~Oct15 $37.47; Oct17 ~$37.38, **three irregular dated points, NOT reliable OHLC/VWAP/ATH**. High early-token volatility, shallow execution depth relative to six-figure capital.
- Binance public BNB/USDT **$722.47** during research, time-sensitive. No verified Binance centralized BEM listing; using Binance for BNB spot is not claim that Binance lists BEM.
- For 600 BNB ($433,482) deployed outright to buy BEM, spot theoretical quantity **11,596.629 BEM** at $37.38 **before price impact, fees, available supply**. Given ~$592k BEM/USDT shown liquidity and $1.06m 24h volume, assuming a $433k market order moves price smoothly $39→$50 is **unfounded**. Must get tiered concentrated-liquidity exact-in multi-hop quote and MEV slippage before comparing. Any future unwind suffers opposite impact.
- Active BEM LP concentrated under specific address; token holder Top 10/20 excluding LP/CEX/bridge/dead not fully decoded, so do not label a 'whale bought' unless wallet funding and controller reconciled.
- BEM perpetual futures OI/funding and options, reputable prediction-market event with provable liquidity **not located**, so `NOT_AVAILABLE/UNVERIFIED` in this review.

## 2026-10-17 OKX Web3 limit-order rejection and independent pool verification

User screenshot (2026-10-17 at approximately 13:57 Asia/Bangkok): BEM short address `0x5c...695a`, UI ~$37.08/BEM, market cap ~$13,608,600, total aggregated liquidity ~$1,092,300 and UI 24h -2.01%; OKX Web3 **limit-order buy** displays `此代币流动性不足，存在风险，暂无法交易` and cannot submit order. User screenshot is UI evidence of **this OKX route/mode refusal**, NOT proof that BSC swaps universally stopped, and not on-chain proof of a blacklist or honeypot. Order input amount was blank; this cannot be blamed on an explicitly entered large quantity.

**Direct BSC RPC independent countercheck, same 2026-10-17 research session**:
- PancakeSwap v3 BEM/USDT contract `0x3098d7a051045000d68ec0360753a40c8cabea31` has live `token0=0x55d398326f99059ff775485246999027b3197955` (USDT, 18 decimals); `token1=0x5ce033B2bFCa3Af30b3e8C8457DeaF776A8b695a` (BEM, 8 decimals); `fee=10000` (1% tier), nonzero active `liquidity()` and nonzero `slot0()`.
- `BEM.balanceOf(pool)=7,480.6977415 BEM` and `USDT.balanceOf(pool)=202,328.36960676254 USDT` from direct ERC20 `balanceOf` eth_call. `slot0.sqrtPriceX96` gives indicative **~$36.54453 USDT/BEM**; marked combined pool-token inventory ~$475,706.95 at this spot, **not exact in-range executable depth or a trading quote**. v3 can have out-of-range positions; total token inventory != active depth. Both balance and price are latest-block reads, not frozen common exact block; variation possible.
- This pool is a **real BSC onchain venue**, independent of OKX limit-order frontend. The screenshot's ~$1.092m "total liquidity" includes other pairs/venues/data methods and CANNOT be assumed available for a single BEM/USDT route or exit size. The direct single venue's ~7,481 BEM inventory is smaller than ~11,210 BEM theoretical buy-size of 580 BNB (~$419k at dated assumptions); large market orders could suffer extreme slippage across price ranges or require multiple pools.
- PancakeSwap official docs distinguish pool custody assets from *in-range active* concentrated liquidity, and expose Smart Router with multihop and split routing: https://docs.pancakeswap.finance/earn/pancakeswap-pools and https://docs.pancakeswap.finance/trade/pancakeswap-exchange/fees-and-routes .
- OKX primary limitations: https://web3.okx.com/zh-hans/help/reasons-for-dex-transaction-failures-and-how-to-resolve-them and https://www.okx.com/zh-hans/help/what-is-limit-order-in-dex . Causes are per token risk control, per-route DEX liquidity thresholds, or unsupported **limit** order path. Precise cause in this screenshot **UNCONFIRMED**. Switching UI to Swap/Flash/market **for read-only quote inspection only** may discriminate limit mode from total route block; never bypass a genuine risky-token protection to force a trade.
- **Financial impact**: static mining ROI assumes BEM rewards can be sold every day near index mid. Verified pool reserves, concentrated-range depth, USDT fee tier (1%), swaps available on alternative routes and partial sell quotes are decisive. A ~$269k/day newly minted BEM notional at $37.38 is large relative to the ~$202k quote inventory in this individual pool, though it is **not** observed actual sell volume. Do not confuse daily minting with daily dumping.
- User requested project research, no mandate to buy BEM/miners; no money transferred, orders placed, tasks or alerts created. Add this as a durable exit-liquidity risk event, not a blanket chainwide scam verdict.


## 7. KOL 3 machines and actual marketplace secondary liquidity

- User post: `190 + 190 + 200 = 580 BNB`, colloquial "about 600", **not exactly 600**, and 3 actual onchain sale tx hashes NOT provided.
- Marketplace displayed an executed **190 BNB** transfer of **Behemoth circuit #1147.1** (`0x1F5Cb4aeaE1807Bf60c3b9C0D8aDBCC14e91f12C`), `NAND=603`, weighted approx 3.62KH, **estimated 16.370 BEM/day** and **11.61 BNB/(BEM/day)**. App source https://tapeout.firsto.ai/circuits/0xb1024b89886b9a34aa4ff5f31c411d708b20a14c/8814; **independent transaction hash & wallet attribution not verified**, preserve as secondary terminal observation. No reliable extra hashes for other 190/200 from post.
- Firsto terminal indicative 99% verified mining pool daily-capacity index **12.89 BNB/(BEM/day)** at a dated displayed snapshot; secondary-market bid/ask, indivisible whole-NFT purchases, program access, admin upgrade, NFT metadata and mining validity require each actual contract check. Market claims 24h circuit turnover ~1.60k BNB, 410 circuit changes; don't confuse executed secondary NFT turnover with primary protocol revenue.
- BSC has multiple NFT/processors, markets, most circuits do NOT necessarily yield BEM. Circuit NFTs can have nonmining web-hosting/computation functions. X Layer onchain circuits are an independent activity, do not equate with BSC BEM miner payout.

## 8. Economic model and why large investors might buy circuits

Inputs: BNB=$722.47, BEM=$37.38, capacity quote q=**12.89 BNB per 1 BEM/day**, 600 BNB budget as author's rounded scenario.
Definitions:
`C_USD = capitalBNB * priceBNB`
`Q = capitalBNB / q` estimated BEM/day at quote and fixed weight
`R_day = Q * priceBEM`
`simplePaybackDays = C_USD / R_day = q * priceBNB / priceBEM`.
At **600 BNB**:
- initial cash **$433,482**;
- theoretical miner stream **46.547711 BEM/day** if secondary asset purchases genuinely fill at capacity quote;
- immediate sell at $37.38 => **~$1,739.95/day** gross; **~249.13-day static payback**;
- if simply buying BEM spot without impact, ~**11,596.63 BEM right away**;
- 240 days constant output would mine **11,171.45 BEM**, below instant token notional (but miner NFT retains optional resale value, could be more/less liquid or worthless).
- for actual unrounded author trade **580 BNB** at same quote: same payback ratio and stream ~44.996 BEM/day; don't attribute $433,482 actual trade cash as fact.
- **190 BNB Behemoth individual example**: 16.370 BEM/day, 190 BNB capital **$137,269.30**, ~$611.91/day at $37.38; **224.33-day** static gross payback, before fees/dilution; aftermarket capacity rate 11.61 vs average 12.89.
- At $50 BEM and same constant capacity, the hypothetical 600 BNB machine payback is ~186.25d, NOT automatically 240d. The KOL's 16.6 BNB/(BEM/day) at $50 follows mechanically from holding payback at 240d: `240*50/722.47=16.6097`. It is a **resale repricing hypothesis**, not a protocol quotation or market guaranteed buyer.
- Price $15 / $25 / $37.38 / $50 / $75 gives constant-power payback **620.84 / 372.51 / 249.13 / 186.25 / 124.17 days**. Assumes instant claim and sales, no fee, stable BNB/USD.
- Network difficulty/dilution: miner actual output is function of share of verified pool weight; if aggregate eligible weight grows and same H held, daily BEM output declines. Assuming total network weight +0.25%/day for 240d and BEM fixed $37.38, recoup **~72.56% of acquisition cost** (no NFT resale); at +0.5%/day **~56.31%**; +1%/day **~36.82%**. No growth case **~96.33%**. These are illustrative growth models **NOT observed actual difficulty trend**; periodic repricing/halving/mining validity and BEM token price movements further change result.
- Fixed 7200 daily total means investors *compete for a fraction of output*; not additive unbounded yields; holder of NFT is buying a claim on variable future emission, NOT a fixed guaranteed BEM/day annuity. If larger new builders join, long-tail miners' emission decreases.
- Rational secondary NFT motives: stream future BEM from scheduled emissions; time-separated token acquisition / implicit DCA; token bullish plus residual NFT resale rights; underpriced NFT per unit verified hashrate; diversification from instantaneous BEM spot buy; opportunistic capital rotation and tax/capital structure; speculative belief mining-rights price will rise when spot price rises. None proves holder can profit or they're distinct investors. Secondary NFT purchases transfer BNB to prior owner; no automatic BEM buy-pressure or project revenue.
- Suspect/conflicts: large buyers may be same economic actor, market-making/internal transfers, or wash trading. Three txs lack proven unique funders; possible sell-side circuit is insider inventory; token price can stay flat while circuit prices pump as these are different markets and expected-duration bets.

## 9. Launch/valuation/security/social/prediction checklist

- Launchpad: Not an ICO or Launchpad for this screenshot, instead circulating mined token plus mined-output NFT market. Compare actual BEM market/LP history vs holder gains, not implied fundraising.
- Comparable project: no rigorous staged matched competitor trading multiples independently obtained; don't present DeFi TVL or mature L1 market caps as basis for BEM valuation. Product and token capture remain separate.
- Team financing/VC history: unconfirmed, don't invent early institutional token cost.
- Official audits: Salus audit PDF known published, exact findings/status not comprehensively inspected; do not call audited safe.
- NFT permission: ownership, transfer restrictions, operator authority, marketplace approval, bidding validity, reward claim and emergency pause must be rechecked on an exact circuit/processor contract before buying.
- Token supply admin: PoD miner sealed != every circuit processor immutable != token ERC20 all privileged roles revoked. `token.owner()` ABI function call reverted; no unsupported ownership claim.
- No independently verified substantial active/liquid prediction-market on BEM outcome, FDV, NFT price.
- Reddit/English community: no credible large organic independent consumer-business discussion located in this snapshot. Viral social post 8,384 impressions + 24 likes in user's screenshot is not high-conviction evidence of actual smart-money bets. Three purchases with unverified tx remain unconfirmed KOL lead.
- Financial conclusion: protocol and marketplace operational at L4, yet revenue from third-party use versus endogenous mining demand unresolved; token has extremely large eventual supply and daily emission, thin market, bridge/admin risks; circuit NFTs face token price, network weight competition, illiquid resale and technological risks. **Do not buy miners just because 240-day gross payback appears attractive**.

## 10. Outstanding evidence plan (research only)

1. Obtain exact three NFT sale **BSC tx hashes** for 190,190,200 BNB and reconcile net paid BNB, NFT circuit ids, ownership changes, buyer/seller/control clusters and fee recipients; if no hashes, leave remaining two `UNVERIFIED`.
2. Query current verified weight and exact mining rewards formula from production PoD contract (not only UI estimates), check weekly weight growth and new rigs; store trailing 14/30d H index and daily reward reconciliation before estimating investment ROI.
3. Retrieve exact Firsto secondary market contract verified bytecode/ABI, quote book breadth, seller wallet concentration and realizable bids for chosen circuit size. Compare buy price vs **sell-side executable** price, don't mark NFT at ask.
4. Query granular Pancake v3 tick bitmap/liquidity and slippage for BEM buy size 600 BNB and future large sale size, multi-pool routing, MEV and 1% pool fee. Price feeds are not executable size quotes.
5. Same-block X Layer minted/supply and BSC locked BEM across bridge, read full multisig threshold/admin upgrade path and LayerZero config; X Layer actual swap pools and transfers separately.
6. Full direct holder/top100 BEM excluding LP/bridge/burn and factory/creator wallets, identify unverified OTC or coordinated distribution; onchain tokenomics beyond cap claims.
7. Independently verify issuer legal entity, historical founder projects, financial statements and customer evidence, product integrations (TapeKit vs miner subsidy), Git change timing, actual Salus audit scope and any unresolved findings.
8. Reconcile actual protocol fees, wallet receipts, claimed 80%/50% buybacks with purchase and **real burn** evidence; distinguish internal mint/NFT turnover from external protocol income.
9. All status changes here require a new user request; no scheduled monitoring, trading or new wallet action authorized.

## Primary/source references (mostly non-Chinese sources, chain/official preferred)

- https://tapeout.net/
- https://tapeout.work/api/v1/chains
- https://tapeout.work/api/v1/bridge
- https://tapeout-public-monitor.tapeout-labs.workers.dev/
- https://bscscan.com/token/0x5ce033B2bFCa3Af30b3e8C8457DeaF776A8b695a
- https://bscscan.com/address/0x7e2e0dc66a3bd9103e69b766afa62d9f7b697b46
- https://github.com/TapeOutProtocol/TapeKit
- https://github.com/TapeOutProtocol/TAPs
- https://github.com/Salusec/Salus-audit/blob/main/2026/Tapeout_audit_report_2026-09-04.pdf
- https://firsto.ai/data (secondary execution-terminal indication; trade transaction hashes not verified, Chinese front end not treated as primary)
- https://tapeout.firsto.ai/circuits/0xb1024b89886b9a34aa4ff5f31c411d708b20a14c/8814 (secondary)
- https://x.com/Deibajie/status/2111160033782489587 (KOL screenshot only).
