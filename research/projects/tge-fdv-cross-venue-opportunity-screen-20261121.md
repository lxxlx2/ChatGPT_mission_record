# TGE / FDV 跨预测市场停运项目的 No 交易机会调查（2026-11-21）

> **CORRECTION 2026-11-21: Prior first-pass list was INCOMPLETE**. Printr and Linera were missing despite being visible in the Polymarket FDV category. The earlier 3-project high-confidence screening was not an exhaustive catalog and must not be treated as an exhaustive investment opportunity list. See Section E. Full cross-platform pagination and L2 CLOB quantities remain unverified.


Status: RESEARCH_ONLY / WATCH / ORDER_BOOK_UNVERIFIED
As-of: 2026-11-21 Asia/Bangkok
Base branch/commit at research start: `main` / `f5c07f601425ec2e1de6ee9d448d2e140336fb30`
Authority: `crypto-300-profit-mission/PROJECT_ANALYSIS_FRAMEWORK.md`, `PROJECT_ANALYSIS_EVIDENCE_WORKFLOW.md`, `token_trading_principles.md`, `MISSION_SPEC.md`.
Scope: first-pass multi-venue catalog, event-rule verification, issuer-state screening, not trades or production monitoring. No limit orders, position changes, or task/monitor creation.

## Method and important limitations

1. Discover TGE and post-TGE FDV questions **before** classifying project survivorship; dedupe by project, market, threshold and settlement deadline.
2. Preserve evidence tiers: official issuer shutdown/token cancellation; operations suspended but token uncertainty; merger/pivot but product alive; no corresponding open PM; resolved market.
3. Verify individual market terms. The typical FDV contract resolves NO if the qualifying token has not launched by the specified deadline, but dates vary. Do not equate a product's sunset date with the prediction contract's resolution date.
4. Record venue, collateral, deadline, price-source rule, all listed thresholds, executable No ASK, aggregate quantities and fee-adjusted price. Index-page % is **not** a No ASK and lifetime volume is **not** executable depth.
5. Compute `gross payoff if No = (1-p)/p`; breakeven Yes probability is `1-p`; price must be from executable level, not a midpoint; include time cost, fees, collateral issuer and oracle risk. Markets in different venues may share the same upstream resolution, so not an independent hedge.
6. This pass could read the browser-opened Polymarket Abstract page for 9 displayed prices and inspect indexed webpages for other venues. **Live CLOB level sizes, fillable quantities, precise order execution, full catalog pagination and fee schedule were NOT verified.** No list can honestly be called exhaustive across all currently-listed individual prediction markets with these access limitations.

## A. High-confidence cancellation / sunset candidates

| Project | Status and original evidence | Polymarket | Predict.fun | OPINION | Limitless | Rule-based No scenario | Verification |
|---|---|---|---|---|---|---|---|
| StandX | 2026-10-15 official announcement: platform token cancelled; DUSD compensation and scheduled wind-down. https://x.com/StandX_Official/article/2110613283967230232 | https://polymarket.com/event/standx-fdv-above-one-day-after-launch ; also https://polymarket.com/event/will-standx-launch-a-token-by | https://predict.fun/market/standx-fdv-above-one-day-after-launch | https://app.opinion.trade/market/standx-fdv-above-one-day-after-launch | https://limitless.exchange/markets/standx-fdv-above-dollar1b-one-day-after-launch-1767884376556 | No qualifying token by 2026-12-31 23:59 ET => No for FDV markets reviewed | Strong project No, executable quotes missing |
| Abstract (ABS) | 2026-10-06 official wind-down and no token, chain closure planned 2026-12-15; original official account: https://x.com/AbstractChain ; independent original report https://www.coindesk.com/tech/2026/10/07/pudgy-penguins-abstract-becomes-second-ethereum-layer-2-to-shut-in-a-week | https://polymarket.com/event/abstract-fdv-above-one-day-after-launch ; TGE timing markets also indexed | https://predict.fun/market/abstract-fdv-above-one-day-after-launch | No verified matching contract in this pass | No verified matching contract in this pass | No qualifying governance token by 2027-12-31 23:59 ET => No | Strong project No, ~1y+ lockup |
| Ventuals | Official 2026-06-15 sunset and explicit no Ventuals token: https://app.ventuals.com/ | https://polymarket.com/event/ventuals-fdv-above-one-day-after-launch ; https://polymarket.com/event/will-ventuals-launch-a-token-by | https://predict.fun/market/ventuals-fdv-above-one-day-after-launch | No verified matching contract | No verified matching contract | No qualifying token by 2026-12-31 23:59 ET => No | Strong project No; Predict.fun was near-zero historical volume |

