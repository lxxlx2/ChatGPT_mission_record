# Airdrop / TGE Monitor State

Updated: 2026-10-02 Asia/Bangkok
Timezone: Asia/Bangkok

- architecture: urgent_plus_4_shards_with_stale_recovery
- expected_schedule: hourly at minute 50
- latest_actual_scheduler_run: 2026-10-02 13:51:03 Asia/Bangkok
- latest_actual_run_status: success
- latest_authoritative_success: 2026-10-02 13:51:03 Asia/Bangkok
- latest_scheduled_shard: 1
- latest_executed_shard: 1
- latest_stale_shard_recovery: false
- latest_candidate_count: 1
- latest_triggered_events: 1
- latest_unverified_candidates: 0
- latest_identity_failures: 0
- latest_source_failures: 0
- latest_notification_decision: ACTION_DELIVERED_ONCE
- latest_notification_status: delivered_once_then_deduped

## Durable known-events

- known_events_checked: true
- due_action_windows: 0
- completed events remain suppressed
- UNICRED #230 2026-10-01 unstake/unlock: COMPLETED_NO_REMAINING_ACTION
- Concrete CT claim-open: DELIVERED_ONCE_LATE_DISCOVERY; unchanged repeats suppressed
- closed_scope_skipped: humans& via Echo/Alpen Capital

## Open urgent events

- Concrete CT claim-open was delivered once at 2026-10-02 13:51 Asia/Bangkok. It had already been open earlier; the user allows one first notification even when discovery is late, provided the event is still current/open and Tier A/B verified. Future unchanged repeats are suppressed.

## Policy correction

- The temporary hard rule `discovery lag >2h => MISSED_TIMELINESS_WINDOW => NO_ACTION` has been removed.
- Current policy: late first discovery may notify once if the event is still current/open, relevant, and verified by Tier A/B.
- The alert must not imply that the event just opened when it opened earlier.
- After one delivered alert for the stable event key, unchanged reminders are suppressed; only a new material Tier A/B delta may alert again.

## Health

- Scheduler persistence for the 13:51 run was successful.
- Concrete CT delivery remains valid as the one allowed first notification under current user policy.
- Future runs must enforce stable event-key dedupe and material-delta-only re-alerting.
