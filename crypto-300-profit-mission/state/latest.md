# Crypto Mission Latest State

Updated: 2026-10-08 Asia/Bangkok
Timezone: Asia/Bangkok
Canonical scope: `../STATUS_SCOPE_2026-10-04.md`

## Current operational posture

- Frank local deterministic signal system: **LIVE** on the existing production build.
- Frank ACCUMULATION local notification: **LIVE**.
- Frank MULTIPLE local notification + standalone Gmail: **LIVE**.
- New Mission Meme follow-decision / Jupiter work remains **REVIEW_ONLY** until separately promoted.
- GPT Frank/Meme signal authority: **REMOVED**.
- `$300-3000` umbrella GPT task: **PAUSED**.
- NFT opportunity radar: **SPEC_PRESENT / RUNTIME_PAUSED**.
- MONSTER / 妖币: **RESEARCH_FROZEN / VALIDATION_NOT_PASSED**.
- CORE PRICE / overall-market trend module: **PAUSED**.
- Other tracked persons / TOKEN_CONSENSUS: **DEFERRED**.
- Production trading: **NO_GO**.

## Current capital policy

- Ignore individual assets worth **< $1** in displayed holdings.
- Binance USDC is investment capital parked in Earn; keep parked unless a materially better opportunity is identified and explicitly approved.
- Bybit USDC is personal cash for living expenses and next month's rent; it is excluded from investment capital.
- Sui chain assets are **0** by latest user confirmation.


## Fresh direct-chain holdings

Primary wallet identities:
- EVM: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Solana: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- Sui: `0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`

Alchemy native/SPL direct reads 2026-10-08 approximately 14:13-14:15 Asia/Bangkok:
- Solana USDC: **31.094071** (finalized slot 454474225; ~$31.11).
- Solana native SOL: **0.038163041** (finalized slot 454474225; ~$4.41).
- Ethereum native ETH: **0.000904693862403571** (~$2.32).
- Ink native ETH: **0.010133156790964273** (~$26.04).

Reference USD marks: ETH $2,569.76; SOL $115.43; USDC $1.00049 (same refresh; not trade prices).

Other EVM network native assets queried (Base, Unichain, Arbitrum, Optimism, Linea, World Chain, BNB, Polygon, Monad, HyperEVM, MegaETH) are individually below $1. Solana classic-token accounts have only canonical USDC as a nonzero token; four Token-2022 one-unit accounts lack verifiable liquid pricing, some are nontransferable. INK points/other unpriced or spam-like receipts are excluded.

The broad EVM multi-chain token-balance interface returned an HTTP 500; several token listings are incomplete/truncated. Hence **other token completeness = UNRESOLVED**. Do not promote unknown tokens into NAV or infer their balances are zero.

Sui: previously user-confirmed 0; **not directly refreshed today**, remains USER_CONFIRMED.

Full per-chain and uncertainty detail is in `portfolio/current.md`.


## CEX / off-chain state

### Binance — USER_CONFIRMED / PARKED INVESTMENT CAPITAL

- Latest screenshot 2026-10-08 approximately 14:10 Bangkok: **631.20 USDT-equivalent estimated total assets**.
- This is an exchange displayed **total valuation**, not proven 631.20 USDC holdings.
- Coin/product breakdown, earn APR and immediately available amount: **not freshly confirmed**.
- Investment reserve; no trading authorization. Approximate portfolio reference: **$631.20**.

### Bybit — USER_CONFIRMED / PERSONAL CASH EXCLUDED

- Latest screenshot 2026-10-08 approximately 14:11 Bangkok: **435.948711 USDC**.
- Displayed account total **$436.16**, USD-equivalent USDC row **$436.12**, available $0.13, in-use $436.03.
- Entire account is reserved for **living expenses and next month's rent**; always exclude from Mission investment NAV and any "$300 to $3000" numerator.
- Dust IMU shown at $0.00 does not change this exclusion.

`BYBIT = EXCLUDED_FROM_INVESTMENT_CAPITAL`

## Legion / JUMP — CLOSED / REFUND COMPLETE

Application outcome:
- **UNSUCCESSFUL / REJECTED**
- final JUMP allocation: **0**
- accepted investment: **0 USDC**

Original 1,000 USDC deposit has been refunded on Ethereum.

Refund transaction:
`0x3d3264417775aa9cf0bf5d83f69f00b2ada9e01852784bc52897264025c5e0b5`

Confirmed ERC-20 transfer:
- sale contract -> participating wallet
- **1,000 USDC**
- timestamp: `2026-10-06T17:28:23Z`

Latest direct contract-state read after refund:
- `investedCapital = 0`
- `hasRefunded = true`
- `hasSettled = false`
- `hasClaimedExcess = false`
- vesting address = zero

Therefore:
- remove the old **$1,000 pending JUMP** bucket;
- do not carry any JUMP token position;
- do not separately add the returned 1,000 USDC on top of current wallet/CEX balances.

Canonical incident/closure evidence:
- `../positions/jump.md`
- `../../research/projects/jump/jump-reclaim-2026-10-07.md`


## Current marked capital reference

Verified material on-chain priced assets (only positions >= $1):
- Solana USDC: ~$31.11
- Solana SOL: ~$4.41
- Ethereum ETH: ~$2.32
- Ink ETH: ~$26.04

**On-chain subtotal: ~ $63.88.**

Binance investment reserve, screenshot UI estimate: **$631.20**.

**Combined known investable/marked reference: ~ $695.08**, excluding Bybit, GANG escrow, assets under $1, unpriced/spam/unsupported tokens, NFTs and illiquid pre-TGE/private rights. Binance availability is not independently verified. This is **not Mission PnL**.

The **500 USDC GANG / The Syndicate Backable on-chain escrow** is already deducted from Solana USDC and is kept separately as `COMMITTED_ONCHAIN / ALLOCATION_PENDING`; receipt and chain evidence are in `../positions/gang.md`. No final GANG allocation or claimable/refundable outcome has been proven for this refresh. The sum $695.08 + $500 = **$1,195.08** is *historical committed capital plus liquid/marked capital reference only*, not an immediately realizable NAV.

**Excluded personal cash:** Bybit UI account total ~$436.16, including 435.948711 USDC reserved for living expenses / next month's rent.

No fresh transactions or yields were inferred from changes in account balances.

## Closed / excluded current holdings

- JUMP public-sale application: rejected / zero allocation / deposit refunded
- Credits: 0
- UNICRED #230: not owned
- SUI: 0
- PONS futures/spot: closed
- XRP / Variational: closed
- prior meme sleeves with zero verified current balances: historical only
- all individual positions below $1: omitted from displayed holdings

## Frank / Mission Meme development state

- Production Frank core remains on the existing frozen/live authority.
- Review-only Mission Control / Jupiter / replay work is maintained separately and must not silently replace production.
- Latest reviewed development branch has diverged substantially from main; integration must preserve newer main state and carry over only reviewed module changes.
- Production trading remains **NO_GO**.

## Refresh policy

Routine scheduled wallet polling remains disabled.

Refresh current holdings only on explicit user request, after a material user-reported action, or when a verified event requires an ownership/balance check.