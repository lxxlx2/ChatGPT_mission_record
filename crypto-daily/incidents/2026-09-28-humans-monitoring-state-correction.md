# Correction: humans& monitoring state

date: 2026-09-28
timezone: Asia/Bangkok
status: corrected

The prior remediation briefly added humans& -> Echo/Alpen Capital as an active monitoring mapping after the missed-refund audit.

That was incorrect current-state logic because the user's humans& allocation had already been fully refunded on 2026-09-24.

Correct state:
- humans& exposure: CLOSED
- capital remaining in deal: 0
- user entitlement requiring monitoring: none
- active humans& / Echo / Alpen rights monitoring: disabled
- historical refund evidence retained for audit
- reactivation requires a new user exposure or explicit instruction

General intermediary-rights logic remains applicable only to active deals.
