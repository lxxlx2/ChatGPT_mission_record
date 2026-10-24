# D1 concrete HTTPSConnection path inside the one coordinator: OFFLINE review

**Baseline:** PR187 exact approved `23f41ea2f984cb652cc07bbf28d9366d18b61701`, with independently archived Mac `APPROVE_OFFLINE_CODE — D1_MAC_PROTECTED_PREFLIGHT_SCOPE_ONLY`. This child branch is **not approved yet**; freeze and re-review its own SHA.

## What now runs together

One and only one existing `run_fake_concurrent()` coordinator continues to own three worker slots, request IDs, shared >=250ms post gate, total/HEAD/BLOCK budgets, `RESERVE_UNKNOWN` fsync before worker submission, raw response archive fsync before `SETTLE`, contiguous block commits, no retry, and failed/unknown bookkeeping.

The new `PatchedConstructorOfflineSource` exercises the actual `_review_concrete_https_once` physical `http.client.HTTPSConnection` code branch **under a test-patched constructor**. It uses the identical shared post gate and response frame protocol. The original standard-library `HTTPSConnection` object is rejected before any connect; this is deliberately *not* a production sender, and Python monkeypatching is not a safe live authorization. The original memory-only and fake source paths are unchanged. `send_live()` remains an unconditional denial.

`tests/test_f0_l2_d1_physical_ctor_integration.py` asserts (1) real HTTPSConnection constructor **call-site** with a network-forbidden patch, private journal, global start pacing and final RAW/SETTLE; (2) unpatched constructor denial before connection; (3) one failed connect charged and never retried; (4) HTTP 503 not accepted as successful chain HEAD; (5) public live entry refusal. The test constructor explicitly forbids real socket use and supplies frames from `FakeSource`. No grant, registry marker, permit, private journal or RPC is used.

## G/J claims and boundaries

- **J01/J02/J03/J04/J06/J07/J08/J09/J10:** new proof is `OFFLINE_PATCHED_CTOR_SINGLE_COORDINATOR_TEST`, **pending CI and independent Mac/Codex review**. Do not label as physical wire send cadence, physical socket throughput, real provider compatibility or OS/power crash recovery.
- **G02/G03/G04/G05/G06:** current Mac `--verify-only` inspects exact checkout and candidate, but does **not** enroll an approved production source, bind the one-use fixed registrar to physical connect, or bind D2/D3 user authority. These stay BLOCKED for live.
- **M02/M03:** same-window real free BSC provider HEAD/committed throughput remains UNMEASURED; original consumed grants remain spent.
- **Critical next gap:** a new independently reviewed, true protected send entry must bind exact user D2 scope, permanently fixed one-use marker O_EXCL/fsync before **any** TLS connect, per-RID RESERVE fsync before connect, RAW-before-SETTLE, a hard whole-operation time limit beyond per-operation 5s socket timeout, unique coordinated POST start pacing and real fail/unknown replay behavior. Current `http.client` call timestamps are call-site observations and must never be called proven on-wire timestamps. Never use the test-only patched constructor as a live network escape hatch.

**Review procedure:** pin this child SHA, compare to approved PR187, verify changed Git blobs and strict source guard. On the independent Mac checkout, run complete F0 unittest suite and focused `test_f0_l2_d1_physical_ctor_integration.py`; run adversarial constructor changes and confirm zero genuine socket/RPC, no writes to fixed production registry. Check unchanged direct `send_live()` denials. Any real socket reachable from test-only API without deliberately monkeypatching the installed constructor is P1.

**Approval target:** `APPROVE_OFFLINE_CODE — D1_PATCHED_PHYSICAL_CTOR_INTEGRATION_SCOPE_ONLY`, **not** a D1 live exit. No new user authorization is implied.

`D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`.

