# PHASE_MONSTER_D1_V3_REDESIGN_REPORT

**MONSTER_D1_V3_TRAIN_PASS; 2024 validation = INSUFFICIENT_DATA + CEILING_FAIL; production = NO_GO.**

V3 achieves the unchanged TRAIN entity ceiling through a real second confirmation stage: 48/72 eligible configs, winner V3-062 at89 median/127p95. Noise reduction costs recall and lead time, and the once-only2024 evaluation fails the ceiling with insufficient target samples. This is not MONSTER_D1_V3_VALIDATION_PASS. No configuration was changed after seeing2024.

Frozen specification: [MONSTER_D1_V3_SPEC.md](docs/MONSTER_D1_V3_SPEC.md). Complete [72-config TRAIN results](docs/results/monster_d1_v3_train.json), [Pareto frontier](docs/results/monster_d1_v3_pareto.json), [once-only validation result](docs/results/monster_d1_v3_validation.json). Private read-only source reuse and machine receipts: `/Users/jerson/Documents/ChatGPT/crypto-monitor-monster-v3-evidence-20261003`.

| # | Field | Actual result |
|---|---|---|
| 1 | starting branch | codex/crypto-monitor-design-20260930; clean |
| 2 | starting SHA | d2dc47b6a2523ed3372638e965376f4dbffaf1ab |
| 3 | V2 baseline | 243 TRAIN configs; V2-237 diagnostic median148/p95215; >=5X20/20, >=10X7/7, >=20X2/2; no V2 validation proof |
| 4 | V2 failure reason | All243 fail unchanged median100/p95150 ceiling; high-recall OR pathways produce too many entities |
| 5 | V3 architecture | Stage0 eligibility -> unchanged broad V2-001 A–E trigger -> Stage1.5 consecutive persistence + independent QUALITY/RS/conditional DUAL confirmation + causal retention/overextension proxy -> lifecycle activation |
| 6 | V3 frozen spec commit | 6860afb0296c296ba4791f0baf425de225df6974; committed and pushed before full TRAIN; winner independently committed 1036518cbc1123b70f67384acfa2a848544e4e55 before 2024 labels |
| 7 | config count | 72 frozen finite structural configurations; no post-validation parameter changes |
| 8 | TRAIN period | 2021-01-01 <=t<2024-01-01; 2020Q4 warmup; 1095 calendar days including zero days |
| 9 | total instruments | 954 historical nonempty, from inventory1724; original total19,160,427 bars reused |
| 10 | entity count | 657 conservative IDs; original802 verified exact-base instruments /152 ambiguous stay separate |
| 11 | >=5X event count | TRAIN instrument20 / entity episode20; targets unchanged |
| 12 | >=10X event count | TRAIN instrument7 / entity episode7; N<10 descriptive, not quantitative validation |
| 13 | >=20X event count | TRAIN instrument2 / entity episode2; descriptive only |
| 14 | candidate median range | 50–138 unique entities/day |
| 15 | candidate p95 range | 86–214/day, nearest-rank |
| 16 | eligible config count | 48/72; eligibility requires both unchanged ceilings |
| 17 | winner | V3-062, lexicographic frozen selection; [3,250000,QUALITY_OR_RS,0.5,true]; tie resolved by config ID, no manual selection |
| 18 | winner median/day | TRAIN89 entities /109 instruments |
| 19 | winner p95/day | TRAIN127 entities /165 instruments; formal gate is unique entities |
| 20 | >=5X recall | TRAIN19/20=95%; instrument and entity-event prehit equal. >=5X unique-entity recall also detailed below. |
| 21 | >=10X recall | TRAIN6/7=85.714%; small sample and one additional miss |
| 22 | >=20X descriptive recall | TRAIN2/2=100%; N=2, not validation proof |
| 23 | strict-before2X | TRAIN >=5X19/20=95%; >=10X6/7=85.714%; >=20X2/2=100% |
| 24 | lead-to2X | TRAIN median93h for >=5X (19 triggered); 97.5h for >=10X (6); 152h >=20X (2). Frozen anchor-24h-to-peak matching, not executable entry lead. |
| 25 | lead-to5X | TRAIN median119h >=5X; 102h >=10X; 152h >=20X |
| 26 | 2021 metrics | median87/p95118; >=5X14/14; >=10X5/5; strict-before2X14/14 and5/5 |
| 27 | 2022 metrics | median92/p95129; >=5X5/6; >=10X1/2; strict-before2X5/6 and1/2; clear year weakness |
| 28 | 2023 metrics | median87/p95133; >=5X and>=10X N=0, recall=N/A; no claim of stable high-tier recall that year |
| 29 | V2 -> V3 comparison | V2-237 -> V3-062: median148->89 (-59,-39.86%); p95215->127 (-88,-40.93%); >=5X100->95% (-5pp); >=10X100->85.714% (-14.286pp); strict-before2X >=5X-5pp / >=10X-14.286pp; median5X lead-to2X119.5->93h (-26.5h), lead-to5X144.5->119h (-25.5h) |
| 30 | Pareto frontier | 6 nondominated configs /3 distinct metric points: V3-058/060=58/95,75%5X; V3-062/064=89/127,95%5X; V3-070/072=50/86,65%5X. All front points ceiling eligible; complete72 results retained. |
| 31 | noise attribution | Broad instrument-hours 2248645; rejected 1882525 (83.72%). Confirmed activations153437; primary A134375 (87.58%), E10236, B8671, C140, D15. TRAIN168h complete148203 /censored5234; non2X144631=97.59%. Counts are activations/instrument-hours, not daily unique entities. |
| 32 | extreme-range analysis | GT11 flagged >=5X episodes unchanged;10/11 prehit. Broad trigger hours with intrahour(range/close)>=1:83. Wick filter did not remove GT targets or prove these flags explain most noise. |
| 33 | low-liquidity analysis | GT9 low-anchor-liquidity flagged >=5X episodes unchanged;8/9 prehit. Broad hours with quote<50000:280452. OSMO2022 >=10X episode is the new miss and has both flags; no synthetic liquidity or removal of difficult targets. |
| 34 | MMT diagnostic | Both Spot/Futures: V2-001 reference2025-11-04 19:00UTC,4h after2X; V3-062 no confirmed bar in same exposed event window. Failure remains; no claimed trigger time/lead. |
| 35 | AVNT diagnostic | Futures: V2-0012025-09-09 22:00UTC,19h before2X; V3-0622025-09-10 16:00UTC,A path,1h before2X;18h later than V2 |
| 36 | BTW diagnostic | Futures: V2-0012026-06-04 21:00UTC,3h before2X; V3-0622026-06-05 20:00UTC,primary A, supporting B/D/E,20h after2X;23h later than V2 |
| 37 | 2024 validation status | Ran exactly once on committed V3-062 only. INSUFFICIENT_DATA plus CEILING_FAIL:366 days, median101/p95152; >=5X entity1/2=50%, instrument2/4=50%; >=10X and>=20X N=0. strict-before2X entity1/2; lead2X13h/5X34h (one triggered entity). Not VALIDATION_PASS. No second config/retry/tuning. Complete168h outcomes64698, censored1397, non2X63759=98.55%. |
| 38 | D2 status | BLOCKED_VALIDATION_NOT_PASSED; existing source audit retained unchanged; no formal shortlist |
| 39 | D3 status | NOT_STARTED; Monster LaunchAgent0; no live Monster or Gmail path |
| 40 | tests | Python3.14:395 passed/3 optional NumPy module skips (3.28s); Python3.12:395 passed/3 optional skips (3.14s); NumPy Python3.13:422 passed/0 skipped (5.11s). V3 specific17 passed. Full72-config TRAIN grid/winner byte-identical on isolated rerun; all first-trigger/daily arrays equal. compileall, two pip checks PASS. No frozen spec/kernel changes after freeze. |
| 41 | CPU / RSS | Full TRAIN meanCPU94.79%, runtime60.51s; sampled tail meanCPU96.90%/peak97.70%, RSS peak99.45MiB. ru_maxrss TRAIN115.80MiB, validation208.14MiB; largest measured across prep/replay/audits/diagnostics454.31MiB <1GiB. Single nice10 heavy worker; sampler timing is partial TRAIN, not whole-run ps sampling. |
| 42 | disk | V3 allocated503226368bytes; all relevant FM2+FM3+FM4+V3 allocated5541122048bytes (5.161GiB). Raw/V1/V2 evidence preserved; no archive redownload. Extra supplementary SQLite and immutable audit outputs increase prior5GiB soft estimate; latest request hard memory limit met; no evidence deleted to conceal disk footprint. |
| 43 | Meme health during replay | Read-only: samePID23182; polls901->1505; RUNNING; one scanner; gap0/unresolved0/duplicate0;4290 unchanged; SQLite integrity ok. No stop/restart/runtime mutation; source/config/plist untouched. |
| 44 | task mutations | 0; $300-3000 untouched; real Gmail sends0; NFT/Core Price/portfolio modifications0 |
| 45 | wallet / trades | 0 /0 |
| 46 | final SHA | Runtime/spec6860afb0296c296ba4791f0baf425de225df6974; selected winner1036518cbc1123b70f67384acfa2a848544e4e55. Final report delivery SHA recorded after commit in private final-delivery-verification.json and final response; avoids self-referential Git hash. |
| 47 | remote HEAD | Final delivery requires exact local=tracking=GitHub remote SHA; verified after push in private final-delivery-verification.json and final response |
| 48 | worktree cleanliness | Final delivery requires git status --short empty; recorded after final report/results commit and push |
| 49 | next gate | STOP for review. TRAIN_PASS only; 2024 not passed and now exposed. Do not reuse2024 to tune/reselect or run V4 automatically. Review persistent Momentum/RS noise, early-new-listing delay, OSMO miss, year instability and future independent evaluation design before further architecture work. D2/D3/production remain blocked. |

