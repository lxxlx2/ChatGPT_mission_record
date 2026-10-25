# F0 D1 — D3 candidate UTC check at the last simulated POST (NO LIVE)

**Approved parent:** PR #198 fixed `ee8528fb7de98efd40de3ac5035dc29a56cf644b`, independently Mac approved `APPROVE_OFFLINE_CODE — D1_REJECTED_HTTP_RAW_DURABLE_FAILURE_ONLY` (522 full unique, 161 D1, 10 physical ctor, 4 budgets, 5 hard-stop, 2 child-lifetime PASS). Reviewer attribution and evidence archived in [PR198](https://github.com/lxxlx2/ChatGPT_mission_record/pull/198#issuecomment-6394745053). This child requires separate pinned-SHA Mac review.

## Missing last-moment gate in the same protected transport path

The reviewed PR197 enforced D3 maximum request count, shared 3-slot POST spacing and timeouts in the existing child. PR198 guaranteed rejected-complete RAW is durably written even on a FAILED response. One remaining issue: a D3 window checked at *parent preflight* could expire **after mock TLS / the shared POST-spacing wait**. The sole coordinator already supports a test-only `OfflinePostUTCWindow.check_at_fake_post()` *after the spacing lock and just before the in-memory POST*, but PR198's protected OS child wasn't passing its approved candidate's UTC window into that existing hook.

## Narrow new source code

- The current protected Mac `rehearse_supervised_mac_entry_offline` takes the already checked **same exact D3 candidate** and embeds only its UTC start/end, original Mac preflight observed UTC instant, matching original D2 permit-byte SHA and pinned reviewed source SHA into the existing bounded eight-key test scope as one strictly nested `post_utc` object.
- The existing `run_bounded_offline_once` validates that sealed nested field **before consuming any disposable O_EXCL test grant**, checks its exact digest against its permit digest and revalidates in the **same** child. The default no-candidate nine-argv workflow and original lifecycle/hard stop stay unchanged.
- The child uses a clearly **virtual offline clock** anchored to the already checked Mac preflight instant plus the child's monotonic elapsed duration. This allows deterministic tests with historic candidate fixture dates. It is **NOT** an authoritative wall clock, user signature or real time. The new `OfflinePostUTCWindow.from_prevalidated_child_scope()` sets up the already existing exact `OfflinePostUTCWindow` type for the **single, unchanged `GlobalStartGate.run`** to invoke at each fake POST, after fake TLS and global delay; it still rejects rollback/expiry/invalid request.
- If the UTC candidate expires after a request's durable RESERVE but before fake POST, the original coordinator durably SETTLEs it FAILED / `PRESTART_OFFLINE_PERMIT_UTC_DENIED`, with **zero** started POST, no RAW and no COMMIT. This is an expected handled denial (not evidence of an actual network POST). On a parent-kill during a blocked mock connect, UNKNOWN/one-use and no retry remain unchanged.

## Coverage, independent acceptance

New `tests/test_f0_l2_d1_candidate_post_utc_child.py` covers: a good bound D3 candidate produces one UTC final check for **every** actual mock POST (not just parent preflight); a narrowly expired window yields RESERVE, no fake POST, FAILED SETTLE and no RAW/COMMIT; malformed/digest-mismatched or invalid checked UTC scope consumes **no** test grant and launches no child.

Review changed modules `f0_l2_d1_post_utc.py`, `f0_l2_d1_hard_stop_once.py`, `f0_l2_d1_protected_mac_entry.py`, new tests and docs at exact SHA. Run full F0, D1 filtered, three new tests separately and prior 10 physical ctor, four budget, hard-stop five/child-lifetime two. On independent Mac detached checkout re-run a real OS child with a historical synthetic candidate and verify the journal, outgoing mock start list, terminal state and marker. Confirm original real `http.client.HTTPSConnection` and socket network remain **forbidden**, fixed production registry never touched, no extra coordinator or background task. UTC here uses a **virtual replay clock**, not a validated live clock or actual HTTPS dispatch.

**Only possible new verdict:** `APPROVE_OFFLINE_CODE — D1_CHILD_FINAL_FAKE_POST_UTC_ONLY` or `REQUEST_CHANGES`. No D2 signed user+reviewer authority, distinct signed D3 human one-shot, real sender release or live provider tests have occurred. `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`.


## Actual first CI failure, narrow correction and raw evidence

The first child SHA `0fbb1b382de0d317f783b462a2e142f06a9f5bfc` [GitHub CI 40172389195](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40172389195) **FAILED**: `Ran 525 tests`, **5 ERROR**, all rooted in `ValueError: D1_UTC_REQUIRED`. The native Mac preflight's `checked_at_utc` diagnostic uses `datetime.isoformat()` with `+00:00`, while the reviewed scope helper `parse_utc_timestamp` intentionally only accepts trailing `Z`. No safety gate failed open, and the failed original CI evidence must not be replaced or deleted.

At source fix SHA `9cafafcd7a8198a9bec9bbd7e49094a82a4f823d`, only `f0_l2_d1_protected_mac_entry.py` is changed: parse the already checked native ISO instant and strictly require UTC offset, then normalize `+00:00` to `Z` before the child scope. The original strict parser and unique coordinator are unchanged.

[GitHub CI 40172532590](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40172532590), job `121106218864`, **completed SUCCESS**, decoded original log: `Ran 525 tests in 78.276s / OK`. Three new candidate-final-POST tests all explicitly PASS. This is Linux only; a later document-only HEAD and independent Mac approval still require their own verification. No real network was involved.


## Independent source-level review correction after initial passing PR199 SHA

Frozen initial PR199 SHA `6859a497de0d7d34aa122e6325dfc9245786e604` had GitHub Linux 525/525 PASS, but further independent source-level inspection found a missing **pre-test-marker rejection**: `_validate_offline_scope()` accepted an explicitly present `"post_utc": null` because it checked the nested value only when `utc is not None`. The parent then irreversibly consumed a disposable TEST one-shot marker; only the child detected `scope["post_utc"]` as None and failed. This violates the promise that malformed candidate timing metadata is rejected *before* consuming a marker. It is an OFFLINE test grant issue, not proof of live dispatch.

The reviewer recorded `REQUEST_CHANGES` on that exact old SHA in [PR199 review comment](https://github.com/lxxlx2/ChatGPT_mission_record/pull/199#issuecomment-6395015358). Source correction `50b0531a3ec19c5b37cb19b235606fa63c212fb1` changes only the nested-field validation: if `post_utc` is present it **must** be an exact five-field dictionary; absent field still preserves legacy no-candidate workflows. Invalid values are rejected before the parent writes or fsyncs an O_EXCL test lease. Test correction `853ddf4c7a267ad16890644f25e6fe11f6c3650b` covers an explicit `null` with registry and evidence both still empty.

The same test SHA adds a separate mid-pacing expiry case, closing another test gap: with a synthetic window ending 500ms after the child virtual anchor and global 700ms fake POST spacing, the first `eth_chainId` fake POST is recorded, but the following `eth_blockNumber` reservation is durably settled FAILED without a second fake POST, response RAW or contiguous COMMIT. This checks the precise regression risk *during pacing*, not merely expiry before the very first POST.

**Important:** The initial old-SHA `APPROVE_OFFLINE_CODE` conclusion was never given; the 525/525 GitHub CI had missing edge coverage. Independent Mac approval requires re-running tests and verifying the new final exact HEAD and the old `REQUEST_CHANGES` remains scoped to the old SHA. No native Mac test by the source-level commenter; the environment remains offline, no real source, no D2/D3 authority or production permit.
