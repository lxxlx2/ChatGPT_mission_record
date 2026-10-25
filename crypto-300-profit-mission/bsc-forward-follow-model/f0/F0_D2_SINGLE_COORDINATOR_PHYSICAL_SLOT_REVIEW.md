# F0 Issue #207 — distinct physical HTTPS source slot through ONE existing coordinator (OFFLINE ONLY)

## Approval source and scope

Parent is independently ARM64 Mac-approved PR209 exact SHA `a23e58f7a5c28095befec2165c3af611b863e5d0`, base PR206 `68e02323288a1909f6f9c0b6d96d487b9c0a5da5`. The real reviewer reported `APPROVE_OFFLINE_CODE — D2_PHYSICAL_HTTPS_RESPONSE_BOUNDARIES_PATCHED_ONLY` for the previous stdlib HTTPS response-boundary hardening. [Attributed archive](https://github.com/lxxlx2/ChatGPT_mission_record/pull/209#issuecomment-6404067631). Actual Mac full F0 559/559, D1 171/171, physical constructor 16/16, D2-A/B/C 10/10/7, UTC 4, budget 4, hard-stop 5 and child lifetime 2; all no skips. Old PR209 does NOT authorize a physical source or live execution.

## Why this is a real code integration milestone, and exactly what it does NOT do

Before this increment, `f0_l2_d1_coordinator.py` only accepted four memory/fake source classes. Although the same fixed TLS call site was tested by `PatchedConstructorOfflineSource`, there was no **distinct physical-source class slot in the existing scheduler**, and promoting one would have required a new coordinator branch or widening the fake whitelist.

The new `StagedPhysicalHTTPSReadOnlySource` is a **new exact zero-state transport type, not a subclass of FakeSource**. It has no configurable host or provider, no synthetic `reply`, no caller-supplied constructor/factory, no signer or authority object. Its explicit `reply_transport_evidence_offline` invokes the already reviewed `_review_concrete_https_once` call path — fixed bsc-dataseed.bnbchain.org:443, verified TLS context, one JSON-RPC POST, strict response status/header/Content-Length/RAW semantics — **only when the genuine stdlib HTTPSConnection has been replaced by the test**. With the genuine ctor identity present it rejects before network. The private `_REVIEW_TEST_ONLY_CAPABILITY` is test scaffolding and must never be treated as a cryptographic production grant. Any private Python function could be invoked by malicious code; this is not a sandbox/security boundary against arbitrary Python monkeypatching.

The original coordinator execution loop containing the ONE `ThreadPoolExecutor(max_workers=3)`, one `GlobalStartGate`, one `ExclusiveEvidence` durable RID writer and original RAW-before-SETTLE/COMMIT integrity is **factored** into `_run_single_shared_coordinator`. The **same** `run_fake_concurrent` public function remains with the same signature and four exact fake-only classes. It rejects staged physical source at admission, before output/RID/constructor. A strictly private `_run_staged_physical_patched_offline` test entry invokes the **same function** with a test-only discriminator and proves the constructor is replaced, both production root sets are empty, and every scope budget still matches. This entry does NOT bypass source authorization, cannot use the real original HTTPS constructor and must never be exposed as a production CLI. In the same `GlobalStartGate.run`, the fifth exact staged type goes through the **already existing** patched-constructor branch and shared start lock; no alternate scheduling, thread pool, RID or journal exists. Direct gate access with unpatched constructor fails before POST.

**Crucial:** the fake source, D2-A/B/C test signatures, production roots, OS fixed-marker paths, Mac protected entry, hard-stop child, `send_live` and D3 production authorization are **UNCHANGED**. This PR does NOT implement a physical live sender, enrollment or user approval. It is an entirely TEST-PATCHED integration of the **same physical HTTPS client call site** with a distinct source type in the same coordinator. Actual live real-source promotion must be a separate independently reviewed code change, authenticated production D2/D3 + OS one-use marker and separate user-approved bounded read-only pilot.

## New seven offline tests

`tests/test_f0_l2_d2_physical_slot_offline.py` exercises:
1. Public fake entry rejects staged physical type *before writer, journal or constructor*.
2. Test-only staged entry with normal actual stdlib HTTPS constructor rejects *before writer/journal*.
3. A mocked HTTPS ctor (and socket.create_connection mocked to FAIL) runs the distinct staged physical source through **same** global 3-slot coordinator, two original RIDs (eth_chainId then eth_blockNumber), global >=250ms POST start pacing, durable RESERVE_UNKNOWN before constructor/POST, 0600 RAW/fsync before SETTLE and zero real network.
4. Complete rejected HTTP 302 from staged type archives 0600 RAW and FAILED SETTLE, never COMMIT or follow redirect.
5. Exact source has `__slots__=()` and refuses instance transport callback replacement; subclass cannot invoke the private staged runner.
6. Direct lower gate with genuine HTTPS constructor cannot produce any POST start record.
7. Staged `send_live` permanently refuses even if supplied a purported permit.

Positive tests use ephemeral synthetic JSON-RPC responses created by a separate fixture object ONLY inside the patched HTTPSConnection. They do not claim provider throughput, physical TCP/TLS traffic, packet times or authority. Full suite should increase from 559 to 566 if all tests succeed; this is an **expectation, not a result**.

## P0/P1 review hazards to check

- Did factoring the original coordinator accidentally change public `run_fake_concurrent` behavior, fake-only source validation, nested import/shadowing, RID order or thread lifetime?
- Ensure **only one** `ThreadPoolExecutor`, `GlobalStartGate`, `ExclusiveEvidence`; no `run_real_concurrent`, second worker pool, queue or ledger. Validate no spoofed source subclass, instance-level `reply_transport_evidence_offline` injection, no direct staged test path reaching genuine HTTPS constructor.
- Ensure no actual socket can be reached under intended offline tests; a patched constructor that secretly delegates to real sockets is NOT proof of authorization and MUST never be used outside fixture-controlled CI.
- Previous D1 hard-stop, unknown/no-retry, one-use TEST marker, 700ms fake UTC gate, headers/Content-Length and D2-A/B/C test-only denial all pass. No new time injection or factory permitted in the production entry.
- Independently compare exact source diff against approved PR209, hash actual source modules, run full F0 (566 expected), D1-only (171 expected), physical constructor (16 expected), new staged slot (7 expected), D2-A/B/C/UTC/budget/hard-stop/child lifetime, inspect actual Mac ARM64 system. Linux CI is separate from independent Mac approval.
- Do not claim this private staged method is production-safe merely because the original ctor identity is checked. Real producer authorization remains unfinished.

Potential verdict at new fixed SHA: `APPROVE_OFFLINE_CODE — D2_SINGLE_COORDINATOR_PHYSICAL_SLOT_PATCHED_ONLY` or `REQUEST_CHANGES`. Neither grants real source startup, network pilot, signer enrollment, nonce, deployment, merge or trading.

**STOP:** `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`.

## Initial CI defect and correction on the same Draft PR

The first Linux run [40239652434](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40239652434) executed 566 tests and reported **two ERROR**, not an approval: the staged source completed coordinator work but the returned diagnostic read `source.growth_bps`, a synthetic-only `FakeSource` field absent on a real-source-shaped object. This proves why refactoring the original executor must preserve source-specific report semantics.

Source fix commit `10847a3a6f7e3f5028289e85daa4a6ddbef9b655`: the common coordinator keeps the original field and original values for fake-only classes but emits `synthetic_source_growth_bps: null` when the staged source is used, explicitly **not inventing a physical source growth estimate**. Test revision commit `705346ce37b47be9bf5e8636c1c5f83c0bf4eb9f` asserts the honest null. An exact new-head complete CI and fresh independent review are mandatory; the initial failed SHA is not approved. No source, trust-root, scheduler, SDK, RPC or signing capability was added by this repair.

