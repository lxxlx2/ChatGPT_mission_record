# Frank wallet replay methodology and latency objective

Date: 2026-09-29 Asia/Bangkok
Wallet: `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`

## Correction to the first test

The first Gmail test using STONK was intentionally a **single positive-control delivery test**:
- objective: prove Gmail send -> Sent label -> message-id readback;
- it was not an exhaustive 30-day rule replay;
- therefore one STONK email was expected by that test design;
- the result cannot be used to claim no historical alerts were missed.

A recall test must enumerate all eligible tokens/signals.

## Exhaustive replay definition

For a selected historical window:
1. enumerate all active DEX/aggregator swaps initiated by Frank;
2. exclude transfers, airdrops, creator rewards, claims, mint events and unsolicited receipts;
3. reconstruct each mint's chronological position, gross buys, gross sells, net exposure and Frank VWAP;
4. simulate only information available at each historical timestamp;
5. simulate the actual hourly :29 observer;
6. apply HFT/WATCH/FORMAL_ENTRY/FORMAL_EXIT/STALE rules;
7. output every detected FORMAL signal, plus every rejected candidate with reason.

Metrics:
- T0 first meaningful accumulation;
- first WATCH time;
- FORMAL_ENTRY time;
- latency from T0;
- price / Frank VWAP at alert;
- current MC at alert if available;
- 1h, 3h, 6h, 24h and 7d forward return;
- maximum favorable excursion and maximum adverse excursion;
- whether 3x or 5x was reached after the alert;
- false-positive and missed-opportunity controls.

Historical replay should produce one complete summary, not one email per historical signal.

## Live target

Reference lane capital: about $100.

Latency target:
- desired first alert: 45-120 minutes after T0;
- routine first alerts >3h are considered too late;
- late exception only with fresh Frank buying and price <= Frank VWAP +5%.

Risk / sizing reference:
- initial 20-30 USD;
- second 20-30 USD only if next observation remains qualified and price is below the do-not-chase level;
- normal per-token cap 50-60 USD.

## Current control observations

STONK exact mint:
`6GmAFSYs4gk3FDao5FzzySQpPZaWsa4rUJHacpMpUNgx`

Frank's current historical token account:
`HHytPmmCDBKPmRtYvteWSkY7NWwXvaeP1t1KKingReMQ`

Direct-chain history confirms extensive STONK activity. In the 30-day window, the token account already had activity at 2026-09-03 21:47:53 Bangkok, and confirmed active STONK sells occurred around 23:28 and 23:46 Bangkok. This demonstrates why a rule that always waits multiple extra scheduler cycles can become too slow.

Public wallet snapshots also show:
- STONK as a multi-day, many-buy conviction position;
- single-buy probes can produce both very large gains and near-total losses;
- rapid multi-buy/multi-sell positions can be execution/HFT noise.

Therefore persistence should be measured from chain history, not only from the count of scheduler runs.
