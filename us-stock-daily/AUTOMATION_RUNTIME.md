# US Stock Daily Automatic Runtime

Updated: 2026-09-28 19:34 Asia/Bangkok
Timezone: Asia/Bangkok

Authority for the existing `美股每日晨报` automation.

## Objective

Deliver one official morning report every Bangkok date with Gmail proof and GitHub archive.

Normal target:
- 07:00: prebuild only
- 08:00: official delivery
- 09:00: recovery only if delivery proof is missing

Do not create duplicate official emails.

## 07:00 prebuild

Create:
`us-stock-daily/delivery-pending/YYYY-MM-DD.md`

Build a complete but bounded report from:
- latest completed US session;
- index/sector breadth when reliably available;
- rates, oil, FX and macro;
- highest-signal company/AI/infrastructure events;
- active user private-market deals only;
- upcoming 24-72h catalysts.

Do not send Gmail at 07:00.

Do not run exhaustive historical backfills or scan every possible sector metric before the pending report is durable.

## 08:00 delivery first

First actions:
1. search Gmail Sent for today's official subject prefix;
2. check official GitHub report;
3. if both complete, exit silently;
4. otherwise read the pending body;
5. refresh only material time-sensitive premarket/macro facts;
6. send Gmail;
7. Gmail readback;
8. archive identical report to GitHub;
9. write completion audit.

Target delivery: by **08:10 Asia/Bangkok**.

A missing secondary metric/source is written as unavailable and does not block delivery.

## 09:00 recovery

If Gmail proof is missing:
- use the existing pending body or GitHub report;
- QA it;
- send first;
- read back;
- archive/fix GitHub second.

Do not restart a broad research cycle before recovery delivery.

## Report quality

Keep the established 12-section structure, but breadth is bounded.

Required factual core:
- major indices / previous session;
- current premarket or global risk context when available;
- rates/oil/macro;
- major sector/company drivers;
- AI/technology/private-market material events;
- 24-72h calendar;
- risk radar;
- concise buy-watch section only when evidence exists.

If a field cannot be verified, say so. Do not invent precision.

Use high-quality English/official sources only. No Chinese-language websites.

## User-specific private market

Only active capital/rights exposure consumes user-specific monitoring.

Closed/refunded deals are historical only.

A deal-host/SPV/intermediary rights event can be material even when the underlying company posts nothing publicly.

## Reliability

At each scheduled run, attempt to persist a small run audit immediately.

GitHub audit failure must not block Gmail delivery at 08:00/09:00.

Provider/source failure in one lane must not abort the whole report.

The scheduler trigger alone is not delivery proof. Gmail Sent message id + readback is the delivery authority.


## Formal resend / correction completeness — 2026-09-29

Any user-facing resend, recovery resend, correction, or superseding edition that serves as the official morning report MUST be a complete formal report, never a short summary.

Requirements:
- preserve the established full 12-section structure;
- use the same quality bar as a normal on-time report;
- re-read the latest complete historical formal report before drafting if format drift is possible;
- refresh material time-sensitive facts;
- send the complete body by Gmail and read it back;
- archive the exact Gmail body to GitHub and read it back;
- mark any earlier incomplete same-day recovery email as superseded in GitHub metadata;
- GitHub failure may delay archive, but MUST NOT reduce the Gmail body to a summary.

A short bullet digest may be sent only when the user explicitly asks for a short digest. It can never silently substitute for the formal morning report.


## Content acceptance and manifest gate — 2026-09-29

This section overrides any older wording that allowed delivery-first recovery to reduce content quality.

Every scheduled run reads:
- `REPORT_SPEC.md`
- `REPORT_ACCEPTANCE.md`

### 07:00
Before marking the pending report ready, create:
`us-stock-daily/delivery-manifest/YYYY-MM-DD.md`

