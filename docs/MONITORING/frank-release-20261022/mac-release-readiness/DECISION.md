# Frank PR #157 Dashboard-only release preparation

**DASHBOARD_ONLY_RELEASE_READY — preparation and user decision only; NO production deployment executed.**

Date: 2026-10-22. Product fixed SHA `31dd598df248ca15f731913a5cbf82e88b981874`; planning branch fixed SHA `419270e96950af7b014dbe70c48b641677eb6f51`. Both remote identities checked before work. Independent detached checkout used, later placed on dedicated QA branch `qa/frank-pr157-dashboard-only-release-rehearsal-20261022`. Main checkout branch/HEAD untouched. Earlier page acceptance not repeated.

## 1. Existing three-file review and actual commands

Reviewed all three additions relative to product: release-lab Python, release-lab GitHub workflow, release decision Markdown. Python only invokes read-only git/ps/lsof/launchctl print, local GET, or temporary filesystem simulation. No launchctl mutation, notifications, trade, production writes or installer invocation. Workflow runs AST and simulate only, with contents:read and no persisted credentials. Decision document grants no deployment authority.

Original fixed lab commands actually executed before any QA edits:

```sh
python3 -B crypto-300-profit-mission/local-agent/scripts/frank_pr157_dashboard_release_lab.py --simulate
python3 -B crypto-300-profit-mission/local-agent/scripts/frank_pr157_dashboard_release_lab.py --audit
```

Raw sanitized JSON outputs: [simulate.txt](simulate.txt), [audit.txt](audit.txt).

Simulation: `staged_approved_files=8`, `synthetic_switch_and_revert=PASS`, `actual_running_dashboard_restarted=false`, `real_release_rollback_proven=false`, production_write/email_sent=false. **The eight-file lab is not a deployable dependency closure and not a running-service rollback test.** Its source allowlist deliberately rejects subsequent QA branch additions; replay original commands at fixed planning SHA, not this evidence/QA HEAD.

Audit limitations: `running_source_sha256` hashes files on the process cwd's disk, not imported Python memory; `real_service_touched=false` means no management/mutation, though local read-only GET contacted it. Its cwd alone does not establish the exact source provenance, rollback or freshness. These were supplemented below.

## 2. Actual current Mac state and provenance

| Entity | Actual observation |
|---|---|
| Dashboard | PID 35963, started Tue Oct 13 17:32:07 2026, listener 8766, root GET 200 |
| MC Loop | PID 36070, started Tue Oct 13 17:32:13 2026 |
| V1 source service | `/api/runtime` reports PID 52300; this is NOT the Dashboard PID |
| Dashboard and Loop code | Same cwd, relative installed release `pr39-immutable-releases/52d43d18ee5a`; no Git checkout there |
| Dashboard LaunchAgent | `com.jerson.frank-meme.dashboard`; single runner argument `dashboard.sh`; RunAtLoad/KeepAlive true |
| Loop LaunchAgent | `com.jerson.frank-meme.loop`; single runner argument `mission-loop.sh`; RunAtLoad/KeepAlive true |
| Both runner source | LOCAL_AGENT points to same old release. Dashboard execs entrypoint `serve`; Loop execs `loop --live-delivery`. Same existing interpreter, separate PIDs |
| Immutable release manifest | Declares `52d43d18ee5a6d87408bc68d4832869fce8817a9`; 148/148 file hashes match disk AND Git blobs at that SHA; no mismatches |
| Old restore evidence | Old manifest package copied read-only into temp, all 148 hashes verified, actual old serve start and return after failure verified |
| Current newer APIs | `/api/frank-intelligence` 404, `/api/frank-activity-watch` 404; expected old code, not an outage |
| Freshness at audit | V1 LIVE/OK, PID alive, heartbeat age 23.256s, last successful poll 2026-10-22T07:43:40.852060+00:00, lag=0, errors=0, DB readable |
| Loop freshness | `/api/control-health`: OK, updated_at 2026-10-22T07:43:59.065460+00:00 |