### Full discovered FDV threshold groups in primary target venues

- StandX Polymarket: $50M, $100M, $200M, $400M, $800M, $1B, $2B, $3B, $5B, $7B, $10B (11). Predict.fun: $200M, $400M, $800M, $1B, $2B, $3B, $5B, $7B, $10B (9). OPINION: $800M, $1B, $2B, $3B, $5B, $7B, $10B (7). Limitless: observed $800M, $1B, $2B (3). Check every threshold's exact rule before execution.
- Abstract Polymarket: $200M, $400M, $600M, $800M, $1B, $1.5B, $2B, $2.5B, $3B (9); Predict.fun has a matching 9-threshold family. Polymarket live page in browser displayed Buy NO 98.0c, 97.9c, 97.5c, 98.5c, 99.0c, 97.9c, 98.2c, 97.9c, 98.0c respectively, **but no verified size at those quotes**; No at 97.5c yields theoretical 2.56% gross return until settlement.
- Ventuals Polymarket and Predict.fun: $100M, $300M, $500M, $800M, $1B, $1.5B, $2B (7 each). Predict.fun cached indexed book shows ~$100 aggregate trading across group (not executable availability).
- StandX OPINION displayed YES probabilities approximately $800M 7%, $1B 0%, $2B 4%, $3B 5%, $5B 2%, $7B 2%, $10B 10% (fresh indexed Nov 21). THESE ARE NOT EXECUTABLE NO BUY PRICES. OPINION lifetime total displayed ~$195.84M with bonus points active, does not prove usable liquidity.
- Limitless $1B StandX displayed wildly inconsistent snapshot examples (50/50 in recent search excerpt, 15.5% / 84.5% in older opened page) while the exposed orderbook had no bid/ask rows. **Never market-order 50c based on that figure**. Limitless rule text says it resolves according to Polymarket's final resolution and rules, sharing upstream outcome risk.

### Primary market links
- https://polymarket.com/predictions/fdv
- https://predict.fun/
- https://app.opinion.trade/pre-tge
- https://limitless.exchange/crypto/type
- https://kalshi.com/markets/kxtokenlaunchventuals/ventuals-token (historical 2025 token-launch contract; not a currently actionable 2026/2027 market)

## B. Provisional risk candidates, not proven token cancellations

| Entity | Observable state | Linked market | Gate |
|---|---|---|---|
| Neutrl (possibly what user calls 'neural'; exact identity not confirmed) | 2026-08 NUSD reserve/liquidity impairment and paused issuance/redemption; a special redemption program was communicated. None of those facts independently proves governance token cancelled. Official announcements: https://telegram.me/s/NeutrlOfficial | https://polymarket.com/event/neutrl-fdv-above-one-day-after-launch ; https://predict.fun/zh-cn/market/neutrl-fdv-above-one-day-after-launch ; https://polymarket.com/event/will-neutrl-launch-a-token-by | Need official latest operations status and whether governance token plan legally or operationally cancelled; NUSD stablecoin does not satisfy governance token market's launch condition |
| Felix | 2026 HIP-3 trading venue shut, but lending business may still operate; closure of a product is not proof of cancellation of all token plans | https://polymarket.com/event/felix-fdv-above-one-day-after-launch | Require canonical issuer cancellation confirmation |
| Farcaster / Neynar | Acquisition/merger and strategic changes, but network operations not necessarily ended | No verified active matching token-launch/FDV market | Do not classify as automatic No |
| Polynomial | 2026 shutdown reports and cancelled token attempt | No verified currently open matching FDV/TGE market | No executable position identified |
| Tally | 2026 closure reports | No verified currently open matching FDV/TGE market | No executable position identified |
| Blast | Layer 2 closure/wind-down reported in 2026, **BLAST token already launched 2024** | Any future first-TGE proposition requires special scrutiny | Exclude as fake new-token No trade |

