# Crypto Mission Performance Tracker

Updated: 2026-09-26 09:18 Asia/Bangkok
Timezone: Asia/Bangkok

## Rules

Wallet balance alone is not P&L.

- external net contributions = capital added from outside the Mission minus capital withdrawn.
- realized P&L = verified closed proceeds minus verified cost basis and fees.
- unrealized P&L = executable current value of open positions minus remaining cost basis.
- internal chain / venue transfers do not create profit.
- when history or current private-venue state is unavailable, use UNRESOLVED instead of estimating.

## Current capital snapshot

DIRECT_CHAIN canonical stablecoins:
- Ethereum: 400.308121 USDC.
- Solana: 339.825001 USDC.
- Base: 0.252982 USDC.
- Unichain: 0.021286 USDC.
- Total: **740.407390 USDC**.

Other assets:
- Solana native: 0.139742323 SOL.
- Ethereum native: 0.001667063838788351 ETH.
- Base native: 0.000790846510479134 ETH.
- Unichain native: 0.000231941590232335 ETH.
- Robinhood Chain native: 0.000081643478484768.
- unidentified Solana SPL balance: 1.745552 tokens, value UNRESOLVED.

Separate:
- PONS margin budget: 50 USDT, private account.
- low-risk interest bucket: 500 USD-equivalent, excluded from speculative Mission performance.
- XRP/Variational private venue sleeve funded by internal reallocation; no external-contribution impact.

## Open / reserved exposure

### JUMP
- 400 USDC reserve on Ethereum.
- no allocation confirmed.
- realized P&L: 0.

### ETH
- 100 USDC reserve.
- no live Mission position confirmed.
- realized/unrealized P&L: 0.

### Opportunity reserve
- 150 USDC ring-fenced.
- not P&L.

### XRP / Variational
USER_CONFIRMED at 2026-09-26 06:08:
- OPEN / FILLED.
- 77.12 XRP long at 1.55589, isolated 3x.
- TP 1.6280; SL 1.5140.
- screenshot unrealized PnL: +0.97 USD at mark 1.56844.
- current public XRP mark can be monitored, but exact current private-venue PnL is UNRESOLVED without a fresh venue read.
- realized P&L: 0 until verified close/partial close.

### PONS
USER_CONFIRMED:
- first 0.6250 entry filled.
- deeper 0.5850 / 0.5450 orders pending.
- exact current private position quantity and account PnL: UNRESOLVED without account read.
- realized P&L: 0 unless a close is confirmed.

### UNICRED #230
- NFT cost basis: 0.0105 ETH.
- still staked.
- exact cumulative rent + current claimable + executable NFT value require live protocol/market reconciliation.
- current economic P&L: UNRESOLVED.

### Credits
- #23042 user-confirmed listing 0.25 ETH.
- #23232 user-confirmed listing 0.40 ETH.
- listing prices are excluded from NAV until executable value/cost basis are reconciled.

## Closed exposure requiring reconciliation

### SHART
- direct wallet balance: 0.
- status: closed.
- final realized P&L: UNRESOLVED until transaction history / proceeds are reconstructed.

### CRED
- direct Unichain balance: 0.
- status: closed liquid exposure.
- final realized P&L: UNRESOLVED until transaction history is reconciled.

## Capital residual

Current canonical direct-chain stablecoins 740.407390 minus:
- 400 JUMP reserve,
- 150 opportunity reserve,
- 100 ETH reserve,
leaves **90.407390 USDC** direct-chain residual.

This residual is available-capital accounting, not profit.

## Scorecards

Do not publish an exact total return yet because:
- the Mission received capital after the original $300 start;
- SHART/CRED realized proceeds remain unresolved;
- UNICRED rent/executable NFT value remain unresolved;
- current private venue PnL for XRP/PONS is not directly readable.

Maintain two eventual scorecards:
1. original-$300 sleeve;
2. total speculative capital after later contributions.
