# Wallet polling policy correction

run_time: 2026-09-28T15:52:00+07:00
status: completed

User requested removal of routine 3-hour all-chain wallet scans.

Effective policy:
- no hourly wallet-balance telemetry lane;
- no every-3-hours full-chain inventory reconciliation;
- no daily automatic wallet reconciliation;
- no periodic Sui retry;
- no periodic Credits/UNICRED ownership check solely to reconfirm unchanged state.

Wallet state is refreshed only:
- on explicit user request;
- after a user-reported material wallet action/change;
- when a verified event requires balance/ownership evidence.

Market/opportunity/security/TGE/Monster monitoring is unaffected.

Reason:
Repeated wallet rescans consume runtime without adding useful information when the user already reports material balance changes.
