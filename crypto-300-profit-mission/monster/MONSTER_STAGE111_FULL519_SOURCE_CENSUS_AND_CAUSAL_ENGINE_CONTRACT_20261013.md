# Monster Stage111: all-519 source census and persistent D0 research implementation contract

Date: 2026-10-13 Asia/Bangkok. Scope: existing Draft PR #30 ONLY. This document adds an explicit source and causal engineering contract to the Stage111 plan. It does NOT assert a profitable or approved new strategy. Monster deployment / Gmail / autotrading remain NO_GO; Frank and the already installed Stage99 snapshot collector are unchanged.

## Frozen historical population, no cherry-picking

- Input 1: `monster/evidence/monster_stage83_all519_source_and_D1_result.jsonl`, exact Git blob `c76b3a137c8dbe56feed3a79a63adcc0752f5e2e`: 519 distinct (date, symbol), 28 prior D0 early>=5m historical 2x cases, original D1 represented in 305 rows, and 214 D0-only cases.
- Input 2: `monster/evidence/monster_stage110_real519D0_305D1_causal_confirm_states.json`, exact Git blob `314c0ee532b93dd24dbda4ec6a146e03ee2c5c1b`: 305 D1 outcomes, 214 D0-only, 11 missed original-early 2x cases. Stage110 rejected. Its future labels and post-D1 outcomes are EVALUATION ONLY.
- Input 3 for future minute replay: first-party Binance daily 1m ZIP with separately verified official CHECKSUM, using the existing `verified_1m_day` reader. Previously recorded first 48h receipts are source-prefix evidence, not proof of full 168h coverage.
- All six original exposed historical 7-day date windows remain research-only. They cannot become independent OOS because a new model is frozen today. If any source day, event identity, listing-time qualification, or minute sequence is unknown, mark `SOURCE_CENSORED` or `IDENTITY_UNKNOWN`; do not turn it into a losing trade or remove the D0 watch from the denominator.
- Preserve separate Spot/USDM/perpetual/TradFi/multiplier identity categories. No historical 30U/300U amount is treated as the current user-authorized notional.

## Source-census implementation requirement

Run a read-only all-519 census BEFORE extensive network replay:
1. Verify immutable Git-blob SHA1 for both inputs (this is distinct from publishers' ZIP SHA256).
2. Validate unique keys, fixed 519 / 305 / 214, original early-2x 28 / 27, 305 vs 214 partition, per-row D0/D1 timestamps.
3. Count source-prefix receipts by date/symbol, verify that each claimed official receipt has 1,440 bars, a full SHA256 hex, and the successful publisher verification marker. A 48-hour prefix is never upgraded to a seven-day completeness claim.
4. For each case, compute its prospective seven-day observation end: min(D0 + 168h, original fixed historical seven-day anchor end) as a **censoring window**, not as an observed verified source interval. List required later calendar days and unknown coverage; never label unavailable future as loss.
5. Save a machine-readable census and fail closed if upstream population or provenance changes. Keep source inventory fully separated from strategy return analysis.

## Causal state-machine contract for the next implementation batch

- Fixed event key: original (historical anchor date, venue-qualified symbol, D0_FIRST_UTC). D0 WATCH persists and remains inspectable across state transitions; one high-priority event must have a stable deterministic ID.
- States: `D0_WATCH_ACTIVE`, `D1_SETUP`, `WATCH_RECOVERY`, `REIGNITION_CANDIDATE`, `PRIORITY`, `INVALIDATED`, `EXPIRED`, `SOURCE_CENSORED`. Expiration terminates attention only, never deletes original WATCH or source provenance.
- A historical original D1 signal may be ingested only at its actual observable timestamp, as an as-of external signal. Neither future first-2x/5x/10x HIGH nor Stage110's future outcome label is permitted as an input.
- Every 1m bar must be fully closed before it can change state. A signal that observes a bar opened at t is observable no earlier than t+60s; the next bar OPEN is the earliest price-only entry proxy. No same-bar HIGH or LOW is an executable fill.
- The maximum seven-day watch is bound to the ORIGINAL historical 7-day anchor as an evaluation interval. D0 observations later than the anchor end are censored. Source gaps, unknown instrument eligibility, delisting or last available price must not silently become `EXPIRED` or a zero return.
- Cooldown, duplicate consolidation, repeated ignition count, late-event expiry, drawdown/invalidation, and the economic exit rule must be selected **before** reading any additional 168h official bars and committed as one falsifiable strategy; research labels may not tune them afterward.
- Report G2 versus the 28 historical D0 early cases, G3 over all original 42 complete UTC06 days, G4 only on cases with an actual next-minute OPEN and a source-complete 24h CLOSE. Show positive/negative cases, 5x/10x misses and costs; even complete OHLC data cannot produce `REAL_EXECUTABLE_NET_PNL`.
- G2 >=80%, G3 average <=5/day and peak <=12/day, median price-proxy >0, adequate verified identity/coverage, fresh independent OOS, and true other-AI review must each be disclosed separately; no single green CI gate authorizes deployment.

## Phase gate

`STAGE111_SOURCE_CENSUS=IN_PROGRESS`; `STAGE111_NEW_STRATEGY=NOT_FROZEN`; `STAGE111_OFFICIAL_FULL519_SEVEN_DAY_REPLAY=NOT_DONE`; `NEW_OOS=NOT_DONE`; `OTHER_AI_REVIEW=NOT_DONE`; `MONSTER_DEPLOYMENT=NO_GO`. No scheduled workflow, LaunchAgent, email, order or automation will be created by this research batch.
