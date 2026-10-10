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
10. top5_count_lint

Any FAIL means `QA_FAIL_NO_SEND`. Rewrite and rerun lint before sending.

## CR-18 Repetition budget
A single event may appear at most twice in the entire email: once as a one-sentence Top-5 summary and once in its primary detail section. A security event detailed in Section 9 must not also be restated in Sections 6, 11, 12 and 13. A future dated checkpoint or concrete user action should be merged into the primary item whenever possible. Only a genuinely separate action/deadline may justify a second non-Top-5 occurrence, and then the Top-5 duplicate must be dropped.

Hard fail examples:
- same Bitget status in Top 5 + Security + Catalysts + Watchlist + Action;
- same NEAR exploit in Top 5 + Protocol + Security + Catalysts + Action;
- BTC/ETH/SOL relative-strength repeated unchanged in Sections 2, 3, 12 and 13.

## CR-19 Section substance and breadth
- Section 1 must contain exactly 5 genuinely important items because the fixed heading is `今日最重要的5件事`. Do not pad with no-op/process text; instead select the five highest-decision-value items across market, flows, regulation, security and protocol/ecosystem evidence.
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
