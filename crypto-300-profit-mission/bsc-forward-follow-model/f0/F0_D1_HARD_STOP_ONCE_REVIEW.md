# F0 D1: OS-level hard process deadline for one-use offline HTTPS-call rehearsal

Parent reviewed source: PR190 `30642f27c1d647ff2d961cd3ce18397b3a07dae0`, independent supplied Mac verdict `APPROVE_OFFLINE_CODE — D1_PATCHED_PHYSICAL_CTOR_INTEGRATION_SCOPE_ONLY`, archived [here](https://github.com/lxxlx2/ChatGPT_mission_record/pull/190#issuecomment-6383757461).

## Mainline value and exact boundary

Previous D1 runtime used a 60-second dispatch limit and per-call <=5-second timeout; a blocked call or unbounded drain could leave the *whole operation* exceeding the intended permission envelope. This child closes one part of that release blocker **only in a test-only OS child**: `f0_l2_d1_hard_stop_once.py` spends an irreversible disposable `OfflineGrantRegistry` marker in the parent **before** launching the child, then uses `subprocess.Popen(...).communicate(timeout=...)`, kill and reap on a hard time limit.

The child uses PR190's exact `PatchedConstructorOfflineSource` class, patched `HTTPSConnection` constructor, `socket.create_connection` denial, and the unchanged single three-slot `run_fake_concurrent` for shared pacing, per-RID `RESERVE_UNKNOWN` flush/fsync before mock connect, RAW-before-SETTLE and no retry. After child exit or kill, parent invokes the existing read-only `reconcile_saved_attempts` auditor. On timeout, reservations without settlement remain UNKNOWN and **INVALID_FOR_PERFORMANCE_CLAIM**. The original grant stays spent and does not reset if an output path changes.

The test registry and evidence roots must be preexisting private 0700 directories under the canonical OS temporary root, separate from each other and the fixed Mac production registry. The test parent has no actual permit, signing, trusted D2/D3 grant, or real network sender. Its public `send_live()` unconditionally denies.

## Review and stop

- Tests in `tests/test_f0_l2_d1_hard_stop_once.py` demonstrate successful one-use bounded offline run, irreversible marker replay prevention, real child kill while its patched `connect()` deliberately sleeps after a durable reservation, INVALID audit/UNKNOWN preservation, strict preflight rejection of invalid paths/parameters, and prohibition of real entry.
- Run the entire F0 test suite and focused D1 and new 5 tests at exact child SHA. Do not treat GitHub Linux CI as independent Mac approval. Verify source imports, zero real sockets, grant consumption ordering, no child retry, and no automatic resumption.
- **Incomplete:** This is an actual OS hard-stop mechanism but still TEST-ONLY. Integrating it into a **real** supervised Mac run requires a separate independently reviewed release binding the exact user D2 scope, D3 user run permission, fixed OS-home production grant marker before any TLS connect, real HTTPS/three-slot coordinator, same-session hard cap, all failure evidence and explicit stop. A real OS SIGKILL is not proof of hardware power-loss durability. No new RPC/WS can be sent by this code as configured.
- This is a bounded hard-deadline implementation, not L1/L2 or F0 feasibility PASS. No project merge, deployment, automation, alerts, wallet signing or trading.

Current `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`.