The manifest records, at minimum:
- latest completed US session date;
- index/session source coverage;
- breadth/volume coverage;
- rates/oil/USD/macro coverage;
- major company/sector driver coverage;
- AI/tech/IPO/private-market coverage;
- institutional/flow coverage;
- policy/global coverage;
- 24-72h catalyst coverage;
- active user-rights coverage;
- source gaps;
- trailing-5 body-length median;
- trailing-5 numbered-item median;
- draft body length/item count;
- acceptance checks STK-01..STK-12;
- `qa_status: PASS|FAIL`.

A pending body is `READY` only when the manifest says QA PASS.

If QA fails, repair only the missing coverage/sections and rerun the acceptance gate. Do not downgrade to a digest.

### 08:00
Delivery is allowed only from a QA-PASS complete pending body.

Refresh material time-sensitive facts, then rerun STK-01..STK-12 before sending.
If refresh causes a gate failure, repair before send.
Do not send a short fallback merely to meet the clock target.

### 09:00 recovery
Recovery uses the same QA gate.
If the stored pending body is incomplete or below the quality-collapse threshold, rebuild the missing coverage first, then send the complete 12-section body.

### Delivery success
A run may mark the formal report fully successful only when:
- Gmail Sent id exists;
- Gmail readback passes;
- GitHub canonical report exists;
- GitHub readback passes;
- report body equality with Gmail passes.

If Gmail succeeds but GitHub fails, mark delivery as Gmail-delivered/archive-pending and perform archive-only recovery. Never resend the same report because archive failed.

### Historical quality control
The latest five complete formal reports are the rolling quality control. Length/item thresholds are a collapse detector, not a target to pad with filler. Semantic gates remain authoritative.

## Single-write morning-delivery override — 2026-09-29 16:54 Asia/Bangkok

This section supersedes earlier attempt-file wording when it conflicts.

07:00:
- do not create an attempt audit;
- build manifest, complete 12-section pending body and STK-01..STK-12 QA in memory;
- after QA PASS, make at most one GitHub mutation to `delivery-pending/YYYY-MM-DD.md`;
- manifest summary may be embedded in the pending document.

08:00:
- dedupe Gmail Sent and canonical GitHub report first;
- if pending is unavailable, rebuild the complete 12-section body in memory from current facts and the latest complete historical format;
- Gmail send + readback is the first mutation/action that determines user delivery;
- after Gmail success, make one GitHub mutation to archive the exact Gmail body to the canonical report;
- do not create a separate run audit;
- Gmail success with GitHub failure is archive-pending and must not cause a duplicate email;
- if Gmail send is blocked, do not make repeated same-cycle send attempts; 09:00 performs recovery.

09:00:
- recover only the missing side with the same complete 12-section QA contract.

No monitoring task may be created, deleted, disabled or rebuilt as part of this repair.



## Durable-first recovery patch — 2026-09-30

Observed on 2026-09-30: the scheduler triggered around the delivery window, but no same-day pending/canonical artifact and no Gmail delivery existed. This proves trigger-time alone is not health evidence.

Current phased contract for the existing task:
- 06:00: primary bounded full-report prebuild; write a small attempt early, then QA-PASS `delivery-pending/YYYY-MM-DD.md` before optional enrichment.
- 07:00: repair/refresh pending only; avoid broad rebuild when a complete pending body already exists.
- 08:00: delivery first. Gmail Sent dedupe, pending read, only material freshness refresh, send/readback before archive. GitHub failure must not block an otherwise QA-PASS Gmail delivery.
- 09:00: recovery only. If Gmail exists, archive-only; if Gmail is missing, use pending/canonical or bounded recovery and send a complete 12-section report.

Reliability rules:
- long in-memory work without a durable checkpoint is prohibited;
- missing secondary data is recorded as unavailable and does not block a complete report;
- Gmail Sent id + readback is delivery authority;
- GitHub archive failure after Gmail success must never cause a resend;
- every recovery/resend remains a full 12-section report.

## 2026-10-09 verified actual schedule and delivery override (latest)

