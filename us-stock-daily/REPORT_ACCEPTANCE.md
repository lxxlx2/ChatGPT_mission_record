# US Stock Daily Acceptance Gate

Updated: 2026-10-02 Asia/Bangkok

The report may be sent as official only when all hard gates pass.

## Hard gates

STK-01 Structure
- exactly the 12 canonical first-level sections in order.

STK-02 Session core
- latest completed session includes Dow, S&P 500 and Nasdaq levels/returns when available;
- session date is explicit.

STK-03 Macro core
- rates plus oil plus USD/macro context, or explicit source-unavailable notation in the internal audit only.

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
- missing data is replaced by an equivalent source when possible or disclosed internally in the audit;
- source/process failure text must not be used as user-visible filler.

STK-12 Quality-collapse guard
- compare body length and numbered-item count against the trailing 5 latest complete formal reports;
- if body length < 70% of trailing-5 median OR numbered-item count < 70% of trailing-5 median, QA fails unless the run audit records a genuine low-event/market-closed reason and all semantic hard gates still pass;
- recovery-path status alone is never a valid reason for the exception.

STK-13 User-visible cleanliness
The email body must not contain monitoring plumbing or editorial commentary about what the report chose not to do.
Audit-only: scheduler/delivery failures, pending/canonical/recovery/readback mechanics, omission explanations, source gaps and report-generation commentary.
If a section truly has no material update, use one short neutral line such as `无高置信新增。`.

STK-14 One logical event = one item
Every numbered item gets an internal `event_key` before send. Do not split one logical event into multiple bullets that only restate/caveat one another.

STK-15 Cross-section event dedupe
Create an internal `event_key -> sections/items` map. One logical event has one primary section. A second mention is allowed only when it adds a distinct decision dimension.

STK-16 Section 11 semantic rule
Section 11 is for substantive market-monitoring misses and model blind spots, not delivery plumbing.

STK-17 Item decision-value gate
Every numbered item must contain a new/material fact, current quantitative observation, concrete risk/opportunity/action, or specific dated/threshold checkpoint.

STK-18 Mandatory pre-send lint
All must PASS before Gmail:
1. structure_lint
2. meta_prose_lint
3. same_event_item_lint
4. cross_section_dedupe_lint
5. decision_value_lint
6. section11_semantic_lint
7. freshness_lint

Any FAIL => `QA_FAIL_NO_SEND`; rewrite and rerun lint.

STK-19 No silent scheduled exit / durable attempt
Every scheduled invocation must write an `attempt` run artifact before doing substantive work.
- 05:40 prebuild may stop after durable prebuild/audit.
- 06:40 repair may prepare missing inputs.
- 07:40 is primary delivery: first search Gmail Sent for today’s exact subject prefix. If absent, it MUST attempt a full report; it may not silently exit.
- 08:40 is recovery: again search Gmail Sent. If absent, it MUST attempt a full recovery delivery using equivalent/fallback sources; it may not silently exit merely because prebuild/pending is absent.
- Every delivery/recovery attempt must finish with a durable final run artifact stating `DELIVERED`, `QA_FAIL_NO_SEND`, or `BLOCKED_WITH_REASON`.
- A scheduler trigger with no attempt/final artifact is `UNHEALTHY` and must be repaired on the next scheduled run.

## Delivery state machine
DRAFT -> PRE_SEND_LINT_PASS -> QA_PASS -> GMAIL_SENT_READBACK -> GITHUB_ARCHIVED_READBACK -> DELIVERED

Any state before GMAIL_SENT_READBACK is not delivered.
If Gmail succeeds and GitHub fails, preserve GMAIL_SENT_READBACK and repair archive only; do not resend.
