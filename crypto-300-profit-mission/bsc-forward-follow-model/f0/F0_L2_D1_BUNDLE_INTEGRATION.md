# F0 D1 offline signed-configuration bundle and audit (PR #172)

**Review parent**: PR #171 Mac independently reported `APPROVE_OFFLINE_CODE — D1_CONTINUATION_SCOPE_ONLY` at `c86b7dbf7b8f714ee68a793823dda18e9346be22`, full **402/402**, D1 **41/41**, 0 SKIP. First-COMMIT P1 closed. Parent remains unchanged. Rejected earlier SHA `9e4b66e9bd119b0752a64dd37504e94b9b68d2ca` retains `REQUEST_CHANGES`.

## What this child D1 code actually proves

The new **`f0_l2_d1_bundle.py`** composes the independently tested primitives rather than reimplementing them.

1. Validate raw JSON bytes strictly: no duplicate keys at any nesting level, no unknown, missing or extra permit fields. These are signed as the **exact bytes** rather than canonicalizing a changed permit.
2. Require two independently verified Ed25519 signature proofs bound to `permit_sha256`, the fixed reviewed Git commit SHA and distinct user/reviewer roles, using the already Mac-reviewed `cryptography==46.0.4` implementation. All keys used by this PR's unit tests are **ephemeral in-memory**; no real user/reviewer public keys enrolled.
3. Validate the strict UTC-Z start/end window and every fixed endpoint/method, 32 total/24 blocks/6 HEAD refresh/3 shared slots/250ms start spacing/4000ms HEAD TTL/5s request timeout/2 MB raw frame/60s dispatch policy through `validate_window_contract`; verify clean exact Git checkout SHA and every independently provided listed source blob SHA256 with `verify_fixed_checkout_offline`. The three checks must all identify the **same** code SHA.
4. Run **only** the existing exact `FakeSource` class through the already-approved three-worker fake coordinator, then independently replay the persisted local evidence with `reconcile_saved_attempts`. A modified instance `reply` callback is explicitly rejected; no executable live transport callback or socket is accepted. Reject bad signatures/out-of-window before any fake RPC or new evidence file is created.
5. Surface **separate** typed labels: `OFFLINE_BUNDLE_VALIDATED_NO_NETWORK_PERMISSION`, `actual_rpc_requests=0`, `real_permit=NOT_CREATED_NOT_ACTIVATED`, `F0_NOT_PASSED / PRODUCTION_NO_GO`. A valid fake journal **does not** imply actual blockchain sampling success.

**Companion tests**: `tests/test_f0_l2_d1_bundle.py`: composed success on detached local test Git commit; signed UTC tampering; separately signed but forbidden resource settings; duplicate/extra JSON fields; swapped signer; modified Git bytes/reviewed manifest; invalid signer or expired signed UTC blocks even fake execution before evidence; bounded exact FakeSource 3-slot fake session; wrong callable injection refusal. These are local temporary Git repos and local test keys; never old private BSC journal.

## Still unresolved — do not label D1 complete

| D0 control | What is achieved | Remaining gate |
|---|---|---|
| G-02 | Signed SHA binds to clean local HEAD and an injected reviewed list of source bytes | **BLOCKED**: trusted immutable complete runtime/dependency source inventory + cryptography wheel/installed file closure not independently attested; caller may inject manifest |
| G-03 | All known permit fields required, no duplicate or extra fields, actual Ed25519 bytes bound to UTC and budget | **BLOCKED**: current UTC is supplied by offline caller; no trusted wall-clock recheck at real send-start or D2 user-authorized signed permit |
| G-04 | Offline distinct user/reviewer signatures verified | **BLOCKED**: no authentic production user/reviewer trust roots or identity enrollment; `PINNED_LIVE_TRUST_ROOTS={}` |
| G-05/G-06 | Existing one-use registry tested separately, not touched by fake session | **BLOCKED**: authenticated grant must be atomically consumed in a future gated runner; no live grant issued |
| J-01...J-05/J-07...J-10 | Fake three-worker coordinator and persisted fake responses independently re-audited in one run | **PARTIAL**: no real sender or OS power-loss rehearsal |
| J-06 | Approved separate fake HTTPS connection semantics still available | **BLOCKED**: `send_live()` always DENIES, no real connection factory or socket, and HTTPS seam NOT connected to the coordinator |
| M-02/M-03 | No new real performance measurement | **BLOCKED**: same-window BSC source growth/commits, persistence and independent first parent anchor unknown |

**Trust boundary:** `validate_offline_bundle(..., test_only_trust_roots, reviewed_files, now)` accepts **caller-supplied** keys, manifest and time. It is NOT a secure live authorization gateway; no code in D1 may use its returned success label to unlock the disabled sender. Changing `PINNED_LIVE_TRUST_ROOTS` or adding a live entrypoint requires separately fixed code SHA and independent review, then independent D2 explicit user permit. A test fixture that signs its own permit is not user authorization.

## Independent Mac review requested for new SHA

From a new clean, detached checkout of the final PR172 commit, verify all new file blobs and compare to PR171 approved exact SHA; ensure original modules were not modified. Use the existing isolated Python test environment with exactly `cryptography==46.0.4`. Run the full test discovery and D1 focused discovery. Independently verify the signed permit byte hash and UTC tamper/counterfeit rejection, Git byte alteration rejection, no duplicated keys or unknown scope acceptance, 250ms fake global starts and 3-slot ceiling, and `reconcile_saved_attempts` on untouched vs intentionally corrupted raw journal.

A result here can only be `APPROVE_OFFLINE_CODE — D1_BUNDLE_SCOPE_ONLY` or `REQUEST_CHANGES` for exact SHA. **No real RPC/WS, real permit/nonce, production trust roots, wallet signatures, trades, Git merge, deployment, Mac background task or schedule.** Consumed old 30-call grant not reused. `F0_NOT_PASSED / PRODUCTION_NO_GO`.
