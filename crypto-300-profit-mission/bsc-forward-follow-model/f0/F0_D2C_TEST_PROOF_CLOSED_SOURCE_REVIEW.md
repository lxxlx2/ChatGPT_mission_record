# F0 D2-C — verify test signatures, reach SAME CLOSED physical source gate (OFFLINE)

**This is not production implementation or live-source release.** The next meaningful gap after test-only D2/D3 signature validation is proving its return value cannot accidentally be promoted into physical source permission. No new scheduler, fake/source replacement, HTTP client, signer enrollment, registry, user consent or network code is introduced.

## Frozen approved baseline

PR204 frozen SHA `8a0037f7d2c2ab8aa1308fa7be18e62e5e76f7dc`, parent approved PR202 `7068312f7e5c1a1bb54fd5c0ab004be74189647c`. External independent ARM64 Mac user-supplied approval `APPROVE_OFFLINE_CODE — D2B_THREE_ROLE_TEST_SIGNATURE_BINDING_ONLY` [archived on PR204](https://github.com/lxxlx2/ChatGPT_mission_record/pull/204#issuecomment-6400602183): complete F0 546/546, D1 165/165, D2-B 10/10, D2-A 10/10, UTC 4/4, physical ctor 10/10, budgets 4/4, hard-stop 5/5, child lifetime 2/2, all 0 skips and exit 0. Test-root signatures are not human identity or production authorization.

## Narrow source change

New `f0_l2_d2c_test_proof_admission_offline.py` exposes ONLY `try_admit_signed_test_fixture_offline()` and permanently denied `send_live()`. The function:
1. **Rejects** if either prior module advertises production roots. Caller does not supply trusted production roots, output directory, sender, transport factory, lease/nonce or callback.
2. Invokes already reviewed D2-B `verify_three_role_test_proofs_offline` on original D2/D3 raw bytes with injected **ephemeral test** public roots and signatures. D2-B itself verifies original D2 user/reviewer and domain-separated D3 operator signatures over the original D3 digest, permit digest, source SHA/manifest and the existing strict D3 candidate budget/UTC rules.
3. Strictly checks the returned TEST-ONLY diagnostic declares zero network, zero physical sender, no real consent and no trusted production roots. **The diagnostic is a caller-forgeable plain dict, not an authority credential.**
4. Constructs a non-executable `UnreleasedPhysicalHTTPSProposal` only from source SHA, manifest, D2 and D3 raw digests already emitted by D2-B; **then calls the original `f0_l2_d1_coordinator.request_physical_source_admission`**, which remains unconditionally DENIED. No alternate scheduler/worker/RID writer is created, and the existing four fake source paths are completely unchanged.
5. Adds a final unconditional `D2C_TEST_FIXTURE_NOT_PRODUCTION_AUTHORIZATION` raise after calling the existing gate. Even if the gate were inadvertently changed to return, the offline rehearsal **cannot** become a live entry.

No changes to source constructor, original `GlobalStartGate`, `run_fake_concurrent`, `ExclusiveEvidence`, signed trust-root enrollments, protected Mac entry or one-use marker. **Nothing creates or invokes actual `HTTPSConnection`.** D2-C is merely a checked *failed* composition of existing approved D2-B and D2-A primitives.

## New independently reviewable tests

`tests/test_f0_l2_d2c_test_proof_admission_offline.py` uses D2-B's in-memory test-key fixture:
- Three valid TEST signatures reach exactly the original D2-A source admission and are denied before any writer/socket/marker call. Inspect the passed exact proposal source SHA, D2 raw digest, D3 raw digest; no prior/private evidence.
- A structurally valid but changed signed D3 input fails at signature **before** the physical admission hook.
- Mutated D2 permit with adjusted D3 digest (and old signatures) fails at D2 cryptographic stage before admission.
- Reused operator/user Ed25519 key denied before admission.
- If either production trust-root group is populated, this test rehearsal fails **before any test verifier**.
- A forged 'production approved' diagnostic refuses before admission.
- If the original admission gate is monkeypatched to incorrectly return a grant, this function still always fails; its `send_live` refuses any input.

Expected count: seven new isolated tests, full F0 553 if all prior tests are preserved. **Do not treat these counts as PASS until exact SHA Linux CI and independent review.** All test mock-patches must assert no physical socket, registry writes or raw capture.

## Acceptance and stop gates

Pin exact Draft PR HEAD SHA and approved PR204 base. Run complete F0, D1-only, D2-C 7, D2-B 10, D2-A 10, UTC 4, patched ctor 10, budgets 4, hard-stop 5, child lifetime 2; record PASS, skip, exit and unique test IDs, hashes and actual loaded source. Independently test valid TEST signatures always reach the **same** closed source gate and that no successful path exists even if that gate returns unexpectedly. Real ARM64 Mac detached validation when available; if not, explicitly report it unverified. Review target `APPROVE_OFFLINE_CODE — D2C_SIGNED_TEST_PROOF_CLOSED_ADMISSION_ONLY` or `REQUEST_CHANGES`. Reviewer must distinguish independent Mac results from GitHub Linux CI.

The actual source is still unavailable. **Real signer/key ownership enrollment, independent true D2/D3 human authority, production OS-user-bound one-use marker and first bounded real read-only pilot require separately explicit user approval and later source reviews.** Do not synthesize signatures or enroll any test key. Do not access real RPC/WS, old private journal, production nonce, deploy, merge, trade or schedule background services.

**Current: `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`.**
