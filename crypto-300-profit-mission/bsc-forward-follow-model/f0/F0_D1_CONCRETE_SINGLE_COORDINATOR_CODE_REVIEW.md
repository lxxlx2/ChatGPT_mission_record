# PR186 — single-coordinator concrete HTTPS code path + Mac provenance, OFFLINE ONLY

## Frozen authority/design and source

- Parent approved design PR185 `a469019b596045d8d4cea9afe9a8393e40a10981`, independent Codex `APPROVE_DESIGN — F0_USER_CODEX_LIGHTWEIGHT_AUTHORITY_MODEL_ONLY`. Only three Markdown files in that parent; source remains `D1_BLOCKED_AUTHORITY`.
- Last approved source-level integrated fake PR183 `4e12e4f43ca2cc466e6c20b79fcdbc23228dd28f`, Mac **464/464 complete** and **103/103 D1 targeted**; PR182 concrete HTTPS source Mac 459/459 complete and 98/98 D1 targeted.
- This child implements a **bounded D1 code integration** under the new user+Codex review model, with no actual live user approval. It **does NOT** claim D1 exit, D2 grant, real network execution or production build.

## Code execution integration (what is actually new)

`f0_l2_d1_concrete_https.SealedConcreteOfflineSource` is a new exact-class sealed in-memory TLS fake connection type. Unlike the old separate mock lifecycle tests, it exercises the **PR182 actual `_review_concrete_https_once()` standard-library code path** inside the **existing ONE three-slot coordinator**. The transport constructor is an immutable `_SealedMemoryTLSFactory` type; it cannot accept arbitrary caller factories and never opens a socket. Real `http.client.HTTPSConnection` is patched to abort by the regression tests. Public `send_live()` in old, concrete and integrated modules stays unconditional DENY.

The same previously independently Mac-reviewed coordinator and journal remain the **sole owners** of all:
1. Stable request ID, method and budget (CHAIN / HEAD / BLOCK, max 32 in proposal, 3 active slots).
2. Durable coordinator-authored `RESERVE_UNKNOWN` fsync BEFORE it submits any worker (and, in the fake test, before memory-TLS `connect()`).
3. One shared global 250ms start lock, dispatch monotonic deadline, HEAD TTL and signed **TEST** UTC check **after fake TLS connect but before POST**.
4. Exact fixed-host `POST /` and bounded RAW response through the reviewed concrete HTTPS client parsing code, not a different source parser; no real TLS socket.
5. Raw response and directory fsync BEFORE SETTLE, independent recovery audit, contiguous COMMIT and UNKNOWN/invalid performance response on error. No automatic retry, refunded grant, reopening or background job.
6. One private disposable TEST O_EXCL/fsync consumed marker via unchanged bundle/inventory gate before any worker. Changing evidence output root does not reset test grant.

There is **no factory or callback** supplied through the bundle, inventory gate or integrated entry. Exact class whitelists accept only `FakeSource`, original `SealedMemoryHTTPSSource`, and this new `SealedConcreteOfflineSource` for offline use.

`f0_l2_d1_mac_provenance.review_loaded_runtime_offline()` performs an offline measurement on a **reviewer-frozen Git checkout**: verify a clean exact HEAD for **all** tracked F0 files, inspect a fixed list of critical Python `sys.modules` physical file origins, and record the local Python executable digest and cryptography distribution digest/RECORD gaps. It does not load unchecked new modules, replace the current execution environment or claim independent cryptographic trust of the full OS. Codex compares this evidence to the known SHA and independently checked Mac release provenance under the approved lightweight F0 model; test-only stub fixtures exercise alternate import origin and dirty checkout refusal. **A digest produced by the running machine cannot authenticate itself.**

`production_d1_exit_verdict()` now describes actual outstanding restrictions per PR185 *without incorrectly requiring a third human reviewer or complete hostile-OS PKI closure*. Until the user approves an exact D2 scope and code genuinely enforces it, `D1_BLOCKED_AUTHORITY` remains correct.

## Integrated tests (new cases)

- Run signed fixed-SHA TEST permit + test pins, O_EXCL grant and reviewer-checked local fake bytes through **concrete HTTPS lifecycle** while the constructor of real `http.client.HTTPSConnection` is patched to fail: 6/6 reserved/settled with matching origin IDs and fake starts; 3 ordered commits; raw audit `OFFLINE_ACCOUNTED_NOT_LIVE`, no real RPC.
- Signed UTC already expired at POST after fake connect: one reserved/settled, no fake POST, no commit, invalid performance claim, consumed grant forever including changed evidence root.
- Wrong pin fails before test marker or evidence file exists.
- HTTP 503 at HEAD or BLOCK: no retry, no false contiguous commits, RAW and invalid audit.
- Arbitrary injected constructor is rejected, and both old and new live entrypoints remain permanently denied.
- Mac loaded module-origin check for exact tracked Git code with a synthetic fixture, shadow-import refusal, missing critical module and dirty source SHA refusal.

## Remaining actual D1 exit; avoid fake test inflation

**D1 is NOT approved for live network.** This PR deliberately does not create an executable real HTTPS sender, real permit/nonce or production root. Before live D2 permission could be discussed, a *separately approved* protected Mac CLI/entry must couple the following to **the same reviewed SHA**:
- Codex verified immutable source and actual loaded modules + known Python executable/distro provenance, not just local self-generated hashes;
- an exact user-approved permit/conditions manifest and fixed non-output-derived private registrar, consumed with O_EXCL and file+directory fsync BEFORE any TLS connect;
- one production coordinator enforcing three-slot global actual POST-**attempt** timing, UTC+monotonic caps and HEAD TTL; all budgets on the real connection code; full-response timeout semantics and stop/drain;
- `RESERVE_UNKNOWN` persisted prior to TLS activity, RAW body prior to SETTLE, crash-and-write-failure UNKNOWN; distinguish `request()` call from physical TLS first-byte observable time;
- independent fixed SHA Mac audit of production integration, then distinct user D2 exact bounded permit and distinct D3 single-shot sampling authorization. Neither chat design approval nor Codex code approval alone is a real run permit.

If actual integration cannot satisfy the hard no-paid/no-retry/once/3-slot controls, explicitly report `D1_BLOCKED_AUTHORITY` or `BLOCKED_SOURCE`; do not enable the old consumed real 30-call grant or lower limits silently.

F0 true target remains the 24–48h wallet-signed BUY/SELL source, ordinary Router wallet controls, +60/+300/+900s matched quotes and independent denominator — none can be inferred from fake tests. Historical actual serial throughput 1.045 blocks/s vs sampled BSC HEAD 2.178 blocks/s and synthetic three-slot 1.740 blocks/s are **not** a true provider capacity claim.

**Current:** `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`. NO_NEW_RPC / NO_WS / NO_REAL_PERMIT / NO_REAL_SIGNATURE / NO_MERGE / NO_DEPLOY / NO_TRADES / NO_BACKGROUND.
