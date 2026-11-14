# Crypto Daily Security Source Policy

Updated: 2026-09-27
Timezone: Asia/Bangkok
Status: canonical

## Purpose

Crypto Daily may never claim that a security scan was comprehensive merely because one generic web query returned no result.

Security coverage and factual verification are separate:

- **coverage** asks whether the required source families were actually queried;
- **verification** asks whether a discovered claim is supported by primary or independent evidence.

No daily report may describe the security lane as complete unless the run audit contains source receipts.

## Required hourly security discovery families

Every ordinary hourly collector must execute a bounded security discovery pack covering as many of the following as available:

### A. Primary / official
- official exchange security and scam notices for major venues relevant to current market activity;
- official project / chain / wallet security notices for material candidates;
- regulator / law-enforcement notices when relevant.

### B. Specialist security feeds
At minimum attempt a rotating subset while maintaining <=3h freshness across the group:
- SlowMist / MistTrack
- PeckShield / PeckShieldAlert
- CertiK Alert / Skynet incident feeds
- Scam Sniffer
- Blockaid
- SEAL / Security Alliance
- ZachXBT when accessible
- DeFiHackLabs or equivalent exploit-reconstruction feeds

### C. Social discovery
- English X/Twitter queries for: hack, exploit, phishing, scam, impersonation, fake token, fake chain, fake app, malicious extension, compromised account, drain, approval, seed phrase;
- Reddit only as discovery/corroboration, never sole proof.

### D. Brand-impersonation query pack
Run targeted combinations for high-risk brands/ecosystems that are currently launching, trending or in the report horizon:
- <brand> + scam
- <brand> + phishing
- <brand> + impersonation
- <brand> + fake token
- <brand> + fake chain
- <brand> + fake app
- <brand> + compromised

When a major exchange launches a chain/wallet/ecosystem, include both the exchange name and ecosystem name.

## Source receipts

Every hourly final audit must record:

`security_source_receipts`:
- source_family
- source/account/domain
- query or page checked
- result: candidate / no_update / unavailable
- checked_at

The run may stay bounded. It may not write only `security checked_no_update` without these receipts.

If X/Reddit cannot be directly retrieved, record `unavailable`; do not claim they were checked.

## Verification hierarchy

For every material security candidate:

Tier 1:
- official issuer / exchange / wallet / chain notice;
- official docs / FAQ / domain;
- direct on-chain evidence;
- regulator / law enforcement;
- reproducible technical evidence.

Tier 2:
- specialist security teams;
- multiple independent high-quality news outlets;
- named researchers with evidence.

Tier 3:
- X/Reddit/KOL/community reports;
- search snippets;
- anonymous screenshots.

Rules:
- Tier 3 alone = discovery lead, not confirmed fact.
- A claim of impersonation/fake token should be checked against the official domain/docs/account and, where relevant, contract/chain identity.
- A loss amount, attacker attribution or victim count requires primary/on-chain proof or at least two independent credible sources.
- Conflicting primary evidence must be surfaced as unresolved.

## Completeness language

Crypto Daily cannot guarantee global completeness.

Allowed:
- `required security source families covered: 7/8`
- `one source family unavailable`
- `no additional material incident found in the covered sources`

Not allowed:
- `there were no other security incidents today`
- `security scan was comprehensive`
- `X/Reddit checked` without evidence of an actual retrieval.

## Daily report gate

Before the 09:00 formal report:
1. aggregate previous 24h security candidates;
2. inspect previous 24h source receipts for coverage gaps;
3. run a fresh security verification pack;
4. explicitly query brand impersonation for major exchanges/chains/wallets in the current 72h catalyst window;
5. carry forward unresolved high-risk candidates.

Chapter 9 may only label an event `confirmed` when verification rules pass.

The 09:00 run audit must include:
- security_coverage_ratio
- security_source_families_missing
- security_candidates_seen
- security_candidates_confirmed
- security_candidates_unresolved
- critical_security_candidates_included
- critical_security_candidates_omitted_with_reason

## GIWA gap lesson — 2026-09-27

The collector missed a user-reported GIWA / Upbit impersonation-scam event.

A bounded generic discovery pass had logged `lane_x_reddit: checked_no_update` without source-level receipts. That status did not prove actual coverage.