## C. Wider surfaced pre-TGE / FDV market inventory awaiting status gate

The indexed market catalogs also surface Predict.fun, Variational, Extended, Puffpaw, OpenSea, Cambria, QFEX, MetaMask, Multipli.fi, Base, MagicBlock, Arc, Unit, Relay, Probable, Pacifica, Theo, Veera, Ostium, Papertrade, Ink, Noble, N1, Nansen, Loopscale, Exponent, Hyperbeat, Perena and fomo.family, among others. These are **not asserted to be shut down or automatic No**. Exact event IDs, all active expiries and per-strike orderbooks require further enumeration. Index search feeds are not a complete authenticated list.

## D. Trade gate and allocation rule

No `SETUP` before all of the following pass:
- exact event and official project canonical identity;
- original English market terms and deadline, qualifying governance token definition, price source, UMA/venue settlement and dispute;
- dated issuer cancellation or verified shutdown, with mergers/rebrands evaluated;
- executable No ASK and aggregate amounts at size $100/$500/$1000 and fill slippage, not screenshot odds, 50/50 placeholders or historical turnover;
- exact fees, settlement currency and collateral risk; date to realistic final redemption, not early shutdown date;
- independent market only if oracle sources genuinely independent, otherwise treat as correlated venue exposure;
- monotonically ordered FDV thresholds and cross-strike mispricing tested with both legs *simultaneously executable*; if not, note pricing inconsistency only.

Current decision: **WATCH** for StandX, Abstract, Ventuals; **RESEARCH / NO_CANCELLATION_PROOF** for Neutrl; **NOT_ACTIONABLE** for historical Kalshi Ventuals and unverified matched markets.

This is a material dated research snapshot, not production authority, a position, or a task. No automated polling, order, wallet signature, Gmail or production change authorized.


## E. Correction: two additional confirmed shutdown candidates discovered from full FDV category review (2026-11-21)

### E1. PRINTR: CONFIRMED shutdown + TGE/airdrop cancellation, strong NO conditional evidence

Official issuer announcement dated 2026-08-17:
- https://x.com/printr/status/2089378985507746006
- Official channel mirrored announcement: https://t.me/s/printrgobrrr
- "all operations will cease by 31 August 2026", staking returned to wallets, application offline, **"there will be no Token Generation Event (TGE) and airdrop."**
- This project should have been found in the initial screening. Error root cause: initial pass sampled projects rather than enumerating category markets first and verifying issuer shutdown status one by one.

Official Polymarket market: https://polymarket.com/zh/event/printr-fdv-above-one-day-after-launch
- Rule: only official Printr token, actively publicly tradable; stablecoin/meme/LST/synthetic excluded; FDV = supply x day-after-launch price. If no qualifying launch by **2027-12-31 23:59 ET**, corresponding **NO** wins. Project sunset 2026-08-31 does not cause automatic early settlement.
- 10 thresholds and **live browser-connected page visible NO buy buttons** on 2026-11-21. The numbers are displayed *buy No price*, not verified executable CLOB levels or sizes:

| FDV threshold | Displayed Buy No (USDC cents) | Gross payoff if No, % | Evidence |
|---|---:|---:|---|
| $50M | 89.5 | 11.73 | browser tab `1243267652`, 2026-11-21 |
| $80M | 95.1 | 5.15 | same |
| $100M | 95.7 | 4.49 | same |
| $150M | 93.4 | 7.07 | same |
| $200M | 95.5 | 4.71 | same |
| $300M | 96.0 | 4.17 | same |
| $400M | 94.1 | 6.27 | same |
| $500M | 95.7 | 4.49 | same |
| $800M | 93.9 | 6.50 | same |
| $1B | 93.8 | 6.61 | same |

