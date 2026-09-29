# Crypto Daily Post-Fix Regression — 2026-09-29

Status: POLICY REGRESSION PASS + HISTORICAL NEGATIVE/POSITIVE CONTROLS PASS

Rules:
- REPORT_SPEC.md
- REPORT_ACCEPTANCE.md
- DELIVERY_RUNBOOK.md
- AUTOMATION_RUNTIME.md daily input manifest + acceptance gate
- SECURITY_SOURCE_POLICY.md

## Deterministic suite

CR-01 PASS — fixed 13-section formal contract.
CR-02 PASS — missing research hour can use final compact payload but gap remains visible.
CR-03 PASS — multiple missing hours are manifest gaps, never implicit no-event.
CR-04 PASS — material security candidate must be included or explicitly excluded after fresh verification.
CR-05 PASS — unavailable X/specialist source remains a source gap.
CR-06 PASS — MEXC-style major-CEX account takeover enters security verification.
CR-07 PASS — unchanged security incident is deduped.
CR-08 PASS — stale/refunded/completed/user-known TGE state is not recycled as new.
CR-09 PASS — unexecuted Early/Meme/NFT lane cannot become “no opportunities”.
CR-10 PASS — institutional/ETF/whale/exchange-flow lane is mandatory in manifest.
CR-11 PASS — Gmail success/GitHub failure becomes archive-only recovery.
CR-12 PASS — recovery uses exact QA-approved complete body.
CR-13 PASS — short supplement cannot replace formal daily.
CR-14 PASS — body mismatch blocks full delivery completion.
CR-15 PASS — quality collapse caused by provider/time pressure fails QA.
CR-16 PASS — monitoring plumbing remains in audit rather than dominating user report.
CR-17 PASS — uncertain causes remain explicitly uncertain.
CR-18 PASS — a complete formal edition may supersede an incomplete same-day edition once with audit trail.

Result: **18 / 18 PASS**.

## Historical negative controls

### 2026-09-29 security-only supplement
Gmail id: 1a0ebc29028e8873
- body length: 998
- canonical sections found: 4
New result: **REJECT as formal report** under CR-01 + CR-13. It can exist only as a supplement.

### 2026-09-29 original formal email
Gmail id: 1a0eba9364d76840
- body length: 2310
- sections: 13
- numbered items: 33
For the final 2026-09-29 quality control:
- trailing-5 median complete body length: 3608
- 70% threshold: 2525.6
- trailing-5 median numbered items: 38
- 70% threshold: 26.6
The body length falls below the collapse threshold.
It also missed the known material MEXC account-security event.
New result: **REJECT / QA_FAIL** under CR-04 + CR-06 + CR-15 even though all 13 headings existed.

This demonstrates why “13 headings present” is no longer accepted as proof of report health.

## Positive control

### 2026-09-29 final formal resend
Gmail id: 1a0ebd5c1a24ba6a
- body length: 4577
- sections: 13
- numbered items: 58
- threshold length: 2525.6
- threshold items: 26.6
- Gmail body == GitHub canonical body: true

New result: **ACCEPT / QA_PASS**.

## Scope note

This proves the new acceptance logic against deterministic cases and real historical failures.
Full live end-to-end acceptance requires the next 08:00 manifest -> 09:00 primary publisher/recovery cycle to leave:
- delivery manifest;
- qa_status PASS;
- complete pending body;
- Gmail Sent/readback;
- exact GitHub archive/readback.
