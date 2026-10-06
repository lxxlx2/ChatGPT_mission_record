# Crypto Mission Latest State

Updated: 2026-10-07 Asia/Bangkok
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

Canonical wallets:
- EVM: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Solana: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`
- Sui: `0xb07d535f1e8607d283c98cd4428f6c76a6101704aedec38da93486fb91a1c101`

Reference marks used only for this balance snapshot:
- ETH: **$2,692.98**
- SOL: **$87.00**
- USDC: **$0.999923**

### Solana — DIRECT_CHAIN / finalized

- USDC: **531.094071** (~$531.05)
- native SOL: **0.039406389** (~$3.43)

Other classic SPL balances returned zero. Token-2022 non-transferable/unpriced/spam-like receipts are not promoted into NAV.

### Ethereum — DIRECT_CHAIN

- native ETH: **0.000904693862403571** (~$2.44)
- canonical USDC: **0**

### Ink — DIRECT_CHAIN

- native ETH: **0.010133156790964273** (~$27.29)

Known Ink NFT inventory remains unpriced and excluded from the marked subtotal.

### Other chains — below $1 / excluded

Fresh native/token balances below the current materiality threshold include Base, Unichain, Arbitrum, Optimism, Linea, World Chain, Robinhood Chain and BNB Chain. MegaETH native balance is 0. No unpriced/spam receipt is promoted into NAV.

### Sui — USER_CONFIRMED

- **all Sui-chain assets = 0**

Do not carry forward any old SUI balance.

## CEX / off-chain state

### Binance — USER_CONFIRMED / PARKED INVESTMENT RESERVE

- **600.866553 USDC**
- screenshot shows Earn current APR **2.11%**
- auto-subscribe enabled
- execution rule: leave in Earn unless a materially better risk/reward opportunity is found and explicitly approved

Current reference mark: ~**$600.82**.

### Bybit — USER_CONFIRMED / PERSONAL CASH EXCLUDED FROM INVESTMENT

- count only the USDC line: **403.020679 USDC** (~$402.99)
- purpose: living expenses + next month's rent
- classification: **EXCLUDED_FROM_INVESTMENT_CAPITAL**

Do not use the Bybit account total-asset figure as Mission capital.

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

Material on-chain subtotal:
- Solana USDC: ~$531.05
- Solana SOL: ~$3.43
- Ethereum ETH: ~$2.44
- Ink ETH: ~$27.29

**On-chain material subtotal: ~ $564.21**

Investable parked CEX capital:
- Binance Earn: ~**$600.82**

**Current Mission-addressable / investable reference: ~ $1,165.03**

Excluded personal cash:
- Bybit USDC: ~**$402.99**, living expenses / rent

Also excluded from the above investable reference:
- sub-$1 dust;
- unpriced NFTs/tokens;
- private/pre-TGE/points rights without reliable liquid marks.

This is asset completeness, **not Mission PnL**.

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