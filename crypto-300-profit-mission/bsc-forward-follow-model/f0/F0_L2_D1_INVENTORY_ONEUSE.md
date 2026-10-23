# F0 D1 PR175 — test-signed inventory and single-use fake session

**Approved parent:** PR173 fixed SHA `3db12aa9a0e91b37a68061312764336620d871df`, independently Mac `APPROVE_OFFLINE_CODE — D1_SOURCE_HTTPS_FAKE_SCOPE_ONLY`. User Mac **420/420 complete**, **59/59 D1**, zero skipped, 145 tracked F0 files (deterministic source manifest SHA256 `dc390a907b43e69b26040c736c1692cffbf3beb00e6831ca84f6b54adeb68a38`), 181 installed cryptography 46.0.4 files read, 73 without RECORD hashes, fake POST min gap 254.053 ms. The parent code stays unchanged. This new SHA requires new Mac approval.

## What is newly implemented — D1 test-only, not live

`f0_l2_d1_inventory_gate.py` is an **offline** two-role inventory commitment check and an isolated test-only **one-use fake** launch rehearsal. It combines independently reviewed code instead of changing prior approval:

1. Independently regenerate a digest of **every tracked F0 Git tree file** at the submitted code SHA using `tracked_f0_source_manifest_offline`, plus installed `cryptography` wheel RECORD/file-byte manifest and Python executable local SHA256. Require the test attestation to match the scanned bytes, approved code commit SHA and exact raw signed permit SHA256. The entire attestation JSON is signed by TWO separate ephemeral Ed25519 keys with explicit user and reviewer role prefixes; wrong role, duplicate JSON property, missing or unexpected fields, a stale wheel or wrong checkout digest are denied. `complete_dependency_closure_attested` is **required to be false**.
2. Call the preexisting approved `validate_offline_bundle`: raw permit signature+UTC and budget checks, clean exact checkout and source byte manifest. None of these inputs is trusted in production because the caller supplies test identities, local source manifest, clock and registry root.
3. Validate fake-only source exact type and fixed 2MB evidence cap, separated private 0700 evidence and registry directories, **before** marker creation.
4. Call previously reviewed `OfflineGrantRegistry.consume` with the test grant_id and signed permit digest. This O_EXCL marker is durable before the 3-slot in-memory HTTPS fake sender is invoked. No retry, no refund and no new grant on exception. A **new output directory cannot make the ID reusable**, and repeated test use must return `D1_GRANT_ALREADY_CONSUMED`. This is a TEMPORARY test registry, **not** the real fixed Mac production root and not an actual permission.
5. Only AFTER consume succeeds, run previously reviewed `run_gated_fake_session` with fixed `SealedMemoryHTTPSSource`, 3 shared slots, >=250ms actual fake POST start spacing and 32/24/6 upper budgets, then read-only `reconcile_saved_attempts`. All outputs explicitly mark actual_rpc_requests=0, `OFFLINE_TEST_ONLY_ONE_USE_FAKE_SESSION` and PRODUCTION=NO_GO.

Existing public live HTTPS `send_live` remains an unconditional exception. No real source, socket, permit, production trust roots, wallet, signing transaction, deployment, merge, daemon or scheduled task were enabled.

## Acceptance matrix and exclusions

| Control | PR175 direct implementation/test | Boundary |
|---|---|---|
| G-02 | `offline_inventory_statement`, `verify_test_inventory_attestation`; source SHA + local wheel digest + Python binary digest linked to BOTH fake signer roles and exact raw permit digest | **TEST_ATTESTED_ONLY**; the installed RECORD and test keys are not an independently trusted wheel/interpreter/std-lib/import closure. The user/reviewer identity is not authenticated |
| G-03/G-04 | Reuses `validate_offline_bundle` with strict UTC and full JSON field/resource signature; attestation uses role separation | **TEST_ONLY**; no production key enrollment or live wall clock and no actual user-approved grant |
| G-05/G-06 | `consume_then_run_fake_once`: checks first, 0700 root then O_EXCL/fsync marker, no replay across output roots; tests cover duplicate and post-consume failure | **TEST_REGISTRY_ONLY**; production fixed-root gate and real process/crash interruption not integrated |
| J-01..J-10 | Reuses reviewed 3-slot in-memory fake HTTPS, raw archives, future completion and contiguous commit audit | **FAKE_ONLY**; no real socket or TLS peer behavior verified |
| M-02/M-03 | No new evidence | **BLOCKED_REAL_PROVIDER** |

### Independent Mac review — new fixed SHA only

Create isolated clean detached checkout at the final PR175 SHA; compare changed files against PR173 approved SHA, verify blobs/SHA256, confirm `f0_l2_d1_grant.py`, `f0_l2_d1_https.py`, original F0 coordinator and #173 source inventory unchanged. Use `cryptography==46.0.4` in a disposable venv, run all tests and `test_f0_l2_d1_*.py` discovery with no skips.

New test targets in `tests/test_f0_l2_d1_inventory_gate.py`: signed F0/wheel/interpreter inventory equality and roles, mutation, unknown or duplicate JSON keys, false trusted-closure declaration, wrong key/role, dirty checkout, expired signed UTC, fake source method monkeypatch refusal. A normal isolated fake session consumes precisely one marker and finishes with 3 commits and independently reconciled PRIVATE raw journal. Second launch with the same grant_id must fail; after a fake archive failure the marker remains spent even if another output root is chosen; invalid signed inputs must never consume or create evidence. Fake sender must remain MEMORY ONLY.

Verdict `APPROVE_OFFLINE_CODE — D1_INVENTORY_ONEUSE_FAKE_SCOPE_ONLY` for fixed SHA only, or `REQUEST_CHANGES` with a mainline P0/P1 reproducer. Do not broaden into old closed issues.

**Missing before D2/D3**: independently sourced immutable whole-runtime and dependency closure incl interpreter/stdlib and wheel trusted hash; trusted identity enrollment and independently authorized *real* permit, fixed permanent private registry at actual entrypoint and OS crash recovery, independently reviewed real HTTPS implementation and real POST start pacing/timeouts, M-02/M-03 actual same-window BSC growth measurements. Previous 30-call grant consumed. `F0_NOT_PASSED / PRODUCTION_NO_GO`.