Independent follow-up found a material identity contradiction that should have triggered investigation:
- official GIWA documentation states GIWA does **not plan to issue its own token** and uses ETH as the native gas token;
- an unaffiliated site promotes a `$GIWA` token and future migration narrative while also disclaiming affiliation with Upbit/Dunamu/GIWA.

This is recorded as a monitoring-gap example. The specific attacker/entity behind the user's reported scam is still separate and must not be inferred without matching evidence.

## Major CEX account-security fast lane — 2026-09-29

The 2026-09-28 MEXC user account-takeover / retained-API incident was missed by the daily report. This is a confirmed discovery-coverage regression.

Every ordinary hourly collector must run one bounded English-language fast-lane search covering major centralized exchanges even when X or specialist feeds are unavailable.

Mandatory exchange set:
- Binance
- Coinbase
- OKX
- Bybit
- MEXC
- Bitget
- Kraken
- Gate
- HTX
- KuCoin

Mandatory incident terms are batched around:
- account takeover / hacked account / unauthorized withdrawal / stolen funds;
- API key / API withdrawal / residual API / compromised API;
- KYC reset / security reset / deepfake / SIM swap / authenticator reset;
- withdrawal freeze / abnormal transfer / user funds;
- compensation / reimbursement / settlement / agreement / resolved.

The fast lane is discovery-oriented. One broad query may batch multiple exchanges/terms, but MEXC, Bitget and any exchange with a current incident must also receive a direct focused query until the case is resolved.

If X is unavailable, the collector must still use fresh English web/news search to discover user reports and official-support responses. X unavailable is not a reason to skip the CEX fast lane.

### Candidate promotion

A CEX user-account incident becomes a security candidate when any of these is found:
- named user/victim reports a material unauthorized withdrawal with timestamps/amounts;
- exchange support or official account acknowledges abnormal asset transfer / dedicated investigation;
- reputable security researcher cites account/API/KYC compromise evidence;
- reputable English news source quotes the user and exchange response.

For a material candidate, verify:
1. amount and asset(s);
2. incident time vs disclosure time;
3. attack path as claim vs confirmed fact;
4. official acknowledgement;
5. remediation / compensation / settlement status;
6. whether the issue implies a reusable user-protection action such as API-key review or withdrawal-whitelist checks.

### Incident lifecycle and no-repeat rule

Persist a stable incident key and lifecycle state:
DISCOVERED -> OFFICIAL_ACK -> REMEDIATION_PENDING -> RESOLVED

A later material state may be appended, e.g. NEW_LOSS_AMOUNT, ROOT_CAUSE_CONFIRMED, COMPENSATION_CONFIRMED.

Do not repeat an unchanged conclusion in hourly research, Gmail alerts, or the next daily report merely because the incident remains newsworthy.

Re-emit only when there is a material delta:
- loss estimate changes materially;
- official acknowledgement appears;
- root cause is confirmed/changed;
- withdrawals/security controls materially change;
- compensation/reimbursement is confirmed;
- case is officially resolved;
- new victims indicate the issue may be systemic.

Daily Chapter 9 should prefer deltas. If an unresolved critical incident must be carried forward for safety, label it ongoing / no material change in one concise line rather than repeating the prior conclusion.

## MEXC miss lesson — 2026-09-29

Missed incident:
- user @shuangfei8 publicly reported 322,110 USDT plus 9,133,999 ONE withdrawn after an account takeover;
- the user alleged an attacker-created API key remained usable after account recovery;
- MEXC support acknowledged the case and later said it had reached an agreement with the user and the matter was fully resolved;
- public English reporting did not disclose the settlement terms or independently confirm full reimbursement amount.

Why the existing policy missed it:
- specialist/X availability gaps were recorded but the fallback discovery pack was too generic;
- the brand-impersonation pack focused on launches/trending brands rather than a fixed major-CEX account-security set;
- official announcement pages alone are weak for individual-account incidents because support-account replies and victim disclosures may appear first.

This incident is the regression test for the CEX fast lane. A healthy hourly run should surface a comparable future event within the next successful hourly cycle after it becomes searchable.

## Multi-user self-custody / hardware-wallet draining regression — 2026-10-09

This is an **existing wallet-security lane**, not a new monitoring category, scheduler, task or user-specific wallet watch. The 2026-10-09 Ledger/Specter claims demonstrate a gap between the broad specification ("wallet security" and Reddit/X discovery) and the narrower mandatory CEX/brand-impersonation discovery actually performed.

