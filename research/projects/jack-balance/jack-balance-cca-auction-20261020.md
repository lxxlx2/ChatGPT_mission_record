# Jack Butcher BALANCE / Credits / Statements — CCA auction, value capture and $500 investment decision

Updated: 2026-10-20 ~23:10 Asia/Bangkok. **USER_SUBMITTED_BIDS_364_367 / ONE_PERSONAL_ONE_ENTRUSTED / NO_CLAIM_OR_TOKEN_SETTLEMENT / NO_CHATGPT_TRADE**. The older 22:40 research-only assessment remains below as a dated snapshot.
Authority: `crypto-300-profit-mission/PROJECT_ANALYSIS_FRAMEWORK.md`, `token_trading_principles.md`, `MISSION_SPEC.md`. This now includes independently verified onchain **escrowed CCA bids** initiated by the user, without asserting tokens are already obtained or conflating entrusted funds with personal beneficial ownership.

## Verified user-submitted two bids, one personal and one entrusted — 2026-10-20

**Current position `BID_PENDING / CCA_OPEN / NO_TOKENS_CLAIMED / EXIT_RESTRICTED`**, supersedes initial research-only no-bid snapshot (which describes the **older 22:40** check). User reports **two separately beneficial positions: $500 own and $500 entrusted on behalf of another person**. Both bids owned at contract level by canonical wallet `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`; cannot determine which bid belongs to the user vs the entrusting person solely from contract, so **do not assign a Bid ID to a beneficial owner without evidence**. **Exclude entrusted ~$500 and corresponding entitlement/liability from personal portfolio totals.**

Direct Ethereum mainnet `bids(uint256)` ABI selector `0x4423c5f1` (returns `(startBlock,startCumulativeMps,exitedBlock,maxPriceQ96,owner,amountQ96,tokensFilled)`) retrieved:
- **Bid #364:** start block `26234863`, owner canonical wallet, locked `0.205500000000000000 ETH`, max price `0.0001608 ETH/BALANCE`, `exitedBlock=0`, `tokensFilled=0` before exit.
- **Bid #367:** start block `26234876`, same canonical wallet, locked `0.205000000000000000 ETH`, max price `0.0001600 ETH/BALANCE`, `exitedBlock=0`, `tokensFilled=0` before exit.
- **Total escrowed = 0.4105 ETH**, approx **$999.52** given contemporaneous ETH price **$2,434.88**. Remaining wallet native ETH read ~0.0029798849 ETH separately. Escrowed ETH does not remain in wallet balance; **never double-count deposit and refundable rights**. User-supplied Uniswap UI shows 0% complete and displayed preliminary 0.683 + 1.79 BALANCE, which are UI estimates, **NOT claimed or finalized token balances**.
- At direct read block `26234938`, chain `clearingPrice()=0.0001595 ETH` (indicative **$0.38836/BALANCE**, ~**$20.87m FDV** at $2,434.88/ETH). Both current limits are VERY close (0.31% and 0.82% above spot). `isGraduated()=false`. `endBlock=claimBlock=26241565`, estimated ~2026-10-21 21:22 Bangkok subject to block time. Contract `currencyRaised()` on nearby block ~1.3656563053 ETH is **settled raised**, not all escrowed 148 ETH.
- CCA uniform-price-per-block, monotonically rising clearing price. A bid only buys where clearing price is at or below limit; after later price exceeds limit it is **outbid** and ceases incremental buying. Locked ETH spends incrementally. `bids().tokensFilled=0` prior to exit is **NOT** proof zero economic token allocation; official UI has preliminary per-block allocations; need checkpoints or exit settlement to prove filled quantity. **No true cost basis, realized PnL or user BALANCE wallet quantity yet**.
- Official contract early exits: active in-range bid **cannot be canceled**; if **outbid and auction graduated**, `exitPartiallyFilledBid(bidId,lastFullyFilledCheckpointBlock,outbidBlock)` can refund unspent ETH before ending; if `isGraduated=false`, calls revert `CannotPartiallyExitBidBeforeGraduation`. After end, `exitBid` settles out-of-range/fully filled or failure; after `claimBlock`, tokens may be claimed only after successful auction and bid exit. **Auction failed at final => full bid refund (minus irreversible gas)**. Direct source: https://github.com/Uniswap/continuous-clearing-auction/blob/main/src/ContinuousClearingAuction.sol and https://developers.uniswap.org/docs/liquidity/liquidity-launchpad/guides/exit-bid .
- **Scenario only, assuming 0.4105 ETH fully deployed at uniform 0.0001595 ETH/BALANCE**: ~2573.67 tokens total; at $10m/$20m/$30m/$40m/$50m future FDV and fixed ETHUSD $2434.88, holdings would be ~$478.82/$957.64/$1436.47/$1915.29/$2394.11 respectively, compared with ~$999.52 initial. NOT a realized or likely final allocation; current max-price ceilings are narrow, price may pass them before much budget spends, leaving refundable ETH.
- **Important liability classification:** Personal ~$500 side and entrusted ~$500 side must have separate allocation and refunds even if their bids are in the same wallet. Contract owner is same wallet but economic ownership differs, so hold delegated bid proceeds as `ENTRUSTED_EXCLUDED`, not personal PnL.
- All original 22:40 discussion and `RESEARCH_ONLY / NO_BID_PLACED` lines below predate these user-originated transactions. No transaction executed by ChatGPT. No sell, liquidity action, claim or automation. Future balance/PnL updates need new chain reads and correct mapping of the beneficial parties.


