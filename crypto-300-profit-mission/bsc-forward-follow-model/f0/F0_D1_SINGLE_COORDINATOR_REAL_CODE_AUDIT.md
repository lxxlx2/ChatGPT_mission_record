# PR #188 — one coordinator with unreleased real HTTPS code, OFFLINE REVIEW ONLY

## Approved baseline and original F0 goal

Parent PR #187 frozen SHA `23f41ea2f984cb652cc07bbf28d9366d18b61701`, independently Mac-approved as `APPROVE_OFFLINE_CODE — D1_MAC_PROTECTED_PREFLIGHT_SCOPE_ONLY`: 481/481 full, **120/120 focused D1**, eight new tests, zero SKIP; 173 F0 tracked files and 11 critical loaded modules in a real Mac detached checkout. This parent remains unchanged.

F0’s business purpose has **not changed**: decide whether free public BSC source can keep up with live wallet-signed BUY/SELL, a concurrent ordinary Router wallet control group, +60/+300/+900s quotes and a reconstructable missed-event denominator. This is not live research evidence. Historical finite serial rate 1.045 blocks/s vs same sampled source 2.178 bps, and a hypothetical fake three-slot 1.740 bps, are insufficient to claim real catch-up.

## Concrete D1 code work

This child does **not add another independent scheduler**. It factors the existing tested three-slot `run_fake_concurrent()` into a **single shared core** `_run_single_coordinator()`, preserving fake callers’ public API and denying all real types through that public fake wrapper. The core retains original:
- method whitelist CHAIN, HEAD and BLOCK; coordinator-generated monotonic integer request IDs;
- combined <=32 attempts, <=24 BLOCK, <=6 refreshes; exactly 3 workers, global >=250ms *observed attempt-call* gap, HEAD TTL and dispatch cap;
- exclusive fsynced `RESERVE_UNKNOWN` per id **before worker is submitted**; caller-scoped marker must be consumed *before core starts*; raw bytes+directory fsync before SETTLE and original request ID bound to contiguous commit;
- no retry, no unknown-to-success conversion, no false completion under HTTP503 or POST-write failure; read-only recovery audits remain unchanged.

`UnreleasedRealHTTPSCodeSource` is an **unreleased code-audit adapter** whose implementation calls the PR182 concrete `_review_concrete_https_once()` containing the genuine `http.client.HTTPSConnection` constructor, TLS hostname verification and fixed host/443, not just a new mock HTTP parser. The shared coordinator’s global gate is called **after** mocked TLS connect and before each attempted POST. The adapter is exact class only; the regular `run_fake_concurrent()` does not accept it.

The private `_review_unreleased_real_concurrent()` is the only code-audit path, with an explicit **temporary test** `OfflineGrantRegistry` that atomically creates and fsyncs a one-use marker BEFORE invoking the shared coordinator. It checks the actual `http.client.HTTPSConnection` object has been monkeypatched in the current process **BEFORE grant consumption**. The source checks again immediately before invoking the concrete HTTPS function. Tests supply a constructor returning a memory-only response, which records the consumed marker and checks the **matching request ID** was already durably reserved at TLS connect time. Both absence of the interception and absence of the test registry fail before network, grant consumption and evidence.

Important security boundary: the internal review ticket and Python monkeypatch are **NOT a production authentication system**. The private code must NEVER run with a real socket; a Python caller controlling the interpreter can alter the patch. The real public `send_live()` functions in all modules remain unconditional DENY. `_review_unreleased_real_concurrent()` also reports `network_requests=None` and `synthetic_source_growth_bps=None` because a code path that normally reaches an actual constructor has not established any independently measurable live-network fact. `physically_started_fake` is a legacy counter name from the shared coordinator; for this review it means *method-call attempt*, **not physical TLS byte transmission**. This PR does NOT finish actual sender startup or D1.

## Focused offline regression and Mac review

New `tests/test_f0_l2_d1_unreleased_real_wiring.py` (seven tests) exercises:
1. one shared coordinator with test marker and each request’s fsynced `RESERVE_UNKNOWN` present on connect, RAW and settlement/recovery ledger, 3-slot/250ms attempt-call control and no performance claims;
2. HTTP503 HEAD raw evidence and zero false commits, no HEAD retry;
3. POST write exception = uncertain failure, original method budget spent, zero false commits, no retry;
4. public fake entry rejects real-type source, public `send_live` refuses;
5. temporary O_EXCL/fsynced marker cannot be refunded by changing output or permit digest;
6. unpatched actual `HTTPSConnection` constructor is denied even with importable test ticket;
7. absent temporary registry prevents any network connection.

All test HTTP constructors must be intercepted before execution; **real socket, RPC or WS requests = 0**. This is a bounded integration test for previously missing sender-to-single-coordinator **code** wiring. The independently approved PR187 Mac `--verify-only` and actual production registrar remain unchanged.

## Still required before D1 exit

The **real protected launch** is not this private fake-test entry. A further independently reviewed SHA must enforce the approved PR185 user+Codex supervised model: exact user-approved scope and Codex-checked loaded Mac bytes, fixed OS-account-home production O_EXCL/fsync marker, identical whole-request `RESERVE_UNKNOWN` before the **real** TLS connect, shared POST attempt limiter/UTC/HEAD TTL and strict deadline, actual durable RAW-before-SETTLE/UNKNOWN on OS or socket failure. No caller-provided monkeypatch, test token, adjustable once-root or test-signed permit can enable a real connection. In particular, a Python `request()` call timestamp cannot prove physical first-byte send, and 5s per-operation socket timeout does not prove a 5s absolute whole-call deadline.

Only a future independent D1 code review can consider closing D1. **D2** requires explicit new exact per-run user permit and independently reviewed scope, and **D3** requires distinct user approval to start ONE bounded actual trial. All earlier 30 authorized real calls are spent. The 24–48h F0 source, control group and quotes require additional distinct evidence/approval after the short capacity experiment. NO_MERGE / NO_DEPLOY / NO_NEW_RPC / NO_WS / NO_TRADES / NO_BACKGROUND.

**State:** `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`.
