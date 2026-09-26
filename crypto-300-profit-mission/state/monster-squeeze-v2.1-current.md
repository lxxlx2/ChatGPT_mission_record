# Monster Squeeze V2.1 Current State

Updated: 2026-09-27 01:18 Asia/Bangkok
Model: frozen V2.1

## Latest persisted automatic result

2026-09-26 23:31 Asia/Bangkok:
- universe_checked: 727 Binance USD-M symbols
- bounded shortlist: QUSDT, USUSDT, RAREUSDT, BRUSDT, SAGAUSDT
- new IGNITION: none confirmed
- relevant EXHAUSTION: none newly confirmed

## 2026-09-27 manual repair/QA screen

Bulk 24h liquid movers included:
- RARE +44.32%
- QNT +26.72%
- US +22.32%
- MARSCOIN +21.70%
- KMNO +19.97%
- 2Z +19.91%
- WLD +17.44%
- RUNE +16.53%

Deep V2.1 gate checks on strongest sampled candidates:

| Symbol | 1h close vs prior-24h high | 6h | 3h vol / prior median | 3h taker buy | latest funding | IGNITION |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| RARE | -7.67% | +2.95% | 3.19x | 50.4% | -0.5330% | NO |
| QNT | -1.43% | +18.63% | 5.79x | 52.8% | +0.0100% | NO |
| US | -15.33% | +13.54% | 13.72x | 48.2% | +0.0871% | NO |
| MARSCOIN | -0.74% | +24.05% | 6.33x | 49.8% | +0.0050% | NO |
| 2Z | -11.26% | -0.47% | 7.04x | 49.2% | -0.4349% | NO |
| SAGA | -29.49% | -3.15% | 0.67x | 48.4% | -0.0194% | NO |

Current result: **no confirmed V2.1 IGNITION** in the sampled leading candidates.

Notes:
- QNT and MARSCOIN have strong 6h/volume momentum but fail the breakout gate; MARSCOIN also fails the taker-buy gate.
- RARE has unusually negative funding and expanded volume, but fails the 6h and breakout gates and is not a confirmed IGNITION.
- SAGA remains in post-squeeze/cooldown structure.

No setup_price is retroactively invented from old runs. Future STRUCTURAL/PRESSURE candidates must persist first_seen/setup_price here so the frozen `price >= setup_price x1.05` gate can be evaluated audibly.
