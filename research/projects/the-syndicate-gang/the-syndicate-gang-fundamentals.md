# The Syndicate / GANG — fundamentals, token economics, and Backable sale mechanics

Updated: 2026-10-09 Asia/Bangkok
Scope: Solana live web/Telegram game; Backable/MetaDAO v0.7 governance/ownership-token public sale.
Research status: `PRODUCT_PUBLIC_BETA / ONCHAIN_SALE_LIVE / FINAL_ALLOCATION_PENDING`
User participation operational authority (do not duplicate balance here): `crypto-300-profit-mission/positions/gang.md`.
Canonical portfolio reference: `crypto-300-profit-mission/portfolio/current.md`.
No trading or automatic monitoring authorized; `PRODUCTION_TRADING=NO_GO`.

## Identity and primary evidence

- Game: https://thesyndicate.games/ ; user docs: https://docs.thesyndicate.games/ ; legal terms: https://thesyndicate.games/terms ; legal operator named there: **Trium Labs, Inc.**
- Project token: `GANG` (not in-game `$RACKET`).
- Backable sale: https://backable.biz/raises/EFUKEM6oaUMdCtVvgaqeV2E9baZ1ikkLng1kTakvjU7k
- Solana launch PDA: `EFUKEM6oaUMdCtVvgaqeV2E9baZ1ikkLng1kTakvjU7k`
- Solana launch v0.7 program: `moontUzsdepotRGe5xsfip7vLPTJnVuafqdUWexVnPM`
- Canonical mint per previous on-chain Mission audit: `syQqkspvb2PRr1meJ5pJDmhgxwc4hUou2TMjjrTmeta`
- Protocol Rust source: https://github.com/metaDAOproject/programs/tree/develop/programs/v07_launchpad/src/state
- Backable primary-source mechanics:
  - https://www.backable.biz/docs/committed-vs-raised
  - https://www.backable.biz/docs/whats-new
  - https://www.backable.biz/docs/reading-a-deal-sheet
  - https://www.backable.biz/docs/monthly-budgets-and-proposals
  - https://www.backable.biz/docs/doing-your-own-research

## Product reality

- https://thesyndicate.games/ actually publishes an open public beta for web/Telegram (account created by email without separate wallet setup), with capos, packs, territory map, quests/hustles, weekly seasons, optional paid extras and real USDC game prizes.
- The official game documents describe the internal `$RACKET` as gameplay currency. Terms explicitly assign no monetary value to in-game currency: do **not** confuse with investable Solana **GANG** ownership/governance token.
- Legal ToS says operator `Trium Labs, Inc.` and public beta, including gameplay/parameter-change discretion. Existence of an interactive production product is confirmed; depth of organic customers, app-store releases and independently auditable commercial activity are not.
- Founder **Tim** discusses career connections with Tensor, Vector, Kamino and Backpack and product history in 2026-10-05 Ownership Podcast, hosted on Solana's media portal: https://solana.com/ru/podcasts/ownership . Attribution as team/founder claim, independent employment references pending.
- Founder-reported 2026-10-05 numbers: **~$265,000 lifetime revenue, 850+ DAU, 25% 30-day retention, four-month beta**. These are **ISSUER CLAIMS / NOT independently independently audited**; no direct Stripe receipts, backend cohort ledger, audited financial statements, gross-to-net reconciliation, or sustainable unit economics obtained. Never treat them as direct verifiable chain revenue.

## Verifiable sale / user capital status as at 2026-10-09 snapshot

The original Mission already stores user-specific chain-verified investment; this research note confirms it and records material changes, not a new position.

