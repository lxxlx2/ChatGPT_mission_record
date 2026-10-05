# PHASE 2A integration report — 2026-09-30

**PHASE_2A_PASS** (technical acceptance A–M). **PRODUCTION = NO_GO**. **PHASE 2B = NO_GO pending separate real Gmail canary authorization and provider evidence**. No market collector, Gmail send, launchd production installation or ChatGPT automation activation was performed.

## Branch, commits and main synchronization

Working tree: `/Users/jerson/Documents/ChatGPT/crypto-monitor-design-20260930`, branch `codex/crypto-monitor-design-20260930`. Primary X-revenue checkout was not modified.

Starting feature HEAD and remote were `0c277f7e015777c6ae73fd879700755c8c24b246`, ahead 4 / behind 11. Fetched main `dac452086f79d7677cd76e81574bc49ba1bdb341`. Inspected all 11 commits and their paths: 9 airdrop/TGE audit commits and 2 crypto-daily run commits, covering 9 distinct run-record files. None modified crypto-300-profit-mission, Mission spec, automation runtime, portfolio/state or local-agent design rules. `git rebase origin/main` completed without conflicts. Main was never force-pushed.

Rebased Phase 0/1 commits: `1b866cc`, `0758abb`, `9073658`, `b9ef123`. Phase 2A implementation commit: `87fb1e23e4be6e0e6c3133ed45659cc701cfd02c`. Remote-configuration enforcement commit: `cfd4b30` (full identity in Git). This report is committed separately; its own final commit is identified by the handoff and Git history. Feature publication uses an explicit lease against the previously verified remote HEAD because the requested rebase rewrote the four existing feature commits.

Immediately after rebase, before Phase 2A implementation: **90 passed in 0.73s, 0 failed, 0 skipped**. compileall, pip check, git diff --check passed. Initial intentional-public code/config secret pattern scan: 32 files, 0 hits. Final suite: **119 passed in 0.75s, 0 failed, 0 skipped** (90 original + 29 Phase 2A cases). Final compileall and pip check passed; final staged report/code checks recorded at publication. Original Phase 1 tests were not edited.

## Private repository and topology

Created `lxxlx2/crypto-monitor-runtime` with explicit --private; immediately verified `isPrivate=true`, `visibility=PRIVATE`. Reverified private visibility after all remote tests. Default branch `main` contains a bootstrap README only. Both `mac-data` and `gpt-data` were created from that bootstrap.

Every transport operation checks repository private visibility. Repository name is pinned; mac writer can write mac-data only, GPT fixture writer gpt-data only. Namespace is strictly `runtime-v2-test/<run_id>/...`. No production `runtime-v2/` path was written; final recursive remote trees contained **0 production paths on either writer branch**. Runtime IDs, commit proofs and raw payloads remain in the private repo/private local evidence; this public report contains aggregate results.

**LOGICAL_WRITER_ISOLATION_ONLY**: both roles use the existing gh account credential, with code-level branch/repository/path guards. These tests establish that configured transports refuse wrong writes before network access. They do not establish branch-level hard credential ACL.

## Implemented behavior

`mission_agent/transport/github.py`: real GitHub Contents API using existing gh auth credential in memory, private visibility checks, role/path guards, pinned-commit reads, exact canonical bytes and Git blob hash verification, explicit CAS expected SHA, immutable archives, idempotent replay, bounded retries and rate-limit backoff. Request/body counters include failures and retries. Credentials/provider response bodies are not printed or persisted by this transport.

Existing files must match caller's previously observed blob SHA. Exact desired bytes are idempotent success even after an ambiguous operation. A 409/422 or timeout triggers reread; differing state is a conflict, never blind overwrite. Network/server/rate-limit retry only occurs after proving expected state still holds. Retry-After >30 seconds defers by raising and retaining pending work. Archives cannot be updated even if a caller omits immutable=True. Success requires readback of branch/path/content/size/blob hash and the actual write commit; API success alone is insufficient.

