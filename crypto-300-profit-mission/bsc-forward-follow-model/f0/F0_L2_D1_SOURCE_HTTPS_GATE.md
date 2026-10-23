# F0 D1 source-byte inventory + sealed memory-HTTPS integration

**Parent / approved SHA**: PR172 `76618f44ca685251e4c7c827083d3d6a93849ac2`, independently Mac `APPROVE_OFFLINE_CODE — D1_BUNDLE_SCOPE_ONLY`. Parent Mac **411/411** full and **50/50** D1 (GitHub CI counted 49 D1 names in a different log filter; accept actual Mac discovery count). Earlier PR171, PR170 and D0 approval SHAs remain unchanged. This child PR173 must receive its **own** fixed-SHA Mac code review.

## Source/dependency evidence: G-02 implementation, not signed provenance

`f0_l2_d1_inventory.py` does two *read-only* scans:

1. `tracked_f0_source_manifest_offline(root, exact_sha)` obtains ALL tracked files under the F0 subtree from the exact Git tree and independently compares checked-out bytes and SHA256 digests with Git blob bytes, requiring the checkout to be clean, and rejecting tracked symlinks/untracked local edits. It produces a sorted manifest and deterministic SHA256 for independent inspection. This is stronger than a user-selected subset, but **only covers this F0 subtree**; unrelated modules, runtime Python stdlib, dynamically imported transitive dependencies and entire repo/entrypoint closure are NOT proved safe.
2. `installed_ed25519_distribution_inventory_offline()` verifies `cryptography==46.0.4` and each installed wheel file carrying a sha256 in its local RECORD, produces a complete file digest inventory including unhashed-record entries, and reports the local Python executable digest. The RECORD is distributed with the same installation and can be edited by the operator; absent an **independently trusted wheel hash/installation attestation**, this is NOT a valid producer-independent source of trust. Interpreter+stdlib and all transitive imports remain unverified. It never enrolls signer keys.

Both reports explicitly say **NOT_INDEPENDENT_ATTESTATION**. They are diagnostics for an external reviewer to cross-check and freeze later, not proof of real user authorization, immutable runtime closure, or code safety by themselves. G-02 = **PARTIAL_OFFLINE_INVENTORY**, still **BLOCKED_LIVE**.

## Coordinator + sealed HTTPS request semantics: J-01/J-02/J-03/J-04/J-06/J-07/J-08/J-10

This child adds `SealedMemoryHTTPSSource` as a second exact allowlisted fake source to the existing 3-worker coordinator in `f0_l2_d1_coordinator.py`. The source subclasses the previously approved in-memory `FakeSource` and internally constructs its own **memory-only** request/response factory. No arbitrary socket factory, user callback, live address or production key can be supplied to it.

- The existing `f0_l2_d1_https._exchange_with_factory` implementation prepares its verified TLS context and fixed host/port/headers, then invokes memory-connection `request("POST", "/")`. At precisely this fake POST transition, `begin_fake_post` acquires the **same GlobalStartGate** lock as every fake method (chainId, HEAD, BLOCK); its monotonic timestamp is recorded after any 250ms wait, after TLS setup, immediately before the in-memory request reply. HEAD age is checked both at reservation and at this gate. All HEAD/BLOCK share exactly 3 worker slots.
- `FakeSource.reply` generates the complete in-memory JSON-RPC frame AFTER fake POST authorization. `_exchange_with_factory` reads bounded raw bytes and closes the private memory connection. The coordinator preserves `RESERVE_UNKNOWN` fsync before worker submission, raw frame bytes fsync before SETTLE, original request identity, ordered COMMIT, error stop/drain, immutable budgets. No external socket is created or visited.
- If a finite BLOCK budget is reached while calls remain in flight, a later **hard** HTTP 503/invalid JSON/parent fault/raw archive failure now upgrades an earlier budget-only stop label. This prevents a malformed response being hidden under `BLOCK_BUDGET`. It changes the resulting diagnostic, not the number of sends or scope.
- `f0_l2_d1_bundle.run_gated_fake_session` can now accept only exact `FakeSource` or exact `SealedMemoryHTTPSSource`, with instance response override refused. Ephemeral two-role signed UTC scope, exact test checkout and reviewed file hashes must PASS **BEFORE** either fake HTTPS POST or evidence file. After bounded dispatch it uses the existing recovery audit; failures invalidate performance evidence, never trigger retries.
- `send_live()` remains an unconditional exception `D1_LIVE_TRANSPORT_DISABLED_REQUIRES_D2_REVIEW`. **Actual HTTP traffic=0.** Fake POST start timestamps are not real provider socket start timestamps, TLS cert verification has not been exercised against a real BSC peer, and this test has no independently enrolled user/reviewer trust roots.

## Independent Mac checks for PR173 new exact SHA

Use a **new clean detached checkout** pinned to the PR173 final SHA, compare all Git blob and SHA256 differences against independently approved PR172 `76618f44ca685251e4c7c827083d3d6a93849ac2`. Use the reviewed isolated Python venv `cryptography==46.0.4`; never install or change an active Mac environment. Run complete F0 tests and focused `test_f0_l2_d1_*.py`; no skip is acceptable.

Run the new inventory on the **same detached checkout** to independently count every F0 source and check its ordered SHA256 digest. Verify the cryptography wheel file list and check that local wheel RECORD cannot be treated as self-authenticating. Tamper one tracked F0 file, create an untracked file, change pinned SHA and add tracked symlink in disposable clone: all must fail.

Run real-thread, memory-only sealed HTTPS success and HTTP503/malformed JSON tests. Check post-TLS actual fake POST timing (`>=250ms` starts), three shared slots, 32/24/6 upper caps, HEAD 4000ms age, original request ID, 0600 RAW and pre-send UNKNOWN durability, fake complete contiguous COMMIT and independent recovery audit. In-flight 503 after budget exhaustion must show `RPC_OR_HEAD_FAULT`, not a falsely clean `BLOCK_BUDGET`. A signed bundle with modified scope, untrusted manifest or expired UTC must create ZERO fake requests/evidence. Confirm public `send_live` still denies unconditionally and no network/real grant connection exists.

Return `APPROVE_OFFLINE_CODE — D1_SOURCE_HTTPS_FAKE_SCOPE_ONLY` or `REQUEST_CHANGES` with exact SHA and core P0/P1 only. Do not silently approve D1 entire system or D2/D3. Old 30-real-request authorization is exhausted.

## Future real gates — still BLOCKED

- Independently frozen and role-signed **whole executable/imported dependency closure**, including approved Git SHA, cryptography trusted wheel hash, interpreter/stdlib and dynamic modules, and guarantee checks run on fixed, nonreplaceable code before each actual send (G-02).
- Authenticated independent **production user/reviewer** public trust roots with real user-signed exact UTC window, endpoint, budgets and nonce; fixed private registry atomic grant consume and failure/restart behavior (G-03/G-04/G-05/G-06).
- A *new separately reviewed* actual network sender integration that proves global **actual network start** pacing, timeout, raw archives, in-flight drainage and HEAD freshness under real provider conditions (J-01...J-10). The current fake memory source is not that implementation.
- M-02/M-03 measured same-window real BSC source growth vs contiguous commits and any long-horizon follow decision; none available.

**No RPC/WS, no usable permit, no signer enrollment, no wallet/trade, no merge/deploy or local background monitoring.** `F0_NOT_PASSED / PRODUCTION_NO_GO`.