**Bounded discovery at each ordinary collector, even if X/Reddit direct access fails:**
- Within the existing general security search batch, explicitly check English results for `hardware wallet drained`, `cold wallet compromised`, `Ledger wallet funds missing`, `Trezor/Coldcard/SafePal user funds stolen`, `multiple wallet users drained`, `seed phrase leak`, `tampered device`, `malicious wallet app`, `signing app vulnerability`, and `reseller/supply chain wallet compromise`. Brands are illustrative terms for a general wallet risk, not a permanently expanded issuer watchlist.
- Include accessible original researcher/security-team updates, wallet issuer support/incident notices and fresh relevant Reddit wallet communities (for example r/ledgerwallet when Ledger is an active candidate); if Reddit/X cannot be read directly, mark them unavailable and run English web/news discovery keyed to the incident and original researcher. A generic `wallet security no update` has no coverage value without a query/result receipt.
- Any credible cluster of >=2 distinct firsthand user complaints, named security-researcher evidence across multiple addresses/chains, suggested >=$1M theft, or reported exploitable wallet signing flaw is a `WALLET_DRAIN_CANDIDATE` for bounded identity/loss/chain verification. This is a **discovery** gate, not an automatic claim that a device vulnerability or full loss is confirmed.
- Record `wallet_user_loss_fast_lane` with actual query, checked_at, source link, result (candidate/no_update/unavailable), and whether next ordinary collector picked up a newly indexed candidate. A missing result/receipt means COVERAGE_GAP, never `checked_no_update`.
- For suspected device/reseller/firmware/seed exposure, separate (a) primary user report, (b) verifiable chain txs, (c) researcher wallet attribution, (d) issuer's response to an individual case, (e) issuer-confirmed systemic vulnerability, and (f) independently reconciled financial loss. Distinct outlets repeating one researcher's estimate are **not independent loss verification**. A brand may be mentioned with evidence labels without alleging a systemic exploit.
- If a high-impact ongoing wallet-risk lead is unresolved, put it in the internal material-candidate ledger for next collector/prebuild; Section 9 of the next formal report should summarize the credible allegation and actionable general risk precautions with `UNCONFIRMED` clearly marked, not suppress the lead simply because official root cause has not been released. Formal verification standards and CR-18/19 dedupe remain in force.
- Previously sent canonical daily reports before a newly published source are not retrospectively classified as missed. The next scheduled collector after a source becomes discoverable is the actual detection SLA; a scheduled run with no final/receipt is UNHEALTHY and must be audited separately. Never backdate discovery.

**2026-10-09 regression lead:** @SpecterAnalyst claimed >$86M linked to hundreds of suspected Ledger-user wallets on ETH/TRON/BTC; media amplification became discoverable at roughly 19:30 Asia/Bangkok, after the 19:20 manual daily send. Community user reports exist, but no independent reconciliation of the $86M or issuer-confirmed generalized hardware failure was established at this review. Two reported Ethereum destinations (0x69c8f401cfc6cd40ac94691d6d7c48e3b7a47841, 0x033636e45d519bebb7b5c2520ca6ce56fbdb4f7a) have real Oct 9 transactions on Ethereum; that alone proves neither theft nor wallet manufacturer attribution. The 19:10 collector on Oct 9 has no durable final. Treat publication-time mismatch, candidate verification gap and persistence failure as separate defects. Do not manufacture a historic delivery or expand TGE scope.

## Official chain-security disclosure discovery regression — 2026-10-10
Existing protocol/chain security discovery MUST query newly issued **first-party chain/core-node vulnerability disclosure reports, emergency patch/release security notes and consensus/monetary-integrity fixes**, including bugs publicly disclosed after their patch shipped. Run a bounded English-source official-advisory query during each ordinary existing security pass and at daily pre-send; focus on active major chains/ecosystems already covered by REPORT_SPEC and any freshly material issuer source. This is part of current protocol security coverage, NOT a new task/asset watch or notification scope.

For an official critical disclosure, record issuer URL, publication date, original discovery date, affected node versions, fix date/activation method, verified real exploitation vs potential exploit, and official operator/user action. A fixed-but-newly-disclosed critical issue is newsworthy; do not silently classify it as 'no incident' because no loss occurred. Missing actual official-advisory query/receipt = SECURITY_COVERAGE_GAP. Maintain CR-18/19 event dedupe and no-fabrication rules.

