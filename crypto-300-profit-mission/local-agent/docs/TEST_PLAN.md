# Crypto Opportunity Monitor — Test plan

Design-only catalogue, 2026-09-30. All cases below are NOT_RUN in this round. PHASE 0 capability point probes are separate evidence and cannot be counted as these test passes. No automated suite is implemented or installed here.

## Execution rules

Future pytest suite uses pinned private/synthetic fixtures and deterministic fake clocks, independent expected results rather than reusing production calculations as assertions. Each run records release SHA, dependency versions, fixture manifest hashes, seed, TEST_ID status PASS/FAIL/BLOCKED/NOT_RUN and actual logs. Blocked/skipped mandatory case does not count as PASS. Real system/provider cases require the explicit preconditions shown. No primary DB corruption, production mailbox ambiguity experiment, public runtime write or new automation. Test outputs stored privately; public summary contains sanitized aggregates only.

Synthetic E2E manifest: 50 unique planned records (10 IGNORE,10 WATCH,10 ACTIONABLE_RISK,10 ACTIONABLE_OPPORTUNITY,10 invalid/stale/mismatch items with explicit dispositions), plus at least3 repeat observations per selected id; randomized ordering from fixed seed, burst/backlog. GPT-labelled outcomes belong to decision fixtures, never local collector-generated investment conclusions. Precompute expected unique-id/disposition/count sets independently. Corrupt inputs quarantined with accountable identity; silent loss denominator includes quarantine/stale and queued items, not only successful deliveries.

Every case uses the following explicit fields; failure_evidence and cleanup are mandatory even on unexpected failure. Failed inputs must remain in a private diagnostic bundle long enough for investigation.

## U-01

- TEST_ID: U-01
- module: price
- purpose: Return and rolling windows
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: 1,445 completed 1m bars with hand-computed closes and gaps
- steps: Compute 5m/15m/1h/4h/24h returns, high/low, RV, reversal, BTC-relative values; compare independent decimal reference
- expected_result: Exact reference values; missing aligned samples unavailable; no future/provisional bar used
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private U-01 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## U-02

- TEST_ID: U-02
- module: price
- purpose: All nine threshold boundaries
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Each rule just below/equal/above threshold; breakout two samples; RV median=0 fixture
- steps: Evaluate frozen manifest; test equality, one/two samples and zero denominator
- expected_result: Equality hits specified inclusive rules; one breakout sample cannot fire; invalid denominator explicit unavailable
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private U-02 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## U-03

- TEST_ID: U-03
- module: identity
- purpose: Deterministic identity/dedup
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Repeated price/Frank/Monster/NFT observation with reordered fields
- steps: Generate ids three times; insert/replay; conflicting payload hash
- expected_result: Same event id and one candidate; conflicting bytes quarantined
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private U-03 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## U-04

- TEST_ID: U-04
- module: hash
- purpose: Cross-implementation payload/batch hash
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: NFC text, decimal strings, shuffled keys, metadata tamper, duplicate keys, NaN
- steps: Canonicalize independently, hash, alter count/TTL/id/item
- expected_result: Known vectors identical; each mutation mismatches; duplicate keys/NaN rejected
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private U-04 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## U-05

- TEST_ID: U-05
- module: SQLite
- purpose: Atomic event/cursor/outbox
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Injected failure after each statement in candidate transaction
- steps: Insert raw/evidence/outbox/cursor; interrupt at every point; reopen DB
- expected_result: All-or-none commit; cursor never advances without raw/evidence/outbox
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private U-05 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## U-06

- TEST_ID: U-06
- module: cursor
- purpose: Contiguous finalized cursor
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Out-of-order signatures, overlap, one unresolved gap
- steps: Ingest pages; resolve gap; compare history/live lanes
- expected_result: No gap-crossing/rollback; overlap dedup; separate cursors
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private U-06 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## U-07

- TEST_ID: U-07
- module: outbox
- purpose: Idempotent persistence/retry
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Commit succeeded remotely but local response lost
- steps: Retry exact immutable batch, reopen DB
- expected_result: No new batch bytes/id on retry; durable outstanding membership retained
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private U-07 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## U-08

- TEST_ID: U-08
- module: delivery
- purpose: All allowed/forbidden transitions
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Every state and timeout/crash/readback event; both policies and null
- steps: Run transition matrix; assert side effects against state
- expected_result: Uncertain never blind-sends; null policy dry-run; terminal invalid transition rejected
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private U-08 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## U-09