## 1. Canonical verified identity and context

- Real project by public artist Jack Butcher, previous Checks, Opepen, Visualize Value. Official Credits and ratings: https://jack.art/credits and https://jack.art/credits/rating/ .
- Credits ERC721 Ethereum `0x97630aA70AB14ed9883B41dAfccBc11349723043`; 122,154 original $8 X Money Credit NFTs (about $977,232 initial gross sale, not financial statement). Official methodology rarity ratings 80–800. 80 Credits burned into one Statement NFT; Statement ratings sum. Max 1,526 original Statements before overprints.
- Statement ERC721 `0x75Edd94b7e49b3bD5C8047b91F165A5e265a069b`. Permanent Statement surrender/lock is proposed 1 rating point : 1 divisible Balance ERC20; qualifying wallet also gets soulbound visualization NFT. The original statement becomes non-tradable on surrender; NOT a guaranteed ROI.
- **BALANCE token** Ethereum `0x3620540c994433D7B4a628C46d2ED5F92572eA07`, ERC20 `decimals=18`; direct Ethereum `totalSupply()=53,750,000` at latest block ~26,234,753 (2026-10-20 around 22:40 Bangkok). This supply is **already minted at ERC20 level**, not merely future theoretical minting, while most units remain escrowed in token's own address. Live transferable float and unlock rights need independent audit.
- **Uniswap CCA auction** official page https://app.uniswap.org/explore/auctions/ethereum/0xa93807cd89a99bb564c7a887ab49cc4ecc3c9226 , actual verified auction contract `0xA93807cD89A99bB564C7A887ab49Cc4EcC3c9226`. Direct `token()` resolves BALANCE, `currency()` native ETH = zero address.
- Founder @jackbutcher *claims* to have bought back **1% of maximum token supply** on the open market and to keep no personal auction sale proceeds, committing auction funds to LP; source X text mirrored at https://www.sotwe.com/JackButcher?lang=id . **ISSUER_STATEMENT**, not independent audit of historical cost or beneficial ownership, and 100% LP allocation does not establish permanent LP lock.

## 2. DIRECT_CHAIN live auction snapshot

