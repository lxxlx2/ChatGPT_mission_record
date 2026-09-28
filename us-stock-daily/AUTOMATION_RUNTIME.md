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