Gross payout formula `100 / displayed_cents - 1`; excludes fees, financing and order slippage. Listed cumulative volume $235,868. No per-price size was available through browser read-only tab context.
- Top-of-book displayed price sum (e.g. $50M YES 21.0c + NO 89.5c = 110.5c) implies a large spread / mark microstructure; do not assume displayed price represents deep executable capacity. The 2027 deadline entails ~1y+ funding lockup.
- Relative strike inconsistencies are observable (e.g. $400M NO 94.1c cheaper than $200M NO 95.5c), but do not call it arbitrage without **both bid/ask executable levels** and volume.

### E2. LINERA: CONFIRMED shutdown, with issuer preserving vague hope to resume someday

- Official current homepage https://linera.io/ says "Linera has ceased operations", Sonar sale attracted nearly $900k but missed minimum; refunds made; emergency financing failed; the team also wrote "**We still hope to finish the protocol and launch applications on it in the future.**" Therefore classify as **SHUTDOWN / POSSIBLE FUTURE REVIVAL**, not proven permanent cancellation of every conceivable new official token.
- Reported founder announcement on official Discord was 2026-09-18. The public Sonar sale was unsuccessful; no verified qualifying public token launch.
- FDV event: https://polymarket.com/event/linera-fdv-above-one-day-after-launch ; same no-token-by **2027-12-31 23:59 ET** -> NO rule. Nine strikes $100M,$200M,$300M,$400M,$500M,$600M,$700M,$800M,$1B. Recent Polymarket web result (crawled ~4 days ago, **not live CLOB**): Buy NO **84c,88c,90c,89c,97.5c,97.2c,97c,97c,97.6c**, respectively; $100M 84c would imply gross 19.05% if really executable. All current sizes unverified.
- TGE deadline event: https://polymarket.com/event/will-linera-launch-a-token-by ; date-scoped NO contracts for 2026-12-31, 2027-03-31, 2027-06-30, 2027-09-30, 2027-12-31. Recent web cached NO purchase prices 91c,88c,92c,90c,90c respectively, **not current executable quotes or verified size**. Individual deadline markets must be checked for final rules and payout dates.
- Critical differentiation: reactivation could affect the long-dated No thesis despite current shutdown.

### E3. Other projects surfaced directly from user's FDV category screenshot / live category sources

| Project | Evidence/status | No thesis |
|---|---|---|
| Apyx | Official Sep 2026 TGE delay and ongoing Season 2; https://blog.apyx.fi/apyx-tge-update/ | EXCLUDE from confirmed cancel bucket; active/delayed |
| Felix | SEC 10-Q and company announcement confirm **Felix HIP-3 perp exchange** June 2026 termination, but Felix lending remains separate active protocol; https://ir.hyperiondefi.com/news-events/press-releases/detail/314/hyperion-defi-reiterates-guidanceon-sunset-of-usdh-and-felix-markets | product-specific closure, governance token cancellation UNVERIFIED |
| TownSquare | DefiLlama still reports protocol TVL, not official shutdown; https://defillama.com/protocol/townsquare | do not call dead |
| StripChain | Official $STRIP sale communications and developer activity surfaced; no authoritative shutdown | do not call dead |
| Pacifica, Unit | In current FDV category; official token cancellation NOT established | research later |
| Printr | Official cancellation | CONFIRMED |
| Linera | Official cessation with possible future resumption | CONFIRMED cessation |

### E4. Primary-source market coverage and remaining blockers

Observed `Polymarket /predictions/fdv` index has an interactive "Show more markets" control; browser connector permits only reading existing tab text, not paging or opening its market filter. Search result text reported '500 active markets', which does not prove that all 500 individual market entries have been inspected.

Other platforms queried: Predict.fun, OPINION, Limitless, Kalshi, but no verified currently matching Printr/Linera FDV orderbook at other venues this sweep. **Do not infer absent** merely because search returned none.

Current priority for further review: `Printr $50M NO` (visible 89.5c), `Linera $100M NO` (recent web result 84c; not live), then short-dated `StandX/Ventuals` (lower total return may be offset by shorter hold period). All remain WATCH pending real executed ask sizes, $100/$500/$1000 VWAP, chain/book data and exact fee/collateral verification.

