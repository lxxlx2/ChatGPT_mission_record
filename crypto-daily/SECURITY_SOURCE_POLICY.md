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
