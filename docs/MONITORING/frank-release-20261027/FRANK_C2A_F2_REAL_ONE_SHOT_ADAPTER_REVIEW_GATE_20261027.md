# Frank C2A F2 — real one-shot adapter candidate gate (2026-10-27)

**CODE_CANDIDATE_ONLY / INDEPENDENT_REVIEW_REQUIRED / C2A_NOT_READY**

Authority: Issue #165 F2 `REQUEST_CHANGES` comment #6431680608; PR220 approved SHA `296f35a8b6dffe1b2384f77b8768aa799a68ed0d`; old source `914e9e47fed2e60bc24690fcb083413a64d4e681`; G1 on-Mac physical manifest `9e749869826c02db2986a133fd7c90801e1452a842cde14e9cc09fadc4ee2860` (different from old PR205 manifests).

## Four targeted changes (separate from product code)

1. **Post-replace fsync window:** arm risk before `os.replace`. Any post-bootout exception triggers one rollback, regardless of return from `atomic_runner`. Compare actual current runner bytes against pinned old/new; refuse unrelated third-party drift. No spurious NO_CHANGE.
2. **Interrupts:** catch `BaseException` inside risky zone and preserve a redacted state. On caught `KeyboardInterrupt`/`SystemExit`, persist UNKNOWN first-bootstrap outcome if possible and perform exactly one recovery. Uncatchable signals/host failure are not solved.
3. **First real command evidence:** `MacDashboardLifecycle.bootstrap` uses a bounded real subprocess pipe reader; `execute_once` writes a private durable first-attempt record BEFORE treating the candidate as success/entering rollback. Save real signed rc when available; timeout/interrupt => null; distinguish EOF/truncation/partial. No command argv or env in evidence.
4. **Bounded OS capture:** nonblocking selector over two pipes; 4KiB reads, 8KiB retained per channel, counters/digests, 20s default wall deadline, process-group kill on timeout/interruption; actual Mac validation still required.

## Existing protections carried forward

No import-time effects or CLI; `authorized=False` by default. Real `launchctl` is encapsulated in `MacDashboardLifecycle` and is NEVER instantiated by tests. Real G0/G3/G4 health and Loop/V1/D2/notifier fingerprints are caller-supplied **not yet implemented**. Old runner byte backup private 0600 with no-clobber before service operations. Old bootstrap attempted once after failure; verify old process and protected workload independently before reporting recovery. No broad installer, unapproved port, chain RPC, wallet, email or trade code.

## Actual evidence, with scope

Author's container environment (non-Mac): 20/20 unittest PASS including 3 real harmless OS subprocess tests. Not tested with real launchctl, actual Mac runner/plist, Chrome, production 8766, RPC or release service. This is not an independent audit. The old 78-line cutover source was unavailable here, so compatibility needs independent Mac verification.

## Stop criteria

Any unreviewed code, user unapproved production action, unknown provider, missing independent probe, invalid baseline, release-label drift, missing verified rollback assets, failure evidence unbounded or unrecorded, failed/unknown rollback, current source/manifest mismatch, unaccepted F0 risk => **C2A_RELEASE_NOT_READY**. Old PR220 APPROVE remains unaffected.

**NO_DEPLOY / NO_RESTART / NO_LAUNCHCTL / NO_RPC / NO_CA_POST / NO_MERGE / NO_TRADES.**

## Independent Mac revision — offline only

See `README_F2_REVIEW.md` for original ZIP hashes, original20-test Mac failures,
three independent counterexamples, minimal remediation and final31/31 PASS.
Initial REQUEST_CHANGES was recorded in Issue165 #6432115589 before changes.
No existing product file from PR220 was changed. Only the F2 adapter, its tests,
workflow and review documents are in this stack.

The rollback path now stops a potentially registered candidate before restoring
old runner bytes and bootstrapping old code. The existing parent-directory inode
is locked across switch/recovery to serialize cooperating callers even with
different evidence directories. Selector setup faults now reap the child.
The canonical-path guard was retained; only Mac test fixtures were normalized.

APPROVE for bounded offline adapter evidence is not production readiness. No live
G0/G3/G4 observer, bounded startup/rollback waiting or verified live backup is
supplied. Full execute_once wall-clock bounds and uncatchable failure recovery
are not certified. Actual release integration and owner F0 risk choice remain
mandatory. Do not call MacDashboardLifecycle on a production plan from this PR.
