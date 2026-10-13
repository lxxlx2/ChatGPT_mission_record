# PR #39 legacy Mission Loop controlled cutover — implementation specification v1

**Date:** 2026-10-13 (Asia/Bangkok). **Status:** DESIGN_READY_FOR_INDEPENDENT_IMPLEMENTATION_REVIEW; **PRODUCTION NO_GO**. This is an operations specification, **not** deployment authorization, tested implementation, or evidence of a Mac restart.

## 0. Decision and immutable scope

**Recommended approach:** add a separately gated **legacy-baseline cutover mode** to the existing controlled release tool, without weakening the normal PR #39 release flow. The preexisting Loop PID cannot be proven to match the current on-disk Python source; its prior in-memory imports are **UNKNOWN** and cannot be reconstructed from file hashes. Stop it only with an explicit legacy-specific authorization and do **not** automatically restart that old Loop if the new cutover fails. This trades potential alert downtime for avoiding a second writer, replay, or unverifiable old-code resurrection. Existing **Dashboard** is a separately verifiable baseline and can remain available until the planned stop.

Scope: **Mission Control Loop and Dashboard only**. Never restart or reconfigure the independent Frank scanner; frozen policy, follow predicates, BUY/SELL model, classification, production trading mode, Gmail provider or transaction decision code are unchanged. Do not auto-merge PR #39 or PR #41. **Trading remains NO_GO**.

Reviewed product bytes must continue to match `bda7ef0dfd89e6c1b11f9020163bf754bed5ae74`, reviewed PR #39 head `da5adc0ae63141e8e2b5fb6735224c6405412e6a`. The ops review head at the time of design is `cf3c0834e3fa4441c32ccf890b0df3811d8d6cef`; future implementation commits naturally change ops SHA and need new independent review and CI pinning. Live `main` must be rechecked by existing merge-tree method, not hard-coded to the main SHA observed today.

Read together with:
- `meme/FRANK_PR39_LEGACY_RUNTIME_DIVERGENCE_DECISION_20261013.md`
- `meme/FRANK_PR39_CONTROLLED_RELEASE_REVIEW_20261013.md`
- `local-agent/scripts/frank_pr39_controlled_release.py`
- `local-agent/tests/test_frank_pr39_controlled_release.py`
- `local-agent/tests/test_frank_pr39_runtime_diagnostics.py`
- `local-agent/tests/test_frank_pr39_immutable_release.py`

## 1. The exact observed exceptional baseline

The user-supplied `frank-pr39-legacy-verification-20261013.json` yielded `UNVERIFIED_RELEASE_BLOCKED`; data is an observation on that date and **must be revalidated just before any mutation**.

- Dashboard PID `25851`: 147/147 disk files equal Git, no extra executable files, actual runtime PASS. Kernel birth verification showed dashboard runner **0.020413 s older** than process; normal strict runtime check works.
- Loop PID `79154`: source worktree HEAD differs only in two committed, documented legacy UI blobs:
  - `mission_agent/mission_control/server.py`: HEAD `b5eb4af5c945cc1b62337d48393fe02243f9505f`, disk `f5e00781ea4af45b4d6b15a09b8cb000f5b744f4`.
  - `mission_agent/mission_control/static/app.js`: HEAD `8f0ac1beace94f01894c151576bc276f48f1b4a4`, disk `14985b35b019054d5ff9871e002c32421345ff17`.
  - Extra `mission_agent/mission_control/delivery_review.py`: disk blob `62f5fa85bf41cd95e4a31a373910f81970368ea6`, not in HEAD.
  - All three recorded as exact `legacy` in `scripts/deploy_frank_dashboard_review_badge.py`. The files' mtimes were around **106233.64 s after Loop start** (~29.51 h); current Loop runner around **162293.545126 s after Loop start** (~45.08 h).