`mission_agent/queue/remote.py`: stores current CAS checkpoint and per-batch remote proof in SQLite meta, atomically marks batch/outbox **REMOTE_CONFIRMED** only after verified readback. Existing schema v1 remains unchanged; no destructive migration. Failed publish/readback increments attempt/error and preserves local authoritative payloads.

`Config.for_remote` identifies GITHUB_PRIVATE and fixes the measured remote batch ceiling at **75,000 bytes**; private-mode configurations reject larger values. Phase 1 LOCAL_FILE keeps its established 100,000-byte fixture ceiling and original tests. GitHubTransport defaults to 75,000; explicit 100,000 is used only for size diagnostics. No production runtime is enabled.

The public opt-in runner `scripts/phase2a_remote.py` performs synthetic remote matrix/full/fault stages, rejects evidence roots inside a Git checkout, requires fresh SQLite for full scenarios, and deliberately SIGKILLs two worker processes. Gmail and real collectors are not invoked. Additional private evidence verification exercises a real concurrent-write 409 and inspects final remote trees.

## Real remote E2E

SQLite ingest → immutable mac-data batch archive → CAS ingest/current.json → exact remote readback → SQLite REMOTE_CONFIRMED → fixture reads actual private remote batch → complete receipt archive/current on gpt-data → Mac reads actual private remote receipt → atomic reconciliation.

100 synthetic events covered IGNORE, WATCH, ACTIONABLE_RISK and ACTIONABLE_OPPORTUNITY, exactly **25 each**. Actual batches held 40, 40 and 20 events; sizes **74,254 / 74,264 / 37,264 bytes**. All are below the selected 75,000 ceiling. Each remote batch and receipt was read through the transport and additionally through the GitHub connector. The connector batch bytes exactly matched SQLite, and all receipts matched input hashes and exact item sets/counts.

| Metric | Measured result |
|---|---:|
| Synthetic events / accepted decisions | 100 / 100 |
| Local candidate loss | 0 |
| GitHub mac-data event loss | 0 |
| GitHub gpt-data receipt loss | 0 |
| Reconciliation loss | 0 |
| Duplicate remote batch/receipt archive | 0 |
| Wrong hash accepted | 0 |
| Missing event receipt accepted | 0 |
| Wrong branch writes accepted | 0 |
| CAS conflict silently overwritten | 0 |
| Connector truncation / byte mismatch within selected limit | 0 / 0 |
| ACTION manifests | 50 DRY_RUN |
| Real Gmail sends | 0 |

Final remote trees contain exactly **3 ingest archives and 3 decision archives** for the 100-event namespace. The dry-run delivery manifest has immutable archive/current copies. ACTION stays DELIVERY_PENDING locally; DRY_RUN is a test manifest, not a claim of provider delivery. Health is published/read remotely but remains UNKNOWN because collectors/production operating conditions are unverified; no healthy claim is made.

## Failure and conflict evidence

| Required case | Execution and result |
|---|---|
| New file create | Real private remote create/readback PASS |
| Existing-file CAS update | Real update with observed blob SHA/readback PASS |
| Stale SHA / 409 | Actual GitHub stale PUT returned 409; additional concurrent raw writer caused the real transport PUT to receive 409, reread and reject without overwrite |
| Same payload retry | Exact remote bytes accepted; no new commit |
| Different payload, same batch identity | Immutable archive HASH_CONFLICT, original preserved |
| Network timeout | Injected timeout around real GitHub API; reread expected state, bounded retry, exact final remote bytes |
| GitHub 404 | Actual missing private file response surfaced, no false success |
| Wrong branch | Both configured roles rejected opposite branch before network write |
| Wrong repo | Public repository configuration rejected before network access |
| Rate limit | Injected 429 around real API; bounded backoff/retry/readback PASS; case-insensitive 403 limit headers and long Retry-After covered by unit tests |
| Manually changed remote file | Raw API writer changed current; old expected-SHA transport rejected, manual bytes retained |
| Receipt wrong hash | Bad receipt written/read through remote gpt-data fault path, reconciliation rejected |
| Receipt missing event | Bad receipt written/read remotely, whole transaction rejected |
| Stale remote current | Actual old batch published/read, consumer rejected stale lifetime |
| Archive exists, same hash | Idempotent read, zero additional commit |
| Archive exists, different hash | HASH_CONFLICT, zero overwrite |

