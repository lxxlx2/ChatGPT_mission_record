# PHASE 2B Gmail canary report — 2026-09-30

**PHASE_2B_PASS**. **PRODUCTION = NO_GO**. **PHASE 3 = NO_GO pending separate review/authorization**. Stop after report/commit/push. No market collector, investment judgement/alert, automation creation/modification/enable, launchd production install, pmset change or portfolio mutation occurred.

## Run, branch, main and regression

Run ID: `phase2b-20260930-gmail-a`. Branch: `codex/crypto-monitor-design-20260930`. Working tree: `/Users/jerson/Documents/ChatGPT/crypto-monitor-design-20260930`. Starting HEAD: `75ec1c74a5aef8d8f19ed994b6899971fefc560d`. Implementation commit after final main sync: `24b0e3a0a19a1ac6e06aabff8735d3dcfc9c68f0`; report is committed separately, with final HEAD in the delivery reply/history. Original primary checkout was not changed.

Fetched origin at phase start. Main remained `dac452086f79d7677cd76e81574bc49ba1bdb341`; feature ahead 7 / behind 0. No new main commits or affected paths existed. Main was already an ancestor; no additional rebase/merge was necessary, and main was never force modified.

Final publication readback found 10 main commits had arrived during canaries, ending at `318b0328896289703454ea0718a340ec99f24d00`. All paths/diffs were inspected: airdrop run records, crypto/us-stock daily report archives, and those two daily modules' AUTOMATION_RUNTIME durable-first/recovery documentation. No crypto-300-profit-mission spec, portfolio/state or local-agent file changed. The daily rules require durable checkpoints and Sent/readback dedupe, consistent with this canary; no scheduled task setting was operated. Rebased all 9 feature commits onto the new main without conflict, then reran all 150 tests, compileall, pip check, diff and secret/public checks. No additional Gmail action was invoked. Feature publication uses an explicit lease against the already published pre-rebase `502e845c16687e04e3af88eba8d6e59f73e67830`; main is never force-pushed.

Before Phase 2B: **119 passed in 0.66s, 0 failed, 0 skipped**; compileall, pip check and git diff --check passed. Initial secret pattern scan: 44 code/document/config files, 0 hits. Final suite: **150 passed in 0.83s, 0 failed, 0 skipped** (119 unchanged original tests + 31 deterministic Phase 2B cases). Final compileall, pip check and diff check passed. New-test development initially caught an INSERT placeholder count error; this was corrected before any real provider invocation, with zero real slots consumed. Canary operations are separate explicit commands, never default pytest.

## Reverified Gmail capability and recipient

Used only the currently connected **Gmail** capability. No OAuth app registration, SMTP/App Password, browser cookie, browser Send automation or AppleScript was used. Mac stores no Gmail credential.

| Capability | Actual evidence | Result |
|---|---|---|
| Profile identity | Current connected profile read; actual existing SENT message From matched profile identity | AVAILABLE_VERIFIED |
| Search/read | Current Sent search and full message read before canaries | AVAILABLE_VERIFIED |
| Sent readback | Existing SENT label checked, then both real canaries fully read/verified | AVAILABLE_VERIFIED |
| Send action | Current action schema discovered before dispatch; two explicit connected sends returned IDs and succeeded in strict Sent readback | AVAILABLE_VERIFIED |
| Recipient | Both actions used authenticated-account self routing (`to=me`); full readback To and From hashed to the verified account identity, with no CC/BCC | **SELF_VERIFIED** |

Send availability before the first dispatch meant the current connected action was present; actual provider execution was verified by slot 1, not assumed from a previous phase. No preliminary test send was used to verify capability. Complete mailbox address is absent from this report/public changes and persisted runtime data. Recipient normalization/hash is used locally and in private receipts.

## Budget and invocation ledger

A single persistent SQLite grant binds the run and verified recipient, with authorized=3. Slots are unique, irreversible after the action invocation claim and cannot be reused by the same event. Changing the run or recipient does not reset the grant. Pre-send validation/preparation failures consume zero invocation slots; reserved intents are distinct from consumed invocations. At invocation dispatch, SQLite commits invoked_at before the connected tool is called exactly once. Never replace/delete this SQLite or open a new root to bypass the grant.

| Counter | Measured value |
|---|---:|
| real_send_slots_authorized | 3 |
| real_send_slots_used | 2 |
| real_send_slots_remaining | 1 |
| send_action_invocations | 2 |
| explicit_provider_success | 2 |
| explicit_provider_reject | 0 |
| ambiguous_provider_results | 0 |
| provider_accepted_messages | 2 |
| Sent_exact_messages | 2 |
| recovery_send_invocations | 0 |
| duplicate_messages | 0 |
| blind_resends | 0 |
| unexpected_recipient_count | 0 |

