# XRP / Variational Omni Event Trade

Updated: 2026-09-27 01:20 Asia/Bangkok

## Status
ACTIVE / FILLED

User-confirmed from Variational Omni UI screenshot.

## Position
- Venue: Variational Omni.
- Instrument: XRP perpetual.
- Direction: LONG.
- Quantity: 77.12 XRP.
- Entry: 1.55589.
- Selected leverage: 3x.
- Margin mode: isolated.
- Position value at screenshot: about 120.96 USD.
- Margin used: about 40.99 USDC.
- Liquidation price shown by UI: 1.24430.
- Account / portfolio equity shown: 50.87 USD.
- Tradable / available balance shown: 10.55 USD.

## Attached exits
- Take profit: 1.6280.
- Stop loss: 1.5140.
- TP/SL remain active unless the user explicitly changes them.

## Snapshot
At the 2026-09-26 06:08 Asia/Bangkok screenshot:
- mark price: 1.56844.
- unrealized PnL: +0.97 USD.
- unrealized return on margin: +2.42%.
- account leverage shown: about 2.38x.

The screenshot is the authoritative source for private venue position state. Public market data may be used for monitoring, but must not overwrite private fill/position fields unless the user confirms or a connected Variational source becomes available.

## Risk / reward from filled entry
Using entry 1.55589:
- TP distance: +0.07211 per XRP.
- SL distance: -0.04189 per XRP.
- Gross TP PnL for 77.12 XRP: about +5.56 USDC before funding/spread/slippage.
- Gross SL PnL for 77.12 XRP: about -3.23 USDC before funding/spread/slippage.
- Gross reward/risk ratio: about 1.72.

## Capital source
- Internal Mission reallocation from the previously uncommitted speculative cash.
- About 52 USD-equivalent was moved toward Arbitrum / Variational.
- This is not a new external contribution.
- Primary objective: event-driven XRP profit.
- Secondary objective: organic Variational points activity.

## Monitoring
While this position remains active, the Mission fast lane must check:
- XRP mark / spot reference and 15m / 1h / 4h moves;
- OI, funding, leverage stress and taker imbalance when available;
- Bitget-hack-related XRP wallet movements and credible Bitget replenishment flows via `watchlists/xrp-bitget-hacker-flow.md`;
- TP 1.6280 and SL 1.5140;
- abnormal rapid drawdown / security events.

Alert only on a NEW actionable trigger. Do not send routine hourly updates.

## Exit / bookkeeping
When TP, SL, manual close or partial close occurs:
- update this file immediately;
- update performance/current.md with realized PnL only after the close is user-confirmed or venue data is verified;
- do not treat Variational points as PnL until distributed and economically realizable.

## 2026-09-26 16:33 public-market refresh

Binance public XRPUSDT mark: **1.53882547**.

Since the latest user-confirmed Variational screenshot, the checked public Binance mark path did not cross:
- TP 1.6280
- SL 1.5140

If the Variational position remains unchanged at 77.12 XRP @ 1.55589:
- public-mark implied uPnL: **~-1.3160 USD**

This does not overwrite the private venue state. Exact Variational PnL/equity remains USER_CONFIRMED until a connected/private venue read or newer screenshot is available.


## 2026-09-27 monitoring correction

The Sep-26 attacker-flow change was not surfaced automatically even though this position file required hack-flow monitoring.

Verified follow-up reporting indicates roughly 54M XRP had left the five original attacker holding accounts, leaving roughly 49M XRP there. Movement is not automatically equivalent to sale.

The dedicated machine-readable authority is now:
`watchlists/xrp-bitget-hacker-flow.md`

While this position is active, its >=5M XRP movement/liquidity/replenishment triggers are required Mission lanes.
