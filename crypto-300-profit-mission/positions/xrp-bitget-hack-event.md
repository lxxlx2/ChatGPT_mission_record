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
