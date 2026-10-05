# MONSTER GROUND TRUTH V1 — frozen before discovery

This specification freezes objective labels, episode grouping, search space, evaluation splits and gates before a full-universe run. English narratives may explain results later; they cannot select symbols or change labels. Price V3 is PAUSED. All output remains shadow evidence with no investment judgment.

## Sources, universe and period

Canonical historical source: Binance official public-data archive, Spot and USDⓈ-M Futures separately. Universe membership uses the saved historical directory inventories (Spot3710/Futures1018) union current official inventory. Stage A uses 1h candles and USDT-quoted symbols; FDUSD/USDC can be separate extension cohorts, never silently substituted. Historical-not-current symbols remain in discovery and replay when bars exist. Archive membership is symbol-level, not a delisted-token assertion.

Analysis anchors: 2025-01-01T00:00:00Z <= t < 2026-10-01T00:00:00Z. Warm-up starts 2024-10-01 where official archives exist. Monthly archives only contain completed months; daily archives fill completed September2026 days when available. The current incomplete hour/day is excluded. Missing/404/timeout/invalid ZIP/checksum failure/parse failure are separate statuses. Unavailable September bars cause right-censoring, not a quiet zero-event result.

Stage B downloads 5m, optionally1m, only around discovered events/candidates. Alpha historical GT is excluded unless an official verifiable historical API is documented and tested; otherwise ALPHA_HISTORICAL_UNAVAILABLE. Current Alpha inventory is not historical coverage proof.

## Candle contract and boundaries

A candle is timestamp/open/high/low/close/base_volume/quote_volume/trade_count. Convert exchange millisecond or microsecond epochs to integer UTC milliseconds explicitly; require exactly3600000ms between adjacent1h opens. High>=max(open,close), low<=min(open,close), prices>0, volumes>=0, trades>=0. Exact duplicates collapse once; conflicting duplicates reject the segment. Missing bars split segments; never forward-fill, invent volume or bridge a gap. Closed-bar feature observation time is open_time+3600000ms; future windows are strictly later bars.

GT does not filter by a learned liquidity threshold. Extreme high prints remain evidence with liquidity and data-quality flags for audit. Each venue/symbol has its own price denomination; no leveraged-symbol or redenomination exclusion based on knowing an outcome. Instrument-migration ambiguity is reported, not hidden.

## Objective anchors, tiers and episodes

For each eligible closed1h bar t, anchor_price=close(t). Evaluate high(t+1)..high(t+72) and high(t+1)..high(t+168), divided by anchor_price. Require all168 subsequent hourly bars in the same contiguous segment. Missing future coverage makes t INELIGIBLE_RIGHT_CENSORED. Retain both72h and7d maxima, but primary tier uses7d.

Walk t chronologically. When primary maximum first reaches>=2, open one event at t. Peak is the earliest future bar attaining the maximum high within168h. Highest mutually exclusive tier: [2,3)=MONSTER_2X, [3,5)=MONSTER_3X, [5,10)=MONSTER_5X, [10,20)=MONSTER_10X, >=20=MONSTER_20X_PLUS. Also report cumulative >=2/3/5/10/20 counts explicitly as a separate table.

To prevent hundreds of overlapping labels, ignore new anchors through peak_bar+168h inclusive (fixed refractory). This is a reproducible episode rule, not proof that economically all related rallies are grouped perfectly. Do not retrospectively extend the peak window or shorten refractory to improve recall. Report sensitivity as a later version, preserving V1.

For each event retain anchor,72h/7d peak multiples,first high-crossing times for1.25/1.5/2/3/5/10/20,peak_time,duration=peak_time-anchor_time,and min(low from t+1 through peak)/anchor_price-1. Crossing bars provide hourly bounds, not second-level execution times. No trading-return claim.

NEW_LISTING_MONSTER requires independently verified first-available instrument history<168h at anchor. A dataset left edge is not a listing date; unverified first-history age is UNKNOWN. OLD_SHELL_REACTIVATION requires >=2160h observed contiguous past history, >=90% usable previous720h bars, median previous720h quote volume<10000USDT/hour, and previous720h close max/min<2. All conditions use bars strictly before or at anchor and do not use symbol names. Age/censoring and qualification must be reported separately.

## Causal D1 feature contract

Live features use closed bars at t or earlier only: returns1/4/6/24h; trailing quote volume/trades; volume acceleration=current quote volume divided by median previous24 bars (denominator must be positive); range expansion=(high-low)/close divided by median previous24 such ranges; BTC-relative1h/4h returns; distance from prior7d/30d high; observed symbol age; time since an observed past spike. 5m/15m features require separately availableStageB/live bars; never interpolate them from1h data.

