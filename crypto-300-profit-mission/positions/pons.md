# PONS Position

Updated: 2026-09-27 12:46 Asia/Bangkok

## Active authority: Binance PONSUSDT perpetual — USER_CONFIRMED

Position:
- LONG **64 PONS**
- entry **0.6250**
- isolated **3x**
- hard stop **0.4980**
- take-profit triggers **0.668 / 0.704 / 0.739**

Fresh public Binance state:
- mark **0.61669610**
- funding **0.00011652**

If the private quantity is unchanged:
- estimated mark-to-entry uPnL **~-0.5314 USDT**
- exact private margin/funding/fees/order fills remain USER_CONFIRMED-only

Prior 0.5850 and 0.5450 averaging bids remain canceled.

## Robinhood Chain spot — CLOSED_DUST

Canonical PONS contract:
`0x39dbed3a2bd333467115de45665cc57f813c4571`

Fresh Alchemy direct-chain balance:
- PONS **0.000953441979624353**
- native ETH **0.000815126815110326**

The former **54.799953441979625 PONS** spot sleeve has been cleared.

The remaining 0.000953441979624353 PONS is residual dust and does **not** count as an active position.

All previously stored Robinhood spot TP/downside trigger monitoring is retired. Do not infer which order/swap produced the exit without transaction-history reconstruction.

## Monitoring

Active PONS monitoring now covers:
1. Binance public mark/funding against the stored futures thresholds;
2. private futures state only when newer USER_CONFIRMED evidence exists;
3. material security/market event affecting the active Binance PONS futures exposure.

Do not run dedicated Robinhood PONS spot price, TP/SL, liquidity or holder monitoring while only residual dust remains.

No automatic order creation/modification/reallocation.
