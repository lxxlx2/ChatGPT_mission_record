# Crypto Daily Acceptance Gate

Updated: 2026-10-02 Asia/Bangkok
Status: canonical pre-delivery QA

The official Crypto Daily can be sent only when all hard gates pass.

## CR-01 Fixed structure
Exactly the REPORT_SPEC 13 first-level sections in canonical order.

## CR-02 24h input manifest
Before drafting, build a delivery manifest covering the previous 24h:
- hourly research/final artifacts seen;
- missing scheduler hours;
- market/derivatives facts;
- security receipts/candidates;
- TGE/claim material state;
- institutional/ETF/whale flows;
- protocol/infrastructure/ecosystem candidates;
- Early/Meme/NFT discovery candidates;
- macro/cross-market inputs;
- active user private-market rights.

Missing hourly artifacts must be visible in the manifest. Missing data cannot be silently interpreted as no event.

## CR-03 Market core
BTC/ETH/SOL current 24h price/range/volume when available, plus material relative-strength outliers.

## CR-04 Security carry-forward
Every material security candidate from the prior 24h is either included in Section 9 after fresh verification or listed in the internal audit as omitted with concrete reason. Major-CEX account-security receipts follow SECURITY_SOURCE_POLICY.md.
The security input manifest must include the existing wallet-user-draining discovery receipt defined by SECURITY_SOURCE_POLICY.md, with an actual English-query/source result and `checked_at`. The absence of a wallet-security receipt is `SECURITY_COVERAGE_GAP`, not proof no hardware-wallet/user-drain incidents occurred. A high-impact user-wallet allegation with direct user/researcher evidence but unresolved manufacturer cause/aggregate loss belongs in the internal unresolved-candidate audit and may be described in Section 9 as unconfirmed when materially safety-relevant; it must never be upgraded to a confirmed exploit or reported audited loss without supporting evidence. Do not add redundant coverage or loosen CR-18/19. 

A first-party critical protocol security advisory published within the prior 48h must be searched and evaluated even when the exploit was patched earlier or caused no known losses. An official advisory identified after yesterday's delivery and omitted from that edition is a material 24h newly discovered candidate for the next Section 9. Require a true official-advisory source receipt or label SECURITY_COVERAGE_GAP; do not declare discovery complete on exchange-account or wallet-drain checks alone. XRPL Oct 9 xrpld 3.4.1 disclosure is an explicit Oct 10 missed item awaiting next-day carry-forward; no actual unlimited mint can be claimed without evidence. Read crypto-daily/research/2026-10-10/xrpl-overflow-official-triage.md. Preserve CR-18/19 and all QA gates.

## CR-05 TGE/rights freshness
Section 7 consumes only current/actionable TGE/rights state. User-known/closed/refunded/expired events are not recycled as new information. When possible, use the canonical TGE monitor state rather than rediscovering stale events.

## CR-06 Early/Meme/NFT coverage
Section 8 may say no material candidate only if the relevant discovery lane actually ran or the manifest records its source gap. A lane that did not run cannot be rewritten as “no opportunities”.

## CR-07 Institutional/on-chain coverage
Material ETF/fund/exchange/whale/market-structure changes are checked and separated from stale historical context.

## CR-08 Macro/cross-market coverage
Material rates/oil/USD/equity/geopolitical drivers are checked when relevant.

Within existing regulation, policy and chain-infrastructure coverage, the input manifest must include an English-language check of material new sovereign/national economic and digital-infrastructure policy announcements. Include a direct government/regulator English release when accessible and independent English reporting for specific blockchain/crypto implications. A top-level nationwide blockchain-network directive qualifies for an actionable *policy-news candidate* even without an immediate public-token market reaction; separate old planning from a new policy publication, permissioned state infrastructure from permissionless L1, and confirmed proposals from launched networks. Source receipts must record published_at, checked_at, original authority and any untranslated/unavailable provision. No verified change = short coverage note; missing source receipt = POLICY_COVERAGE_GAP, not 'no update'.

