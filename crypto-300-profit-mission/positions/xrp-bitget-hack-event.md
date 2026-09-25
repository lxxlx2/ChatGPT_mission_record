# XRP / Bitget hack event trade

Updated: 2026-09-26 01:30 Asia/Bangkok

## Capital and venue
- Venue: Variational Omni
- Instrument: XRP perpetual
- User-reported funding path: bridged about 52 USD-equivalent from Solana to Arbitrum, converted to USDC for Omni.
- Variational portfolio shown before/after order submission: about 49.90 USDC.
- Objective: positive expected trading PnL first, with Omni points as a secondary objective.
- Privacy: no wallet address, tx hash, or other identifying transaction details are stored here.

## User-confirmed order state — RESTING / PENDING FILL
- Direction: LONG XRP
- Order type: Limit
- Entry limit: 1.5560
- Quantity: 77.12 XRP
- Notional size: about 120 USD
- Margin mode: isolated
- Leverage: 3x
- Required margin shown by Variational: about 40.35 USDC
- Remaining account buffer before fill: about 9.55 USDC
- Take profit: 1.6280
- Hard stop: 1.5140
- TP/SL maximum slippage shown: 1%
- Entry-order maximum slippage shown: 0.5%
- Screenshot status at 2026-09-26 01:30 Asia/Bangkok: three pending orders visible: entry limit buy, stop-loss sell-all, take-profit sell-all.
- Do not count this as filled exposure until the user confirms fill or a connected private source proves it.

## Risk / reward estimate
- Entry to stop: about -2.70% on XRP.
- Approximate loss at stop on 120 USD notional: about -3.24 USDC, excluding funding, spread and slippage.
- Entry to take-profit: about +4.63%.
- Approximate gross profit at take-profit on 120 USD notional: about +5.55 USDC, excluding funding, spread and slippage.
- Approximate gross reward/risk: about 1.7x.

## Monitoring / email triggers
- Keep this under the existing $300 Crypto Profit Mission hourly monitor.
- Rapid move trigger: absolute 15m >=2.0%, 1h >=3.0%, or 4h >=5.0%.
- Level triggers: 1.5140, 1.5190, 1.5560, 1.6280, 1.6300, 1.7000.
- If public XRP trades through 1.5560 while this file still says pending, treat as probable fill and email the user to verify Variational; do not silently change status to FILLED.
- Leverage-stress trigger: roughly 1h OI change >=10% with price move >=1.5%, or absolute 8h funding >=0.05%.
- On-chain event trigger: attacker-controlled XRP movement >=5M XRP toward executable liquidity / bridge / exchange, or credible Bitget XRP replenishment >=5M XRP.
- Triggered alerts go by Gmail to lxx.run688@gmail.com with subject prefix: Crypto Mission 操作提醒｜XRP｜.
- No trigger means silence.

## Variational points discipline
- Trading volume is only one component of points and the full allocation formula is not public.
- Avoid wash-style churn or excessive leverage solely to farm points.
- This is an organic event trade; entry and eventual exit naturally generate activity if filled.

## Invalidation / management
- Cancel the unfilled long if credible evidence shows attacker-controlled XRP being moved in large size toward executable liquidity.
- Cancel or reassess if XRP breaks below the event support area around 1.519 before the order fills.
- After confirmed fill, update actual fill price, actual size, liquidation price, TP/SL status, funding and realized/unrealized PnL.
- Pending orders must never be counted as filled exposure.


## Capital-source correction and objective — 2026-09-26
- Capital is from the Mission's prior ~141 USDC-equivalent uncommitted pool.
- About 52 USD-equivalent was reallocated to Arbitrum/Variational; about 49.90 USDC is visible in Omni.
- This is an internal Mission transfer, not an external contribution.
- Approximate remaining uncommitted Mission cash after this reallocation: ~89 USD-equivalent, pending exact bridge/swap/gas reconciliation.
- Objective hierarchy:
  1. seek positive event-driven P&L from the Bitget/XRP dislocation;
  2. earn Variational Omni points through organic trading activity as a secondary benefit.

## Market update — 2026-09-26 about 01:35 Asia/Bangkok
- Public Binance XRPUSDT: about 1.5700; 24h +2.44%; 24h range 1.5191–1.6300; 24h spot volume about 343.9M XRP / 540.8M USDT.
- BTCUSDT 24h about -0.39%; ETHUSDT about +0.43%. XRP is therefore showing material relative strength versus BTC and ETH over the same 24h window.
- Binance XRP perpetual OI fell from about 318.31M XRP to 314.10M XRP over the latest hour, about -1.32%.
- Aggregate latest 12 x 5m taker flow: buy/sell ratio about 0.97; the latest two 5m samples were about 0.65 / 0.65, indicating near-term active selling pressure.
- Top-trader position accounts are still heavily long: about 71.8% long, position L/S ratio about 2.55.
- Latest Binance funding sample is only about +0.000973% per 8h, so the long side is crowded by account ratio but not yet expensive by funding.
- Visible Binance book snapshot shows notable bids clustered around 1.560–1.562 and notable asks around 1.574–1.579. Treat displayed depth as transient and spoofable, not durable support/resistance.
- Latest verified hack tracking still places roughly 102.9M XRP in attacker-linked wallets. Only about 33,500 XRP had been observed routed through Bridgers in the verified follow-up, around 0.03% of the stolen XRP. This leaves very large latent supply risk but no evidence yet of a broad XRP liquidation.
- Bitget's latest official notice located in this update still has withdrawals paused during the security review.

## Current interpretation
- The resting 1.5560 bid remains preferred over chasing around 1.57.
- Short-term base case is consolidation/retest around 1.56–1.58 after the event spike, because price remains relatively strong while OI is contracting and current taker flow is mildly sell-heavy.
- Bullish continuation requires acceptance back above roughly 1.58–1.59, then a retest of the 1.63 event high. A clean 1.63 break with renewed spot/taker demand would strengthen the long thesis.
- A loss of 1.556 followed by 1.519 invalidates the event-support structure and requires cancellation/reassessment if still unfilled.
- Main asymmetry remains event-driven: potential Bitget inventory/replenishment demand versus attacker-held ~103M XRP supply. Bitget has not publicly committed to buying 103M XRP in the open market, so the replenishment thesis must remain conditional.
- At public price ~1.5700, a hypothetical already-filled 1.5560 position would be about +1.08 USDC gross (+2.68% on the shown ~40.35 USDC margin), but the private Variational order is still recorded as pending, so actual P&L remains 0 until fill is confirmed.
