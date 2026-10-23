# F0 D1 continuation — PR171, independent fixed-SHA Mac review still required

Approved parent PR170 SHA 022f6a4668014af051fc3a1e98a254f5149cc3f7: APPROVE_OFFLINE_CODE — D1_PARTIAL_SCOPE_ONLY; 383 full / 22 D1 tests PASS on independent Mac. Original source unchanged in child PR171.

PR171 adds three new offline components with isolated tests (no real source used):

1. f0_l2_d1_preflight.py: exact Git HEAD/clean checkout, reviewed file manifest SHA256, symlink rejection; strict Z-UTC active permit window and 32/24/6/3/250ms/4000ms/5s/2MB/60s contract. These are UNAUTHENTICATED OFFLINE primitives. In the absence of a separately signed/frozen manifest and production identity roots, no real permit can be accepted.
2. f0_l2_d1_https.py: send_live ALWAYS raises D1_LIVE_TRANSPORT_DISABLED_REQUIRES_D2_REVIEW. Internal fixed hostname bsc-dataseed.bnbchain.org, 443 and POST / TLS core accepts NO default factory and is tested ONLY using in-memory fake connections. Assertions verify TLS hostname/cert, HTTP response and RPC ID, no proxy, redirects, compressed content, retry or oversized payloads. This is NOT an actual live socket trial, nor is it wired to the approved fake coordinator.
3. f0_l2_d1_recovery.py: read-only audit of 0700/0600 private JSONL and fake raw frames. Detects duplicate/orphan SETTLE, mismatched owner/height, non-contiguous commit, duplicate parent faults, raw body hash tampering, interrupted/truncated journal, unaccounted UNKNOWN and FAILED settlement. It NEVER retries or resumes a crashed attempt; INVALID_FOR_PERFORMANCE_CLAIM is explicit.

Matrix deltas (all claims conditional on independently reviewed final SHA):
G-02: OFFLINE CHECKOUT VALIDATOR IMPLEMENTED; a trusted complete file/dependency manifest and live startup integration still missing.
G-03: OFFLINE UTC CONTRACT VALIDATOR IMPLEMENTED; not yet bound to authenticated signed permit or actual time of live operation.
G-04: Approved parent signature verification; production user/reviewer public key enrollment still NOT DONE.
J-06: DISABLED HTTPS CORE TESTED USING MEMORY FAKES; real socket path, cert/proxy behavior and evidence integration NOT VERIFIED.
J-08: OFFLINE DUPLICATE/FAULT RECORD RECONCILIATION TESTED; real live replay and integrated idempotency still NOT VERIFIED.
J-10: OFFLINE CRASH/UNKNOWN ACCOUNTING TESTED; no actual power-loss/restart live trial.
M-02/M-03: BLOCKED for real-source same-window results; short samples will never prove sustained catch-up.

D1 approval here must be scoped APPROVE_OFFLINE_CODE — D1_CONTINUATION_SCOPE_ONLY or REQUEST_CHANGES. F0_NOT_PASSED / PRODUCTION_NO_GO. No live RPC/WS, real permit, nonce, private key enrollment, deployment, trading, background task or merge. Historic 30-request grant consumed.

Mac verification: detached checkout at final PR171 SHA, compare child to approved PR170 exact SHA, verify changed files and clean status; use prior isolated Mac venv with cryptography==46.0.4 and run full and focused tests. All new network tests use fake connections. The private original BSC journal need not be read, altered or uploaded.
## 2026-10-23 PR171 r2 — first continuous commit P1 narrowly fixed

- Previous frozen SHA `9e4b66e9bd119b0752a64dd37504e94b9b68d2ca` independently Mac **REQUEST_CHANGES** even though 400/400 and 39/39 passed. Additional genuine-coordinator-journal test deleted the first `COMMIT_CONTIGUOUS` while preserving all requests and raw SHA256 frames; prior code mistakenly accepted a suffix as `OFFLINE_ACCOUNTED_NOT_LIVE`.
- New recovery audit binds the expected start to **the first reserved legal BLOCK**; if an `INITIAL_HEAD` RPC success is in the raw journal, also checks its actual JSON-RPC response ID, full archived body and HEAD height, requiring first reserved BLOCK at `HEAD+1`. The first `COMMIT_CONTIGUOUS` must be exactly that start; all subsequent commits remain adjacent. Reserved BLOCK heights are also monotonic contiguous in coordinator reservation order. Deleting all commits from an otherwise fully received BLOCK run is `INVALID_FOR_PERFORMANCE_CLAIM`, not an innocent zero-commit success. P1-specific error `D1_RECOVERY_FIRST_COMMIT_START_GAP`.
- Regressions: use actual `FakeSource` and `run_fake_concurrent()` to generate a normal 2+ committed block journal, **delete only first COMMIT** with all original RESERVE/SETTLE/raw frames retained, require audit rejection, then delete every COMMIT and require invalid performance status. A separate synthetic initial HEAD/first reserve mismatch fails. Original UNKNOWN/FAILED/parent fault and archive tamper tests stay unchanged. No extra RPC, keys, permission or live sender.
- The first block remains **externally parent unanchored**; this fix proves only internally expected height bookkeeping. An attacker who rewrites all journal and raw evidence consistently still requires externally protected evidence anchors later; offline verification is not identity validation or production run authorization.