Regression: CPC Central Committee/State Council Oct 9 2026 national blockchain-network policy was absent from the Oct 10 23:14 collector despite English Oct 10 reports. Record `china:20261009:new-quality-productive-forces:national-blockchain-network` and read `crypto-daily/research/2026-10-10/china-national-blockchain-network-policy-triage.md` in the next eligible complete daily. This is within existing policy/infrastructure scope; no new alert, task or ticker watch. CR-18/CR-19 dedupe, factual source tiers and no-token-speculation rules remain unchanged.

## CR-09 Deduplication
Unchanged prior-day conclusions are not repeated as new. Carry-forward is allowed only when still decision-relevant and clearly identified as ongoing or when a material delta exists.

## CR-10 No recovery downgrade
Primary, recovery, manual resend and correction all use the same full 13-section content contract. A short digest/patch can never silently become the official report.

## CR-11 Delivery integrity
- Gmail send + readback;
- canonical GitHub archive + readback;
- exact body equality after YAML metadata;
- prior incomplete/superseded same-day versions recorded.

## CR-12 Quality-collapse guard
Compare against trailing 5 latest complete formal reports. If body length <70% of median OR numbered-item count <70% of median, QA fails unless a genuine low-event reason is documented and CR-01 through CR-09 all still pass. Provider failure, recovery mode or time pressure are never sufficient exceptions.

## CR-13 User-visible cleanliness
Monitoring-health details, run failures, QA mechanics and persistence plumbing stay out of the report body. Audit-only: omission explanations, old-item suppression reasons, source-coverage/process explanations, scheduler/Gmail/GitHub/recovery/prebuild/pending/canonical details. If there is genuinely no decision-relevant update for a section, use one short neutral line such as `无高置信新增。`.

## CR-14 One logical event = one user-visible item
Before delivery, every numbered item must be assigned an internal `event_key`. Status + caveat + next checkpoint for the same event belong in the same item. Two adjacent items with the same event_key are an automatic QA failure unless they are truly independent user actions.

## CR-15 Cross-section event dedupe
Build an internal pre-send event map: `event_key -> sections/items`. A logical event gets one primary detail section. A second occurrence is allowed only as a short Top-5 summary or when it adds a distinct user decision dimension that cannot be expressed in the primary item. Repeated status, disclaimer or conclusion is forbidden.

## CR-16 Item decision-value gate
Every numbered user-visible item must contain at least one of: a new/materially changed verified fact; a current quantitative market/state observation; a concrete user-relevant risk/opportunity/action; or a specific future checkpoint with date/time/threshold.

## CR-17 Mandatory pre-send lint
Before Gmail send, require PASS for:
1. structure_lint
2. meta_prose_lint
3. same_event_item_lint
4. cross_section_dedupe_lint
5. decision_value_lint
6. stale_rights_lint
7. freshness_lint
8. repetition_budget_lint
9. section_substance_lint
10. top5_count_lint (1–5 high-impact verified items, fewer than five when justified)
11. high_impact_candidate_accounting_lint
12. cross_domain_discovery_receipt_lint

Any FAIL means `QA_FAIL_NO_SEND`. Rewrite and rerun lint before sending.

## CR-18 Repetition budget
A single event may appear at most twice in the entire email: once as a one-sentence Top-5 summary and once in its primary detail section. A security event detailed in Section 9 must not also be restated in Sections 6, 11, 12 and 13. A future dated checkpoint or concrete user action should be merged into the primary item whenever possible. Only a genuinely separate action/deadline may justify a second non-Top-5 occurrence, and then the Top-5 duplicate must be dropped.

Hard fail examples:
- same Bitget status in Top 5 + Security + Catalysts + Watchlist + Action;
- same NEAR exploit in Top 5 + Protocol + Security + Catalysts + Action;
- BTC/ETH/SOL relative-strength repeated unchanged in Sections 2, 3, 12 and 13.

