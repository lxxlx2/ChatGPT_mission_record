# PHASE3B_PRICE_V2_CALIBRATION_REPORT — 2026-09-30

**PHASE_3B_FAIL_VALIDATION; PRICE_RULE_V2 = FAIL; PHASE_3C = NO_GO; PRODUCTION = NO_GO.**

The sole committed calibration winner failed its first chronological validation: aggregate15/20 episode hits (75%), SOL8/13 (61.538%). Frozen90% recall gates failed. Operational-load gates passed, but cannot compensate for missed episodes. No alternate config was selected, no second validation run, no audit/HYPE winner diagnostic and no V3 development occurred.

## Frozen sequence and provenance

Branch: `codex/crypto-monitor-design-20260930`.
V2_FREEZE_COMMIT: `15753ad1092cc2b1b9bd36270dd770916c50aec0` (committed and pushed before search).
V2_WINNER_COMMIT: `0b3d0cff2199c2bab42d07b42d4e5b8b9259e654` (candidate config and complete calibration result committed and pushed before validation).
Final report commit is the commit adding this file; final SHA is reported after push. Initial sync rebased three new airdrop/TGE run-record commits onto main4d7dcfa7acaebf810a3a10461f164c803a2ec78b before freeze. There is no later rewrite of freeze/winner commits.

The original V1 features/rules/replay/tests/GT/report remain byte-identical to pre-3B.28 private Phase3 evidence files were hash-checked unchanged after validation. V1 code still runs alongside V2; none of its thresholds,48/28/20 ETH minute results or187 SOL minute candidates/173 R4 minute hits were replaced.

Freeze files: PRICE_RULE_V2_CALIBRATION_PLAN.md,PRICE_GT_V2_EPISODES.md,PRICE_RULE_V2_SEARCH_SPACE.md,config/price_rule_v2_search.json. Official English Binance REST market docs rechecked on2026-09-30: https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints . Actual source remains public Spot market-only GET https://data-api.binance.vision/api/v3/klines . No third-party price/history source.

First search scored324 configs but result serialization failed before artifacts because cluster-distribution keys were integers. Converted keys to strings; same immutable calibration data and same frozen324 configs were rerun. No thresholds/contracts were changed based on scores. The final successful calibration artifact is immutable.

## History and partition audit

Fixed120d evaluation interval: [2026-06-02T05:57:00Z,2026-09-30T05:57:00Z). Each asset has172800 evaluation bars; separate partition files include1476 prior warmup bars each. Those intentional overlapping warmup contexts are not unique extra evaluation minutes. No new SQLite derived history database was created.

| Role | UTC half-open range | Evaluation bars per asset | Warmup per asset | Receipt SHA256 |
|---|---|---:|---:|---|
| AUDIT | 2026-08-31T05:57:00+00:00 → 2026-09-30T05:57:00+00:00 | 43200 |1476| `64899a65d1d1ba050d015138348e40ac7fddb823fa4ef63cf58d26eb67b1b307` |
| CALIBRATION | 2026-06-02T05:57:00+00:00 → 2026-08-01T05:57:00+00:00 | 86400 |1476| `aaf8949d674720da54fb5b960aa9f1d28a73451ca76df008a408e710329304a8` |
| VALIDATION | 2026-08-01T05:57:00+00:00 → 2026-08-31T05:57:00+00:00 | 43200 |1476| `47d956614776f99a68c10856040d159a2de68469ec330c412a7b80892aee9668` |

All12 asset/partition canonical caches have exact counts, aligned consecutive unique open times, valid OHLC and completed bars. Duplicates=0,missing-before-repair=0,repair calls=0,unresolved gaps=0 for every cache. Each raw/canonical gzip has plaintext/compressed SHA256,source/symbol/from/to/retrieved_at/row count. Full manifests and receipts are private under `/Users/jerson/Documents/ChatGPT/crypto-monitor-phase3b-evidence-20260930`. Each partition is role/range/hash-bound. CALIBRATION values alone determine winner; acquisition of held-out files is allowed and is distinct from opening them for evaluation.

## Evaluation semantics and search

