# Missed Daily-Report Security Event: Magic Eden / Limit Break Payment Processor

Detected in audit: 2026-09-27
Affected report: `crypto-daily/reports/daily/2026/2026-09/2026-09-26.md`
Classification: missed_high_priority_security_carry_forward

## What happened

The Sep-25 23:00 hourly research correctly captured a material Magic Eden / Limit Break Payment Processor V2 security event:
- legacy EVM approvals exposed NFTs worth more than $5.7M;
- 23,155 NFTs were reported rescued by a whitehat;
- users with historical Magic Eden EVM approvals were advised to revoke Payment Processor V2 permissions;
- live Magic Eden listings were reported unaffected.

The 2026-09-26 09:20 formal daily omitted this item entirely.

## Why it was missed

This was an **aggregation / promotion failure**, not a discovery failure.

The hourly collector had the event in:
`crypto-daily/research/2026-09-25/230000.md`

The manual-recovery daily report prioritized a small fresh set and did not enforce a mandatory carry-forward checklist over every high-priority security candidate from the prior 24 hours.

## Repair

Formal-report generation must build a critical carry-forward set from the prior 24h research and final audits.

A security candidate cannot be silently omitted when any is true:
- user remediation is required (revoke / patch / move assets / claim rescue);
- exposure/loss >= $1M;
- a wallet, exchange, bridge, approval or marketplace vulnerability remains active;
- a prior research file labels it material/actionable security.

Each such item must be either:
- included in Chapter 9 after fresh verification; or
- explicitly marked closed/false-positive with an omission reason in the run audit.

## Current primary-wallet check

At audit time:
- current non-spam Ethereum NFT contracts checked against Payment Processor V2 operator approval returned false;
- Ethereum WETH allowance to Payment Processor V2 returned zero;
- Base WETH allowance to Payment Processor V2 returned zero.

Base NFT approval enumeration was not fully verified in this audit due provider output limits, so do not generalize this check to every wallet/chain historically used by the user.