Timeout/rate-limit cases are injected responses, not claims that GitHub naturally timed out or throttled this run. The subsequent operations use the real private API; no LOCAL_FILE substitutes. Unit tests additionally cover ambiguous PUT accepted-before-timeout, retry exhaustion, readback corruption, wrong visibility, readback failure preventing REMOTE_CONFIRMED, and remote-success-before-SQLite-checkpoint recovery.

## Restart recovery

1. Process A ingested 100 candidates, built/published the first batch and persisted REMOTE_CONFIRMED, then died by **SIGKILL** without graceful SQLite close. Restart preserved 100 candidates and the original batch identity. Publishing the same batch performed **0 new commits**; immutable/current content was unchanged. Fixture read real remote bytes and generated the first receipt once.
2. Receipt was already on gpt-data. A separate Mac worker read that remote receipt, then died by **SIGKILL before reconciliation**. Restart confirmed 0 prior decisions, read the existing remote receipt and reconciled it. First-batch fixture judgement invocation count remained **1**.

Both child exit statuses were asserted as -SIGKILL. A separate unit test covers remote success followed by death before the SQLite publication checkpoint; replay adopts exact existing bytes with no new write. The real SIGKILL publisher test killed after SQLite confirmation, so the pre-checkpoint window is identified accurately as unit evidence.

## Connector truncation matrix and selected ceiling

Actual `github_fetch_file` on the PRIVATE mac-data branch was used. Complete structured content was compared byte-for-byte with the original private local canonical file. Exact equality implies matching SHA-256; size was independently matched to API remote bytes. No rendered excerpt was treated as read proof.

| Requested bytes | Remote bytes | Connector received bytes | Hash/bytes match | Truncated |
|---:|---:|---:|---|---|
| 1,000 | 1,000 | 1,000 | yes | no |
| 10,000 | 10,000 | 10,000 | yes | no |
| 50,000 | 50,000 | 50,000 | yes | no |
| 90,000 | 90,000 | 90,000 | yes | no |
| 99,000 | 99,000 | 99,000 | yes | no |

Size probes contain a valid fixture batch and explicit top-level synthetic transport padding to reach exact sizes; per-item/count/schema/hash/TTL validation passed. They test transfer completeness, not a realistic dense 99KB candidate workload. The full-load 75KB scenario uses realistic bounded synthetic items, with all three batches separately connector-verified.

Verified maximum: **99,000 bytes**. Selected remote ceiling: **75,000 bytes** = 75.76% of the maximum, **24.24% safety margin**. This is measured for the current connector's structured-content execution path. Future scheduled GPT must still prove it can receive and validate these complete bytes/hash checks in its own execution context; this result does not prove scheduled model context ingestion or autonomous write permission.

## Requests, commits and transfer volume

Counts below are instrumented GitHubAPI calls/body bytes, including retries/errors; they exclude HTTP/TLS headers, Git traffic, gh provisioning/metadata calls and connector internals. Connector execution was separately counted as **12 tool calls**: 1 bootstrap read, 5 matrix reads, 3 full-load batch reads and 3 full-load receipt reads. No unmeasured connector-internal REST request count is invented.

| Scenario | REST requests | Runtime commits | Uploaded body bytes | Downloaded body bytes |
|---|---:|---:|---:|---:|
| Five-size matrix | 105 | 10 | 667,684 | 2,217,428 |
| 100-event flow, including both killed workers | 209 | 17 | 604,428 | 2,871,620 |
| Failure matrix | 103 | 8 | 1,697 | 286,690 |
| Concurrent real 409 + final tree verification | 25 | 2 | 382 | 70,639 |
| **Instrumented total** | **442** | **37** | **1,274,191** | **5,446,377** |

Private bootstrap adds **1 commit**, making **38 total private runtime commits**. Branch creation adds refs, not commits. 100-event scenario's 17 writes: 6 ingest + 6 decision + 2 dry-run delivery + 1 health + 2 intentionally bad receipt fault files. Its ordinary pipeline therefore uses **15 commits**, not one commit per tick/event; crash/idempotent replays add 0 writes.

