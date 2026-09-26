# Monster-Coin Squeeze Monitor V2.1

Updated: 2026-09-26 12:36 Asia/Bangkok

Purpose: factual squeeze/blow-off state classification across Binance Alpha and Binance USDⓈ-M Futures.

## Frozen state machine

Parameters remain frozen unless a separate explicit backtest changes the model version.

### STRUCTURAL_CANDIDATE
Plausible squeeze structure such as low effective float, concentrated supply, shallow/asymmetric spot depth, Alpha/Futures attention leverage or OI/liquidity imbalance.

Discovery state only.

### PRESSURE
A structural candidate develops squeeze pressure through weak/negative funding, growing leverage/volume or evidence of vulnerable shorts.

Intraday PRESSURE is logged unless another factual alert gate is met.

### IGNITION
Within 7 days of setup, all must hold:
1. latest completed 1h close > prior 24h high by >=1%;
2. 6h gain >=10%;
3. latest 3h average quote volume >=1.5x prior-24h hourly median;
4. representative 3h Taker Buy Ratio >=51%;
5. price >= setup price x1.05.

Historical reference from prior backtest:
- 84 Binance USDⓈ-M perpetuals;
- 13 V2 IGNITION signals;
- 61.5% reached +20% within 72h.

Historical hit rate is context, not a forecast.

### EXHAUSTION
After IGNITION / major squeeze, evidence may include:
- funding normalization / materially positive funding;
- OI deleveraging;
- fading taker buying;
- failed continuation / loss of breakout structure.

## Universe

Every Mission hourly run:
- bulk Binance USDⓈ-M universe screen;
- Binance Alpha discovery when available;
- 7-day carried candidates;
- active SAGA watch.

Detailed deep-check is limited to the bounded shortlist defined by RUNBOOK.

Primary data:
- Binance official market/futures data;
- price/klines/quote volume;
- mark/funding/OI;
- taker buy/sell;
- top-trader positioning;
- spot depth/liquidity when needed;
- direct-chain holder/float evidence when available.

English X/Reddit may support narrative discovery but cannot substitute for market facts.

## Alerts

Automation alerts are factual state-transition notices.

- STRUCTURAL_CANDIDATE: GitHub intraday, daily summary candidate.
- PRESSURE: GitHub intraday.
- first confirmed IGNITION: Gmail + ChatGPT factual alert.
- EXHAUSTION: immediate factual alert if tied to a prior alerted IGNITION or user-held asset; otherwise daily summary.
- duplicate unchanged state: silent.

IGNITION alert includes:
- symbol;
- state transition;
- current price;
- 1h breakout %;
- 6h change;
- 3h volume multiplier;
- 3h taker-buy %;
- funding / OI trend;
- invalidation / chase risk;
- unconfirmed fields;
- `decision_status: REVIEW_REQUIRED`.

It must not include newly invented position sizing, leverage or buy/sell instructions.

## 19:29 daily summary

The same existing Mission run summarizes:
- today's state transitions;
- up to 5 strongest STRUCTURAL/PRESSURE candidates;
- all IGNITION/EXHAUSTION;
- explicit "no confirmed IGNITION/EXHAUSTION" when applicable.

## Functional QA

Record:
- universe_checked;
- alpha_checked;
- futures_checked;
- candidates_count;
- structural_count;
- pressure_count;
- ignition_count;
- exhaustion_count;
- data_source_failures.

Skipping this lane prevents full success.
