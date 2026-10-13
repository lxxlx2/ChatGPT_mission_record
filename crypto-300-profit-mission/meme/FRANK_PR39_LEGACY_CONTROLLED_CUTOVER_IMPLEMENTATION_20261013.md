# PR #39 legacy Loop controlled cutover: implementation report (2026-10-13)

**Status:** IMPLEMENTED_LOCALLY, NOT PUSHED, NO CI, NO MAC EXECUTION. **PRODUCTION NO_GO.**
This is not a deployment authorization and not an independent AI approval.

## Identities

| Item | Reference |
| --- | --- |
| Remote PR #41 head (unchanged, base of this work) | `1d1f0a9900177c1d9d8bb2e17328ab7a0736b24b` |
| Design revision (local commit) | `ce77b9f0` |
| Implementation + tests + CI workflow (local commit) | `f7d726b1` |
| PR #39 product head (unchanged) | `da5adc0ae63141e8e2b5fb6735224c6405412e6a` |
| Product bytes (unchanged) | `bda7ef0dfd89e6c1b11f9020163bf754bed5ae74` |
| Remote branch | `review/frank-pr39-controlled-release-20261013` at `1d1f0a99` (not updated) |

## Design review outcome

The baseline design's core decisions were kept. Two blocking defects and several constraints were corrected in `FRANK_PR39_LEGACY_CONTROLLED_CUTOVER_DESIGN_REVISION_20261013.md`:

- R1 (blocking): the queue was proven terminal before the stop, but the legacy Loop kept running in between. Implemented as phase `L25_FROZEN`: `SIGSTOP` the identity-verified PID, re-check the strict terminal queue while frozen, and `SIGCONT` on any abort.
- R2 (blocking): `KeepAlive=true` would respawn the legacy Loop from its mutated runner after a bare kill. Implemented as `disable`, then `bootout` (unload), then an identity-verified `SIGKILL` only if still alive.
- R3: every signal re-reads the process identity (PID, kernel birth, command, cwd) immediately before sending it.
- R4: the legacy Loop never receives a runtime PASS; the plan reports `UNVERIFIED_KNOWN_DISK_OVERLAY_ONLY`.
- R5: reuse of `ledger`, `review_reasons`, `source_drift_diagnostic`, `stage_immutable_release`, `backup`, `migrate`, `assert_preserved`, `http_check`, `scanner_inventory`, `atomic`, `replace_source`, `disk_gate`. No second release engine.
- R6: journal with intent-before-action and fsync; `L100_SUCCESS` and `LEGACY_ABORTED_BEFORE_STOP` are excluded from the normal unfinished scan; normal `--recover` refuses legacy journals.
- R7: scanner snapshot compared at L00 (plan), L40 (post-stop) and L90 (post-switch).

## Implemented

- `--legacy-cutover-plan`: read-only eligibility. Exact three-file overlay (`source_drift_diagnostic` must return the documented class, with exactly two modified tracked files and one extra module), overlay and runner modified after process birth, legacy process command, interpreter and cwd, plist lifecycle, dashboard strict runtime plus precise identity, strict terminal queue, historical MANUAL_REVIEW accepted only as zero-attempt pre-send expiries, pre-stop duplicate or unknown worker gate, scanner snapshot, policy pin and bytes, disk gate, dashboard HTTP. Output contains no paths, identifiers or content.
- `--legacy-cutover-apply`: requires `--apply` plus `--authorize-production-restart`, `--authorize-future-real-notifications` and `--authorize-legacy-unverified-loop-cutover`. Phases L00 to L100 with the order enforced by the journal.
- Failure handling: before freeze, abort without signals. While frozen, resume the untouched Loop. If the frozen identity is no longer verifiable, unload the label (never resume blindly). After the stop, the legacy Loop is never restarted; only new processes are unloaded; the journal ends in `LEGACY_MANUAL_RECOVERY_REQUIRED`.
- `--legacy-recover-inventory`: read-only; reports phase, intent, process and runner state, and performs no action.
- Mac wrapper additions: `identity`, `signal_verified` (identity checked before each signal).

## Test matrix (design section 6) to tests