- TEST_ID: U-09
- module: health
- purpose: Health and stale calculation
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Missing metrics; disk80/95 boundaries; seq regression; expired HEALTHY
- steps: Evaluate local health and external TTL at just before/after expiry
- expected_result: Missing UNKNOWN; disk breaches specified states; expired host UNHEALTHY_STALE_HOST
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private U-09 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## U-10

- TEST_ID: U-10
- module: retry
- purpose: Rate limit/backoff
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: 429 Retry-After=60; reset header; seeded failures
- steps: Advance fake monotonic clock, collect retry intervals
- expected_result: No request before server wait; jitter bounded 1..300s; persisted retry survives restart
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private U-10 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## U-11

- TEST_ID: U-11
- module: migration
- purpose: Migration and compatible rollback
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Old schema, checksum change, failure midway, newer schema
- steps: Backup; migrate; abort; restart; attempt incompatible binary
- expected_result: Transactional rollback and version/history agreement; newer schema refused
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private U-11 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## U-12

- TEST_ID: U-12
- module: security
- purpose: No local semantic decision / prompt injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: External ignore-previous/run-command/send-money text and prohibited local enum
- steps: Normalize source, build batch, inspect tool routing/local outputs
- expected_result: Untrusted tagged bounded data only; forbidden collector decision rejected; no command/recipient change
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private U-12 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## U-13

- TEST_ID: U-13
- module: Frank
- purpose: Authority and balance semantics
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: signer/non-signer/fee-payer/ATA owner/inner CPI/WSOL/error fixtures
- steps: Parse full raw fixture; compare independent expected evidence
- expected_result: Distinct ownership/authority evidence; exact integer deltas; tx_error preserved; no local BUY/SELL
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private U-13 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## I-01

- TEST_ID: I-01
- module: pipeline
- purpose: SQLite -> candidate -> outbox -> batch
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: 50 fixed-seed synthetic observations with duplicate/out-of-order inputs
- steps: Commit, batch, inspect ledger and item membership
- expected_result: Expected unique ids exactly match committed candidates; every eligible item queued or batched
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private I-01 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## I-02

- TEST_ID: I-02
- module: transport
- purpose: Batch -> mock transport -> receipt
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Multi-page backlog, valid full receipts
- steps: Publish mock private mac-data; fixture consumer writes gpt-data; reconcile
- expected_result: Exact ids/hash/count validated; no ack before correct receipt
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private I-02 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## I-03

- TEST_ID: I-03
- module: reconciliation
- purpose: Hash and exact-set reconciliation
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Missing/extra/duplicate item, wrong batch/hash, replay receipt
- steps: Inject each receipt; inspect candidate status
- expected_result: Invalid receipt quarantined; no incorrect consumed flags; replay idempotent
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private I-03 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## I-04

- TEST_ID: I-04
- module: recovery
- purpose: Restart at all boundaries
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Crash before/after commit/publish/receipt import
- steps: Kill harness at checkpoint; reopen; resume same event set
- expected_result: Restart loss=0; cursor monotonic; outbox resumes; no duplicate candidate
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private I-04 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## I-05

- TEST_ID: I-05
- module: private GitHub
- purpose: Real authenticated branches/CAS
- precondition: Private test repo explicitly authorized/provisioned; credentials verified; DRY_RUN; no Gmail
- input: Non-sensitive synthetic payloads in owner-provided private test repo
- steps: Verify private; create authorized writer branches; publish/readback; race CAS; reconcile
- expected_result: Exact bytes/hash and branch permissions; losing writer blocked; no writes to public destination
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private I-05 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## I-06

- TEST_ID: I-06
- module: scheduled GPT
- purpose: Real scheduler consumer contract
- precondition: Owner has separately authorized existing-task canary changes; scheduler access and private repo verified; no new task
- input: 40 normal + urgent + backlog across immutable pages
- steps: Authorized existing consumer canary reads bounded input; validate decisions and lease CAS
- expected_result: No truncation; receipt ids/count/hash exact; conditional-write concurrency works
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private I-06 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## I-07

- TEST_ID: I-07
- module: Gmail mock
- purpose: Intent/send/readback protocol
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: IGNORE/WATCH/ACTION fixtures
- steps: Consume fixtures, acquire lease, Sent search, mock send/readback, persist receipt
- expected_result: IGNORE/WATCH zero sends; ACTION obeys state machine and exact token
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private I-07 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## G-01

