# ETH Conditional Perpetual Plan

Updated: 2026-09-26 07:52 Asia/Bangkok

## Current decision
NO MARKET ENTRY at the current ~2685 area.

The Sep-25 options-expiry one-shot task completed but its conclusion was not persisted to the Mission report. That persistence failure is now treated as a monitoring QA defect. ETH is folded into the hourly Mission monitor.

## Current Binance USDⓈ-M snapshot
Fresh public market data:
- mark: ~2685.23;
- 24h range: 2666.00 to 2742.66;
- 24h change: about -0.10%;
- current funding reference: about +0.0074% per 8h;
- current OI: ~2.266M ETH;
- OI has drifted down from roughly 2.288M in the recent 12h window;
- broad-account long/short ratio: ~2.71;
- top-trader position long/short ratio: ~1.68;
- top-trader account ratio: ~1.54;
- latest completed 1h taker buy/sell ratio: ~0.70.

Interpretation:
- long positioning is crowded;
- funding is positive but not extreme;
- recent taker flow is sell-heavy;
- OI is not confirming a fresh leveraged breakout;
- price is inside the recent range after rejection from 2742.66.

Therefore chasing a long near 2685 is not justified.

## Mission capital
ETH reserve remains up to 100 USDC, split 50 + 50.
Use isolated margin. Default leverage ceiling for this plan: 3x.

## Setup A — pullback long, preferred
Only arm after price trades into 2648-2662 and then reclaims/holds >=2665 on a completed 15m/1h structure with taker flow improving.

First bullet:
- margin: 50 USDC;
- leverage: 3x isolated;
- target entry: 2655-2665 after reclaim confirmation;
- hard stop: 2622;
- TP1: 2698;
- TP2: 2738.

Second 50 USDC bullet only after:
- price holds above 2698/2705;
- OI is stable/rising instead of falling;
- taker-buy ratio is >1 on confirmation.

Do not average down below the hard stop.

## Setup B — breakdown short
Only consider if a completed 1h candle closes below 2660 and the next reclaim attempt fails, preferably with OI rising or sell-side taker dominance continuing.

- margin: 50 USDC;
- leverage: 3x isolated;
- entry zone: 2650-2660 after failed reclaim;
- hard stop: 2689;
- TP1: 2628;
- TP2: 2595.

This is secondary to Setup A and must not coexist with a long.

## Breakout rule
Do not chase an upside breakout unless a completed 1h close establishes above 2743 and the breakout has both:
- taker buy/sell >1.05;
- OI rising >=1% versus the prior hour.

If qualified, create a fresh plan before entry. Do not automatically reuse old 2810/2760 rules.

## Hourly alerts
Notify immediately only when:
- Setup A becomes fully qualified;
- Setup B becomes fully qualified;
- breakout qualification above 2743 is confirmed;
- a planned setup is invalidated before entry;
- after entry, stop/TP or material leverage stress triggers.

No setup = GitHub only, no hourly user notification.