## Noise reduction versus missed targets

| Configuration | TRAIN median/p95 entities/day | >=5X prehit | >=10X prehit | >=5X strict-before2X | Median5X lead-to2X | Delta median/p95 vs V2-237 |
|---|---|---|---|---|---|---|
| V2-237, ineligible reference |148/215|20/20|7/7|20/20|119.5h|0/0|
| V3-070 |50/86|13/20|4/7|60%|30.0h|-98/-129|
| V3-058 |58/95|15/20|5/7|75%|51.0h|-90/-120|
| V3-062 |89/127|19/20|6/7|95%|93.0h|-59/-88|

Equal Pareto points retain tied config IDs in machine results; they do not authorize manual choice. The winner is fixed by the previously committed lexicographic rule. Lowest noise loses7 of20 >=5X events and more than half of the high-tier lead; balanced75% recall is also materially below the winner.

## Meaning and limits

The target definition still includes difficult/illiquid spikes and leveraged/ambiguous instruments, including exceptional high prints. High/anchor-close GT multiples are not executable investment returns. Entity metrics refer to conservatively deduplicated overlapping entity episodes; they do not imply every ambiguous ID is a verified distinct real token.

Unique-ID recall >=5X (at least one prehit episode per ID): 18/19; event-episode recall remains the frozen primary metric.

