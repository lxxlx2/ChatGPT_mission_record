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

## STK-25 IPO status receipt and real X source provenance — 2026-10-28

Every original daily research pass must produce an IPO issuer status check receipt `issuer, official_source_url, status, last_official_stage_changed_at, checked_at, new_delta_or_none`. In the existing §五, important verified new issuer filing, amended terms, pricing, share allocation or trading status MUST appear in a labeled `IPO / Pre-IPO / 新股机会` subsection; an unchanged rumor is NOT a fresh headline. The exchange-mediated potential Anthropic allocations are an *independent venue-specific hypothesis*, distinct from Anthropic's own stock filing or an ANTHROPICUSDT futures contract. No invented venue offer.

Every pass must also produce an `official_x` source method receipt under `docs/MONITORING/X_FIRST_PARTY_SOURCE_POLICY.md`: actual Browser tab availability and original read when feasible, else public original X link search + SEC/IR and explicit X_SOURCE_GAP. Never claim continuous logged-in X scanning because a previous interactive ChatGPT session saw a browser tab. Reuse existing schedule; no extra task, browser automations or local deployment. Stock report QA is not full fact recall if IPO and original source lanes are unchecked; preserve all 12 market/news sections even when social sources are unavailable.

## STK-26 — Overnight issuer earnings discovery and recovery after a draft QA failure (2026-11-04)
A daily readiness pass is NOT complete merely because AP/Reuters have index closes and previous day's pending draft has 12 headings. Before 07:40 and again in the last existing 08:40 recovery window, separately check the official earnings calendars plus actual after-hours issuer IR/SEC 8-K releases for the latest US cash-market session. Candidate examples include large technology/AI suppliers and issuers with material revised guidance; the current issuer, exact release date, headline revenue, segment revenue and forward guidance must be checked against official IR/SEC, not preview articles. A major actual release absent from an otherwise formatted draft is SEMANTIC_QA_FAIL; repair the complete draft rather than sending a half-quality report.
Regression: the 2026-11-04 automated draft was DRAFT_UNVERIFIED and omitted 2026-11-03 after-hours AMD Q3 2026 official revenue $13.377bn / Data Center $8.546bn / next-quarter revenue guide ~$17bn. A manually researched and independently numbered 12-chapter full recovery was sent with Gmail Sent ID `1a1a481104e18df5` and Git canonical archive `us-stock-daily/reports/daily/2026/2026-11/2026-11-04.md` (commit `b6979faad2a076981e48fdd732ec6438186e4712`). This proves one recovered delivery; it does NOT prove the scheduled source pass is repaired.
Failure-handling: failed optional Git/cross-day QA write must not itself become a permanent no-send loop when a truthful independent semantic review of the final full 12 chapters is possible under the existing degraded-delivery policy. Keep CI_NOT_PROVEN if so, never rename it PASS, dedupe by actual Gmail Sent first, read back full sent body, and archive. Do not add a new automation or notify in ChatGPT App.

## STK-27 November 2 canonical-correction audit and residual exceptions (2026-11-08)
Verified failure: Nov2 2026 reissue Gmail `1a1b715f3180aa78` and `2026-11-02-corrected.md` had byte-identical report bodies, but original standard canonical `2026-11-02.md` still pointed to Gmail `1a199b7638c436ba`. The 31-day monthly manifest and future dedupe could thus silently select original. Fixed by preserving original full body at `2026-11-02-original.md`, promoting the exact corrected Gmail body to standard `2026-11-02.md`, and marking `2026-11-02-corrected.md` a noncanonical audit copy. These files must never count as 3 separate reports; only D.md is authoritative. Gmail Sent + Git readback prove delivery/body sync; cloud CI still `NOT_PROVEN`.
Audit caveat: corrected email itself retains a brief resend-version explanatory sentence, and original daily emails remain stored. STK-13 editorial preference for process text only in internal audit is therefore not perfectly satisfied retrospectively. Do not pretend a past already-Sent body can be silently edited or blindly send another copy solely to erase harmless release metadata. Future corrections should place detailed process failures exclusively in YAML/run audit and use only a concise user-relevant correction header if necessary.
A report with 12 headings but no real fact in several sections is not full semantic QA. For weekend/holiday dates, a genuinely empty research lane may use neutral no-news text, but the report must still show independently validated material issuer/market developments, future catalysts and a decision-oriented watchlist when source evidence exists; mark discovery PARTIAL if sources are not read. An audit of delivered body must not claim `CI_QA_PASS` absent actual CI receipt.

