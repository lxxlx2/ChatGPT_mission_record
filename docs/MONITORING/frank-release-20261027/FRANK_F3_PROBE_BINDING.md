# Frank F3: real read-only evidence and F2 caller binding

Status: IMPLEMENTED_FOR_REVIEW / OFFLINE_ONLY / C2A_NOT_READY.
Authority: Issue165 #6436850568. Product code is ONLY
`296f35a8b6dffe1b2384f77b8768aa799a68ed0d` (448 files), F2 adapter ONLY
`b6282569a76d50113b30853612e5b4839ca8cd3c`. Neither approved version is edited.
This F3 branch is execution tooling, never the product artifact source.

## Investigation and reuse

Read the fixed-source `scripts/frank_pr39_controlled_release.py` read-only
identity/precise-birth/source techniques, `mission_control/server.py` actual GET
routes, `mission_control/frank.py` runtime behavior and the approved F2 adapter.
PR39 also implements dual-service disable/enable/stop/start and SQLite mutation:
DO NOT import its executable release controller. F3 reuses only its public Apple
proc_bsdinfo ABI technique, with additional UID/image/argv evidence. Its old
unbounded subprocess and generic URL helpers are not reused. F2 bytes are checked
against SHA256 aa010235d30dec625847bb5ae132f25e830cecb2ffa0c30f5591dc2edc55446a
before loading. F3 does not repeat F2's closed 31-test/S0/G1/F0 work.

## Read-only sampler: actual evidence rather than filled Identity

`frank_c2a_f3_probe.collect` reads fresh on every invocation:
- Exactly three labels, `launchctl print` and `print-disabled` only. No lifecycle
  verb is in the sampler whitelist. No sudo, broad Home search, or environment dump.
- Apple libproc PID/UID/status and microsecond birth, proc_pidpath image and
  KERN_PROCARGS2 argv. The kernel buffer's environment tail is not decoded,
  returned or logged; only argc argv are used. ABI constants/struct were checked
  against local Apple SDK sysctl.h/proc_info.h and the existing PR39 helper.
- Exact argv arrays, lsof cwd, canonical owner-owned runner/plist/interpreter,
  full expected runner/plist bytes/modes, launch arguments/environment, VENV-to-
  interpreter linkage, execute access and launchd enabled/auto-start conditions.
  Files must predate the kernel process birth; identities are bracketed again
  AFTER files and HTTP to reject restarts/PID reuse during the sample.
- Complete source file sets, SHA256, Git blob header SHA1 when present, execution
  modes and all directories; symlinks, extras and races fail. Dashboard old/new
  sources are immutable and bound to the published G1 canonical manifest hashes
  `eb30010e4973f2d886c2fd7e0054b248c8f041864a5dc545fe8a032de2d1195f` /
  `9e749869826c02db2986a133fd7c90801e1452a842cde14e9cc09fadc4ee2860`.
  Protected legacy sources may explicitly use OWNED_SOURCE (0644/0755), with an
  externally reviewed complete manifest/hash; this NEVER weakens Dashboard's
  immutable requirement or changes existing permissions. Installed physical modes
  and content are evidence, not a signature or a memory/module attestation.
- Unique 127.0.0.1:8766 listener and the other visible listener multiset. Duplicate
  IPv4/IPv6 names on unrelated services are retained as a multiset, not discarded.
- Loop/V1 identities, required policy/registry/authority file hashes tied to actual
  argv pointers, dated D2 whole-file hash/0600 + private parent0700, and fresh health
  notification counters. Missing counters are UNKNOWN/failure, never invented0.
  Raw D2 content is hashed in private memory, never returned or uploaded.
