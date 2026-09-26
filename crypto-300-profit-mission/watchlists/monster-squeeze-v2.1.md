# Monster-Coin Squeeze Monitor V2.1

Updated: 2026-09-26 07:52 Asia/Bangkok

## Purpose
Reusable squeeze / blow-off monitoring for Binance Alpha and Binance USDⓈ-M Futures. The goal is to detect a small number of asymmetric momentum events early enough to matter while avoiding routine altcoin noise.

## Frozen state machine
The state machine remains frozen unless a new backtest explicitly justifies a version change.

### STRUCTURAL_CANDIDATE
Requires a plausible squeeze structure, using available evidence such as:
- low effective float / concentrated supply;
- shallow or asymmetric spot depth;
- Binance Alpha and/or Futures access that can expand attention/leverage;
- OI relative to spot depth / available liquidity;
- a historical or current structure that can support forced covering.

This is a discovery state, not an entry signal.

### PRESSURE
A structural candidate develops squeeze pressure, typically involving negative/weak funding, growing volume / leverage pressure, or other evidence that shorts are becoming vulnerable.

PRESSURE remains silent intraday unless another Mission risk/action rule is hit.

### IGNITION
Frozen V2 ignition gate. Within 7 days of the setup, require all of:
1. latest completed 1h close > prior 24h high by at least 1%;
2. 6h price gain >= 10%;
3. latest 3h average quote volume >= 1.5x the prior-24h hourly median;
4. aggregate/representative 3h Taker Buy Ratio >= 51%;
5. price >= setup price x 1.05.

If all five are satisfied, state = IGNITION.

Backtest reference:
- 84 Binance USDⓈ-M perpetuals launched 2024-12-18 through 2025-04-30;
- observed about 63 days;
- 13 V2 IGNITION signals;
- 61.5% reached +20% within 72h.

This historical hit rate is a reference, not a guarantee.

### EXHAUSTION
After an IGNITION / major squeeze, watch for:
- funding normalizing or turning materially positive;
- OI deleveraging;
- taker buying fading;
- failed continuation / loss of breakout structure.

If the user has an active position or the Mission previously sent an IGNITION alert, EXHAUSTION is actionable and must alert immediately. Otherwise include it in the daily summary.

## Scan universe
Every Mission hourly run:
- Binance Alpha current universe;
- Binance USDⓈ-M perpetual universe;
- candidates carried from the previous 7 days.

Do not use Chinese websites as confirmation sources.

Primary data:
- Binance official Alpha / Futures data;
- price / klines / quote volume;
- mark, funding, OI;
- taker buy/sell;
- top-trader positioning;
- spot depth / liquidity;
- direct chain holder / float evidence when available.

English X / Reddit can help explain narrative or crowding but cannot substitute for market data.

## Alert policy
- STRUCTURAL_CANDIDATE: GitHub only intraday. Include the strongest candidates in the 19:29 Bangkok daily summary.
- PRESSURE: GitHub only intraday.
- IGNITION: immediate Gmail + user-visible ChatGPT alert on the first hourly run that confirms it.
- EXHAUSTION: immediate Gmail + ChatGPT if a prior IGNITION was alerted or the user holds the asset; otherwise daily summary.
- Duplicate state with no material data change stays silent.

An IGNITION alert must include:
- symbol;
- setup/state transition;
- current price;
- 1h breakout percentage;
- 6h change;
- 3h volume multiplier;
- 3h taker-buy percentage;
- funding and OI trend;
- invalidation / chase risk;
- whether it is action-ready or watch-only;
- suggested maximum Mission capital source if action-ready.

## Daily summary
At the Mission run at 19:29 Asia/Bangkok:
- summarize today's state transitions;
- show up to 5 strongest STRUCTURAL/PRESSURE candidates;
- list every IGNITION/EXHAUSTION;
- if none, explicitly say there was no confirmed IGNITION/EXHAUSTION;
- user-visible summary is required even when no action signal fired.

This replaces the separate 妖币每日汇总 automation.

## Functional QA
Every hourly Mission run records:
- universe_checked;
- alpha_checked;
- futures_checked;
- candidates_count;
- structural_count;
- pressure_count;
- ignition_count;
- exhaustion_count;
- data_source_failures.

A run that skips this lane cannot be marked fully successful.

## Smoke test — 2026-09-26
WLD was checked because it was up about 12.6% over 24h and OI was rising. It did NOT pass IGNITION at the check:
- no completed 1h close > prior 24h high by 1%;
- 6h gain was below 10%;
- recent 3h taker-buy share was around/below the 51% gate.
Result: hot candidate / watch, not IGNITION.
