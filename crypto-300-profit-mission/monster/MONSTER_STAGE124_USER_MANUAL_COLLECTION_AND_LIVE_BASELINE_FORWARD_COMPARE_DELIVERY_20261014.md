# Monster Stage124 — user-controlled manual collection only, 525 live symbols benchmark ready

Date 2026-10-14 Asia/Bangkok. Original Monster Draft PR #30 research branch. User's current explicit instructions: stop the **three already installed Stage99 local launchd scheduled captures**, and user will personally request future Binance data collection when appropriate. Do not schedule a replacement, activate an existing ChatGPT automation, create a cloud or Mac job, enable emails, or deploy any Monster trading/watcher component. The exact user-local stop command was provided in chat, scoped solely to:
- `com.lxxlx2.monster.stage99.usdm.20261014`
- `com.lxxlx2.monster.stage99.usdm.20261028`
- `com.lxxlx2.monster.stage99.usdm.20261111`

The command uses `launchctl bootout` and `launchctl disable` on only those labels and backs up each `$HOME/Library/LaunchAgents/<label>.plist` as `.plist.disabled`; no Frank service, user documents, earlier status or log is targeted. **User has not yet returned the actual post-command output; do not claim tasks were stopped.** This statement replaces prior intent to keep Stage99 future scheduled jobs active. If a job has run already or the plist does not exist, the command attempts cleanup and still verifies service absence; anything unexpected needs actual user output.

## Research milestone and locked original data

- Stage123 real connected Binance read-only public market source observation at `2026-10-14T09:48:24.840Z` recorded **BEFORE any later manually requested follow-up outcome**. Saved complete original 927-symbol exchangeInfo, 525 active USD-M USDT perpetual, all 793 24h price-change tickers, 795 best bid/ask tickers and 930 mark/funding records in eight separate Git source files + manifest: `monster/evidence/monster_stage123_20261014T094824Z_manifest.json`.
- Actual active 525/525 have current valid BBO, mark and 24h reference data, each of those 525 source timestamps within a source-readable interval of approximately 36 sec. This data is structured native Binance public connector output, **not Stage97 raw paired HTTPS + Binance /fapi/v1/time bodies** and cannot backfill the failed original `2026-10-14T06:00:00Z` Stage99 scheduled first-window evidence.
- Pre-registered evaluation semantics written BEFORE any manual T1 outcome at `MONSTER_STAGE124_FROZEN_MANUAL_MARKET_TWO_SNAPSHOT_FORWARD_COMPARISON_PROTOCOL_20261014.md`, commit `3c2547ab96bbe47b4b8b5dedcdb28d1e1070e60f`.
- Pure fully offline comparison code `local-agent/scripts/monster_v4_stage124_manual_snapshot_forward_compare.py` introduced commit `989f388c6b194bf947f85700e98f99de240c71a8`. Can be run with `--before <manifest> --after <manifest> --out <json> --rows <jsonl>` ONLY after an actual next manual Binance capture is saved; with `--before <manifest> --out <json>`, it reports source readiness and explicitly no T1. Does not access networks or schedule captures.
- Full original T0 baseline 525, per-symbol exact Unicode names and merged price sources, specific censorship reasons for source gaps, later listings distinct from T0, time-causal first/second batch checks, forward midprice + mark **endpoint-only** percent change, endpoint >=2x/5x/10x without claiming first-crossing time, per-cohort p10/median/p90 and negative cases all preserved. Notional, bid depth or actual execution are unknown.
- Official 1m full future path remains needed to infer first GT2 high/time and true early D0/D1 recall. Do NOT use later 24h rolling backwards change as a forward D0 model prediction. Old Stage118 strategy remains REJECTED, and new data are descriptive not proof of OOS.

## Actual tests and source-readiness archived

- Offline macOS+Ubuntu GitHub Actions [Stage124 #38547672796](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38547672796) **SUCCESS**, both platforms executed selftests loading original eight Git evidence files. Actual source readback: 927 original market symbols, 525 original as-of active USD-M, **525 source-complete** original symbols, 0 missing. Tests use synthetic T1 **only** inside unit test to validate one +150% endpoint, one -60% endpoint, a delisted/inactive symbol, a newly listed symbol excluded from original denominator, counter closure and causality; no synthetic T1 stored as real future outcome.
- Actual machine evidence `monster/evidence/monster_stage124_real_current525_source_ready_NO_T1.json`, blob `3c136516ab743b92315ca9d20e49d7171647baa8`:
  `full_source_exchange_entries=927`, `original_active_population=525`, `complete_active_ticker_bbo_mark=525`, `real_T1=NOT_REQUESTED_OR_ARCHIVED`, `true_forward_price_proxy=NOT_YET_OBSERVABLE`, `actual_Stage99_stop_command_user_confirmation=NOT_YET_RECEIVED`.
- Git push CI is triggered on code changes only; **no schedule** directive, no background research data collector was created. Work stays on same Monster PR #30.

## Next manual step without any automation

Whenever user next says "采集 Binance 妖币数据", retrieve the same four Binance connected public endpoints (full original symbol universe and complete 24h, bid/ask, mark/funding). Archive all returned rows with their true **NEW** observation time into corresponding stage123-format shards+manifest on existing PR30. Then execute the same pure Stage124 code with the committed first manifest as T0 and the new actual manifest as T1, publishing full original-denominator 525 forward endpoint price/gap statistics and newly listed symbols. No new user-local scripts needed for connector-based descriptive observation. Do NOT promise any particular future performance or time.

Important: user's command execution result has not yet been seen. Respect actual LaunchAgent state and do not assert local stop was accomplished remotely.

`STAGE124_USER_MANUAL_ONLY_POLICY=ACTIVE`;
`STAGE124_REAL_T0_927_MARKET_SOURCE=DONE`;
`STAGE124_REAL_T0_525_ACTIVE_SOURCE_PROVENANCE=DONE`;
`STAGE124_OFFLINE_T0_T1_COMPARATOR=CODE_AND_TWO_OS_CI_PASS`;
`STAGE124_NEW_REAL_T1=NOT_REQUESTED`;
`STAGE124_REAL_SOURCE_ONLY_READINESS=ARCHIVED`;
`ORIGINAL_STAGE99_OCT14=SOURCE_FAILED_NO_BACKFILL`;
`STAGE99_LOCAL_STOP_OUTPUT=NOT_RECEIVED`;
`NO_AUTO_CAPTURE_CREATED`;
`G0_CRYPTO=PARTIAL`;
`G1_G2_G3_EARLY_OPPORTUNITY_RECALL=NOT_PROVEN`;
`G4_EXECUTABLE_NET=UNKNOWN`;
`EXTERNAL_MODEL_REVIEW=NOT_DONE`;
`MONSTER_DEPLOY=NO_GO`;
`FRANK=UNCHANGED`;
`GMAIL=OFF`.