Full private paths were inspected locally but are not uploaded. Path identities and runner/plist SHA256 are in audit.txt. Production immutable manifest SHA256 `8f3f4336d9581b5fb8fb509517773088b630e27d7e3a78375ea1a86325c25086`. Audit details: [provenance-health.json](provenance-health.json), [old-git-provenance.json](old-git-provenance.json).

The current Dashboard entrypoint/cwd/manifest identify old installed source; Python loaded-memory equivalence cannot be retroactively attested. V1 `/api/runtime.code_commit=858ef37bbabcfe2f2baeaaeeb95f3478e044defb` is V1 provenance, not Dashboard provenance. Do not mislabel it as Dashboard installed SHA.

## 3. Additional actual Mac temp rehearsal

New QA-only script: `crypto-300-profit-mission/local-agent/scripts/frank_pr157_dashboard_temp_rehearsal.py`, fixed reviewed commit `69dfeafbdd05f73dd9d66e0bfacdaf35b2352248`. Not a production installer; no install mode. Invocation (private local paths supplied as CLI variables):

```sh
python3 -B crypto-300-profit-mission/local-agent/scripts/frank_pr157_dashboard_temp_rehearsal.py --old-source "$READONLY_OLD_RELEASE" --python "$EXISTING_FRANK_VENV/bin/python"
```

Actual run uses existing Frank virtualenv, no dependency installs. Result [full-rehearsal.json](full-rehearsal.json): **PASS, 6/6 directed checks**, 435 candidate files from full fixed-SHA local-agent Git archive, deterministic manifest digest `568c02201905377e83c4fd126ecb37fa02c6baa6f672b6ab62a40c80d155ff5a`. This hash is canonical sorted JSON filename-to-SHA256 map, not a tarball byte hash. No Monster/BSC code is executed; full archive preserves import/config dependency closure without using policy installers.

1. Verify 148 old package files and actually start old Dashboard from copied fixture-only package.
2. Verify all candidate file hashes, atomic temporary active pointer change, actual candidate `serve` start and HTTP static equality plus `/api/runtime`, `/api/frank-intelligence`, `/api/frank-activity-watch` JSON 200.
3. Bind only OS-selected temporary loopback port to inject startup failure; candidate child exits nonzero.
4. Atomically restore temp old pointer, restart old Dashboard child and validate exact old HTML + runtime HTTP.
5. Corrupt staged server.py; manifest checker rejects before switching, active pointer remains old.
6. Recheck source old 148 hashes unchanged. All owned child processes stopped by finally cleanup.

All data roots, control writes, copied old/new artifacts, logs and pointers are under a new TemporaryDirectory. No production database read or copy for this rehearsal. Empty fixture data explicitly yields unknown/missing source rather than pretending LIVE. Evidence-export disabled; environment removes production credentials; non-loopback socket.connect denied/logged. Actual denied network attempts=0. No launchctl action, real service restart or production rollback was performed/proven. The kernel chose an ephemeral port; neither 8766 nor 8765 was used for rehearsal.

Initial local attempt rejected macOS `/tmp` symlink normalization before launching a child; fixed path comparison to resolved temp root. Also preserved virtualenv interpreter invocation path rather than resolving its Python symlink. Final fixed script and directed checks above passed; no product source changed.

## 4. Dashboard-only mechanism — submitted for user decision, not execution

**Do not overwrite the current shared immutable release or run install_mission_meme_launchd.sh.** New Dashboard gets a separate, fixed-SHA directory; Loop and V1 remain on current code and PIDs.

Future authorized operations, in order:

