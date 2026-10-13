# PR #39 legacy Loop cutover: independent design review and revisions (2026-10-13)

Baseline: `crypto-300-profit-mission/meme/FRANK_PR39_LEGACY_CONTROLLED_CUTOVER_DESIGN_20261013.md` at `1d1f0a9900177c1d9d8bb2e17328ab7a0736b24b`.
This revision supersedes the baseline only where stated. Everything not listed here stands.

## Review verdict on the baseline

The core decisions are sound and retained:
- The legacy Loop's in-memory modules are unknowable; the legacy path must never restart it.
- Stopping the legacy Loop is safe irrespective of its unknown version: the stop removes a writer, it cannot create a new one.
- Normal `prepare()` keeps rejecting `SOURCE_MIXED_BYTES`; the exceptional mode is explicit and triple-authorized.
- The Frank scanner is never restarted, held or reconfigured.
- Recovery never restores or re-runs the legacy Loop and never restores an old SQLite backup.

Two blocking defects and several implementation constraints were found and are corrected below.

## Blocking defect R1: unfrozen window between queue proof and stop

The baseline proved the queue terminal at L00 and again after the stop at L50. Between them the legacy Loop keeps running: it may enqueue a new decision, perform a live Gmail send, or leave a row in SENDING. Those effects happen after the proof and before the stop.

Revision: add phase `L25_FROZEN`. After the backups at L20, send `SIGSTOP` to the identity-verified legacy PID. A stopped process cannot write SQLite or call the provider. While frozen, re-read the strict terminal queue and the PID identity. Any failure sends `SIGCONT`, records `LEGACY_ABORTED_BEFORE_STOP`, and the legacy Loop resumes unchanged. A send that was already in flight at the provider may complete remotely while frozen; if the process is later killed with SENDING, the new code reconciles it through `find_sent` and does not resend. L50 still blocks in that case.

## Blocking defect R2: launchd would respawn the legacy Loop

The Loop LaunchAgent has `KeepAlive=true`. A bare `kill` of its PID is followed by an immediate launchd respawn with the unchanged runner, which points at the mutated legacy worktree. That creates a second live writer.

Revision: the only permitted stop order is: `launchctl disable` (hold), then `launchctl bootout` (unload; no respawn), then verify absence, and only then an identity-verified `SIGKILL` if the PID is still alive. A raw `kill` before the unload is forbidden.

## Required constraint R3: PID identity before every signal

Every `SIGSTOP`, `SIGCONT` and `SIGKILL` requires re-reading the identity tuple (pid, kernel process birth at microsecond precision, command line, cwd) and comparing it with the recorded tuple. Mismatch aborts with manual review. This prevents PID reuse from signalling an unrelated process.

## Required constraint R4: legacy-only classification gates

- The overlay files (`server.py`, `static/app.js`, extra `delivery_review.py`) must be modified after the Loop's process birth, and so must the runner. If they are not, the case is not the documented legacy shape; it goes back to normal review and is not cut over.
- The legacy plan reports `legacy_loop_runtime=UNVERIFIED_KNOWN_DISK_OVERLAY_ONLY`. It never reports a runtime PASS and never weakens `Mac.runtime('loop')`.

## Required constraint R5: reuse, do not re-engineer

Reuse without modification: `ledger()` (strict terminal queue, historical MANUAL_REVIEW are terminal), `review_reasons()`, `source_drift_diagnostic()` (exact three-file classification), `stage_immutable_release()`, `backup()`, `migrate()`, `assert_preserved()`, `http_check()`, `scanner_inventory()`, `Mac.runtime('dashboard')`, `atomic()`, `replace_source()`, `disk_gate()`.

## Required constraint R6: journal phases and normal-path terminal set

- Legacy journals carry `mode=LEGACY_CUTOVER`. Every irreversible action has an `intent` record written and fsynced before it runs, and a completion record after.
- Terminal phases `L100_SUCCESS` and `LEGACY_ABORTED_BEFORE_STOP` are excluded from the normal unfinished-release scan. Without this a completed legacy cutover would block every future normal release forever.
- `LEGACY_MANUAL_RECOVERY_REQUIRED` is non-terminal for the normal path and blocks it.
- Normal `--recover` refuses any legacy journal.

## Required constraint R7: scanner invariance checkpoints

Scanner PID, protected policy and registry hashes, source digest, entry hash and loaded source digest are compared at L00, after the stop (L40), and at L90. A change blocks the next step. The code never calls launchctl on the scanner label.

## Recovery scope for this implementation round

`--legacy-recover-inventory` is read-only. It reports the phase, observed PIDs and identities, runner pointers (old, new or unknown), queue against the watermark, and the required manual action. It performs no action. A forward-completion action is deliberately not implemented in this round; any such action needs its own review.

## Accepted operational trade-off (unchanged)

A failure after the stop leaves the Loop, and possibly the Dashboard, offline until a human reviews the journal. This is preferred to a duplicate live writer, a resumed unreviewed policy, or an unverified old version.

## Not changed

No change to reviewed PR #39 product files, frozen Frank policy, classifiers, trading mode (`NO_GO`), or the Gmail provider.
