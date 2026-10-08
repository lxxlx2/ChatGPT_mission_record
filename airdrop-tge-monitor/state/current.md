# Airdrop / TGE Monitor State

Updated: 2026-10-08 Asia/Bangkok
Timezone: Asia/Bangkok

- architecture: urgent_plus_4_shards_with_stale_recovery
- expected_schedule: hourly at minute 50
- latest_actual_scheduler_run: 2026-10-08 05:47:29 Asia/Bangkok
- latest_actual_run_status: success
- latest_authoritative_success: 2026-10-08 05:47:29 Asia/Bangkok
- latest_run_path: airdrop-tge-monitor/runs/2026-10-08/054729-final-retry.md
- latest_scheduled_shard: 1
- latest_executed_shard: 1
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
- user_suppressed_scope_skipped: Abstract / ABS

## Open urgent events

- No new ACTION passed ACTION_GATE in the latest run.

## Policy

- Late first discovery may notify once only when the event remains current/open, user-relevant, and Tier A/B verified.
- Stable event keys already delivered are permanently suppressed absent a new material Tier A/B delta.
- User-confirmed completed/closed/refunded/suppressed state outranks later discovery results.

## Health

- Latest authoritative completion: airdrop-tge-monitor/runs/2026-10-08/054729-final-retry.md
- Known-events were processed before discovery.
- Urgent set and Shard 1 completed without unresolved source or identity failures.
- No new Tier A/B material delta affecting unresolved user rights was found.
- No Gmail or ChatGPT notification was attempted because triggered_events=0.

## 2026-10-08 11:49 Asia/Bangkok delivery-integrity audit
- audit_scope: existing automation only; no new monitored project, no schedule changes
- latest_observed_attempt: 2026-10-08 11:47:00 Asia/Bangkok, `runs/2026-10-08/114700-attempt.md`
- latest_observed_partial_final: 2026-10-08 10:49:42 Asia/Bangkok, `runs/2026-10-08/104942-final-retry.md`
- latest_authoritative_success_remains: 2026-10-08 05:47:29 Asia/Bangkok; later attempted runs must not be counted as successful
- missing_completion_artifacts_at_audit: 07:53, 08:50, 09:48, 11:47 attempt timestamps; no matching final or final-retry in enumerated run directory
- 06:47 Cambria candidate: `PENDING_DELIVERY` recorded in `064733-final-retry.md`; no Gmail/event-archive proof; published official X status URL points to a 2026-09-30 post, content and current reopening/extension are not independently retrievable; the previously delivered opt-in notification is `1a0e149fa6d9718a` (2026-09-27), with original deadline Sep 29 23:00 ET. Treat delta as UNVERIFIED_PENDING, do not send an unchanged or expired reminder.
- latest 10:49 run: `partial`, triggered_events=0, three rejected candidates, state update previously blocked
- health: DEGRADED_MISSING_FINALS_AND_STATE_LAG; source completeness must not be implied; next existing run should execute its canonical known-events and urgent checks, reconcile pending Cambria only if official current right/action is demonstrated, and write one terminal final plus state/current