GT units are episodes, independent of candidate output. Five frozen material families:4%1h,7%4h,5%15m reversal,1.5% three-sample causal breakout,4x vol plus2.5%5m move. Same-direction material families merge;30 consecutive observed inactive minutes close; opposite selected material direction immediately starts a new episode. Concurrent opposite-family directions use frozen family priority, and conflict counts are retained. Warmup-onset episodes excluded; partition tails may be right-censored. Onset is causal; end/peak may use later canonical path. Candidate state uses30min per-rule inactivity hysteresis; activation/RULE_ADDED/REVERSAL only, no severity tiers or fixed-time silence.

A same-direction event in onset[-15min,0] receives credit. +5min late hits are separate and never raise main recall. All complete UTC zero days included in load percentiles; partial days reported separately. This contract prevents counting each sustained minute as an independent move but does not prove the conflict priority models all market episodes well.

Exactly324 global configurations evaluated,108 passed all calibration gates. Winner config_id251: **R1=3%,R2=4%,R3=8%,R4=14%,R7 multiplier=3,R7 move=2%**. Fixed R5=4%,R6 two-sample causal1%,R8=4pp,R9=6pp. No per-asset tuning. Winner SHA256: `49705c55329363e2aeb412bf66f82917e0c7050778e804ec4f1152edbe443b32`.

Deterministic ranking was rechecked against all passing rows: minimum qualifying-asset recall=1;aggregate25/25=1;combined p95/day=5;total candidate episodes=33;then lexicographically higher thresholds in frozen order. Exact Fractions were used for rank, not rounded display percentages. Complete leaderboard is config/price_rule_v2_calibration_result.json.

## Calibration and validation metrics

| Role | Asset | Episodes/hits/misses | Recall | Candidate episodes/events | Events/day | Median/p95/max full day | Unmatched events/rate |
|---|---|---:|---:|---:|---:|---|---|
|CALIBRATION|BNB|2/2/0|100.000%|4/4|0.066667|0.0/1/1|2/0.5|
|CALIBRATION|BTC|2/2/0|100.000%|2/2|0.033333|0.0/0/1|0/0|
|CALIBRATION|ETH|10/10/0|100.000%|12/14|0.233333|0.0/2/4|3/0.2142857142857142857142857143|
|CALIBRATION|SOL|11/11/0|100.000%|15/20|0.333333|0.0/3/7|9/0.45|
|VALIDATION|BNB|1/1/0|100.000%|1/4|0.133333|0.0/0/4|2/0.5|
|VALIDATION|BTC|1/1/0|100.000%|2/2|0.066667|0.0/1/1|1/0.5|
|VALIDATION|ETH|5/5/0|100.000%|8/16|0.533333|0.0/5/9|10/0.625|
|VALIDATION|SOL|13/8/5|61.538%|10/21|0.700000|0.0/5/13|13/0.6190476190476190476190476190|

Calibration: BTC2,ETH10,SOL11,BNB2 episodes;25/25 aggregate;40 candidate events,33 candidate episodes;combined p95/day5. CalibrationBTC/BNB have insufficient per-asset samples.

Validation: BTC1,ETH5,SOL13,BNB1 episodes;15/20 aggregate;43 candidate events,21 candidate episodes;combined p95/day15. **BTC/ETH/BNB = INSUFFICIENT_VALIDATION_EPISODES**, not per-asset PASS. SOL is sufficiently sampled and FAILS. Validation failures: AGGREGATE_RECALL,SOL_RECALL. All frozen event-load gates pass. Only one validation-open receipt exists and it pins original winner hash/commit.

