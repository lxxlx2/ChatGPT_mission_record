# D1: durable receipt before any HTTPS constructor and one child candidate rehearsal

**Approved parent:** PR194 `3470cd841a5b4d0cfc625bd4bf88a2abad37cfb4`, independently Mac reviewed as `APPROVE_OFFLINE_CODE — D1_REAL_SENDER_D2_D3_CANDIDATE_CONTRACT_ONLY` (F0 512/512, D1 151/151, new 10/10, previous 7/7; zero SKIP). [Review archive](https://github.com/lxxlx2/ChatGPT_mission_record/pull/194#issuecomment-6389334567).

## Focused engineering increment

The existing concrete HTTPS routine previously constructed `http.client.HTTPSConnection` **before** calling its coordinator-owned durable reservation guard. Although the standard constructor does not normally connect, a constructor can later change or be patched to perform eager I/O. The single-coordinator `RESERVE_UNKNOWN` journal already fsyncs before handing requests to workers, but defense-in-depth requires the *same RID guard* to pass before any constructor-side I/O is even possible.

The physical call site now invokes the existing `pre_connect_guard(request)` before the HTTPS constructor, and only then executes `HTTPSConnection(HOST, PORT, timeout, verified TLS context)`, `connect()`, same shared global pacing check, `request()`, bounded RAW capture and no retries. The test for a rejected coordinator receipt now explicitly requires **zero constructor invocations** (as well as zero connects) and no unsafe closing behavior. The token to run an offline physical review remains test-only; `send_live()` remains unconditionally disabled. This change is an ordering fix, **not** a new authorization capability.

Separately, the **existing** protected Mac `rehearse_supervised_mac_entry_offline` optionally takes `one_shot_intent_raw` so the approved PR194 D2/D3 candidate envelope is bound to the **same Mac preflight's source SHA, permit byte hash and actual source-manifest digest** **BEFORE** the disposable *TEST* grant marker is consumed. It then invokes the **unchanged PR192 parent-loss/hard-stop child and PR190 single three-slot patched constructor coordinator**, returning the still-blocked candidate diagnostic alongside one observed mock journal. The actual fixed OS-user production registry remains inspected-only. Invalid intent fails before *any* test marker; real network remains entirely forbidden.

New `tests/test_f0_l2_d1_bound_wire_rehearsal.py` covers successful one-path candidate -> preflight -> 6 reservations / 6 settlements / durable RAW, 3-slot accounting and no replay; invalid candidate -> no disposable marker; and hang after RESERVED -> parent SIGKILL with UNKNOWN[1] / zero SETTLE, no production mutations. Existing physical-constructor test has updated ordering expectation.

## Limits and independent review

This is **not a live transport**. Existing production keys for D2 and signed D3 one-shot authority are still missing. Code deliberately cannot enable a real socket or consume a fixed production nonce. Unit tests patch the HTTPS constructor and allow no real RPC/WS. Real sender admission into the **same** one coordinator must be developed in a future exact-SHA audited commit *after* distinct-role trust roots / separate user D3 execution and immutable Mac runtime release prerequisites are independently reviewed; avoid creating a second coordinator or unsupported source type.

Mac reviewer: verify fixed child PR SHA/base and four changed paths (including docs), actual imports; test full F0, focused D1, **new three tests isolated**, and `test_f0_l2_d1_physical_ctor_integration.py` 7 isolated. Independently simulate a constructor with eager side effects and a refused preconnect reservation, verify zero ctor, zero socket and journal unchanged, plus normal and hard-stop child. Confirm neither simulated preflight nor unsigned candidate can activate network, no production/private root reads, no merge/deploy/service/trades.

**Verdict target:** `APPROVE_OFFLINE_CODE — D1_PRECONSTRUCTOR_RECEIPT_BOUND_REHEARSAL_ONLY` at exact new SHA, or `REQUEST_CHANGES`. No D2/D3 approval or F0 stage promotion.

**`D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`.**
