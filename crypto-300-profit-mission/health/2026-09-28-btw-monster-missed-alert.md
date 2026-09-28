# BTW Monster V2.1 missed-alert incident

date: 2026-09-28
timezone: Asia/Bangkok
status: confirmed_monitoring_gap

## What happened

The Monster scanner did see BTW.

At 2026-09-27 12:34 Asia/Bangkok, the persisted Monster recovery state listed:
- BTWUSDT +17.39% 24h
- BTW was in the current liquid-mover shortlist
- deep-check was deferred because only 3 new symbols were allowed and QNT/Q/SOON consumed all slots

The runtime failed to persist BTW into a durable deferred-candidate queue.

After that, multiple automatic Mission runs reported:
- monster_due: false
- monster_status: not_due

No later full scan/deep-check recovered BTW before the move accelerated.

## Retrospective market data

Official Binance futures hourly data shows objective market gates, excluding the persisted setup-price gate, were simultaneously satisfied at least twice:

2026-09-28 13:00 Asia/Bangkok completed hour:
- close 1.3637
- prior-24h breakout +1.45%
- 6h gain +11.44%
- 3h quote-volume multiplier ~4.60x
- 3h taker-buy ~52.45%

2026-09-28 14:00 Asia/Bangkok completed hour:
- close 1.4243
- prior-24h breakout +3.97%
- 6h gain +15.52%
- 3h quote-volume multiplier ~7.29x
- 3h taker-buy ~53.15%

The prior shortlist period traded around 1.05-1.06. Both later closes were far above +5% from that observed region.

Frozen-model policy forbids reconstructing a historical setup_price, so no historical IGNITION state is fabricated.

## Root cause

1. max-3 deep-check cap had no starvation-safe carry-forward queue;
2. deferred symbols were informational text only, not durable state;
3. later scheduler cycles incorrectly marked Monster not_due instead of using elapsed time since last successful full scan;
4. alerting therefore never reached BTW despite later qualifying market behavior.

## Fix

- persist every deferred shortlist symbol;
- reserve >=1 slot per due scan for oldest deferred;
- due when >=3h since last successful full scan;
- 19:29 full scan remains mandatory;
- BTW is now tracked prospectively from setup_price 1.2825 as PRESSURE.
