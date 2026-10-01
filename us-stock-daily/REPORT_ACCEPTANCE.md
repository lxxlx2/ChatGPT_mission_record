# US Stock Daily Acceptance Gate

Updated: 2026-10-01 Asia/Bangkok

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

Audit-only, never user-visible:
- scheduler/delivery failures;
- pending/canonical/recovery/readback mechanics;
- why a field was omitted;
- why a section was not deeply scanned;
- “无法核验所以不写”“本轮不进行全量深扫”“不为了数量要求添加标的”等 editorial/process language.

If a section truly has no material update, use one short neutral line such as `无高置信新增。`.

STK-14 One logical event = one item
Every numbered item gets an internal `event_key` before send.

Do not split one logical event into two bullets where the second only qualifies/caveats the first. Merge status, caveat and next checkpoint for the same event into one item.

Adjacent items with the same event_key are a hard QA failure unless they represent independent user actions.

STK-15 Cross-section event dedupe
Create an internal `event_key -> sections/items` map.

One logical event has one primary section. A second mention is allowed only when it adds a distinct decision dimension, not when it repeats the same status/conclusion.

Examples:
- a macro release may appear in the market recap and later as a forward catalyst only if the later mention is a genuinely different dated next event;
- the same stock move should not be repeated in Sections 2, 3 and 10 unless each occurrence adds separate decision value.

Repeated event_key without `distinct_dimension` = QA FAIL.

STK-16 Section 11 semantic rule
Section 11 is for substantive market-monitoring misses and model blind spots, not delivery plumbing.

Allowed examples:
- index looked stable but breadth/new-lows deteriorated materially;
- a regulation-driven single-stock crash was not captured by the sector-level scan;
- cross-asset rates/oil/USD interaction was missed.

Forbidden:
- scheduler did not run;
- Gmail was not sent;
- pending file missing;
- recovery path explanation;
- GitHub/archive/readback status.

STK-17 Item decision-value gate
Every numbered item must contain at least one of:
- a new/materially changed verified fact;
- a current quantitative observation;
- a concrete risk/opportunity/action;
- a specific dated/threshold checkpoint.

An item fails if its primary purpose is to explain omission, process, lack of coverage, or a decision not to include something.

STK-18 Mandatory pre-send lint
Before Gmail send, create an internal lint result. All must PASS:
1. `structure_lint` — exact 12 headings/order.
2. `meta_prose_lint` — no process/editorial filler.
3. `same_event_item_lint` — no split duplicate event within a section.
4. `cross_section_dedupe_lint` — repeated event requires distinct decision dimension.
5. `decision_value_lint` — every numbered item passes STK-17.
6. `section11_semantic_lint` — Section 11 contains only substantive market misses, no delivery plumbing.
7. `freshness_lint` — dates/times and market state are current for the report cutoff.

Any FAIL => `QA_FAIL_NO_SEND`. Rewrite and rerun lint before sending.

The internal audit records only PASS/FAIL plus offending item identifiers; lint commentary itself never enters the email.

## Delivery state machine

DRAFT -> PRE_SEND_LINT_PASS -> QA_PASS -> GMAIL_SENT_READBACK -> GITHUB_ARCHIVED_READBACK -> DELIVERED

Any state before GMAIL_SENT_READBACK is not delivered.
If Gmail succeeds and GitHub fails, preserve GMAIL_SENT_READBACK and repair archive only; do not resend.
