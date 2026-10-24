# F0 D1: protected Mac preflight bound to one offline HTTPS child

**Reviewed parent:** PR #192 `dee62174d382654fa89042c72ad62fd0ddd5eb2d`, supplied independent Mac `APPROVE_OFFLINE_CODE — D1_CHILD_PARENT_LOSS_TEST_ONLY` with full 495/495, D1 134/134 and isolated 2/2 PASS. [Archived approved report](https://github.com/lxxlx2/ChatGPT_mission_record/pull/192#issuecomment-6388944759). Old SHA `eb6992e96a7663ff03f27531e7a7a6a34bc377cb` remains REQUEST_CHANGES.

## One actual integration step, no parallel scheduler

`rehearse_supervised_mac_entry_offline(...)` has been added to the **existing** `f0_l2_d1_protected_mac_entry.py`, not a new competing entrypoint. It composes, in order:

1. Before any marker or subprocess, reject released/D2/D3 release constants, invalid or non-test grant identity, invalid deadline and unsafe path shape. The standard `send_live()` remains an unconditional failure.
2. Run the existing macOS-only `inspect_supervised_mac_scope_offline()` for immutable checkout/loaded source provenance, strict candidate UTC scope and **read-only** inspection of the user-account-fixed private production grant path. Reject incorrect HEAD, expired candidate scope and non-private evidence before any test marker.
3. Require its explicit `D1_BLOCKED_AUTHORITY` result and cap hard-stop seconds to the validated candidate dispatch ceiling. Never convert this candidate into a D2 permit or D3 instruction. Deny any shared/ancestor/descendant root between inspected Mac evidence and disposable test roots.
4. Call the **unchanged** one-use test-only `run_bounded_offline_once` from PR #192 using a disposable registry and test evidence directory under the canonical OS temp root. Its parent consumes an O_EXCL+fsync TEST marker before launching exactly one protected child; the same child reuses PR #190's test-patched physical `HTTPSConnection` call site, per-RID durable RESERVE proof before mock TLS connect, single 3-slot coordinator, paced fake POST, RAW/SETTLE and no replay. PR #191 hard process cap and PR #192 inherited-pipe orphan child watchdog remain unmodified.
5. Return one structured result that keeps inspected code SHA and candidate bytes hash attached to the exact test-run summary, plus explicit zero real requests, no D2/D3, fixed production marker **not consumed**, `D1_BLOCKED_AUTHORITY / PRODUCTION_NO_GO`.

No live source type is introduced to the coordinator. No true sender source can be instantiated via this path. No new run/serve/daemon CLI mode was added. There is still only one single coordinator, the unchanged fake one.

## Tests and independent review acceptance

`tests/test_f0_l2_d1_mac_entry_binding.py` covers full preflight -> mock OS parent/child success, immutable source/candidate digest binding, real 3-slot accounting; duplicate test grant refusal, incorrect code SHA rejected before any test marker, test root cannot overlap inspected production/evidence roots, forbidden release constants, explicit send_live denial, child mock connect hang -> parent SIGKILL / UNKNOWN / spent once marker, and invalid deadline. Tests run only against synthetic transport; macOS-specific platform and reviewed checkout origins are mocked **in CI tests**, and must be verified independently from real Mac in separate review.

Independent Mac reviewer must pin this child HEAD, inspect all diffs/source blobs, check native `cryptography==46.0.4` and loaded critical origins in real frozen checkout, execute full F0 unittest, focused D1 and isolated 7 binding tests, then independently validate full one-process rehearsal with an ephemeral candidate permit and disposable registry. Verify no real BSC socket/RPC or original user's private evidence used. If an actual native preflight is tested, the candidate's scope window must be explicitly synthetic and actively valid only for that test; this is not D2. Never create real user approvals or consume a production marker.

## Remaining release blockers

- Real HTTPS source still has no approved `run_live`; `send_live()` remains unconditional deny. A protected **live** implementation must join reviewed D2 exact user scope, independently D3 approved one-time run, fixed OS-home grant before first socket/connect, per-request durable reserve before TLS, one global three-slot scheduler and global POST pacing, verified real sender under one child-lifetime and session watchdog, physical failure-UNKNOWN handling. Live free-provider performance is untested. Passing this integration confirms only **mock transport whole-path composition**.
- No network, background service, deployment, merge, trade, asset or alert activity is authorized.

**Approval target:** `APPROVE_OFFLINE_CODE — D1_MAC_PREVIEW_ENTRY_COMPOSED_TEST_ONLY` at an independently verified exact new SHA. Otherwise `REQUEST_CHANGES`. Parent approval does not carry to the child automatically.

`D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`.