Mandatory operational caution: **no trades, automatic monitors, emails or production automation authorized**. No live quote or order execution proven.


## F. Second-pass evidence-based catalog expansion from user screenshot and connected browser (2026-11-21)

**Not an exhaustive verified all-platform scan.** The user specifically requests all liquid venues and all crypto token launch + FDV markets before screening stopped projects. Data-source audit: connected browser Polymarket `/zh/crypto/pre-market/token-launch` yielded precisely **39 unique event slugs** after removing nested expiry links; this is only loaded initial page (not all pages, all times, or all categories). Polymarket public Gamma REST supports pagination and CLOB book-level sizes but was inaccessible through current network/web tools. The container cannot DNS resolve Gamma. Do not claim that all markets or full orderbook sizes were retrieved. FDV names and all previous candidates are separate additions; a verified exhaustive coverage count across venues is currently UNAVAILABLE.

### F1. 39 distinct Polymarket Token Launch event URLs extracted from browser

1. Predict.fun会在___前推出代币吗？ | https://polymarket.com/event/will-predictfun-launch-a-token-by
2. Jumper会在___之前启动令牌吗？ | https://polymarket.com/event/will-jumper-launch-a-token-by
3. Exponent会在___之前启动令牌吗？ | https://polymarket.com/event/will-exponent-launch-a-token-by
4. Revolut会在2026年推出美元稳定币吗？ | https://polymarket.com/event/will-revolut-launch-a-usd-stablecoin-in-2026
5. Tuyo会在___之前推出代币吗？ | https://polymarket.com/event/will-tuyo-launch-a-token-by
6. Hibachi会在___之前发行代币吗？ | https://polymarket.com/event/will-hibachi-launch-a-token-by
7. Betmoar会在___之前推出代币吗？ | https://polymarket.com/event/will-betmoar-launch-a-token-by
8. Phantom会在___前推出代币吗？ | https://polymarket.com/event/will-phantom-launch-a-token-by
9. Arc会在___前发放代币吗？ | https://polymarket.com/event/will-arc-launch-a-token-by
10. Spark会在___前推出代币吗？ | https://polymarket.com/event/will-spark-launch-a-token-by
11. Base会在___之前启动令牌吗？ | https://polymarket.com/event/will-base-launch-a-token-in-2025-341
12. Hylo会在___之前推出代币吗？ | https://polymarket.com/event/will-hylo-launch-a-token-by
13. Prjx会在___之前启动代币吗？ | https://polymarket.com/event/will-prjx-launch-a-token-in-2025
14. Rabby会在___之前推出代币吗？ | https://polymarket.com/event/will-rabby-launch-a-token-by
15. Canza会在___前推出代币吗？ | https://polymarket.com/event/will-canza-launch-a-token-by
16. 滑翔机会在___之前启动代币吗？ | https://polymarket.com/event/will-glider-launch-a-token-by
17. Opensea会在___之前推出代币吗？ | https://polymarket.com/event/will-opensea-launch-a-token-by-142
18. Pacifica会在___前推出代币吗？ | https://polymarket.com/event/will-pacifica-launch-a-token-by
19. Cashmere会在___前推出代币吗？ | https://polymarket.com/event/will-cashmere-launch-a-token-by
20. 庭院会在___之前推出代币吗？ | https://polymarket.com/event/will-courtyard-launch-a-token-by-20260727145836884
21. Axiom会在___之前推出代币吗？ | https://polymarket.com/event/will-axiom-launch-a-token-in-2025
22. Dreamcash会在___前推出代币吗？ | https://polymarket.com/event/will-dreamcash-launch-a-token-by
23. Soneium会在___之前推出代币吗？ | https://polymarket.com/event/will-soneium-launch-a-token-by
24. N1会在___之前推出代币吗？ | https://polymarket.com/event/will-n1-launch-a-token-by
25. 霸王龙会在___前推出代币吗？ | https://polymarket.com/event/will-t-rex-launch-a-token-by
26. Miracle会在___前推出代币吗？ | https://polymarket.com/event/will-miracle-launch-a-token-by
27. Axis会在___之前启动代币吗？ | https://polymarket.com/event/will-axis-launch-a-token-by-20260729144519159
28. Robinhood Chain会在___之前推出代币吗？ | https://polymarket.com/event/will-robinhood-chain-launch-a-token-by-20260727172111377
29. Beezie会在___之前推出代币吗？ | https://polymarket.com/event/will-beezie-launch-a-token-by-20260727145435056
30. 怪物会在___前发动代币吗？ | https://polymarket.com/event/will-monster-launch-a-token-by-20260727145113739
31. Phygitals会在___之前推出代币吗？ | https://polymarket.com/event/will-phygitals-launch-a-token-by-20260727144541111
32. 土星会在___之前发射代币吗？ | https://polymarket.com/event/will-saturn-launch-a-token-by
33. Will 3Jane launch a token by ___? | https://polymarket.com/event/will-3jane-launch-a-token-by
34. Fuse Energy会在___前推出代币吗？ | https://polymarket.com/event/will-fuse-energy-launch-a-token-by
35. QFEX会在___之前推出代币吗？ | https://polymarket.com/event/will-qfex-launch-a-token-by
36. Meta会在2026年推出美元稳定币吗？ | https://polymarket.com/event/will-meta-launch-a-usd-stablecoin-in-2026
37. 特朗普会在12月31日前发行一种加密货币吗？ | https://polymarket.com/event/will-trump-launch-a-coin-by-january-31
38. X会在2026年发行美元稳定币吗？ | https://polymarket.com/event/will-x-launch-their-own-stablecoin-in-2026
39. Perena会在___之前发行代币吗？ | https://polymarket.com/event/will-perena-launch-a-token-by

