# Frank Mission Loop upgrade: read-only gate handoff (2026-10-12)

## Existing Mac production status (user-visible evidence)

The user-provided live Dashboard screenshot after the prior successful dashboard-only rollout showed: green Frank status, heartbeat age 24 seconds, 211 24h indexed signatures, 9 local recognized buys, 4 local recognized sells, 6 recent review entries, observed token pool 236, 7 model-marked holdings (on-chain balances not independently verified), 2 holdings needing verification, zero current follow candidates, and historical notification review 15 Gmail with the corrected label "数据库无发送尝试记录".

These UI values are **only screenshot observations** and do not independently prove all mail history or production database consistency.

The earlier Mac operator output independently reported `DASHBOARD_RELEASE=SUCCESS`, `DASHBOARD_STILL_LIVE=PASS`, `MISSION_LOOP_PID_UNCHANGED=PASS`, and `MISSION_LOOP_FILE_UNCHANGED=PASS` for rollout pin `6a5b7e8a533f99c871e31f9674329fcb4f929cc2`. Accordingly, Dashboard has moved, but live Mission Loop remains on its previous code path.

## Critical behavior established by merged source

- `MissionMemeService.cycle()` can update the **writable** control SQLite and drain Gmail/local notifications when the pre-approved live-delivery policy gate is true. Therefore never run a live `cycle` or new `loop` against production DB just to test compatibility.
- `GmailDelivery.drain()` checks source-decision age before first Gmail send. Historical `MANUAL_REVIEW` is excluded. `SENDING`/`SENT_UNVERIFIED` (and rows with provider message ID) reconcile via provider readback, not immediate resend.
- A fresh old `PENDING` or `RETRYABLE_ERROR` Gmail row may still be eligible for a new send. A fresh local `PENDING` or `RETRY_PENDING` row may cause a desktop notification. An upgrade must not reset the control database, policy, or delivery state to bypass these identity guards.
- The general installer `scripts/install_mission_meme_launchd.sh` replaces **both** LaunchAgents, including live Mission Loop and Dashboard; it is explicitly **not** a safe upgrade tool for this handoff.
- Evidence Git export is opt-in via `MISSION_EVIDENCE_EXPORT_ENABLED=1`, and remains explicitly out of scope while the CA async Future issue L3 is unresolved.

## Implemented preparation

New pinned read-only Mac preflight script:
`crypto-300-profit-mission/local-agent/scripts/frank_loop_upgrade_readonly_preflight_20261012.py`

Capabilities:
1. Requires the previously deployed Dashboard to point to the exact reviewed PR #34 merged commit.
2. Confirms live loop and Dashboard PIDs are stable, installation pointers exist, expected policy SHA matches the independently installed approved SHA, and the control heartbeat is fresh.
3. Checks Gmail OAuth secret **file permission only**, without printing or refreshing tokens.
4. Takes transactionally consistent, read-only SQLite snapshots inside a disposable temp directory and validates the **new** ControlDB schema bootstrapping against the **copied** control DB only.
5. Compares all existing decision/delivery counts and statuses before/after simulated schema bootstrapping; never calls `cycle`, `loop`, OAuth `ready`, Gmail `send`, live RPC, GitHub write APIs or `launchctl kickstart`.
6. Classifies pending Gmail/local state. Fresh potentially-sendable preexisting notifications are a **hard gate**; stale preexisting notifications and uncertain already-attempted records are separately reported.
7. Prints only PASS/BLOCKED checks and creates a sanitized aggregate-only ZIP under `~/Downloads`. The SQLite snapshots and any locally private credentials never leave the Mac.

[GitHub Actions #38209745669](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38209745669) completed **SUCCESS** against operations branch commit `63ce17b375d999dae64a890216248013e1026375`: 7 synthetic no-send safety tests passed, all **1230** combined local-agent tests passed (0 skipped), pyflakes and syntax checks passed.

## Next gate

**LOOP_DEPLOYMENT=NOT_STARTED**. Before any live Mission Loop restart, collect actual Mac preflight result and inspect aggregate pending statuses. If the preflight fails, investigate; never override by setting `--live-delivery` or clearing status history.

If it passes, prepare a separate **loop-only, explicitly opted-in, reversible** release path with fresh SQLite backups, PID/current-policy invariants, and legacy notification anti-replay checks immediately before restart. The existing Dashboard should not be restarted again for a Loop update.

Any saved receipt on Git shall omit raw database bytes, addresses, token IDs, OAuth material, local absolute paths and signer/RPC secrets.
