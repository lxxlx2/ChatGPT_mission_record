# SAGA anomaly / squeeze-cycle watch

Added: 2026-09-26
Timezone: Asia/Bangkok
Parent mission: `crypto-300-profit-mission/MISSION_SPEC.md`

## Scope

Monitor Saga (`SAGA`) inside the existing $300 Crypto Profit Mission. This is a watchlist only, not a funded position and not a separate automation. Any new derivatives trade remains recommendation-only until the user explicitly approves capital allocation.

Primary venue:
- Binance spot: `SAGAUSDT`
- Binance USDⓈ-M perpetual: `SAGAUSDT`

Purpose:
- apply the frozen squeeze/anomaly model as a forward-test candidate;
- distinguish PRESSURE, IGNITION, EXHAUSTION and re-accumulation states;
- detect whether SAGA develops another MYX/ALPACA-style squeeze cycle or a long-crowding/spot-led manipulation cycle.

## Structural background

SAGA qualifies for monitoring because the live market structure is unusually leveraged relative to the token's small circulating market capitalization:
- circulating supply: approximately 416,505,429 SAGA;
- total supply reference: approximately 1.10B SAGA, with inflation / no hard max supply;
- current circulating market cap at the Binance price around the 2026-09-26 baseline: roughly 14-15M USD;
- Binance USDⓈ-M OI at the baseline: roughly 16.7M USD;
- CoinGlass aggregate futures OI reference at the same period: roughly 40.7M USD;
- aggregate derivatives activity is multiple times spot activity.

Project/context risk:
- Saga announced in July 2026 that its crypto business was sold and the chain moved to independent stewardship under Alapin Holdings / dao5-family ownership while Saga AI Labs pivoted toward AI;
- Bitget delisted SAGA/USDT spot on 2026-09-24;
- Binance removed SAGA/FDUSD on 2026-09-11, while SAGA/USDT remained available;
- SagaEVM entered a 60-day sunset on 2026-09-24, while Saga Mainnet continues.

These facts increase the "legacy shell / thin fundamental catalyst / derivatives-dominant" characteristics relevant to this Mission. They do not prove manipulation or coordinated control.

## Baseline cycle snapshot — 2026-09-26

Binance 1D/1H data:
- local cycle low: 0.01274 on 2026-09-09;
- cycle high: 0.09167 on 2026-09-25 00:00 UTC;
- low-to-high multiple: approximately 7.2x;
- screenshot/post reference price: approximately 0.0773;
- live baseline price when this watch was added: approximately 0.0351;
- drawdown from 0.09167 cycle high to baseline: approximately -61.7%;
- drawdown from the screenshot/post reference price to baseline: approximately -54.5%.

Leverage:
- Binance OI near cycle high: approximately 40.30M USD;
- Binance OI at baseline: approximately 16.71M USD;
- OI decline from peak: approximately -58.5%;
- current Binance OI is still roughly comparable to / above circulating market cap.

Funding:
- recent Binance funding remained positive around +0.005% per 4h throughout the observed top / crash window.
- Therefore the observed 2026-09-25 blow-off is NOT classified as the canonical "negative-funding short squeeze" pattern.

Positioning:
- top-trader position long/short ratio near the cycle high: approximately 3.69, about 78.7% long;
- top-trader position ratio at baseline: approximately 2.38, about 70.4% long;
- top-trader account ratio at baseline: approximately 1.49, about 59.8% long;
- broad account ratio at baseline: approximately 1.11, about 52.6% long.

Flow:
- latest complete 1h taker buy/sell ratio at the baseline was approximately 0.83, showing sell-side taker dominance;
- Binance 24h futures quote volume around the baseline: approximately 341M USDT versus approximately 65M USDT Binance spot quote volume;
- CoinGlass aggregate 24h futures volume reference: approximately 623M USD versus approximately 76M USD spot volume.

## Current classification

