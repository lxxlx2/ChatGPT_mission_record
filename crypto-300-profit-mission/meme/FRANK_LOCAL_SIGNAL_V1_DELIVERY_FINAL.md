# FRANK_LOCAL_SIGNAL_V1 delivery final — 2026-10-04

FRANK_LOCAL_SIGNAL_V1_LIVE. MULTIPLE_GMAIL=CREDENTIAL_BLOCKED. GPT_SIGNAL_AUTHORITY=REMOVED.

Acceptance snapshot: 2026-10-04T04:38:24.873207+07:00 (Asia/Bangkok). No threshold, amount gate, mapping, persistence, distribution/HFT/stale predicate or signal state machine was changed. Frozen policy SHA256 remains `83ebab1fbb8ec7e03950626137c5597a38b81b8a4085d9150610018cc78cedab`. Policy, scanner, evaluator, engine, registry-independent ledger and service source remain byte-identical to the prior accepted baseline; seven protected implementation/config files were checked. Existing signal bodies/hashes/IDs survived migration and restart unchanged.

## Scanner

| Field | Verified value |
|---|---|
| FRANK LIVE | YES |
| PID | 37615 |
| Last successful poll | 2026-10-04T04:38:23.238291+07:00 |
| Last processed signature | `5LkrGm6A3sHnDUz4V5BruLQYr8avKQGeXv8MBEmzBmQxFmdJmKjTadMttdAb2uHukx9ExrjPL6DVA44bDNEVkHJH` |
| Last processed slot | 453056621 |
| Chain/local gap | 0 |
| Restart count | 1 |
| Exactly one scanner/delivery authority | YES |
| Pending raw / model | 0 / 0 |
| Consecutive errors / source drift | 0 / false |

Scanner ran throughout development. A single controlled restart of the existing LaunchAgent loaded the delivery module: old PID 12188 stopped at 2026-10-04 04:36:19.268 Asia/Bangkok; PID 37615 started at 04:36:19.750. Cursor/SQLite/health/LaunchAgent snapshots were preserved. Restart-window catch-up=0; first cycle passed without gap. No new LaunchAgent or scheduled task was created. Gmail networking runs in an independent thread with a separate SQLite connection and delivery lock; it cannot block the scanner thread or local notifier.

## Gmail capability audit

| Capability before implementation | Result |
|---|---|
| Existing reusable local real sender | NO |
| Existing local credential usable by daemon | NO |
| Credential source | NONE (no proven Gmail authorized-user OAuth with send + Sent read access) |
| Existing local Sent readback | NO |
| Interactive Gmail connector | YES; profile and Sent search returned successfully |

Audited current/legacy mission runtimes, Crypto Daily/us-stock runtime code, OAuth/Google credential/token/.env candidates under Documents/Projects/config/local stores, process and launchd environment key names, Keychain metadata and installed Gmail helpers. Keychain had one Google service metadata match, but no proven usable Gmail OAuth source. Prior local Gmail implementations were mocks, content/outbox code, or externally driven connected-capability canaries. No local Gmail CLI/helper was found. No software installed, OAuth consent performed, scopes expanded, or credential system created; no secrets printed or committed. Connector access does not expose an authorized credential to the autonomous local daemon and is not reported as local Gmail LIVE.

New sender and Sent-readback implementation exist and pass isolated provider tests. Only an existing authorized-user OAuth file is supported; its refresh is in memory and does not rewrite the credential file. Google scope proof must permit sending and reading Sent.

## Gmail result and content

MULTIPLE Gmail = **CREDENTIAL_BLOCKED**. Exact blocker: no audited, authorized local OAuth source usable by the daemon for Gmail send plus Sent readback. No real TEST Gmail was sent, and no real Gmail message ID/readback PASS is claimed. Real live signals were not fabricated for delivery testing.

MULTIPLE alone creates a Gmail identity; ACCUMULATION stays local only. Standalone subject is `[Frank 多倍信号] <short mint> | <stage> | YYYY-MM-DD HH:mm` in Asia/Bangkok. Body includes Signal ID/time, Token/CA, Stage/Episode, first/latest active buy time, buy/sell counts, latest/cumulative raw quote, observed inventory, exact reasons and latest triggering transaction. Missing symbol does not block delivery. No non-USDC value is relabeled USD.

## Durable outbox and recovery

`gmail_delivery.signal_id` is a SQLite PRIMARY KEY; deterministic RFC822 Message-ID is UNIQUE. Metadata contains message_type, delivery_mode, delivery_forbidden, subject/body/body_hash/content_hash, status/attempt_count/created_at/last_attempt_at/sent_at, Gmail message/thread IDs, readback_verified, last_error and receipt. Existing master outbox remains the durable signal-to-delivery link. Signal payloads and identities are not rewritten.

The MIME message carries stable Message-ID, X-Frank-Signal-ID, X-Frank-Content-Hash, mode header and visible identity/content markers. Before any send/retry, Sent is checked; readback verifies SENT label, subject, signal identity, mode, headers and decoded body. A matching Sent message restores receipt and SENT_VERIFIED without resending. A successful API response alone is SENT_UNVERIFIED.

After a crash before writing message ID, durable SENDING triggers Sent search. Temporary search indexing/readback failure never causes a blind resend; unresolved acceptance stays SENT_UNVERIFIED. This fail-closed behavior prevents duplicates but may require inspection if no verifiable Sent receipt becomes available. Gmail does not supply an application-level transactional send guarantee.

