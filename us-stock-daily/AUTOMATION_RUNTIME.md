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