Daily planning formula: **96–144 periodic health writes + 4×B complete batch/receipt writes + 2×D coalesced delivery summaries + material-state health changes**. Example only, not observed daily throughput: 100 similar events/day, B=3 and D=1 implies **110–158 commits/day**, plus state-change health. If delivery summary is emitted once per batch, D=3 implies 114–162. Each simple CAS publication currently costs approximately 9 instrumented REST calls due to repeated visibility/pinned readbacks; a basic full batch cycle costs about 42 calls. Example B=3,D=1 plus periodic health gives roughly **1,008–1,440 REST calls/day** before extra verification/faults. This is a planning estimate requiring later shadow measurement, not a production rate-limit guarantee. Candidate events are coalesced; health is 10–15 minutes/state-change driven.

## Scheduled consumer and Gmail scope

`GPT_CONSUMER_SPEC.md` defines future private health read/stale rejection, pending-batch verification, GPT judgement, exact complete decision receipt, ACTION delivery handoff and silent IGNORE/WATCH. It forbids full Binance scans, bulk Solana tx, NFT crawling and historical replay. Existing `$300 Crypto资产状态监控` was not enabled. Current Codex cannot manage its ChatGPT scheduled automation; future deployment capabilities remain a separate gate.

No real Gmail send or new Sent search was needed/performed this phase. Exact `[MISSION:<event_id>]` lookup is specified as search-for-candidates followed by SENT label and literal marker readback; search absence is not delivery proof. Previously verified read capabilities are not a new send verification. Real provider canary remains separately authorized PHASE 2B work.

## Evidence, public contamination and limitations

Private local evidence: `/Users/jerson/Documents/ChatGPT/crypto-monitor-phase2a-evidence-20260930` (directory 0700, payload/stat files 0600). Contains SQLite, raw synthetic probe/batch/receipt files, connector summaries, JUnit, per-stage counters, private remote trees and independent concurrent-write verifier. These files are outside the public Git checkout and were not committed/pushed there. Remote immutable/current commit/blob proofs are persisted in SQLite meta; remote trees and private API reads permit independent verification. Tests retain their explicit test namespace for audit.

Public changes are restricted to implementation, tests, synthetic runner, consumer spec, README and sanitized integration report. No runtime JSON, SQLite/WAL, provider IDs, credentials or evidence files were added. The original main's unrelated run records were inherited through rebase, not generated by this phase. Final public review verified exactly 8 authorized changed files, 0 runtime/evidence files and 0 edits to original Phase 1 tests. Final secret pattern scan examined 45 code/config/document files with 0 hits; staged diff check passed. Pattern scans are not a complete secret-detection guarantee.

Known limitations: logical branch isolation only; shared broad account credential; private access revocation or visibility changes fail closed; no real scheduled GPT quality/access/write verification; connector result tested programmatically rather than scheduled model context; timeout/rate-limit faults injected; real publish SIGKILL after SQLite confirmation while pre-checkpoint case is unit-only; no natural network interruption/host sleep/production uptime study; per-file archive/current writes are separate commits with recoverable intermediate states; strict CAS conflicts require reread/review rather than automatic last-writer merge; test identities are synthetic and production install identities remain a later gate; bounded retries leave pending work for a later cycle; no long-running daily resource/rate-limit guarantee, real Gmail or market collectors.

## Acceptance decision

A main sync/90 original tests: PASS. B private visibility: PASS. C both branches: PASS. D batch remote/readback: PASS. E receipt remote/readback: PASS. F actual 409/CAS handling: PASS. G immutable archive: PASS. H two real SIGKILL recoveries: PASS. I 100 events zero silent loss: PASS. J rejected hash mismatch: PASS. K wrong branch rejected: PASS. L connector completeness within selected ceiling: PASS. M no new public runtime contamination: PASS (8 authorized public files, 0 runtime additions).

**PHASE_2A_PASS. PRODUCTION = NO_GO. PHASE_2B = NO_GO until separate explicit Gmail canary authorization and provider gates. Stop at Phase 2A.**
