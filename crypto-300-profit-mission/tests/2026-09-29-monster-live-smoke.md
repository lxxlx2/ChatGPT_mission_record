# Monster V2.1 Live Smoke Test — 2026-09-29

Status: PASS_FOR_RUNTIME_PATH
Live state mutated: no
Model thresholds changed: no

## Bulk screen
Current Binance USD-M 24h ticker call:
- total symbols returned: 780
- eligible liquid USDT symbols with quoteVolume >= 10M USDT: 204
- strongest current movers included:
  - NMRUSDT +28.487%, quote volume ~265.0M
  - ARXUSDT +24.203%, ~21.5M
  - CRVUSDT +22.154%, ~106.2M
  - HBARUSDT +20.108%, ~1.029B
  - MARSCOINUSDT +19.795%, ~227.7M
  - MUBARAKUSDT +18.424%, ~108.8M
  - 0GUSDT +17.143%, ~62.8M

Bulk universe path: PASS.

## Five-symbol deep-check smoke
This smoke intentionally used the new max-5 runtime budget:
- four historical deferred controls: RUNE, IN, W, DASH
- one current top mover: NMR

Latest completed-hour objective metrics:

| Symbol | breakout vs prior-24h high | 6h | 3h volume mult | 3h taker buy | funding | OI window | Current IGNITION |
|---|---:|---:|---:|---:|---:|---:|---|
| RUNEUSDT | -2.53% | +0.14% | 1.00x | 52.63% | +0.0100% | -1.40% | NO |
| INUSDT | -2.71% | +0.03% | 0.70x | 38.97% | +0.0105% | -1.88% | NO |
| WUSDT | -0.34% | +6.07% | 0.95x | 51.08% | +0.0050% | +7.43% | NO |
| DASHUSDT | -9.06% | -5.90% | 1.07x | 49.37% | -0.0018% | +0.16% | NO |
| NMRUSDT | -17.25% | -6.60% | 4.86x | 48.69% | -0.1974% | -3.01% | NO |

The test proves:
- one bulk screen can enumerate the liquid universe;
- five deep checks can complete inside the manual test budget;
- old deferred candidates can be explicitly terminally classified instead of silently disappearing;
- strong 24h movers are not automatically promoted when V2.1 ignition gates fail;
- frozen model thresholds are unchanged.

## Regression mapping
- MON-01 full universe: PASS
- MON-02 deep-check or deferred accounting: PASS by new rule, live scheduler proof pending
- MON-03 reserve >=2 old deferred: PASS in smoke
- MON-04 max-5 path: PASS
- MON-05 terminal result requirement: PASS by rule
- MON-06 BTW starvation fixture: PASS by regression rule
- MON-07 coverage-count schema: PASS by rule; scheduler artifact pending
- MON-08 19:29 daily coverage artifact: PENDING next real 19:29
- MON-09 frozen thresholds: PASS

No Monster alert was sent because this was a regression smoke and no tested symbol satisfied IGNITION.