| Slot | Independent purpose | Action invoked | Provider observed | Final exact Sent count | Final state |
|---|---|---|---|---:|---|
| 1 | Scenario A normal self canary | yes, once | explicit SUCCESS; one returned identity, matched readback | 1 | DELIVERED |
| 2 | Scenario B real accepted send followed by injected local persistence failure/SIGKILL recovery | yes, once | explicit SUCCESS; one returned identity, matched restart readback | 1 | DELIVERED |
| 3 | Optional independent purpose | **no** | NOT_INVOKED | 0 | no event delivery attempted |

Third slot was unnecessary and left unused; its remaining authorization is not a request or plan to send it. No timeout/ambiguous send was retried. The two provider action calls occurred, so exactly two slots remain permanently consumed regardless of local receipt behavior.

## Real remote input chain and SEND_INTENT

Both A and B independently followed:

SQLite synthetic candidate → PRIVATE GitHub mac-data immutable batch/current → exact pinned remote readback → REMOTE_CONFIRMED → fixture consumer reads actual remote batch → ACTIONABLE_RISK decision receipt on gpt-data archive/current → Mac reads remote receipt → atomic reconciliation → DELIVERY_PENDING → fresh exact Sent precheck → transactional SEND_INTENT → connected Gmail action.

Event identities use only `phase2b:gmail:<run_id>:normal` and `phase2b:gmail:<run_id>:receipt-failure`. The optional-extra identity was queried only. There is no production event ID or investment judgement. Three planned identities had zero Sent candidates before the run; both actually used identities were queried again immediately before preparation and remained zero. Empty complete search results mean exact count zero for these fresh identities; nonempty search results always require full message verification.

SEND_INTENT stores run/event, recipient_hash, literal subject marker, delivery_policy, unique slot, created_at and DELIVERY_SENDING in SQLite before invocation. A separate invocation timestamp/result ledger survives restart. Both REAL_GMAIL_ENABLED=true and explicit --real-gmail-canary must pass; private visibility and durable pending state are rechecked immediately before dispatch. Default execution is OFF.

The subject contains the exact event marker and TEST ONLY. Body contains the requested canary/test/no-investment-action statements plus event/run/scenario/UTC time, without investment instructions or live prices. Raw message content is omitted from this public report.

## Scenario A and three replays

Slot 1 real provider call returned explicit success and a provider message ID. Actual Sent query found one candidate; full Gmail read validated SENT label, exactly equal subject, exactly one body event_id line, self To/From, no additional recipients, reasonable provider internal timestamp, required test notices and identity equal to the returned ID. Local state became DELIVERED only after validation.

Private delivery receipt archive/current were written on gpt-data, read back with canonical bytes/hash and commit provenance, and independently read through the GitHub connector. Receipt hash and complete SQLite input binding passed.

Same-event orchestration replay was entered **three times** through the existing-intent lookup/recovery path. Each replay performed a fresh real Sent search and full read. Each exact count remained 1; provider identity remained unchanged; local state remained DELIVERED; budget remained used=1. **Additional action invocations = 0**. Verified timestamp is preserved after first verification so replays do not change the immutable receipt's hash; deterministic coverage checks that property.

## Scenario B failure and real restart

Slot 2 was a separate event that completed the same actual private input/decision chain. Fresh precheck was zero. SEND_INTENT and invocation claim were committed, then the connected real Gmail action returned explicit success and a provider ID.

A durable provider-observation row recorded that actual success. The test then entered the delivery-result persistence transaction, wrote the intended immediate result update, deliberately raised **INJECTED_POST_ACCEPTANCE_PERSISTENCE_FAILURE**, and rolled back that transaction. No final DELIVERED state or delivery receipt existed at the failure point. The controlled error handler persisted DELIVERY_UNCERTAIN. Its intent result field was UNKNOWN because the update rolled back; the separate observed-result ledger remained SUCCESS. This UNKNOWN local field is not a naturally ambiguous provider response.

The delivery process then terminated by **SIGKILL, shell exit 137**, after the controlled failure and before successful reconciliation. A new process reopened SQLite: A was DELIVERED, B was DELIVERY_UNCERTAIN and used slots remained 2. No provider action was called on recovery.

Restart performed real Sent search, found one candidate, fully read it and verified SENT, exact subject/body event, self recipient/sender, timestamp and identity equal to the durable provider observation. B recovered to DELIVERED, then published/read its private receipt. **B provider messages=1; B send invocations=1; recovery send invocations=0; duplicates=0.**

The provider succeeded naturally. The persistence fault was deliberately injected after acceptance; it is not described as a real Gmail outage. There was no network disconnection, request kill, plugin alteration or deletion of the sent message.

## Final Sent counts, receipts and runtime privacy

After recovery and receipt publication, all three planned event identities were queried again. A/B full messages were reread and revalidated; optional-extra had zero complete search candidates.

| Identity purpose | Before | Final exact Sent | Full readback |
|---|---:|---:|---|
| A normal | 0 | 1 | PASS |
| B receipt failure | 0 | 1 | PASS |
| Optional third | 0 | 0 | not sent |

