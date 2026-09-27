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