## CR-19 Section substance and breadth
- Section 1 contains at most five genuinely important and independently supportable items. The existing fixed heading `今日最重要的5件事` is a capacity label, NOT a quota: when only 3–4 material events exist, write 3–4, never fabricate or pad to five. The top5_count_lint rejects >5 and filler and accepts fewer when the event ledger supports that count.
- Section 2 is the canonical home for BTC/ETH/SOL core tape.
- Section 3 must focus on mature-market movers/persistent trends beyond merely restating Section 2. If a liquid asset moves roughly >=5% in 24h, >=15% in 7d, or has a major catalyst/volume shock, investigate it. If none qualifies, one short line is better than recycled BTC/ETH/SOL prose.
- Section 5 prioritizes actual ETF/fund/exchange/whale capital movement. Analyst price targets alone do not satisfy institutional-flow coverage.
- Section 6 is for protocol/infrastructure/ecosystem developments that are not already security items.
- Section 11 contains only future catalysts not already fully described elsewhere.
- Section 12 contains persistent trends/opportunities with distinct multi-period evidence or a concise no-update line; it may not simply repeat Section 2 prices.
- Section 13 contains only concrete portfolio/risk actions that follow from the day’s evidence. It may reference an earlier item briefly but must not restate the event narrative.

## State machine
DRAFT -> INPUT_MANIFEST_READY -> PRE_SEND_LINT_PASS -> QA_PASS -> GMAIL_SENT_READBACK -> GITHUB_ARCHIVED_READBACK -> DELIVERED

If Gmail succeeds but GitHub archive fails, repair GitHub only and do not resend.

## Existing-scope chain shutdown / forced migration regression guard (2026-10-07)
Within existing chain-ecosystem, infrastructure, security and cross-market coverage, daily prebuild and pre-send discovery must include fresh English searches for a confirmed chain/L2 shutdown, sunset, wind-down, permanent halt, forced asset migration, bridge withdrawal deadline or loss of access. This adds no new monitored asset, user-specific alert, or automation.

A confirmed material chain-termination announcement is eligible for the formal Crypto Daily under Section 6 or Section 9, even when that project is USER_SUPPRESSED inside the separate TGE/airdrop rights monitor. TGE suppression applies solely to its user-specific rights discovery/notifications; it does not erase market-wide material infrastructure news. Maintain original user suppression and never reactivate user-specific TGE alerting without explicit user instruction.

For each candidate, verify the official announcement, chain identity, effective shutdown date, actual migration/bridge steps and loss-of-access risks. Include exactly one primary detailed report item with material user-relevant safety action, and at most one Top-5 short summary if truly high priority. Warn about fake migration websites; never present an unverified migration link as trusted. If key fields remain unavailable, record the gap in internal audit, without asserting the chain remains operational or claiming comprehensive discovery.

Regression incident: Abstract/ABS announced on 2026-10-06 that Abstract L2 will end on 2026-12-15, with users asked to migrate funds before the deadline. The 2026-10-07 formal Crypto Daily omitted this major chain shutdown despite the pre-delivery window; keep this omission in the quality audit. The user's separate Abstract/ABS TGE suppression remains unchanged.

## CR-20 Discovery coverage, importance and survival — 2026-10-10

