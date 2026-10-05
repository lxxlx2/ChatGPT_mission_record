# Airdrop / TGE Monitor State

Updated: 2026-10-05 Asia/Bangkok
Timezone: Asia/Bangkok

- architecture: urgent_plus_4_shards_with_stale_recovery
- expected_schedule: hourly at minute 50
- latest_actual_scheduler_run: 2026-10-05 15:00:03 Asia/Bangkok
- latest_actual_run_status: success
- latest_authoritative_success: 2026-10-05 15:00:03 Asia/Bangkok
- latest_run_path: airdrop-tge-monitor/runs/2026-10-05/150003-final.md
- latest_scheduled_shard: 3
- latest_executed_shard: 3
- latest_stale_shard_recovery: false
- latest_candidate_count: 0
- latest_triggered_events: 0
- latest_unverified_candidates: 0
- latest_identity_failures: 0
- latest_source_failures: 0
- latest_notification_decision: NO_ACTION
- latest_notification_status: silent

## Durable known-events

- known_events_checked: true
- due_action_windows: 0
- completed events remain suppressed
- UNICRED #230 2026-10-01 unstake/unlock: COMPLETED_NO_REMAINING_ACTION
- Concrete CT claim-open: DELIVERED_ONCE_LATE_DISCOVERY; unchanged repeats suppressed
- HEEBOO claim-open: DELIVERED; unchanged repeats suppressed
- Reflect USDC+ recovery claim: DELIVERED; unchanged repeats suppressed
- Surf Season 1 referral rewards claim: DELIVERED; unchanged repeats suppressed
- MetaMask Money Sweepstakes registration: DELIVERED; unchanged repeats suppressed
- Cambria RSGP Genesis opt-in: DELIVERED_RECOVERY; unchanged repeats suppressed
- closed_scope_skipped: humans& via Echo/Alpen Capital

## Open urgent events

- No new ACTION passed ACTION_GATE in the latest run.

## Policy

- Late first discovery may notify once only when the event remains current/open, user-relevant, and Tier A/B verified.
- Stable event keys already delivered are permanently suppressed absent a new material Tier A/B delta.
- User-confirmed completed/closed/refunded/suppressed state outranks later discovery results.

## Health

- Latest final audit completed successfully.
- Known-events were processed before discovery.
- Urgent set and Shard 3 completed without unresolved source or identity failures.
- No new Tier A/B material delta affecting unresolved user rights was found.
- No Gmail or ChatGPT notification was attempted because triggered_events=0.
