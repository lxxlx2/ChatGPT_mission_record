# Slop Cash / SLOP — Umia auction participation research

Updated: 2026-10-27 Asia/Bangkok (official auction price/cap, supply, Robinhood USDG, eligibility stages; exact calendar time/CA still unconfirmed)
Scope: ICO / pre-launch token auction / Robinhood Chain
State: `USER_INTENDS_TO_PARTICIPATE / WAIT_FOR_FINAL_AUCTION_TERMS / NO_FUNDS_COMMITTED`
Decision classification: `WATCH` (not SETUP or ACTIVE).
Execution: `NO_GO`; the user has expressed interest only, with no authorization for funding, wallet signature, live trading, scheduling or monitoring.

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
