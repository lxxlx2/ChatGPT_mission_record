# US Stock Daily Acceptance Gate

Updated: 2026-09-29 Asia/Bangkok

The report may be sent as official only when all hard gates pass.

## Hard gates

STK-01 Structure
- exactly the 12 canonical first-level sections in order.

STK-02 Session core
- latest completed session includes Dow, S&P 500 and Nasdaq levels/returns when available;
- session date is explicit.

STK-03 Macro core
- rates plus oil plus USD/macro context, or explicit source-unavailable notation in the audit.

STK-04 Driver coverage
- major company/sector moves are tied to verified drivers where available;
- no unsupported causal claim.

STK-05 Theme depth
- Section 4 contains a real thematic synthesis, not a generic placeholder.

STK-06 AI/primary-market coverage
- material AI/tech/IPO/private-market developments are checked;
- active user-rights events are separated from generic company news.

STK-07 Catalyst/risk coverage
- Sections 8 and 9 contain risk radar and dated 24-72h catalysts.

STK-08 Buy-watch discipline
- Section 10 may be empty/brief when no evidence exists;
- any candidate must include why-now plus key risk/invalidation.

STK-09 No recovery downgrade
- recovery/resend/correction uses the same full 12-section contract;
- a short digest can never become canonical unless the user explicitly requested a digest.

STK-10 Delivery integrity
- Gmail Sent id + readback;
- GitHub canonical body archived;
- body equality after stripping YAML metadata;
- prior same-day incomplete edition marked superseded.

STK-11 Missing-source resilience
- one source/provider failure cannot silently delete required sections;
- missing data is either replaced by an equivalent source or disclosed internally and handled conservatively.

STK-12 Quality-collapse guard
- compare body length and numbered-item count against the trailing 5 latest complete formal reports;
- if body length < 70% of trailing-5 median OR numbered-item count < 70% of trailing-5 median, QA fails unless the run audit records a genuine low-event/market-closed reason and all semantic hard gates still pass;
- recovery-path status alone is never a valid reason for the exception.

## Delivery state machine

DRAFT -> QA_PASS -> GMAIL_SENT_READBACK -> GITHUB_ARCHIVED_READBACK -> DELIVERED

Any state before GMAIL_SENT_READBACK is not delivered.
If Gmail succeeds and GitHub fails, preserve GMAIL_SENT_READBACK and repair archive only; do not resend.
