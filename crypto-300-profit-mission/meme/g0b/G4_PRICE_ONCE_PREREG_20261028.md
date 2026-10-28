# Frank G4 one-shot historical price coverage — preregistration (2026-10-28)

**Owner consent:** the user approved proceeding with the previously proposed one-time **limited free historical-price evidence collection** for the five preidentified signal examples plus one biased no-signal control. This fixed protocol is written and committed BEFORE any new provider GET requests. No new market feed, scheduled job, production read, private Mac data, RPC provider, notification, or trading.

## Purpose and endpoints

Answer only: can a **price-proxy** be anchored at the **actual formal MULT time** for HcRL, PerPs, Hg5, or at **ACC and Frank's documented early exit** for 8K5, E4Ap? C3 no-signal negative proxy control is retained regardless of provider coverage.

- Provider: **public keyless GeckoTerminal API**, `https://api.geckoterminal.com/api/v2`. Not Solana RPC; no paid key; no private credentials.
- Exactly two path patterns: `/networks/solana/tokens/{frozen-mint}/pools?page=1` and `/networks/solana/pools/{selected-pool}/ohlcv/minute`.
- **Hard cap 18 HTTP GET attempts**: six pool discoveries + at most two 1m OHLCV queries per case; no retries, no redirect, no pagination, no silent alternative providers. HTTP 429/auth/paywall/server/network/schema failures STOP; no automatic resumption. Sequential requests spaced **>=12.5 seconds**, max 4.8/min in steady state; finite 22s individual timeout, 15 minute workflow maximum.
- Pool is selected by frozen deterministic rule: first page of pools **currently ranked** by provider, oldest of those pre-existing before relevant signal, exact frozen Mint paired with USDC/WSOL; explicitly subject to **survivorship/selection bias**. Validate pool address before any OHLCV call.
- OHLCV minute `aggregate=1,currency=usd,include_empty_intervals=false`, token side pinned by pool identity. Entry query target through T0+3600s and the exit query target through exit+180s. No fallback if missing. Keep all raw JSON and HTTP status/response SHA256 in a run artifact.
- All cases are fixed by `g4_price_one_shot.py` importing the hash-verified archived M3 study (blob `a31a2bbcd1fe7c70951152f2a23edca6c934dc40`), original G0-B manifest, and hash-verified selected root-lot evidence (blob `b44cc2140927246f9a428c8c455a6793eb80b662`).

| ID | Frozen mint prefix | Entry anchor | Exit target | Primary question |
|---|---|---|---|---|
| M2 | HcRL | **formal MULT** 2026-09-06 21:29:00 UTC | MULT+24h | Historical actual MULT lag price coverage |
| M3 | PerPs | **formal MULT** 2026-09-12 18:29:00 UTC | MULT+24h | Whether ACC+300s +118% proxy is misleading for MULT |
| M4 | Hg5 | **formal MULT** 2026-09-14 18:29:00 UTC (earlier episode) | MULT+24h | Candle availability and tiny-volume risk |
| A2 | 8K5 | ACC 2026-09-08 02:42:17 UTC | Documented Frank final exit 2026-09-08 04:27:36 UTC | Early Frank-exit proxy vs wrong 24h exit |
| A3 | E4Ap | ACC 2026-09-11 03:24:02 UTC | Documented Frank final exit 2026-09-11 03:47:54 UTC | Short holding window; lag beyond exit invalid |
| C3 | H1kX | Reconstructed no-signal BUY 2026-09-08 17:18:20 UTC | BUY+24h | **Biased**, negative/illiquid reference; not representative |

Lag ladder frozen for each case: **30, 120, 300, 900, 3600 seconds** after its actual entry anchor. A lag at/after the precommitted exit is `ENTRY_AT_OR_AFTER_EXIT`, not a profit/zero. The next **minute candle starting at/after** target and within 180 seconds, with nonzero minute volume, provides a **future-known close-price proxy**. If its close time is at/after the exit anchor, reject it. Missing candles, unranked pools, zero-volume bars and non-executable depth remain explicit missing, never forced to fill.

## Evidence grade and decision

- A price-relative percentage `(exit_close / entry_close - 1)*100` is **gross candle-close proxy only**; its entry and exit prices are *not* actual executable quotes or Frank's lot prices.
- 1m trading volume is only a contextual indicator. No user trade amount is assumed. No router execution, historic market impact, gas/priority fee/slippage, LP reserves at time, fill failures or exit depth are measured.
- **No strategy GO/NO-GO inference** can follow from this selected in-sample six-case check. Outcomes must keep missing cases. All time-to-first-availability and true notification delay remain unverified.
- Results are reviewable even if the request stream fails early: one artifact retains raw responses, attempt ledger, sample clocks and nulls. An empty/partial artifact is not a PASS.
- One **path-filtered push** to *this dedicated branch when the workflow file is created* is the sole executor; there is **no schedule, workflow_dispatch, cron, auto retry, or automatic continuation**. No second workflow-file change without new authorization.

**Disposition:** `ONE_SHOT_RESEARCH_PERMISSION_ONLY / 18_GET_ATTEMPT_HARD_LIMIT / NO_PRODUCTION / NO_NOTIFICATION / NO_TRADE`.
