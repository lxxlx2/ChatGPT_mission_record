# Monster Squeeze V2.1 Current State

Updated: 2026-09-27 12:34 Asia/Bangkok
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