The single existing 美股每日晨报 scheduler uses Asia/Bangkok 05:40 prebuild, 06:40 repair, 07:40 primary, 08:40 recovery. This clarifies the actual schedule; older 07:00/08:00/09:00 prose in this document is superseded and must not be used to alter the existing scheduler.

For 2026-10-09, primary and recovery had a complete 12-section QA-PASS pending body but approved Gmail tool calls returned execution safety blocks. Manual official recovery sent one full report to the authorized recipient, Gmail id `1a1209a71157526b`; authoritative Git archive is `us-stock-daily/reports/daily/2026/2026-10/2026-10-09.md`. Same-day future invocations MUST dedupe this Sent and repair archive only, never resend.

Prioritize actual delivery over redundant research: compact attempt, read latest canonical and pending, Gmail Sent dedupe, validate latest completed market session / macro / 12 sections / STK acceptance, bounded repair, full text/plain Gmail, readback, identical Git archive/readback, terminal audit. If tool safety blocks an email, report real BLOCKED_WITH_REASON internally without claiming delivery; a future existing recovery slot may retry after Sent dedupe. Prompt simplification does not override platform checks or relax quality standards. No task, name, schedule, monitor scope, or monthly-subtask change.

## 2026-10-16 formal recovery and dedupe proof

The 07:40 automatic delivery invocation wrote `runs/2026-10-16/074000-final.md` with a real Gmail platform safety BLOCKED_WITH_REASON. The full 12-section QA-PASS pending body was already durable at `delivery-pending/2026-10-16.md`. The same authorized pending body was subsequently delivered successfully through Gmail with Sent/readback and archived identically:
- Gmail subject: `美股每日晨报｜2026-10-16｜正式补发`
- Gmail Sent id: `1a1428c5b456ae66`
- Git archive: `us-stock-daily/reports/daily/2026/2026-10/2026-10-16.md`
- Git commit: `b206e2d78ec01b36229ad38714fcb18e41df423e`

For every existing primary/recovery slot, dedupe against Sent subject **prefix** `美股每日晨报｜YYYY-MM-DD`, including `｜正式补发`, and verify matching recipient + complete readback/canonical Git body before any send. A previous blocked primary run must not override actual later delivery proof or trigger a second email. Persist a truthful terminal BLOCKED_WITH_REASON if Gmail is blocked again; do not bypass platform safety checks or weaken STK quality gates. Today's manual recovery confirms one delivery, not that future autonomous platform safety decisions are repaired.

## 2026-10-18 actual QA/Pending/Delivery single-write correction (latest)

