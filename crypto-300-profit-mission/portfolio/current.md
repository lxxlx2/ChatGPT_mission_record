# Current Portfolio / Capital Map

Updated: 2026-09-26 13:00 Asia/Bangkok
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

Fresh RPC reconciliation through about 2026-09-26 13:00 Asia/Bangkok.

### Ethereum mainnet
- USDC: **400.308121**
- native ETH: **0.001667063838788351**

### Solana
- canonical USDC: **330.799585**
- native SOL: **0.135545164**
- SHART canonical mint: **0**
- unidentified SPL mint `2MU93nLHhDsHzgEYBKbVbwLDd2pi71ubGp8SkEv9dZwQ`: **1.745552 tokens**
  - identity/value: **UNRESOLVED**
  - excluded from Mission NAV until verified.

### Base
- canonical USDC: **0.252982**
- native ETH: **0.000790846510479134**

### Unichain
- canonical USDC: **0.021286**
- native ETH: **0.000231941590232335**
- CRED: **0**

### Robinhood Chain
- native ETH: **0.000826657957256326**
- canonical PONS contract: `0x39dbed3a2bd333467115de45665cc57f813c4571`
- PONS balance: **54.799953441979625**
- Alchemy PONS price: **0.6448796581 USD**
- PONS spot mark value: **~35.34 USD**
- ETH reference price: **2684.44 USD**
- native gas mark value: **~2.22 USD**
- unknown/spam ERC-20 balances remain excluded unless identity/value are verified.

### Arbitrum
- current connected Alchemy app does not support ARB_MAINNET.
- native ETH / USDC wallet balances: **UNAVAILABLE**.
- do not infer them from old bridge amounts or Variational UI.

### Canonical direct-chain stablecoins
- Ethereum + Solana + Base + Unichain: **731.381974 USDC**

Compared with the 09:18 snapshot, Solana canonical USDC decreased by **9.025416 USDC** and native SOL decreased by **0.004197159 SOL**. This file does not infer the cause from balance delta alone.

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

This is the latest confirmed private-venue state. Public XRP prices may monitor risk but must not rewrite this private state.

### PONS sleeve

Latest USER_CONFIRMED Binance futures state at 2026-09-26 12:58:
- LONG PONSUSDT, isolated 3x
- entry: **0.6250**
- position notional shown: **41.32 USDT**
- margin shown: **13.20 USDT**
- mark shown: **0.6451307**
- unrealized PnL shown: **+1.31 USDT**
- realized PnL shown: **-0.13 USDT**
- liquidation price shown: **0.4293629**
- hard stop: **0.4980**
- old 0.5850 / 0.5450 resting entries: **CANCELED**

DIRECT_CHAIN Robinhood Chain:
- PONS spot: **54.799953441979625 PONS** (~**35.34 USD** at the fresh Alchemy price)
- native gas: **0.000826657957256326 ETH** (~**2.22 USD** at the current ETH reference)

User confirms the released Binance order capital was withdrawn and converted into spot PONS + gas.
Exact spot cost basis and withdrawal/swap fees are UNRESOLVED.

### Low-risk bucket
- 500 USD-equivalent, user-confirmed as earning interest.
- excluded from speculative Mission capital.

## Non-liquid / protocol positions

### UNICRED
- NFT #230 remains active.
- acquisition cost reference: 0.0105 ETH.
- staked / locked until 2026-10-01 17:28:04 Asia/Bangkok.
- liquid CRED wallet balance: 0 DIRECT_CHAIN.
- exact current claimable rent requires a fresh protocol read.

### Credits
Latest user-confirmed listing state:
- #23042 listed at 0.25 ETH.
- #23232 listed at 0.40 ETH.
Listing prices are not executable NAV.

## Current capital map

Based on **731.381974 USDC** canonical direct-chain stablecoins:
- 400 USDC: JUMP conditional reserve.
- 150 USDC: short-window opportunity reserve.
- 100 USDC: ETH conditional reserve.
- **81.381974 USDC**: direct-chain residual after those ring-fenced reservations.

Separately:
- PONS: original 50-USDT sleeve is now split between the remaining Binance futures position and Robinhood Chain spot PONS + gas; there are no live 0.5850/0.5450 averaging orders.
- XRP/Variational: private venue exposure funded by prior internal reallocation.
- 500 USD-equivalent low-risk bucket: outside speculative Mission.

The 81.381974 figure is available-capital accounting, not profit.

## Closed liquid exposures

- SHART: 0 DIRECT_CHAIN.
- CRED: 0 DIRECT_CHAIN.