Cross-sectional percentiles are computed at the same closed-bar timestamp across all eligible instruments in the same venue/cohort; include symbols that subsequently delist. Percentile is midrank: (count_less+0.5*count_equal)/N, retaining N and missing-symbol count. Require N>=20. BTC reference is BTCUSDT from the same official venue/time; missing or stale BTC blocks feature evaluation rather than substituting0. A future-discovered symbol must not appear before its first actual candle. No future price/max/peak/tier/event flag may enter a live feature or candidate payload.

## Finite search, state and splits

48 deterministic configurations, Cartesian product:

- return percentile threshold: 0.95 / 0.98 / 0.99;
- volume-acceleration percentile threshold: 0.80 / 0.95;
- BTC-relative percentile threshold: 0.80 / 0.95;
- range-expansion ratio threshold: 1.5 / 2.0;
- minimum current hourly quote volume: 10000 / 50000 USDT.

Activation: max(1h_return_percentile,4h_return_percentile)>=return_threshold AND (volume_acceleration_percentile>=volume_threshold OR BTC_relative_4h_percentile>=BTC_threshold) AND range_expansion>=range_threshold AND quote_volume>=liquidity_threshold. Missing features do not satisfy conditions. Every config uses identical universe/coverage and causal timestamps.

State per venue/symbol is INACTIVE/ACTIVE. Emit RAW_MONSTER_CANDIDATE only on INACTIVE->ACTIVE. Rearm after3 consecutive eligible closed bars failing activation. Gaps reset state to UNKNOWN; first recovered observation is explicitly recovery_context and not credited as an uninterrupted earlier trigger. V1 has no escalation branch. State must be durable for live restart; event_id derives fromvenue/symbol/config_version/activation_time.

TRAIN anchors: 2025-01-01<=t<2026-01-01. VALIDATION anchors: 2026-01-01<=t<2026-07-01. AUDIT/RECENT: 2026-07-01<=t<2026-10-01, diagnostic only. Evaluation events with future labels crossing a split boundary are censored for model selection/validation; no TRAIN target can include VALIDATION future bars. Select a single config using TRAIN only; never tune against VALIDATION/AUDIT. Prefer configs meeting all TRAIN gates; among those minimize median symbols/day, then maximize10X+ recall, then5X+ recall, then lexicographic config ID. If none meet gates, choose highest minimum normalized recall subject to noise gate; if none satisfy noise, report NEEDS_CALIBRATION without a winner for forward. Frozen48 configs are exhaustive; no ad hoc retry grid.

## Metrics and acceptance

For each event, candidate first time is earliest activation in [anchor_time-24h,peak_time], same venue/symbol. Report first candidate multiple=close(candidate_time)/anchor_price and lead hours to each threshold/peak. A pre-hit requires first candidate at or before the first2x crossing; negative lead is a late hit and is not a pre-hit. Keep late-hit and never-hit counts separately. Main recall=pre-hit/event_count. Report fractions triggered strictly before1.25/1.5/2/3/5 price crossings, each with explicit denominator; no crossing meansN/A.

Primary cohorts: >=5x, >=10x, >=20x separately; also exact tiers, venue, current-listed/historical-not-current,new-listing/old-shell/unknown-age. Gate: >=5x pre-hit recall>=85%, >=10x pre-hit recall>=90%, >=70% of >=10x events first-trigger strictly before2x, median unique candidate symbols/day<=30, p95<=60. Require at least10 eligible>=10x events in VALIDATION; fewer means MONSTER_D1_INSUFFICIENT_DATA, not PASS. Report event counts and uncovered/censored symbols; a covered-subset gate is not full-universe acceptance.

Noise counts include all eligible calendar days, including zero-candidate days; report candidates/day,episodes/day,unique symbols/day,p95,max. Forward24h/72h/7d candidate non-2x rates require complete subsequent horizon; incomplete horizons are CENSORED and excluded with their count reported. Quantiles use nearest-rank forp95; median ordinary sorted midpoint. Largest misses rank by event peak multiple descending thenID. Largest noise candidates rank by preceding activation return descending thenID. Retain all misses/noise; English explanations may not changeGT.

D2 begins only after D1 acceptable gate. Real derivative endpoints are then tested only forD1 candidate symbols. D3 requires at least2h manual real scanner1–5min with queue/private test transport, restart/dedupe/hash/75KB/item budget, requests/failure/stale/CPU/RSS metrics. No launchd, automation, Gmail or investment alerts.

MONSTER_GT_V1_FREEZE_COMMIT is the commit containing this specification, resolved and recorded in private evidence and FM2 report after commit/push. No full-universe event discovery may run before that remote identity is verified.
