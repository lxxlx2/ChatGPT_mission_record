# Monster Stage115: D0 +2.75% pooled price edge fails six-date stability check

Date: 2026-10-14 Asia/Bangkok. Research-only original Monster Draft PR #30. The pre-analysis contract `MONSTER_STAGE115_ORIGINAL519_D0_PRICE_PROXY_SEGMENT_STABILITY_PROTOCOL_20261014.md` was committed as `fee351869298c32d3324d0b43eef0a0716d40a8d` before looking at these fixed strata. Original all-519 real Stage114 source blob `de64a09ff4f8b35009fd1ff71a284542fd5de5ac` and compact blob `33e38198a8ad2c0d99ebf4161c77264978ffbcc4` have been source-locked; no existing strategy was modified.

## Actual original evidence and CI

- Full machine evidence: `monster/evidence/monster_stage115_all519_d0_cohort_stability_actual.json` Git blob `11cd01007e85c32996d3d691af87007e226688a7`, actually archived in same PR by CI commit `495feda99865889e83ae7670a701197b30d1ef08`.
- Final successful GitHub Actions run `38501344821`: <https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38501344821>.
- Initial run `38501195873` failed, retained as genuine failure. Root cause: Stage115 initially looked for `frozen_5m_24h_entry_horizon_price_proxies` in Stage114 archived reduced per-case rows, which actually use `entry_price_proxy_gross_by_horizon`; CI reported `KeyError`. Fixed ONLY source-schema decoding in commit `769accd637fe35bb4d4cd4f79c8b47fd041fcbc9`, reran and successfully archived without touching prior raw evidence, D0/D1/P signal times, cohorts or thresholds.
- Stage115 confirmed original519 cases, 519 5m prices, 480 complete 24h prices, 39 source-censored 24h, and exact original +2.752013313057699480675981950% pooled 24h median with 266 positive prices. Source label remains `BINANCE_USDM_HISTORIC_MIXED`; real tradability, actual fills and user notional are UNKNOWN.

## Critical six original historic anchor windows

| Original seven-day anchor | D0 cases | Completed 24h price outcomes | Gross median 24h | Positive / complete |
| --- | ---: | ---: | ---: | ---: |
| 2025-01-30 | 161 | 160 | **+20.631246%** | 142/160 |
| 2025-06-02 | 34 | 33 | **-2.163194%** | 12/33 |
| 2025-08-01 | 54 | 41 | **-2.551490%** | 15/41 |
| 2025-10-02 | 75 | 68 | **-3.142642%** | 26/68 |
| 2026-06-21 | 100 | 91 | **-4.702703%** | 33/91 |
| 2026-07-28 | 95 | 87 | **-2.495028%** | 38/87 |

**Only ONE of SIX date-window medians is positive.** The pooled +2.75% is substantially skewed by one high-return and high-population old window. January-30 anchor contributes 142 of the original overall 266 positive full24h observations, though it contains 160 of the 480 full24h observations. The other five combined include 320 completed 24h observations and **124 positive (38.75%)**. All date cohorts remain in the data; the latter subgroup is purely a post-result explanatory cross-check, not a new holdout.

Additional historical source-census timing: 132 of the 161 D0 alerts in the original 2025-01-30 seven-day window first occurred on UTC **2025-02-03**, per Stage83 original immutable 519 D0 record. This concentration is CONFIRMED, while a specific common market shock/regime causing the high median remains an *unverified research hypothesis*. Do not claim causality without further matched event-time evidence.

## Other prespecified descriptive strata

- Original D1 PRESENT: 305 D0 cases, 280 complete D0->24h prices, gross median **+3.987000%**; D0-only: 214 cases, 200 complete 24h, gross median **+0.610428%**. These are not truly independent training/validation cohorts.
- Stage111 later FIRST PRIORITY EXISTS: 277 D0 cases, 272 complete D0->24h, median **+0.215456%**. NO LATER PRIORITY: 242 D0 cases, 208 complete 24h, median **+11.259179%**. The latter PRIORITY partition depends on FUTURE events; **strictly prohibited** as an as-of trading filter or investment probability.
- ORIGINAL IDENTITIES: 501 `CRYPTO_IDENTITY_UNVERIFIED`, 15 `MULTIPLIER_MAPPING_UNVERIFIED`, 3 `CONFIRMED_TRADFI_OUT_OF_CRYPTO_SCOPE`. No source currently licenses describing 501 as confirmed valid spot crypto or true D2 eligible instruments.
- Left tail among all 480 complete D0-24h price observations: 23 <= -20%; the historical pooled p10 is -15.128205%. Only 4 observations >= +100%, and 16 >= +50%. 5m D0 gross median was +0.016900%, with 261/519 positive, before fee or actual spread/slippage. A 20bps each-side fee sensitivity turns the small median 5m observation negative (Stage114).
- Neither an optimistic unpaired D0 result nor a future-labeled NO PRIORITY group establishes actual expected profit. Stage111 priority model remains `REJECTED`.

## Decision and next falsifiable mainline

`STAGE115_DESCRIPTION=COMPLETED`, `D0_POSITIVE_GROSS_POOLED_GENERALIZABILITY=NOT_ESTABLISHED`, `STAGE111_V1=REJECTED`.

Do NOT revert to "buy every original D0." The mainline goal is (a) consistently timely D0 WATCH across genuine point-in-time crypto universe; (b) **new** as-of signal ranking or admission with confirmed available venue/actual executable price, without pretending the historical future-priority label can select winners; and (c) trustworthy current-source out-of-sample / forward verification with independent other-AI review, cost and timing guardrails. Before choosing a strategy candidate, isolate whether date-dependent exceptional D0 returns correlate with observable entry-time liquidity / volume and then preregister a single model on untouched future data. Do not fit the six already exposed windows until the median turns positive.

Implementation must keep existing Frank, Stage99, local workflows and emails untouched; nothing here authorizes an installed Monster monitor. `PRODUCTION_TRADING=NO_GO`, `MONSTER_DEPLOYMENT=NO_GO`, `MONSTER_GMAIL=OFF`, `OOS=NOT_DONE`, `REAL_NET=UNKNOWN`, `NEW_OTHER_AI_REVIEW=NOT_DONE`.