1. At execution time recheck exact Dashboard/Loop/V1 identity, PID/start, 8766 owner, runner/plist/policy identities, fresh health and expected hashes. Drift means STOP; this audit is time-bound.
2. Prepare a NEW Dashboard-only immutable release path using product SHA `31dd598df248ca15f731913a5cbf82e88b981874`, verify all 435 filenames/hashes against canonical manifest. Do not copy candidate config into installed policy paths. Keep old shared directory intact. No merges/cherry-picks/rebuilt unknown SHA.
3. Preserve exact current Dashboard runner bytes/hash, plist bytes/hash and old release manifest in a private rollback bundle, verify readback. Do not store credentials, DB, queues or RPC-file content in Git. Verify existing interpreter imports against candidate before changing runner.
4. Change only Dashboard runner's LOCAL_AGENT literal to new dedicated release path, atomically and with existing mode/ownership. Preserve other environment, production/control roots, port and interpreter. Existing runner's PID/port bookkeeping and cluster-report directory behavior remain Dashboard-only incidental writes, to be explicitly included in production approval. No new Loop, policy or outbox operation.
5. Requires **separate user approval for a Dashboard-only restart**. Only positively identified `com.jerson.frank-meme.dashboard` may be stopped/reloaded. Existing same-label plist remains unchanged; exact-label bootout/bootstrap is a proposed future operation, not performed here. There may be a short Dashboard outage; no zero-downtime or precise duration guarantee. Never call shared installer or restart Loop/V1.
6. Read back new Dashboard PID/start/cwd/hash, 8766 listener, root/runtime/candidates/trades/intelligence/activity APIs and fresh source status. Check Loop/V1 PIDs and protected runner/plist/policy identities unchanged. Do not send a notification as validation.
7. On new start/health failure, restore exact saved Dashboard runner bytes atomically, stop ONLY positively identified new Dashboard service and start ONLY original Dashboard; verify old cwd/hash, new Dashboard PID, 8766 root/runtime. Never restore old Loop policy, replay queue, sign policy, or kill an unknown listener. If service identity or old bundle cannot be positively verified, STOP and request controlled recovery; do not improvise process kills.

Affected future files: NEW dedicated Dashboard release files + private rollback bundle + only dashboard.sh LOCAL_AGENT line; existing Dashboard PID/port bookkeeping/logs. Plist must retain original bytes. Shared old release, mission-loop.sh, Loop plist, V1 code, production SQLite, existing notification queues, installed policy/signature/trust/RPC credential files remain unchanged by release operations. Normal independent Loop/V1 activity can continue; this preparation does not freeze or prove queue contents never change naturally.

**Actual installed source remains old `52d43d18ee5a6d87408bc68d4832869fce8817a9` (manifest and Git-byte verified); proposed final Dashboard installed SHA after separately authorized successful cutover is exactly `31dd598df248ca15f731913a5cbf82e88b981874`. No new SHA is installed now.** QA or evidence commits are never product install SHAs.

## 5. Independent review, final readback and gates

Independent local Gemini reviewer of public QA script at fixed `69dfeafb...`: PASS, no findings. Separate independent review of Dashboard-only release decision: PASS, no blockers. These are source/design reviews, not additional runtime executions by the reviewer. Exact tool results and egress-material hashes: [independent-script-review.json](independent-script-review.json), [independent-plan-review.json](independent-plan-review.json). No private paths, production raw data or credentials sent for review.

Final readback [after-check.json](after-check.json): Dashboard/Loop PID/start, cwd identities, runner and plist hashes unchanged; V1 PID52300 LIVE; 8766 root200; no rehearsal-owned processes remaining. No real notifications, policy signing, launchd mutation, production writes, RPC, transactions, merges or deployments. Main checkout remains unchanged.

**No unresolved P0/P1/P2 preparation blocker. DASHBOARD_ONLY_RELEASE_READY is limited to preparing the explicit user cutover decision.** Real launchd cutover/recovery remains NOT_TESTED because production management is not authorized. This is an execution-time gate requiring separate authorization and readback, not a claimed recovered service. Stop after publishing evidence; do not continue page tests or execute the plan.
