# F0 D1 orphan-child control: mock-only parent-loss lifecycle

**Frozen approved parent:** PR #191 `8baa185b00c1a69b1caaf46144122b91aafc1a41`, supplied independent Mac verdict `APPROVE_OFFLINE_CODE — D1_ONEUSE_HARD_STOP_TEST_ONLY` (493 full / 132 D1 / 5 isolated, all PASS). [Approval record](https://github.com/lxxlx2/ChatGPT_mission_record/pull/191#issuecomment-6385600295).

## Mainline defect

The previous supervisor used `proc.communicate(timeout=...)` and `proc.kill()`. If the **parent** dies, the mock child can continue its blocking `connect()` without oversight. That is an actual release blocker for any later live read-only runner.

## One bounded repair in existing process module

After the previously reviewed offline grant's O_EXCL + fsync, the parent opens an **anonymous kernel pipe**, passes only its read end to the existing subprocess using `pass_fds`, and retains the single write end. The child validates the inherited read descriptor and starts a daemon watch thread before starting the unchanged PR190 patched HTTPS mock, unique three-slot coordinator and evidence journal. If the parent dies, the kernel closes its write end; the watcher sees EOF and calls `os._exit` even while the child main thread is blocked. A separate child-side monotonic deadline is kept with 0.75 seconds of supervisor-reaping allowance after the parent's hard deadline, so the original supervisor kills/reaps at its requested threshold rather than racing the child watcher.

A private `child_watchdog_termination.json` diagnostic is O_EXCL-created and fsynced before watchdog exit when possible. Such a diagnostic **never proves network requests have settled**; journal reservations remain UNKNOWN on termination, consumed test grant remains spent, and the existing read-only auditor judges performance invalid. If the disk write fails, the child still exits and cannot retry. No public socket, real trust root, production marker, true permit or D2/D3 grant is used.

## Review verification

- New `tests/test_f0_l2_d1_child_lifetime.py`: an actual separate parent process runs a child blocked in patched `connect()` after durable `RESERVE_UNKNOWN`. The test SIGKILLs that parent, checks the watchdog EOF diagnostic, still-UNKNOWN journal, once-marker and refusal to replay with changed output. Also rejects a direct CLI lacking inherited liveness FD.
- Original five tests must still pass, including parent timeout kill and normal six-request accounting.
- Run full F0 unittest suite, focused D1 and the child-lifetime test individually on an independent Mac with reviewed `cryptography==46.0.4`; inspect no real socket or local production registry use. Verify GitHub CI and exact SHA, both source and loaded modules.
- **Known limits:** an anonymous pipe is a process-lifetime signal; this does not prove survival of abrupt hardware power loss, Python interpreter compromise, malicious privileged OS control or a real TLS connection. It does not establish physical POST timings. Death of **both** processes is not evidence of a clean session; durable UNKNOWN rows must remain censored. Parent `SIGSTOP` and blocked scheduling can exceed exact wall targets by watcher grace; production deadlines must be separately reviewed. The child-side thread depends on being scheduled by the OS.

**Approval target:** `APPROVE_OFFLINE_CODE — D1_CHILD_PARENT_LOSS_TEST_ONLY` at a *new fixed SHA*. No prior approval carries automatically.

**Next mainline:** integrate this reviewed lifetime primitive into an independently reviewed **real protected Mac entry** that binds exact D2 scope and separate D3 user intent, immutable code/runtime provenance, fixed OS-home-based one-use marker, per-RID fsync-before-real-TLS-connect, true single 3-slot coordinator, full RAW-before-SETTLE, no retries and a whole-session hard limit. No real network without separate explicit user authorization.

**Gate:** `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`.

## Actual CI for first code SHA

New source SHA `22569efb399ca2eff17953a08c00236bf43e3f14`: [GitHub Actions run 40104487410](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40104487410), job `120903229018`, completed SUCCESS. Decoded log ends with `Ran 495 tests in 66.823s` / `OK`. The actual nested-parent SIGKILL test and direct-CLI guard-denial test were executed. This is Linux CI, **not Mac evidence**. The final child-branch SHA (after documentation-only status updates) requires its own CI readback. No independent Mac approval yet.

## Mac review P1 and narrowly scoped retest

At old SHA `eb6992e96a7663ff03f27531e7a7a6a34bc377cb` the independent Mac reviewer recorded `REQUEST_CHANGES` because standalone `test_supervisor_sigkill_makes_blocked_child_self_exit` raced a zero-length watchdog JSON created with `O_EXCL` before write/fsync. The reviewer also separately verified child EOF and disappearance via `ps`, so the one P1 was **test synchronization**, not proof of a live orphan. Full 495/495 and D1 134/134 passed on that old Mac run, while standalone two tests returned 1 PASS / 1 ERROR. Preserve both outcomes.

New code SHA `9d26aae567a806e8caa416afede6599f2d518512` changes ONLY the standalone test. It collects the actual direct child PID before SIGKILL, polls for a complete parseable diagnostic AND an OS-confirmed terminal child state, and explicitly labels a zombie as exited but awaiting OS reaping. A fixed deadline stops the test on incomplete JSON or still-running child. Existing durable UNKNOWN, once-marker, no-replay and no real network assertions remain. [Linux GitHub CI 40106155306](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/40106155306) completed success with 495/495. **Still required:** independent Mac full, D1, and **isolated two tests**, plus read-only OS process check at the exact new PR HEAD. No approval transfer from the rejected SHA.