### F2. Additional FDV, TGE, related listing markets not covered by page above

Already listed in earlier sections: StandX, Abstract, Ventuals, Printr, Linera, Neutrl; also target market names via public category indexes:
Predict.fun, Variational, Extended, Ink, Base, OpenSea, GenLayer, MetaMask, Surf, Puffpaw, MagicBlock, Theo, Hyperbeat, Relay, Probable, QFEX, TownSquare, Apyx, Felix, Linera, Printr, Ventuals, Pacifica, Unit, StripChain, Cambria, Neutrl, Fomo.family, Perena, Tally (market not verified), Polynomial (market not verified), Veera, Ostium, Papertrade, 3Jane, Canza, Exponent, Nansen, Loopscale.
Category pages: https://polymarket.com/crypto/pre-market/fdv ; https://polymarket.com/crypto/pre-market/token-launch ; https://polymarket.com/predictions/fdv ; https://polymarket.com/predictions/token-launch
Other market families to check include *listing within N days after TGE*, e.g. https://polymarket.com/event/linera-listed-on-within-30-days-of-tge with an explicit no-token => NO clause; do not miss non-FDV outcome families.

### F3. Cross-venue category listing (recorded scope, incomplete due Load More and access restrictions)

- OPINION https://app.opinion.trade/pre-tge initial page rendered Metamask FDV, StandX FDV, OpenSea FDV, Predict.fun FDV, fomo.family token launch, Nansen token launch, Polymarket FDV, Loopscale token launch, Probable token launch/FDV, Polymarket token launch, Pacifica token launch, Exponent token launch, Puffpaw FDV, Hyperbeat FDV, Perena token launch. **Load more markets** not enumerated, OPINION live L2/API authentication not available. Percentages are midpoint / displayed probabilities and NO fill quantity UNVERIFIED.
- Limitless https://limitless.exchange/crypto/type page rendered 64 Crypto total category, ~32 Pre-TGE tag (page snapshot old and not a live 2026-11-21 guarantee), initial rows list Theo, Pacifica, Veera FDV, StandX FDV, Puffpaw FDV, Metamask FDV, OpenSea FDV, Ostium TGE. **Loading more markets** remains, current L2 size UNVERIFIED. Earlier spotty cached Limitless 50/50 StandX is NOT a demonstrated executable ask.
- Predict.fun https://predict.fun/ and explicit https://predict.fun/market/standx-fdv-above-one-day-after-launch and /market/ventuals-fdv-above-one-day-after-launch confirm both groups; logged-out index does not expose verifiable L2 fillable No ASK and depth. Found no authoritative proof of current $100/$500/$1000 fills.
- Kalshi public historical searches include Ventuals launch legacy series; no matching live confirmed FDV book in this investigation. Absence from search ≠ no market exists. Polymarket US and Myriad have different rules and should not be conflated with international Polymarket.
- Myriad https://myriad.markets/events/when-will-poly-tge confirmed separate token launch contract family but no verified shutdown-project matched current market.

