# Scheduled GPT consumer contract (Phase 2A, inactive)

Status: deployment specification only. Existing `$300 Crypto资产状态监控` remains disabled. Production remains NO_GO. Phase 2A fixture execution uses private test paths and no Gmail send.

## Repository and authority

`lxxlx2/crypto-monitor-runtime` must be PRIVATE before every read/write cycle. SQLite on Mac remains authoritative for candidates, outbox, accepted decisions, and delivery intents. GitHub is transport. A scheduled consumer must have verified private-repository read access and gpt-data write capability. Current Codex cannot manage ChatGPT scheduled automation; its activation, actual scheduled private access and write capability require separate verification.

Mac writes mac-data; consumer writes gpt-data. The current credential is shared account-level access, so isolation is **LOGICAL_WRITER_ISOLATION_ONLY**. Role-specific transports reject wrong branch/repository/path before network access. Separate identities with enforced branch rules are a future deployment requirement if hard ACL is desired. Do not claim current logical guards are credential-level denial.

All Phase 2A artifacts are `runtime-v2-test/<run_id>/...`. Future `runtime-v2/...` paths are reserved and remain unwritten. Each role has `ingest`, `health`, `decisions`, or `delivery` paths with current.json and immutable archives as appropriate. Batch archive basename preserves batch identity. Receipts use input_batch_id. No real secrets, wallet JSON, provider IDs or tokens belong in envelopes/public code.

## Future scheduled cycle

1. Read mac-data health/current.json from a pinned branch commit. Validate schema, canonical bytes/hash where applicable, generated_at, valid_until, monotonic sequence and repository visibility. Expired/missing health is UNHEALTHY_STALE_HOST; never infer healthy from absence or a previous cycle.
2. Read current pending ingest batch. Verify schema_version, batch_id, generated_at, valid_until, item_count, exact unique item set, per-item hashes, canonical payload_sha256 and actual byte limit. Pin the read to a commit and keep branch/path/blob/commit provenance. Reject truncation, oversize or stale current; do not judge a partial batch.
3. Check gpt-data decision archive for the input_batch_id before judging. A matching complete receipt is an idempotent recovery result; do not request another judgement after Mac restart. Different contents for the same identity is HASH_CONFLICT.
4. Judge only the supplied normalized candidates according to Mission/token/meme rules. Phase 2A uses deterministic fixture labels; these do not validate real GPT decision quality. A future consumer emits IGNORE, WATCH, ACTIONABLE_RISK or ACTIONABLE_OPPORTUNITY with structured reason and exact item hash for every item.
5. Publish a complete decision receipt to gpt-data decisions/archive/<batch_id>.json, then current.json with explicit previous blob SHA. Receipt fields: schema_version, input_batch_id, input_payload_sha256, consumed_item_count, decision_count, consumer_version, decision_timestamp, decisions[event_id,item_payload_sha256,decision,reason]. Decision timestamp must be within input lifetime. Verify every item's identity/count/hash before writing. Immutable same bytes succeeds without a new commit; differing bytes fails. On 409 or timeout reread, accept exact bytes only, otherwise surface conflict or preserve pending work. No blind overwrite.
6. Read back exact canonical receipt bytes and record branch/path/blob/commit. Only then report transport success. Mac reconciliation validates the whole receipt atomically against its stored batch. A late read of a decision made within the batch lifetime is allowed unless Mac has explicitly expired that batch.
7. ACTION enters delivery phase. During Phase 2A delivery is DRY_RUN/MOCK/NOT_SENT only, no Gmail API send. IGNORE/WATCH are silent. Future PHASE 2B requires explicit real-canary authorization and provider verification before enabling delivery.
8. Stop the cycle without crawling or replaying source history. Errors preserve queued candidates and expose degraded/unknown state; never fabricate a successful receipt or healthy signal.

No full Binance scan, bulk Solana transaction fetch, full-network NFT crawl, historical replay, collector startup, launchd install or automation activation is part of this consumer.

## Integrity and byte budget

Canonical JSON: NFC UTF-8, sorted keys, no insignificant whitespace, no floating point values, no duplicate keys. payload_sha256 is SHA-256 of canonical envelope excluding payload_sha256. Individual candidate payload hashes are separately validated. Maximum 40 normal plus 8 urgent items, each <=2000 bytes. Production byte ceiling must be based on measured connector reads with a 20–30 percent margin; integration report records the selected value. Never bypass the limit by string truncation. Split complete items into another persisted batch.

Consumers must receive full raw bytes through the connector or an equivalent verified reader and perform programmatic count/hash checks before GPT judgement. Successful tool status or rendered excerpts are insufficient. Scheduled GPT must demonstrate these checks on its own actual execution path before production activation; Phase 2A connector testing alone does not prove scheduled deployment readiness.

## Gmail exact lookup design, read-only in Phase 2A

The future marker is `[MISSION:<event_id>]`. Gmail search is only a candidate discovery operation, not exact proof: search subject marker / in:sent, retrieve complete matching messages, require SENT label and exact literal marker in subject/body, and match the locally persisted event intent. Zero matches after an ambiguous send means DELIVERY_UNCERTAIN and cooldown; never blind resend. One verified exact match can reconcile delivery. Multiple distinct matching messages require manual review. Search tokenization, stale indexing and timeout must not be treated as proof of absence. Phase 2A performs no real send; an optional existing Sent lookup does not establish send capability. Current unit/provider fixtures cover this design; actual real-provider send and readback remain PHASE 2B gates.

## Write volume

Candidate-driven batching coalesces events into complete bounded envelopes; no tick commits. Health publishes every 10–15 minutes or on material state change (96–144 baseline commits/day), with CAS and unchanged-content suppression. Decision and delivery publications are event-driven. Typical batch cycle: two ingest writes, two decision writes, and at most two dry-run delivery writes; readbacks do not create commits. Rate limit responses defer pending work, bounded backoff never silently loses events. Report measured API calls/bytes separately from a daily volume estimate.
