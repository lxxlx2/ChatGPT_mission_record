# Monster-Coin Squeeze Monitor V2.1

Updated: 2026-09-28 Asia/Bangkok

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

Full universe cadence:
- one bulk Binance USDⓈ-M universe screen every 3 hours;
- one required full scan at 19:29 for the daily summary;
- Binance Alpha discovery when available;
- 7-day carried candidates;
- active SAGA watch.

On non-due hourly Mission cycles:
- do not fetch the entire futures universe;
- cheaply refresh persisted STRUCTURAL/PRESSURE/IGNITION candidates when practical;
- record `monster_status: not_due` when no refresh is needed.

Each full scan deep-checks at most 3 new shortlist symbols before persistence. Additional candidates can roll into the next due scan.

Primary data:
- Binance official market/futures data;
- price/klines/quote volume;
- mark/funding/OI;
- taker buy/sell;
- top-trader positioning;
- spot depth/liquidity when needed;
- direct-chain holder/float evidence when available.

English X/Reddit may support narrative discovery but cannot substitute for market facts.

## Durable candidate state

Authority:
`state/monster-squeeze-v2.1-current.md`

A candidate that becomes STRUCTURAL_CANDIDATE or PRESSURE must persist its `first_seen` and `setup_price`. The frozen IGNITION rule requiring price >= setup_price x1.05 cannot be evaluated from an ephemeral shortlist alone.

Do not invent setup prices from past prices after the fact.

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

The same existing Mission run summarizes and delivers:
- universe size and data-source status;
- today's state transitions;
- up to 5 strongest STRUCTURAL/PRESSURE candidates with key gates;
- all IGNITION/EXHAUSTION;
- explicit "no confirmed IGNITION/EXHAUSTION" when applicable;
- data gaps.

The summary must be sent by Gmail + ChatGPT. Audit-only generation is incomplete delivery. Gmail exact-subject dedupe prevents duplicates.

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

On a due Monster cycle, failure is recorded as a Monster data gap and must be retried on the next due/recovery opportunity. On a non-due cycle, `not_due` is healthy. Monster work occurs after the Mission core final so it cannot erase core scheduler proof.


## Anti-starvation queue

The deep-check cap of 3 is a runtime budget, not permission to forget candidates.

Any full-screen symbol that qualifies for the shortlist but is not deep-checked must be persisted as `DEFERRED_SHORTLIST` with:
- first_seen;
- snapshot price if directly available in that scan;
- 24h change / quote volume;
- reason for shortlist;
- next_due;
- expiry.

At each due Monster scan:
1. deep-check at least **1 oldest deferred candidate** first;
2. use remaining slots for the strongest current candidates;
3. remove a deferred candidate only after a deep-check rejects/promotes it, it expires, or market data becomes unavailable with an explicit gap.

A newly stronger mover must not indefinitely starve an older deferred candidate.

## Deterministic due rule

A full Monster screen is due when either:
- elapsed time since `last_successful_full_scan_at` is >= 3 hours; or
- it is the required 19:29 Asia/Bangkok daily-summary cycle.

Do not derive `monster_due:false` only from the wall-clock hour. Scheduler drift does not cancel a due scan.

Persist `last_successful_full_scan_at` after every completed full screen.

## Missed-candidate regression: BTWUSDT

Observed:
- 2026-09-27 12:34 Asia/Bangkok recovery scan explicitly shortlisted **BTWUSDT +17.39%**.
- It was not deep-checked only because QNT/Q/SOON consumed the max-3 slots.
- No durable deferred queue entry was created.
- Later automatic runs incorrectly reported `monster_due:false`, so BTW never received its required follow-up deep-check.

Retrospective Binance hourly data shows BTW met all four objective market gates, excluding the persisted-setup gate, at:
- 2026-09-28 13:00 Asia/Bangkok close: breakout +1.45%, 6h +11.44%, 3h volume ~4.60x, 3h taker-buy ~52.45%.
- 2026-09-28 14:00 Asia/Bangkok close: breakout +3.97%, 6h +15.52%, 3h volume ~7.29x, 3h taker-buy ~53.15%.

At the 2026-09-27 shortlist time BTW traded around 1.05-1.06, so either later close was also >5% above that observed region. However the frozen model forbids inventing a setup price after the fact, therefore this incident is recorded as `MISSED_ALERT / NOT_BACKFILLED_AS_IGNITION`, not as a fabricated historical state transition.

This is a runtime coverage failure, not evidence that V2.1 market gates rejected BTW.


## Coverage-completeness override — 2026-09-29

Frozen V2.1 market thresholds remain unchanged. Runtime coverage is expanded.

On each due full scan:
- maximum deep-check budget = 5;
- if at least two deferred candidates exist, the two oldest deferred candidates consume the first two slots;
- remaining slots go to current strongest shortlist candidates;
- if only one deferred exists, reserve one slot for it.

Every shortlist symbol must end the scan in one of:
- DEEP_CHECKED_PROMOTED;
- DEEP_CHECKED_REJECTED;
- DEEP_CHECKED_RETAINED;
- DEFERRED_SHORTLIST;
- DATA_GAP.

No silent disappearance is permitted.

Every due audit records:
- universe_count
- shortlist_count
- shortlist_symbols
- deep_checked_count
- deep_checked_symbols
- deferred_checked
- deferred_added
- deferred_remaining
- promotions
- rejections
- ignition_count
- exhaustion_count
- data_gaps

At 19:29 persist a GitHub coverage report even when zero IGNITION/EXHAUSTION:
`crypto-300-profit-mission/reports/monster/YYYY/YYYY-MM/YYYY-MM-DD.md`

The existing 19:29 factual Gmail/ChatGPT summary remains unchanged.


## Efficient deep-check data plan — 2026-09-29

To reduce scheduler timeouts while preserving V2.1:
- use all-symbol 24h ticker once;
- use all-symbol mark/funding once when needed;
- per deep-check symbol use 1h kline + OI history as the default;
- derive 3h taker-buy share from kline total volume and taker-buy volume fields where available;
- dedicated taker-volume/top-trader calls are late-stage confirmation calls, not mandatory for obvious early rejection.

An early rejection is valid only when the already-fetched metrics prove a frozen V2.1 gate cannot pass.
Do not label a candidate IGNITION until every required IGNITION metric has been obtained.
