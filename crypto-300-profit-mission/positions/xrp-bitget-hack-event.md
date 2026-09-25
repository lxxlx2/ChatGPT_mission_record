# XRP / Bitget hack event trade

Updated: 2026-09-26 Asia/Bangkok

## Capital and venue
- Venue: Variational Omni
- Instrument: XRP perpetual
- User-reported funding path: bridged about 52 USD-equivalent from Solana to Arbitrum, converted to USDC for Omni.
- Variational portfolio shown before order: about 49.90 USDC.
- Objective: positive expected trading PnL first, with Omni points as a secondary objective.
- Privacy: no wallet address, tx hash, or other identifying transaction details are stored here.

## Current plan — PENDING LIMIT ORDER
- Direction: LONG XRP
- Order type: Limit
- Entry limit: 1.5560
- Leverage: 3x
- Notional size: 120 USD
- Expected initial margin: about 40 USDC
- Reserve cash / margin buffer: about 9.9 USDC
- Estimated XRP quantity at entry: about 77.12 XRP
- Take profit: 1.6280
- Hard stop: 1.5140
- Order status: pending / not user-confirmed as submitted or filled yet

## Risk / reward estimate
- Entry to stop: about -2.70% on XRP.
- Approximate loss at stop on 120 USD notional: about -3.24 USDC, excluding funding, spread and slippage.
- Entry to take-profit: about +4.63%.
- Approximate gross profit at take-profit on 120 USD notional: about +5.55 USDC, excluding funding, spread and slippage.
- Approximate gross reward/risk: about 1.7x.
- Do not raise leverage to the UI maximum. Keep 3x for this event trade.

## Market snapshot used for the plan
- XRPUSDT reference price around planning time: about 1.5752.
- Binance XRP perpetual open interest: about 314.5M XRP.
- Top-trader 15m position long share: about 71.8%, long/short ratio about 2.54.
- Latest sampled 15m taker buy/sell ratio recovered to about 1.20 after several sell-heavy intervals.
- Recent local support cluster observed around 1.548-1.559.
- Recent event high/resistance around 1.63.
- Trade thesis remains conditional on no confirmed large-scale disposal of the stolen XRP by attacker-controlled wallets before entry.

## Variational points discipline
- Official Omni documentation states that trading volume is only one component of points and the full allocation formula is not public.
- Avoid wash-style churn or excessive leverage solely to farm points.
- This order is intended to be an organic event trade. Opening and later closing the position will naturally generate platform activity/volume if filled.

## Invalidation / management
- Cancel the unfilled long if credible on-chain evidence shows attacker-controlled XRP being moved in large size toward executable liquidity/venues.
- Cancel or reassess if XRP breaks below the event support area around 1.519 before the order fills.
- After a confirmed fill, update this file with actual fill price, actual size, liquidation price, TP/SL status, funding, and realized PnL.
- Pending orders must never be counted as filled exposure.
