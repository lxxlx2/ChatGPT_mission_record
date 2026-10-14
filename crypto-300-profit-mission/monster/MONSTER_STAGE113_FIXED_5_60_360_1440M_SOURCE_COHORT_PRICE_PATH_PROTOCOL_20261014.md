# Monster Stage113: full519 as-of signal entry/holding-time gross price decomposition

Date: 2026-10-14 Asia/Bangkok. Existing Monster Draft PR #30. THIS IS A FROZEN DIAGNOSTIC CONTRACT, **not a new trading strategy or an attempt to optimize original Stage111 thresholds**.

## Why this is the only next diagnostic

Stage112 source-locked all519 evidence (blob `1f07c873a8cddbac5128a4b97d64cf4c6d554ba3`) reproduces 740 Stage111 PRIORITY events. First signals had 24h price-only gross median -3.2477% and repeats -4.0705%; within 137 same-coin paired comparisons repeat-minus-first median -1.2393 pp. Eight of nine missed original early-2x opportunities had their first PRIORITY AFTER the first 2x crossing. Raw event IDs collide across different symbols in 62 values. This supports diagnostic hypotheses about late momentum purchase and price reversion; it does NOT support tuning a single threshold on the exposed dates.

## Frozen evaluation and time contract before re-reading minute outcomes

- Population: all original 519 D0 with Stage111 V1 unchanged, all 277 first PRIORITY and 463 repeated PRIORITY events. Preserve the original rejected Stage111 G2 19/28, G3 740/42 and G4 598 complete24h -3.50427%; do not drop censored or unknown identity records.
- Historical source: Binance official USD-M daily 1m publisher SHA256-verified ZIP, via the **same Stage111 reader and same Stage111 core**. Extend no trading universe, keep the original six exposed 7-day anchors. The first Stage111 decision is observable when the final 15m minute closes; next 1m OPEN (timestamp `signal.observable_ms`) is **the first proxy entry**, never the triggering bar price/HIGH.
- PRESET and never choose based on returns: exactly **5, 60, 360, 1,440** consecutive 1m holding intervals from proxy entry. Exit price = CLOSE of the last fully completed minute in that interval. Entry and exit minute must have real recorded trades/quote. Require a complete contiguous minute sequence, and require the exit to be within the fixed original seven-day anchor end; otherwise `CENSORED`.
- Per-event record: (date,symbol,venue/identity, D0, original D1 if any, first/repeat episode ordinal, visible time, entry-next-open, source publisher SHA receipts, elapsed horizon, exit close, gross % price-only, hypothetical fixed 20bps-per-side sensitivity, lowest/minute low adverse price proxy). No trading-notional assumption, no option to pick a best time during the horizon.
- Exactly reproduce Stage111 existing 24h price outcome for every event when the 1,440m path is source-complete. If mismatched, error and stop: do not silently substitute new data.
- Compare **both** all events and FIRST/REPEAT subdivisions. Report each horizon's n, positives, gross median, <=-20% loss frequency, source-censored count, and same-coin case-weighted first-event or repeat-case median when available. Also report the common-source-complete 24h cohort separately to prevent short-horizon selection bias.
- Include proper source/no-trades censoring, first vs later episode overlap disclosure, identity and venue uncertainty. A price-only maximum adverse 1m low is NOT guaranteed stop fill; no trade execution claims.
- No forecasting, no loss-avoidance conclusion or production activation can follow from these exposed windows. If later returns are worse, this is only a hypothesis about reversion that must be separately tested on truly unseen OOS with executable evidence. If immediate 5m returns are poor, the entry path and filtering model need a genuinely new design before new OOS.

## Gates and limits

`STAGE113_DESCRIPTIVE_ONLY`, original model `REJECTED`, `NEW_OOS=NOT_DONE`, `G0_SCOPE=PARTIAL`, `REAL_NET=UNKNOWN`, `MONSTER_DEPLOYMENT=NO_GO`, `MONSTER_GMAIL=OFF`, `FRANK_UNCHANGED`, `STAGE99_UNCHANGED`, no schedule/automation/production change. Other-AI review only counts on actual received review output, not a drafted prompt.
