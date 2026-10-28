# Three existing monitors: 2026-10-27/28 delivery, app-message and novelty audit

Observation time: 2026-10-28 12:52 Asia/Bangkok.
Scope is the THREE existing enabled ChatGPT automations only. No new scheduled automation, no Mac agent, no additional timed workflow, no change to original schedule or Gmail recipient. User requested **email delivery only** and **zero task-generated text on the ChatGPT app conversation**.

## Real Gmail and Git evidence

| Monitor/date | Gmail actual Sent | Git canonical |
| --- | --- | --- |
| Crypto 2026-10-27 | `1a17b2d317942c5a` | `crypto-daily/reports/daily/2026/2026-10/2026-10-27.md` |
| Crypto 2026-10-28 | `1a180500065679d2` | `crypto-daily/reports/daily/2026/2026-10/2026-10-28.md` |
| US stocks 2026-10-27 | `1a17ace257d35937` | `us-stock-daily/reports/daily/2026/2026-10/2026-10-27.md` |
| US stocks 2026-10-28 | `1a17ff534fa52261` | `us-stock-daily/reports/daily/2026/2026-10/2026-10-28.md` |

All four were observed in Gmail Sent; their report bodies were read in the current audit. Reports were delivered and do not need any resend. No new TGE entitlement alert exists in Gmail Sent; current genuine `airdrop-tge-monitor/state/current.md` points at 2026-10-28 12:04:14 BKK `PARTIAL` with 5 candidates, 0 action, 5 source gaps; no blank claim email should be sent.

Crypto 28 body: 13 sections, 34 numbered items; US stocks 28: 12 sections, 43 numbered items. A schema PASS previously verified only sections/receipts and exact same event+version, not robust semantic cross-date recall.

## Proven app leakage

A targeted private task run check for Crypto task `6a8600b9d12481919bc43ebc800c9916` returned latest 2026-10-28 12:20 run **completed** but `latest_result.content_text` contained about 1,272 characters of research summary, exact Git blob hashes, market values and source gaps. This explains the user-visible task-conversation message despite prior `notifications_enabled=false` and `email_enabled=false`. User saw the 12:24 message on iPhone. It is a nonempty task assistant completion, NOT evidence of a newly authorized Gmail and NOT the same control as disabling push notifications. Before this fix the prompt said "App silent" but did not actually suppress task completion output.

**Changed all 3 existing task prompts to demand a literal zero-character assistant completion in every scheduled slot.** The prompt continues to run collection/prebuild/full Gmail/known-events actions with Git receipts. Internal failures and noteworthy findings stay Git-only until a legitimate original-email action. The platform may still display a task or conversation shell; task prompt text cannot guarantee that an app hides every internal run. This exact UX behavior must be rechecked on future task executions before declaring App silence fixed.

## Actual duplicate check failure & repair

The prior `crypto-daily/scripts/editorial_gate.mjs` only rejected `event_key::material_version` exact matches. A daily key or new descriptive version could bypass it even if the underlying incident had no real new state. Existing `daily_event_gate.mjs` also treated `material_delta` string length as proof of freshness and used aliases that many latest ledger events left empty. Old prebuilt Oct28 manifest lacked stable family fields and was nevertheless approved by original CI. Running the *new* gate against that immutable old draft returns `NEWS_EVENT_MISSING_FAMILY_KEY` on 20 published narrative events. **This is a prospective stricter rule, not a retroactive reason to send another Oct28 email.**

The new executable Crypto editorial gate requires family keys for non-routine narrative events. An already delivered incident family can appear again only with a different version AND a linked official `novelty_proof` (specific changed field, actual before/after state, primary evidence URL/time, old version binding), and the new value must appear in the published item. Narrative family replay with only date/title updates is a hard failure. Recurring market prices/actual new ETF reporting days are not artificially prohibited. Five new regression cases cover daily-key replay, same family/version, genuinely changed issuer state, unmentioned claimed updates, missing family. GitHub push-only CI self-test actually reported `NODE_TESTS_PASSED_ON_GITHUB_RUNNER_NOT_PRODUCTION_DELIVERY` for commit `072ae6663bb5f15b2b253879ff38da337c7c71b5`, matching editorial gate blob `8cfec73aeeca310fd5f86ba88a410c151ba69d9e`. This DOES NOT retroactively validate the prior daily.

US-stock daily `REPORT_ACCEPTANCE.md` new STK-23 now requires stable family facts, measured-session exceptions, old/new official evidence and no repeated AI-capex/FOMC/ETF-overlap essays across chapters. New `us-stock-daily/scripts/novelty_gate.mjs` has nine checked test cases; its own push-only **non-timed** `.github/workflows/us-stock-novelty-qa.yml` runs the real Node tests and, for new JSON daily manifests, checks the reported body and records SHA-bound receipt. Actual GitHub cloud self-test `us-stock-daily/delivery-qa/_ci-selftest.json` says `NODE_TESTS_PASSED_NOT_A_DAILY_REPORT`; per-report QA must not be inferred from that smoke test. Original stock task prompt was updated to prepare a JSON manifest and compare the future per-report SHA when possible. Old canonical MD/Gmail historical reports remain intact.

**Truth about the repeated example**: ConnectWise changed status over multiple October 26–27 issuer releases; a genuinely new official state transition can deserve a short §9 follow-up. But repeating "still awaiting validation" with no new state on subsequent days is not a fresh security incident. In US stocks, a completed new market session is a legitimate new fact; describing generic AI debt risk and FOMC anticipation as fresh in several separate sections is not.

TGE's `AUTOMATION_RUNTIME.md` was updated to demand true zero-character app output, one canonical Git final, and stable project+beneficiary+right+window dedup. Partially checked shards are not fully verified completion, and a third-party claim calendar is not a wallet-specific ACTION.

## Delivery/channel invariant and residual risk

- Existing Crypto schedule: Asia/Bangkok 00/03/06/08/09/10/11/12/16/20:20. Existing stock: 05/06/07/08:40. Existing TGE: every HH:00. All remain enabled.
- No extra test/resend was emailed. Only the two regular October 27 and two regular October 28 report deliveries are reported here.
- **Not yet production-proven:** the NEXT scheduled tasks produce *no user-visible chat text*, their future JSON manifests really include source-bound family deltas and pass relevant per-report CI, and all normal Gmail Sent/readback/Git workflows remain complete. This is not a claim that disabling task reply text disables the ChatGPT app's conversation UI itself.
