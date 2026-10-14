# Frank A05-R1 PR #59 external review: R1/R2 transport gate remediation

Date: 2026-10-14 (Asia/Bangkok)

Status: `EXTERNAL_REQUEST_CHANGES / CHILD_FIX_CODE_SUBMITTED / NEW_EXACT_SHA_CI_AND_INDEPENDENT_REVIEW_REQUIRED / REAL_SOURCE_UNVERIFIED / NO_MERGE / NO_DEPLOY`.

## Verified review conflict and acceptance decision

PR #59 fixed audited source SHA: `9b6f7a90fe92ae6eea497d364ebc7f9bf109f042` (parent PR #58 `063e8bada37534c13e801ea6f63e97d8f5586f4b`). The user supplied two independent external review reports: GPT-6.1 Sol `REQUEST_CHANGES` with real socket HTTP/TLS reproductions of two P2 source-provenance bugs; Gemini 3.8 `APPROVE` after synthetic/baseline tests but without exercising these HTTP transport failures. The concrete reproduced blocking findings prevail; do not promote the old SHA to code approved.

- **R1 / P2 HTTPS-to-HTTP redirect downgrade:** Default `urllib.request.urlopen` follows HTTPS 302 to HTTP as GET. Redirected cleartext but parseable JSON-RPC bodies could be stored as fully verified token-account sources, including isolated Sidecar import.
- **R2 / P2 short HTTP entity:** `response.read(MAX+1)` may return less than server-declared `Content-Length`, even if received bytes form complete valid JSON. Offline hash/replay cannot attest the missing HTTP entity bytes. Aborted chunked framing is also a fail-closed transport source.
- Gemini's symlink/`/tmp` observations and JSON-RPC version strictness are nonblocking follow-ups; no unrelated up/downstream rewrite for this fix.

## Scoped child implementation

Child branch: `fix/frank-a05-rpc-transport-integrity-20261014` from frozen PR #59 SHA.

- Only the new standalone `scripts/frank_capture_owner_full_receipts.py` wire RPC opener is changed. All redirects are explicitly refused (preserving HTTPS origin and POST RPC semantics); HTTP 200 enforced. A single well-formed bounded `Content-Length` must match actual bytes; conflicting length/transfer encoding metadata, declared oversize and incomplete chunked HTTP entity fail closed. Transport exceptions are presented without leaking RPC URLs.
- Five real-socket local TLS/HTTP tests added to `test_frank_a05_complete_rpc_receipts.py`: valid direct HTTPS dual responses; blocked HTTPS 302 → HTTP; parseable JSON with declared length greater than sent body; missing terminating chunk; declared oversize with short sent body. Rejection yields `PARTIAL_SOURCE`, no full snapshot and no accepted offline replay.
- A05 module and disposable combined F01/C02 GitHub workflows are enabled for the child branch; retain exact-SHA verification. A standalone local Python HTTPS/HTTP socket harness passed `1 passed` before pushing, but **this is not a substitute for source branch CI, in-repo test results or independent re-review**.
- The parent approved normalizer/inventory, immutable Sidecar, frozen Frank V1 strategy, Gmail, LaunchAgents, protected SQLite and Mac production runtime are untouched.

## Remaining mandatory gates

1. Verify the child branch exact HEAD and both GitHub Actions workflow conclusions. Preserve any failures and fixes rather than attributing an older green SHA to a newer one.
2. Independent another-AI re-review **new child exact SHA**; must reproduce R1/R2, check complete HTTP response preservation on true TLS and any upstream/downstream compatibility change. Verdict `APPROVE` or `REQUEST_CHANGES` with auditable reproduction. Prior Gemini APPROVE applies to old SHA only.
3. After code approval, manually capture full actual finalized SPL and Token-2022 Frank owner RPC receipts through an authorized bounded source; then reconcile the authoritative historic 32 target Mints, all live token accounts, previously closed account history, and follow prescribed F02 API → UI → Mac isolation → cross-module integration review → final overall review. No current count, wallet value, cost, PnL or sale event inferred from synthetic tests.

**NO_MERGE / NO_DEPLOY / NO_TRADES / NO_GMAIL / NO_PRODUCTION_SQLITE_WRITE / NO_AUTOMATION**.
