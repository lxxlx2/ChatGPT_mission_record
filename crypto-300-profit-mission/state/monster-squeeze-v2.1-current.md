# Monster Squeeze V2.1 Current State

Updated: 2026-09-28 Asia/Bangkok
Model: frozen V2.1

## Durable active candidates

### QNTUSDT
- first_seen: 2026-09-27 12:34 Asia/Bangkok
- setup_price: **188.83655035**
- current_state: **PRESSURE**
- expiry: 2026-10-04 12:34 Asia/Bangkok
- 24h change: **+89.79%**
- completed 1h close vs prior-24h high: **-3.12%**
- 6h change: **+32.06%**
- latest 3h quote-volume / prior hourly median: **9.19x**
- representative 3h taker buy: **49.80%**
- funding: **-0.038663%**
- ~6h OI value change: **+85.12%**
- IGNITION: **NO**
- failed gates: breakout; taker-buy; newly persisted setup-price +5% gate cannot be satisfied at first_seen

Rationale: extreme price/volume/OI expansion plus negative funding creates factual squeeze pressure, but completed-hour breakout and taker-buy confirmation are absent.

### SOONUSDT
- first_seen: 2026-09-27 12:34 Asia/Bangkok
- setup_price: **0.3062**
- current_state: **PRESSURE**
- expiry: 2026-10-04 12:34 Asia/Bangkok
- 24h change: **+49.10%**
- completed 1h close vs prior-24h high: **+4.92%**
- 6h change: **+33.75%**
- latest 3h quote-volume / prior hourly median: **66.22x**
- representative 3h taker buy: **49.75%**
- funding: **+0.036309%**
- ~6h OI value change: **+63.07%**
- IGNITION: **NO**
- failed gates: taker-buy; newly persisted setup-price +5% gate cannot be satisfied at first_seen

Rationale: extraordinary volume/OI expansion and strong price momentum meet pressure-style leverage/volume conditions, while taker-buy confirmation is absent and funding is already positive.

## Rejected / deferred current shortlist

### QUSDT
- 24h: +83.01%
- completed 1h close vs prior-24h high: -20.71%
- 6h: -0.89%
- 3h volume multiplier: 1.79x
- taker buy: 50.12%
- funding: +0.107521%
- ~6h OI value change: +5.99%
- current result: no PRESSURE/IGNITION promotion; structure is currently post-spike / failed-continuation-like.

Due to max-3 deep-check rule, current liquid movers not deep-checked in this recovery include:
- RAREUSDT +48.99%
- USUSDT +45.14%
- RUNEUSDT +23.60%
- BTWUSDT +17.39%
- INUSDT +15.94%
- WUSDT +15.71%
- DASHUSDT +15.50%

These are shortlist carry-forward only. No state is invented without deep checks.

## Current recovery scan

Bulk screen:
- Binance USD-M liquid symbols with >=10M USDT 24h quote volume
- strongest sampled: QNT, Q, SOON, RARE, US, RUNE, BTW, IN, W, DASH

Deep-check count: **3**
- QNT: PRESSURE
- Q: rejected
- SOON: PRESSURE

Current confirmed IGNITION count: **0**
Current relevant EXHAUSTION alert count: **0**

No immediate Gmail/ChatGPT Monster alert is required from this recovery scan.

## Historical context

2026-09-26 23:31 automatic full screen:
- universe_checked: 727 Binance USD-M symbols
- shortlist: QUSDT, USUSDT, RAREUSDT, BRUSDT, SAGAUSDT
- new IGNITION: none confirmed
- relevant EXHAUSTION: none newly confirmed

The 2026-09-27 01:18 manual QA also found no confirmed IGNITION among the sampled leaders at that time.

## Rules retained

- Parameters remain frozen V2.1.
- Setup prices are persisted at first confirmed STRUCTURAL/PRESSURE state and are never reconstructed retroactively.
- A new candidate cannot satisfy the price >= setup_price x1.05 gate at its first_seen snapshot.
- PRESSURE remains GitHub/daily-summary state unless another factual immediate-alert gate is met.


## Recovered missed-candidate state

