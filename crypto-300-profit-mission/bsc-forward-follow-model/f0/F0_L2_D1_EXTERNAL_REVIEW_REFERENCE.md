# F0 D1: externally anchored partial runtime reference — PR177

**Parent independently Mac approved**: Draft PR176 exact SHA `a1d33ab0fd7f68db01b67d3d7da6603af1fd6797`, `APPROVE_OFFLINE_CODE — D1_OS_CRASH_FAKE_SCOPE_ONLY`: 430/430 full, 69/69 focused D1, 3/3 genuine SIGKILL (-9) of temporary fake session at marker/RESERVE/RAW fsync boundaries; no new P0/P1. Parent code is frozen, unchanged. PR177 is an **independent new child Draft** whose code requires separate exact-SHA review.

## One next-stage mainline improvement, not another fake scanning loop

Prior D1 inventory attestation used an operator-injected trust root, self-generated hash lists and signatures from ephemeral test keys. These can establish **consistency** but not **external provenance**. It is unsafe for a live sender to trust them.

New `f0_l2_d1_external_review.py` implements only the reviewer/reference half of the future gate, without adding a sender, permit issuer or production key:

1. Two top-level immutable-intent constants `PINNED_REVIEW_AUTHORITY_KEY_ID=None` and `PINNED_REVIEW_AUTHORITY_PUBLIC_PEM=None`. The **normal configuration has no enrolled authority and rejects EVERY verification**, before attempting disk or network work, with `D1_REVIEW_AUTHORITY_NOT_ENROLLED`. Public verification API accepts **no trust-roots parameter** and cannot have the caller nominate an arbitrary reviewer key.
2. An externally signed **exact raw JSON byte statement**, domain-separated `bsc-f0-d1-independent-review-reference-OFFLINE-v1` and SHA256-bound. Schema is strict; duplicate/extra/missing JSON fields or a claim `complete_runtime_closure_attested=true` fail. Reviewer key ID and canonical Ed25519 public-key fingerprint must match the pinned authority, and the signature must verify against the pinned public key.
3. After signature verification, separately reconstruct the current exact **Git HEAD/F0 tracked source manifest** and its deterministic SHA256, entire installed `cryptography==46.0.4` file-byte/RECORD summary, interpreter binary SHA, and the exact raw permit byte SHA. The recomputed local report must match every signed field, including file counts and hash-missing entries. A valid reviewer signature on values that **do not reflect the actual machine** is rejected.
4. Successful result is named `OFFLINE_INDEPENDENT_REFERENCE_MATCH_PARTIAL_ONLY` with `complete_runtime_closure_attested=False`, `live_sender_authorized=False`, `grant_consumed=False`, `production_user_consent_verified=False`, `actual_rpc_requests=0`. There is **NO** capability token, network call, registry marker, live entrypoint or production permission conferred.

**New unit tests** `tests/test_f0_l2_d1_external_review.py` run solely in a disposable local Git checkout. Only tests monkeypatch empty pin constants with ephemeral review public keys; the production/default code remains default-deny. They verify independently signed exact reference success in the fixture, default no-authority denial, substitute self-signed key denial, role/ID mismatch, externally re-signed incorrect source/wheel/interpreter/permit/count values, dirty checkout, duplicate or extra fields, and misleading full-closure claims.

## Precise security limitations and next dependency

- These pins are **not** populated in this PR. A fake/test patchable Python constant is not by itself a hardware-backed or nonreplaceable trust root. An operator who can replace installed code and its pinned key can forge a reference. **D1 still needs a separately reviewed fixed bootstrap key, verified immutable code/dependency closure, and evidence that the reviewer actually approved the exact bundle**.
- Signing the manifest does **not** prove independent provenance of installed wheels, Python standard library, dynamically imported modules, native libraries or package-manager build chain. Existing source inventory currently covers all tracked **F0 subtree** paths, not other imported repo code; `cryptography` local RECORD has 73 unhashed files per the last independent Mac review. The schema intentionally disallows a false `complete_runtime_closure_attested=true`.
- A code SHA in this offline reference is not user consent. A future D2 grant needs **separately enrolled production user AND reviewer identities**, independent byte-signed scope+UTC+nonce, fixed registry and a new explicit user authorization. PR177 **does not** alter `PINNED_LIVE_TRUST_ROOTS={}`, `send_live` still unconditionally DENIES.
- Real BSC source throughput, physical sender timing, restart uncertainty and first-parent external anchoring have **no new evidence**. No RPC/WS, secrets, production keys, permit, nonce, trading, merge, deployment, or scheduled task.

## Exact-SHA independent Mac review

1. Detached clean new checkout at final PR177 head, compare to the approved PR176 SHA and review ONLY changed files; full Git blob SHA256 and HEAD parity. Confirm no existing approved source was edited and no new live entry was added.
2. Use isolated Mac Python environment with `cryptography==46.0.4`, run full F0 tests plus `test_f0_l2_d1_*.py` D1 discovery, zero SKIPs.
3. Call `verify_independently_signed_reference_offline` without monkeypatching pins; it MUST deny `D1_REVIEW_AUTHORITY_NOT_ENROLLED`, even if supplied a cryptographically valid self-signed manifest. Verify **no** permit marker, journal or socket is accessed on this denial.
4. In a fresh isolated **test-only** fixture, pin only a separately generated reviewer public key, recreate source and wheel inventory and signed reference, require exact SHA/manifest/permit equality, then try self-signed substitute key and legitimate signer re-signing incorrect source/wheel/Python/permit values. Each must fail with reviewer signature/byte mismatch. Change Git checkout bytes, alias reviewer ID, introduce duplicate/unknown fields or assert false full closure; all must fail.
5. Distinguish partial reviewer verification from **real** independent trust bootstrap. Never mark G-02 live PASS or D1 complete. Report `APPROVE_OFFLINE_CODE — D1_EXTERNAL_REVIEW_REFERENCE_ONLY` or `REQUEST_CHANGES` at new fixed SHA.

**Status**: `G-02=OFFLINE_EXTERNAL_REVIEW_SEAM_PARTIAL`, D1 incomplete; G-03..G-06 actual real identity+one-use active path BLOCKED, J-06 real TLS/socket BLOCKED, J-10 only OS_PROCESS_SIGKILL_FAKE_PASS, M-02/M-03 real BSC measurements BLOCKED. `F0_NOT_PASSED / PRODUCTION_NO_GO`.