Additional metrics, preserving exact onset vs pre-onset, lead quantiles, activation distribution and clusters:
- CALIBRATION BNB: `{"candidate_cluster_distribution": {"1": 4}, "exact_onset_hit": 2, "late_5m_diagnostic": 0, "median_lead_seconds": 0, "p25_lead_seconds": 0, "p75_lead_seconds": 0, "pre_onset_hit": 0, "rule_activation_distribution": {"R1": 1, "R2": 2, "R7": 1}}`.
- CALIBRATION BTC: `{"candidate_cluster_distribution": {"1": 2}, "exact_onset_hit": 2, "late_5m_diagnostic": 0, "median_lead_seconds": 0, "p25_lead_seconds": 0, "p75_lead_seconds": 0, "pre_onset_hit": 0, "rule_activation_distribution": {"R1": 1, "R2": 1, "R7": 1}}`.
- CALIBRATION ETH: `{"candidate_cluster_distribution": {"1": 10, "2": 2}, "exact_onset_hit": 10, "late_5m_diagnostic": 0, "median_lead_seconds": 0, "p25_lead_seconds": 0, "p75_lead_seconds": 0, "pre_onset_hit": 1, "rule_activation_distribution": {"R1": 3, "R2": 8, "R5": 1, "R7": 6}}`.
- CALIBRATION SOL: `{"candidate_cluster_distribution": {"1": 10, "2": 5}, "exact_onset_hit": 11, "late_5m_diagnostic": 0, "median_lead_seconds": 0, "p25_lead_seconds": 0, "p75_lead_seconds": 0, "pre_onset_hit": 0, "rule_activation_distribution": {"R1": 6, "R2": 10, "R5": 2, "R7": 7}}`.
- VALIDATION BNB: `{"candidate_cluster_distribution": {"4": 1}, "exact_onset_hit": 1, "late_5m_diagnostic": 0, "median_lead_seconds": 60, "p25_lead_seconds": 60, "p75_lead_seconds": 60, "pre_onset_hit": 1, "rule_activation_distribution": {"R1": 1, "R2": 2, "R5": 1, "R7": 1}}`.
- VALIDATION BTC: `{"candidate_cluster_distribution": {"1": 2}, "exact_onset_hit": 1, "late_5m_diagnostic": 0, "median_lead_seconds": 0, "p25_lead_seconds": 0, "p75_lead_seconds": 0, "pre_onset_hit": 0, "rule_activation_distribution": {"R1": 1, "R2": 1, "R7": 2}}`.
- VALIDATION ETH: `{"candidate_cluster_distribution": {"1": 4, "2": 2, "3": 1, "5": 1}, "exact_onset_hit": 5, "late_5m_diagnostic": 0, "median_lead_seconds": 0, "p25_lead_seconds": 0, "p75_lead_seconds": 0, "pre_onset_hit": 1, "rule_activation_distribution": {"R1": 4, "R2": 5, "R3": 3, "R4": 1, "R5": 3, "R7": 5, "R8": 1, "R9": 2}}`.
- VALIDATION SOL: `{"candidate_cluster_distribution": {"1": 4, "2": 3, "3": 1, "4": 2}, "exact_onset_hit": 5, "late_5m_diagnostic": 3, "median_lead_seconds": 180, "p25_lead_seconds": 0, "p75_lead_seconds": 420, "pre_onset_hit": 5, "rule_activation_distribution": {"R1": 4, "R2": 5, "R3": 2, "R4": 2, "R5": 3, "R7": 5, "R8": 4, "R9": 2}}`.

Five SOL validation misses (onset UTC):
- `gt2e:SOL:1787375640000:UP`: 2026-08-22T05:14:00+00:00.
- `gt2e:SOL:1787375760000:UP`: 2026-08-22T05:16:00+00:00.
- `gt2e:SOL:1787376000000:UP`: 2026-08-22T05:20:00+00:00.
- `gt2e:SOL:1787376240000:UP`: 2026-08-22T05:24:00+00:00.
- `gt2e:SOL:1787387880000:DOWN`: 2026-08-22T08:38:00+00:00.

Three SOL missed episodes have a late<=5min detection diagnostic; they remain misses. The clustered UP onsets on August22 deserve review of opposite-direction transitions and frozen direction priority before authorizing a new evaluation version; this report does not assert their causes from unrecorded paths or silently merge them after seeing failure. Full missed-episode price-path investigation was not rerun after the stop condition.

## Audit, V1 comparison and HYPE — intentionally not run

AUDIT is **NOT RUN**, because the sole winner failed validation. If ever separately authorized, this latest30d window must be labeled AUDIT_NOT_BLIND. There is no V2 audit recall/candidate reduction result.

