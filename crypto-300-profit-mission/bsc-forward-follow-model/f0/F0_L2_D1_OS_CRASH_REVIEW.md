# F0 D1 — POSIX process-crash offline durability acceptance, PR176

**Approved parent:** PR175 `17964d878424834ec04535c3866f115cb6f34fe7`, Mac independently `APPROVE_OFFLINE_CODE — D1_INVENTORY_ONEUSE_FAKE_SCOPE_ONLY`. Actual Mac 427/427 full, 66/66 D1 focused, 7/7 new; parent frozen, no runtime source changes. The prior proof was OSError in RAW archival and in-memory fake one-use registration, not a process actually killed during I/O.

## Why this phase

D1 J-10 previously had no OS-process interruption evidence. This child builds **a single new test-only module** `tests/test_f0_l2_d1_os_crash_survival.py` with three disposable POSIX subprocesses killed by actual `SIGKILL` at deterministic fsync boundaries. Existing approved `OfflineGrantRegistry`, `ExclusiveEvidence`, `SealedMemoryHTTPSSource` and `reconcile_saved_attempts` are **not edited**.

The subprocess registers a fake 0600 marker in an isolated 0700 root, using test grant ID and all-test SHA digest, then either:

1. **MARKER** — immediately after atomic O_EXCL/file+dir fsync, before evidence creation. Parent verifies no journal, exactly one spent marker, and reuse rejected.
2. **RESERVE** — immediately after the first CHAIN `RESERVE_UNKNOWN` event was written, flushed and fsynced, **before** the executor submits the fake worker. Parent verifies complete newline journal, 1 reserved CHAIN with no SETTLE, no RAW or COMMIT, and `INVALID_FOR_PERFORMANCE_CLAIM` with UNKNOWN request ID.
3. **RAW** — after the first BLOCK fake response's raw bytes and RAW directory have been fsynced but before any corresponding `SETTLE` event; parent verifies orphan raw response with original request ID, BLOCK still pending, no continuous commit, invalid audit, and spent marker.

Each child has a 15-second process timeout, is a short-lived direct subprocess (not an automation/daemon), uses **exact sealed in-memory HTTPS** and temporarily monkeypatches any `http.client.HTTPSConnection` attempt to raise. It never loads private BSC journal, creates real nonce/permit, contacts RPC/WS, or signs a chain transaction.

**Checks:** OS returncode must be negative `SIGKILL`; private evidence and marker file modes, full newline journal, pending request identities, zero auto retries, no journal mutation from reconciliation, and same grant ID rejected even if output would be moved. All fatal cases preserve the prior attempt as potentially sent/UNKNOWN, never convert to successful network provenance.

**Important limits:** A real OS `SIGKILL` process crash tests durability as exposed by the current file system, **not sudden physical power loss**, torn disk writes, media failure, malicious deletion of the registry, multi-host unique nonce storage, or real HTTPS request uncertainty. The old completed/failed fake response frames are fabricated. No independently trusted production root or actual live entry exists. J-10 may be marked **OS_PROCESS_SIGKILL_FAKE_PASS subject to independent Mac replay**, never REAL_POWERLOSS_PASS or LIVE_PASS.

## Independent Mac fixed-SHA review

- New clean detached checkout at final PR176 SHA; compare one test file, this document and HANDOFF/tracker updates against approved PR175 fixed SHA. Git blob/SHA256 clean.
- `cryptography==46.0.4` isolated reviewed venv; run full F0 tests and `test_f0_l2_d1_*.py` focused discovery. GitHub Linux first full test evidence has 430 PASS, 3 new; Mac counts should be reported from actual fresh logs.
- Verify each child is truly terminated with SIGKILL at intended boundary, not by TimeoutExpired, assertion or catchable exception. Read disposable marker/log/raw bytes. Assert immutable marker and UNKNOWN after process exits; no automatic retry on next attempt even if output directory changes.
- Check library imports and test body contain no real network fallback, no `send_live` or token/permit/nonce issuance, no use of production `PRIVATE_FIXED_REGISTRY`, no daemon/background scheduling. Termination happens only in the disposable test subprocess; reviewer Mac shell should remain intact.
- Request verdict `APPROVE_OFFLINE_CODE — D1_OS_CRASH_FAKE_SCOPE_ONLY` or `REQUEST_CHANGES` only for new mainline P0/P1. No reopening older approved edge cases.

## Remaining gates, unchanged

G-02 independently attested **full runtime** (wheel trusted hash, interpreter/stdlib and imported dependency closure) remains BLOCKED; local RECORD + ephemeral signing is not enough. G-03/G-04 production identity/root and actual user-signed UTC/nonce authorization remain BLOCKED; G-05/G-06 must bind the *fixed production registry* to future real startup, not the temporary offline test directory. J-06 real HTTPS/socket and physical send-start limiter remain blocked; M-02/M-03 source growth and sustained chase evidence absent. Explicit D2 user authorization is still required for any future real short-run D3. Old 30-call authorization consumed. `F0_NOT_PASSED / PRODUCTION_NO_GO`.
