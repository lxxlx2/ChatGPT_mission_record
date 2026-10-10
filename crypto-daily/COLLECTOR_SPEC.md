# Crypto Hourly Collector Spec — V2 (2026-10-10)

Mode: FACTUAL_NEWS_COLLECTOR
Active schedule (user-authorized 2026-10-10): ordinary collector 00:20/03:20/06:20/12:20/16:20/20:20; prebuild 08:20; primary 09:20; recover 10:20/11:20, all Asia/Bangkok. Historical 15:10/19:10/23:10 notes below are retrospective only.
Timezone: Asia/Bangkok
Authority: existing `Crypto 每日情报` task; actual schedule and Gmail unchanged.
Scope: same REPORT_SPEC.md categories; do not add a task, extra alerts, permanent ticker/project watches or paid feeds.

## Problem addressed
The former `hour % 3` shard rule was wrong for actual ordinary collector hours
`00:10, 03:10, 06:10, 15:10, 19:10, 23:10`: it assigned four of six runs
to shard 0 and only one each to shards 1 and 2. Publication near/after 19:10,
missing finals, official releases not covered by generic security searches, and
the absence of independent pre-send discovery caused demonstrable omissions.

## Execution order — bounded and factual
1. Read current task canonical and the previous two actual completed collector
   finals. Write one small `runs/YYYY-MM-DD/HHMMSS-attempt.md` before research
   if possible (one retry maximum). Do not use a provisional final.
2. Core market/risk: BTC/ETH/SOL spot, unusual liquid movers, existing deadline
   watch and the SECURITY_SOURCE_POLICY mandatory CEX, wallet-user-loss and
   official protocol security checks. A query without a real result/receipt does
   not prove coverage.
3. **Cross-domain headline discovery, EVERY collector**, independent of shard:
   issue a bounded English discovery batch using news index/search for:
   - urgent chain/protocol/wallet/exchange security, critical patch or shutdown;
   - nation/regulator/major-chain policy, market access or macro change;
   - ETF/issuer/exchange/whale/funding and unusual market structure;
   - significant existing-scope ecosystem, RWA, stablecoin, TGE/deadline, NFT
     or early-market development.
   Typically use 4 focused batched searches, plus up to 2 source-specific
   lookups on highest-impact NEW leads. Record actual queries, timestamps,
   result URL(s), and coverage errors. This is a DISCOVERY pass, not proof
   every website worldwide was checked. X/Reddit inaccessible -> indexed
   English sources / official first-party websites; mark direct sources missing.
4. One **deep shard**, with the original scope unchanged:
   0 social/NFT; 1 ecosystem/primary market/TGE/RWA/PM;
   2 institutional flows/macro/policy/derivatives/deep security.
   Choose from the last **two successfully persisted deep-shard completions**:
   prefer the shard missing from those two when they differ; if identical,
   choose the next one cyclically. If history unavailable, use fallback mapping
   `00=0,03=1,06=2,12=0,16=1,20=2` (not wall-clock modulo).
   A partial/attempt-only run does not count as a completed shard. At the
   next available collector prioritize the missed shard. Log
   `planned_shard, executed_shard, last_two_complete_shards, backlog_shards`.
   Aim for all three shards in any three successful covered collector runs;
   do not claim this property when artifacts or sources are missing.
5. Persist a compact event ledger in the SAME existing research/final artifacts:
   `event_key, category, first_seen_at_bkk, source_published_at, checked_at,
   source_url, source_tier, claim, confirmed_facts, unverified, materiality,
   status, candidate_next_step`.
   Status is DISCOVERED / VERIFYING / VERIFIED / DISMISSED / CARRIED.
   Discovery is NEVER synonymous with endorsement or verified loss/trade.
   Keep up to eight ordinary candidates; HIGH materiality candidates are
   separately carried until verified, disproved or explicitly reasoned out,
   and must not silently vanish because eight ordinary slots were full.
6. Terminal audit: write exactly one factual `HHMMSS-final.md`; if blocked,
   retry one compact `HHMMSS-final-retry.md`. Preserve at minimum coverage
   matrix, real links, unresolved high-impact event keys, gaps, actual
   research persistence and failure reason. Missing final => UNHEALTHY.
   Report `success` only if core+cross-domain+deep shard+durable final
   completed; otherwise PARTIAL with explicit missing lanes. No invented
   `checked_no_update` from unavailable providers.

## Daily publisher and recovery handoff
At 08:20, read the previous 24h research AND finals, including failed or
missing hours, plus a 48h carry-over for new official critical disclosures
and previously missed material leads. Independently run the same cross-domain
headlines batch against the *since-last-sent* period; do NOT treat a missing
collector report as proof of no events. Record every HIGH candidate with
`included_section` or `excluded_with_reason` in the delivery manifest.
A source publication AFTER today's sent email is due in the next ordinary
collector and next eligible formal report, not retroactively a false omission.

At 09:20, 10:20 and 11:20, dedupe Gmail Sent first, refresh core quotes
and highest-impact headlines/official material updates, do all latest
REPORT_ACCEPTANCE pre-send checks and CR-18/19, then send only a complete
13-section QA-PASS email. A source/provider gap requires explicit internal
`PARTIAL_COVERAGE`; do not invent facts and do not automatically suppress
a verified report solely because one optional platform is unreachable.
Missing discovery attempts/manifest, however, cannot count as QA_PASS.
Sent + readback + identical Git archive are separate delivery evidence.
Never send a second normal email for the same date.

## Stable regression scenarios
- Oct 6 Abstract L2 wind-down: chain shutdown/forced migration headline.
- Oct 9 Ledger multiple user wallet drains: allegations first; amount/causation
  NOT confirmed by reposts; later issuer acknowledgement is a state change.
- Oct 9 XRPL critical inflation-potential overflow disclosed AFTER Sep 25
  patch: official severity and patch dates distinct from real exploitation.
- Oct 9/10 national blockchain network policy: actual government/industry
  policy vs no token-launch or trading legalization inference.
- Any scheduled hour with no final: backlog must not be called covered.
The collector is factual research only: no personalized trading instructions,
wallet signatures, NFT mint links, or unverified token purchases.
