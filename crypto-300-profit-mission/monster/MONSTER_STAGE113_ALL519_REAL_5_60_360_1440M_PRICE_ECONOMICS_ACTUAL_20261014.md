# Monster Stage113: official real-1m fixed-horizon gross price economics, entire original519

Date: 2026-10-14 Asia/Bangkok. Original Monster Draft PR #30, historical research only. The pre-registered diagnostic contract `MONSTER_STAGE113_FIXED_5_60_360_1440M_SOURCE_COHORT_PRICE_PATH_PROTOCOL_20261014.md` was committed at `96d29b81e8484a010b87ae4283ddec6432f4caac` BEFORE the new 5m/60m/360m forward path computations.

## Source and reproducibility

- Source cases: original Stage83 519 D0, Stage111 V1 unchanged core and 740 previously recorded Stage111 PRIORITY events. 277 FIRST, 463 REPEAT, 305 original D1 and 214 D0-only. All prior 6 historical windows are exposed research cases, NOT untouched OOS.
- Actual machine results: `monster/evidence/monster_stage113_real519_5_60_360_1440m_actual.json`, Git blob `b5e56d4ec50cfb34ace39303e96bbc30e894a5d1`.
- Official Binance historical daily 1-minute publisher-checksum verification reused the Stage111 source reader. All 519 source cases have `EXPIRED` status for their original fixed-anchor observation window. Censored later holding periods remain censored rather than counted as failures.
- Stage113 code `../local-agent/scripts/monster_v4_stage113_fixed_horizons_official.py` and `../local-agent/scripts/monster_v4_stage113_horizon_aggregate.py`; actual 6-date ×4 shard source/aggregation CI `monster-stage113-fixed-horizon-original519-1m.yml`. Each complete 24h result must numerically match the original archived Stage111. Entire 598 observation 24h median recomputed as -3.504274750385354539869490800%; original 237 FIRST and 361 REPEAT complete cases also matched.
- The data are theoretical next-minute OPEN to later 1-minute close PRICE_ONLY outcomes. The 20bps per side column is a fixed cost SENSITIVITY, NOT a verified Binance fee/fill/slippage, and not an individual's actual profit.

## All 740 priority events: frozen four holding horizons

| Frozen duration after causal next-open | Completed price-only proxy | Positive | Gross median | Synthetic 20bps each-side median | Censored because horizon/no trades |
| --- | ---: | ---: | ---: | ---: | ---: |
| 5m | 740 | 312 | **-0.217549%** | -0.615882% | 0 |
| 60m | 737 | 302 | **-0.788221%** | -1.184276% | 3 |
| 360m / 6h | 705 | 296 | **-1.253704%** | -1.647901% | 35 |
| 1440m / 24h | 598 | 231 | **-3.504275%** | -3.889487% | 142 |

The effective populations differ as the original seven-day anchor ends; one cannot directly treat the rising negative median as a same-sample causal decay. On the **598-source-complete 24h cohort**, common-cohort median prices are: 5m **-0.212182%** (598 scored); 60m **-0.808899%** (598 scored); 360m **-1.251956%** (597 scored, one exit bar censored); and 24h **-3.504275%** (598 scored). This common-cohort analysis supports descriptive worsening across horizons without the main variable-population confounding; holding-time causality and realistic liquidity remain unresolved.

## FIRST versus REPEAT price-only outcomes

| Duration | FIRST n | FIRST gross median | REPEAT n | REPEAT gross median |
| --- | ---: | ---: | ---: | ---: |
| 5m | 277 | -0.203538% | 463 | -0.245942% |
| 60m | 276 | -0.656921% | 461 | -0.899550% |
| 360m | 268 | -1.336598% | 437 | -1.251956% |
| 1440m | 237 | -3.247724% | 361 | -4.070467% |

Even first-event 5m prices have a negative gross median; repeated episodes exhibit a slightly worse 5m median. Do NOT infer that simply shortening fixed exits converts the rejected strategy to profitability, or that all repeated signals are worthless.

## Practical model implication and current authority

The Stage111 15m REST→REIGNITION admission mechanism is insufficient for economic quality: original early-2x recall 19/28 failed, 8 major cases first acquired PRIORITY only AFTER 2x, and the price-only path is adverse already at 5m. A logically different next candidate must prioritize finding actionable entry earlier and proving executable venue/price, rather than adding yet another after-the-fact 15m/24h percent threshold. D0 WATCH must remain retained and queryable even when D1/Priority is rejected, with explicit stale/deferred identity.

**Do not select 5m or any other horizon as an improved winning strategy from these exposed results.** The first useful next step is to compare an as-of earlier D0/first D1 versus delayed Stage111 PRICE timing **in the same cases** on the fixed exposed dataset, and then formulate a pre-committed candidate to test on truly new/OOS source days with actual order-book, fees, depth and an explicitly specified transaction notional. Keep per-event and per-case analyses separate. The original D0 prior timing may be earlier but is also higher-noise, so lower entry price does not imply positive NAV.

Status: `STAGE113_SOURCE_COMPLETE=519/519`; `STAGE113_PRICE_DIAGNOSTIC=COMPLETED_HISTORICAL_ONLY`; `STAGE111_STRATEGY=REJECTED`; `NEW_MODEL_OOS=NOT_DONE`; `OTHER_AI_INDEPENDENT_REVIEW=NOT_DONE`; `REAL_EXECUTABLE_PNL=UNKNOWN`; `MONSTER_DEPLOYMENT=NO_GO`; `GMAIL=OFF`; `FRANK=UNCHANGED`; `STAGE99=UNCHANGED`. No new scheduler, automation or installed runtime was created.
