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

## 2026-10-16 cross-project beneficiary discovery and delta-first input

Every existing bounded headline discovery / 08:20 prebuild / 09:20 publisher / 10:20-11:20 recovery must perform a bounded, English, *event-centric* sweep for material newly-issued rewards/compensations by third parties benefiting communities in the current TGE Registry (including StandX), without adding those third-party issuers to the independent full-time monitored project roster. Search concepts: `<tracked project> community compensation airdrop`, `<tracked project> holders allocation`, `<tracked project> points special distribution`, `<tracked project> users snapshot`, plus official Binance Wallet Alpha launch announcements when connected to already tracked rights.

Carry confirmed source URL and publication date, beneficiary, issuer, program, claim-open status, snapshot status and event key into the pending manifest. Secondary news reports are discovery leads, not proof of user eligibility. Never reject the whole story merely because the original issuer is not itself a TGE shard member. Regression: October 15 NeoSoul DNA promised StandX community allocation and October 16 Binance Wallet Alpha listing were overlooked, while previously delivered Space/Surf/StandX incidents repeated in daily reports. Apply `REPORT_ACCEPTANCE.md` CR-21 before composing the user-facing Section 7; other security and market breadth remain unchanged.


## 2026-10-17 existing CEX-risk multi-venue sanctions/counterparty discovery
In the bounded security/venue/policy headline lane, require an English current-materiality sweep of \`<major exchange> newly restricted counterparties deposits withdrawals\`, \`<major exchange> source of funds AML hold freezes sanctioned exchange\`, and new/enhanced official help-center/legal-terms changes for Binance, Bybit and Bitget plus any newly impacted relevant major CEX. Keep venue and restricted ENTITY identities in one event ledger. A third venue's upgraded enforcement is a new incremental event despite two old venue restrictions; do not decide \`already known\` from HTX keyword repetition. Require per-venue official URL, date and enforcement scope. If first-party 2026-10-16 Bitget social/legal post cannot be read, label original \`SOURCE_GAP\`, keep secondary attributable coverage with explicit uncertainty. Coverage must be evaluated in prebuild AND at publisher/recovery, independent of missing historical collector finals. Preserve no new task/alert policy.

## 2026-10-21 P0 major labeled onchain transfer discovery (existing lane, no new task)
The existing BTC/ETH/SOL onchain/whale/institution research MUST include a bounded independent primary-English sweep of fresh Arkham Research (<https://info.arkm.com/research>), Arkham-tagged transaction reports, Lookonchain/Onchain Lens original posts and an accessible public BTC explorer as source/identity cross-check. Minimum topic queries: "Arkham BTC whale Coinbase Prime government wallet transfer 24h", "site:info.arkm.com/research Bitcoin BTC October YYYY", and "Lookonchain large BTC exchange deposit transaction YYYY-MM-DD"; search 1-2 pages per lane rather than requiring expensive Arkham account/API. No GMGN, subscription, or added automated monitor.

When a labeled transfer has contemporaneous value >= USD 10m, government/exchange involvement, dormant coin reactivation, known fund/entity movements, or material exchange-deposit risk, produce a candidate EVEN IF same source identity made equal-sized transfers previously. Use TXID, date, origin wallet and tranche ordinal to distinguish events. Never dedupe by asset, rounded amount, entity or destination alone. A 500 BTC fifth transfer is new even though 500 BTC happened four times earlier. Distinguish onchain transfer from sale, Arkham entity attribution from governmental confirmation, and recipient exchange deposit from executed disposal. Source unavailable: record \`source_gap\` plus query timestamp and fallback; do not claim the lane fully checked or fabricate TX decoding.

Real incident regression: Arkham Oct20 2026 reported fifth distinct Clifton Collins 500 BTC (~$41.5m) transfer to a Coinbase Prime-tagged destination with TXID eb0bde50049e924590a1812af2d2699c13d513415d3f03bbe3d10f316b3d6756. The Oct21 full 65-item report omitted it entirely. Evidence is in research/2026-10-21/clifton-collins-arkham-fifth-500btc-missed.md. Existing CEX restrictions, ETF, security, NFT and rights lanes continue unchanged.

## 2026-10-21 Arkham source scanner implementation (actual Git source)
The bounded, no-paid-API, read-only Node source collector is crypto-daily/scripts/arkham_primary_discovery.mjs; offline fixtures crypto-daily/tests/test_arkham_primary_discovery.mjs. It looks at original info.arkm.com/research and /sitemap.xml, sorts dated sitemap candidates newest-first, fetches up to 24 original articles in batches of 8 with 6.5-second HTTP timeout and manual redirect policy, never follows third-party domains, extracts source dates, BTC amounts, TXIDs when actually linked and a HIGH_REVIEW candidate for a labelled large BTC movement. It prints JSON source receipts and source gaps. It does NOT assert complete on-chain transaction coverage or proven wallet beneficial ownership. A 403 or unreadable page is PARTIAL_SOURCE_GAP, NOT no whale activity.
When an executor with Node and public internet exists, invoke node crypto-daily/scripts/arkham_primary_discovery.mjs and retain actual JSON evidence; separate first-party TX verification and use daily_event_gate.mjs on the final complete report. In the ChatGPT task environment where Node cannot run, do not claim this script executed: use actual web searches of Arkham first-party article publication windows, Lookonchain/Onchain Lens, explorer and original exchange notices, save manual source-receipt status, then perform equivalent event/version/dedup decisions. Do not silently skip discovery. Test command: node --test crypto-daily/tests/test_arkham_primary_discovery.mjs crypto-daily/tests/test_daily_event_gate.mjs.
Concrete regression: October 20 2026 fifth distinct Clifton Collins-tagged 500 BTC transfer reported by Arkham was omitted from originally delivered Oct21 email and is now present in corrected Oct21 Gmail ID 1a15c6d25715d6ca, with the specific transaction identifier preserved. Future no-material-delta repeats must be suppressed using the event ledger.

## 2026-10-21 discovery to editorial interface (Git control plane)

The existing bounded primary-source discovery runs before any report ranking. Reuse the EXISTING collector and deep-shard cadence. In every actual source receipt include lane, concrete English query/original source URL, checked_at, observed result URL(s) or real source_gap/error. The output is CANDIDATES, not ready-to-email prose. Feed the candidate list to `PIPELINE_CONTRACT.md` and machine routing `EDITORIAL_RULESET.json` with source tier, event key, version, user relevance, independently supported global impact and data freshness. Never put BALANCE CCA bid under global Top5 merely because it is personally relevant. Major labelled BTC transfers remain discoverable independently of whether a same-size earlier transfer existed. Git-only evidence/lookup and ChatGPT monitor; no user Mac agent or new GitHub Actions schedule.
