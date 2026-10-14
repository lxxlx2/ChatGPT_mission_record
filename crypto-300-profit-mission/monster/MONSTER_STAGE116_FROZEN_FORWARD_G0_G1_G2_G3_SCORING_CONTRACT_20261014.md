# Monster Stage116: frozen future full-market OOS scoring and entry-evidence integration

Date: 2026-10-14 (Asia/Bangkok). Scope: existing Monster Draft PR #30. Objective: implement the genuinely missing G0/G1/G2/G3 scoring for the already frozen forward periods before any future outcomes are read; keep D0/D1 frozen from Stage91, not fit another model on Stage83/111/115's six exposed windows. This is a necessary research model validation component, **not a production watcher or order engine**.

## Fixed inputs and dates (prior Stage105)

- `2026-10-14T06:00:00Z`, `2026-10-28T06:00:00Z`, `2026-11-11T06:00:00Z`, each exactly 168h; all times UTC. These exact future windows are already frozen by `monster_v4_stage105_capture_universe_core.py`. No adjusting days if the first capture is missed.
- Market: raw Binance USD-M USDT PERPETUAL exchangeInfo at as-of capture (within 15m before start), verified from the separate Binance /fapi/v1/time raw bodies and receipt clocks using unchanged Stage97 logic. Do not infer historical eligibility from today's exchangeInfo.
- Every candidate symbol selected from the authenticated as-of universe must appear once in the window's replay output. Same Stage91 `replay_raw_symbol` pure old-V4 D0/Stage79 D1 logic with nine contiguous publisher SHA256-checked daily 1m ZIPs (prior day warmup + seven active days + last source day), and true past-bounded decision times.
- Original label = anchor first minute OPEN vs subsequent 168h first 1m HIGH >=2x/5x/10x, for post-hoc discovery recall ONLY, never an executable fill, ranking input or user PnL.

## Missing full-market scorer to implement now

1. Preserve **all venue-symbol attempts**, including no WATCH, no D1, missing future official 1m ZIP, as-of unknown identity, newly listed after capture, futures/stock-like underlying, and ambiguous multiplier names. No falsely treating 900 historical symbols as fully eligible crypto.
2. Validate original snapshot evidence raw bytes, independently reported Binance server time and capture order with Stage97 read-only proof verifier; filename or arbitrary `source_authenticity=ATTESTED` field alone is never authoritative.
3. Reconcile source per-window against the *authenticated* full USD-M candidate set. All three windows are required for FINAL gate evaluation; missing windows produce `PENDING_SOURCE` rather than fabricated zero event or fraction.
4. For source-complete, identity-proven true crypto cases only, compute first early / first >=5m before 2x/5x/10x and original D1 >=5m before first 2x. Exclusion of confirmed noncrypto must be evidence-backed as-of timestamp, and unknown crypto eligibility must keep G0 `PARTIAL` and G1/G2 `NOT_SCORABLE`.
5. G1: first D0 strict before 2x >=90%, >=5m before >=85%, **at least 20 real independent first 2x crypto opportunities spanning all three independent windows**; if underpowered mark `UNDERPOWERED`. G2: among original D0 >=5m early 2x, D1 also >=5m early in >=80%; no counts dropped because D1 was late. G3: 21 complete original UTC06 daily buckets, original D1 high-priority average <=5/day, peak <=12, with exact no hard top-N hiding, no future labels in notification logic.
6. G4 real executable net remains **UNKNOWN** until each admission receives as-of positive crypto identity+correct contract unit+bid/ask/depth+fees/real venue status and an explicitly supplied notional, validated using original Stage90 D2 read-only engine. Do not substitute historic close, USD-M 1m HIGH, or arbitrary 30/300 quote amount.
7. No result of purely synthetic selftests upgrades to live validation; GitHub CI can compile/selftest score core on macOS/Ubuntu, but must never auto-create a scheduled USD-M collector, reminder, background source capture, real Gmail or real trade. The existing Stage99 helper is unchanged.
8. Before the first complete future window, all `G0-G4=INCOMPLETE/PENDING`. Model with inherited original Stage79 D1 still has exposed-history G2/G3 failure and must not be promoted even if new CI is green. Historical Stage108-115 rejected/diagnostic evidence must remain immutable.

## Explicit hard gates

`G0=PARTIAL_UNTIL_GENUINE_ASOF_CRYPTO_AND_VENUE_PROOF`;
`G1=NOT_SCORABLE_UNTIL_ALL_3_WINDOWS_AND_20_CRYPTO_2X`;
`G2=NOT_SCORABLE_UNTIL_G1_VALID`;
`G3=NOT_SCORABLE_UNTIL_COMPLETE_21_DAY_OOS_ATTENTION`;
`G4=EXECUTION_UNKNOWN`;
`G5=OTHER_AI_REVIEW_NOT_DONE`;
`G6=MONSTER_DEPLOYMENT_NO_GO`.

No automatic order/trading, Mac local installation, existing Frank/Stage99 mutation or notification. Later source capture requires its own explicit one-shot authorization at the actual predeclared time window. A push-triggered code/unit-test CI is not an ongoing monitor.
