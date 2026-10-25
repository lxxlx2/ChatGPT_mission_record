# BSC F0 Issue #207 — fixed physical HTTPS response framing in same coordinator (OFFLINE)

**Scope:** improve the existing *actual standard-library HTTPSConnection code site* used today under patched constructors by the **sole D1 three-slot coordinator**. Do not introduce a second scheduler, an executable real source, public live flag, network adapter, signing authority or production marker. This is **one bounded source-code prerequisite**, not completion of Issue #207.

## Pinned inherited source / independent review

Based directly on PR206 exact `68e02323288a1909f6f9c0b6d96d487b9c0a5da5`, independent ARM64 Mac `APPROVE_OFFLINE_CODE — D2C_SIGNED_TEST_PROOF_CLOSED_ADMISSION_ONLY`, full F0 553/553 unique, D1 165, D2-C 7, D2-B 10, D2-A 10, UTC 4, patched physical HTTPS constructor 10, budget 4, hard-stop 5, child lifetime 2. Review archival attribution [PR206 comment 6403827434](https://github.com/lxxlx2/ChatGPT_mission_record/pull/206#issuecomment-6403827434). Previous PRs remain Draft/unmerged and nobody has actual D2/D3 live authority.

[Issue #207 requirements](https://github.com/lxxlx2/ChatGPT_mission_record/issues/207) include bounded HTTP body *and headers*, physically completed vs incomplete RAW integrity and no alternate dispatcher. Existing `f0_l2_d1_concrete_https._review_concrete_https_once` already does fixed HOST:443 verified TLS, one POST, bounded body, pre-connect reservation guard and final mock POST gate. But it previously trusted an unbounded `getheaders()` list and an inconsistent `Content-Length` as long as some bytes were returned, which could mislabel a partial frame `RAW`.

## Bounded transport code changes

Only `f0_l2_d1_concrete_https.py` response metadata handling:
- Explicit 40-header maximum and max 8192 bytes aggregate decoded header name/value representation; forbid control characters in names/values (except a horizontal tab in value), invalid header names, duplicated case-insensitive names and out-of-range status. The Python `http.client` library already has its own parsing limits; these stricter checks still apply to the returned metadata before body-read/RAW acceptance.
- If a `Content-Length` is declared: require decimal ASCII of at most seven digits and length no greater than the already-enforced response body cap, BEFORE attempting to read body. After a bounded read, require exact body-byte count match. A short response or inconsistent declaration is classified FAILED with **no complete RAW**, preserving only optional prefix hash diagnostic. No fabricated response digest or success settlement. Without a `Content-Length`, preserve existing bounded read behavior.
- Complete bounded `Transfer-Encoding` responses are archived with original body bytes and declared **FAILED**, just like complete HTTP 302 or gzip; never parsed RPC OK. No redirect/alternate transport/fallback and no retry. This deliberately does not assert the decoded HTTP library body equals raw TLS on-wire bytes.
- Original `_review_concrete_https_once` test token, permanently rejecting public `send_live`, actual immutable coordinator, three global slots, O_EXCL journal, RAW-before-SETTLE ordering and global final UTC gate are unchanged.

## New independent regression tests

Extend existing `tests/test_f0_l2_d1_physical_ctor_integration.py` with six exact offline tests through `run_fake_concurrent(PatchedConstructorOfflineSource)`, with **`socket.create_connection` patched to throw and `http.client.HTTPSConnection` entirely replaced by the fixture**, all under the original scheduler:

1. Correct complete `Content-Length` preserves normal chain success and RAW archive.
2. Declared too-long response with partial bytes gives only FAILED SETTLE, zero COMMIT, no fabricated `raw_sha256` or RAW.
3. Declared too-short response likewise FAILED with no RAW.
4. Declared oversized body length (>2 MB) rejected before any payload can be accepted, no RAW.
5. Oversized response header (>8 KiB) rejected, no RAW.
6. Complete Transfer-Encoding response has durable 0600 RAW + SHA256 but FAILED SETTLE, no COMMIT.

Previous patched 302/gzip/partial-body failure tests and all D2-A/B/C/UTC/parent-loss tests must still pass. Six new tests imply full F0 **559** and patched physical ctor **16**, if no failures; independently read exact CI job logs rather than claiming PASS now.

## Required exact-SHA review

Compare against the approved PR206 SHA: precisely 2 runtime/test source files plus this review doc and HANDOFF. Independently execute full F0, D1-only, physical ctor, D2-A/B/C and all other critical isolation suites. Inspect actual bytes and fsync order for incomplete vs complete RAW, journal RID RESERVE_UNKNOWN before constructor and SETTLE FAILED with no COMMIT; ensure all slots/gaps still original. On independent Mac ARM64, detached exact code SHA, imported origin provenance, 11 critical modules and cryptography==46.0.4, unique test IDs/zero skips. If Mac not run mark Mac UNVERIFIED.

Verdict ONLY `APPROVE_OFFLINE_CODE — D2_PHYSICAL_HTTPS_RESPONSE_BOUNDARIES_PATCHED_ONLY` or `REQUEST_CHANGES`. Approval has **NO right to call a real RPC**, no production signer trust, no one-use authorization or actual physical source availability. Actual signed physical sender integration within the existing coordinator remains a later separate change/authorization.

**Stop status:** `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`. No real BSC RPC/WS, signer enrollment or real D3 approval, production nonce, old private journal, merge, deployment, background monitoring or trading.
