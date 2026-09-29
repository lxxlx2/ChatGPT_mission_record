# TGE / Airdrop Regression Cases

Updated: 2026-09-29

These are deterministic acceptance fixtures. They are intentionally independent of live market discovery so future rule changes can be checked against the same expected outcomes.

| ID | Fixture | Expected |
|---|---|---|
| TGE-01 | Canonical project official source announces a new current claim/deadline/action page | ACTION |
| TGE-02 | Media/KOL/independent source only; no first-party/direct-rights proof | NO_ACTION |
| TGE-03 | Old official announcement resurfaces with no changed event field | NO_ACTION |
| TGE-04 | User already told ChatGPT the same event and it is persisted as known | NO_ACTION |
| TGE-05 | Fully refunded/CLOSED deal with no remaining entitlement | NO_ACTION |
| TGE-06 | Explicitly mapped SPV/platform confirms new refund/allocation/settlement affecting user rights | ACTION |
| TGE-07 | Same event repeated by many secondary sources | NO_ACTION after first known event |
| TGE-08 | Same-name/cross-project collision, e.g. Spacecoin candidate while monitoring Space @intodotspace | NO_ACTION / IDENTITY_FAIL |
| TGE-09 | Canonical project officially replaces an old claim route with a new one | ACTION once as material delta |
| TGE-10 | Undated/static candidate with no direct current rights-state proof | NO_ACTION |
| TGE-11 | Direct mapped user-rights platform proves live claim/refund while project is silent | ACTION |
| TGE-12 | Reachable official source, no material change | NO_ACTION |
| TGE-13 | Previously delivered event reappears unchanged | NO_ACTION |
| TGE-14 | Attempt exists but final/final-retry completion proof is absent | UNHEALTHY; never count as healthy NO_ACTION |
| TGE-15 | Underlying company funding/valuation changes, but user's SPV/allocation/terms/fees/rights do not | NO_ACTION |
| TGE-16 | User already completed/claimed/opted-in/refunded and same action is rediscovered | NO_ACTION |

Pass requirement: 16/16.