- Scanner PID observed `52300` with source digest `599f2f05f197725a25fd85a82501504a772f253866c0556183bbfd82da00a0ce`; protected against restart. Scanner/cursor must be verified fresh later.
- 26/26 latest BUYs had `USDC_DIRECT_NUMERIC`; 35 decision_events, 35 decision_snapshots, 36 outbox, 18 Gmail, 18 local, no presentation table. 15 LIVE Gmail `MANUAL_REVIEW` were zero-attempt pre-send expirations, not delivery retries. Preserve them.

**Semantic distinction:** `DOCUMENTED_LEGACY_DISK_BYTES_RUNTIME_UNVERIFIED` says only the current *disk* matches a known legacy overlay. It does **not** certify Loop PID 79154's in-memory modules, its initial runner text, or safe restartability. We will **not** make `Mac.runtime('loop')` report PASS for this state.

## 2. CLI and authorization contract

Extend `frank_pr39_controlled_release.py` conservatively; no second partially redundant release engine.

- Ordinary existing default/normal mode stays unchanged, read-only, and must still reject `SOURCE_MIXED_BYTES`.
- Add `--legacy-cutover-plan` as an explicit **read-only** command. It computes a separate `LEGACY_PLAN_* / BLOCKED_*` status, with checks for actual Live PID/cwd/loaded plist/runner, **exact legacy disk fingerprint**, timestamp regression, scanner, files, policy, source, queues, disk space, network pins. This is *not* the existing `PASS_READ_ONLY_RELEASE_INVENTORY`; distinctly mark `old_loop_runtime_verified=false`, `old_loop_restorable=false`, `requires_explicit_legacy_consent=true`. No DB writes, status normalization, Git fetch in production trees, imports that write pycache, journal, lock, launchctl actions, or live notification sends. Network fetch to separate audit clone may be used to verify candidate, if no mutation of the production source.
- Implement `--apply --authorize-production-restart --authorize-future-real-notifications --authorize-legacy-unverified-loop-cutover` only **after** implementation review, tests, Mac dry-run, and a separate explicit user go-ahead. Three authorizations are all necessary for this exceptional mode; a generic `--apply` may **never** silently select it. The new flag without apply / required flags cannot mutate. No auto-yes or environment-variable bypass.
- Use exact `--expected-release-sha` and verify clean ops clone plus reviewed product hashes and immutable release image. Existing `--recover` must not call normal `rollback()` for a legacy journal: fail closed or provide a *separate* explicitly reviewed forward-completion/manual recovery subcommand with fresh authorization, safe journal ownership and the same identity checks.
- Preflight success means **eligible to request authorization**, not permission to deploy. The legacy mode is allowed to *recognize a documented nonrestorable old Loop* only within its special preparation; the normal mode remains strict.

## 3. Read-only baseline contract (no acceptance by hash alone)

Require **all** of the following on the Mac, freshly measured and with stable PID between observations:

A. New candidate source exactly matches reviewed product + ops SHA; no mixed or extra executable files; exact PR39 head and current main merge-tree compatible; approved config/policy and frozen scanner files still match protected pins. Immutable release staging only after explicit apply (because staging writes to Application Support).

B. Dashboard follows the normal strict `Mac.runtime('dashboard')`: loaded LaunchAgent runner/plist, command + interpreter, cwd, source manifest and accurate process birth; dashboard HTTP `/`, `/static/app.js`, `/api/control-health` must be measured. Do not falsely mark an old dashboard as new.

C. Loop is a **special legacy identity inventory**, not a pseudo normal runtime: confirm the unique loaded Loop label/PID, `ps` command = Loop and configured interpreter, `lsof` cwd, exact `LOCAL_AGENT` path and approved PROD/CONTROL_POINTER/POLICY/VENV, plist ProgramArguments/KeepAlive/environment and runner identities, the **only** source changes equal the three exact known legacy blobs, no other source file changes/extras, observed runner modification after process birth, and observed historical file mtimes after birth. If any additional or missing file, policy disagreement, anomalous process/cwd, unknown PID, ambiguous source root, or potential second writer exists, **BLOCK**, not fallback to legacy acceptance. Initial loaded Python bytes remain explicitly UNKNOWN.