### F4. Correct screenshot interpretation and migration vs closure

- **Hylo: ACTIVE**, not proven merged/cancelled. As of Nov 20 DefiLlama reports ~$41.03M TVL, ~$394,517 fees/30d and ~$181,552 revenue/30d. https://defillama.com/protocol/hylo ; 2026-10-20 new investment and 2026-11-03 new leverage product. No eligible governance token announced, but absence of token ≠ shutdown.
- **Axiom: ACTIVE**, not proven closed. Official https://axiom.trade still advertises active multi-chain trading and dated new blog 2026-11-10 https://axiom.trade/blog/token-scanner . Team's historical "no current plans to launch a native token" is not permanent cancellation; 2026/2027 token launch markets remain conditional.
- **Dreamcash: PARTIAL PRODUCT SUNSET**. HIP-3 CASH perp markets closed June/July; non-custodial trading app continues, not evidence of full issuer shutdown.
- **Beezie: CHAIN MIGRATION**. 2026-10-16 official https://beezie.com/blog/beezie-is-making-solana-its-home states ending Base operation, moving to Solana, not token cancellation.
- **Jumper: corporate spin-off**, still active and marketed JUMP public sale, not a canceled project. https://li.fi/knowledge-hub/li.fi-update-august-2026 .
- **Cashmere: ACTIVE** latest 2026-11-20 Terms; 2026-10 docs mention planned $CSM, exclude.
- **Perena: ACTIVE** with DefiLlama TVL November 2026; exclude.
- **QFEX: ACTIVE market data November 2026; exclude shutdown assumption.
- **Felix: PARTIAL product shutdown**, HIP-3 only, cannot infer all token plans.
- **Neutrl: LIQUIDITY/RESERVE INCIDENT**, issuance/redemption incident does not by itself prove cancellation of qualifying governance token.
- **Apyx: TOKEN DELAY**, official still developing; not eligible.
- **Printr: OFFICIAL PROJECT SHUTDOWN & TOKEN CANCELLED**, Aug 2026; stronger evidence than merely no news.
- **Linera: OFFICIAL SHUTDOWN / POSSIBLE REBOOT**, https://linera.io/ says ceased operations but team hopes to resume.
- **StandX / Ventuals / Abstract** official cancellation or sunset; corresponding rule/date separately checked above.

### F5. Oracle precedent and rule adjudication

- Polymarket's official rules: https://help.polymarket.com/en/articles/13364518-how-are-prediction-markets-resolved ; proposal needs bond; unsuccessful/too-early proposal can lose $750 bond. Disputes: https://help.polymarket.com/en/articles/13364551-how-are-markets-disputed ; the oracle can rule **Too Early**, **Unknown/50-50**, or a valid Yes/No. The presence of a formal explicit **'no qualifying token by deadline => No'** term is materially different from a general canceled-event contract.
- Real concluded FDV threshold markets available for studying the mechanics: https://polymarket.com/event/paradex-fdv-above-one-day-after-launch/paradex-fdv-above-1pt5b-one-day-after-launch-362-245-215-336-786-573-581-399-713 (Final outcome NO), https://polymarket.com/event/zama-fdv-above-one-day-after-launch (some Final outcome YES), https://polymarket.com/event/octra-fdv-above-one-day-after-launch (some Final NO). These prove threshold No/Yes outcomes are possible, **not a confirmed precedent of early No on a cancelled issuer more than 1y before deadline**.
- Distinguish cancellation, renamed governance token, moved token issuer, stablecoin/memecoin exclusions, delayed TGE and time-zone dependent observation. If the exact original wording says 'by Dec 31' and the TGE is before that date, a revived project can still turn a confident No into zero.
- Practical payoff: with verified executable weighted No price `p`, binary gross ROI `1/p-1`; share count `budget/VWAP` only if the orderbook shows sufficient size. Historical volume or index-level platform liquidity does not establish capacity. $100/$500/$1000 actual buying capacity is **UNVERIFIED for every candidate** due missing token IDs / CLOB depth via current access. Do NOT invent numbers.
- Do not promote 50/50 placeholder prices, stale index percentages, bid/midpoint prices or reward-farmed high notional volume to executable arbitrage.

