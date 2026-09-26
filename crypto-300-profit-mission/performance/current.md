# Crypto Mission Performance Tracker

Updated: 2026-09-26 14:18 Asia/Bangkok
Timezone: Asia/Bangkok

## Accounting rules

Wallet balance alone is not P&L.

- internal bridge / chain / venue movements are not profit or loss;
- realized P&L requires verified proceeds, cost basis and fees;
- private venue values remain USER_CONFIRMED unless directly connected;
- unpriced / unsolicited tokens are excluded from NAV;
- listing / conditional-order values are not realized P&L.

## Current direct-chain capital

Fresh supported-chain reconciliation:

### Canonical stablecoins
- Ethereum USDC: **400.308121**
- Solana USDC: **248.657361**
- BNB Chain USDC: **30.00474761**
- Base USDC: **0.252982**
- Unichain USDC: **0.021286**

Total canonical direct-chain stablecoins: **679.24449761 USDC**.

### Native gas assets
- Ethereum: **0.001667063838788351 ETH**
- Solana: **0.133415487 SOL**
- BNB Chain: **0.002684170274192202 BNB**
- Robinhood Chain: **0.000825190918816326 ETH**
- Ink: **0.01113370814547789 ETH**
- Base: **0.000790846510479134 ETH**
- Unichain: **0.000231941590232335 ETH**

Arbitrum remains UNAVAILABLE in the current Alchemy app.

## Cross-chain capital change

Solana canonical USDC is now **248.657361**, down **82.142224 USDC** from the prior 330.799585 snapshot.

The user confirms this reduction came from cross-chain capital movements used to adjust positions. This is treated as an internal capital movement, not P&L.

BNB Chain now contains:
- **30.00474761 USDC**
- **0.002684170274192202 BNB**
- GSTOCK direct-chain balance: **0**

The BNB-chain funds are associated with the current GSTOCK pending-order plan. No direct-chain GSTOCK fill is visible.

## Open / reserved exposure

### JUMP
- 400 USDC reserve on Ethereum.
- allocation not confirmed.
- realized P&L: 0.

### ETH
- 100 USDC conditional reserve.
- no confirmed live Mission ETH position.

### Opportunity reserve
- 150 USDC accounting reserve.
- currently distributed across chains / plans rather than assumed to remain wholly on Solana.
- do not double-count converted assets as free USDC.

### GSTOCK
- status: **PLAN_NOT_FILLED**
- direct-chain GSTOCK: **0**
- BNB Chain reserve: about 30 USDC plus BNB gas
- order UI state is not verifiable from wallet RPC.

### XRP / Variational
Latest USER_CONFIRMED:
- 77.12 XRP long @ 1.55589
- isolated 3x
- TP 1.6280
- SL 1.5140

Exact current private-venue PnL remains UNRESOLVED without a new venue read/user screenshot.

### PONS futures
Latest USER_CONFIRMED at 2026-09-26 13:45:
- LONG 64 PONS, isolated 3x
- entry 0.6250
- TP reduce-only: 25 @ 0.668; 22 @ 0.704; 16 @ 0.739
- hard stop: Mark <= 0.4980, reduce-only 100%
- old 0.5850 / 0.5450 averaging bids canceled
- 1 PONS residual is not covered by the TP ladder, but remains covered by the 100% stop.

### PONS spot
DIRECT_CHAIN:
- **54.799953441979625 PONS**
- Blockscout market reference around **0.643077 USD**
- mark value roughly **35.24 USD**

Verified acquisition leg:
- 35.291194 USDG -> 54.799953441979625 PONS
- average acquisition rate ~0.64400044 USDG/PONS

USER_CONFIRMED orders:
- TP: 11 @ 0.668; 16.4 @ 0.704; 16.4 @ 0.739; 11 @ 0.845
- downside triggers: 27.39 @ 0.598 and 27.39 @ 0.575

After any spot TP fill, fixed downside-trigger quantities require manual REVIEW_REQUIRED / resize against the remaining wallet balance.

## Ink

DIRECT_CHAIN / Blockscout:
- native ETH: **0.01113370814547789**
- Tydro Ink Points: **7.665136656205785948**
- existing NFT: Fresh INK commemorative NFT #372

The newly discussed target Ink NFT is still pending. Existing Fresh INK #372 must not be confused with the target mint.

## Robinhood non-PONS receipts

Present but excluded from NAV pending intentional-position and market-value verification:
- JOLLY
- HYPERCAT
- familiars
- RMB
- 富贵
- DIH
- DGDY

## UNICRED / Credits

- UNICRED NFT #230 remains active / locked; economic P&L unresolved until current rent + executable NFT value are reconciled.
- Credits #23042 and #23232 listing prices remain excluded from NAV unless executable value is verified.

## Closed exposure

- SHART direct balance: 0
- liquid CRED direct balance: 0

Final realized P&L for historical closed sleeves remains UNRESOLVED until transaction-history cost/proceeds are fully reconciled.

## Residual accounting

679.24449761 canonical stablecoins minus:
- 400 JUMP reserve
- 150 opportunity reserve
- 100 ETH reserve

Arithmetic residual: **29.24449761 USDC**.

This is accounting residual, not profit. The opportunity reserve already includes cross-chain / converted position capital and must not be counted twice.

## Scorecards

Do not publish an exact total Mission return until:
- later capital contributions are separated from the original-$300 sleeve;
- closed SHART/CRED proceeds are reconciled;
- private venue XRP/PONS current PnL is refreshed;
- UNICRED / NFT executable values are current.
