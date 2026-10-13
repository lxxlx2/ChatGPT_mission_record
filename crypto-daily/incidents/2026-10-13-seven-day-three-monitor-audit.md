# Three-monitor weekly delivery / reliability audit
Audit date: 2026-10-13, Asia/Bangkok; interval: 2026-10-07 through 2026-10-13 (final day partial).
Authority: Gmail Sent actual IDs + readback, GitHub repo default branch report files/run finals, existing ChatGPT automation state.
No new tasks, no timetable changes and no altered monitoring scope.

## Daily authoritative email status BEFORE current recovery
| Date | Crypto Gmail | Stock Gmail |
|---|---|---|
| 10/07 | 1a11426183bfe6df | 1a113fc11be4e1ba |
| 10/08 | 1a119dac79ec41b7 | 1a119d9b4b8d44a7 |
| 10/09 | 1a1209d4664105f9 | 1a1209a71157526b |
| 10/10 | 1a1250134a5d7044 | 1a124ff190b6da75 |
| 10/11 | 1a129ba8b218cc41 | 1a129bc6cb19b381 |
| 10/12 | MISSING | MISSING |
| 10/13 | MISSING | MISSING |

## Actual GitHub run directory counts BEFORE current recovery
These are audit ARTIFACT counts, not successful invocations. Some finals contain PARTIAL or BLOCKED.
| Date | Crypto total / finals | Stock total / finals | TGE total / finals |
|---|---:|---:|---:|
| 10/07 | 9 / 7 | 2 / 2 | 40 / 21 |
| 10/08 | 14 / 10 | 6 / 3 | 37 / 15 |
| 10/09 | 15 / 9 | 7 / 3 | 33 / 16 |
| 10/10 | 12 / 6 | 7 / 4 | 33 / 12 |
| 10/11 | 9 / 4 | 7 / 3 | 33 / 16 |
| 10/12 | 6 / 1 | 7 / 3 | 34 / 14 |
| 10/13 partial day | 9 / 4 | 6 / 3 | 19 / 7 |
| Seven-day observed | 74 / 41 | 42 / 21 | 229 / 101 |
Some attempted slots were not paired with a durable final; a final marked PARTIAL or BLOCKED is not a successful scan. No unobserved slots may be backfilled as completed.

## Four user-authorized FULL daily email recoveries NOW delivered
| Date | Stream | Gmail Sent and readback | Exact archive path |
|---|---|---|---|
| Oct12 | Stock 12 sections / 51 items | 1a1346d2fd8a14ab | us-stock-daily/reports/daily/2026/2026-10/2026-10-12.md |
| Oct13 | Stock 12 sections / 52 items | 1a1346cc3e5c6f80 | us-stock-daily/reports/daily/2026/2026-10/2026-10-13.md |
| Oct12 | Crypto 13 sections / 39 items | 1a134745c66c555a | crypto-daily/reports/daily/2026/2026-10/2026-10-12.md |
| Oct13 | Crypto 13 sections / 40 items | 1a13471f2bf7eb43 | crypto-daily/reports/daily/2026/2026-10/2026-10-13.md |
Each actual Gmail Sent body was read back and archived identically, verified by fresh Git readback. Oct12 Crypto historical report explicitly used Binance official Oct12 10:00-11:00 BKK historical one-hour Klines and same-hour prior-day comparators; late Oct12 news marked historical retrospect, not claimed as available at morning send. Oct13 used Binance Spot snapshot ~15:43 BKK. The Stock source windows are Oct9 and Oct12 complete U.S. sessions respectively.

## Root causes and corrections
1. Persistent AUTOMATED external safety-check refusals for Gmail and intermittent Git create/update. Evidence: crypto-daily/runs/2026-10-12/102000-final.md, crypto-daily/runs/2026-10-13/102000-final.md and us-stock-daily/runs/2026-10-13/084400-final.md. This is an execution-layer blocker, NOT an evidence that QA passed email was sent. Interactive manual recovery worked. Prompt rewriting is NOT a proven cure, and no bypass was attempted.
2. Missing terminal collector finals despite attempts and research. Missing docs cannot count as no-news, full-source coverage or complete shard.
3. TGE shard starvation: oldest FULLY successful shard timestamp stuck at 2026-10-10 due ongoing PARTIAL/source gaps; repeatedly selecting that group displaced other scheduled groups. Fixed latest AUT0MATION_RUNTIME.md + MONITOR_SPEC.md + REGISTRY.md Oct13 with separate last_meaningful_attempt_at and last_verified_complete_at, at most one overdue override in four persisted invocations, <=2 identical shards in a row, fallback hour%4. PARTIAL never upgraded to FULL.
4. Three existing enabled automations' prompts shortened Oct13, preserving latest Git canonical, email and QA proofs, dedupe and scheduled hours; attempt+final bounded writes, delivery-first priority. Not guaranteed to resolve host safety checks.

## TGE actual ACTION review
Oct11 Space @intodotspace SPC public-sale claim UI Oct15 closing was actually mailed as 1a129b8b2ddd1607 and deduped in known-events. No further eligible unsent ACTION was established by the reviewed Oct12/13 finals. Surf NFT future member-claim countdown, Concrete extra USDC and Neutrl candidate rights remain VERIFYING due missing first-party/current personal entitlement evidence. Do not send TGE daily mail or repeat completed/refunded/excluded events.
Oct13 TGE state/current.md last confirmed partial terminal at 08:02 BKK; later 13:55 and 14:55 attempt-only records were observed with NO durable terminal at audit time. Do not claim fully successful coverage.

## Production acceptance NOT YET PASSED
Future real unattended Stock 07:40 and Crypto 09:20 runs must create actual Gmail Sent+readback and identical Git archive. Future at least 4 documented TGE hourly runs must show fair coverage of groups and honest SOURCE_GAP without repeated permanent shard1. No newly scheduled automation or modified RRULE. This audit confirms backfill completion, NOT unattended execution reliability.

## TGE fairness dry-run, NOT a live scheduling result
Eight hypothetical consecutive hours with all source reads partial: prior frozen-oldest-complete logic can repeatedly choose [1,1,1,1,1,1,1,1]; corrected evidence-unavailable fallback is local hour%4 [0,1,2,3,0,1,2,3]. Each shard attempted twice; basic fairness PASS, with actual verified complete coverage still 0. Live next-four-hour execution and Gmail automation stability remain NOT_YET_VERIFIED.