LIVE, TEST and historical delivery are distinct. TEST requires test-prefixed identity, exact `[TEST] Frank MULTIPLE Gmail Delivery` subject and both explicit disclaimers. Runtime does not deliver TEST rows unless an isolated test caller explicitly enables them. Historical/dry-run Gmail rows have delivery_forbidden=true and DRY_RUN_AUDIT. The durable `signal_delivery_flags` read view supplies an explicit forbidden bit for every historical signal, including imported ACCUMULATION, without changing its original body/hash/identity. Credential recovery processes pending unsent LIVE rows only; historical and TEST rows cannot be promoted.

Live Gmail outbox at this snapshot:

| pending | sent_verified | sent_unverified | blocked | failed |
|---:|---:|---:|---:|---:|
| 0 | 0 | 0 | 0 | 0 |

Zero reflects no new qualifying live MULTIPLE, not a successful email send. Independent durable synthetic evidence verifies blocked-row preservation and accepted-send/crash/Sent-recovery with exactly one simulated send and zero external Gmail sends.

## Legacy GPT consumer

**REMOVED_FROM_EXISTING_TASK**. The enabled existing `$300-3000` hourly monitoring task was inspected through its actual task editor. Its old prompt consumed `runtime-v2/meme/manifest/current.json`, ran GPT SEND/NO_SEND, wrote decisions and could send aggregated Gmail. Those instructions were replaced with explicit NO_CONSUMPTION / NO_AUTHORITY / NO_DELIVERY for Frank/Meme. Save was followed by reopening the editor and matching the saved prompt. Prompt backups and a readback screenshot are private.

Task identity/name/hourly schedule remain; Monster, NFT and CORE retain their prior DEFERRED_NOT_CANCELLED scope. Crypto Daily/us-stock/airdrop tasks were not edited. No new task was created; the existing task was not globally deleted or paused.

## Private runtime

Old manifest and marker explicitly contain `authority=SUPERSEDED_FOR_FRANK_SIGNAL_AUTHORITY`, `current_frank_authority=LOCAL_FRANK_LOCAL_SIGNAL_V1`, historical_only=true and removed-consumer status. Old manifest is superseded/expired. Exact canonical readbacks passed. Only mac-data was written; gpt-data/main remained unchanged. All 28 immutable historical run Git objects retained identical paths/blob hashes. No audit/history was deleted. New Frank service does not write old GPT handoff or depend on GPT.

## Live reconciliation

Starting cursor exclusive: `5nMEWWJPygqDV1oyiW4GCS5kQN1BGeoGwJXNw8EpJTWNC8XJSo9AkCZyQx79mEPstAUUvq4gjuXdSvK5m33aJMHY`. Finalized head: `5LkrGm6A3sHnDUz4V5BruLQYr8avKQGeXv8MBEmzBmQxFmdJmKjTadMttdAb2uHukx9ExrjPL6DVA44bDNEVkHJH`.

| Chain signatures | Local signatures | Missing | Extra | Total local |
|---:|---:|---:|---:|---:|
| 23 | 23 | 0 | 0 | 58 |

Window includes 7 verified ACTIVE_TRADE, 1 ATA_CREATE, 1 FAILED_TX, 5 PASSIVE_TRANSFER and 9 UNKNOWN_NEEDS_REVIEW. All were durably classified/acknowledged with frozen live policy. No new ACCUMULATION/MULTIPLE stage was generated in this window; the imported historical accumulation stays DRY_RUN_AUDIT.

## Tests

490 passed / 3 skipped / 0 failed. Skips are existing unrelated Monster modules without numpy. Coverage includes unique MULTIPLE outbox, no ACCUMULATION email, IDs/receipts, exact Sent identity/content, post-send crash, delayed Sent visibility, readback-before-resend, credential blockage/recovery, historical/dry-run bans, TEST isolation, Gmail failure/nonblocking scanner, GPT independence, legacy authority exclusion and unchanged signal identities.

## Git and operational follow-up

Branch: `codex/frank-only-local-signals`. Starting local/remote HEAD: `29476e140e0cdacb93a4fcedbae57c2fbc80ee1d`, clean. Running delivery implementation commit: `20893b4d2179c8f4977d388e95aa6b2582527d06`; loaded source hash: `f9edbe2239db9f6900306cdfa440714bc5e19b2d072f5ef1f50811346d2cdc3f`. Final reporting/audit-view CLI changes do not alter loaded scanner/model/delivery modules; running source hash is verified. Changes are committed/pushed on this branch, with final HEAD/remote equality and cleanliness reported at handoff. No main merge.

If an already authorized credential becomes available later, reference that existing file via private runtime `gmail-existing-source.json` (existing_oauth_file, optional recipient) or existing launch environment; do not put secrets in this public repository. Recipient defaults to the authenticated Gmail profile. Run `python -m scripts.frank_gmail_delivery --db /absolute/private/forward.sqlite --check` to validate the existing source and readback scope without sending. Current blocker remains until this validation can pass. The adapter checks configuration each polling cycle, and only eligible unsent LIVE outbox rows become deliverable.

API contracts follow [Google Gmail send](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/send), [Sent search/list](https://developers.google.com/workspace/gmail/api/guides/filtering) and [OAuth scopes](https://developers.google.com/workspace/gmail/api/auth/scopes).

FRANK_LOCAL_SIGNAL_V1_LIVE
LOCAL_ACCUMULATION = LIVE
LOCAL_MULTIPLE = LIVE
MULTIPLE_GMAIL = CREDENTIAL_BLOCKED
GPT_SIGNAL_AUTHORITY = REMOVED
PRODUCTION_TRADING = NO_GO
OTHER_PERSONS = DEFERRED
NEW_AUTOMATION = NO
