# Slop Cash / SLOP — Umia auction participation research

Updated: 2026-10-09 Asia/Bangkok
Scope: ICO / pre-launch token auction / Robinhood Chain
State: `USER_INTENDS_TO_PARTICIPATE / WAIT_FOR_FINAL_AUCTION_TERMS / NO_FUNDS_COMMITTED`
Decision classification: `WATCH` (not SETUP or ACTIVE).
Execution: `NO_GO`; the user has expressed interest only, with no authorization for funding, wallet signature, live trading, scheduling or monitoring.

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