| Design category | Tests |
| --- | --- |
| 1 exact legacy shape only; extra file blocks before stop | `test_plan_on_exact_legacy_shape_is_eligible_and_read_only`, `test_fourth_unexpected_source_file_blocks_before_any_stop`, `test_overlay_predating_process_start_is_not_the_legacy_shape`, `test_tampered_plist_lifecycle_blocks`, `test_mixed_legacy_checkout_is_still_rejected_by_normal_source_gate` |
| 2 read-only default, no mutation | plan read-only test (sandbox tree hashed before and after) |
| 3 dashboard strict, loop never PASS | plan test asserts the legacy Loop never receives `runtime` |
| 4 pre-stop active queue; post-stop reappearance; historical 15 preserved | `test_pending_gmail_or_outbox_blocks_before_any_stop`, `test_queue_reappearing_after_stop_blocks_before_migration`, `test_full_legacy_cutover_switches_both_and_never_duplicates_a_writer` (historical rows byte-identical) |
| 5 scanner drift at each checkpoint | `test_scanner_drift_at_each_checkpoint_blocks_the_next_step` (L40 and L90) |
| 6 WAL backup, locked and low disk | `test_wal_backup_preserves_uncheckpointed_history`, `test_pre_freeze_failure_aborts_without_signalling_the_legacy_loop`, `test_low_disk_blocks_the_plan` |
| 7 failure after each phase; SIGINT, SIGTERM, hard kill | `test_queue_becoming_active_while_frozen_resumes_the_untouched_loop`, `test_unverifiable_frozen_loop_is_unloaded_so_launchd_cannot_respawn_it`, `test_failure_after_stop_never_restarts_the_legacy_loop`, `test_new_dashboard_started_but_new_loop_fails_stops_new_processes_not_legacy`, `test_signal_during_unload_is_fail_stopped_for_both_signals`, `test_interrupt_while_switching_runners_leaves_loop_unrestarted`, `test_hard_kill_after_intent_leaves_recoverable_journal_and_no_second_loop` (forked child, exit 137 with no cleanup) |
| 8 runners only point at the immutable release | full cutover asserts both runners reference the staged path |
| 9 migration idempotent and additive; identities preserved | `test_migration_is_idempotent_and_additive_only`, full cutover identity comparison |
| 10 recovery read-only; refuses normal journals | `test_recovery_inventory_is_read_only_and_refuses_normal_journals`, `test_normal_recovery_refuses_a_legacy_journal` |
| 11 dashboard HTML, JS and API, new Loop heartbeat | `http_check` target path; `fresh()` heartbeat after start in the full cutover |
| 12 regression | full Local Agent regression, see below |

Also: `test_success_never_leaves_two_loop_processes_alive`, `test_journal_rejects_out_of_order_or_unlogged_phases`, `test_cutover_tool_imports_no_gmail_or_delivery_send_path` (AST), `test_legacy_plan_and_apply_flags_cannot_be_mixed_with_a_normal_apply`.

## Defects found during development and fixed

1. The product digest rejects floats by design; the legacy fingerprint contains process-birth floats. Fixed with a separate `legacy_digest` (sorted JSON, product digest untouched). Found by the first test run, not by reading.
2. Reason codes from the ledger contain lowercase table suffixes; the widened pattern also applies to the existing entry-point handler, which only carries code-defined constants.
3. The plan lacked the design's pre-stop duplicate-worker gate. Added.
4. The Dashboard identity was not measured with precise kernel birth in the plan, so the L80 comparison could fall back to the whole-second rule. Added.
5. An unverifiable frozen Loop would have stayed stopped with the runner mutated and no safe way to resume. Now unloaded.
6. Two test expectations were wrong (drift checkpoint index; a Path compared with a string). Corrected after verifying the implementation matched the design, not by weakening assertions.

## Verification

- Legacy suite: 32 passed.
- All PR #39 suites together: 111 passed before the final additions; the final committed tree passes the full regression.
- Full Local Agent regression with `FRANK_EXPECT_REAL_GIT_REPLAY=1` on committed `f7d726b1`: **1388 passed, 0 skipped, 0 failed**.
- pyflakes and `node --check` on app.js: clean.
- No GitHub CI run exists for this head.

## Remaining blockers (not closed by this work)

1. The commit is not pushed to the remote; the environment has no push credentials. No remote CI can run until someone pushes it.
2. Mac-only validation is not done: `launchctl disable`/`bootout` behaviour with a SIGSTOPped process and ExitTimeOut; whether KeepAlive respawns after disable; `ps`/`lsof` output formats; precise kernel birth availability on the current macOS; the L70 to L80 timing against the runner-birth rule.
3. The legacy worktree HEAD commit is not pinned (only its blobs are documented). Forward safety does not depend on it, but provenance is weaker than the design implies.
4. The read-only `--legacy-cutover-plan` has never executed on the Mac.
5. Operational outage after a failure past the stop is accepted by the design, not yet by the operator.
6. Forward recovery is intentionally not implemented; any such action needs its own review.
7. Independent AI review is pending.

## Commands

No Mac command is ready: the commands would clone the review branch, which is not pushed. Once pushed, the read-only plan is the only command to run first.