Snapshot about 2026-10-20 22:40 Asia/Bangkok, block **26,234,753** (not a frozen multi-call block guarantee):
- startBlock **26,234,365** (creation 2026-10-20T14:22:35Z per Blockscout), endBlock=claimBlock **26,241,565**. 7,200 block window ~24 hours, expected finish 2026-10-21 about **21:22 Bangkok**, actual time block-dependent. Claims also require settlement and exit mechanisms.
- Auction `totalSupply()=268,750 BALANCE` = exactly **0.5%** of 53,750,000 token supply. Auction currently holds all 268,750 tokens because allocated portions remain in contract until claimed; `remainingSupply()=262,141.81375`; settled/cleared allocation ~**6,608.18625**, **2.45886%** of the auction's offered supply.
- `clearingPrice()` raw Q96 converted **0.0001513 ETH/BALANCE** (Ethereum CCA); `floorPrice()` **0.00001 ETH/BALANCE**. Current direct Alchemy ETH/USD $2430.14 (2026-10-20T15:34:50Z), hence **$0.367680182/BALANCE**, full-supply mark **~$19,762,810 FDV**. This is **NOT** $19.76m of tradable float or organic value.
- `currencyRaised()=0.886540739427585836 ETH` (**already settled raising**), `getBalance(auction)≈128.084618744349 ETH` from independent contract indexer, most presumably unspent bidder deposits; do not call the 128 ETH revenue or fully attributed bids. Uniswap indexed UI page around time of research shows bid volume ~40.76762 ETH (~$99.1k) and clearing price 0.000151 ETH, but page loading error and lag mean **UI volume and direct contract balances do not reconcile**. Price happened to match. `nextBidId()=345` bid IDs, not unique wallets.
- `isGraduated()=false` at snapshot. `tokensRecipient()=0xc9951be537d6f9df431579cc493ac4e250e3b93e` (Uniswap liquidity owner), `fundsRecipient()=0x2eef0e2a9a652d755accad95a24541a98b5ca000`; identities/upgrade/control/LP hook and actual created v4 pool not comprehensively audited yet.
- **DIRECT_CHAIN supply location (latest ERC20 balanceOf)**:
  - BALANCE token's *own contract* `0x3620540c994433D7B4a628C46d2ED5F92572eA07`: **52,050,623.9513 BALANCE (~96.838%)** retained. Do not automatically label this minted amount immediately saleable or fully locked without audited transfer/escrow function semantics.
  - CCA auction contract: **268,750** (0.5%).
  - FundsRecipient above: **268,750** (0.5%), different contract from auction.
  - TokensRecipient above: **0** at snapshot.
  - Remaining **1,161,876.0487 (~2.162%)** in other accounts not yet fully attributed. These figures sum to 53.75m.
- Pool DEX executable depth, v4 token0/token1, fee tier, creator/founder real balances, post-auction pool ownership lock/withdrawal rights, ability to redeem Statements now and whether redemption credits supply can be transferred straight into pool **UNVERIFIED**. No current Uniswap v4 swap quote; do NOT invent available spot market or a locked pool.

## 3. CCA mechanics, timing, gas and refund

Official Uniswap docs:
- https://developers.uniswap.org/docs/liquidity/liquidity-launchpad/concepts/cca
- https://developers.uniswap.org/docs/liquidity/liquidity-launchpad/overview
- https://developers.uniswap.org/docs/liquidity/liquidity-launchpad/guides/exit-bid
- Bid consists of native **ETH** budget and **max ETH/token or Max FDV** ceiling. It must be **strictly greater than live clearing**. The max is a LIMIT not the user's guaranteed average realized price; CCA spreads eligible purchase across remaining auction blocks. If current clearing rises above a bidder max, further participation stops. Partially filled/outbid bid residual refunded after valid exit; after end/claimBlock a participant must follow exit + claim rules, rather than assuming immediate spend/automatic wallet receipt.
- Approx expected close October 21 21:22 Bangkok; actual chain block 26,241,565 controls. UI shows 100% "Committed to LP", not same as guaranteed LP initialization, immutability or ETH redeemability.
- The indexed CCA snapshot's "1.71% of supply sold" is **stale or different aggregation** from direct chain remaining supply 2.46%; chain authoritative.
- Transaction gas and claim gas in Ethereum must be budgeted. At 2026-10-20 ~22:40 direct `eth_gasPrice=0.602550172 gwei` (changes); use **$15 USD budget reserve** for planning, **NOT** a forecast of actual fees. Onchain wallet `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c` direct native ETH **0.000190807320080339 ETH (~$0.46)**, insufficient to place a $500 ETH bid. No current other-platform CEX balances independently read; Binance account historical screenshot amounts must not be treated as available ETH. User must personally fund native ETH (and check current gas), no ChatGPT transfer authorized.

