# GIWA / Upbit impersonation monitoring gap

date: 2026-09-27
timezone: Asia/Bangkok
status: monitoring_gap_confirmed_event_identity_pending
severity: process_gap

## What happened

The user reported a same-day scam incident involving an actor pretending to represent Upbit's GIWA chain.

Repository search found no GIWA candidate in:
- today's Crypto Daily research;
- today's Crypto Daily run audits;
- today's Airdrop/TGE run audits and event reports.

The 14:00 Crypto Daily final had:
- lane_bounded_english_discovery: success
- lane_x_reddit: checked_no_update

but contained no exact security source receipts. Therefore those labels do not prove the required security feeds/accounts were actually covered.

## Independent follow-up

Primary GIWA documentation says:
- GIWA does not plan to issue its own native token;
- ETH is the native token / gas asset.

A currently indexed unaffiliated site promotes a $GIWA token and future migration narrative while also disclaiming any affiliation with Upbit, Dunamu or GIWA.

This contradiction is a valid brand/token-confusion security signal and should have been discovered by a GIWA + fake-token / impersonation query pack.

This file does not attribute the user's reported scam to that specific site. Exact incident identity remains pending a matching post/domain/account/contract.

## Root cause

- security discovery was bounded and generic;
- audit fields allowed `checked_no_update` without exact source/account/query receipts;
- no mandatory brand-impersonation query pack existed;
- daily report completeness depended on hourly candidate discovery, so a discovery miss could propagate into Chapter 9.

## Remediation

- created `crypto-daily/SECURITY_SOURCE_POLICY.md`;
- source-level receipts are mandatory;
- unavailable X/Reddit/security feeds must be labeled unavailable;
- added rotating specialist-security source coverage;
- added explicit brand impersonation queries;
- added 09:00 security coverage/gap gate;
- global completeness claims prohibited.

## Verification rule

A report may call an incident confirmed only after primary/direct evidence or adequate independent corroboration. Social posts alone remain discovery leads.