- Fixed same-origin HTTP GET whitelist: root, exact JS/CSS, `/api/runtime`, optional
  explicitly known `/api/cluster-latest?mint=...` with optional exact job_id.
  No proxy, redirect, external host, POST, worker/scanner or arbitrary endpoint.
  Static bytes must match the observed source. `/api/runtime` is Frank V1 health,
  so its PID is checked against V1, NOT the Dashboard PID. The route reads its DB
  read-only; F3 never opens SQLite. G0/G3/G4 safe GET does not submit new work.
  A configured cache report is always HISTORICAL_NOT_NEW_ANALYSIS; no guessed
  Mint/job IDs. ID match proves attribution only, not full CA/current holdings.

Only digests/IDs/timing/provenance summaries leave the observer. No raw argv,
private paths, balances, reports, credential environment or HTTP body in receipts.
The listener census is subject to OS visibility; warnings/incomplete/truncated
command results fail closed. No claim of an atomic system snapshot is made.

## Contract and caller

Private JSON contract is intentionally NOT auto-discovered from the user's Home.
It requires old/new Source specs (`sha`, `root`, `manifest`, `manifest_sha256`,
`count`); `services` for dashboard/loop/v1 (`label`, runner/hash/mode, plist/hash/
mode/launch_argv/expected launch_environment, actual argv, image/hash and canonical
resolved interpreter/hash; protected services additionally a complete source spec).
It also requires `evidence_dir`, D2 path/hash, the two health file paths and
`protected_files` with loop_policy, v1_policy, v1_registry, v1_authority roles,
path/hash/mode. Other explicitly reviewed frozen files may be included. Secrets
are not needed. D2 authority is the previously approved dated Oct25 digest, not a
new balance claim. A later Mac gate must supply and review the actual private
contract; none is committed or assumed valid for current production here.

F3 P2 review follow-up: Dashboard supports the exact one-element plist
`ProgramArguments = [dashboard runner path]` profile only. The one-shot release
edits that runner's `LOCAL_AGENT` line. Interpreter-direct, wrapper and
runner-plus-extra-argv configurations must fail **before any Plan/bootout**,
even when the contract launch arguments and plist digest were updated together.
`validate_contract` rejects an unsupported declared Dashboard launch profile;
`collect` also checks the actual plist bytes, independently of the caller
declaration. The existing direct-interpreter branch remains available for
appropriate protected services, not Dashboard. Three negative tests exercise
the reviewer P2, an extra-argument variant and zero service-command/runner
mutation. This is a code/isolated fix pending an independent new-SHA review,
not live launchd or rollback acceptance.

`BoundCaller.prepare()` performs real G0 (only when explicitly invoked), then
constructs F2's Plan from the observed old runner with EXACTLY its LOCAL_AGENT
line changed. Original inputs are copied, no caller-supplied Identity accepted.
`execute` defaults to deny, requires external owner authorization AND explicit F0
unknown-risk decision; these booleans are preconditions, NOT authentication or
permission. It invokes unchanged F2 with the bound probe and an explicitly supplied
lifecycle; it never creates a real lifecycle by default. The public entry requires
the exact fixed F2 MacDashboardLifecycle type, current gui/UID domain and the
exact prepared plist. Fake lifecycle is allowed only by private test hook patching.
The missing public binding was independently reproduced in development as an
accepted unbound protocol object, then closed before this Draft review.
The wrapper tags recovery independently of whether candidate bootstrap was reached.

Sequence: prepare G0 -> new F2-baseline G0 -> independent G3 -> independent G4.
Every stage starts a new observer; ID and temporal overlap/replay checks apply.
The second G0 must still match prepare's Dashboard PID/birth and protected state.
G4 must match G3's Dashboard PID AND birth. Recovery gets its own RESTORE observation,
old source/runner/GET/protected gates and fresh timing. A damaged candidate must
not prevent independent old restoration verification: RESTORE verifies old source
only. This P2 was first reproduced as ROLLBACK_UNVERIFIED_STOP despite valid old
recovery, recorded in Issue165 #6437623062, then fixed with the same test passing.

## Time and failure boundaries (not a whole-release kill promise)

