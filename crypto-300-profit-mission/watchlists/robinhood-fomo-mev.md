# Robinhood / FOMO execution-flow watch

Updated: 2026-09-26
Status: active research and execution-risk filter
Chain ID: 4663

## Seed addresses
- 0xb49deec1a52eea46f3a6a158f8f9b155809b8c44
- 0x44c0ba0b734d4b7705fcd07ddae9fbbc078d74dd
- common observed execution contract: 0x68a04a63Fd1d8EAbF167EF48ed0A0EF06c2374d9

## Baseline observations
On 2026-09-25, two rapid round trips were verified on chain:
- Protocol: about 1,000 USDG out and 1,065.421329 USDG back, gross difference about 65.42 USDG.
- EARNED: about 579.942580 USDG out and 609.717726 USDG back, gross difference about 29.78 USDG.

The wallet/operator identity and information source remain unverified.

## Monitoring fields
For each rapid round trip record:
- time and block
- wallet
- token and contract
- stablecoin out/in
- token amount
- nearby independent buyers
- estimated third-party notional
- gross difference and fees
- pool liquidity
- price at exit
- forward return at 30s, 1m, 5m and 15m
- net flow after exit
- cluster-link evidence
- confidence

## Calibration
Collect at least 30 complete observations across at least 10 tokens before using the signal as a standalone positive-entry factor. Before that threshold, use it mainly as an execution-cost and risk filter, or as supporting evidence for an independently valid Mission candidate.

## Risk threshold
Flag a candidate as execution-toxic when there are at least 3 relevant rapid round trips in 10 minutes with average observed extraction of at least 4%, or estimated user entry slippage exceeds 5%.

All positive trade candidates still require the normal Mission identity, venue, liquidity, downside and expected-value checks.
