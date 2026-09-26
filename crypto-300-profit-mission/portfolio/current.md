# Current Portfolio / Capital Map

Updated: 2026-09-27 03:40 Asia/Bangkok
Timezone: Asia/Bangkok

## Accounting policy

- DIRECT_CHAIN = fresh connected chain / explorer data.
- USER_CONFIRMED = latest user-confirmed private venue state.
- MARKET_ESTIMATE = fresh public mark applied to a verified quantity.
- UNRESOLVED = exclude from strict NAV until identity / execution value is verified.
- Internal bridge / venue transfers are not PnL.

## Current structure

User confirms that, apart from:
1. the Binance PONS perpetual position; and
2. one combined **598 USD-equivalent earn bucket**,

the remaining tracked capital is now on-chain.

The prior separate 500 + 98 earn labels are consolidated into one **598 USD-equivalent off-chain earn bucket** for accounting.

## DIRECT_CHAIN snapshot

### Ethereum
- USDC: **400.308121**
- native ETH: **0.001667063838788351**
- native mark at ETH ~2683.81: **~4.47 USD**

### Solana
Fresh finalized RPC:
- USDC: **328.018516**
- native SOL: **0.128587689**
- PAID: **947.685473**
- e/acc: **0**
- KARDASHEV: **0**
- unidentified legacy SPL mint `2MU93nLHhDsHzgEYBKbVbwLDd2pi71ubGp8SkEv9dZwQ`: **1.745552**, UNRESOLVED
- additional 1-unit / non-transferable Token-2022 receipts remain excluded from NAV unless independently identified

At SOL ~121.45:
- native SOL mark: **~15.62 USD**

The former e/acc and KARDASHEV positions are fully exited on-chain.

### BNB Chain
- canonical USDC: **0**
- GSTOCK: **1183.5967247073113**
- native BNB: **0.007916720924652341**
- GSTOCK reference: **~0.02446444 USD**
- GSTOCK mark: **~28.96 USD**
- BNB gas mark at ~770.39: **~6.10 USD**

### Robinhood Chain
- PONS: **54.799953441979624353**
- native ETH: **0.000825190918816326**
- PONS reference: **~0.63625280 USD**
- PONS spot mark: **~34.87 USD**
- native ETH mark: **~2.21 USD**

### Ink
Fresh explorer state:
- native ETH: **0.01113370814547789**
- Tydro Ink Points: **7.665136656205785948**
- Fresh INK commemorative NFT #372: **owned**
- separately discussed target Ink NFT: no new confirmed mint in this snapshot
- native ETH mark: **~29.88 USD**

### Base
- canonical USDC: **0.252982**
- native ETH: **0.000790846510479134**
- native ETH mark: **~2.12 USD**

### Unichain
- canonical USDC: **0.021286**
- native ETH: **0.000231941590232335**
- UNICRED NFT #230: tracked operationally
- native ETH mark: **~0.62 USD**

### Arbitrum
Fresh Blockscout:
- native ETH: **0.000825005012848238**
- canonical USDC: **0.000001**
- native ETH mark: **~2.21 USD**
- spoof / non-canonical tokens named USDC remain excluded
- pRCADE and other unpriced receipts remain excluded from NAV

## Canonical stablecoins

Current on-chain canonical stablecoins:
- Ethereum: 400.308121
- Solana: 328.018516
- Base: 0.252982
- Unichain: 0.021286
- Arbitrum: 0.000001
- BNB Chain: 0

**Total canonical on-chain stablecoins: 728.600906 USDC.**

## Other directly priced on-chain assets

Using current connected references:
- native gas assets across tracked chains: **~63.24 USD**
- GSTOCK: **~28.96 USD**
- Robinhood PONS spot: **~34.87 USD**

PAID, Tydro Points, NFTs and unidentified/spam receipts are excluded from strict priced NAV here.

## Off-chain tracked capital

### Binance PONSUSDT perpetual
Latest USER_CONFIRMED position remains:
- LONG **64 PONS**
- entry **0.6250**
- isolated 3x
- TP 0.668 / 0.704 / 0.739
- hard stop 0.498

Current public Binance mark: **~0.63688970**.
If the private position is unchanged:
- estimated current unrealized PnL: **~+0.76 USDT**
- exact private margin/funding/realized state remains USER_CONFIRMED until refreshed.

### Combined earn bucket
USER_CONFIRMED:
- **598 USD-equivalent total**
- treat the former 500 + 98 labels as one combined off-chain earn bucket
- do not split them in portfolio accounting unless the user later requests it

## Closed / retired exposures

- XRP / Variational: CLOSED, stop/lower bound hit.
- e/acc: 0 on-chain.
- KARDASHEV: 0 on-chain.
- SHART: 0.
- CRED liquid: 0.

## Summary

Current tracked capital model:
- on-chain assets = primary live portfolio;
- Binance PONS perpetual = only tracked off-chain active derivative;
- 598 USD-equivalent = one combined off-chain earn bucket;
- no active Variational XRP exposure.
