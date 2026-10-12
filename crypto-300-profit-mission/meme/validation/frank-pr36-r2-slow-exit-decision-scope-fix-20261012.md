# Frank PR #36 second independent review — applied reviewer patch; deploy remains BLOCKED (2026-10-12)

## Independent review inputs
User-provided `files(1).zip` SHA256 `fefce514b883f2f25389201ccb3333a622b53622a7d10f4309a92db95937be16` contained exactly:
- `frank-loop-rollout-v4-fixes.patch` (6917 bytes; SHA256 `5af67299688bd97f1149d3135a1c1c5e6a61e48133088c6330bd14c18fb12b8b`);
- `frank-loop-rollout-fault-injection-v2.py` (11095 bytes; SHA256 `33832284803f9c32bc61b64c5a2fac451c214f53b99a2589dd43b11f7f50cb32`).

These artifacts were inspected without executing the uploaded fault-injection program. The review claimed local author head `97012aaa58ae6d3666ca27676497f309786dc7bd` and unpublished local patch commit `a3e042a6124c0a1774f9eb1e4897b7b560d80528`. The raw patch explicitly recorded **old Git blobs** `25438302ae4f01cf84e4dc8c6e9b7f00bd50b971` for rollout script and `9334b219f046d00a1ab0cf928a83085f929cb538` for tests, and these exactly matched live PR #36 file blobs before application.

## Issues confirmed by source/review

1. **Incomplete critical-code-difference gate (BLOCKER)**: explicit set of 5 filenames missed `mission_agent/signals/store.py` (USDC classification/quote state) and wallet/transfer/other Python decision input paths. Replaced with a complete `mission_agent/**/*.py` per-module digest comparison. Additional protection tracks `scripts/mission_meme_v1.py` CLI entrypoint. Relative filenames are now output as `DECISION_MODULE_CHANGED=<path>`; any changes require `--approve-signal-code-change` for apply, and prepare mode lists the exact deltas.
2. **Slow old PID exit (operations reliability)**: previous code raised `OLD_LOOP_PROCESS_STILL_ALIVE` immediately at first polling opportunity after `kickstart -k`. Revised it to poll until old PID actually exits and only accept a heartbeat after the first observed old-PID exit. If it still exists at timeout, fails closed, does not automatically restart an extra Loop.
3. Kept first-review fixes: interrupt handling, stale-heartbeat rejection, byte-exact restore if old Loop untouched, strict legacy Gmail read-only rollback gate, byte-identical legacy `delivery.py` requirement for auto rollback, PID sanity, no dashboard kickstart, policy SHA/preflight pin.

Patch application to the GitHub review branch is explicit, not a claim that unpublished Claude patch commits existed remotely:
- script merged reviewer patch `b63de60a4d0c26e23871899ebb60a1fa124d5c55` (Git blob `5c900dd28aca8bcfb95e2d70fd77070cf9a59044`, matches patch's expected blob);
- tests `a7251f25bdb60650a7a912786302794748ded9c2`;
- include runtime CLI entrypoint and relative per-file diff print in subsequent changes;
- final exact PR #36 head `c6b64fa94007228d5035cf764895f92b10ad32d9`.

## Independent CI
[GitHub Actions 38259482046](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38259482046), head `c6b64fa94007228d5035cf764895f92b10ad32d9`: **SUCCESS**, 33 focused rollout tests and 1260 full local-agent tests passed, 0 failed or skipped. Syntax, pyflakes and existing no-live-Mac side effect static checks passed. The full suite includes real historical Git archive replay. CI runs on isolated Linux test machines; Mac's real launchd and OAuth/Gmail providers were **not** exercised.

## Status and release gates

**PR36: DRAFT. MERGE/DEPLOY=NOT_AUTHORIZED in this report.** Code/tests committed and CI validated; no Mac restart, SQLite writes, Gmail send, actual source switch or merge to main occurred during this review.

The original Mac preflight 31/31 PASS is retained as *historical* evidence; **do not treat it as a new live preflight** for the current code. Before deploy: (1) latest exact-head independent review; (2) Mac read-only/live runner and original version evidence; (3) explicit evaluation of the decision-module file differences and approval of any actual signal behavior change; (4) choose manual recovery if old `delivery.py` diverges (automatic rollback intentionally disabled); (5) rerun freshly pinned read-only preflight; (6) separate explicit operator approval for any live Loop restart.

Residual limitation: local notification delivery remains at-least-once; a timeout/crash in the fresh under-600s window can repeat a desktop alert. No guarantee of exactly-once providers. Other modules or scripts outside the compare scope should be evaluated based on their actual invocation, not presumed identical.