### BTWUSDT — recovered current watch
- historical first shortlist observation: **2026-09-27 12:34 Asia/Bangkok**
- historical shortlist snapshot: **+17.39% 24h**
- historical status: deferred by max-3 deep-check cap, then lost because no durable deferred queue existed
- historical alert audit: **MISSED_ALERT / NOT_BACKFILLED_AS_IGNITION**
- current reference mark: **~1.2825**
- current 24h futures change: **+12.23%**
- current 24h futures quote volume: **~247.2M USDT**
- current futures OI value: **~153.8M USDT**
- current account long/short ratio: **~0.61** (~62% short accounts)
- current top-trader position long/short ratio: **~2.02**
- current funding: **+0.0181% per 4h**
- current state for forward monitoring: **PRESSURE**
- new forward setup price: **1.2825**
- new forward first_seen: **2026-09-28**
- forward expiry: **2026-10-05**
- current IGNITION: **NO**, because latest completed hour is post-spike and fails breakout / 6h momentum gates

Retrospective objective-gate evidence:
- 2026-09-28 13:00 Bangkok: breakout +1.45%; 6h +11.44%; volume 4.60x; 3h taker buy 52.45%.
- 2026-09-28 14:00 Bangkok: breakout +3.97%; 6h +15.52%; volume 7.29x; 3h taker buy 53.15%.

Do not invent a historical setup price or backfill IGNITION. Track BTW prospectively from the new 1.2825 setup.


## Runtime health index — 2026-09-28 19:22

last_successful_full_scan_at: **2026-09-28 19:22 Asia/Bangkok** (manual health-check)
liquid_universe_24h_quote_volume_ge_10m: **226 symbols**

Current manual deep-check:
- RAREUSDT: rejected / post-spike; breakout -24.85%, 6h -9.63%, volume 0.63x, taker buy 48.39%, OI ~-20.20%.
- QNTUSDT: prior PRESSURE now failed-continuation / exhaustion-like; breakout -36.82%, 6h -11.36%, volume 1.98x, taker buy 50.09%, OI ~-6.98%.
- HBARUSDT: **PRESSURE candidate**; close 0.11739, breakout -0.63%, 6h +20.80%, volume 26.52x, taker buy 49.81%, funding -0.001788%, OI ~+74.92%. New setup_price **0.11739**.
- MARSCOINUSDT: shortlist/deferred; close 0.15037, breakout -5.49%, 6h +17.73%, volume 3.57x, taker buy 50.15%, OI ~+27.93%.
- BTWUSDT: forward PRESSURE remains; latest completed-hour breakout -12.06%, 6h -4.98%, volume 5.85x, taker buy 50.48%, OI ~+3.70%.

No current IGNITION in this sampled health-check.

### Durable DEFERRED_SHORTLIST

Old carry-forward candidates from 2026-09-27 are retained until checked:
- USUSDT — historical first_seen 2026-09-27 12:34; setup_price unavailable_historical; next_due immediate.
- RUNEUSDT — historical first_seen 2026-09-27 12:34; setup_price unavailable_historical; next_due immediate.
- INUSDT — historical first_seen 2026-09-27 12:34; setup_price unavailable_historical; next_due immediate.
- WUSDT — historical first_seen 2026-09-27 12:34; setup_price unavailable_historical; next_due immediate.
- DASHUSDT — historical first_seen 2026-09-27 12:34; setup_price unavailable_historical; next_due immediate.
- MARSCOINUSDT — first_seen 2026-09-28 19:22; setup_price 0.15037; next_due next Monster scan.

RAREUSDT has now been deep-checked and is removed from deferred state.

19:29 remains a mandatory full screen even though this manual health-check occurred seven minutes earlier.


## Full scan 2026-09-29 12:33 Asia/Bangkok
- last_successful_full_scan_at: **2026-09-29 12:33 Asia/Bangkok**
- liquid_universe_24h_quote_volume_ge_10m: **233 symbols**
- top movers included NMR +37.601%, MARSCOIN +28.882%, HBAR +23.795%, US +18.611%.
- deep-checks: USUSDT (oldest deferred), MARSCOINUSDT, HBARUSDT.
- USUSDT: no IGNITION; historical setup_price unavailable, so setup-price gate cannot be fabricated.
- MARSCOINUSDT: no IGNITION; current mark 0.15880878, latest completed 1h close 0.15015 remains below prior-24h high.
- HBARUSDT: PRESSURE retained; current mark 0.11744, latest completed 1h close 0.12042 remains below prior-24h high.
- confirmed IGNITION: **0**
- relevant EXHAUSTION: **0**
- DEFERRED_SHORTLIST remains durable for unchecked carry-forward symbols; USUSDT is now checked and may be removed from oldest-deferred priority.