ETH old20 V1 minute misses -> V2 episode mapping/resolved count: **NOT EVALUATED**, no audit permitted. SOL V1 R4=173 minute hits -> V2 audit activation count: **NOT EVALUATED**. It would be misleading to substitute calibration/validation counts or a synthetic test for this requested latest30d comparison. Original V1 baseline remains23 ETH/187 SOL candidates. Unit test does prove an unchanged84-minute R4 condition yields exactly one activation absent another rule/reversal, but this is not173->1 measured historical audit evidence.

HYPE is excluded from120d optimization. Final winner HYPE diagnostic **NOT RUN** after validation failure. Approved historical-limitation status remains FORWARD_DATA_ACCUMULATING; no forward collector was started and no30d HYPE claim made. Existing5041-bar official history remains unchanged.

## Leakage, determinism and tests

255 tests total (original214 unchanged +41 V2). Final complete suites: Python3.14.6=255 passed in1.89s;Python3.12.14=255 passed in1.79s;zero failed/skipped on both. Coverage includes GT90-minute merge,flicker/reset boundary,immediate reversal,type union,direction conflicts,R4 persistence,new-rule activation,individual rule rearm,stable sparse/minute state hashes,role/range capability rejection,GT/candidate typed-input separation,immutable winner write,committed winner mutation rejection,frozen documents byte check,one-shot validation receipt,one-winner CLI,audit write isolation,held-out process I/O guard,exact deterministic rank and noise gates. Ordinary tests use offline fixtures only. compileall,dependency checks and diff check passed;scoped credential-pattern scan passed on Phase3B additions (heuristic, not proof of absence).

Calibration optimizer accepts exactly CalibrationOnly and cannot accept VALIDATION/AUDIT capability/path; copied wrong-role receipts rejected. Price label/candidate builders expose no file reader. The process I/O audit-hook guard was added and tested during implementation; the successful calibration run started before that hook was added, so this report does **not** claim an OS-level hook trace for that executed search. Executed isolation evidence is the fixed calibration capability, loader range/hash checks, code inspection and automated rejection tests. Winner config/result byte/hash provenance is checked against its original commit, not just current editable files. No held-out metrics fed ranking and no validation-based reselection occurred.

Calibration winner and validation: sparse batch vs minute incremental candidate state hashes and event identity hashes match for all four assets. Synthetic price-feature provisional/incremental and GT episode determinism cases pass. Full independent official-feature/GT recomputation in two distinct ingestion paths was not performed; both real candidate paths share one price-derived feature/GT projection. Thus state/activation equivalence is measured, while whole-history feature/GT reconstruction equivalence is a remaining limitation, not a fabricated comprehensive PASS.

## Resources and preserved boundaries

History acquisition wall 327.2399127079989s,CPU 48.726371s,peak RSS 586.88MiB. Successful calibration wall 45.72613295800693s,CPU 45.596298999999995s,peak RSS 324.23MiB. AcquisitionRSS exceeds500MiB; this is an offline acquisition process, not a live collector acceptance result. Validation CPU/RSS was not separately instrumented; no invented benchmark.

Phase3B gzip cache bytes=58614201. Phase3B SQLite bytes=0. Existing Phase3 SQLite bytes=585121792. Combined old+new private evidence bytes=659148881 (<5GiB). Budget checked before/after acquisition; new history processed partition-by-partition with compact transition projections rather than a large derived SQLite table.

Real Gmail sends=0;third canary slot untouched;ChatGPT automation mutations=0;real private transport writes=0;production writes=0;live collector/shadow/SIGKILL/launchd/portfolio changes=0. Frank/Monster/NFT not entered.

## Decision and limitations

**PHASE_3B_FAIL_VALIDATION; PRICE_RULE_V2=FAIL; PHASE_3C=NO_GO.** Calibration100% did not generalize to the frozen episode validation. Labels are sparse, most assets lack10 validation episodes;candidate/GT numeric threshold overlap and frozen direction priority remain evaluation limitations. Unmatched events are operational noise proxies, not verified false investment alerts. The strict onset window makes late detection a miss by design. Neither a different leaderboard row nor broader grid nor normalized/per-asset rule was tried after failure. Any V3 or evaluation-contract changes need a new explicit review. Final report/validation artifact committed and pushed, then work stops.
