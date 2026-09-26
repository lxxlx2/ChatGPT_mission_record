# Current Portfolio / Capital Map

Updated: 2026-09-26 09:18 Asia/Bangkok
Timezone: Asia/Bangkok

## Verification policy

This file is CURRENT STATE only. Historical snapshots stay in Git history and run audits.

Labels:
- DIRECT_CHAIN: fresh RPC result from connected Alchemy app `ChatGPT Crypto Monitor`.
- USER_CONFIRMED: latest user screenshot / explicit statement from a private venue that cannot currently be read directly.
- MARKET: current public market data.
- UNRESOLVED: identity, value, cost basis or private venue state is not independently readable.

Never replace a failed live read with an older value and call it current.

## Canonical wallets

- EVM primary: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Solana primary: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`

## DIRECT_CHAIN snapshot

Fresh RPC read around 2026-09-26 09:18 Asia/Bangkok.

### Ethereum mainnet
- USDC: **400.308121**
- native ETH: **0.001667063838788351**

### Solana
- canonical USDC: **339.825001**
- native SOL: **0.139742323**
- SHART canonical mint `UpBBfyC75u3kxDGWmmmW2yauk9YY3CqZhdt1KUDkids`: **0**
- unidentified SPL mint `2MU93nLHhDsHzgEYBKbVbwLDd2pi71ubGp8SkEv9dZwQ`: **1.745552 tokens**
  - identity/value: **UNRESOLVED**
  - do not include in Mission NAV until verified.
- previously identified auxiliary native-WSOL accounts: closed; no longer an active balance item.

### Base
- canonical USDC: **0.252982**
- native ETH: **0.000790846510479134**

### Unichain
- canonical USDC: **0.021286**
- native ETH: **0.000231941590232335**
- CRED: **0**

### Robinhood Chain
- native balance: **0.000081643478484768**
- unsolicited/unknown ERC-20 balances are excluded unless identity and value are verified.

### Arbitrum
- direct read attempted at 2026-09-26 09:36 Asia/Bangkok.
- current Alchemy app returned RPC 403 because ARB_MAINNET is not enabled.
- native ETH / USDC wallet balances: **UNAVAILABLE**.
- do not estimate from prior transfers or Variational UI.

### Canonical direct-chain stablecoins
- Total canonical USDC across Ethereum + Solana + Base + Unichain: **740.407390 USDC**

Previous authoritative total was 791.448965 USDC. Current direct-chain total is lower by **51.041575 USDC**. This file does not infer the cause from balance delta alone.

## USER_CONFIRMED private / off-chain exposure

### XRP / Variational Omni
Last user-confirmed screenshot: 2026-09-26 06:08 Asia/Bangkok.
- XRP-PERP LONG
- quantity: 77.12 XRP
- entry: 1.55589
- isolated 3x
- TP: 1.6280
- SL: 1.5140
- margin shown: about 40.99 USDC
- Omni equity shown: 50.87 USD
- available shown: 10.55 USD

This is the latest confirmed private-venue state, not a live wallet read. Public XRP prices may monitor risk but must not silently rewrite the private position.

### PONS / Binance
Latest user-confirmed execution state:
- total margin budget: 50 USDT
- only 0.6250 entry confirmed filled
- 0.5850 and 0.5450 remain pending resting orders
- isolated 3x
- hard stop: 0.4980 Mark Price

Private Binance account fill/position quantity is not directly connected here, so do not invent it from public market data.

### Low-risk bucket
- 500 USD-equivalent, user-confirmed as earning interest.
- Excluded from speculative Mission capital and cannot be reassigned automatically.

## Non-liquid / protocol positions

### UNICRED
- NFT #230 remains the active protocol position.
- acquisition cost reference: 0.0105 ETH.
- staked / locked until 2026-10-01 17:28:04 Asia/Bangkok.
- liquid CRED wallet balance: 0 DIRECT_CHAIN.
- exact current claimable rent requires a fresh protocol read; do not infer from old snapshots.

### Credits
Latest user-confirmed listing state:
- #23042 listed at 0.25 ETH.
- #23232 listed at 0.40 ETH.
These listing prices are not executable NAV and must not be counted as unrealized P&L without current bids/sales evidence.

## Current capital map

Based on **740.407390 USDC** canonical direct-chain stablecoins:
- 400 USDC: JUMP conditional reserve on Ethereum.
- 150 USDC: short-window opportunity reserve.
- 100 USDC: ETH conditional setup reserve.
- **90.407390 USDC**: direct-chain residual after those ring-fenced reservations.

Separately:
- PONS: 50-USDT margin budget.
- XRP/Variational: already funded from a prior internal Mission reallocation; private venue balance/position is tracked separately above.
- 500 USD-equivalent low-risk bucket: outside speculative Mission.

The 90.407390 figure is an accounting residual from current direct-chain canonical stablecoins. It must not be interpreted as profit.

## Closed liquid exposures

- SHART: 0 DIRECT_CHAIN, closed for exposure accounting.
- CRED: 0 DIRECT_CHAIN, closed as a liquid token exposure.