The authoritative bounded collector and pre-send discovery protocol is `COLLECTOR_SPEC.md` V2. Verify:
1. A real cross-domain English headline discovery attempt covering existing scope (critical security/chain stoppage, regulation/policy, market/ETF/flows and major ecosystem/rights) was performed no later than pre-send. Source receipt contains actual query/category, checked_at, returned source URL and unavailable/fallback status. A name-only `checked_no_update` is NOT evidence.
2. Deep shard selection derives from the last two actually completed persisted collector shard records. **Never use wall-clock hour modulo 3** against the existing sparse schedule. A missed/partial shard is not a completed scan. If old collectors are missing, log the gap; independently refresh critical recent news before sending.
3. An event manifest tracks `event_key, claim, source_published_at, first_seen_at, actual source, confirmation_state, materiality, primary_section, excluded_reason`. Every HIGH materiality candidate from prior research/finals (including last 48h previously omitted official disclosures) is either addressed in ONE report detail section or excluded with an evidence-based reason. An eight ordinary-candidate cap cannot silently drop HIGH items.
4. **Separate discovery from verification.** Serious but unconfirmed user reports remain internally `VERIFYING`; confirmed official fixed vulnerabilities remain material even when there was no theft; do not imply manufacturer compromise or actual token inflation from hypothetical attack severity. Cross-domain candidate gate does not require a token/CA to exist.
5. The 08:20 prebuild and the 09:20/10:20/11:20 full publisher/recovery independently refresh high-impact news since the previous authoritative sent email, instead of assuming hourly collectors were complete. News published after a prior day's send is first eligible for the next collector/next normal report.
6. A network/source blockage must not be falsely marked checked or trigger invented content. If bounded English alternative retrieval was attempted and the mandatory material facts for a complete report are independently verifiable, a single optional social/specialist outage may be recorded as PARTIAL_COVERAGE in internal audit without causing an automatic Gmail miss. If discovery was not attempted at all, `discovery_coverage_lint: FAIL`; repair in the same invocation. Delivery still requires all other full-report hard gates.
7. Report quality and operation health are independent. `DISCOVERY_OK`, `CONTENT_QA_PASS`, `EMAIL_SENT_READBACK`, and `GIT_ARCHIVE_EQUAL` are separately evidenced states. Neither a final run log nor a generated report is proof of sent Gmail; Git outages do not authorize fabricated completion or duplicate sends.

Regression inputs: Abstract chain shutdown, Ledger multi-user-wallet allegations, official XRPL 3.4.1 fixed critical disclosure, Oct 9 national blockchain-network directive, and absent collector finals. No new task, notification channel, watchlist category or timetable is authorized.

## CR-21 Cross-day and cross-monitor event delta gate — 2026-10-16

**Mandatory hard gate for any formal primary/recovery/correction edition, in addition to CR-01..CR-20.** Before building sections 1, 7, 8, 11 and 13:
1. Read the most recent authoritative Sent/readback Crypto daily (at least previous 3 calendar days if available), plus existing `airdrop-tge-monitor/state/known-events.md` and Gmail Sent event notifications. Build a compact persisted `event_key -> first_published_at, last_user_notified_at, source, status, material_delta` ledger; do not rely on keyword overlap or remembered no-action status. A sent TGE ACTION event is **already user-known** in the Crypto daily as well.
2. For every TGE/claim/airdrop/entitlement/closing candidate, compare what **changed since the most recent user-facing delivery**, not just whether an old deadline is still upcoming. Without a separately verified new eligibility rule, token/allocation quantity, opened claim/eligibility checker, changed deadline, extended/reopened venue, new rights-provider commitment, or new risk materially affecting the user, mark `NO_MATERIAL_DELTA`. Suppress from all user-facing sections, including “previously alerted”, “awaiting official update”, “no re-alert”, source-gap exposition and outdated reminders. Those statements belong in internal ledger only.
3. `Space:spc_public_claim_dapp_sunset:2026-10-15`, `surf:surfboard_member_claim_open:2026-10-15`, and `standx:winddown_dusd_airdrop:2026-10-15` are regression examples: initial already-delivered notices MAY NOT consume the next day's report merely to repeat their status. Historic Space shutdown reminders repeated in October 12-16 formal dailies despite the October 11 email, and Surf/StandX were repeated on October 16 after the October 15 separate notices. This is a confirmed QA miss.
4. Material NEW partner/cross-issuer entitlements to an EXISTING registry project's user community are new distinct event keys, even when the underlying old project alert was delivered. Example `neosoul:dna_standx_community_allocation:2026-10-15` is NOT the same event as `standx:winddown_dusd_airdrop:2026-10-15`. The beneficiary relationship must be discovered and represented, keeping source tier and personal eligibility separated. The Binance Wallet DNA Alpha release is a separate `neosoul:dna_binance_alpha_release:2026-10-16`; avoid conflating Alpha Points claims with the proposed StandX community allocation.
5. If zero verified material TGE delta exists, Section 7 keeps its fixed heading and writes only `无高置信新增。` . An unresolved material *new* claim may appear with explicit uncertainty only after a fresh attributable source and high-impact relevance check; do not invent a claim link, snapshot, allocation or user qualification.
6. Hard FAIL `cross_day_rights_dedupe_lint` if any old event without a material delta is repeated in user-facing prose or if a newly discovered, attributable high-impact partner compensation candidate is silently omitted from the internal candidate ledger. Also log `candidate_discovered_at, source_published_at, source_tier, last_sent_date, dedupe_key, included_or_excluded_reason`. Do not send when FAIL. Fix in the same authorized delivery/recovery window; preserve all other CR gates.


