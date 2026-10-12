# Frank Mission Loop PR36 merged (code-only) and Mac identity gate — 2026-10-12

## Verified independent review and GitHub code merge
- PR #36 [code](https://github.com/lxxlx2/ChatGPT_mission_record/pull/36): head `c6b64fa94007228d5035cf764895f92b10ad32d9`, reviewed `MERGE_APPROVED`; **production restart DEPLOY_BLOCKED**.
- Exact-head CI [38259482046](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38259482046): 33 focused tests and 1,260 full Frank tests passed, zero skipped.
- GitHub code-only merge commit: `77653116eb5c0da537041d934fdc5871a3d36709`. Only three new files (loop-only rollout script, safety tests, CI workflow) entered main. This is NOT a Mac production release.
- The PR36 independent reviewer used synthetic old checkout `64c1a21c^` as an example and found 12 changed package modules; **actual running Mac old checkout/version is not yet established**.

## Newly implemented Mac pre-release identity observation, no production mutation
Isolated research branch: `ops/frank-loop-mac-identity-readonly-20261012`
- Exact CI test head `82a050d1fa10b903fc644b80486eb406a940ac5b`.
- Script: `crypto-300-profit-mission/local-agent/scripts/frank_loop_mac_identity_readonly_20261012.py` with Git blob `c6ba44737e074592cad2b921a33de8c4bcbad247`.
- Tests: `tests/research/test_frank_loop_mac_identity_readonly_20261012.py`.
- [GitHub Actions 38261871588](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38261871588): **11 focused tests, 1271 total Frank regression tests, zero failed or skipped**. Includes actual Git historical replay, syntax and pyflakes.
- The script reads macOS `launchctl print` for current Loop/Dashboard PIDs and `ps`/`lsof` only to classify the old Loop command and current working directory **without printing raw process paths or arguments**.
- It reads old and pinned Dashboard checkout Git HEADs, hashes `mission_agent/**/*.py` and `scripts/mission_meme_v1.py` from both *on-disk* sources, prints changed **relative code filenames** and records whether `delivery.py` is byte-identical. It checks that both runners reference the same venv and, through standard-library metadata only, that Python >=3.11 and the release's `websockets==15.0.1` dependency is installed.
- The only generated artifact is a sanitized `~/Downloads/frank-loop-identity-readonly-*.zip` containing `identity.json` (code SHA, version, aggregate statuses and module filenames; no RPC URL, credentials, raw DB, absolute source paths, raw process args, Gmail bodies, wallet contents).
- There is **no launchctl kickstart, service cycle, Gmail call, RPC call or SQLite production read/write** in this script.
- Process PID / cwd / runner HEAD only corroborate source association; they **cannot attest immutable in-memory imported Python module bytes**. This limitation is explicitly recorded in the JSON.

## Operational status and next gates
**Mac Loop is NOT upgraded by any step above.** Its last prior read-only clone/Gmail preflight (31/31 PASS) is historical evidence, not proof for a later restart. The Dashboard remains on PR34 code; PR35 opportunity-first layout is code-merged but Mac rollout still separate.

Next:
1. Run this pinned **read-only Mac identity audit**, inspect the exact old checkout SHA, CLI/venv match, and all changed code modules.
2. If code differs, review differences and secure **explicit user approval** of signal-path changes; do not assume old example commit is live.
3. If old `delivery.py` differs from target, **automatic rollback is intentionally unavailable**; present and approve a safe manual-recovery path rather than declaring rollback guaranteed.
4. Separately rerun fresh 31-check existing read-only preflight and independently evaluate first-cycle latency / actual launchd behavior.
5. Request separate explicit operator approval before any production Loop restart; never use general installer that replaces both Loop and Dashboard. Do not auto-enable `MISSION_EVIDENCE_EXPORT_ENABLED`.

Current release status: **CODE_MERGED; MAC_LOOP_DEPLOY=BLOCKED; GMAIL_AND_DB_UNTOUCHED**.
