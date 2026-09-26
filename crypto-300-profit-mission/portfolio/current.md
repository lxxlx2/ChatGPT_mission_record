# Current Portfolio / Capital Map

Updated: 2026-09-26 14:12 Asia/Bangkok
Timezone: Asia/Bangkok

## Verification policy

CURRENT STATE only. Historical snapshots remain in Git history/run audits.

Labels:
- DIRECT_CHAIN: fresh connected chain data
- USER_CONFIRMED: latest private venue/order UI or explicit user statement
- MARKET: fresh public market reference
- UNRESOLVED: do not estimate

## Canonical wallets

- EVM primary: `0x3df4ebe3e5bd012f459cd3392c90a2d8b576ea7c`
- Solana primary: `BP7hHLZAGqZF1gRMEFh3kzZkrbGbTfKQo6Q5c6Lu4dSp`

## DIRECT_CHAIN snapshot

### Ethereum
- USDC: **400.308121**
- native ETH: **0.001667063838788351**

### Solana
Fresh finalized RPC:
- USDC: **248.657361**
- native SOL: **0.133415487**
- SHART: **0**
- unidentified SPL mint `2MU93nLHhDsHzgEYBKbVbwLDd2pi71ubGp8SkEv9dZwQ`: **1.745552**, identity/value UNRESOLVED

Relative to the prior 330.799585-USDC snapshot:
- USDC delta: **-82.142224**
- SOL delta: **-0.002129677**

User confirms the lower Solana USDC is from cross-chain capital movements used to adjust positions. Exact per-bridge allocation is not inferred unless transaction legs are fully reconciled.

### BNB Chain
Fresh Alchemy:
- canonical USDC: **30.00474761**
- native BNB: **0.002684170274192202** (~**2.08 USD** at BNB 773.31)
- canonical GSTOCK: **0**
- GSTOCK market reference: **~0.024487 USD**

The USDC/BNB is associated with the user's GSTOCK pending-order plan. No chain fill is visible yet.

### Robinhood Chain
Fresh Alchemy + Blockscout:
- native ETH: **0.000825190918816326**
- PONS: **54.799953441979625**
- PONS market reference: **~0.642-0.643 USD**

Other ERC-20 receipts currently present but excluded from NAV because no reliable exchange rate / intentional-position verification is available:
- Jollybot (JOLLY): **256.593895779031580672**
- HYPERCAT: **167.675752122821869568**
- familiars: **1833.405043146758291456**
- Robinhood Monkey Business (RMB): **500,000**
- 富贵: **6,500**
- DIH: **1**
- DGDY: **1**

Blockscout currently reports no exchange rate for those non-PONS balances. Treat them as unpriced/unsolicited until independently verified as intentional positions.

### Ink
Fresh Blockscout state:
- native ETH: **0.01113370814547789** (~**29.93 USD** at ETH 2688.52)
- Tydro Ink Points: **7.665136656205785948**
- existing NFT: **Fresh INK - OpenSea x Ink Commemorative NFT #372**

The newly discussed target Ink NFT is still pending; no new target NFT is recorded as minted.

### Base
- canonical USDC: **0.252982**
- native ETH: **0.000790846510479134**

### Unichain
- canonical USDC: **0.021286**
- native ETH: **0.000231941590232335**
- CRED: **0**

### Arbitrum
Current Alchemy app support remains unavailable for direct wallet RPC. Do not infer current balance.

## Canonical direct-chain stablecoins

Ethereum + Solana + BNB Chain + Base + Unichain:
**679.24449761 USDC**

This is current wallet accounting, not PnL.

## Private / order-state exposures

### XRP / Variational
Latest USER_CONFIRMED:
- LONG 77.12 XRP @ 1.55589
- isolated 3x
- TP 1.6280
- SL 1.5140

### PONS
Authority: `positions/pons.md`.
- Binance futures state remains USER_CONFIRMED from the latest screenshots.
- Robinhood spot balance is DIRECT_CHAIN.
- spot/futures TP/SL order state follows the position file.

### GSTOCK
Authority: `positions/gstock-plan.md`.
- BNB Chain reserve: about 30 USDC + BNB gas
- chain GSTOCK balance: 0
- current state: PLAN_NOT_FILLED

## Other Mission positions

- JUMP reserve: 400 USDC on Ethereum.
- ETH conditional reserve: 100 USDC.
- short-window opportunity reserve: 150 USDC, now distributed across chains/plans rather than assumed to remain wholly on Solana.
- low-risk 500 USD-equivalent interest bucket remains outside the speculative Mission.
- UNICRED NFT #230 remains active/locked.
- Credits #23042 / #23232 remain user-confirmed listings.

## Residual accounting

Using canonical direct-chain stablecoins **679.24449761 USDC**:
- 400 JUMP reserve
- 150 short-window opportunity reserve
- 100 ETH conditional reserve

Arithmetic residual: **29.24449761 USDC**.

This residual is accounting only. The cross-chain opportunity reserve now includes the BNB/GSTOCK plan and other converted assets, so wallet-token values must not be double-counted as free capital.