D. Both control and Frank SQLite readable via `mode=ro`, integrity/foreign-keys OK; record immutable delivery rows and queue statuses. Require **all** outbox, Gmail and local rows in established terminal states at the instant of collection, with Gmail message ID / frozen content hash / outbox receipt matching. `MANUAL_REVIEW` historical zero-attempt expirations are terminal audit rows, not candidates for resend. Any active/retry/unknown state = BLOCK. No cleaning history to make it pass.

E. Scanner source/policy/PID/health/cursors recorded, and remain independent from the planned Loop/Dashboard stop. No scanner restart. Heartbeat freshness, last-successful poll and cursor identities checked. Free disk threshold and backup destination permissions checked; no secrets or raw email content in Git/JSON.

F. Check no unfinished `pr39-releases/*/journal.json` or other in-progress release, no competing active release locks, and no service drift between samples. If the currently observed PIDs changed (e.g., Loop naturally restarted into new source), **re-run the normal release inventory**; do not force the exceptional mode unnecessarily.

## 4. The explicit cutover transaction (only after authorization)

Operate under the existing exclusive `release.lock` and private mode-0600 journal; make phases durable with atomic replace + fsync. The journal stores the immutable source hashes, exact current PIDs, old runner/plist bytes, DB snapshots/row identities, scanner invariants, backup locations and irreversible legacy nature. Private raw record details must remain local, **never** upload to Git.

Proposed monotonic phases:

| Phase | Action and invariant | Permitted continuation |
| --- | --- | --- |
| `L00_RECHECKED` | Exact candidate pins, observed legacy Loop disk fingerprint, strict Dashboard runtime, current queue/runner/scanner/protected config, fresh health, lock/disk recheck. Explicit three-flag authorization logged. | Otherwise abort without change |
| `L10_STAGED` | Stage byte-verified immutable release under `Application Support/FrankMeme/pr39-immutable-releases/<ops-sha12>`, verify read-only marker/hash and that runner replacements will reference ONLY that target; preserve old runners in private journal. | No daemon has been stopped |
| `L20_PRESTOP_BACKED_UP` | Consistent online SQLite backup of control DB AND Frank DB, `PRAGMA integrity_check`, `foreign_key_check`, backup scope/size/hash, protected files and identity watermark (row-level checks); copies private 0600. This is disaster evidence only, not a rollback image to overwrite later data. | Do not touch live rows |
| `L30_HOLDS_SET` | Hold Loop + Dashboard by exact LaunchAgent labels. Scanner neither held nor stopped. Confirm no second writers/surprise child processes. | If any stop failed or PID changed, explicit recovery handling |
| `L40_LOOP_DASHBOARD_STOPPED` | Stop Loop and Dashboard, verify both **old PIDs dead**, absence in `launchctl`, no matching orphan workers via `ps/lsof`, no live Gmail sending/uncertain effects. Never allow concurrently running old/new Loops. | The **old Loop is now non-restorable** absent separate verified reconstruction |
| `L50_POSTSTOP_BACKED_UP` | Read fresh post-stop outbox/Gmail/local, enforce all terminal, snapshot complete row identities, take second consistent SQLite backups/integrity/foreign key/size checks; freeze watermark for N4/duplicate avoidance. Scanner PID/source/policy/cursors unchanged (cursor may only advance). | If queue not terminal, fail-stopped; do not arbitrarily resend or delete |
| `L60_DDL_APPLIED` | Apply only approved `CREATE TABLE IF NOT EXISTS local_delivery_presentation` in an isolated transaction. Verify schema/FK; byte-compare all historical decision, outbox, Gmail, local row identities to L50 snapshot. Never update historical input hashes. | Additive schema may persist on failure |
| `L70_RUNNERS_SWITCHED` | Atomically rewrite only two runner `LOCAL_AGENT` pointers to immutable source, keep approved fields/PYTHONPATH and `MISSION_EVIDENCE_EXPORT_ENABLED=0`; `bash -n`, file hash/readback. Require new loop/dashboard source entire manifest intact. | No launch before all checks pass |
| `L80_DASHBOARD_VERIFIED` | Bootstrap dashboard only; confirm **new PID**, exact process cwd/interpreter, source hashes/mtime, HTML/JS byte comparison and API fields. Scanner protected unchanged. | Dashboard does not send Gmail; prove no new notification row here |
| `L90_LOOP_VERIFIED` | Bootstrap Loop only after dashboard good, verify independent new PID, runner/cwd/interpreter/source, fresh policy-bound heartbeat, scanner unchanged. Confirm historical IDs/receipt hashes/status/attempt counts preserved and no replays. No synthetic signals/mail. | Future real transitions permitted only by unchanged approved policy |
| `L100_SUCCESS` | Save final redacted evidence with expected vs actual hashes, start/stop PID, queue deltas, backup/integrity, new schema, scanner/cursor, API/heartbeat, no trading. Only now may report success. | Unfinished release lock/journal cleared per existing conventions |

