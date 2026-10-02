# Airdrop / TGE Monitor State

Updated: 2026-10-02 13:54 Asia/Bangkok
Timezone: Asia/Bangkok

- architecture: urgent_plus_4_shards_with_stale_recovery
- expected_schedule: hourly at minute 50
- latest_actual_scheduler_run: 2026-10-02 13:51:03 Asia/Bangkok
- latest_actual_run_status: success_but_alert_reclassified_stale_by_user_feedback
- latest_authoritative_success: 2026-10-02 13:51:03 Asia/Bangkok
- latest_scheduled_shard: 1
- latest_executed_shard: 1
- latest_stale_shard_recovery: false
- latest_candidate_count: 1
- latest_triggered_events: 0 after correction
- latest_unverified_candidates: 0
- latest_identity_failures: 0
- latest_source_failures: 0
- latest_notification_decision: CT_ALERT_RECLASSIFIED_NO_ACTION
- latest_notification_status: historical_delivery_preserved_but_future_suppressed

## Durable known-events

- known_events_checked: true
- due_action_windows: 0
- completed events remain suppressed
- UNICRED #230 2026-10-01 unstake/unlock: COMPLETED_NO_REMAINING_ACTION
- Concrete CT claim-open: USER_SUPPRESSED_STALE_ALERT; unchanged reminder permanently suppressed
- closed_scope_skipped: humans& via Echo/Alpen Capital

## Open urgent events

- none from the corrected 13:51 run.

## Correction to 2026-10-02 13:51 run

- The run delivered `[空投/TGE提醒][Concrete][CT Claim开放]` with Gmail id `1a0fb623103c8948`.
- User feedback established that the claim had already been live for many hours before discovery, so the notification was not timely.
- Historical Gmail/event archive remains as audit evidence and is not rewritten as if it never happened.
- Canonical ACTION_GATE now rejects plain claim-open / registration-open / TGE-live / listing-live alerts first discovered more than 2 hours after canonical publication/effective time, unless a genuinely new Tier A/B delta creates immediate entitlement risk.
- Future unchanged Concrete CT claim-open reminders are suppressed via `state/known-events.md`.

## Health

- Scheduler persistence for the 13:51 run was successful.
- Notification quality/timeliness gate was insufficient and has been corrected.
- Next runs must apply `discovery_lag_minutes` and `MISSED_TIMELINESS_WINDOW` before any ACTION decision.
