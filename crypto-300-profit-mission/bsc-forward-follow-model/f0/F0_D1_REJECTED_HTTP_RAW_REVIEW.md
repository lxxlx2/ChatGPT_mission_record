# F0 D1 — preserve bounded HTTP RAW on a rejected concrete response (mock only)

**Frozen independently approved parent:** PR197 `7957a3508bc784be393f11a8b500156251eafde9`, supplied independent Mac `APPROVE_OFFLINE_CODE — D1_CANDIDATE_BUDGET_ENFORCEMENT_TEST_ONLY` (519 unique F0 tests, 158 D1, four new, original three/seven/five/two all PASS). [Independent approval archived](https://github.com/lxxlx2/ChatGPT_mission_record/pull/197#issuecomment-6394611042). No D2/D3 production authority inherited.

## Mainline concrete source -> SAME coordinator accounting

The existing concrete `_review_concrete_https_once` captures a bounded RAW HTTP response (status, headers, body), including **3xx redirects** and HTTP responses flagged for **compressed content**. Those frames are rejected as transport failures, as they must be. But the previously reviewed `PatchedConstructorOfflineSource.reply_over_memory_https` raised on `state != RAW`, silently dropping any complete rejected RAW frame before the existing coordinator's durable `ExclusiveEvidence.settle` writer could archive it.

The changed source **keeps the same fixed HTTPS constructor and one existing coordinator** and now exposes a mock-only `reply_transport_evidence_offline` that returns the complete bounded RAW frame **together with a separate fail classification** when the concrete path rejects it. The legacy `reply_over_memory_https` continues to return only successful frames and raises for a failed transport; direct APIs and all live-sending gates remain disabled.

The existing `GlobalStartGate.run` **does not create a second scheduler**. For the exact test-only patched physical source, it consumes that structured result after original per-RID durable preconnect proof and the same global POST spacing:
- HTTP 302, compressed or otherwise rejected but fully read bounded RAW: worker emits `TRANSPORT_REJECTED_RAW` with original `raw_frame`, not FRAME success.
- Connect, POST or response-read exception with no complete bounded RAW: worker emits `TRANSPORT_FAILED_NO_RAW` with `frame=None`. A partial/oversized read does **not** invent complete RAW bytes.
- The original coordinator completion always marks these cases **FAILED**, archives available bounded RAW **with file+directory fsync before settlement fsync**, then stops the current single run. No chain success or contiguous COMMIT is possible; no automatic retry, no 302 redirect-follow, no decompress.

The existing `ExclusiveEvidence`, `run_fake_concurrent`, hard-stop/parent-loss child, strict D3 cap and production registry modules are unchanged. Test-only constructors still replace `http.client.HTTPSConnection` and socket connections are denied. Real network remains unexecuted.

## Verification checklist

The modified physical constructor test module adds three isolated scenarios:
1. A 302 response is never followed or accepted, but original bounded RAW is archived with SHA256 verified against the SETTLE row; RID/ordering/3-slot limits retained.
2. A response whose headers indicate compression is rejected but complete original RAW bytes are saved with matching digest.
3. A read exception after POST has **no completed RAW**, never invents a SHA/body file, and is settled as a failed/uncertain transport (not a success).

Run full F0, targeted D1, the whole constructor test module isolated (original seven + three = ten), and old hard-stop, parent-loss and candidate-budget tests in an independent Mac detached checkout at the exact new SHA. Verify the change doesn't accidentally treat 302, gzip or read exceptions as valid chain evidence; verify no actual RPC, fixed grant, background tasks, merged code or deployed runner. Inspect journal and original RAW bytes where practical. The distinction **complete rejected RAW versus incomplete/unknown transport** must stay explicit; a failed SETTLE is not a successful RPC or proof of real physical timing.

**Approval target:** `APPROVE_OFFLINE_CODE — D1_REJECTED_HTTP_RAW_DURABLE_FAILURE_ONLY` or `REQUEST_CHANGES` at a pinned new SHA. A passing Linux CI is not equivalent to Mac independent approval. The actual production sender remains unimplemented/unreleased, D2/D3 signed permissions absent.

**`D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`.**
