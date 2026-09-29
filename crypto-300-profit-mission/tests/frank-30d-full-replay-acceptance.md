# Frank 30D Full Replay Acceptance Spec

Status: OPEN / NOT YET COMPLETED
Date: 2026-09-29
Wallet: `498g1rVnFcnjBjpfw1xyqA1WvgQXUU8RWuELjxkjAayQ`

## Why this file exists

The current file `research/frank-wallet-30d-replay-2026-09-29.md` is explicitly a first-pass snapshot analysis. It does not satisfy the user's requirement to run the complete 30-day transaction history.

This acceptance spec is the definition of done for that requirement.

## Definition of done

The replay is complete only when:
1. every wallet signature in the 30D window has been paginated and accounted for;
2. every active DEX/aggregator swap has been classified chronologically;
3. every traded token has a per-token event timeline;
4. the historical hourly :29 observer has been simulated without future information;
5. all WATCH / PRECONFIRM / SUSPECTED_CONVICTION / HFT / STALE / rejected outcomes are emitted;
6. every filtered/rejected token that later achieved >=3x is explicitly listed;
7. every entry-like signal has T0, alert time, latency, Frank buy/VWAP, alert price, forward returns, MFE, MAE and Frank later sell/exit timing where data exists;
8. the requested high-market-cap/high-liquidity subset is separately summarized;
9. a single aggregate report states total active tokens -> WATCH -> PRECONFIRM -> SUSPECTED_CONVICTION -> HFT -> STALE -> rejected -> later >=3x misses;
10. the full replay has no hidden pagination/provider gap. Any unavailable block is a test failure, not an assumed no-action period.

## Historical delivery behavior

Historical replay is audit-only:
- no Gmail per historical token;
- no live stage mutation;
- no live cursor mutation.

Only the final aggregate replay report is stored.

## Current status

OPEN.

Existing artifacts are methodology/positive controls only and MUST NOT be described as a completed exhaustive 30D backtest.