For every phase: journal **before** irreversible actions, exact idempotent recovery semantics for SIGINT/SIGTERM/SIGKILL; another invocation cannot create a second Loop. Scanner may legitimately add to its own DB as long as no rollback and cursor never regresses; compare immutable portions, not raw byte equality of live WAL. Recheck all protected artifacts before/after each restart, not only initial prepare.

## 5. Failure handling (the central difference from normal mode)

**Before L30**: no Loop/Dashboard was intentionally stopped, so abort and leave both processes, runner bytes, DB and queue unchanged; cleanup only private staging if safe and **never remove an immutable dir referenced by a live runner**.

**L30 through L70**: do not restart the old Loop or trust the modified legacy worktree; keep Loop disabled/stopped, ensure no orphan worker, durable `LEGACY_MANUAL_RECOVERY_REQUIRED` journal, report private backup paths and the failing gate. Dashboard may be independently restored/restarted only if its *old* source is still byte-verified, the previous runner and plist are proven exact and a deliberately reviewed Dashboard-only fallback has passed tests; otherwise hold it stopped too. Do not roll back or overwrite either SQLite DB.

**L80/L90 partial success then failure**: first stop any newly started Loop and Dashboard so no mixed writer/reader continues, verify absent and no descendants. **Never restore/restart the unproven old Loop.** Keep the journal in recovery-required state. Any unexpected post-cutover decision/receipt/new Gmail attempt is a **manual reconciliation blocker** before even a known-good forward recovery.

**Recovery**: default is *read-only recovery inventory*; later recovery action (if implemented) may resume the **already pinned/verified NEW immutable release** only after independently rechecking journal integrity, old/new PID absence, ledger watermark (including any new rows), frozen policy/queue, scanner source/cursor, and fresh explicit authorization; never blindly call existing `rollback()`. An exact **independently audited** restorable old image would be a different, separately authorized project, not inferred from current disk. Any ambiguous send status remains MANUAL_REVIEW rather than retry. No notifications from replayed old snapshots or changed N4 input_hash alone.

**Trade-off made explicit:** a failed cutover can temporarily leave the Loop (and maybe Dashboard) offline. This is preferable to duplicate live Gmail, unexpected resumed policy, or a second uncontrolled writer. This operational outage risk must be expressly accepted before production authorization.

## 6. Test / review acceptance matrix

No tests run against live Mac or real provider. Build deterministic isolated temp SQLite with WAL, fake `launchctl`, fake process/cwd/birth/health, fake HTTP, frozen Git product fixtures and an isolated release directory. Keep all existing PR39 tests.

