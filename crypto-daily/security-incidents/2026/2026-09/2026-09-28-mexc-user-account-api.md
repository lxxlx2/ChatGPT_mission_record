# MEXC user-account security incident — 2026-09-28

Status: RESOLVED_PUBLICLY / settlement terms undisclosed
Discovery class: CEX account takeover / alleged retained API withdrawal path

## Verified public facts

- A MEXC user identified publicly as @shuangfei8 reported that 322,110 USDT and 9,133,999 ONE were withdrawn after an account takeover.
- The user alleged that an API key created while the attacker controlled the account remained usable after recovery procedures.
- Public reporting states the withdrawals occurred shortly after a 24-hour withdrawal restriction expired.
- MEXC support publicly acknowledged the incident, escalated it to a security investigation, and later said it had reached an agreement with the user and that the matter was fully resolved.
- Public English sources did not disclose the settlement terms and did not independently confirm a full reimbursement amount.

## Monitoring regression

The 2026-09-28 Crypto Daily report did not surface this event. The security lane recorded unavailable specialist/X coverage and relied on a discovery pack that was too generic for individual-account CEX incidents.

Corrective action:
- SECURITY_SOURCE_POLICY.md now requires an hourly major-CEX account-security fast lane.
- Fixed exchange set includes MEXC and nine other major CEXs.
- Search terms include account takeover, API withdrawal, KYC/security reset, deepfake, unauthorized withdrawal, compensation and resolution.
- Event lifecycle dedupe prevents repeating unchanged conclusions.

Regression expectation: a comparable searchable CEX account-security event should be discovered in the next successful hourly cycle, subject to external search/indexing availability.
