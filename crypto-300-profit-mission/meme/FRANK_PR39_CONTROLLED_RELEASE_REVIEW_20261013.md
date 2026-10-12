# Frank PR #39 controlled release — independent operations review

Date: 2026-10-13 (Asia/Bangkok). **Production decision: NO_GO / REQUEST_CHANGES until Mac runtime and deployment gates pass.**

## Scope and evidence

Reviewed upstream ops branch: `ops/frank-pr39-controlled-release-20261013` at `d58d4e3b0909f2c19166e60d7bf6878671c6afb7`.
Approved **product**, which is deliberately not changed by this review: `bda7ef0dfd89e6c1b11f9020163bf754bed5ae74`.
PR #39 evidence HEAD reviewed separately: `da5adc0ae63141e8e2b5fb6735224c6405412e6a`. The prior product CI `38295256441` succeeded; PR #39 remains distinct from this ops review.
The reviewer supplied an archived patch and report, `frank-pr39-controlled-release-review-fix.patch`, which were inspected against the upstream ops source, and the two production release defects were reconstructed in this **new Git branch**. The upstream ops branch was **not overwritten**. No production action was executed.

## Blocking code findings

- **F1 (High, patched in review branch)**: the old release runner would reference the operator's mutable checkout/cache clone, so future `git checkout`, removal or reset could alter live source silently. A separate `Application Support/FrankMeme/pr39-immutable-releases/<release-sha-prefix>` directory is now staged from an exact `git archive`, byte-compared to reviewed candidate source, marked with a source digest manifest, and made read-only. Runtime source integrity checks validate the manifest, require expected files, and reject extra source files. This does not protect against privileged, deliberate file modification; runtime verification and release discipline remain required.
- **F2 (Medium, patched in review branch)**: the original ops code rejected every new `main` SHA because of an obsolete hard-coded exact comparison. The replacement still pins PR #39 head exactly, fetches current remote main, confirms the fetched SHA matches the independent `ls-remote` observation, and performs a `git merge-tree` compatibility check. Unexpected modifications outside approved PR #39 paths remain blocked.
- **F3 (Low, unchanged)**: `launchctl bootout/bootstrap` changes LaunchAgent lifecycle more than `kickstart -k`. Running behavior must be checked on the user's actual macOS; scanner service must not be restarted.

## Verified from source design

- Default CLI provides read-only inventory; actual `--apply` requires **both** authorization flags, and `--recover` requires explicit apply authorization.
- A private journal, exclusive release lock, process absence checks and runtime source comparison are included.
- `local_delivery_presentation` is an additive table. On rollback the database is **not** replaced by a historical backup.
- Gmail and local outbox snapshots are compared by immutable decision identity; terminal states and existing content hashes are protected.
- The separate Frank scanner PID/plist/cursor/source are monitored and are **not** targeted for restart.

These are code-review findings, **not claims that production LaunchAgents were exercised**.

## Read-only Mac evidence already supplied for the previous preflight

The operator's uploaded `frank-pr39-preflight-20261013.json` reported:
- 26 Frank indexed states; 26 last-BUY `USDC_DIRECT_NUMERIC` predicates; 0 missing latest BUY predicates.
- Control SQLite integrity OK; 35 decision events; 17 historical LIVE Gmail rows: 2 SENT_VERIFIED, 15 MANUAL_REVIEW.
- 0 Gmail in-flight and 0 pending local messages at the observation time.
- `local_delivery_presentation` not yet present, as expected on the old runtime.
This is historical point-in-time **aggregate read-only evidence**, not fresh release permission.
The 15 `MANUAL_REVIEW` reasons are not verified by the aggregate report.

## Tests and outstanding blockers

The separate review branch adds real-Git immutable staging tests for root and nested layouts, read-only source bits, tampered files, injected files, existing incompatible release and unsafe tar paths. CI result and exact SHA must be appended only after GitHub confirms completion.

Still required **before any production source switch**:
1. GitHub CI on the exact ops review branch and any further independent review of its new release logic.
2. The Mac-only `--collect-evidence` showing actual loaded Loop/Dashboard versions, PIDs, runner pointers, heartbeat/policy and scanner ownership, current database and in-flight queue, and 15 MANUAL_REVIEW reason counts.
3. Confirm `launchctl`/macOS process inspection works as designed on the actual host, verify the fresh main merge-tree and exact PR39 head, and ensure current runtime protected source hashes remain valid.
4. Perform private consistent backup and integrity checks immediately before release; then obtain explicit approval for two-service controlled restart and future natural notification delivery.
5. Verify post-switch source version, HTTP UI/API, immutable delivery rows, scanner cursor and heartbeat without emitting synthetic signals or Gmail.

**No merge, no Mac restart, no Gmail send, no database mutation, and no live trading was authorized or performed by this review.**
