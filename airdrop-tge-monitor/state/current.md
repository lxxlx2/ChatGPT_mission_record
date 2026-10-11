# Airdrop / TGE Monitor State
Updated: 2026-10-11 (manual recovery after 13:04 scheduler final) Asia/Bangkok
Timezone: Asia/Bangkok
- expected_schedule: hourly :00 Asia/Bangkok (user-approved 2026-10-10)
- latest_actual_run: 2026-10-11 13:04:55 Asia/Bangkok
- latest_actual_run_status: partial
- latest_authoritative_success: 2026-10-10 07:52:16 Asia/Bangkok
- latest_run_path: airdrop-tge-monitor/runs/2026-10-11/130455-final-retry.md
- latest_attempt_path: airdrop-tge-monitor/runs/2026-10-11/130209-attempt.md
- latest_scheduled_shard: 1
- latest_executed_shard: 1
- stale_shard_recovery: true
- latest_candidate_count: 5
- latest_triggered_events: 1 (Space Oct15 event qualified; one verified delivery)
- latest_identity_failures: 1
- latest_source_failures: 4
- latest_notification_decision: ACTION_DELIVERED_MANUAL_RECOVERY
- latest_notification_status: SENT_READBACK_VERIFIED (Gmail 1a129b8b2ddd1607)
- latest_gmail_attempted: true (13:04 blocked, later manual recovery succeeded)

## Durable known-events
Read state/known-events.md before discovery. Delivered Concrete CT claim, HEEBOO claim, Surf referral rewards, Reflect recovery, MetaMask Sweepstakes and Cambria opt-in are suppressed unless new Tier A/B material delta is confirmed. UNICRED #230 completed. humans& fully refunded and CLOSED; Abstract user-suppressed; Grass and Backpack excluded. Independent Loopscale TGE scope removed.

## Pending and health
- Concrete additional USDC allocation/date remains UNVERIFIED_CANDIDATE: canonical claim page inaccessible, no independent first-party evidence establishing a new entitlement. Keep silent.
- Last observed prior shard finals: shard0 2026-10-10 17:54 partial; shard1 2026-10-10 13:55 partial; shard2 2026-10-10 22:49 partial; shard3 2026-10-10 15:52 partial. Current shard1 partial at 2026-10-11 00:05 does not establish complete coverage.
- 2026-10-10 23:45 attempt commit was observed, without confirmed terminal final. Other prior attempt-only gaps remain unresolved.
- 2026-10-11 00:04 attempt write was blocked by GitHub safety check; terminal 000512-final.md was successfully created. Run is partial, not authoritative success.
- Current schedule is HH:00; no task ID/title/scope/recipient/notification gate changes. No extra daily email.

- 2026-10-11 06:04:59: partial urgent + stale shard1, terminal final-retry persisted. No new verified ACTION. Concrete additional allocation, Neutrl redemption and Autheo/THEO name collision were suppressed by ACTION_GATE; five source gaps. Scheduled shard2 deferred to rotation. Attempt-only historical gaps remain unresolved.

- 2026-10-11 07:05:54: partial urgent + shard3, 070554-final-retry.md persisted; attempt and primary final writes blocked. No Tier A/B new ACTION. Concrete extra allocation unverified; Cambria charter mint 4096/4096 sold out; other checked projects no verified material delta. No Gmail/App notification. Historical attempt-only gaps remain.

- 2026-10-11 10:02:47: partial urgent + stale shard1; 100247-final-retry.md persisted, attempt and primary final blocked by connector safety check. No new Tier A/B verified ACTION. Space Oct 15 claim sunset remains pending because original Telegram and docs unavailable for direct readback; Concrete extra allocation and Neutrl redemption unverified for user-level new rights. THEO/Autheo collision suppressed. No Gmail/App notification. Prior attempt-only gaps unresolved.

- 2026-10-11 13:04:55: partial urgent + shard1, one Space public SPC claim dApp sunset ACTION (Oct 15) met official evidence gate. Scheduled Gmail was blocked by execution safety check, saved final-retry with pending_delivery. Existing event subsequently sent in explicit manual recovery after Gmail Sent dedupe, id 1a129b8b2ddd1607, readback PASS; archive 040407-space-spc-claim-dapp-sunset.md readback PASS; stable event_key now added to state/known-events.md and unchanged reminder suppressed. All other four candidates remain without eligible ACTION; four source gaps and one identity rejection; overall scheduler health remains DEGRADED_PARTIAL. This manual success does not prove scheduled Gmail write recovered.
