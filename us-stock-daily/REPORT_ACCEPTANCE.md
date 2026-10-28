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

STK-12 Quality-collapse guard (revised 2026-10-21)
- compare body length and numbered-item count against trailing 5 actually delivered formal reports for diagnostic coverage warnings, not numerical quota filling;
- below 70% of historical median is WARN/REVIEW only and cannot by itself produce QA_FAIL or require old AI/rates/earnings news to be copied. Market-closed/low-event periods legitimately contain fewer current facts, while all 12 original headings remain;
- HARD FAIL still applies when essential available market indices, genuinely new high-impact news, dated sources, market-day integrity, actionable catalyst/risk checks or other semantic STK rules are missing. Never send a vague recovery digest as a shortcut; do not pad with unchanged repeated commentary to match old report length.

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


## STK-20 Section-local numbering and correction-readback gate — 2026-10-17
A report with the 12 canonical first-level headings MUST restart item numbering at （1） under EACH new heading and continue locally （2）, （3）... without gaps/duplicates. Global running numbers spanning headings are a hard failure even if sections and overall item counts pass. Parse the final email body by canonical section boundaries before EVERY primary, recovery or manual correction send; run the same parser over Gmail readback. Where a section has no substantive items, show \`无高置信新增。\` without a spurious numbered item.
Do not resend a previously delivered same-date report on a normal automated run. If and only if a specifically identified content/format defect materially degrades a delivered official report and the user requests correction, send a full 12-section \`｜修正版\` after checking Gmail Sent for that EXACT corrected subject; mark prior delivery superseded in canonical Git metadata while preserving original Sent ID in the audit. Verify identical readback and Git archival body.

## STK-21 QA finality / no speculative READY — 2026-10-18

Hard gate. In the exact FINAL Gmail-bound body, execute **all** semantic checks (STK-01..STK-20, especially decision_value_lint, meta_prose_lint, latest source-date/freshness, section-local numbering and market-day correctness) BEFORE setting \`qa_status: PASS\` and \`status: READY\` on any durable pending manifest. Drafts written earlier must say \`DRAFT_UNVERIFIED\` or \`QA_PENDING\`, never \`READY\`. Repair identified low-value content IN MEMORY and rerun on the corrected final text; avoid depending on a second GitHub edit when a single finalized source file will suffice. Sending is authorized only after the complete final body passes all gates; a missing secondary Git audit write by itself cannot veto a separately verified, fully compliant Gmail send. A platform safety rejection remains a real block, never something to bypass. Run evidence must distinguish semantic QA failure from provider-level Git or Gmail safety rejection. Regression: 2026-10-18 07:40 automatic report had early pending \`qa_status PASS\` followed by STK-17/18 failure and blocked Git correction; manual full delivery later succeeded via separate authenticated send/readback.

## STK-22 Freshness, cross-day novelty and bounded theme exposure — 2026-10-21
Avoid filler to satisfy report length or a fixed 55+ item quota. Preserve the 12 canonical headings; a section without genuinely new material can say \`无高置信新增。\` as one unnumbered line. Every numbered item should contribute a dated market move, official new result, changed institutional signal, previously unreported risk, new next-72h action/catalyst, or a quantitatively justified synthesis of NEW evidence. Unchanged last-week AI debt risk, user portfolio overlap, future Tesla/Meta earnings and general Fed/rates caution are NOT four independently new stories just because mentioned in four sections/dates; avoid multiple repeated paragraphs. Each material event/catalyst normally gets one detail and at most one highlight in another chapter. A dated imminent earnings result may recur as an actionable calendar item while it is truly upcoming, but once results publish, replace forecast content with actual earnings and do not keep prior anticipation prose. Compare the last 7 authoritative daily Sent/Git bodies for event identity and material changes before composition; report old context internally instead of repeatedly numbering "nothing new." Preserve the true QA and delivery gates; do not turn a source gap into a universal veto, downgrade a full morning report, or invent dates/market values.

## STK-23 Evidence-bound cross-day novelty and EMAIL-ONLY completion — 2026-10-28
The user wants Gmail reports, NOT ChatGPT app messages, status recaps or source-gap notifications. Every scheduled run must exit with a literally empty final assistant response; write all run/status/error/QA details into Git only. Both ChatGPT task notification flags and email notification flags have been disabled in the product, yet nonempty task replies still appear on the task's conversation surface, so "App静默" text alone is insufficient. Do not send a second test/digest/health email.

For daily articles, use 7 days of actual authoritative Gmail Sent bodies and Git canonicals to build a **stable cross-day family ledger** before writing. Every non-routine numbered item must declare internally `family_key` (persistent across dates), `material_version`, `primary_section`, `first_published_at`, `observed_at`, original evidence URL and status `NEW / MATERIAL_DELTA / ROUTINE_DATED_FACT / WATCH_ONLY / DUPLICATE`. If it shares a family previously covered, a MATERIAL_DELTA requires changed field, prior/new values and a newer official disclosure or genuinely newer measured session. One price close per new trading day, a released earnings result, a changed forecast, a new bond/CDS quote, and a finite upcoming event calendar can legitimately recur as *new dated facts*. "AI capex is risky", "the Fed is about to decide", "ETF holdings overlap" and any stale issuer background cannot be repeated as independent numbered news across chapters and consecutive days without quantitative new facts. A future catalyst may appear once in §9 at its verified date with a short countdown, NOT as three quasi-new essays elsewhere. Within one email keep a single primary section per event, at most one very short cross-reference, and no unchanged boilerplate in §11 or §12. Exclude or reduce old unsupported commentary rather than padding a paragraph quota. Keep the full 12 sections and factual market/macro breadth; no short recovery newsletter.

A manual/CI check that only verifies section count or local numbering must NOT be called semantic dedup PASS. Save a small inspectable `novelty_evidence` matrix as part of each report's Git audit with candidates, source versions and exclusions; if reliable previous-email comparison is unavailable, disclose DE-DUP_SOURCE_GAP internally and avoid declaring globally duplicate-free. Normal Gmail delivery still requires original send ID/readback/Git full-body integrity.

## STK-24 — IPO issuer news vs exchange-mediated IPO access (2026-10-28)

The user wants Anthropic issuer IPO process in the existing AI/technology/primary-market section **and** to know whether crypto venues (Kraken, Binance, Bitget, Bybit, Gate, OKX) might separately enable real Anthropic IPO application/allocations or tokenized-equity distribution, analogous to earlier SpaceX programs. This is a WATCH hypothesis, NOT proof that any venue already offers it. Exchange IPO Access must be distinguished from a synthetic ANTHROPICUSDT pre-IPO perpetual, which has no IPO shares. Stock daily should cover genuinely new SEC/issuer filing, price range, underwriting, IPO allocation details and eligibility when supported by primary sources; do not reprint exchange speculation daily. The parallel Crypto daily owns detailed venue-specific potential participation terms under its Git rules. No new monitoring schedule or duplicate email.
