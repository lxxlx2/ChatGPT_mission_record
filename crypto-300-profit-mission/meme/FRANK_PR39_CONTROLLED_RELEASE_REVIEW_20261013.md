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

The separate review branch adds real-Git immutable staging tests for root and nested layouts, read-only source bits, tampered files, injected files, existing incompatible release, writable existing release and unsafe tar paths. The initial upstream ZIP patch failed GitHub CI as a normal non-root user: chmod on the nested staging parent prevented `rename`, and tampering fixtures could not write locked files. The reviewed implementation was corrected to rename verified source **before** locking directory permissions, to fail closed on reusing a writable existing release, and to explicitly grant test-only permissions to simulate deliberate tampering.

CI evidence: [GitHub Actions 38319496576](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38319496576) on head `1ecee84656e84ef945d856bf6308aa24b081518c`, **SUCCESS** with **117 targeted passed** and **1,344 full local-agent tests passed**, including real Git replay. Subsequent documentation-only commits must be checked on their exact HEAD before final release assessment.

Still required **before any production source switch**:
1. GitHub CI on the exact ops review branch and any further independent review of its new release logic.
2. The Mac-only `--collect-evidence` showing actual loaded Loop/Dashboard versions, PIDs, runner pointers, heartbeat/policy and scanner ownership, current database and in-flight queue, and 15 MANUAL_REVIEW reason counts.
3. Confirm `launchctl`/macOS process inspection works as designed on the actual host, verify the fresh main merge-tree and exact PR39 head, and ensure current runtime protected source hashes remain valid.
4. Perform private consistent backup and integrity checks immediately before release; then obtain explicit approval for two-service controlled restart and future natural notification delivery.
5. Verify post-switch source version, HTTP UI/API, immutable delivery rows, scanner cursor and heartbeat without emitting synthetic signals or Gmail.

**No merge, no Mac restart, no Gmail send, no database mutation, and no live trading was authorized or performed by this review.**


## Actual Mac controlled read-only inventory (2026-10-13 Bangkok)

The operator executed the reviewed ops `--collect-evidence` against the
running Mac and uploaded a JSON report. Overall **UNVERIFIED_RELEASE_BLOCKED**.
No production mutation, restart, Gmail send, or merge was performed.

- `manual_review_reasons=PASS`: **15** historical LIVE Gmail MANUAL_REVIEW,
  all **15** are `GMAIL_DECISION_STALE_OR_TIME_UNVERIFIED_BEFORE_SEND`
  with zero recorded send attempts / no receipt; **0 require private review**
  under the instrumented checks. Preserve their ledger rows and do not resend.
- `databases_and_scanner=PASS`: Frank latest BUY predicate coverage is **26/26**
  `USDC_DIRECT_NUMERIC`, 0 missing. SQLite record counts are **35**
  decision events and snapshots, **36** outbox, **18** Gmail, **18** local,
  **0** local presentation. Frank scanner running-source fingerprint and
  PID were retrieved, but full scanner lifecycle proof remains dependent
  on the complete preflight.
- `loop_actual_runtime=UNVERIFIED(SOURCE_MIXED_BYTES)`.
- `dashboard_actual_runtime=UNVERIFIED(RUNNER_START_SECOND_AMBIGUOUS)`.
- `complete_release_preflight=UNVERIFIED(SOURCE_MIXED_BYTES)`.

**Do not suppress either runtime guard.** A historical authorized UI/runtime
overlay may explain a Git HEAD mismatch, but source provenance is unproven
until the exact differing filenames and actual Git blob identities are
collected. The Dashboard runner's mtime lies in the same coarse one-second
bucket as the process start; this by itself does not prove whether the
running process loaded the before or after text. The new isolated read-only
`source_drift_diagnostic` and `runner_start_time_diagnostic` return
repository-relative paths, Git content identities, and timestamp deltas
without exposing private root paths or local source/credentials. They **do
not** change the production gate or authorize a restart.

A subsequent Mac run of this updated review branch must verify these
diagnostic values, then any acceptance of explicitly reviewed legacy
overlays needs its own exact hash allowlist and independent test.