- TEST_ID: G-01
- module: Gmail reliability mock
- purpose: Send success/readback
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: ACTION, provider success
- steps: Search empty; persist intent; send returns id; persist/readback
- expected_result: One send; persisted id before delivered; DELIVERED only after verified SENT readback
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private G-01 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## G-02

- TEST_ID: G-02
- module: Gmail reliability mock
- purpose: Receipt persistence failure
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Provider success; post-send write fails
- steps: Crash after send; reopen consumer; reconcile Sent
- expected_result: Uncertain intent survives; Sent positive -> delivered; no resend
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private G-02 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## G-03

- TEST_ID: G-03
- module: Gmail reliability mock
- purpose: Delayed Sent visibility
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Provider success; immediate lookup empty
- steps: Return empty search for three polls; then positive
- expected_result: Uncertain until verified; cooldown honored; exactly one mock send
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private G-03 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## G-04

- TEST_ID: G-04
- module: Gmail reliability mock
- purpose: Unknown send timeout
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Provider request timeout, possible acceptance
- steps: Timeout; restart; return ambiguous/negative/positive Sent
- expected_result: DELIVERY_UNCERTAIN; no blind resend; positive resolves; null policy cannot retry
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private G-04 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## G-05

- TEST_ID: G-05
- module: Gmail reliability mock
- purpose: Same event replay
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: One delivered id replayed >=3
- steps: Replay with original and new batch ids
- expected_result: Candidate=1 and send count=1; prior decision/receipt reused consistently
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private G-05 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## G-06

- TEST_ID: G-06
- module: Gmail reliability mock
- purpose: Concurrent consumers
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Two consumers same ACTION
- steps: Barrier race CAS lease; loser retries; inspect provider calls
- expected_result: Only lease winner sends; stale fences rejected; sending lease expiry uncertain
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private G-06 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## G-07

- TEST_ID: G-07
- module: Gmail reliability mock
- purpose: Crash before send
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Crash after persisted intent before call
- steps: Reopen with provider negative search
- expected_result: Intent uncertain, no blind send; explicit policy/manual disposition required
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private G-07 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## G-08

- TEST_ID: G-08
- module: Gmail reliability mock
- purpose: Crash after send
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Crash after provider acceptance before id receipt
- steps: Restart and delay search visibility
- expected_result: Durable sending intent converted uncertain; final positive readback resolves once
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private G-08 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## G-09

- TEST_ID: G-09
- module: Gmail reliability mock
- purpose: Cold uncertain restart
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Stored uncertain state, expired lease
- steps: New process boot; reconcile Sent only
- expected_result: No provider send during uncertainty; prior fence/attempt retained
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private G-09 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## G-10

- TEST_ID: G-10
- module: Gmail reliability mock
- purpose: Readback failure
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Provider id success, read API unavailable
- steps: Fail readback then restore
- expected_result: Never mark DELIVERED early; uncertain resolves after verified readback
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private G-10 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-01

- TEST_ID: F-01
- module: network
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: 5min outage
- steps: Disable fixture networking; recover; drain
- expected_result: No committed loss; source degraded; catch-up resumes
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-01 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-02

- TEST_ID: F-02
- module: Solana 429
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Retry-After then success
- steps: Inject throttling at gap
- expected_result: Official-only requests; wait respected; cursor stable until success
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-02 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-03

- TEST_ID: F-03
- module: Solana null
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Old target null response
- steps: Persist unavailable; evaluate archival gate
- expected_result: UNAVAILABLE_ON_PUBLIC_RPC; oldest required -> FULL_HISTORY_NOT_FEASIBLE_WITH_PUBLIC_RPC_ONLY
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-03 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-04

- TEST_ID: F-04
- module: Solana timeout
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Timeout then success
- steps: Interrupt fetch, restart, repeat
- expected_result: No assumed null/passive; cursor preserved; bounded retry
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-04 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-05

- TEST_ID: F-05
- module: Binance disconnect
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Midbar close and reconnect
- steps: Inject close; resubscribe; backfill; overlap
- expected_result: Gap explicit; no duplicate final bars/events; provisional cannot fire
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-05 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-06

- TEST_ID: F-06
- module: Hyperliquid disconnect
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Subscription ack but no data then disconnect
- steps: Timeout freshness; reconnect/snapshot
- expected_result: Ack not data success; HYPE unknown/stale until fresh data
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-06 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-07

