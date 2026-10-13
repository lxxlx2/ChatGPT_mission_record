# Frank PR #39 — Claude legacy cutover import and independent review

**Date:** 2026-10-13, Asia/Bangkok. **Decision:** `READY_FOR_MAC_READ_ONLY_PLAN`; `PRODUCTION_DEPLOYMENT=NO_GO`. The special cutover code is an unapproved release candidate, not an authorization.

## Source and provenance

User uploaded the Claude local report and `files(4).zip`, which contains `pr39-legacy-cutover.bundle` (thin Git bundle) and an implementation report. Bundle head: `dcb82ff1ce3f23bb184a3c93ca1e4c91c4a20e14`; prerequisite base `1d1f0a9900177c1d9d8bb2e17328ab7a0736b24b` is the preexisting PR #41 head. The Claude local author could not push.

The complete changed implementation was imported into the **same PR #41 review branch** via GitHub API, without force-pushing or changing PR #39 product files. Four imported full-text Git blobs matched the user's bundle SHA exactly:

| File | Git blob SHA |
| --- | --- |
| `tests/test_frank_pr39_legacy_cutover.py` | `7598c58c88a64802c2364b83eaa9c79bcd214b75` |
| `.github/workflows/frank-pr39-legacy-cutover.yml` | `993242c200bdf09cb58910f9cdae90d5c9491062` |
| `meme/FRANK_PR39_LEGACY_CONTROLLED_CUTOVER_DESIGN_REVISION_20261013.md` | `f540fc86773ab697a094ab2a4dc03a930907b3f1` |
| `meme/FRANK_PR39_LEGACY_CONTROLLED_CUTOVER_IMPLEMENTATION_20261013.md` | `08d7d89a4d6a62b199abf41f936485042f1d67f1` |

The updated operations script was reconstructed from the bundle's original delta against preexisting blob `a5578f62d87d0119ad2608e11d39da9b63c87308` (55,941 bytes), yielding Git blob `b6a04e473f9801586c99f6e0d214d14a123c76dc` (78,169 bytes). No trader strategy files were changed.

## Exact GitHub CI

Imported implementation and original tests at commit `721bd3d0f9457f15fb377de56519f7895db755f7`:
- [Legacy cutover safety, run 38325916787](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38325916787): **111 targeted PASS, 1,388 full PASS**, genuine Git replay.
- [Existing controlled release, run 38325916813](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38325916813): **129 targeted PASS, 1,388 full PASS**.

Independent code inspection found and fixed a **pre-stop partial LaunchAgent hold recovery defect**: while the legacy Loop is frozen, the first `launchctl disable` may succeed and the second may fail. The original exception handler resumed the Loop with `SIGCONT` but left its LaunchAgent disabled and falsely marked a clean abort. This also affects interruptions between L30 operations.

- Operations fix commit `83f6e64fdd950c0ad0f549f7d0e2f8c26e8e27ba`: track successful holds; release them before identity-verified `SIGCONT`. If unable to restore, attempt to hold/unload both services and require manual recovery rather than declaring a harmless abort.
- Regression commit `6f2ac5376b415b317575ac3c1e7efbddb755b87f`: test partial holds and failure to release; simulator now models `release_hold`.
- [Legacy safety CI 38326183961](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38326183961): **113 targeted PASS, 1,390 full PASS**.
- [Controlled release CI 38326183981](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38326183981): **129 targeted PASS, 1,390 full PASS**.

**Review scope:** source review and isolated GitHub CI only; the user has not yet executed the new `--legacy-cutover-plan` on the real macOS host. No claims of production success.

## Core release contracts preserved

- The ordinary `prepare` remains strictly blocked by `SOURCE_MIXED_BYTES` for the old Loop; special mode requires an exact three-file historical disk fingerprint and an explicit third authorization in addition to the standard two.
- The old in-memory Loop version is never called verified. Stop only after identity-verified `SIGSTOP`, strict terminal notification ledger recheck and controlled launchd unload. The potentially updated legacy disk tree cannot be trusted for an automatic rollback.
- SQLite online backups and only additive DDL; no historical row rewrite or backup overwrite of future receipts.
- Separate Frank scanner untouched; no synthetic decisions, test Gmail or automatic trading.
- Recovery inventory is read-only; interrupted legacy journal blocks ordinary release/recovery.

## Explicit remaining blockers

1. **Actual Mac process lifecycle is not verified.** macOS `bootout` of a SIGSTOPped process, `KeepAlive` behavior, worker PID/cwd and all timestamps require the new read-only `--legacy-cutover-plan` plus a separate deployment review. The read-only plan itself will **not** test SIGSTOP/bootout.
2. **Post-stop failure is intentionally fail-stopped/manual.** If `bootout` or worker cleanup fails, the code attempts a safe unload, writes `LEGACY_MANUAL_RECOVERY_REQUIRED`, and never restarts the unprovable old Loop. Under abnormal OS failures this is a best-effort cleanup, **not a guarantee of zero orphan workers**. There is no separately audited forward recovery tool.
3. **The first authorized cutover may cause downtime** of Mission Loop and Dashboard if post-stop checks fail. That downtime risk has not been accepted by the operator.
4. **Independent final production review and explicit authorization remain missing** even after green GitHub CI.

The next correct step is **one Mac read-only `--legacy-cutover-plan`** on the reviewed exact SHA, not another repetition of old source-fingerprint probes. Only after reviewing that packet should a separately authorized, carefully monitored deployment be considered.

**Neither PR #39 nor PR #41 was merged; both stay Draft. No production changes were made by this review.**