## STK-27 — real 2026-11-02 email had empty chapters despite 12 headings
14-day actual Sent-body inspection (Oct25–Nov7) found 14/14 stock daily messages, but Nov2 was only ~3.5K chars and retained all 12 headings while six sections had zero numbered items; some were just unnumbered paragraphs and §5/6/10/11 were generic `无高置信新增`. This passed prior structural checking because `scripts/novelty_gate.mjs` only checked heading count and numbering of existing items. A correctly dated US weekend/holiday may have no new exchange close; it must still deliver valid prior session context, current news, original-source catalysts, risk/watch conditions, IPO stage when useful and explicit provenance. Zero-numbered substantial section must fail `EMPTY_STOCK_SECTION` in the edited code and block formal mail until corrected; don't manufacture new quotes or issuer events to pad sections.
Correction sent to original Gmail subject `美股每日晨报｜2026-11-02｜完整更正补发（结构与内容修复）`, Sent `1a1b715f3180aa78`; archived exact readback at `us-stock-daily/reports/daily/2026/2026-11/2026-11-02-corrected.md`, commit `9308926e58a02b5ccab2348c4a31121d5d400cac`. Original Gmail ID `1a199b7638c436ba` retained for audit. Source gate patch at `scripts/novelty_gate.mjs` and regression test at `tests/test_novelty_gate.mjs` verified by Git readback; 15/15 cases pass in isolated JS reproduction (CI on GitHub not independently proven). New task must honor gate; if QA fails try within existing 08:40 recovery, not send another empty skeleton. No separate monitor.

## STK-28 — issuer IPO state must be as-of-report verified (2026-11-08)
Historical regression: the Aug20 2026 report wrongly described Cerebras as still pursuing an IPO after May14 listing and May15 close. It recited an earlier May4 S-1 proposed $115–$125 range and 28M shares as if an open offering; definitive issuer May13 pricing and SEC May15 8-K already showed $185 and 34.5M total shares. A partial source QA/12-headings test let this material fact through. Formal corrected email `1a1b7892ab4b79bd`, original `1a01cb7369b2b78f`; canonical `reports/daily/2026/2026-08/2026-08-20.md` updated, original archived `-original.md`.
Acceptance gate for any named pre-IPO/IPO/ticker/public-offering item: verify at least one issuer IR original publication and SEC effective registration or 8-K/424(b) plus actual exchange listing status **as of report date**. The most recent *authoritative issuer event* wins over older draft S-1 data and secondary articles. Classify `IPO_PIPELINE` vs `PRICED` vs `ALREADY_TRADING` vs `CLOSED` explicitly; if already trading, do not call it pending or imply IPO subscription eligibility. Record offer shares and price as proposed vs actual, with event date and evidence links, and do not reuse a dated price without the final settlement and trading-stage check. On source gap write `IPO_STAGE_UNVERIFIED` and block a claim about actionable subscription; do not manufacture listing date, price or price targets. A static text/heading lint passing does NOT establish factual stage QA. Previous actual Gmail corrections are immutable; future corrections require one verified new Sent and exact canonical body.



## STK-29 — 2026-11-11 cross-day replay, seven-day receipt and non-padding correction
The original 2026-11-11 QA review found related risks to the Crypto rights replay problem in stock delivery: (a) the original `scripts/novelty_gate.mjs` treated absent last-seven-day delivered reports as only a warning; (b) old `CALENDAR` events could be re-numbered on a later date without a materially new issuer change, and calendar dates outside the coming 72 hours were not strictly rejected; (c) prior strict 12-item-section check encouraged padding with status/no-news meta text; (d) historical 2026-11-01 §10 and 2026-11-03 §11 were empty despite 12 top-level headings in delivered email. Empty headings alone are a content QA exception; they do not prove a specific new issuer event was missed, so do not invent historical news to send a cosmetic correction.