- TEST_ID: F-07
- module: GitHub409
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Two attempted expected-SHA updates
- steps: Race conflicting writes
- expected_result: No overwrite/force push; refetch/CAS exact hash recovery
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-07 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-08

- TEST_ID: F-08
- module: GitHub rate limit
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: 403 secondary/429/reset
- steps: Inject headers; restart timer
- expected_result: Backoff honors provider; queue retained
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-08 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-09

- TEST_ID: F-09
- module: GitHub unavailable
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: 503 for two consumer cycles
- steps: Continue local commits, recover transport
- expected_result: No silent loss; health/backlog reflects delay; pending pages recover
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-09 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-10

- TEST_ID: F-10
- module: SQLite lock
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Other process writer lock >busy timeout
- steps: Hold lock, release, retry
- expected_result: Bounded wait; no partial cursor/event commit
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-10 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-11

- TEST_ID: F-11
- module: SQLite corruption
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Corrupted COPY of DB only
- steps: Run integrity check and backup restore in sandbox
- expected_result: Refuse corrupt writes; restored checks match backup; post-backup recovery documented
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-11 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-12

- TEST_ID: F-12
- module: disk full
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Quota-limited temporary filesystem
- steps: Fail raw/DB write; restore space
- expected_result: No false archive/cursor success; UNHEALTHY_DISK; unresolved retained
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-12 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-13

- TEST_ID: F-13
- module: process kill
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: SIGKILL each mission process in isolated harness
- steps: Kill at persistence boundaries; supervised restart
- expected_result: Committed loss=0; restart counts and gaps honest
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-13 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-14

- TEST_ID: F-14
- module: sleep gap
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Advance wall clock while tasks suspended
- steps: Resume fixture host then real sleep test later
- expected_result: External stale TTL; sleep gap recorded; sources backfilled/unknown
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-14 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-15

- TEST_ID: F-15
- module: stale health
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Last HEALTHY expired
- steps: Advance external clock past valid_until
- expected_result: UNHEALTHY_STALE_HOST even if status string HEALTHY
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-15 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-16

- TEST_ID: F-16
- module: corrupt JSON
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Truncated batch/receipt JSON
- steps: Import malformed bytes
- expected_result: Quarantine diagnostic; no consume/delivery
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-16 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-17

- TEST_ID: F-17
- module: hash mismatch
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: One-byte payload/metadata change
- steps: Read and validate tamper
- expected_result: No ack; exact mismatch logged
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-17 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-18

- TEST_ID: F-18
- module: duplicate candidate
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: >=3 repeated observations
- steps: Concurrent insert + restart
- expected_result: PK ensures one candidate; conflict hash quarantined
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-18 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-19

- TEST_ID: F-19
- module: duplicate consumer
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Two consumers, lease expires after send intent
- steps: Race and resume loser
- expected_result: No auto lease steal/resend; uncertain persisted
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-19 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-20

- TEST_ID: F-20
- module: missed cycle
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: One missing scheduled run
- steps: Keep batches; next successful cycle consumes
- expected_result: Recovery100%; no silently dropped/stale events
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-20 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-21

- TEST_ID: F-21
- module: clock jump
- purpose: Failure injection
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: UTC clock ±10min and unavailable offset
- steps: Advance fake wall clock independent of monotonic
- expected_result: Latency monotonic; time-dependent rules quarantined; offset unknown not zero
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-21 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## F-22

- TEST_ID: F-22
- module: reboot/login
- purpose: Reboot/FileVault and launch-mode recovery
- precondition: Later explicit system-test authorization; backup; selected launch mode; synthetic-only; no production mails
- input: Authorized controlled Mac reboot with queued synthetic events
- steps: Record mode; reboot; check prelogin/postlogin execution; restore credentials; drain
- expected_result: Observed behavior matches selected owner requirement; any login dependence explicit; committed loss=0
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-22 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Restore approved test-only launch labels and prior power/test settings; verify original services unaffected; retain private reboot/sleep logs; user production state untouched.

## F-23

- TEST_ID: F-23
- module: launchd
- purpose: Supervisor restart
- precondition: Later explicit install/test authorization; isolated labels/config
- input: Each installed test plist process killed
- steps: Kill only test process; observe restart/throttle/circuit breaker
- expected_result: Verified automatic test restart and bounded loops; no unrelated process changed
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-23 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Restore approved test-only launch labels and prior power/test settings; verify original services unaffected; retain private reboot/sleep logs; user production state untouched.

## F-24