| Boundary | Limit | Behavior |
| --- | --- | --- |
| each native readonly command/socket timeout | 2s | command capture via fixed F2, GET has 4MiB framing cap |
| entire read-only observer child | <=10s attempt | private fixed worker, bounded stdout, timeout group kill/reap |
| G0 | 30s | one attempt; failure before service changes |
| G3 startup wait | <=45s and <=8 attempts | retry only availability, never integrity/protected drift |
| G4 | 30s | one independent observation; no reused G3 |
| RESTORE wait | <=45s and <=8 attempts | independent reserve even after normal observer deadline |
| normal observer/caller elapsed budget | 180s | includes elapsed F2 work at next checkpoint; NOT hard worker kill |

Short socket timeouts are not end-to-end response deadlines; the observer child
bounds slow reads at the process level. A private FIFO blocked-read child is
actually timed out/killed in tests. Individual G0/G4 attempts are capped10s even
though the stage ceilings are30s. F2 lifecycle commands retain their approved20s
I/O deadline plus bounded cleanup. Recovery is attempted once by F2, never by a
second deployment loop.

Important limitations: private scratch creation/cleanup and prepare's pre-risk
runner read are outside the observer child. F2's own file reads/fsync/rename and
kernel-uninterruptible I/O can hang. This caller cannot wake a blocked F2 call or
promise a hard end-to-end release deadline. Catchable failures invoke F2 recovery;
unkillable I/O/SIGKILL/power loss and a separate emergency supervisor/runbook still
need independent review before production. Do not terminate the whole cutover
process blindly after bootout and call that safe rollback. A deadline cannot
cancel an already-running launchd service or imply recovery success.

## Actual development validation / next gate

Tests use synthetic files/manifests and fake OS outputs but run the REAL collector,
source/permissions, phase binding and unchanged F2 controller. Production authority
constants are patched ONLY in fixtures; a real worker with unpatched constants
rejects those manifests before OS/HTTP, proving no fixture is live admission.
A temporary random-port HTTP server exercises the actual GET transport via a test
connection redirect, never production8766; redirects, oversize and short bodies fail.
The Darwin ABI test reads only its own test process, not any production process.
Linux skips only that Mac-specific check and must not claim Mac PASS for it.

No actual G0, production GET, real launchctl print/lifecycle, private source/D2
read, deployment or restart was performed. Browser is always NOT_VERIFIED; exact
served HTML/JS/CSS is an HTTP/static check, not DOM acceptance. Existing S0 is not
rerun. Code/CI pass requires a new fixed-SHA independent F3 review followed by a
separately scoped read-only Mac contract acceptance. Actual restore operability,
F0 unknown-risk acceptance, a hung-filesystem emergency decision and one-shot
production authorization remain outstanding. NO_DEPLOY / NO_RESTART / NO_RPC /
NO_CA_POST / NO_TRADES / NO_NOTIFICATIONS / NO_MERGE.

## Fixed review handoff validation

Mac macOS27.0.1/Python3.14.7: final41/41 offline tests pass, no skips. This includes
actual self-process Darwin ABI only, the bounded blocked-FIFO worker, random-port
HTTP transport and actual collector/F2 phase integration with synthetic OS data.
No production visit was made. The public lifecycle-binding P1 counterexample was
recorded before remediation in Issue165 #6442659245; it now rejects unbound protocol
objects before any command. An additional test constructs the fixed F2 lifecycle
with ONLY a temporary fixture plist (no methods invoked) to check exact domain/
plist matching. The F2 source remains byte-for-byte unchanged. Development tests
are not independent approval; request fixed-SHA review of this F3 Draft next.

The runtime-data-root P1 was reproduced and recorded in Issue165 #6442758968:
an identical private D2 copy could previously stand in for the live source.
F3 now binds Dashboard/Loop production/control roots and V1 root from the exact
kernel-verified argv, derives the fixed D2/health paths, and rejects copies or
cross-service root disagreement. Evidence must be outside data/source/runner roots.
The same-byte copy negative regression now passes. This is data-source binding,
not a signature, owner permission, or proof of current balances.
