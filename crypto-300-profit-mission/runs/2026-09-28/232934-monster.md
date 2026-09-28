run_time: 2026-09-28T23:29:34+07:00
monster_due: true
reason: last_successful_full_scan_at 2026-09-28 19:22 Asia/Bangkok; elapsed > 3h
bulk_source: Binance USD-M 24h ticker
universe_count: 780
liquid_universe_quoteVolume_ge_10m: 216
deep_check_count: 3
deep_checked:
  - USUSDT: oldest durable deferred; no persisted setup_price; IGNITION impossible under frozen V2.1 setup-price gate; remains checked_without_ignition
  - HBARUSDT: persisted PRESSURE setup_price 0.11739; current 24h +36.729%; latest completed-hour close 0.12549; price gate >= setup*1.05 satisfied; full IGNITION not confirmed because completed-hour breakout/taker aggregate gates are not all confirmed
  - MARSCOINUSDT: persisted deferred setup_price 0.15037; current 24h +23.776%; latest completed-hour close 0.14450; setup-price +5% gate failed; no IGNITION
top_liquid_movers: HBARUSDT +36.729%; QNTUSDT +25.060%; MARSCOINUSDT +23.776%; AZTECUSDT +18.650%; ALGOUSDT +15.994%
ignition_count: 0
relevant_exhaustion_count: 0
notification: none
last_successful_full_scan_at: 2026-09-28 23:29 Asia/Bangkok
note: max-3 deep-check budget enforced; remaining unexamined shortlist must remain deferred in durable Monster state on next state persistence
