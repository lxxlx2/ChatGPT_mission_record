# F0 D1 — protected Mac fixed one-use registrar (source-only / no live entry)

**Approved immutable parent:** PR #187 fixed SHA `23f41ea2f984cb652cc07bbf28d9366d18b61701`, Codex/Mac `APPROVE_OFFLINE_CODE — D1_MAC_PROTECTED_PREFLIGHT_SCOPE_ONLY`; Mac **481/481 full**, **120/120 D1**, **8/8 new**, zero SKIP. Real Mac `--verify-only` checked **173 tracked F0 source files and 11 loaded critical modules**, no socket/marker. Prior `9d352bb2...` REQUEST_CHANGES is still valid only for that old SHA.

## What changed

The existing `FixedLocalGrantRegistry` in `f0_l2_d1_grant.py` can now validate the **actual Mac OS account** directory (POSIX account record), instead of treating `PRIVATE_FIXED_REGISTRY` from `Path.home()`/environment alone as trustworthy:

- macOS only; immutable-by-caller code-defined relative root `~/Library/Application Support/MissionEvidence/f0-grant-registry`; OS account home must match actual imported fixed root. HOME, permit, evidence-root and output-root variations cannot redirect it.
- Every ancestor is read with `lstat`; no symlink or non-directory component. The account home and descendants must be OS-user-owned, with no group/other write bits. The final registry is private mode `0700`; **the code does not create it**.
- The granted O_EXCL consumed marker remains `0600`, written and file-fsynced; the **same opened directory fd** is fsynced before returning. A duplicate grant remains denied when permit content or evidence root changes; no refund or retry on uncertain persistence.
- The `FixedLocalGrantRegistry` measures root `(st_dev, st_ino)` and rechecks before use; `OfflineGrantRegistry.consume` also compares the *opened directory fd* against the expected identity before it creates the marker, preventing a check-to-open directory-swap from silently targeting an unreviewed root.
- The original `OfflineGrantRegistry(root)` remains strictly test-only and retains its behavior; the existing fixed-registry test was updated to emulate a canonical OS-account home, not arbitrary output root. New tests run only under private temporary directories and patch Darwin/OS home. No production Mac grant store or BSC journal touched.

## Critical scope boundary

This is **G-05/G-06 registrar code hardening**, **not the production D1 live launch**. In particular:

1. The approved PR #187 protected Mac `--verify-only` entry still does not call `FixedLocalGrantRegistry.consume()`; it must never create a marker simply because a *candidate* scope is valid.
2. A future exact user-approved D2 permit and separate D3 explicit real run are still required. Neither a test grant nor a Codex `APPROVE_OFFLINE_CODE` is permission to send requests.
3. This registry does not yet coordinate actual HTTPS sockets; no actual `RESERVE_UNKNOWN` before TLS connect and no real RAW-before-SETTLE can be claimed from these tests. Actual absolute request deadline and socket crash/partial-write UNKNOWN remain incomplete.
4. This local POSIX store does not guarantee persistence under malicious OS admin deletion, host reinstall, restored backup or compromised runtime. For the narrowly bounded supervised read-only F0 experiment, this is an explicit threat-model limitation, not an invitation to call it cryptographically permanent.
5. There is **another Draft sibling PR #188** from the same fixed parent for the unreleased HTTPS single-coordinator route; it modifies `f0_l2_d1_coordinator.py` and adds its own module/tests. This PR does **not** touch those files. They are independent increments that must be reconciled into **one new exact SHA and a single independent Mac review** before any D1 release readiness decision; do not mark either child independently as a complete sender.

## Codex acceptance

Review exact fixed child SHA versus approved PR187; run the complete and D1-focused suites on Mac `cryptography==46.0.4`. New `test_f0_l2_d1_mac_fixed_registry.py` cases must prove legitimate temporary account-root grant creation/0600 marker and durable ownership, duplicate denial, spoofed HOME / arbitrary root refusal, intermediate symlink denial, wrong modes/owner, path replacement after construction, mismatch on the opened directory fd, and both public live entrypoints still refusing before network. Original `test_f0_l2_d1_grant.py` fixed-root fixture must be updated to the new canonical simulated home. **No actual RPC/WS, production registry or private BSC journal**. New/future tests may run in a child process only; no daemon.

Approved scope verdict may be `APPROVE_OFFLINE_CODE — D1_FIXED_OS_REGISTRY_SCOPE_ONLY`, or `REQUEST_CHANGES` for reproducible mainline P0/P1. It must never be interpreted as full D1 completion, D2 permit or D3 real-run approval.

**Current release state:** `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`. Constraints: NO_NEW_RPC / NO_REAL_PERMIT / NO_MERGE / NO_DEPLOY / NO_TRADES / NO_BACKGROUND.