## 4. Three routes and direct economic arbitrage warning

**Route A: CCA.** 268,750 auction tokens 0.5% of total. Early circulating valuation heavily sensitive to tiny float; current reference $19.76m FDV. A $500 total-budget investor may allocate e.g. **$485 bid + ~$15 gas/claim reserve**, giving ~**0.199576 ETH** bid at $2430.14. At present indicative price, if all $485 filled and no other fees, ~**1,319 BALANCE**. Actual fill is uncertain and max cap is not actual average execution price. If max FDV is **$12m**, max price ~$0.00009187ETH / ~$0.2233/token, which is **below current clearing 0.0001513** and CCA WILL REJECT A BID at this cap now.

**Route B: Credits/Statement:** Requires **80 qualifying Credits in same wallet** to form Statement; historical Mission user's original six Credits `#21646,#21753,#22857,#23042,#23232,#23328` are **all exited**, current known holding zero, documented `crypto-300-profit-mission/positions/credits.md` updated Oct10. No active credits at latest historical read. Third party Credits live index https://credits.ninja on Oct20 shows ordinary floor **~$47.67 per NFT**, 24h about **3,626 NFT sales / ~$212,616 volume**. Therefore **80 floor Credits would cost ~$3,814** at that snapshot, far exceeding $500 (before marketplace gas, marketplace fees, score variation). Mean score if 53.75m cap derives from 122154 Credits is **~440**; at $0.36768 each that averages **~$161.78** theoretical token equivalence per Credit (but cheap Credits may have much lower ratings, cannot buy all at floor, and actual conversion/vesting/gas unverified!). 80 Credits average ~35,200 BALANCE at $0.368 ~$12.9k, which is a **potential market cross-pricing anomaly** if redeemable and liquid, and implies *supply release selling pressure*, not a guaranteed free arbitrage.
- Verse primary seller-history evidence https://verse.works/items/ethereum/0x75edd94b7e49b3bd5c8047b91f165a5e265a069b/168: Statement #168 rating 27,814 sold **1.4 ETH ~$3,393** on **Oct 8** (historic, BEFORE auction), implying $0.122 per score vs auction $0.368; neither live statement ask nor executable token redemption today.
- Credits can retain art/rarity collecting demand independent of their BALANCE redemption optionality. Burn/surrender permanently destroys/transfers art liquidity to a different form. If arbitrage seems too large, **first verify locking/redeeming smart-contract rights and actual tradeable exit**.

**Route C: Wait post-auction spot market** and acquire only with live two-sided v4 reserves and $100/$500 exact-in quotes. Can have better or worse price than auction, no guarantee the platform will start exactly when endBlock arrives. Avoid chasing first one-minute candle.

**Scenario FDVs and theoretical $485 token notional quantities** (at each assumed entry FDV, using fixed supply 53.75m and no fee):
$8m -> price $0.14884, ~3258.6 units;
$10m -> $0.18605, ~2606.9;
$12m -> $0.22326, ~2172.4;
$15m -> $0.27907, ~1737.9;
$19.7628m -> $0.36768, ~1319.1;
$20m -> $0.37209, ~1303.4;
$22m -> $0.40930, ~1184.9;
$25m -> $0.46512, ~1042.75;
$40m -> $0.74419, ~651.7 (at $485 *new* cost basis).
If **purchase at $19.7628m FDV** for $485 and later sell ALL same units at FDV $10m/$15m/$20m/$30m/$40m/$50m, theoretical **$245 / $368 / $491 / $736 / $982 / $1,227** before fees; *cash reserve adds ~$15 separately and realized fill may differ*.
- **Risk judgment**: $19.76m FDV vs ~$0.98m X Money primary issuance gross and independent ~$47.67 Credit floor implies major narrative/cross-market premium. These are different claims/rights and no mechanistic one-to-one floor fair-value, but **do not assume undervalued**. Tradable spot float/LP likely limited, pending conversion overhang significant.

