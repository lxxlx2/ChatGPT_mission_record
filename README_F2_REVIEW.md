# Frank F2 Dashboard-only one-shot adapter — offline candidate

**Status: MAC_OFFLINE_ADAPTER_CHECKED / DRAFT_REVIEW_ONLY / C2A_RELEASE_NOT_READY**

This is an isolated candidate for F2 review, not a runnable production release package.
It contains a real OS bounded stdout/stderr reader, real atomic runner replacement,
a concrete `MacDashboardLifecycle` for a future, separately authorized one-shot use,
a fail-closed recovery controller, and offline unit/integration tests. It has **no CLI**
and **no auto-execution**. Importing it does nothing.

## Fixed upstream product provenance

- Approved product code: `296f35a8b6dffe1b2384f77b8768aa799a68ed0d` (PR #220).
- Old installed source reference: `914e9e47fed2e60bc24690fcb083413a64d4e681`.
- Existing G1 physical candidate and rollback-source manifests are **not** modified by this zip; release artifacts and runtime must be verified independently again before actual cutover.
- F2 old executor review: Issue #165, comment #6431680608. The local old 78-line executor was NOT available here, so no assertion of an exact patch or deployment compatibility is made.

## Local tests ONLY

Run from `crypto-300-profit-mission/local-agent/`:

`python3 -B -m unittest -v tests/test_frank_c2a_f2_one_shot.py`

The tests create disposable temp runner files, use injected fake lifecycle/probe, and run ONLY harmless Python subprocesses for real bounded pipe capture, output truncation, timeout and inherited-pipe descendant cleanup. No launchctl, network, endpoint, CA POST, or real Mac server. `authorized=True` in tests is only to exercise synthetic temporary fixtures and **not** real-life authorization. Do not run this test suite from inside a live production release script.

## Independent-review blockers before production

1. This candidate is NOT connected to the old 78-line local executor, actual production startup wrapper, G1 source manifest or rollback mapping; a Mac operator must verify exact integration without bootout/bootstrap before considering live use. `MacDashboardLifecycle` is real but its construction/calls must remain prohibited until explicit one-use authorization.
2. `execute_once` trusts a caller-supplied independent `probe()` for true G0, G3 and G4 identity and protected Loop/V1/D2/notification invariants; such a Mac probe is not included. It cannot truthfully claim real source/port health without it. The `authorized` boolean is an API precondition, **not user authentication**.
3. Real Mac launchctl behavior, actual plist environment, file ACLs/quarantine, physical 8766 listener and old-runtime recovery remain unverified. `S0_PASS` and `G1_PASS` do not cover this.
4. Unknown historical first bootstrap error (`F0_READONLY_UNRESOLVED`) must be explicitly risk accepted or deferred. The absence of original rc/stderr cannot be fixed retroactively.
5. Uncatchable SIGKILL, hard power loss, OOM, inability to fsync and arbitrary malicious same-UID mutations cannot be fully recovered by Python exception handlers. OS process-group cleanup after timeout must be verified on the user's Mac in a completely isolated fixture.
6. Filesystem/source contents, old runnable interpreter and Dashboard plist must be verified against new/current Mac state. No release or real Quick is authorized.

## Review focus

- Fault after `os.replace` but before parent-directory fsync must not report NO_CHANGE or miss rollback.
- `KeyboardInterrupt`/`SystemExit` after a risky operation must route through a one-shot restore (SIGKILL and power loss are explicitly uncovered).
- Actual first attempt returncode and output bytes are persisted privately and no-clobber with file + directory fsync; missing output is UNKNOWN, not fabricated zero bytes.
- An inability to persist evidence still triggers one bounded restoration attempt.
- Huge stdout/stderr are drained in fixed 4KiB chunks with retention capped at 8192 bytes per stream, marked as truncated. Timeout kills the new-session process group. Capture status and actual bounded bytes are separated from complete-output claims.
- Preapproved new product SHA, candidate runner exact bytes, old runner original bytes/mode, G0/G3/G4 and protected snapshots are independent conditions. Never modify Loop/V1/D2 and never use the broad installer.

Next action should be *independent Mac code/fixture review*, in a new **Draft** PR based on the fixed PR220 branch, without merging or deploying. Stop at code verdict. Future separately approved production execution must be scoped exactly to Dashboard-only and use a new one-time owner authorization.

## Mac independent review and minimal remediation (2026-10-27)

The original ZIP SHA256 is
`7f1f9a3f9c98b75ebfbcef3e353a2b1ac9558f99745b93c77f51f8a6e817642d`.
Original adapter/test hashes were independently verified against Issue165
#6431947349. The ZIP was reviewed, not executed as a production entry point.

Original 20 tests on macOS27.0.1/Python3.14.7: 5 PASS, 2 FAIL, 13 ERROR.
The 15 blocked cases used noncanonical `/var` temporary fixture paths, rejected
by the adapter's existing path guard. Fixtures now use `.resolve()`; the guard
remains intact and has an explicit alias-rejection test.

The original candidate also failed three independent counterexamples:
- A registered candidate after successful bootstrap/G3 failure was not stopped
  before restoring/bootstrapping the old job. Recovery now attempts exactly one
  Dashboard-only bootout before runner restoration and old bootstrap. A nonzero
  bootout (e.g. never registered) cannot prove absence or success: only a complete
  rc0 old bootstrap AND the independent old process/protected probe verify recovery.
  A cleanup exception or invalid result stops recovery as unverified/failed.
- Different evidence directories did not serialize the same runner. A nonblocking
  flock on the existing canonical parent directory now covers preflight, switch
  and recovery, across runner inode replacements and cooperating processes.
  No extra production lockfile is introduced. Noncooperating writers and malicious
  same-UID mutation remain outside this advisory guarantee and must be excluded
  by the later live integration contract. Directory flock was tested on Mac.
- Selector initialization after Popen could leak a running child. Initialization
  is now inside the cleanup boundary; the child is killed/reaped and pipes closed
  when setup fails. The independent original-version probe cleaned its leaked
  harmless child itself; no process was left running.

Final Mac result: **31/31 PASS**, comprising the original20 and11 targeted cases.
The suite covers registered-candidate recovery, cross-thread and cross-process
locking, SystemExit, actual evidence fsync failure, no-clobber symlink defense,
incomplete streams, actual negative signal rc, missing executable, and actual
process-group descendant termination. It uses scratch files/fake lifecycle and
harmless Python children; never real launchctl. The TIMEOUT fixture now uses
returncode=None, matching actual bounded-command semantics.

The old local 78-line executor was compared at SHA256
`008ffc70c7d283a0a29089cd5dbbab2c0af9642b9ddf5ea816139ac6ff89ee6f`.
This adapter is NOT patched into that file or into a production runner. Both
scripts express source checks, transition and failure recovery, but old live
G0/protected/HTTP helpers must not be silently reused as validated new probes.
No runnable production plan is included. `authorized=True` is not a permit,
flock is not authentication, and SHA256 is integrity correlation, not a signature.

## Outstanding real release gates

Before any live use, a separately reviewed caller must bind the exact new448-file
manifest and old446-file reference to contemporaneous runner/plist/interpreter/
PID/source/port identity, exclude concurrent external writers, implement bounded
real G0/G3/G4 and old recovery probes, and define actual rollout/restore waiting.
The command reader's timeout bounds its I/O/cleanup path, not the entire execute_once
wall time: filesystem fsync and caller probes have no global deadline here.
SIGKILL, power loss, stuck kernel I/O, OOM, disk failure and same-UID tampering
are not solved by catching BaseException or an advisory lock.

Old-service bootstrap must be proven in a future independently authorized gate;
this offline suite cannot prove live rollback operability. F0 remains unresolved,
owner risk acceptance is pending, and no cutover/CA/RPC authority follows from
this Draft PR. There is no need for more unrelated offline modules.