As of the 2026-09-26 baseline:

- STRUCTURAL CANDIDATE: **YES**
- PRESSURE under frozen V2.1 short-squeeze rules: **NO**
- IGNITION under frozen V2.1 rules: **NO**
- EXHAUSTION / post-liquidation cooldown: **YES / high confidence**

Reason:
- price completed a parabolic multi-day expansion;
- OI expanded into the high and then collapsed by roughly 58%;
- funding did not turn negative, so the move was dominated by long crowding / leveraged momentum rather than classic short-squeeze fuel;
- top traders remain materially net long even after the crash;
- current taker flow is weak / sell-dominant;
- the price has already retraced more than half from the cycle high.

Do not treat the screenshot's "early stage" claim as current state. At the screenshot price around 0.0773 the trade was already close to the blow-off phase.

## Frozen model monitoring

Keep the previously frozen V2.1 thresholds. Do not retune them specifically for SAGA.

### PRESSURE
Check:
- funding direction and change;
- OI growth versus price;
- top-trader positions/accounts;
- price resilience;
- spot/perp volume divergence;
- circulating market cap versus OI;
- taker buy/sell imbalance.

A classic squeeze PRESSURE state requires negative funding / leverage stress plus the existing V2.1 score gates.

### IGNITION
Only promote to confirmed IGNITION when the frozen V2.1 conditions are simultaneously satisfied after PRESSURE:
- 1h close > prior 24h high by >=1%;
- 6h price change >=+10%;
- latest 3h average quote volume >=1.5x the prior 24h median hourly quote volume;
- latest 3h taker-buy share >=51%;
- price >=105% of the PRESSURE setup price;
- available live OI / top-trader data support rather than contradict the signal.

### EXHAUSTION
Treat as high-priority risk when a squeeze/pump has already occurred and several of these appear:
- material price reversal from the local peak;
- OI contracts sharply after expanding into the high;
- funding normalizes / flips toward crowded longs;
- top-trader longs remain elevated while price weakens;
- taker flow turns persistently sell-dominant;
- spot volume cannot support the derivatives notional;
- repeated failure to reclaim the prior breakout structure.

The 2026-09-26 baseline already meets EXHAUSTION.

## Alert rules

Hourly Mission checks must include SAGA while this watchlist is active.

Stay silent for:
- ordinary +/-10% noise;
- generic social posts claiming a new high or "庄家";
- a single funding/OI anomaly with no model confirmation;
- repeated EXHAUSTION information already reported.

Notify through the Mission's normal Gmail + ChatGPT delivery only for a NEW material state transition:
1. confirmed V2.1 PRESSURE -> IGNITION;
2. a new post-cooldown accumulation / second-cycle setup that passes the frozen model and live OI confirmation;
3. a fresh EXHAUSTION transition after a new rally;
4. a major exchange/listing/delisting/security/network event that changes executable liquidity or downside;
5. an extreme derivatives imbalance that creates a concrete trade with explicit entry, invalidation, realistic slippage and a defined Mission capital source.

Do not automatically allocate capital. Any proposed SAGA trade must compete for the existing Mission opportunity capital and requires user approval.

## Required hourly fields

Record:
- spot and perp price;
- 15m / 1h / 4h / 24h returns;
- 24h spot and futures volume;
- Binance OI USD and 1h / 6h / 24h OI change;
- OI / circulating market-cap ratio;
- funding rate and settlement interval;
- broad long/short ratio;
- top-trader account and position ratios;
- taker buy/sell ratio;
- latest local 24h high/low;
- V2.1 state and state transition;
- whether notification gate was met.

## Evidence baseline

Primary market data: Binance public market/futures APIs.
Cross-exchange derivatives reference: CoinGlass.
Supply / unlock reference: CoinMarketCap / Tokenomist.
Project/exchange events: Saga / Saga AI Labs public statements, Binance official announcements, Bitget official announcements.

