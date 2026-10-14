# Monster Stage111 V1: all-519 official historical 1m replay, frozen-gate decision

Date verified: 2026-10-14 Asia/Bangkok. Scope: existing Monster Draft PR #30 only. Evidence source: `monster/evidence/monster_stage111_real519_persistent_15m_v1_actual_results.json`, Git blob `9473443f407deb5e4c9e7e14d64685b2e8e49cea`. Evidence was archived by CI commit `0a5d185caf242c4546b2357de5422a2a3023bf36` on 2026-10-13 UTC. The frozen strategy contract was committed earlier as `MONSTER_STAGE111_PERSISTENT_RECOVERY_CAUSAL_RESEARCH_V1_FROZEN_20261013.md`; do not alter its thresholds after reading these outcomes.

## Verified actual result

- Historical original D0 cohort: **519 / 519** unique date-symbol cases; previously observed D1 cohort **305**, and D0-only **214**.
- Historical official 1m source case-status ledger: `EXPIRED=519` (the original fixed seven-day anchor observation interval completed for each case, including late-D0 shorter windows). This does not mean each case has a full seven days from D0, or historical live venue eligibility / order book.
- G2: among 28 original D0 >=5m-early 2x cases, Stage111 first priority >=5m early in **19/28 = 67.86%**. Nine original opportunities missed. Original Stage79 D1 was 27/28, Stage110 was 16/28; Stage111 improves versus Stage110 but **fails preregistered >=80%**.
- G3: **740** total historical PRIORITY occurrences across the original **42** UTC06 days, mean **17.619/day**, peak **46/day**. Fails both frozen mean <=5 and peak <=12.
- G4 historical delayed next 1m OPEN to 24h terminal close price-only cohort: **598** complete price-proxy observations, **231** positive and **57** <=-20% gross; median gross return **-3.504274750385354539869490800%**. Fails the precommitted price-only >0 gate. Price proxy is not executable net return.
- Real bid/ask, depth, user notional, actual fills, venue eligibility and fee/slippage: **UNKNOWN**. Remaining asset identity uncertainties include 501 CRYPTO_IDENTITY_UNVERIFIED, 15 MULTIPLIER_MAPPING_UNVERIFIED, 3 CONFIRMED_TRADFI_OUT_OF_CRYPTO_SCOPE in the fixed starting inventory.
- These six historical windows were already exposed during earlier Monster research; **independent OOS = NOT_DONE** and new-model independent AI review = NOT_DONE.

## Decision

`STAGE111_V1_RESEARCH_STRATEGY=REJECTED_PRE_REGISTERED_G2_G3_GROSS_PRICE_GATES`.

This rejection follows the actual frozen results despite successful source collection and CI. Do NOT describe the historical replay as a validated profitable strategy, do NOT redeploy Stage111 in Monster or promote its PRIORITY to BUY. Preserve raw machine evidence, original thresholds, Stage108/109/110 failure artifacts and current Stage111 V1 implementation unchanged for future comparison. No parameter grid/tuning or changing the winner after reading these exposed dates.

## Most relevant observed root causes, not validated causal proof

The longer D0 observation rescues three additional original early 2x cases versus Stage110 (19 rather than 16) but triggers far more priority events and the price-only median remains negative. The next mainline problem is **entry economics and information value of recurrent ignition**, rather than adding more time windows or blindly changing fixed percent thresholds. Analyze repeated priority-event concentration per coin, original D0/D1 timing, tradability/identity and matched outcomes for ordinary losing controls; freeze any genuinely different timing/execution hypothesis before new validation data. Do not spend the next stage optimizing the same six dates.

## Gates and authority

`FULL519_HISTORICAL_SOURCE_REPLAY=ARCHIVED`;
`STAGE111_V1=REJECTED`;
`NEW_OOS=NOT_DONE`;
`REAL_EXECUTABLE_NET=UNKNOWN`;
`NEW_OTHER_AI_REVIEW=NOT_DONE`;
`MONSTER_DEPLOYMENT=NO_GO`;
`MONSTER_GMAIL=OFF`;
`AUTOTRADE=NO_GO`;
`FRANK=UNCHANGED`;
`STAGE99_LOCAL_CAPTURE=UNCHANGED`;
`NO_NEW_MONITOR_OR_SCHEDULE`.

No changes to installed local services or scheduled tasks in this research-only record.