Unique-ID recall >=10X (at least one prehit episode per ID): 6/7; event-episode recall remains the frozen primary metric.

Unique-ID recall >=20X (at least one prehit episode per ID): 2/2; event-episode recall remains the frozen primary metric.

Exposed MMT/AVNT/BTW use the same anchor-minus24h to peak windows as the existing V2 reference and record first confirmed bars with window-local state. These are explanatory diagnostics, not full-history lifecycle activation proof or validation. V3 misses/delays them materially; no token-specific tuning was performed.

The original14 kernel tests were frozen before TRAIN. Additional3 end-to-end tests exercise paired instruments/entity counting, calendar zeros, strict crossing semantics, immutable separate-output rerun and validation-lock-before-GT. Initial short-fixture runs exposed absent-year fixture handling and exclusive-publication behavior; fixtures were corrected to use separate immutable output roots without changing frozen production code or result selection. Final17 tests pass. A resource sampler initially used the NumPy-free base Python and failed to import; it was rerun in the already existing NumPy environment. Its actual coverage is explicitly partial.

Largest residual primary-path source is A Momentum; optional RS can confirm ordinary prolonged relative outperformance that never becomes2X. Low-quote and extreme-range flags describe some targets/noise, but are not sufficient explanations for all flow. The failed2024 ceiling and worse exposed-case early recall require review; merely choosing another already-scored model against2024 would invalidate its holdout role. No V4, D2 shortlist, D3, LaunchAgent, task/Gmail or trades were started. Meme stayed healthy and received zero code/config/runtime mutations.

Final authored-diff review and credential scan: PASS across15 changed files; GitHub/OpenAI/AWS/private-key credential patterns zero hits. Protected Meme/Frank source, config and prior FM3/FM4 reports, GT and V2 preprocessing/spec/config/evaluator paths remain unchanged. Shared utility changes=0.
