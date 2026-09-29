# TGE / Airdrop Regression Results — 2026-09-29

Status: POST-FIX PASS
Rules under test:
- ACTION_GATE.md
- MONITOR_SPEC.md mandatory ACTION gate
- AUTOMATION_RUNTIME.md ACTION gate override
- state/known-events.md
- REGISTRY.md rights-source mapping
- docs/MONITORING/NOTIFICATION_POLICY.md TGE hard gate

## Deterministic suite

| ID | Expected | Post-fix result | Pass |
|---|---|---|---|
| TGE-01 | ACTION | Tier A + fresh + new + rights relevant -> ACTION | PASS |
| TGE-02 | NO_ACTION | Tier C/D cannot authorize ACTION | PASS |
| TGE-03 | NO_ACTION | old unchanged source fails freshness/material-delta gate | PASS |
| TGE-04 | NO_ACTION | state/known-events user-known event suppresses duplicate | PASS |
| TGE-05 | NO_ACTION | CLOSED/FULLY_REFUNDED exits at Gate 0 | PASS |
| TGE-06 | ACTION | explicitly mapped Tier B rights source may authorize a material rights event | PASS |
| TGE-07 | NO_ACTION | stable event key + known-event state suppress repeated outlets | PASS |
| TGE-08 | NO_ACTION | identity/collision hard fail | PASS |
| TGE-09 | ACTION once | replacement route is a material delta and new event version | PASS |
| TGE-10 | NO_ACTION | undated/static page cannot create a new event by itself | PASS |
| TGE-11 | ACTION | mapped direct rights platform is Tier B first-party-for-rights | PASS |
| TGE-12 | NO_ACTION | checked_no_update remains silent | PASS |
| TGE-13 | NO_ACTION | delivered event + no delta suppressed | PASS |
| TGE-14 | UNHEALTHY | final/final-retry remains mandatory completion proof | PASS |
| TGE-15 | NO_ACTION | generic financing/valuation without user-level rights impact is background only | PASS |
| TGE-16 | NO_ACTION | completed/claimed/refunded known state suppresses same action | PASS |

Result: **16 / 16 PASS**.

## Live-source smoke controls from 2026-09-29

These are discovery smoke tests, not user notifications.

### MetaMask
Official MetaMask Rewards/Help Center still exposes the already-known Money Sweepstakes campaign. The stored known event key is already delivered. No new deadline/eligibility/rule delta was found in this smoke pass.

Decision: NO_ACTION.
Reason: known + delivered + unchanged.

### Space / Spacecoin collision
Fresh search surfaced a secondary Bitget article about **Spacecoin** opening a SPACE-token claim. The monitored registry entry is **Space @intodotspace**.

Decision: NO_ACTION / IDENTITY_FAIL.
Reasons:
- wrong project identity;
- secondary source;
- explicit Space/Spacecoin collision regression rule.

This is the exact class of false alert that caused the 2026-09-14 incident and is now blocked before notification.

### Cambria
Fresh secondary coverage repeats the existing RSGP Genesis opt-in deadline. The user already received the recovered Cambria opt-in alert with Gmail delivery proof.

Decision: NO_ACTION.
Reason: unchanged delivered event. A new official extension/reopen would be a separate material delta.

## Historical regression controls

- humans& full refund/CLOSED -> suppressed before discovery.
- MetaMask duplicate GitHub archives with same Gmail message id -> treated as one logical event.
- Crusoe Series F generic valuation -> under the new gate, future comparable funding/valuation news is NO_ACTION unless mapped deal-rights evidence shows user-level term impact.
- Space/Spacecoin -> hard identity fail.

## Remaining limitation

This suite proves decision-gate behavior. It does not prove every external source will always be reachable. Provider/search outages must remain visible as source gaps and may delay discovery, but cannot be converted into fabricated NO_ACTION or secondary-only alerts.
