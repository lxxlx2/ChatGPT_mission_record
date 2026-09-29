# Crypto Daily Acceptance Gate

Updated: 2026-09-29 Asia/Bangkok
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
Every material security candidate from the prior 24h is either:
- included in Section 9 after fresh verification; or
- listed in the internal audit as omitted with concrete reason.
Major-CEX account-security receipts follow SECURITY_SOURCE_POLICY.md.

## CR-05 TGE/rights freshness
Section 7 consumes only current/actionable TGE/rights state. User-known/closed/refunded/expired events are not recycled as new information. When possible, use the canonical TGE monitor state rather than rediscovering stale events.

## CR-06 Early/Meme/NFT coverage
Section 8 may say no material candidate only if the relevant discovery lane actually ran or the manifest records its source gap. A lane that did not run cannot be rewritten as “no opportunities”.

## CR-07 Institutional/on-chain coverage
Material ETF/fund/exchange/whale/market-structure changes are checked and separated from stale historical context.

## CR-08 Macro/cross-market coverage
Material rates/oil/USD/equity/geopolitical drivers are checked when relevant.

## CR-09 Deduplication
Unchanged prior-day conclusions are not repeated as new. Carry-forward is allowed only when still decision-relevant and clearly identified as ongoing or when a material delta exists.

## CR-10 No recovery downgrade
09:00 primary, 09:10/10:10/11:10 recovery, manual resend and correction all use the same full 13-section content contract. A short digest/patch can never silently become the official report.

## CR-11 Delivery integrity
- Gmail send + readback;
- canonical GitHub archive + readback;
- exact body equality after YAML metadata;
- prior incomplete/superseded same-day versions recorded.

## CR-12 Quality-collapse guard
Compare against trailing 5 latest complete formal reports:
- if body length < 70% of median OR numbered-item count < 70% of median, QA fails unless a genuine low-event reason is documented and CR-01 through CR-09 all still pass;
- provider failure, recovery mode or time pressure are never sufficient exceptions.

## CR-13 User-visible cleanliness
Monitoring-health details, run failures, “QA passed”, internal classification mechanics and persistence plumbing stay out of the report body unless the monitor failure itself directly changes the reliability of a substantive conclusion the user needs.

## State machine
DRAFT -> INPUT_MANIFEST_READY -> QA_PASS -> GMAIL_SENT_READBACK -> GITHUB_ARCHIVED_READBACK -> DELIVERED

If Gmail succeeds but GitHub archive fails, repair GitHub only and do not resend.
