# PR179 — Reviewer-pinned offline evidence

**Approved parent:** PR176 at `a1d33ab0fd7f68db01b67d3d7da6603af1fd6797`. Independent Mac verdict `APPROVE_OFFLINE_CODE — D1_OS_CRASH_FAKE_SCOPE_ONLY`: 430 full, 69 focused, 3 genuine SIGKILL test cases PASS. Parent source is unchanged.

## D1 offline change

`f0_l2_d1_review_pins.py` adds `verify_pinned_offline_evidence`, accepting separately predeclared `OfflineReviewerPins`. It compares exact candidate Git SHA, original permit bytes SHA256, signed inventory statement SHA256 and separate Ed25519 user/reviewer public-key fingerprints **before** the existing two-role signature and local F0 Git, cryptography RECORD and interpreter-byte checks.

A modified permit, changed source, replacement role public key, or altered and newly signed local inventory does not satisfy the previous reference pins. A self-declaration of complete dependency closure is rejected.

The six focused regression tests generate temporary fixture keys and a local Git repository. No production keys or permissions are generated.

## Unresolved real trust

The pins remain **caller-supplied**. The verifier cannot authenticate where they came from. A real runner would need a separately reviewed, immutable out-of-band trust anchor and independently authenticated real signer identities. No such production root is enrolled here. Its success status is deliberately `OFFLINE_EXTERNAL_PIN_MATCH_NOT_AUTHORIZATION`, and it reports `independent_pin_origin_authenticated=false`.

The existing inventory does not independently authenticate the cryptography wheel distribution, interpreter/stdlib, dynamic dependencies, or 73 installed RECORD entries missing hashes. This is **G-02 OFFLINE PIN VALIDATOR ONLY**, not full executable dependency provenance.

No sender or registry interface was added. Real HTTPS `send_live` still denies; no real RPC/WS, grant, nonce, signing, trade, merge, deployment, or background task. D2/D3 require separate explicit approval. `F0_NOT_PASSED / PRODUCTION_NO_GO`.

## Mac independent review

Create a new detached checkout pinned to the PR179 final SHA and compare only its changes with the approved PR176 SHA. Re-run the full F0 test discovery and `test_f0_l2_d1_*.py` focused discovery in the previously verified `cryptography==46.0.4` environment. Check source and Git blob hashes, six pinned-reference tests, and independently replace a signer public key or re-sign a different manifest while keeping old pins. The validator must reject those changes. Confirm there is no path to a real network call or real permit.

Valid result is `APPROVE_OFFLINE_CODE — D1_REVIEW_PIN_SCOPE_ONLY` or `REQUEST_CHANGES` on the exact new SHA, not approval of production identity or complete D1.