- TEST_ID: F-24
- module: closed lid/power
- purpose: Sleep/wake and power behavior
- precondition: Later explicit physical test authorization; user present; backups; no destructive power removal
- input: AC/battery/closed lid/hibernate controlled scenarios
- steps: Capture source/health before sleep; resume; external TTL review
- expected_result: No awake-through-lid claim without evidence; gap and queue preserved
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private F-24 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Restore approved test-only launch labels and prior power/test settings; verify original services unaffected; retain private reboot/sleep logs; user production state untouched.

## L-01

- TEST_ID: L-01
- module: load
- purpose: 40 normal + urgent + backlog
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: 40 normal, 8 urgent, 80 old backlog; each <=2,000 bytes
- steps: Run repeated consumer cycles; count bytes/pages/oldest ids
- expected_result: Each batch<=100,000 bytes; <=40 normal; urgent bound; oldest fairness; zero loss
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private L-01 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## L-02

- TEST_ID: L-02
- module: load
- purpose: Over-limit pagination
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Exactly100,000 and100,001 byte envelopes; oversized item
- steps: Serialize, publish, consume pages
- expected_result: Over-limit never published; backlog retained; oversized item explicit quarantine/split
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private L-02 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## L-03

- TEST_ID: L-03
- module: load
- purpose: Duplicates and out-of-order
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: 1,000 repeated/out-of-order observations
- steps: Load concurrently, compare expected unique ids
- expected_result: No duplicate candidate; ordered features/cursor correct; bounded memory
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private L-03 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## L-04

- TEST_ID: L-04
- module: load
- purpose: Consumer slower than producer
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Arrival <=capacity burst then sustained >capacity
- steps: Advance six hourly cycles, throttle consumer
- expected_result: Burst drains with expected fairness; growth>2 cycles marks unhealthy; overload NO_GO without capacity fix
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private L-04 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## E-01

- TEST_ID: E-01
- module: synthetic E2E
- purpose: Full local risk-first path
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: 50 unique synthetic events +>=3 duplicate replays, out-of-order, corrupt/stale/hash-mismatch/backlog
- steps: fake -> SQLite -> candidate -> outbox -> bounded mock transport -> GPT-compatible fixture -> delivery -> Gmail mock -> receipt; crash/restart and reconcile
- expected_result: silent event loss=0; duplicate candidate=0; receipt mismatch accepted=0; restart loss=0; all quarantines/stale dispositions enumerated
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private E-01 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## P-01

- TEST_ID: P-01
- module: price replay
- purpose: Frozen 30d gate all five assets
- precondition: History verified; HYPE gate blocked until forward accumulation or approved data; no fallback bars
- input: >=30d completed 1m +warm-up per asset, frozen formula/rule manifest
- steps: Validate input coverage; replay shared live module; independent evaluation labels
- expected_result: Per-asset trigger totals/day median,p95,max/rule counts/overlap/noise/objective misses; full coverage; no hindsight tuning
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private P-01 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## P-02

- TEST_ID: P-02
- module: price live
- purpose: >=24h WebSocket and live/replay parity
- precondition: PHASE3 source dependencies ready; read-only live capture; private runtime only
- input: Recorded 24h+ source events plus forced connection replacement
- steps: Capture/replay same bars; exercise heartbeat/resubscription/overlap
- expected_result: Canonical feature/candidate hashes identical; gap accounted; documented 24h reconnect continuity
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private P-02 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## FR-01

- TEST_ID: FR-01
- module: Frank archive
- purpose: Four rank availability gate
- precondition: PHASE4 design approved; manifest verified; no500/history task yet
- input: Frozen exact target manifest; newest/25%age/median/oldest
- steps: Fetch each official RPC finalized version1; classify response and bounded retry
- expected_result: All FETCHED -> archival PASS; oldest null -> NOT_FEASIBLE; timeout unresolved -> blocked NOT_PASS
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private FR-01 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## FR-02

- TEST_ID: FR-02
- module: Frank500
- purpose: Consecutive500 complete accounting
- precondition: FR-01 PASS; independent explorer accessible; no live-cursor changes
- input: 500 contiguous frozen target signatures
- steps: Fetch raw gzip/evidence; consistency/cursor; seeded sample>=50 against independent explorer
- expected_result: requested=500; each FETCHED/unavailable; fetched persistence/evidence100%; gap0; consistency PASS; manual>=50 all match; missing input blocks full-history gate
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private FR-02 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## FR-03

