# G4 PR #239 — exit-side causal correction, no provider requery

**Review disposition:** `REQUEST_CHANGES` at legacy HEAD `ac81a40666a7196144eb0f168099251a9637abe9`. Do not approve the original numerical price proxy table; legacy public price run #40663663748 and original first offline audit #40664687654 remain immutable records of the original rule, **not** repaired outputs.

## Demonstrated bug

Legacy `g4_price_one_shot.py` uses `close_proxy(exit_bars, exit_time)` whose selected exit bar **starts at or after** the precommitted exit anchor and closes 60–180 seconds AFTER that anchor. The previous implementation guarded only the ENTRY close against future exit-time knowledge. All 16 of 16 non-null legacy price proxy rows were thus calculated using an exit bar that was not yet completed at the declared exit decision time.

The preregistration `G4_PRICE_ONCE_PREREG_20261028.md` is immutable. Its condition requiring a candle close known before the exit anchor is interpreted **strictly**: `exit_price_known_at < exit_target`. The old query's next-at/after exit bars violate this. Reproducing old numbers with the same rule does **not** constitute an independent causal validation.

## Fixed analysis policy

Two clearly separated lanes:

1. **Primary, immutable preregistration**: keep the original input, selected pool, six cases, time anchors, 30 lag rows and HTTP receipt unchanged. A non-null price result requires (a) an eligible ENTRY bar, (b) its close known before exit, and (c) an eligible EXIT bar whose close was known **strictly before** the exit anchor. A future-known exit close is `EXIT_CANDLE_KNOWN_AFTER_EXIT` with `gross_candle_close_proxy_pct = null`. Do not claim even a price-proxy return when this fails. The original query's exit-next-bars invalidate all 16 previously non-null rows.
2. **Secondary exploratory sensitivity (NOT preregistered)**: separately choose the **latest positive-volume 1-minute close strictly before** the exit anchor, from the ORIGINAL stored raw exit OHLCV only; reject if the close is more than 180 seconds stale, missing or after/at anchor. Preserve the same original entry-bar rule with its future-known price caveat. Label every derived numeric result `RETROSPECTIVE_PREANCHOR_CLOSE_SENSITIVITY_ONLY`, never `PRIMARY`, `EXECUTABLE` or `ACTUAL_FOLLOWER_PNL`. Record both entry and exit candle minute volume, relative staleness and true trigger clocks.

Both lanes use only existing GitHub Artifact #12805017729 from run #40663663748. `g4_raw_artifact_reaudit.py` replays the original legacy status, recomputes strict causality **independently of the strategy code** and calculates secondary sensitivities. A separate offline-only workflow must run current tests and this raw replay. No GeckoTerminal, Solana RPC, wallet, Mac production data, trade, monitoring, notification or service code may be invoked.

## Acceptance gate

- Test the explicit counterexample that old code could return +100% using an exit candle known 60 seconds AFTER exit; now returns `EXIT_CANDLE_KNOWN_AFTER_EXIT` and null.
- Validate the 180-second positive-volume pre-anchor selector and reject at/after anchor and stale bars.
- Verify all 30 rows against raw receipt, 16 previously non-null values flagged, all primary strict outcomes null under the original fixed next-candle selection, with secondary analysis separately tabulated and not counted as primary.
- Preserve legacy report with prominent `SUPERSEDED / REQUEST_CHANGES` note; publish corrected report with fixed SHA, explicit old vs new price semantics, exact case-by-case results, low-volume warnings and `STRATEGY_NEED_MORE_DATA`.
- **Do not rerun the original external API workflow or reuse its request allowance.** A new offline-only workflow can download the original artifact using GitHub read-only `actions: read` and upload revised calculations.

**Key distinction:** A pre-anchor historical close is more causally conservative, but still is not a fill at the actual exit, and the user has not supplied an execution amount. Any positive proxy remains exploratory; `VERIFIED_EXECUTABLE_FOLLOWER_QUOTES = 0`.
