# US Stock Daily Post-Fix Regression — 2026-09-29

Status: POLICY REGRESSION PASS + HISTORICAL NEGATIVE/POSITIVE CONTROLS PASS

Rules:
- REPORT_SPEC.md
- REPORT_ACCEPTANCE.md
- AUTOMATION_RUNTIME.md content acceptance/manifest gate

## Deterministic suite

STK-01 PASS — fixed 12-section contract.
STK-02 PASS — source failure cannot downgrade structure.
STK-03 PASS — below-threshold prebuild is QA_FAIL.
STK-04 PASS — Gmail success/GitHub failure becomes archive-only recovery.
STK-05 PASS — Gmail failure retains same complete pending body.
STK-06 PASS — short digest is rejected as official.
STK-07 PASS — same-day delivered report dedupes.
STK-08 PASS — attribution/causal claims remain evidence-bound.
STK-09 PASS — weekend/holiday still requires latest session + current context; exception must be explicit.
STK-10 PASS — generic private-company news is separated from user-rights changes.
STK-11 PASS — body mismatch blocks full delivery completion and triggers archive repair only.
STK-12 PASS — <70% trailing-5 length/item collapse fails QA absent documented genuine low-event exception.

Result: **12 / 12 PASS**.

## Historical negative controls

### 2026-09-29 short recovery digest
Gmail id: 1a0ebc37335f3ba0
- body length: 542
- canonical sections: 0
- numbered items: 0
New result: **REJECT / QA_FAIL** under STK-01 + STK-06.

### 2026-09-28 thin formal report
Gmail id: 1a0e5cc0b292b1e6
- body length: 2169
- numbered items: 31
Using the five prior complete controls for the 2026-09-29 evaluation:
- trailing-5 median length: 5162
- 70% threshold: 3613.4
- trailing-5 median numbered items: 48
- 70% threshold: 33.6
New result: **REJECT / QA_FAIL** under STK-12 unless a genuine low-event exception is documented and all semantic gates pass.

## Positive control

### 2026-09-29 final formal resend
Gmail id: 1a0ebd0a1d3cc2a8
- body length: 4251
- sections: 12
- numbered items: 54
- threshold length: 3613.4
- threshold items: 33.6
- Gmail body == GitHub canonical body: true

New result: **ACCEPT / QA_PASS**.

## Scope note

This proves the new acceptance logic against deterministic and real historical controls.
It does not yet prove the next scheduled 07:00 -> 08:00 -> 09:00 automation cycle end-to-end. That requires the next live run to create a manifest, QA-PASS pending, Gmail proof and exact GitHub archive.
