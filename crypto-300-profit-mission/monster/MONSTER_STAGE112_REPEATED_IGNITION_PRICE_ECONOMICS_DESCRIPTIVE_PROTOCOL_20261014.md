# Monster Stage112: original519 repeated-ignition economic attribution, source-frozen diagnostic contract

Date: 2026-10-14 Asia/Bangkok. Status: diagnostic protocol frozen before reading all Stage111 shard-level event paths. Branch: original Draft PR #30 only. Stage111 V1 remains REJECTED. This is **read-only descriptive analysis of an EXPOSED historical population**, not a new strategy, OOS test or deployment request.

## Full factual starting baseline

Frozen source population is Stage83 original 519 D0, 305 original D1, 214 original D0-only, 28 D0 early>=5m historical 2x. Stage111 V1 results archived by CI in Git blob `9473443f407deb5e4c9e7e14d64685b2e8e49cea` (original PR commit `0a5d185caf242c4546b2357de5422a2a3023bf36`).

Stage111 V1 actual: 19/28 early >=5m 2x (G2 fail), 740 PRIORITY events / 42 complete historic UTC06 days (average 17.619, peak 46, G3 fail), 598 source-complete 24h delayed-entry price-only observations (231 positive; gross median -3.504274750385354539869490800%, G4 fail), original 519 fixed anchor windows source-complete. Independently verified metadata say the 519 cases are not necessarily point-in-time crypto-only eligible, and 24h source-complete is a subset of all PRIORITY events.

Existing archived case-repeat frequency is 242 with zero PRIORITY, 110 with exactly one, 167 with >=2, including 630/740 (85.135%) of the total events. A high repeated-alert share alone does not prove later episodes are unprofitable. The difference is what Stage112 diagnoses.

## Exact immutable evidence inputs

1. Original Stage111 real Binance 1m CI workflow `monster-stage111-full519-persistent-real1m.yml`, matching **workflow head SHA `760b3605a2d1673a9765d7daeee8ffea62558507`**. Require a fully successful original run, not the more recent Stage112 push.
2. All 24 individual archived `monster-stage111-<date>-s<shard>` workflow artifacts from that **same run**, with exact six original dates and four shards. Require schema `MONSTER_STAGE111_REAL_FULL519_FROZEN_V1_OFFICIAL_1M_REPLAY`, original Stage83/110 Git blob lock and no duplicate or missing (date,symbol).
3. Recompute frozen Stage111 aggregate and compare its principal results with the already Git-archived `monster_stage111_real519_persistent_15m_v1_actual_results.json`: total PRIORITY=740, G2=19/28, complete 24h price-only outcomes=598, positive=231. If mismatch, fail closed; do not diagnose an altered sample.
4. No future HIGH/2x/5x/10x label influences grouping of events into FIRST/REPEAT; these are after-the-fact evaluation labels only.

## Diagnostics that must all be produced

A. Full 519 denominator: 0/1/2+ priorities per original D0, per-case repeat count including 0, count of all 740 events and number of source-complete 24h price paths.

B. For each chronologically sorted PRIORITY event with unique event ID, record FIRST (ordinal 1) vs REPEAT (ordinal >=2) and episode interval, the already archived 24h price-only proxy if present, whether it was censored and why; aggregate gross return median, profitable count, <=-20% risk and fee sensitivity separately. Price proxies must never be described as fills or real executable net return.

C. Per-case **first opportunity** economics separately from event-weighted economics. Do not count a coin with 13 repeated PRIORITY events as 13 independently sampled winners. Show case-weighted first-event gross return, and separately the overall case-median of complete repeated-event gross results (with selection caveat).

D. Actual first-priority G2 at least 5min before 2x for all 28 original eligible historical cases, and a supplementary "ANY PRIORITY before 2x" metric. Preserve FIRST/REPEAT distinction in the 28 cases and report all nine Stage111 misses by (date,symbol). No other trading model or threshold is applied.

E. Repeat concentration by original anchor day, source trading identity, D1/no-D1, and per-coin event count. Distinguish venues and `IDENTITY_UNVERIFIED` from confirmed crypto. Report source-unknown separately, not as losers.

F. Adversarial / causality data QA: fail on duplicate event ID, out-of-order visible time, PRIORITY timestamp outside original anchored seven-day historical window, inconsistent source receipts, impossible positive return completeness, reference-cohort mismatch and attempts to use future GT labels for ranking.

## Interpretation and gate

Stage112 is a **descriptive diagnostic**, so G2/G3/G4 are not reinterpreted as new PASS. It is intended to determine whether a **new, separately frozen, falsifiable entry-timing / attention-value hypothesis** is justified, on separate later truly unseen data. No grid, no historical top-N deleting signals, no parameter patch to Stage111 V1.

Next protocol after genuine results: if repeats dominate adverse outcomes, test the economic distinction between WATCH retention and actionable admission in a new candidate with unexposed OOS. If first-event economics are equally poor, focus on executable venue/entry price and full source economics rather than additional filters. Do not claim causation from exposed cohorts.

No changes to Stage99 local collector, Frank, installed services, current portfolio or Mission production. No scheduled workflows, Gmail or trading; `MONSTER_DEPLOYMENT=NO_GO`.
