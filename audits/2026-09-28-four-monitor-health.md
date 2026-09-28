# Four-monitor health audit — 2026-09-28

Audit time: 2026-09-28 19:34 Asia/Bangkok

Systems:
1. Crypto Daily
2. US Stock Daily
3. $300 Crypto Mission / Monster
4. Airdrop-TGE / rights monitor

## Crypto Daily

Health: DEGRADED_DELIVERY, collector partly healthy.

Evidence:
- 2026-09-26 delivery ~09:17
- 2026-09-27 delivery ~12:08 manual recovery
- 2026-09-28 delivery ~09:16 manual recovery
- today's 09:00 scheduled publisher did not create a completed final/send
- ordinary hourly collector later resumed, but some research writes are blocked by provider safety checks
- security specialist coverage is frequently unavailable

Fix:
- 08:00 prebuild delivery-pending body
- 09:00 Gmail-first delivery
- non-critical missing sources no longer block
- specialist security source rotation over four hours
- existing fallback remains idempotent

## US Stock Daily

Health: FAILED_SCHEDULED_DELIVERY today.

Evidence:
- 08:00 and 09:00 produced no durable run artifact/Gmail
- 09:16 manual recovery delivered today's report
- automation prompt was extremely large and attempted too much work before delivery

Fix:
- new compact AUTOMATION_RUNTIME.md
- 07:00 prebuild
- 08:00 delivery-first
- 09:00 recovery
- bounded 12-section report; missing secondary metrics do not block Gmail
- schedule should be changed from 08/09/12 to 07/08/09

## $300 Crypto Mission

Health: CORE_AUDIT_RUNNING, OPPORTUNITY_MONITOR previously ineffective.

Confirmed regression:
- BTW entered shortlist 2026-09-27 12:34 but was starved by max-3 deep-check cap
- later cycles incorrectly marked Monster not_due
- BTW later met objective market gates but no alert was emitted

Fix already applied:
- durable DEFERRED_SHORTLIST
- >=1 oldest deferred deep-check per due scan
- elapsed-time due logic
- 19:29 mandatory full scan
- manual 19:22 health-check: 226 liquid symbols; HBAR PRESSURE; no sampled IGNITION

## Airdrop/TGE

Health: DEGRADED / CLOCK_AND_DELIVERY_INTEGRITY.

Confirmed issues:
- state/current.md was stale by >1 day
- 19:19 latest run remained provisional/incomplete
- impossible future run timestamps existed
  - file claiming 20:15 was actually committed ~10:13 Bangkok
  - file claiming 22:15 was actually committed ~18:18 Bangkok
- Crusoe material valuation ACTION was detected at 13:13 but Gmail failed and later NO_ACTION runs did not recover it

Fix:
- future timestamp artifacts marked non-authoritative
- actual wall-clock validation rule
- pending ACTION delivery survives later NO_ACTION
- state cache refreshed
- Crusoe recovery email delivered: Gmail id 1a0e801b313706a0
- event archived with delivery proof

## Overall

All four systems had real reliability defects. This was not simply a lack of market events.

Priority after this patch:
1. prove US Stock sends automatically by 08:10 next run
2. prove Crypto Daily sends automatically by 09:10 next run
3. verify 19:29 Monster full scan + Gmail summary today
4. verify next TGE run completes with non-future timestamp and closes provisional state
