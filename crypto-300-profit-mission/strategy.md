# $300 Crypto Profit Mission

Timezone: Asia/Bangkok

## Capital plan

- JUMP Legion ICO reserve: 150 USDC
- PONS trading margin: about 50 USDT
- ETH trading margin: about 50 USDT
- Flexible reserve: 50 USDT

The goal is to maximize upside over roughly three months without allowing one PONS or ETH trade to consume the whole capital pool.

## PONS plan

Instrument: Binance PONSUSDT perpetual
Mode: isolated
Max leverage: 3x
Primary resting entries:
- 0.6250, about 40 USDT notional
- 0.5850, about 49.73 USDT notional
- 0.5450, about 59.95 USDT notional

Hard stop for the resting-entry plan:
- 0.4980, Mark Price, Stop Market
- Never widen this stop to rescue the trade.

If all three entries fill, expected average entry is about 0.578 and planned loss at 0.498 is about 20 to 21 USDT before fees, funding and slippage.

Profit-taking plan:
- 0.738: close 10%
- 0.795: close 15%
- 0.955: close 20%
- 1.28: close 20%
- 1.75: close 15%
- final 20% runner

Stop management:
- After a valid 4h hold above 0.742, move remaining stop to about 0.618.
- After a valid break above 0.80, move remaining stop to about 0.665.
- After a valid break above 0.97, move remaining stop to about 0.795.
- After a valid break above 1.30, move remaining stop to about 0.955.
- After 1.75, manage the final 20% with roughly a 15% trailing stop unless market structure materially changes.

Stale-order rules:
- If PONS establishes a valid 4h close above 0.742, cancel any unfilled 0.585 and 0.545 resting bids.
- If all three resting entries fill, do not add more PONS with the reserve capital automatically.
- If the hard stop is hit, wait for a fresh 4h structure before considering re-entry.

Breakout alternative when none of the resting entries has filled:
- Require a 4h close above 0.666.
- Then require a 1h retest of 0.655 to 0.665 that holds above roughly 0.650.
- Cancel old resting-entry orders before switching to this breakout setup.
- Use about 100 USDT notional, 2x isolated, roughly 50 USDT margin.
- Stop about 0.618.
- Initial targets: 0.738, 0.795, 0.955, 1.28.
- Do not chase a vertical move into 0.70 to 0.80 without a retest.

PONS non-price risk triggers:
- Funding above +0.03% per 4h for 24h: pause adding.
- Funding above +0.05% per 4h persistently: reassess and consider reducing 25% to 50%.
- Binance ADL risk HIGH: do not raise leverage above 3x and favor incremental profit-taking.
- Significant deterioration in top-trader long/short ratio, OI, liquidation structure, or abnormal basis: reassess before adding.
- Official change to the Pons buyback/burn mechanism: immediate reassessment.
- Large onchain treasury/distributor movements, large holder deposits to exchanges, abnormal mint/burn changes, or contract/admin changes: immediate reassessment.
- If 7d holder revenue falls below about 1.5M USD and 7d DEX volume below about 250M USD for a sustained period, reassess the thesis even if the hard stop has not traded.

## ETH plan

Do not force an entry before the September 25, 2026 quarterly options expiry.
Deribit quarterly options expire at 08:00 UTC, which is 15:00 Asia/Bangkok.

Primary post-expiry long setup:
- Look for ETH roughly 2,590 to 2,630.
- Require a 4h reclaim/hold above about 2,640 after the reaction.
- Use about 50 USDT margin, isolated, normally 4x.
- Approximate 200 USDT notional.
- Stop about 2,535.
- TP1 2,800: close 25%
- TP2 3,000: close 30%
- TP3 3,300: close 25%
- Final 20% runner / trailing management.

Breakout alternative:
- If ETH closes a daily candle above about 2,810 without giving the pullback setup, wait for a 2,760 to 2,790 retest before considering entry.
- Do not chase a vertical move.
- Invalidate the current long setup if daily structure breaks materially below about 2,540, then reassess from fresh market data.

ETH monitoring must include:
- spot/perpetual price structure
- funding
- open interest
- top-trader positioning
- Hyperliquid / major perpetual market context when available
- large options positioning / expiry effects
- Polymarket probabilities
- ETF flows and material macro catalysts

## JUMP reserve

Keep 150 USDC reserved until the official Legion/Jumper sale page confirms sale date, FDV, token price, allocation, TGE unlock, vesting and initial circulation.

Working allocation rule:
- Around 75M FDV with at least 50% sale-token TGE unlock: up to 150 USDC application.
- Around 100M to 125M FDV: reduce application to about 100 USDC.
- Above 150M FDV or unfavorable unlock/circulation: reduce sharply or skip.

Do not treat community-posted tokenomics as confirmed until official Jumper/Legion documentation is available.

## Notification rules

Every monitor run should update the mission repository, but email and user notification must remain silent unless there is a material actionable change.

Material changes include:
- entry/stop/take-profit trigger
- stale-order cancellation trigger
- breakout setup confirmation
- funding/OI/long-short/ADL deterioration significant enough to alter the plan
- large onchain PONS flow or contract/admin/burn mechanism change
- official Pons announcement that materially changes token economics or market structure
- ETH post-expiry trade window becoming actionable
- official JUMP/Legion sale terms becoming available or materially changing

No material change means NO_ACTION and no email.