1. Legacy exact three-file fingerprint recognized only in explicit `--legacy-cutover-plan` as `KNOWN_DISK_LEGACY_RUNTIME_UNKNOWN`; normal `prepare()` **still fails** `SOURCE_MIXED_BYTES`. Any fourth file, missing extra module, modified policy, differing blob, runner tamper or duplicate worker blocks **before stop**.
2. Legacy flags absent/partial/without `--apply` never stop or send; default/plan is truly read-only, including no `__pycache__` writes to production.
3. Dashboard strict verified runtime; runner newer/unknown runtime blocks. Loop modified-after-start baseline is accepted as **non-restorable**, never fabricated normal `Mac.runtime('loop')=PASS`.
4. Prestop active Gmail/outbox/local state or uncertain send blocks before stop; re-emerging pending/unknown state **post-stop** blocks before migration/start. Exactly 15 historical zero-attempt MANUAL_REVIEW are preserved, never resent.
5. Scanner status/cursor/source/policy drift at L00, L40, L70, L90 prevents the next step; code never calls `launchctl` on scanner.
6. Both DB backups real SQLite API with uncheckpointed WAL; verify consistent data, integrity and permissions; locked DB, insufficient disk, interrupted backup abort/fail-stopped appropriately; never restore DB by copying it.
7. Unexpected fail/KeyboardInterrupt/SIGKILL after **each** journal phase: no second worker, no old Loop restart, no live Gmail, phase recoverable and accurate, protected runner/database file integrity. Exercise after L80 and L90 too.
8. New runner always points at read-only immutable candidate, never cache Git checkout. Simulate deleted/mutated staged file, wrong SHA, unexpected extra source, rollback pointer conflict.
9. Migration idempotent; historical row identities, Gmail wire IDs, receipt/body hashes, attempt counts and N4 changed input hash do **not** generate resend or new sendable decision. Compare identical existing `decision_id`/channel/snapshot IDs, not counts only.
10. Recover command default read-only and refuses unsafe journal, changed version, live duplicate process, active queue, postcutover extra decision or missing backup. Only explicitly reviewed forward continuation may resume new release.
11. Verify Dashboard HTML/JS/API + new Loop heartbeat and actual source **after** start; never call Gmail send endpoints as a test.
12. Run isolated special-mode tests, existing 129+ release/identity tests, complete Local Agent regression with true Git replay, GitHub CI on exact head and **another independent AI review**; Mac read-only **legacy-cutover-plan** final evidence must be separately reviewed before production consent.

## 7. Required deliverables and explicit STOP conditions

Implementation in the *existing* ops review branch/PR #41 (or fresh ops branch based on it, preserving other work), with no changes to reviewed PR39 product files. Deliver:
- Full `legacy-cutover-plan` schema and safe command; no direct `--apply` command for the user until reviewed/accepted.
- Deployment/recovery code and journal phase tests with actual CI links/counts, source commit SHA and narrow diff.
- Independent reviewer report `APPROVE` or `REQUEST_CHANGES` including what remains Mac-only `UNVERIFIED`.
- Deterministic contingency: old Loop **cannot be automatically restarted** from mutated disk, recovery defaults fail-stopped, no DB restore, scanner always independent.
- Exact services to be stopped (`com.<user>.frank-meme.loop` and `com.<user>.frank-meme.dashboard`), **not** the Frank scanner.
- No secret, wallet, Gmail recipient/body, OAuth token, transaction or raw SQLite row contents in public Git/this chat.
- Operators get zsh commands with **no `#` comments** and, when uploading a file, an `open -R` file-selection command.
- Final decision **NO_GO** until independent ops review, exact GitHub CI, legacy-plan Mac validation, and fresh user authorization.

**Do not turn a real deployment into an experiment.** The next implementation job is to code and validate this specification, stop at an operator-authorization boundary, then submit for independent review.
