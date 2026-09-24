# BTC Regime / JasonLeo Watchlist

Updated: 2026-09-25 02:16 Asia/Bangkok

## Role

This file is an execution watchlist for the Crypto Profit Mission.

External X source:
- Handle: `@Jason60704294`
- Role: supplementary public trader signal
- Authority: low by itself; no trade may be triggered solely from this account

## Captured framework

From the user's 2026-09-25 screenshot of the source's public post:
- source reports a prior BTC long thesis around 58,000 and says much of the profit was lost during an unsuccessful attempt to time the top;
- source reports current combined long exposure built around roughly 78,000;
- current reference price in that post was roughly 84,000;
- below roughly 79,000: begin reducing long exposure;
- a fast move to roughly 98,000 to 105,000: consider a partial defensive short for weekly-scale pullback risk;
- daily hold above roughly 108,000: defensive short thesis invalid;
- if price balances sufficiently between roughly 80,000 and 100,000: source would consider roughly 115,000 to 125,000 as a later defensive / decision zone.

Treat self-reported entries and PnL as unverified unless independently supported by public position/onchain evidence.

## Machine-checkable Mission interpretation

### BTC_RISK_OFF candidate
Require one of:
- 4h close below 79,000 followed by a failed reclaim; or
- daily close below 79,000.

Then reassess ETH/high-beta exposure and prohibit automatic averaging down.

### BTC_HEDGE_CANDIDATE
Require BTC inside 98,000 to 105,000 after a fast extension plus at least two independent overheating confirmations.

Useful confirmations:
- funding materially above its recent baseline;
- OI expands rapidly with price;
- top-trader or broad-account long positioning becomes crowded;
- liquidation-driven upside acceleration;
- unusually large 24h/48h extension versus recent realized volatility.

The price zone by itself does not qualify.

### BTC_HEDGE_INVALIDATED
If a defensive hedge thesis is active and a daily candle establishes above roughly 108,000, cancel that thesis and reassess from fresh data.

### BTC_BULL_CONTINUATION candidate
Require:
- multi-day balance mainly within 80,000 to 100,000;
- no confirmed 79,000 breakdown;
- leverage/funding/OI crowding cools or remains controlled;
- price exits the balance with confirmation.

Use 115,000 to 125,000 as an upside reference zone, not as a guaranteed target.

## Data checks each hourly run

Primary:
- Binance BTCUSDT price, 4h and 1d candles
- funding
- OI and OI change
- top-trader long/short positioning
- broad account long/short ratio

Secondary when available:
- Hyperliquid and other major perpetual venues
- liquidation structure
- options / major expiry positioning
- US spot BTC ETF flows
- major macro event risk
- public posts from `@Jason60704294`

## External-source alert filter

Record new relevant posts to GitHub. Notify only when a new post:
- changes explicit key levels;
- reports a material BTC position change;
- invalidates the previously captured framework;
- introduces a new path thesis that would alter the Mission's risk posture.

Generic commentary or unchanged views => NO_ACTION.

## Current reference snapshot

Binance BTCUSDT checked around 2026-09-25 02:17 Asia/Bangkok:
- last price: about 84,567.3
- 24h high: about 84,901.6
- 24h low: about 82,832.0
- current recent funding sample: about +0.001422%
- latest 4h top-trader position long/short ratio: about 1.9817
- latest 4h broad-account long/short ratio: about 1.2701

Interpretation at this snapshot:
- 79,000 risk-off trigger not active;
- 98,000 to 105,000 hedge zone not active;
- current data supports monitoring rather than a new BTC trade;
- no new BTC capital allocation is authorized.