Regression: XRPL disclosed an XRP-creating payment-engine integer-overflow flaw on Oct 9 (fixed in xrpld 3.4.1 released Sep 25, no evidence of public exploitation), plus a separate Batch validation problem. The Oct 10 formal daily omitted the official disclosure. See `crypto-daily/research/2026-10-10/xrpl-overflow-official-triage.md`. Include this material previously omitted official disclosure in next eligible formal daily Section 9 after fresh verification. No invented exploit, loss or token inflation.


## Existing CEX asset-access and source-of-funds risk regression — 2026-10-17
Security coverage includes first-party exchange notices changing who can send/receive customer deposits, what source addresses/intermediaries count as restricted, what assets may be frozen or held for KYC/AML review, what trading/withdrawals are paused, and when user accounts can be terminated. Treat irreversible account-access threats as high materiality even if there is no hack, theft, coin delisting or dramatic token-price move. Compare multiple major CEXes by named counterparty and effective/enforcement dates, explicitly retaining new material policy delta for one CEX after prior restrictions elsewhere. Verify exact scope and modal language, cite primary English support/legal text when available and mark original social-post gaps honestly. Regression HTX / Huobi Global SA restrictions at Binance, Bybit and Bitget, with Bitget Oct 16 stricter enforcement secondary-reported; don't call all old HTX token holders banned.

## 2026-11-05 SignalPlus third-party trading API incident: mandatory connector dependency discovery
Regression incident: 2026-11-05 Yi He @heyibinance publicly reported that Binance revoked **all API keys linked to SignalPlus** after the third-party derivatives platform reported a POTENTIAL security issue. Reuters independently reported Deribit removed linked API keys too; no trustworthy source in this review confirmed the exploit path, victims, or loss amount. Sources: https://x.com/heyibinance/status/2118295336657772943 and https://www.reuters.com/technology/binance-removes-all-signalplus-api-keys-after-security-issue-2026-11-05/ . The user-provided screenshot directly shows issuer-account text, while the current programmatic original X permalink gave HTTP403. Do not claim direct programmatic X read or a proven Binance breach.
This is a **third-party trading connector / exchange API risk**, pre-existing category within CEX account-security and cloud credential leakage, distinct from prior Binance hot-wallet theft. A security scan confined to Binance announcement list and prior wallet theft will MISS such a user-action event. Each existing ordinary collector (including 20:20) and pre-send full security check must search a bounded API-connector query pack covering the major exchange original account-security statements, integrated derivatives/portfolio trading platforms, and first-party or reputable original indexed posts. Query combinations: "exchange + third-party trading API / SignalPlus / Deribit + revoke API key / credential exposure / abnormal orders", include previous 24h and date filter where available; expand to other provider names on newly identified material candidates. A source gap is never a clean result.
For each material candidate record `security_source_receipts` with issuer, original permalink/official help page OR accurate X-original-unavailable + independent English corroboration, published_at, checked_at, direct user action, affected integration, affected exchange(s), and lifecycle. Use stable incident family `trading-api:signalplus:2026-11-05` and material version `binance-deribit-api-revocation-v1`; never repeat unchanged warning as a new event next day. Distinguish (a) platform *potential* security issue, (b) issuer confirmed API-key revocation, (c) direct trading/order/account exposure unverified, and (d) unaffected exchange assertion. In full report route one primary §9 item, optional one Top5 summary if timely & high impact. If ordinary daily already mailed before the announcement, record the fresh late-day event in an actual collector receipt and cover it next formal report, with no unsupported standalone health email.
User action for users who actually linked SignalPlus: sign in to each exchange directly; verify active orders, fills/positions, revoke remaining linked keys; do not rebind until issuer resolution; if creating replacement keys, least privilege/IP whitelist. User-specific exposure cannot be presumed from holding BNB/BTC or a mere connected wallet elsewhere. No automatic key or account changes authorized.
2026-11-05 scheduled 20:20 collector recorded Bitget rANT venue research and an X source gap but no SignalPlus candidate in the inspected final/source file; 09:20 daily was never sent. 2026-11-05 full 13-chapter user-requested recovery Gmail Sent `1a1ac87a1624ca68` includes verified public warning, independent Reuters and the appropriate caution. Future on-schedule detection still requires real validation.


