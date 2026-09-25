# Crypto Mission Performance Tracker

Updated: 2026-09-25
Timezone: Asia/Bangkok

## Purpose

Track progress toward the Mission without confusing new deposits/transfers with trading profit.

Wallet balance alone is NOT P&L.

Authoritative performance formula:
- net contributions = external capital added to the Mission minus external capital withdrawn;
- realized P&L = closed-trade / sale / claim proceeds minus attributable cost basis and fees;
- unrealized P&L = current executable value of open positions minus remaining cost basis;
- Mission equity = net contributions + realized P&L + unrealized P&L.

When transaction history or cost basis is missing, mark the metric unresolved rather than inferring profit from current wallet balances.

## Current capital snapshot

Direct-chain canonical stablecoins:
- Ethereum: 400.308121 USDC.
- Solana: 390.866576 USDC.
- Base: 0.252982 USDC.
- Unichain: 0.021286 USDC.
- Total: ~791.448965 USDC.

Separate:
- PONS margin budget: 50 USDT.
- Low-risk interest bucket: 500 USD-equivalent, excluded from speculative Mission performance unless the user later decides to include its yield in the same scorecard.

## Open / reserved exposures

### PONS
- First entry only: 0.6250.
- Approx first-tranche notional: ~40 USDT.
- Remaining 0.5850 / 0.5450 orders are pending and do not count as deployed exposure.
- Current realized P&L: 0 unless a partial close occurs.
- Unrealized P&L must be calculated from fresh mark and exact filled quantity.

### JUMP
- 400 USDC reserved on Ethereum mainnet.
- No allocation yet.
- Current realized/unrealized P&L: 0.

### ETH
- 100 USDC reserved.
- No live Mission position.
- P&L: 0.

### UNICRED #230
- NFT cost basis: 0.0105 ETH.
- Still staked.
- Exact cumulative realized rent and current claimable rent require live reconciliation.
- Net economic P&L remains unresolved until cumulative rent + executable NFT value are refreshed.

### Credits
- #23042 listed 0.25 ETH.
- #23232 listed 0.40 ETH.
- Cost basis and executable bid/value are not fully reconciled in this file.
- Do not treat listing price as unrealized P&L.

## Closed exposure requiring reconciliation

### SHARTCOIN
- Current canonical wallet balance: 0.
- Exposure status: closed.
- Final realized P&L is unresolved until outgoing transaction history and swap proceeds are reconstructed.
- Do not infer the close price from the last balance or old screenshots.

### CRED
- Current direct Unichain balance: 0.
- Exposure status: closed.
- Prior notes indicate principal had been recovered, but final realized P&L requires transaction-history reconciliation before being treated as exact.

## Mission scorecard

At the current state, an exact total-return percentage is intentionally not published because:
1. the Mission received additional capital after the original $300 starting point;
2. SHART and CRED final realized proceeds have not yet been fully reconstructed;
3. UNICRED rent and Credits executable values are not fully reconciled.

Daily reconciliation should maintain two scorecards once history is available:
- Original-$300 sleeve performance.
- Total speculative capital performance after later contributions.

This prevents later deposits from being mistaken for profit.

## Update rules

Update this file on the daily full reconciliation and whenever:
- capital is added/withdrawn,
- a position opens/closes,
- a material partial take-profit occurs,
- an ICO/NFT allocation is confirmed,
- realized proceeds are reconstructed,
- an active position cost basis changes.

Every number must be labeled direct-chain, exchange/user-confirmed, market-derived, or unresolved.