## 5. Mission-style project review

- Creator: real-world public conceptual artist Jack Butcher with Checks and Opepen history. Creator identity/reputation **verified from artist official bio** https://jack.art/ ; no need to invent a new VC team.
- Product stage: **Level 3 mainnet** (live ERC721 credits/statements, live Ethereum auction and Balances NFT examples, https://verse.works/series/balances-by-jack-butcher indicates initial 8 ERC721 artworks around October 20). NFT secondary activity is material but there is no independently validated ongoing business profit, paid enterprise adoption or holder cash-flow right, hence no Level 5.
- Financing: original $8 payment X Money credits = paid NFT mint; no verified SAFT seed investor, equity round or institutional entry. Uniswap is launch venue, **NOT a balance token investor**.
- Value capture: token transferable ownership of a conceptual artwork record, non-transferable ERC721 artwork per wallet, fee generation from LP to liquidity owner **not necessarily token holders**, no official yield, mandatory buyback, shareholder income or audited revenue.
- Risk: (1) early float vs theoretical 53.75m FDV mismatch; (2) 96.84% ERC20 balance held in program self custody, redeem/unlock mechanics not fully audited, creator/LP controls; (3) secondary-credit implied value premium vs auction, possible NFT-to-token conversion sell pressure; (4) initial LP not established, price impact and liquidation slippage unknown; (5) creator NFT art value depends on cultural demand; (6) CCA partial fill or refund delays, native ETH mainnet gas; (7) ETH denominated auction shifts USD cost if ETH moves; (8) no reliably matched independent Polymarket prediction contract for this art token; **NO VERIFIED PM PROBABILITIES**, don't invent.
- Source quality: project docs = artist issuer claims; hard numbers above from direct RPC; Verse completed historical trade = third party marketplace ledger; floor/sales = independent indexer, rates refresh.
- No platform token governance claim, CEX listings, options/futures, treasury ROI, investor unlock schedule or revenue-sharing evidence verified. Specific owner/proxy/mint/pause and LP withdrawal code audit pending; don't assert 'safe' or 'immutable'.

## 6. Decision: all-in $500 hypothetical, NO EXECUTION

**Recommended pricing discipline:** `WATCH / NO_GO at current ~$19.8m auction FDV for unconditional all-in`. Price sensitivity from NFT redemptions too high; user wants $500 total exposure but do not execute full size just because auction is live. If insisting on *immediate* CCA full exposure, only as illustrative setup: ~$485 max native ETH budget, ~$15 funding/gas/claim buffer, **set max FDV risk cap independently** and recognize cap must exceed current ~19.76m; a $22m cap yields max price ~$0.40930 / 0.00016843 ETH and at that worst cap 1184.94 BALANCE for $485 if fully filled. This is NOT recommended until full contract/pool rights audited and bid volume/executable float revisited. If max acceptable valuation is $10m–$12m, **cannot bid now**, wait for verifiable spot liquidity and conditional market price <= intended cap. No DEX order, no signing, no user transfers, no monitor added; user's production trading defaults NO_GO.
- For actual interactive confirmation only after user specifically chooses an on-chain action, verify current native wallet ETH, auction latest block/endBlock, current floor + clearing and max FDV, recipient address, simulation and gas, and max spend including fees. Never write projected holdings to portfolio.

## Sources

- https://app.uniswap.org/explore/auctions/ethereum/0xa93807cd89a99bb564c7a887ab49cc4ecc3c9226
- https://jack.art/credits
- https://jack.art/credits/rating/
- https://jack.art/
- https://developers.uniswap.org/docs/liquidity/liquidity-launchpad/overview
- https://developers.uniswap.org/docs/liquidity/liquidity-launchpad/guides/exit-bid
- https://verse.works/series/balances-by-jack-butcher
- https://verse.works/items/ethereum/0x75edd94b7e49b3bd5c8047b91f165a5e265a069b/168
- https://credits.ninja/