The final sent stock daily must:
1. Read seven **consecutive actual prior Bangkok report dates** from Gmail Sent full-body messages; if Gmail momentarily unavailable use the verified *one canonical final Git report* per date, recording actual Gmail ID/visible archive version and actual body text checked. `previous_days_checked` must be the exact seven dates D-7..D-1, unique and not placeholders; absent baseline is `PREVIOUS_SEVEN_SENT_DAYS_NOT_PROVEN`, a hard semantic QA failure. User-authorized ordinary daily delivery may still use independently source-checked manual equivalent under a genuine runtime/API limitation, but must record the exception and never label executable QA PASS or quietly invent historical checks. A missing optional Git write after independent full QA is not by itself a reason to fail Gmail delivery.
2. Every nonroutine numbered story has stable `family_key`, source date, real `material_version`, source URL, primary section and explicit old→new proof if previous family version exists. Already reported old statuses, old notifications, SOURCE_GAP, unverified issuer results, monitoring/Git/Gmail/QA execution narration, and 'no high-confidence update' must not be numbered to fill a chapter. The fixed §11 `漏检复盘与监控修正` heading stays in the original 12-heading layout, but its detail should be real market evidence / a meaningful analyst model revision; internal process repair belongs in Git run audit.
3. Future calendar item must concern a verifiable event within the current **72-hour horizon**, and cannot repeat an already delivered `calendar_date/material_version` on a later day as allegedly new. Repeated family requires real new schedule, changed field, previous/new value and a newer official source. Once the actual earnings/CPI result arrives, replace 'upcoming' with the actual released result in its natural primary section.
4. A chapter legitimately having NO fresh news stays under its fixed heading with exactly unnumbered `无高置信新增。` ONLY if there is an actual readable original source receipt, checked_at and a specific internal reason of at least 25 characters for that chapter. The amended validator accepts an evidence-backed blank with `empty_section_reasons[]` and `section_source_receipts[]`; otherwise fails `EMPTY_STOCK_SECTION`. This explicitly supersedes older unconditional "every chapter must contain a numbered item" guidance. Never fabricate a market event or repeat a stale IPO for section-count compliance.
5. Run the updated `scripts/novelty_gate.mjs` on the actual final `items/events/previous_events` manifest when Node is available; its push-only CI workflow is tests/provenance only. Without executable runtime, perform per-item/cross-day manual equivalent and record `CODE_NOT_EXECUTED`, `MANUAL_EQUIVALENT_ONLY` truthfully. The final actual Gmail Sent body, recipient and date prefix must be read back and exactly match the canonical Git `reports/daily/YYYY/YYYY-MM/D.md`. Old corrections remain immutable audit; only the latest actual corrected Sent is canonical. A Git archive write failure after verified Sent is `SENT_ARCHIVE_PENDING`; next existing run repairs only Git and NEVER resends.

The existing scheduler (05/06/07/08:40 Asia/Bangkok), unique original automation, Gmail recipient, 12-heading form and monthly report remain unchanged. An old successfully Sent report is not automatically factually perfect, and a future unattended delivery is only proven after real Sent+Git readback.


## STK-30 — Prior seven-day full-body evidence contract and archival authority (2026-11-11)
The existing STK-29 and no-repetition gate failed to objectively prove its claimed seven-day dedup baseline because `previous_days_checked` was only an array of seven date strings. A generated manifest could claim all seven dates without reading ANY Gmail/Git body. The current `scripts/novelty_gate.mjs` now also requires `previous_day_receipts` with exactly one entry per preceding Bangkok calendar day, `date`, `source=GMAIL_SENT` and actual `gmail_message_id`, `sent_readback=true`, `full_body_reviewed=true`; alternatively `source=GIT_CANONICAL`, real 40-character blob SHA, `canonical_readback=true`, `full_body_reviewed=true`. Merely naming the dates, a guessed ID, filename, or draft is insufficient; the validator checks the proof schema while run audit must preserve actual tool evidence. The seven-day reviewed edition is the latest verified corrected version under the unique canonical D.md, not superseded sidecars.

If any previously issued stock, AI, earnings, IPO, Fed or calendar story appears again, compare stable family_key and material_version. A new publisher headline or current report date does not establish a material delta. An unchanged future deadline already notified is an internal watch event unless it changes execution or eligibility, while updated official results can be fresh. §十一 only gets a genuinely decision-relevant research/model failure, never task/Gmail/Git/CI logs. A section can retain the unnumbered neutral no-news line after actual source inspection and internal reason; do not fill with old facts simply to hit 12 item count. BLS, SEC, corporate IR actual source state wins over old reports.

Every sender/recovery invocation performs all semantic QA on the exact proposed full 12-chapter body before sending. Node available: run `scripts/novelty_gate.mjs` with receipts and preserve result. No Node: independently verify seven actual full prior message bodies and review every item; state `CODE_NOT_EXECUTED/MANUAL_EQUIVALENT_ONLY`, never promise executable PASS. Missing proof should trigger reconstruction in the existing 07:40/08:40 windows, not fabricate 7 dates nor turn the mail into a digest. Preserve Gmail Sent ID+full body as canonical Git D.md; archive old corrected variants separately, never rewrite historical emails. Git fail after real Sent => SENT_ARCHIVE_PENDING, archive-only retry. This code-and-prompt patch does not prove future autonomous delivery until actual scheduled Gmail Sent readback + Git exact body.
