# Frank F02-R1 P2 real HTTP fix: later partial attempt with lower slot

Date: 2026-10-14 Asia/Bangkok
Status: `NEW_CHILD_FIX_BRANCH / CI_IN_PROGRESS / INDEPENDENT_NEW_SHA_REVIEW_PENDING / NO_MERGE / NO_DEPLOY`

## Fixed reviewer finding

External GPT-6.1 Sol reported `REQUEST_CHANGES` on immutable [PR #62](https://github.com/lxxlx2/ChatGPT_mission_record/pull/62) SHA `c24119989b7e752ee925e38c777ceb376ac97f81`:

- P2 F02-01: a valid newer `PARTIAL_SOURCE` with residual Solana slot **lower** than the prior complete wire-verified capture could be ignored by historical slot-first selector, letting F02 return old positive raw balance as `FRESH_VERIFIED_ARCHIVED_OBSERVATION`. Independently reproduced by reviewer using an actual localhost HTTP request, earlier slots 5001/5002, later partial slot 5000, raw `123000000`. Existing repository CI did not cover this. Higher residual slot partial already masked.
- P3 F02-02: SQLite query `sqlite3.Error` escaped the HTTP error boundary, closing the connection instead of providing fixed 503 `RESEARCH_SOURCE_UNAVAILABLE`. Adjacent cheap repair; not a reason to refactor modules or add migrations.
- Existing external reports preserve parent A05-R1/R2 code APPROVE and user Mac archived actual frozen 32 technical reconciliation. F02 #62 original code remains `REQUEST_CHANGES`; do not reinterpret green prior CI as P2 closure.

## Minimal repair scope

Implement **only F02 child API** attempt-based availability gate, without altering shared history selector or production dashboard/server:

- Leave `latest_inventory` alone: its preference for max on-chain Slot is needed for historical evidence/backfill selection and existing tests.
- After the existing selector has cryptographically checked all Sidecar document hashes and parsed timestamps, scan immutable `ACCOUNT_CAPTURE` rows read-only to find any more-recent **actual attempt timestamp** than selected chain-slot observation (future captures excluded).
- If the latest later attempt is `PARTIAL_SOURCE`, including a lower residual Slot, fail closed: `LATEST_CAPTURE_ATTEMPT_FAILED` and 32 `SOURCE_UNAVAILABLE` rows with `observed_raw_amount=null`, `observed_quantity=null`, no target Token Account leakage. If a more-recent complete source is not pinned by the startup original-wire SHA, `LATEST_SOURCE_NOT_WIRE_VERIFIED` and no old quantity. Old partial or historical evidence backfill with older timestamp does not poison a more recent verified observation.
- Surface **separate** latest-attempt status/UTC/slot/source-SHA/missing Program IDs, distinct from the selected historical chain Slot/SHA, without ever claiming sale/profit.
- Catch `sqlite3.Error` at the existing HTTP and CLI safe error boundaries; report fixed 503 body and no private paths. No schema change, migration or production write.

## Verification and gates

New tests exercise **actual local HTTP** for later low-slot and high-slot partial, older partial, archived older-slot import, later complete unverified lower-slot attempt and broken read-only SQLite schema/HTTP 503. Test-only immutable snapshots use correct `wallet_inventory_snapshot._fingerprint`; no external RPC/Mac files uploaded to CI.

Run module targeted/full GitHub CI and disposable F01/C02/A05/F02 combined targeted/full for **final child SHA**; then require independent other-AI re-review of original P2/P3 reproductions with actual sockets. CI green does not imply Mac operational validation. This repair must not block F02-R2 browser design with unrelated hypothetical edge work.

Existing research Sidecar import from user's private bundle remains manual and not yet authorized/completed. No new RPC; no prod Mac service, Frank V1, production SQLite, Gmail, LaunchAgent, automation or trades touched.

`NO_MERGE / NO_DEPLOY / NO_TRADES / NO_GMAIL / NO_PRODUCTION_SQLITE_WRITE / NO_NEW_AUTOMATION`
