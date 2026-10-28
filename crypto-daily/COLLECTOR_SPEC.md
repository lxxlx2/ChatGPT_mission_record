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

## 2026-10-22 P0 security-discovery repair: core web RCE and global TLS/CA
The existing Crypto Daily security lane is BROAD financial-infrastructure security, not just blockchain exploits, Ledger wallet advisories or exchange status pages. Its mandatory sibling source receipts (specified in EDITORIAL_RULESET.json) are \`web_runtime_rce\` and \`web_pki_tls\`, alongside \`security\`. This is one more source-discovery step INSIDE the original scheduled Crypto task and Git controls, not a new task, local Mac scanner, GitHub Actions schedule or paid API.

EVERY report on its publication date must perform a bounded fresh English original-source check in these independent families:
- \`web_runtime_rce\`: PHP Security page <https://www.php.net/archive/2026.php> and relevant vendor security advisories; ENISA <https://www.enisa.europa.eu/news>, CERT-EU <https://cert.europa.eu/publications/security-advisories>, UK NCSC <https://www.ncsc.gov.uk/>, US CISA; for discovered high-severity vulnerabilities look up vendor final and CVE status. General web-runtime/authentication errors can impact crypto venues, TGE sign-in, API custodians and fiat rails. Scan only high/material dated notices; do not copy generic PHP articles daily.
- \`web_pki_tls\`: Mozilla Security <https://blog.mozilla.org/security/>, Chrome Root Program <https://blog.google/security/>, public Mozilla CA incident discussions <https://groups.google.com/a/mozilla.org/g/dev-security-policy/>, Cloudflare original security blog <https://blog.cloudflare.com/>, and national CERT alerts. Look for critical CA private-key exposures, mass revocations, TLS-root distrust, browser trust store changes, software-supply-chain compromises. A compromised CA is different from a browser engine zero-day and different from an exchange hack.

Before writing "无高置信新增" in §9, prove these 2 independent checks and a dated genuine security source sweep in the manifest. Record URL/query, checked_at, original published_at, bounded results, and any SOURCE_GAP. Empty search results do NOT mean exhaustive full-internet safety. Any HIGH new advisory that is verified must enter the candidate list with a one-line inclusion/exclusion reason; independently ranked global systemic incidents merit Top5, with §9 detail. Do not demand user cryptocurrency ownership as relevance for wide financial TLS/web infrastructure safety.

Regression case A: PHP2Shell, two unauthenticated RCEs CVE-2026-109618 and CVE-2026-109619 disclosed 2026-10-21 (vendor and EU national CERT advisories, patched same day). Crypto Oct22 earlier §9 erroneously said no new verified security.
Regression case B: Indian eMudhra eight weak intermediate CA private keys, originally reported 2026-10-17 and broadly publicly disclosed 2026-10-20; Google/Mozilla + India's CERT 2026-10-21 clarified TLS impersonation and emergency client mitigations. Keys were tiny integers (4, 56, 66, 115, 155, 156, 230, 237), not a generic "India browser vulnerability." This is separate from PHP; updated browsers are protected but some other TLS clients still need trust-store patches. Do not claim all HTTPS connections are compromised or actual financial theft without evidence.

Sources are English official first: https://www.php.net/archive/2026.php ; https://www.enisa.europa.eu/news/joint-statement-on-critical-php-vulnerabilities ; https://blog.mozilla.org/security/2026/10/20/protecting-firefox-users-following-the-compromise-of-emudhra-intermediate-certificates/ ; https://blog.google/security/protecting-chrome-and-android-users-from-compromised-emudhra-intermediate-ca-certificates/ ; https://www.cert-in.org.in/s2cMainServlet?CACODE=CICA-2026-3649&pageid=PUBADV01 .

## 2026-10-23 P0 expansion: current developer/API security MUST be discovered independently
This is a correction to the already-existing Crypto market daily broad security lane, not a new task, paid API or user's Mac collector. In addition to prior \`web_runtime_rce\` and \`web_pki_tls\`, the canonical Git JSON requires three distinct original-source checks and real dated receipts: \`ai_package_supply_chain\`, \`cloud_secrets_identity\`, \`backend_framework_auth\`. An old wallet/security blog is not a substitute for any of these. A source error is SOURCE_GAP, not proof nothing happened. For every verified material new event, use independent event_key/material_version/source publication and source checks; route §9 and possibly independent Top5 when large cross-sector impact, with 1 highlight and 1 detail MAX. Explicit no-new-incident must not be used while primary checks are inaccessible.

Original source families:
* AI Python supply chain: LiteLLM security releases/incident blog, official PyPI/GH security advisories, original vendor reports. Regression: LiteLLM open-source \`1.107.0\` malicious PyPI wheels and Docker images were publicly available for ~2h October 21, 2026. Credential-stealing/RCE payload; legitimate developer GitHub token compromise. Source: https://docs.litellm.ai/blog/security-incident-oct-21-2026 . Do not treat entire prior version family as compromised or imply this service's own private enterprise registry affected.
* Cloud secrets and identity: original Railway incident/status and Microsoft/ConnectWise OAuth compromise articles. Regression: https://blog.railway.com/p/security-disclosure-wednesday-october-21st (potential plaintext env vars, rotate exposed keys, source primary Oct21) and https://www.microsoft.com/en-us/security/blog/2026/10/21/storm-0940-uses-artex-agentic-ai-connectwise-supply-chain-compromise/ (Microsoft attributes agentic-AI accelerated, multi-tenant compromised ConnectWise OAuth; successful auth is not confirmation of data exfiltration). Do not combine these independent incidents into one or imply all Microsoft/Railway customers are breached.
* Backend framework/runtimes: original Node.js release advisories, Laravel security advisories and national CERT alerts. Regression: Node.js October 21 security train CVE-2026-111497 Brotli OOB RCE, CVE-2026-105483/106069 TLS host verification bypass; patched 22.23.4,24.22.1,26.12.1 https://nodejs.org/en/blog/vulnerability/october-2026-security-releases . Laravel GHSA-f9x3-7vq9-cph6 TokenGuard auth bypass CVSS 9.2 under specific MySQL/MariaDB token guards, fixed 12.68.0/13.29.0 https://github.com/laravel/framework/security/advisories/GHSA-f9x3-7vq9-cph6 .
Original release publication dates and affected conditions must be preserved; do not call previously patched October 19 advisories fresh October 23 disclosures. Include major previous few days' completely unreported events as CATCHUP instead of old-event filler. Assign actual-affected guidance only if relevant configuration/installation is evidenced.

## 2026-10-28 — Third-party Anthropic IPO via crypto exchanges: WATCH, not an existing allocation

The user requests monitoring **whether** Kraken, Binance, Bitget, Bybit, Gate and OKX might open an Anthropic IPO application/tokenized-share allocation analogous to past SpaceX venue programs. The user does **not** claim an Anthropic allocation program is live. Never write 'already launched' until independently confirmed on the relevant venue's official dated English page.

Keep this within the existing scheduled Crypto market discovery; NO NEW automation, Mac process, GitHub cron, paid API, or repeated Gmail. Monitor each official venue's IPO, xStocks/tokenized equities, pre-IPO and derivatives product announcements and, where available at the actual time of the scheduled task, official X posts. Do not assume the interactive logged-in X tab persists into a scheduled run. If unavailable, mark BROWSER_SESSION_UNAVAILABLE and continue official web announcements/SEC sources.

Classify venue offerings precisely: (a) actual primary IPO share allocation / application, (b) economically backed tokenized equity or secondary token, (c) nonbinding interest registration, (d) synthetic perpetual/pre-IPO price bet, or (e) rumor with no live venue product. A perp listing is not IPO access, is not proof of actual stock ownership, and is not an allocation window.

If a venue publishes an actual new Anthropic IPO access opening or verified imminent registration deadline, include a sourced, actionable item in existing Crypto daily §7, with venue identity, eligible locations/KYC, dates in Asia/Bangkok, funding, minimum/maximum, distribution/refund, legal nature, custody/beneficial interest and source URL. If nothing official is open, report status only if a substantive official new milestone appears; do not fill the report with daily 'still no offer' prose. A company SEC S-1 filing and an exchange IPO product are separate event families. Stable key `ipoaccess:anthropic:<venue>:<product_type>` and proof-bound material changes are required. IPO of Kraken/Payward itself is a different topic and is not this request.

## X primary-source collection contract for all existing Crypto windows — 2026-10-28

Mandatory authoritative shared policy: `docs/MONITORING/X_FIRST_PARTY_SOURCE_POLICY.md`. Use original read-only Browser `list_tabs` / `get_tab_context` **only if the actual current scheduled runtime exposes them and actual relevant x.com tab IDs**; do not import the interactive conversation's prior tab IDs and never assume the user's desktop X login is exposed in a scheduled executor. Otherwise use public x.com original permalink search by bounded relevant verified issuer handles plus their official websites/documents, record `browser_session=UNAVAILABLE` and `X_SOURCE_GAP` where appropriate. Preserve ALL existing primary feeds, no Mac task, new scheduler or login automation.

For Anthropic IPO **exchange-mediated possible allocation** specifically check official Kraken/Binance/Bitget/Bybit/Gate/OKX dated X announcements and official Exchange Support/IPO Access product terms, independently from SEC Anthropic issuer S-1, and separate perps from equity subscription. Save one `official_x` and one `third_party_ipo_access` source receipt each bounded run (actual checked or explained source_gap), event triage and product state. Unknown stays UNCONFIRMED, not a claim to send a subscription email.