Receipts contain schema/run/event/decision/policy/state/slot/invocation flag/provider result class, provider_message_id_hash, sent_at, verified_at, literal marker, recipient_hash, input_batch_id, input_payload_sha256 and receipt_sha256. sent_at is the recorded invocation UTC timestamp; actual Gmail internal_date is independently checked against that window during verification. Full provider IDs are stored only in private local SQLite, not the public report or remote receipt. B receipt's provider_result_class uses the durable SUCCESS observation despite the deliberately rolled-back intent update.

Both receipt hashes passed recomputation and actual remote archive/current readback; connector reads of both immutable receipt archives exactly matched local safe canonical receipt bytes. No raw MIME, Gmail credential, complete recipient or raw Gmail body is included in remote receipts. Full readback files existed only transiently in the outside-Git private directory and were deleted by recovery.

PRIVATE repo `lxxlx2/crypto-monitor-runtime` was verified before canaries, before both invocation dispatches and after all testing. It remains PRIVATE. All writes were under `runtime-v2-test/<run_id>/`; fresh recursive tree checks show **runtime-v2 production path count=0 on mac-data and gpt-data**. Existing isolation remains LOGICAL_WRITER_ISOLATION_ONLY.

## Implementation and deterministic test coverage

`mission_agent/delivery/canary.py` provides fixed-grant budget/recipient binding, durable intent/invocation/result persistence, strict parsed-MIME readback, uncertain recovery, immutable-receipt-safe replay and persisted global stop on identity/conflicting-Sent errors. `scripts/phase2b_canary.py` provides separate opt-in remote flow, prepare/invoke, result/fault, recovery, receipt and status operations. It is a bridge to Codex's connected action, not a local Gmail credential adapter. Commands reopen SQLite; no Gmail send call exists inside ordinary Python tests or this local process.

31 new deterministic cases cover budget persistence across restart, zero consumption before provider invocation, all success/reject/timeout/ambiguous/unknown invocation consumption, exhaustion, event slot reuse prohibition, no blind uncertain resend, lookup recovery, multiple exact Sent manual review, recipient/subject/body/label/timestamp/provider-ID rejection, private visibility revalidation, post-acceptance rollback recovery, no-match uncertainty, grant replacement rejection, replay receipt stability, persistent global abort, both invocation gates, missing pending validation and recipient-grant immutability. Original 119 tests were not edited.

The first deterministic INSERT-placeholder failure was fixed before real sends. Final new tests exercise injected TIMEOUT/AMBIGUOUS/EXPLICIT_REJECT; these were not observed naturally on the two real calls.

## Evidence, public contamination and limits

Private local evidence directory: `/Users/jerson/Documents/ChatGPT/crypto-monitor-phase2b-evidence-20260930` (0700; files finalized 0600). Includes the authoritative SQLite/slot ledger, safe receipts, precheck/replay/aggregate summaries, runtime verification, JUnit and integrity manifest. No raw recipient/address/body remains in transient input files. Full provider IDs live only in SQLite as permitted. No token or credential file was created.

Public changes are limited to canary orchestration, separate explicit bridge, deterministic tests, README and this sanitized report. Complete authenticated address and both real provider IDs are checked against all added public material before commit. Final review verified exactly 5 authorized public files, 0 runtime/evidence additions, 0 authenticated-address hits, 0 real provider-ID hits and 0 edits to original 119 tests. Pattern secret scan examined 49 files with 0 hits; email-pattern and diff checks passed. No private JSON/SQLite was added. This is a pattern/literal review, not a general guarantee against every possible secret encoding.

Limitations: two successful self canaries are a bounded sample, not a production reliability guarantee; injected local rollback is not a natural Gmail failure; no natural provider timeout/reject was observed; scheduled ChatGPT deployment/access/reliability still needs shadow validation; connected action invocation and local SQLite cannot form one cross-system atomic transaction, so the durable invocation claim immediately before dispatch is conservatively irreversible on an unknown handoff; exact observed action calls and budget claims both equal 2 here. Budget protection depends on retaining the authoritative authorization SQLite, not resetting/deleting it. Search index delay yields uncertain lookup-only recovery. Timestamp window and plain-text MIME verification are deliberately strict. Logical GitHub writer guards are not hard credential ACL. No market/production/long-duration uptime evidence was obtained.

## Acceptance A–P and next gate

A main regression PASS; B private visibility PASS; C real current Gmail send PASS; D SELF_VERIFIED PASS; E normal A PASS; F three A replays with zero extra sends PASS; G real B send PASS; H post-acceptance persistence failure PASS; I actual process restart/readback recovery PASS; J B recovery sends=0 PASS; K used=2<=3 PASS; L duplicate exact events=0 PASS; M blind resend=0 PASS; N unexpected recipient=0 PASS; O both private receipts/hash/connector verification PASS; P public contamination=0 PASS (5 authorized files, no runtime/address/provider IDs).

**PHASE_2B_PASS. Third slot unused. PRODUCTION = NO_GO. PHASE 3 = NO_GO until separate approval. No further real send, collector or deployment work continues.**

Timestamp verification uses the parsed provider internal timestamp in epoch milliseconds rather than trusting displayed Date alone, consistent with the [official Gmail Message resource](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages).
