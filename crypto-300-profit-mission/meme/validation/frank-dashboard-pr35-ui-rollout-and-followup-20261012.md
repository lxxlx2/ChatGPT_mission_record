# Frank Dashboard PR35-only rollout and screenshot follow-ups — 2026-10-12

## User request and screenshot fact check
The user authorized **Dashboard UI deployment first**, then asked to repair the misleading sell/accumulation Gmail wording and reduce the observed-token research table. This does **not** authorize the separate PR36 production Mission Loop restart.

Screenshot evidence: current deployed Mac PR34 Dashboard showed stats before a long watch pool (272 observed, 11 focused) and follow opportunities lower down. A newly delivered `NO_BUY` email showed historical `多次强加仓` in subject while latest action was SELL, inventory unknown and last historical buy payment 15,000 USDC. The old dashboard source and fixed Gmail renderer confirmed these represent UI clarity issues rather than evidence of falsely claimed trade execution.

## P1 Dashboard-only release ready — waiting for local Mac execution receipt

- PR35 already code-merged as `62697bf98606c19c5709c27006a6a40d9408db97`.
- Operational branch: `ops/frank-dashboard-pr35-only-rollout-20261012`.
- Strict pinned release helper: `crypto-300-profit-mission/local-agent/scripts/frank_dashboard_pr35_only_rollout_20261012.py` Git blob SHA `d8a3189f3e15a8311d5bf3a8ad54e15e169279d0`; exact tested helper HEAD `a1671e87c41f449e20c9bdca7761e30829b87d41`.
- [GitHub CI 38270688861](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38270688861): **11 focused UI/rollout tests and 1267 complete Frank tests passed, 0 skipped/fail**. Tested exact HEAD; includes real historical Git archive playback.
- Helper accepts `--apply-dashboard`, snapshots live SQLite read-only into owner-only backups and validates detached isolated candidate HTTP server. It requires literal PR35 DOM order and existing J7/BPXX read-only historical fields. It verifies current Dashboard listener belongs to old PID, changes only Dashboard `LOCAL_AGENT` to the pinned source, restarts only Dashboard and checks old Loop PID and script hash stayed unchanged.
- The user was given copy-paste zsh that downloads this exact helper over HTTPS, verifies Git blob SHA and then runs only `--apply-dashboard`.
- **No Mac execution receipt yet in this conversation.** Do NOT mark Mac Dashboard as deployed from GitHub CI alone; wait for `LIVE_PR35_OPPORTUNITY_FIRST=PASS`, `MISSION_LOOP_PID_UNCHANGED=PASS`, `DASHBOARD_RELEASE=SUCCESS` and browser check.

## P2 Future Gmail copy issue — Draft PR37
- [PR #37](https://github.com/lxxlx2/ChatGPT_mission_record/pull/37): `review/frank-notification-copy-20261012`, HEAD `64ffe60797d1903d808d7d3223a6fd5704f82a28`, Draft.
- [GitHub CI 38271418409](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38271418409): **35 focused and 1266 full tests passed**, 0 skipped.
- SELL/EXIT/SELL_POSITION_UNRESOLVED email title now prioritizes latest sell and unknown inventory, while historical MULTIPLE pattern is explicitly separate; last buy contribution is explicitly historical; audit section groups tx/Mission IDs. Unmodified `GmailDelivery._wire_body` preserves stored previous-provider readback, and no historical Gmail re-render/backfill/send path is introduced.
- **Separate independent review required before merge.** Live PR34/older Loop does not receive this template update from P1, and it must NOT be used as pretext to restart Mission Loop. Any later live Loop deploy of the new renderer requires a fresh rollback compatibility/replay review.

## P3 Compact observed-token research panel — Draft PR38
- [PR #38](https://github.com/lxxlx2/ChatGPT_mission_record/pull/38): `review/frank-watchpool-collapse-20261012`, HEAD `adc900cef0efc05dde3daaf3507b07a47ebfbbdd`, Draft.
- [GitHub CI 38272215542](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38272215542): **7 focused DOM/layout tests and 1263 full Frank tests passed**, 0 skipped/fail.
- The existing watch pool is `<details>` collapsed by default, with visible focus and total counts. All original filters, search, blockchain evidence, CA links, history and no-action disclaimers remain. `app.js` only reuses the existing WATCH_NOW status filter; no API/server/decision/Gmail changes.
- **Separate independent layout review required**; do not include PR38 in the currently pending PR35-only Mac release.

## Release sequencing
1. Operator executes already-provided **Dashboard-only PR35** Mac command and supplies terminal and screenshot. Confirm success or handle rollback before declaring deployment.
2. Independent review PR37 and PR38; fix findings; run exact-head regression; merge only when approved.
3. Deploy PR38 only in a future separate Dashboard-only controlled release. Keep PR37 template code out of a Dashboard-only release unless it has been reviewed for unrelated source side effects; it requires a separate Loop release.
4. PR36 Loop upgrade remains a **separate, not yet authorized** production process despite earlier prepare-only PASS. Do not restart Loop, mutate production DB, resend historical Gmail, or enable CA evidence exports in this P1/P2/P3 workflow.
