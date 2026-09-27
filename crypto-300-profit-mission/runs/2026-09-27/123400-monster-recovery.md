# Monster V2.1 manual recovery scan

run_time: 2026-09-27 12:34 Asia/Bangkok
run_mode: manual_recovery_after_scheduler_gap
model: frozen V2.1
status: completed

bulk_filter: Binance USD-M USDT symbols with >=10M USDT 24h quote volume
top_liquid_movers:
- QNTUSDT +89.79%
- QUSDT +83.01%
- SOONUSDT +49.10%
- RAREUSDT +48.99%
- USUSDT +45.14%
- RUNEUSDT +23.60%
- BTWUSDT +17.39%
- INUSDT +15.94%
- WUSDT +15.71%
- DASHUSDT +15.50%

deep_checks: 3

QNTUSDT:
- state: PRESSURE
- setup_price: 188.83655035
- breakout: -3.12%
- 6h: +32.06%
- vol_mult: 9.19x
- taker_buy: 49.80%
- funding: -0.038663%
- OI_6h: +85.12%
- ignition: false

QUSDT:
- state: rejected_currently
- breakout: -20.71%
- 6h: -0.89%
- vol_mult: 1.79x
- taker_buy: 50.12%
- funding: +0.107521%
- OI_6h: +5.99%
- ignition: false

SOONUSDT:
- state: PRESSURE
- setup_price: 0.3062
- breakout: +4.92%
- 6h: +33.75%
- vol_mult: 66.22x
- taker_buy: 49.75%
- funding: +0.036309%
- OI_6h: +63.07%
- ignition: false

confirmed_ignition_count: 0
relevant_exhaustion_alert_count: 0
gmail: not_required
chatgpt_alert: not_required

The two new PRESSURE candidates are persisted with first_seen/setup_price. Deferred movers remain unclassified until a future bounded deep check.