Observed failure at the existing 07:40 2026-10-18 scheduled primary:
- \`us-stock-daily/runs/2026-10-18/074000-final.md\` correctly reports \`BLOCKED_WITH_REASON\`: a 12-section 55-item \`delivery-pending/2026-10-18.md\` was initially persisted with \`qa_status: PASS\`, but *afterward* STK-17/STK-18 semantic lint found items with weak decision value/process language. The attempted Git update to repair the same pending file was blocked by provider safety checks. Gmail was NOT attempted. A \`qa_status: PASS\` manifest written before final semantic lint is not authoritative.
- The same pending was independently rechecked and full Oct 18 email manually sent/read back: \`1a14c8c78a35b388\`, subject \`美股每日晨报｜2026-10-18｜正式补发\`, to \`lxx.run688@gmail.com\`, 12 chapters, 55 locally numbered items, 6188 chars; identical canonical archive \`us-stock-daily/reports/daily/2026/2026-10/2026-10-18.md\`, commit \`25908fca5264d6a50d3f0e50b5bf301ba1602416\`. Normal 08:40 recovery MUST dedupe this actual Sent and only repair archive, never re-email.

Required no-extra-task publisher sequence:
1. Check Gmail Sent exact **date prefix including corrected/resend subjects** first, and existing canonical readback. If already delivered, exit silently after archive-only repair where necessary.
2. **In memory** build full 12-section body; apply all CURRENT STK hard gates and semantic lints including STK-17/18/20, section-local numbering, event and source coverage, no operational filler and trailing-five collapse. If a lint detects weak items, fix the in-memory text and RE-RUN lint before marking \`QA_PASS\`.
3. After full lint PASS, persist at most **one** ready body (pending or equivalent complete terminal draft). A prebuilt early checkpoint must be labeled \`DRAFT_UNVERIFIED\`, never \`READY/qa_status: PASS\` before all semantic tests. Do not persist speculative PASS and then depend on an additional GitHub update of the same file.
4. If a second GitHub edit is blocked yet a *different* independently audited final in-memory full body passes ALL gates, Git is not a prerequisite to Gmail: attempt the legitimate Gmail send of that actual verified full body, then read back and archive exactly what was sent. This does NOT permit skipping QA, pretending missing proofs passed, or circumventing safety checks. A Gmail provider block remains \`BLOCKED_WITH_REASON\`; no false delivery claim.
5. At 07:40/08:40 ensure the terminal audit describes the final *verified body* and exact remaining gaps, rather than calling the whole operation PASS because a preliminary draft looked structurally complete. Report success only on real Gmail Sent/readback + canonical Git equality; manual recovery success does not prove future automated reliability.

Do not modify the existing scheduler, recipient, 12-section market-news scope, monthly reporting, quiet App policy, or safety constraints.

## 2026-11-23 Monday premarket fresh-event and no-duplicate recovery regression

P0 verified failure: 05:40/06:40 produced `us-stock-daily/delivery-pending/2026-11-23.md` marked DRAFT_UNVERIFIED, but 07:40 and 08:40 remained QA_FAIL_NO_SEND and had no actual Sent or canonical. The draft repeated Nov20 stock index prints, already delivered Anthropic IPO closing and Nov24 ADI/Dell dates without a stable material version, while new **Nov23 morning Reuters and AP news** about Asia AI-linked market losses, US futures rebound, and Asian market-rule measures was omitted. Original morning slot got stuck iterating source gaps and seven-day novelty review without discovering or writing today's real content. X login failure and missing a fresh IPO opportunity are not by themselves evidence a truthful complete report is impossible.

Within original 05:40/06:40 prep, collect last US full cash session with date, then perform date-scoped English official/Reuters/AP discovery of **today's Asia and US futures premarket cross-market shifts**, all significant dated corporate financial results and issuer IPO/stage changes. On Monday or a post-holiday session explicitly distinguish *old Friday close* from *new Monday Asia/futures*; report USD stock futures as a timestamped indication only, never as same-day closed share index. Today (Nov23) AP https://apnews.com/article/stocks-markets-rates-technology-ai-anthropic-49ba1beba78fa4ed2bd5898029f79c91 and Reuters https://www.reuters.com/world/china/global-markets-view-europe-2026-11-23/ were legitimate original-dated new sources and should have been considered. Older ADI/Dell earnings already in prior email may appear as an updated nearing calendar item but never a **new** IPO event.

At 07:40/08:40 if the first draft is repetitive, *fix it in place or in-memory* by substituting material newly verified dated events, dropping old repeated analysis, and applying genuine 12-chapter, source and seven-day Gmail/Git semantic checks. Unverified X/IPO that has no material event stays SOURCE_GAP or "无高置信新增。" with internal evidence and must not be fabricated, nor treated as an automatic general send veto. If independently required exact sources still fail, name the gate and do not claim success. Once the full editorially audited text meets rules, prioritize actual single Gmail Sent + recipient/full body readback + canonical exact Git. Do not require a second conflicting edit of an old pending file before sending a distinct fully approved body.

Nov23 has since been recovered manually: Sent `1a206fd2ccd55bfb`, canonical `us-stock-daily/reports/daily/2026/2026-11/2026-11-23.md`, blob `8d89d56b9a8ab3b8090ab344dd882dfc932e6052`. Absolutely no further send for same date. Next real 07:40 unattended Gmail+Git is required to validate production fix; unchanged task, original schedule, monthlies, email-only policy and no other automations.

## 2026-11-24 P0 missing phases and material Nvidia issuer discovery

Repeated production failure: 2026-11-24 original stock task was enabled; only `runs/2026-11-24/054000-attempt.md` was present (222 characters, status PREBUILD_IN_PROGRESS), no subsequent 06:40/07:40/08:40 terminal audit, no canonical and no Gmail Sent. The task's platform `completed` flag by itself cannot prove that sources, finished draft or a mail send existed. No actual error receipt proves the exact scheduler/runtime cause. This is a missing whole publication-stage problem, not merely another paragraph in an otherwise complete report.

Material missed facts: 2026-11-23 NVIDIA officially reinstated Jensen Huang as CEO and director immediately, while an independent board investigation continued (https://nvidianews.nvidia.com/news/nvidia-board-reinstates-jensen-huang-as-president-ceo-and-board-director). AP verified 11/23 full US cash close: S&P 500 7,237.17 (+326.78, +4.73%), Dow 49,595.31 (+1447.98, +3.01%), Nasdaq 24,089.56 (+1471.82, +6.51%), Russell 2669.66 (+87.87, +3.40%), source https://apnews.com/article/wall-street-stocks-dow-nasdaq-fcdf1bad36b4f81c90cbb0f33a2c5704. Reuters 11/24 Asia markets and yields provide new cross-market data at https://www.reuters.com/world/china/global-markets-global-markets-2026-11-24/. These updates outrank repeatedly describing Friday's old selloff, ADI/Dell calendar or already completed Anthropic IPO as a new headline. Issuer statement and market facts are distinct; don't present investigated allegations as resolved.

Repair only original task; keep latest Git 12-section scope, STK semantic dedupe, source hard gates, seven-day Sent verification, IPO/earnings/risk radar, monthly report, original 05/06/07/08:40 schedule and recipient. Runtime prompt is a concise bootstrapper instead of accumulated dated incident instructions. At 05:40 fetch previous completed US cash close and original/dated current issuer/SEC/AP/Reuters evidence, write one COMPLETE 12-chapter draft; at 06:40 actually finalize 7-day novelty, current morning macro and 12 sections; 07:40 send only after actual QA, 08:40 recover from source drafts or rebuild if missing. Do not stop simply because X/optional IPO data is inaccessible, but do not waive true hard material facts/semantics. After sending: Gmail SENT and full body readback, archive that exact body as unique canonical and single final. Code gates not run => CODE_NOT_EXECUTED, no CI claims. If material source fails, preserve real QA_FAIL and blocker receipts rather than empty success.

2026-11-24 manually recovered with Gmail Sent `1a20bcc62de875a9` and canonical `us-stock-daily/reports/daily/2026/2026-11/2026-11-24.md` blob `4a0c289ac614069e7729ff2ca7143702d3c780c6`; exact Gmail body check passed. Any same-day original slot must not resend. True recovery awaits next unattended 07:40 SENT/readback/Git proof. No additional monitor or changes to quiet notification policy.

## 2026-11-28 14:16 ICT recurrent scheduled-delivery regression
Four original morning attempts left finals but 08:40 was QA_FAIL_NO_SEND despite a substantive pending draft; missing evidence included prior seven-day exact canonical comparisons and independent current sources. Manual recovery verified 7/7 earlier Sent/Git bodies, new Census release and close data, sent 1a22102d746ba256 and exact canonical readback (commit f980c386de6371c188aaa238c65405b756fbb70d); partial coverage, code not executed. Original automation prompt updated and read back; times unchanged. Use actual available GitHub fetch_file/fetch/create_file/update_file and Gmail search_email_ids/batch_read_email/send_email operations, with exact schema where exposed. Complete required semantic checks before send; do not let redundant discovery/rule rereads consume publisher window. Optional gaps remain explicit. Manual delivery is not proof of autonomous recovery.
