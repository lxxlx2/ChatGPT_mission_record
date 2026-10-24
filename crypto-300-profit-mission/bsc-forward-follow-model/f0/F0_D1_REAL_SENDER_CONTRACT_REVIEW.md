# F0 D1: immutable D2/D3 candidate contract at the protected Mac entry

## Reviewed parent

PR #193 at fixed SHA `267f25bb6d0d3e16b53a231d770ac957f2ce6c98`: user-supplied independent Mac verdict `APPROVE_OFFLINE_CODE — D1_MAC_PREVIEW_ENTRY_COMPOSED_TEST_ONLY` (502 full / 141 D1 / 7 separately all PASS, zero SKIPs). Archived [here](https://github.com/lxxlx2/ChatGPT_mission_record/pull/193#issuecomment-6389121419). This approval remains scoped to **mock-only** Mac integration.

## Concrete new mainline increment

The previous code had an actual reviewed **offline** Mac entry but no checkable data model binding a later *real* HTTPS sender to separate exact D2 user/reviewer permit and D3 user **one-shot run** intent. Adding a callable production network transport today would bypass that missing release boundary.

New `f0_l2_d1_real_sender_contract.py` provides a strict, immutable, non-authorizing **candidate** D2/D3 envelope:

- D2 candidate `permit_raw` is parsed with the existing strict field set and local UTC window; changing any bytes changes its SHA256.
- Distinct D3 `one_shot_intent_raw` requires exact field set, 8192-byte cap, duplicate-JSON-field rejection and separate `run_id`, SHA-40 code commit, original D2 permit SHA256, same `grant_id`, and **actual reviewed source manifest SHA256**, taken from the existing checkout preflight. User-supplied manifest is not trusted by itself.
- Fixed destination `https://bsc-dataseed.bnbchain.org`, BSC chain ID 56 and three read-only RPC methods, HTTP-only HTTPS/443 as already scoped, no WS/proxy/redirect/retry/background, free-only, execute-once. The D3 window must match D2 precisely; neither UTC clock nor candidate document alone authenticates an actual user.
- D3 cannot widen D2 totals, head/block budgets, per-request timeout, total dispatch time, head TTL or global concurrency 3. Its send-start gap may only be **larger**. D3 `max_response_bytes` must remain precisely 2,000,000 as the current single coordinator does not enforce a smaller caller-selected RAW limit. Reject values with Python bool/int confusion and incoherent sums.
- Return a **frozen BlockedRealHTTPSBinding** diagnostic: same unique coordinator, cap, fixed endpoint and checked SHA, but `signed_user_intent_verified=False`, `signed_reviewer_d2_verified=False`, `real_https_enabled=False`, `actual_rpc_calls=0`, `D1_BLOCKED_AUTHORITY`, `PRODUCTION_NO_GO`.
- `require_real_sender_release` and `send_live` unconditionally reject regardless of any positional arguments, injected fake trust roots, candidate or environment flags. No D2/D3 live roots are enrolled. No test transport factory can be submitted to this interface.

The *existing* `f0_l2_d1_protected_mac_entry.py` adds `inspect_real_https_sender_candidate_offline`, which **first** performs the native exact SHA, loaded modules, source inventory, active UTC candidate scope and **read-only** fixed production registry preflight, then requires that same preflight to return `D1_BLOCKED_AUTHORITY`, then binds the D3 candidate to the **actual preflight source manifest digest**. The function does not construct a sender, spawn a process, consume marker, write journal or open socket. Existing `rehearse_supervised_mac_entry_offline` still uses the original one hard-stop child and single 3-slot fake coordinator unchanged; existing CLI still accepts `--verify-only` and no `--run`.

## Tests and review scope

`tests/test_f0_l2_d1_real_sender_contract.py`: ten negative/positive diagnostics validating code/D2/D3/source manifest binding, narrower budgets and slower starts, no elevation by mock/injected D2 roots, zero real connection, no registry writes, missing/extra/duplicate fields, time expiry, D3 identity mismatch, fixed response cap, and protected Mac route under synthetic test-only provenance. They are **contract tests, not real HTTP tests**. GitHub CI runs full F0 test discovery. The independent Mac auditor must pin the exact new PR SHA, check all files/blobs/source imports and run complete F0, D1 and the nine tests in isolation. Existing PR193 standalone seven and PR192 two must continue passing.

## Next necessary independent release work — not in this PR

This code is an exact interface and refusal boundary, **not a live sender**. D2 needs independently pinned production trust roots and distinct verified signatures binding permit bytes, SHA, manifest, user and reviewer; D3 needs an independently authenticated exact one-time user execution statement and new one-use nonce, the OS fixed production registry O_EXCL/fsync before real TLS, and no ability to inject a fake roots/path/clock source. Only then may a later code-reviewed release route the existing shared three-slot coordinator's fsynced per-request reservation to the already drafted physical `http.client.HTTPSConnection` code, with global POST pacing, UTC final check, timeout/UNKNOWN and OS process lifecycle. No new scheduler, no default buy amount, no trades or wallet signer.

**No real network call, unapproved production registry write, merge, deployment, service, monitor, email, or scheduled task.** No F0 L1/L2 observations have been obtained. `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`.

**Requested review verdict:** `APPROVE_OFFLINE_CODE — D1_REAL_SENDER_D2_D3_CANDIDATE_CONTRACT_ONLY` on exact new SHA or `REQUEST_CHANGES`; never `PRODUCTION_GO`.