Direct finalized Alchemy Solana account read, decoded with fields from official v0.7 Rust `Launch` and `FundingRecord`:
- snapshot around finalized slot `454860355` (2026-10-09 Bangkok afternoon/evening; do not imply current forever);
- `Launch.state=Live`;
- `minimum_raise_amount=250,000 USDC`;
- `total_committed_amount=492,409.03 USDC`;
- `total_approved_amount=0` (the sale has **not been settled**);
- `monthly_spending_limit_amount=41,666 USDC`;
- `unix_timestamp_started=1791394201`; `seconds_for_launch=345600`; scheduled expiry **2026-10-12 00:30:01 Bangkok**, not guaranteed exact claim time;
- `performance_package_token_amount=12,900,000 GANG`, `months_until_insiders_can_unlock=18`;
- `additional_tokens_amount=1,357,894 GANG`; investigate recipient constraints;
- `is_performance_package_initialized=false`.
- FundingRecord PDA `GgFwSstgG9e6XDEWAc4wrcD8EqVaqHpzo7ScvNGEEQot`: `committed_amount=500 USDC`, `approved_amount=0`, `is_tokens_claimed=false`, `is_usdc_refunded=false`.
- User funding original Solana finalized signature: `LLxbLZNJYKcWGchRt7QNwnx8UKs4gzu5rYC2CFbRWzm9FzjrCjFHaMbKeebKHZAc8gkcympJTqioHGp2f7ifYia`.

**Committed is escrow, not funded company revenue.** `minimum_raise_amount=250K` is a floor; it does not encode a hard maximum 1M. Some launch references advertise $1M fundraising maximum; the hard on-chain enforcement/approval policy must be checked when settlement occurs. Backable primary docs say overflow commitments are refundable and qualified shares follow time-weighting, early-fill and ownership-score adjustment (with Aligned Parties excluded before scoring). No individual token quantity can be inferred simply from `500 / 492409.03`.

### Nominal launch valuation scenarios, not actual fills

Previously validated mint/sale token structure:
- total token mint about **27,157,894 GANG**;
- allocation pool **10,000,000 GANG** to approved participants;
- **2,900,000 GANG** reserved for initial liquidity;
- **12,900,000 GANG** locked performance package (18-month parameter);
- **1,357,894 GANG** additional designated recipient allocation.

If final **approved** raise = $250K, participant's nominal token price $0.025 and FDV about $678,947; if final **approved** raise = $1M, nominal price $0.10 and FDV about $2,715,789. Both are **conditional math, not a quoted actual allocation/exit price**. Circulating market cap and ability to sell depend on LP, claims, locked/nonlocked other allotments and actual price impact. Do not use commitments instead of approved amount in this calculation.

## Basic business-risk assessment

- Product/user traction: genuine working gameplay and payment pathways at Level 3 product existence, **claimed** Level 4/5 business metrics (no audited repeatable revenue).
- Team credibility: identifiable operator and named founder, historic employers unverified, no material VC investment inferred from using a launchpad.
- Financial risk: Backable says 80% of approved amount to project treasury and 20% to initial LP. At 250K approved, initial treasury would be 200K; at $1M, 800K (scenario only). Actual spend, founder withdrawals, prize pool operating costs, and real monthly unit economics are unresolved. A founder's budget allowance `41,666 USDC/month` is **withdrawal ceiling**, not proof money is spent every month.
- Distribution/valuation: founder team performance package sizable; 18 months is significant but must inspect precise on-chain unlock mechanics; separate 1.36M designated recipient and LP control can matter sooner.
- Liquidity: no genuine trading/claim as of this snapshot; no verified order book/pool depth/executable $500 exit. Launch FDV cannot be translated into guaranteed gain.
- Backable explicitly describes raises as **permissionless and not vetted**; on-chain escrow and DAO mechanics do not prove founder business claims or token appreciation.
- Rights: Backable advertises an ownership/governance legal entity mechanism, but an SPL GANG holding should **not** be stated as direct equity ownership, dividends or redeemable $500 without inspecting the deal sheet, actual IP assignments and corporate documents.
- Risk grade: `HIGH` with genuine product and sale evidence; `ACTIVE_PENDING_ALLOCATION` for the user's position, no extra capital approval. Re-evaluate after close with actual approved allocation, refunds, LP formation, pricing, liquidity and ongoing team execution.

## Next manual actions

- At/after scheduled close, validate LaunchState, approved amounts, final allocation and refundable balance from original FundingRecord. Trigger claim/refund manually only with explicit transaction approval; never assume closing-time automatic claim.
- Check funded treasury/LP, locked founder allocation, additional recipient account, connected mint/freeze authorities and real 5%/10% price impacts.
- Obtain independently reproducible payments/active user time series, preferably transaction/payments processor verifiable reports, DAU retention definition and sustainable gross margin; assess token rights to value capture.
- Continue separation between research and operational user capital; no changes to live signals, alarms or runtime.
