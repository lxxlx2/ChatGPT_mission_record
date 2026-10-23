# B02 offline self-FD gate correction — UNRESOLVED / REQUEST_CHANGES

Scope authorized by [PR178 comment6376813567](https://github.com/lxxlx2/ChatGPT_mission_record/pull/178#issuecomment-6376813567). Offline synthetic Mac filesystem only. No production diagnostic, permission change, exporter, wallet-data read or import. PR178 product remains fixed `ea9a7715beb4d2a55ae956bf993828cbddcb50e5`; no product edits. Historical B02 BLOCKED record remains unchanged; its unknown consumer was not identified retrospectively.

## Original executor defect and narrow prototype

Read the actual transient previous executor locally. B01 keeps one bound directory fd open through B02; access_inventory used lsof `-Fpu` and allowed only three service PIDs, without per-FD identity or an exact self-descriptor class. This explains a possible self-observation false positive but does not prove which consumer caused the historical failure.

Prototype records executor PID/start before opening synthetic directory; then records FD/device/inode/directory type through fstat. Real macOS lsof captures per-FD metadata; exact PID/start/FD/device/inode/DIR comparison separates self proof, independently approved exact service reference, and all other consumers. Same UID/executable name, arbitrary extra executor FD and new unrecognized processes are not blanket-allowed. Closed managed tokens are invalidated. Inventory errors/missing numeric per-FD proof fail closed.

## Actual tests and counterexample

|Case|Actual result|
|---|---|
|Exact bound self-FD, real OS inventory|PASS: self1, unknown0|
|Additional unrelated child process, same UID|PASS: unknown1 blocks; separately approved exact PID/start/FD reference recognized|
|Additional FD of executor itself|PASS: unknown1 blocks|
|Synthetic same-directory mode0755→0700→0755|PASS, original device/inode retained|
|Repeated observations during managed lifecycle|PASS, no allowlist expansion|
|Managed close then same-directory descriptor reuse|PASS: old inactive proof rejected|
|Missing FD or changed directory/inode|PASS: UNRESOLVED fail-closed|
|**Unmanaged close→reopen same directory, same FD integer**|**FAIL: old proof accepted; exact full contract NOT met**|

Seven initial managed-lifecycle tests passed on Darwin. A bounded supplemental counterexample then really closed the descriptor outside the wrapper and reopened the same synthetic directory. The OS reused the integer; PID/start/device/inode/type also remained identical, so classify incorrectly returned PASS. It is not sufficient to document this case as unsupported when the user contract explicitly requires recycled descriptors to be rejected. No production readiness claimed.

## Independent review and stopping decision

A read-only independent reviewer initially returned conditional PASS for the explicitly managed lifecycle. After receiving the executed counterexample, final review returned **NEEDS_CHANGES / BLOCKING**, agreeing that stale-proof acceptance violates the required contract. Both results are preserved; final review governs. Only standalone synthetic code/results were sent under PUBLIC policy; no original executor/runner, private argv/paths or wallet source sent.

**Final: OFFLINE_B02_SELF_FD_GATE_UNRESOLVED / REQUEST_CHANGES / NOT_APPROVED_FOR_PRODUCTION_ATTEMPT.** Existing metadata proof has no descriptor-generation discriminator for same-inode reuse; an actual independently verified lifecycle/generation mechanism is still missing. A suggested nonce or wrapper counter alone must not be assumed to establish OS-level identity after unmanaged close/reopen. Per project timebox, stop here rather than add successive corner-case tools. Do not resume production chmod/import on the strength of7 managed tests or initial conditional review. Separate owner authorization and independent acceptance would still be required for a future attempt.

## Safety and cleanup

All temporary synthetic directories removed, final synthetic permission0755 before removal; helper child stopped. No production root even read in this run. `PROD_WRITES=0 / EXPORTER=0 / RPC=0 / PROD_HTTP=0 / RESTARTS=0 / DEPLOYS=0 / MERGES=0 / NOTIFICATIONS=0 / TRADES=0`.

Only sanitized report, test assertions, source-code hashes, gate definition and reviewer output published. Prototype remains local offline scaffolding, not installed, not integrated into the prior production executor. No private paths, raw process identities, wallet data, SQLite, credentials, real runner source or complete config uploaded. No new PR/product fork.
