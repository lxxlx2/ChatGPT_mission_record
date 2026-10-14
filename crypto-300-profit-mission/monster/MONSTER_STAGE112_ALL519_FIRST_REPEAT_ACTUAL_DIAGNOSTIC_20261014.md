# Monster Stage112: original519 first/repeat event economics and late-signal root cause

Date: 2026-10-14 Asia/Bangkok. Scope: original Draft PR #30, historical research only. **No strategy validation PASS.** All upstream Stage111 model thresholds, source artifacts and rejected gates remain unchanged.

## 1. Real source / method / provenance

- Protocol frozen before all-shard event-level inspection: `MONSTER_STAGE112_REPEATED_IGNITION_PRICE_ECONOMICS_DESCRIPTIVE_PROTOCOL_20261014.md`, commit `d0dff968373bf07a053e600f7dc37e3ed8b64d5f`.
- Analysis program: `../local-agent/scripts/monster_v4_stage112_repeated_ignition_diagnostic.py`, first commit `f4219a02be1911d5df41549fb19773cbb87e3f82`, followed by predeclared descriptive pairing/timing attribution addition `0d394e8abd0a8e72f9cbc92b4da4cef9935c89b5`; the model's state transitions were not changed.
- Actual machine evidence: `evidence/monster_stage112_real519_first_repeat_diagnostic.json`, Git blob `1f07c873a8cddbac5128a4b97d64cf4c6d554ba3`.
- The CI reused 24 Stage111 official-Binance 1m shards from the original workflow head `760b3605a2d1673a9765d7daeee8ffea62558507`, then independently re-ran the fixed Stage111 all519 / all42 UTC06-day aggregates against its original Git-blob-locked result `9473443f407deb5e4c9e7e14d64685b2e8e49cea`. Source Git evidence is immutable/exposed historical, NOT fresh OOS.
- Results are next-minute OPEN to completed 24h CLOSE OHLC **PRICE_ONLY** proxies, no execution evidence, and an overlapping/repeated-coin observational sample. True executable net PnL remains UNKNOWN.

## 2. What actually generates the notification load

| Historical population | Actual count |
| --- | ---: |
| Original D0 cases | 519 |
| No Stage111 PRIORITY | 242 |
| One Stage111 PRIORITY | 110 |
| At least two Stage111 PRIORITY | 167 |
| Total observed priority events | 740 |
| Unique cases with at least one priority | 277 |
| First priority events | 277 |
| Later repeated priorities | 463 |
| All events emitted by repeat-prone cases | 630 |

Repeat events account for 463/740 = 62.57% of raw alert occurrences. Repeat-prone cases produce 630/740 = 85.14% of raw occurrences. These are distinct causal episodes in an exposed simulation; **do not** call all repeats worthless or silently drop them.

Original D1 cohort: 305 cases -> 586 priority occurrences and 475 completed 24h price proxies. D0-only cohort: 214 cases -> 154 priority occurrences and 123 complete price proxies. The difference may reflect selection/concentration; it does not establish D1 value.

## 3. First vs repeat price-only economics

| Actual price result | FIRST | REPEAT |
| --- | ---: | ---: |
| Total priority events | 277 | 463 |
| 24h completed price proxy | 237 | 361 |
| Positive 24h price proxy | 83 | 148 |
| <= -20% 24h gross loss | 17 | 40 |
| 24h gross median | -3.247723875526566% | -4.070466570466570% |
| Artificial 20bps each-side cost sensitivity median | -3.633960506761989% | -4.453418799726185% |

The repeat price-proxy median is worse, but the positive repeat share is somewhat higher (148/361 versus 83/237); the tail/mix cannot be summarized as repeats always losing.

**Case-level paired comparison**, only cases with both first and at least one repeat completed 24h proxy: 137 cases, first gross median -2.073365231259968%, within-case repeat-median gross median -4.103343465045593%, median within-case repeat-minus-first -1.239269396016938 percentage points, 62 cases better, 75 cases worse. This is descriptive within exposed dates, not causal and not independent transaction samples.

## 4. Why early-warning remains broken

Recompute the 28 historical D0 signals that predated first 2x by >=5m using first actual Stage111 PRIORITY time:

- 19: FIRST PRIORITY >=5m before first 2x.
- 8: FIRST PRIORITY **AFTER** the first 2x had already happened.
- 1: no PRIORITY at all.

All nine failures remain accounted for in the machine evidence, including original high-profile MYXUSDT, AIAUSDT, BANKUSDT, JELLYJELLYUSDT, MMTUSDT. Do not count a late signal as a successful pre-2x alert. Stage111 G2 **still fails** at 19/28 <80%.

This signals two separate deficits: (a) valuable early D0 information is lost between watch and attention/priority, and (b) delayed entry into price acceleration often has negative 24h economics. Solving alert volume alone would not solve either.

## 5. Engineering observation, NOT a reason to deploy

The Stage111 research engine computes raw `event_id` from D0 timestamp, observable event time, state and local ordinal, omitting the venue-qualified symbol. Stage112 actual all519 event inspection found **62 raw ID values shared across different date-symbol cases**. This is a notification/outbox collision hazard if raw Stage111 identifiers were ever re-used globally. Current stage112 reports use fully scoped `date:symbol:event_id` identity; the rejected Stage111 source engine and historical evidence were left untouched. When a future strategy reaches the delivery gate, a venue/asset-qualified identity and a duplicate-restart test are required. No live outbox was changed.

## 6. Decision and next highest-value work

`STAGE112_DESCRIPTIVE_DIAGNOSTIC=DONE_WITH_ARCHIVED_REAL519_SHARDS`.
`STAGE111_V1=REJECTED`; `NEW_OOS=NOT_DONE`; `REAL_EXECUTABLE_NET=UNKNOWN`;
`OTHER_AI_REVIEW_OF_NEW_MODEL=NOT_DONE`; `MONSTER_DEPLOYMENT=NO_GO`.

These data refute the idea that simple repeat-alert dedupe or waiting longer after D0 is sufficient. The highest-value next research question is **how much of the negative 24h return is present within the first 5/60/360 minutes after the actual causal signal, versus later price reversal**, and whether the weak 24h average is primarily price timing, instrument identity, or crowding. Define exit horizons before re-reading future minute outcomes and report all cases, including censored ones, with event-weighted and case-weighted results. This is descriptive research only; it cannot authorize an edited strategy on these already exposed six windows.

A genuinely new executable strategy must freeze admission/entry/exit rules before an independent unseen period, verify point-in-time venue eligibility plus real order book/fee/notional, pass the original G0-G6 standards and other-AI review before any Mac deployment request. No changes to Frank, Stage99 collector, other Mission modules, scheduled tasks, real Gmail or trading in Stage112.