## CR-22 Section-local numbered-item continuity — 2026-10-17
Mandatory for original report, prebuild, recovery, manual resend and correction. Exactly 13 canonical top-level sections; under EACH heading, numbered user-visible items start at （1） and increase by one without gaps or duplicates until the NEXT top-level heading. Restart at （1） in each section. Never use global numbering across the full email. A section with no items may use \`无高置信新增。\`; no phantom number.
Run an independent pre-send parser over the FINAL email body (not the draft or old Git file): for every canonical heading, extract only its own full-width numbered lines, compare sequence against 1..N, and FAIL \`section_local_numbering_lint\` if any section begins at 2 or inherits the preceding section's counter. Exactly the same byte string must be sent, read back and archived; the parser must run again on Gmail-readback text. Corrections are authorized only with an explicit \`｜修正版\` suffix after checking Sent and archiving supersession metadata; an already-delivered identical corrected subject must never be sent twice.

## CR-23 Multi-exchange restricted-counterparty / funds-provenance risk — 2026-10-17
A mandatory high-materiality discovery and accounting gate under EXISTING CEX, regulation and account-security coverage (no new monitor or ticker watch).
- Daily prebuild and every send/recovery slot must check material newly announced changes in deposit/withdrawal restrictions, named sanctioned counterparties, associated exchanges, freezes, compliance holds, forced account terminations, and direct/indirect source-of-funds review across major CEXes. Aggregate BY COUNTERPARTY, not by ticker or venue in isolation. A material worsening by exchange #3 is a distinct delta, even if exchanges #1/#2 restricted that counterparty months ago. Source receipt requires exact issuer/legal entity, announcement/update time, effective date, affected direction, direct/indirect scope, stated MAY/WILL consequence and the original official URL or a clear SOURCE_GAP with attributable English evidence.
- High materiality when it potentially causes blocked user funds, rejected withdrawal/deposit, trading restrictions or account termination; never suppress because the underlying sanctions or two other exchanges' restrictions are older than 24h. Put one substantive detailed item in Section 9 or 4 and at most a one-sentence Section 1 highlight; user action may be summarized without retelling the same story.
- Do not conflate HTX (formerly Huobi, Huobi Global SA) with Huione/Huobi-issued tokens or generic asset holdings. This applies to counterparty and provenance links, NOT every coin once traded on HTX. Distinguish direct transfers from merely having touched intermediaries, platform enforcement from government sanctions, and confirmed official wording from later secondary attributed claims.
- Regression: Binance official Aug 14 restriction effective Aug 23, Bitget first-party Aug restriction effective Aug 23, Bybit Sep 23 restricted-counterparty list include HTX; Oct 16 2026 English reporting states Bitget newly intensified enforcement and expanded list, while the direct NEW English official post remained SOURCE_GAP at review. Oct 17 formal Crypto daily entirely missed the material new Bitget cross-venue update. This omission is a \`high_impact_candidate_accounting_lint\` FAIL until represented in next eligible full correction. Treat first party vs corroboration honestly.
- Archive source/effective dates, which specific venue changed today, user risk, unresolved first-party, and \`event_key: bitget:restricted-counterparty-htx-direct-enforcement:2026-10-16\`. \`cex_restricted_counterparty_delta_lint\` FAIL if verified material candidate is omitted. No instructions to evade sanctions, no unsafe bridging workaround, no fabricated user balances, no trade recommendation merely from sanctions news.
