# F0 D1 — TLS connect versus HTTP POST attempt boundary, OFFLINE PR181

**Approved base:** PR #180 fixed SHA `e0af79fcf564aa3d5de826003e8ec0b5f6b49469`, independent Mac `APPROVE_OFFLINE_CODE — D1_POST_UTC_FAKE_SCOPE_ONLY`, 442/442 full tests, 81/81 D1 targeted, six new UTC tests, no P0/P1. The parent remains unchanged.

## Mainline problem

A future genuine HTTPS client has multiple observable phases, not just one mock `POST`. Actual TLS `connect()` may transmit network packets before a subsequent UTC/HEAD final-POST check, while `request()` may fail after partial HTTP bytes. A pre-POST expiry can therefore prevent HTTP POST but cannot retroactively claim **zero network connection attempts**. The existing fake HTTPS coordinator correctly checked its fake POST time but did not expose an actual connection phase.

This D1 child introduces `f0_l2_d1_tls_phases._exercise_tls_post_with_mock` as **test-only source code**. It always requires an **explicit injected connection factory** (no default real factory) and a pre-POST guard. It builds a certificate-verifying/hostname-checking TLS context; fixes HTTPS host/port; asks mock connection to `connect()`, requires an established `sock`, calls final pre-POST guard AFTER TLS setup, then attempts ONE `POST /` with no redirects, compression, proxies or retry; bounds raw bytes and closes in finally. A 503 raw frame remains available to a future journal adapter; unstarted/attempted POST states remain distinct from full committed blocks.

**Critical observation limit:** `post_attempted_at_monotonic` records the **call to `conn.request()`**, NOT an independently measured physical byte emission on the TCP/TLS socket. The new API does NOT claim physical POST start pacing, proof of actual TLS peer verification, or durable RAW settlement; those require a distinct sender integration and independent audit. The factory and guard are caller-injected **mock interfaces**, so the module cannot authenticate that they are safe or represent production consent. `send_live()` in this module AND the pre-existing `f0_l2_d1_https.py` both unconditionally DENY. Do not use the private mock helper as a live entrypoint.

## Tests

`tests/test_f0_l2_d1_tls_phases.py`: seven cases with in-memory mocked connection, global patch forbidding `http.client.HTTPSConnection`, and no sockets. Valid protocol is CONNECT → final guard → POST → response read → CLOSE; denied UTC/HEAD guard after mock connect never initiates mock POST; connect exception and uncertain POST write never retry; 503 raw kept separate from HTTP success; redirect/compression/oversize denied; timeout/response cap checked; public `send_live` disabled.

These tests do **not** use a real endpoint, live permission, production registry, authentication keys, private BSC journal, persistent service or network request. Data is synthetic.

## Review verdict and remaining blockers

Independent Mac fixed-SHA review must compare new changes against approved PR180, verify blobs/SHA256 and clean checkout, test `cryptography==46.0.4` full and focused D1 discovery and separately inspect the seven cases. In particular, avoid confusing `connect_attempted` with `POST` or call-to-request with physical wire-byte start. A refused post may have spent a network connection attempt; a POST write timeout can be UNKNOWN, never eligible to retry on same grant.

Approve only `APPROVE_OFFLINE_CODE — D1_TLS_PHASE_MOCK_SCOPE_ONLY`, not genuine live HTTPS sender. Remaining G-02 authenticated complete runtime source, G-03/G-04 production user/reviewer trust and time source, G-05/G-06 actual fixed-root permit consumption, J-06 physically enforced send-start + live transport, J-10 real interruption, M-02/M-03 real provider throughput are still blocked. Prior real 30-call grant consumed. `F0_NOT_PASSED / PRODUCTION_NO_GO`.