- TEST_ID: FR-03
- module: Frank7106
- purpose: Full history isolation
- precondition: FR-01 and FR-02 PASS first; no per-token real mails
- input: Entire7,106 manifest with frozen window
- steps: Backfill independent lane; enumerate all outcomes; compare manifest coverage
- expected_result: No silent gaps/no live queue starvation; missing required history NOT_FEASIBLE; complete aggregate report
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private FR-03 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## M-01

- TEST_ID: M-01
- module: Monster retention
- purpose: Actual source availability
- precondition: PHASE7; current official docs read; no fabricated historical metrics
- input: OI/funding/taker/top-trader endpoints, active and delisted inventory
- steps: Probe date bounds and samples; record availability
- expected_result: available_since/retention_days/delisted_supported backed by real responses; gaps explicit
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private M-01 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## M-02

- TEST_ID: M-02
- module: Monster gates
- purpose: D1/D2/D3 and starvation
- precondition: M-01 complete; D3 minimum forward sample/window reviewed before evaluation
- input: Frozen price/volume replay, deferred queue, forward derivatives
- steps: Evaluate recall with delisted denominator; preserve forward data; later full model
- expected_result: Separate D1/D2/D3 verdicts; no retroactive setup; oldest deferred processed; unavailable features do not pass D3
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private M-02 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## N-01

- TEST_ID: N-01
- module: NFT
- purpose: Deterministic source changes and gaps
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Page/mint/price/supply changes, timeout, duplicate, injection text
- steps: Run required/best-effort/discovery fixtures; inspect health/candidates
- expected_result: Required events100% queued; source gaps explicit; optional outages do not fail hard gate; no local value conclusion
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private N-01 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## B-01

- TEST_ID: B-01
- module: benchmark
- purpose: Measured resource envelope
- precondition: Implementation exists; hardware/runtime versions captured; private evidence storage
- input: >=60min synthetic normal/stress and later actual collectors
- steps: Sample aggregate CPU/RSS every10s, network/DB/WAL/raw/backup/events/writes; report p95 and average
- expected_result: Actual normal avg CPU<10%, RSS<500MB; measured budget thresholds; no shell snapshot substituted
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private B-01 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## B-02

- TEST_ID: B-02
- module: backup
- purpose: Backup restore/retention integrity
- precondition: Isolated temporary DB; fake UTC/monotonic clock; fixed seed; no real send; pinned test dependencies installed
- input: Committed DB+WAL+gzip archive and pending events
- steps: Online backup; restore isolated copy; run retention with pinned/unacked events
- expected_result: integrity_check PASS; restored hashes/cursors/counts match; unresolved/pinned data retained
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private B-02 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## S-01

- TEST_ID: S-01
- module: shadow
- purpose: 48h real scheduled stack
- precondition: Owner-authorized existing consumer shadow; private transport proven; real Gmail off
- input: 40 normal+urgent+backlog stress plus ordinary sources
- steps: Inventory expected hourly cycles, validate receipts, force missed cycle, measure pending age and recovery
- expected_result: >=48h; scheduled success>=95%; silent loss0; missed recovery100%; oldest<=2cycles normal; bytes<=100KB; no truncation; no growth>2cycles
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private S-01 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Stop isolated harness/clients; remove temporary DB and synthetic fixtures after retaining redacted evidence; restore fake clock/network hooks; leave user portfolio, legacy histories and automation unchanged.

## C-01

- TEST_ID: C-01
- module: Gmail real canary
- purpose: Provider-backed final delivery gate
- precondition: Explicit user canary authorization, verified send capability, selected test policy, private ledger/CAS; synthetic mail only
- input: 3 distinct synthetic ACTION ids; one replay>=3; receipt fail/ambiguous send/Sent delay
- steps: Authorized canary sends; verify actual Sent counts/readback; inject local failure safely; reconcile
- expected_result: 3 complete successes; repeated id actual count1; uncertain never blind resend; failure scenarios traced
- pass_condition: All stated expected_result assertions proven by recorded outputs; zero unaccounted ids/unsafe side effects; no mandatory assertion skipped.
- failure_evidence: Private C-01 log, input manifest/hash, actual-vs-expected assertions, DB/queue/cursor/state snapshots, transport hashes and mock/provider-call count as applicable; public report redacts payloads, credentials and provider ids.
- cleanup: Release test leases, disable canary-send mode, preserve private provider receipts; do not delete real Sent evidence or change automation without authorization.
