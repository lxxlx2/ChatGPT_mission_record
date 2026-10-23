# F0 D1 — Offline fake HTTPS actual POST-time signed UTC gate (PR180)

**Approved parent:** PR179 fixed SHA `e65e8bf3ceca4436e8adce9db6a1ce9c037e8e88`, Mac independent `APPROVE_OFFLINE_CODE — D1_REVIEW_PIN_SCOPE_ONLY`: 436/436 full, 75/75 D1 targeted, 6/6 new, no mainline P0/P1. PR179 source is unchanged.

## Why

Previous offline bundle checked signed UTC once before spinning up worker tasks. The existing sealed-memory HTTPS worker already checked **monotonic** HEAD freshness and the dispatch deadline at its actual fake POST transition. But a signed permit can expire **between initial validation and the POST start** while the TLS/context setup or concurrency pacing waits. The candidate must refuse that individual attempt without sending even when the request is already durably reserved.

## New bounded implementation

- `f0_l2_d1_post_utc.OfflinePostUTCWindow` accepts the same signed permit raw bytes and reviewed source SHA. It strictly parses its signed `window_start_utc` and `window_end_utc`, enforces a maximum 10-minute window and tracks the last UTC observation. It rejects naive/non-UTC clocks, wall-clock rollback, dates outside the window and invalid RPC payloads. Test clock is injected and **NOT trusted external time**.
- `GlobalStartGate.run` accepts only a validated `OfflinePostUTCWindow` and only for **exact** `SealedMemoryHTTPSSource`. At the in-memory `POST("/", ...)` transition, AFTER fixed HTTPS context construction and spacing wait, it rechecks the signed UTC window while holding the shared gate lock. Dispatch deadline and HEAD TTL are also rechecked after the clock call. An invalid UTC produces `PRESTART_OFFLINE_PERMIT_UTC_DENIED` rather than a fake POST; the reserved request is settled as FAILED, no auto retry.
- `run_gated_fake_session` creates that window only after the already reviewed two-role ephemeral signatures, UTC/budget, fixed Git and file hashes have passed. Its optional `test_only_fake_post_utc_clock` cannot enable an arbitrary source, callback or real socket. `consume_then_run_fake_once` forwards the test-only clock to the existing signed-inventory and O_EXCL/fsync test registry flow; a spent test grant remains spent after post-time UTC denial.
- The new result metric `fake_post_utc_checks` counts checks that actually passed at memory POST start. The result still explicitly reports `network_requests=0`, `no_live_sender=true` and `F0_NOT_PASSED / PRODUCTION_NO_GO`.

## New tests

`tests/test_f0_l2_d1_post_utc.py` exercises valid fake POST starts, UTC expiry after successful startup but before BLOCK memory POST, wall-clock rollback between CHAIN and HEAD, naive clock denial, wrong source or unbound permit, and fake post-UTC expiry after one-use test registry consumption with reuse refused in a different output directory.

Only in-memory fake sources, disposable Git fixtures and ephemeral keys are used. The test suite patches `http.client.HTTPSConnection` to fail if called. No actual BSC RPC/WS or socket capability is installed or invoked.

## Limits / next gates

This is **G-03/J-02/J-04 OFFLINE TIME-OF-USE FAKE** progress, not an authenticated real clock, complete running code and wheel provenance, externally verified user/reviewer identities, permanent production registry activation or actual TLS socket integration. A user-supplied fake UTC clock is intentionally not trusted for D2. A new independently authenticated D2 permit + explicit user permission is needed before any physical provider request. J-06 real HTTPS, J-10 real socket interruption, M-02/M-03 same-window throughput and sustainable follow remain blocked.

**Mac independent review:** new clean detached checkout pinned to PR180 final SHA; verify changed Git blobs/SHA256 against frozen PR179, run full and `test_f0_l2_d1_*.py` discovery in isolated cryptography 46.0.4 environment. Check both expiry at start and after fake TLS setup, no fake BLOCK started and original reservation remains correctly SETTLED FAILED, first-commit audit still rejects missing origins, no signing identity or network path enabled. Verdict `APPROVE_OFFLINE_CODE — D1_POST_UTC_FAKE_SCOPE_ONLY` or `REQUEST_CHANGES` at the exact new SHA only.

No true real network, production keys, D2/3 approval, trade, merge, deployment, persistent local service or background automation. Old 30-call real allowance consumed.
