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