## Existing wallet/device security lane: message-renderer and embedded-widget RCE regression (2026-11-14)

Incident classification: **CONFIRMED_DISCOVERY_MISS**. The November 11–13, 2026 research on Telegram in-chat HTML Widgets/QuickJS-ng was absent from the November 11–14 crypto hourly research receipts and Gmail Sent reports when directly checked on November 14. This is an existing consumer wallet-device/client software security responsibility, not permission to add a new scheduler, separate watch category, or backup email automation. The existing six cloud/runtime security lanes did not cover this adjacent native application threat.

**Mandatory existing security discovery receipt**: every 00:20/03:20/06:20 research rotation and 08:20 daily prebuild shall check one bounded English query for material client-side message rendering/native-code execution vulnerabilities, e.g. `messaging app widget QuickJS RCE Telegram zero click`, `desktop messaging HTML renderer sandbox escape`, `chat attachment malicious message remote code execution wallet theft`, and accessible first-party researcher/vender security repositories. Query these categories generically so a different client can be discovered. Capture actual search terms, checked_at, publication/disclosure date, at least one accessible original researcher/advisory URL and readback, observed platform and version, previous event family/version, upstream fix commit, released/installed client version status and any SOURCE_GAP. A single old Node.js/Laravel/web-framework item does not satisfy this client-device lane. If the original publisher cannot be reached, record `CLIENT_MESSAGE_RENDERER_SECURITY_SOURCE_GAP` rather than `checked_no_update`.

**Materiality and editorial routing**: independently reproducible arbitrary native code execution by rendering a bot-sent HTML widget, attachment, emoji, message preview, image or chat content is a high-impact Section 9 security candidate, even when no crypto exchange is named or no wallet drain has been confirmed. Also eligible for a single concise Top-5 entry if broad public impact. Native client RCE, sandbox-code execution in an isolated process, mere memory corruption/DoS, and observed real-world compromise are different evidence tiers; keep the distinction. A malformed program execution demo on one Windows build does not prove macOS 7.4.3 vulnerable. Different attack chains and package versions must not be collapsed into one blanket 'patched on all devices' claim.

**2026-11-14 original-source regression**: Telegram Official Bot API `https://core.telegram.org/bots/api` dated November 9 introduced `sendWidget`; `https://core.telegram.org/bots/widgets` explains HTML JavaScript runs on message layout in an embedded QuickJS sandbox. Primary researcher `https://github.com/bikini/telejam` reports two independent native RCE paths on stock Windows Telegram Desktop **7.4.2** with calculator demonstrations, one patched in engine commit `ca3594d` and second related to quickjs-ng #1910 unresolved at researcher recording. Independent repository `https://github.com/davtur19/tg-widget-rce` and `VULNS.md` document older Android/iOS/Desktop/macOS versions, including platform-specific exploit constraints and subsequent fixes. Verify actual Telegram QuickJS fork commit `https://github.com/TelegramMessenger/quickjs/commit/ca3594dae5fd0dd6d667be74a322e8e935a2d217`. The research repo's statement that its archived BUG-1 is fixed on current builds is a researcher assertion, not a substitute for client-specific released-build validation. Public reports of code execution on newer 7.4.3 require direct source and are UNCONFIRMED until independently checked.

**Immediate historical correction**: 2026-11-13 original Crypto 09:20/10:20/11:20 all failed without a formal email. Include this newly discovered high-impact candidate in a complete, truthful Nov 13 recovery report once finished, explicitly labeling source/disclosure time and version. No routine extra "health" email; never send an incomplete 13-chapter report under the guise of correcting the security omission. On Nov 14 daily include if not already delivered or if confirmed new independently meaningful version; don't resend unchanged status after first valid disclosure. Verify actual Gmail Sent+full-body and Git canonical before claiming repaired. If not delivered, remain MISSED/OPEN and do not invent message IDs.

**User action boundaries**: use official client update channels, avoid running PoCs or opening unfamiliar bot widgets on sensitive wallet/developer devices, inspect active sessions if compromise is suspected. No evidence from this source review establishes that this user's own Mac or wallets were compromised. Do not imply a server-side restriction alone removes risks from already received historical widgets. Never publish working exploit code or build instructions in user-facing alerts.
