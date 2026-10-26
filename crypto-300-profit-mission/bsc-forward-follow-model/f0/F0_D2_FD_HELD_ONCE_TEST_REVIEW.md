# BSC F0 Issue #207 — held-dirFD O_EXCL one-use rehearsal (DISPOSABLE ONLY)

## Reviewed parent and precise scope

Parent: independently ARM64 Mac-approved PR213 SHA `e351ac98c20e60c9dcc890f2d91aaa22b3885910`, [review report archived](https://github.com/lxxlx2/ChatGPT_mission_record/pull/213#issuecomment-6408822982). Mac full F0 578/578; D1 171; OS-bound registry readonly 10; staged 9; physical HTTPS constructor 16; D2-A/B/C 10/10/7; UTC 4; hard-stop 5; child lifetime 2; zero skip. This parent only inspected directory metadata and never consumed actual production markers.

Issue #207 requires the **single OS-account-fixed production directory FD** to remain bound through future atomic O_EXCL once-grant consumption. This increment implements *exactly one shared atomic marker writer* used by existing D1 disposable registry and a new D2 disposable FD-held rehearsal, with no real human signatures, real production root, network source, sender or execution grant.

## Runtime implementation

**One writer (not a second marker protocol):** `f0_l2_d1_grant._consume_once_using_open_dirfd` is extracted from the existing `OfflineGrantRegistry.consume` implementation. It validates exact grant-ID/raw-permit SHA shapes and fstat on the already-opened **private directory FD** (real OS UID, directory type, group/other mode denied), then creates exactly the same `sha256(grant_id).consumed.json` with `O_CREAT | O_EXCL | O_WRONLY | O_NOFOLLOW`, 0600, writes the same `CONSUMED_OR_UNKNOWN` JSON, fsyncs marker and directory, and reports `CONSUMED_NOT_A_NETWORK_AUTHORIZATION`. Existing `OfflineGrantRegistry.consume` still opens/closes its own directory FD and now invokes this SAME private primitive. No test or code path may clear a spent marker after unexpected exception, fsync uncertainty or timeout; no retry logic.

**New strictly disposable D2 rehearsal:** `f0_l2_d2_fd_held_one_use_offline.rehearse_held_test_registry_once_offline` only operates on an ALREADY CREATED, UID-owned, 0700 direct child of `tempfile.gettempdir().resolve()`, with hard-coded `bsc-f0-once-test-` prefix, no symlinks or alias and not equal/ancestor/descendant to the separately derived real OS-account production path or frozen `PRIVATE_FIXED_REGISTRY`. Path input is explicit only because this is a **TEST, NEVER PRODUCTION** entry. It opens the disposable directory with `O_RDONLY | O_DIRECTORY | O_NOFOLLOW`, compares fstat inode to path lstat before write, holds that *same FD* through the original atomic helper and checks path inode again after fsync. It closes FD on every path. Success returns only `TEST_MARKER_CONSUMED_NOT_PRODUCTION`, `production_marker_consumed=False`, `real_human_authority_verified=False`, `network_requests=0`, `PRODUCTION_NO_GO`. Its `send_live` always denies. This is not a callable production sender.

**Do not overclaim:** a directory can be renamed/replaced by its owner or privileged OS actor between separate processes. Holding a directory FD prevents writes from being silently redirected during the *current* critical section but does not provide durable protection against a malicious owner swapping a new empty directory in for a future run, or deletion of the marker. A post-consume pathname/inode mismatch is a fail-closed `D2_ONCE_TEST_DIR_CHANGED_AFTER_CONSUME`, *not* a proof that marker remains discoverable by name. The true production launcher would require a separately reviewed fixed OS account and ancestor ownership threat model, D2/D3 immutable source/permit authentication, and explicit new user permission before any marker or BSC call.

## New 10 offline tests

`tests/test_f0_l2_d2_fd_held_one_use_offline.py`, only ephemeral `TemporaryDirectory(prefix="bsc-f0-once-test-")`:
1. Valid first TEST one-use consume creates 0600 marker with same hashed filename, digest and old `CONSUMED_OR_UNKNOWN`, zero HTTPS or socket.
2. Same grant ID cannot be reused with the same OR a different permit digest; bytes preserved.
3. Two concurrent attempts to spend same ID yield exactly one winner and one `D1_GRANT_ALREADY_CONSUMED`.
4. Generic/non-disposable path rejected before write.
5. Symlinked disposable-looking path rejected.
6. Mode 0750 rejected before consumption.
7. Test root renamed/replaced after the held FD's real atomic write -> FAIL, original spent marker remains in renamed inode, no apparent success or retry. Clean up both fixture directories.
8. Non-directory opened FD cannot be passed to the shared marker primitive; existing unrelated bytes unchanged.
9. Original D1 `OfflineGrantRegistry.consume` shares the SAME O_EXCL writer: same grant ID cannot be spent via the new test entry after old D1 consumes.
10. Even a positive test marker cannot invoke `send_live`.

No user-supplied production signer roots, no production nonce, no test marker written outside OS temporary directory, no real BSC RPC/WS, trading, background task, merge or deploy.

## Required independent review

Freeze exact SHA and approved PR213 base. Run complete GitHub Linux CI (expected **588** tests, D1 unchanged 171, OS readonly 10, staged 9, physical ctor 16, D2-A/B/C 10/10/7, UTC 4, budgets 4, hard-stop 5, child lifetime 2) then independent ARM64 Mac detached clean SHA review. Verify runtime provenance and every changed file SHA256, unique test IDs, no skips. Independently reproduce O_EXCL race and fd-held rename without using the new test's helper code, and confirm **all marker writes remain inside disposable /tmp**; no production directory ever opened. Check old D1 registry behavior and original coordinator. Also review abrupt `os.fsync` fault semantics: marker must stay UNKNOWN/spent and never be removed/retried.

Possible exact-SHA verdict ONLY `APPROVE_OFFLINE_CODE — D2_SINGLE_FD_HELD_ONCE_TEST_MARKER_ONLY` or `REQUEST_CHANGES`. A test-only FD receipt and a successful 0600 temporary marker are **not production D2/D3 authority**. The independent human identity bindings and OS-fixed production runner are missing.

**HARD STATUS:** `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`.