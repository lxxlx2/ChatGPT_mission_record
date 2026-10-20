# F0 L1 — bounded injected full-block collection + durable pre-send journal

**Status:** `OFFLINE_INJECTION_CODE / UNREVIEWED_COMBINED_AND_NEW_CODE / NO_NETWORK_AUTHORIZATION / NO_RUN`.

Base is the unreviewed PR #144 *combined* HEAD. That combination itself carries two independent sibling approvals: PR141 fixed SHA `d71459915b3ea78e1e1660aa97ed0e5472ce7454` (218/218 zero skip) and PR143 fixed SHA `8d372eeba9e178bae4d4a7578d0657b8351528c3` (219/219 zero skip). Their union is not independently approved until 224/224 zero skip in a full checkout. This PR adds **6 new tests**, making **230 EXPECTED**, not yet observed; no claim of test execution in this GitHub authoring environment.

## Exactly what is implemented

`f0_l1_injected_capture.capture_injected_blocks()` is a **Python library function requiring an externally passed sender and UTC/monotonic clocks**. No RPC endpoint, HTTP/WS client, live CLI, credentials, background scheduler, retry loop, running clock event loop or valid permit exists here. The tests inject a fake sender only. An external caller can provide an unsafe sender — **this helper is not a permission or a validated live network runner**, and must not be wired to one until its implementation and actual permit pass a separate review and fresh explicit user authorization.

The helper strictly binds exact Git blobs for real PR116 20 PRIMARY cohort and documented 2 Pancake Router addresses *before attempting to invoke sender*. For a fully bounded integer height interval (up to the existing 512-row offline window cap) it composes `eth_getBlockByNumber([height, true])` JSON-RPC requests using injected sender. A fake sender can raise TimeoutError or return saved JSON-RPC full block; all results feed the **existing `f0_l1_window.offline_window`** and `f0_rpc_adapter.block_candidates` parser. The watch signer and ordinary non-watch Router-address candidates share each observed block and the unchanged PR116 FNV seed.

Before **every injected sender invocation** the helper fsyncs `journal.json` through PR136's `atomic_json`, recording the request ID, height, method, parameters, supplied UTC+monotonic clock and `ATTEMPTED_OUTCOME_UNKNOWN`. On return it writes a final `RPC_RESPONSE` or sanitized `FAILED` classification/response digest, without raw RPC response or error text in the saved journal. An uncaught `KeyboardInterrupt` deliberately preserves the UNKNOWN row; no automatic retry. The journal is always separate from fixed `report.json`, and neither may already exist at startup.

The injected sender is bounded by `max_calls`, `start_height/end_height`, and a consecutive-error limit; unattempted heights remain in the full planned-height denominator as `MISSING_NOT_ATTEMPTED`. Main/offline control eligibility is always false. The report labels both `actual_rpc_calls=0` **for this pure library** and `first_seen_source=INJECTED_CLOCK_NOT_REAL`, never a true public first-seen, E1/E2/E3/PnL or quote. `provider_billed=UNVERIFIED` remains. A Python callback is arbitrary code, so `actual_rpc_calls=0` must NEVER be cited as a guarantee about a caller-supplied sender; it is true only for the provided fakes and the fact that this module itself has no socket implementation.

Malformed saved RPC responses are counted as FAILED; if the reused verified offline ledger rejects conflicting saved block identity/parentage the helper writes a `INJECTED_SAVED_PARSER_REJECTED` report and retains the separate journal for audit rather than promoting bad blocks to controls.

## Specific offline test cases

`tests/test_f0_l1_injected_capture.py` adds six fake-sender tests:
1. Five-height injected plan (three synthetic saved full-block responses, two timeouts); all five entries persisted **BEFORE fake sends**; 3 frozen signer and 3 ordinary Router-address candidate hits from the same blocks, no control eligibility, two failures, zero real RPC.
2. Call cap at 3 yields 3 attempted / 2 missing heights, no backfill or phantom source response.
3. Wrong response IDs count as failed attempts; consecutive-error stop; never log fake secret.
4. Simulated `KeyboardInterrupt` leaves exactly one `ATTEMPTED_OUTCOME_UNKNOWN` row and no fabricated final report.
5. `--report` role collision (journal path == report path) fails with zero fake sends, zero files.
6. A mutated Router registry byte is rejected before journal creation and sender callback invocation.

**All tests require a FULL checkout with actual raw PR116 manifest and official Router registry.** The authoring session has created these tests, not executed the new suite; independent reviewer MUST run 230/230 tests, ZERO SKIP, from the full combined branch and verify the source/fixture exact blobs. Treat any failure as REQUEST_CHANGES, not as a reason to bypass the failing test or rewrite reviewed history.

## What remains for a real short-window L1

A future independently reviewed **real HTTP or WS source driver** must choose / attest chain identity, fresh start head, bounded 2-minute UTC interval, actual first response and first visible timestamps, max total requests, max Router discovery budget, source rate and free quota, stop/finality and independent gap verification. Under official ~0.45s nominal BSC blocks, 120 sec is ~267 heights plus head/identity/receipt requests, and a serial fake-sender library does **not** prove this network throughput. No live capture, first-seen claim, Router swap causality, E1/E2/E3, +60/+300/+900 quotes or paper profit has been approved or measured.

**Both earlier single-use grants (old 4-call smoke, later 24-call code-at-height) are exhausted.** This PR does not create permission to send any further request, receive WS events, trade, sign, merge, deploy or notify.