### F6. Next actionable checks **remain incomplete**

For each of Printr, Linera, StandX, Ventuals, Abstract, fetch fresh market token IDs and raw CLOB No asks from the platform; evaluate all strikes/dates, cumulative size, $100/$500/$1000 weighted price and fees. Project official no-token statements strongly support expiry No but do not guarantee early resolution. Trade state WATCH / NO_GO unless specific executable price+size and account jurisdiction/settlement venue restrictions are verified.

Audit: correction only, no production monitor, scheduled automation, real wallet/venue order or position change.

## G. Direct official API execution attempt and reproducible one-shot scanner (2026-11-21)

### Work actually executed

- Verified official API specifications for Polymarket Gamma /events offset pagination (max limit 500) and CLOB /book, Kalshi open /markets cursor pagination, Myriad public /markets page pagination, Predict.fun /v1/markets and /markets/{id}/orderbook (mainnet API key required), OPINION /openapi/market and /token/orderbook (API key required), and Limitless /markets/active /markets/{slug}/orderbook (public read in SDK docs but latest academy documentation may require API signed requests).
- Created a **one-shot, read-only** source file and offline tests on the existing research branch:
  - `research/tools/crypto_tge_fdv_scan.py` at Git commit `9b94631e2f8a0c6c0ad1b7f0c4128d3a583af2a4`
  - `research/tools/test_crypto_tge_fdv_scan.py` at Git commit `ed4a65459b93ec9db9310d08411a98ba00d7084d`
- Local test run: `python -m unittest -v test_crypto_tge_fdv_scan.py` => **7 tests passed**; verified calculations for share-based No asks, VWAP/slippage/no-depth guards and Gamma parsing with synthetic data. This is an **offline unit test**, not live provider acceptance.
- Executed once against official internet hosts using `python crypto_tge_fdv_scan.py --out current_attempt --timeout 2 --max-pages 1 --max-books 10`. Exit code **2 (INCOMPLETE)**, exactly:
  - Polymarket Gamma: DNS/network resolution failure, pages read 0.
  - Kalshi: DNS/network resolution failure, pages read 0.
  - Myriad: DNS/network resolution failure, pages read 0.
  - Limitless: DNS/network resolution failure, pages read 0.
  - Predict.fun: `PREDICT_API_KEY` not connected, pages read 0.
  - OPINION: `OPINION_API_KEY` not connected, pages read 0.
  - Total relevant contracts from THIS LIVE API RUN: 0 **due to provider unavailability**, not zero actual markets. Executable orderbooks: 0. Not an all-venue scan.
- Browser source from user's connected Polymarket tab separately yielded 39 unique visible Token Launch event slugs in Section F. These are not direct API results and were not converted into false live market coverage.
- No requests for wallet balances, private user positions or authenticated trade execution; no orders, no production runtime changes, no scheduled jobs.

### Current completion gate

**MARKET_UNIVERSE_INCOMPLETE / NO_LIVE_BOOK_CAPACITY / RESEARCH_ONLY.**

No full-coverage verified market list has been obtained. The official API scanner is now available in Git with test evidence but it is not a substitute for successfully executing an actual network scan. It prints per-venue coverage/errors and writes `audit.json`, `markets.csv`, `coverage.json`; a failure or missing credential stays explicit and never turns into a claim of no markets.

The first-pass claim of a comprehensive all-platform review remains **withdrawn**. Verified issuer-status shortlist remains Printr / StandX / Ventuals / Abstract / Linera subject to exact venue contract deadlines, terms, and executable No ask liquidity; no candidate is authorized for trade from these results.
