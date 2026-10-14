# Monster Stage131: historical first-minute new listings into full-market G1 denominator, actual implementation and CI

2026-10-14 Asia/Bangkok. Original [Monster PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30), research-only. Stage77 model acceptance and module development rules unchanged. No Frank, Gmail, orders, launchd, background schedule, or deployment.

## 1. The irreversible first forward-window blocker

Stage105/116 had explicitly frozen three 168-hour weeks opening 2026-10-14 / 10-28 / 11-11 at 06:00 UTC. First 10-14 06:00 source **failed**: no authenticated Stage97 start capture, `SOURCE_FAILED_NO_BACKFILL`. Later 10-14 09:48 Stage123 exploratory snapshot is valid only as its own later observation. **The originally promised all-three-window Stage116 G1 validation cannot pass using only those three frozen windows**, even if the other two later become complete. We preserved that fact in new machine evidence rather than inventing a make-up date, changing the old time, or claiming 10-14 is a new independent OOS.

The future experiment must be separately source-authenticated and **pre-register at least three new non-overlapping forward windows** before their true start times. Subsequent windows must be initiated only by the user's chat request; Stage99 is stopped, and market snapshots hours apart do not prove 1m/3m real-time D0 alert latency. No fresh forward G1 sample was added here.

## 2. Actual mainline implemented

Before new Stage131 code, committed [Stage131 frozen two-lane population protocol](MONSTER_STAGE131_FROZEN_DYNAMIC_LISTING_FULL_MARKET_G1_POPULATION_BRIDGE_20261014.md), commit `270d627ffb4f7e182c48bb317b65c2760bf1daa5`. Implemented:

- [Population bridge](../local-agent/scripts/monster_v4_stage131_dynamic_listing_g1_population_bridge.py) with separate `PREEXISTING_AT_WINDOW_START` and `IN_WINDOW_FIRST_TRADABLE_MINUTE_CANDIDATE` lanes. All original attempted symbols retained, including no-watch, source-censored, issuer/trading status unknown and normal non-winners.
- Exact venue symbol/date matching (including Unicode). Duplicate symbol between start population and post-start listings raises `STAGE131_COHORT_DOUBLE_COUNT_OR_LISTING_REUSE`; new listing timestamps outside the 168h UTC06 window and invalid source ordering fail closed. Later snapshot `COIN` or `EQUITY` labels **never** independently certify historical issuer/transaction status, no venue or crypto gate may pass because of caller-supplied booleans.
- Pure offline ingestion of the immutable Git [Stage130 source-verified concise original31 cohort](evidence/monster_stage130_original31_publisher_sha1m_momentum_archived_summary_20261014.json), verifying its actual Git blob, 31 unique symbol/date cases, 147 SHA publisher archive ZIP receipt count, 159,675 source minutes, first minute to original fixed seven-day end, original frozen market/exposed status and all first-trigger versus future2x clock ordering. Cross-joins older complete Stage129 hour evidence but cannot miscount the Stage93 old 51 / 48 first-D0 2x cohort.
- The `first minute closed` theoretical listing observation remains distinct from the later first positive 3m **research** momentum event; no replacement of original 24h quote ticker, no BUY/execute verdict, no notification or fill claims.

The 31 historical source-verified new-listing cohorts split by **later exchange labels** into COIN=20, EQUITY=7, HK_EQUITY=4, which **do not imply corresponding historical crypto issuer identity**. All 31 source rows are always retained, even if later label is a stock-like underlying.

## 3. Data and scoring limitations from actual Stage130 artifact

- 31/31 historical first minute source complete, 147 publisher checksum-verified ZIPs, 159,675 minutes. First distinct research momentum in 19/31; two **already exposed** gross high2x events (VINE/APR) both had research momentum at least five minutes before the first future high2x minute. The other 17 first signals had no gross2x in this limited cohort.
- Independently reading the original [Stage130 CI #38566877450 artifact](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38566877450) full `stage130_real31.json` shows **581 qualifying repeated 3m momentum condition observations** across those same 31 rows. These 581 positive **polls** do not constitute 581 unique opportunities; the initial 19 should not be inflated by re-notifying the same symbol. Stage131 uses first-event unique symbol/date accounting and does not claim this retrospective 31-subset burden passes full-market G3.
- Real net profit is still unknown: no actual time-of-D0 level 2 execution / orderbook / fees / user notional / conservative future exit. Both new first minute detection and subsequent momentum remain separate from actual actionable trading.

## 4. Independent reproducibility and test results

Added [Stage131 tests](../local-agent/scripts/test_monster_v4_stage131_dynamic_listing_g1_population_bridge.py) for real original31 source integrity and source-hash check, all31 symbol/date population accounting, duplicate symbol and Unicode exact identity, stale/out-of-window listing rejection, future 2x label not modifying an earlier first momentum signal, legacy frozen first-window inability to pass, and proof that caller data cannot turn `G0` into verified.

[GitHub Actions #38572431172](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38572431172), commit `2b09c65088c25543bcbd480673902f8320dfaa70`:
- macOS job `115880806979`: SUCCESS
- Ubuntu job `115880807349`: SUCCESS
- Python seven unit tests per OS + compilation + real all31 actual source digest and machine audit: SUCCESS
- Mac and Ubuntu machine stdout summary fully identical (source 31, 147 ZIP receipts, 159,675 bars, 19 unique first signals, 2/2 previously exposed gross2x early5).
- Permanent Git [Stage131 machine evidence](evidence/monster_stage131_dynamic_listing_original31_reconciliation_summary_20261014.json); CI artifacts retain full 31-row generated ledger for 30 days; the Stage130 original publisher ZIPs remain reproducible from Binance publisher website but are not permanently embedded in Git.

This is a **code/evidence engineering pass**, not model acceptance. Other AI independent review NOT_DONE.

## 5. Next mainline without boundary detours

1. Before any new forward source, freeze independently **three valid full-time windows** with complete initial as-of venue universe and in-window update origin, including new listings, delistings/halts and no-watch cases. Do not retroactively substitute for original Oct14 failure; no new automatic timing tasks.
2. For each user-triggered **real as-of** observation, capture authoritative time/market metadata at the time plus full original publisher SHA minutes afterward; without minute-by-minute contemporaneous observation history, label simulated first trigger as *historical causal replay* rather than real-time WATCH.
3. Apply original V4 D0 and pre-registered new-listing research lane to same complete all-market crypto population and score G0/G1 for real forward samples, G2/G3 with no alerts dropped. Any missing venue eligibility/crypto issuer or unavailable future 168h remains censored; sample size at least 20 2x on three truly independent complete windows before even considering G1 PASS.
4. Only after G1/G2/G3 gates, actual G4 complete bid/ask depth, transaction fees, user-defined notional and conservative exit across >=30 independently supported sample opportunities, new independent other AI Review and explicit user approval may permit local Mac dry-run/production discussion. Frank, other investments and mail stay unchanged.

`STAGE131_IMPLEMENTATION=DONE`; `STAGE131_MACOS_UBUNTU_CI=PASS`; `STAGE131_HISTORICAL_EXPOSED_31_REPRODUCED=DONE`; `ORIGINAL_STAGE116_20261014_0600=SOURCE_FAILED_NO_BACKFILL`; `G0=PARTIAL`; `G1_NEW_OOS=NOT_SCORABLE`; `G2_G3=NOT_PASSED`; `G4=UNKNOWN`; `INDEPENDENT_OTHER_AI_REVIEW=NOT_DONE`; `MONSTER_DEPLOY=NO_GO`; `GMAIL=OFF`; `FRANK=UNCHANGED`; `NO_NEW_AUTOMATION`.
