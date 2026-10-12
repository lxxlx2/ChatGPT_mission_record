# Frank PR #39 — legacy Loop runtime divergence: final read-only investigation

Date: 2026-10-13, Asia/Bangkok. **Disposition: NO_GO for current controlled release; stop repeating source/time-only inventories.** This report uses user-supplied Mac read-only evidence, the committed historical deployment hashes, and the currently reviewed ops implementation. It does **not** authorize a Mac restart or release.

## Evidence from the latest user-supplied Mac file

Input: `frank-pr39-legacy-verification-20261013.json`; report gate `UNVERIFIED_RELEASE_BLOCKED`. No production DB mutation, email send, or service restart occurred.

| Probe | Observed result | Interpretation |
| --- | --- | --- |
| Dashboard actual runtime | PASS, process PID 25851, 147/147 Git-tracked source files matched, 0 extra | Disk source and runner are independently verified |
| Dashboard runner vs kernel process start | **-0.020413 seconds** | Runner was written ~20 ms **before** process birth; coarse `ps` start time had caused a false ambiguous-second result |
| Loop actual runtime | UNVERIFIED (`SOURCE_MIXED_BYTES`) | Gate remains blocked |
| Loop `server.py` | Git blob `b5eb4af5c945cc1b62337d48393fe02243f9505f`; observed `f5e00781ea4af45b4d6b15a09b8cb000f5b744f4` | Exact legacy pair documented in `scripts/deploy_frank_dashboard_review_badge.py` |
| Loop `static/app.js` | Git blob `8f0ac1beace94f01894c151576bc276f48f1b4a4`; observed `14985b35b019054d5ff9871e002c32421345ff17` | Exact documented legacy pair |
| Loop extra `delivery_review.py` | `62f5fa85bf41cd95e4a31a373910f81970368ea6` | Exact documented legacy extra module, not a random unverified file |
| Loop historical overlay MTIME | Three above files modified ~106233.64 seconds **after** Loop process birth | The current disk filesystem is newer than the running process; which code Python previously imported cannot be reconstructed from disk hashes alone |
| Loop runner MTIME | +162293.545126 seconds relative to kernel process birth | Runner changed ~45.08 hours **after** process start; current runner is **not** evidence of the script content initially executed by PID 79154 |
| Frank scanner | PID 52300, loaded hash observed `599f2f05f197725a25fd85a82501504a772f253866c0556183bbfd82da00a0ce` | Scanner evidence collected; don't infer full lifecycle acceptance |
| Frank latest BUY | 26 of 26 `USDC_DIRECT_NUMERIC`; 0 missing | Last-BUY amount semantics gate PASS, not all-history exhaustive |
| Mission Control outbox | 35 decisions and snapshots; 36 outbox, 18 Gmail, 18 local, 0 presentation rows | Counts only, not blanket permission for future messages |
| Historical Gmail MANUAL_REVIEW | 15; all `GMAIL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND`; 15 expired before send, 0 requiring private review by current diagnostic | Preserve historical identities and **do not retry or resend** |

## Causal and safety conclusion

All three Loop disk modifications have **known Git blob provenance**. This closes the question whether unknown source files were introduced. It does **not** prove that PID 79154 loaded those specific bytes: two Python files and one JS file were updated ~29.5 hours after it started, and its `mission-loop.sh` was changed ~45.1 hours after startup. On-disk provenance is distinct from in-memory/runtime provenance.

The current `Mac.runtime('loop')` implementation correctly rejects this state via `source_manifest`, and `prepare()` requires *both* Loop and Dashboard actual runtime checks before any mutation. Simply whitelisting the three legacy hashes, rewriting file mtimes, or ignoring the runner timestamp would fabricate a PASS. **Do not** add such a bypass.

Further repeating the current read-only source/time probes cannot establish historical Python import bytes. No further operator collection of the same probe is necessary.

## Remaining engineering task (not yet authorized or implemented)

Design a **separately reviewed, explicit legacy-runtime reconciliation / controlled cutover** path, not a silent exception to normal `prepare`.

1. Freeze exact product pin (`bda7ef0dfd89e6c1b11f9020163bf754bed5ae74`) and ops release candidate bytes; re-verify PR #39 head, current `main` merge-tree, and protected Frank policy/scanner bytes. Product changes remain forbidden.
2. Before any restart, take private read-only source/runner/plist evidence and a consistent SQLite backup. Confirm no Gmail/local/outbox in-flight work **immediately** before the controlled stop. Do not modify old notification rows or generate test signals.
3. Obtain explicit operator authorization for this *nonstandard* preexisting Loop divergence. Then hold and stop affected Loop/Dashboard writers, verify no orphan writers, take another fully consistent post-stop SQLite backup with integrity checks, and verify scanner PID/source/cursor continues independently unchanged.
4. Switch both runners only to the byte-verified, read-only, immutable release directory. No runner shall reference `~/.cache` or a mutable Git checkout. Apply only the approved additive presentation-table DDL.
5. Verify actual new loop/dashboard source and independent process identities, health, dashboard UI/API, ledger identity, and actual scanner cursor progression. Do not send a synthetic Gmail or synthetic decision; only real future transitions can be eligible.
6. Critical legacy-specific rollback caveat: the old Loop in-memory version cannot be reconstructed from the now-modified disk tree. A failure must **not automatically restart the old Loop** based solely on its currently visible runner/source. Fail stopped with private journal and explicit human review unless a separately audited, exact restorable old release has been established. Never restore a historical SQLite backup over new decisions/receipts.

Current dual-service ops implementation does **not** contain an independently validated implementation for this legacy baseline; it intentionally rejects `SOURCE_MIXED_BYTES`. The next engineering task is design, targeted failure-injection tests, a separate independent AI review, and Mac dry-run gates before seeking deployment consent.

## Status

- PR #39 is still Draft/unmerged.
- PR #41 is operations-review Draft/unmerged.
- Previous PR #35 Dashboard stays live; existing Loop/scanner untouched.
- Production trading stays `NO_GO`.
- This investigation is complete at the read-only evidence level; **deployment remains NO_GO**.
