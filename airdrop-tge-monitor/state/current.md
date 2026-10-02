# Airdrop / TGE Monitor State

Updated: 2026-10-02 13:51:03 Asia/Bangkok
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
- latest_notification_decision: ACTION
- latest_notification_status: delivered
- delivery_proof_policy: Gmail Sent message id + readback + event archive

## Durable known-events

- known_events_checked: true
- due_action_windows: 0
- completed events remain suppressed
- UNICRED #230 2026-10-01 unstake/unlock: COMPLETED_NO_REMAINING_ACTION, suppress reminders
- closed_scope_skipped: humans& via Echo/Alpen Capital

## Open urgent events

- Concrete CT claim is live for eligible users; alert delivered this run. Future unchanged reminders suppressed by event key `concrete:ct_claim_open:2026-09-30`.

## Latest successful run

- run_path: airdrop-tge-monitor/runs/2026-10-02/135103-final.md
- scheduled_shard: 1
- executed_shard: 1
- urgent_checked: Concrete, MetaMask, Claynosaurz, HEEBOO, Space (@intodotspace)
- shard_projects_checked: Surf, ForecastFDN, Hylo, OnRe, Loopscale, Reflect, Tydro, Theo, Neutrl, Concrete
- result: one fresh Tier A Concrete claim action delivered; no other qualifying ACTION
- candidate_count: 1
- action_count: 1
- identity_failures: 0
- source_failures: 0
- gmail_attempted: true
- gmail_sent: true
- gmail_message_id: 1a0fb623103c8948
- event_path: airdrop-tge-monitor/reports/events/2026/2026-10/2026-10-02/135103-concrete-ct-claim-open.md

## Health

- 2026-10-02 13:51:03 run completed with authoritative final persisted.
- ACTION_GATE, known-events, REGISTRY, MONITOR_SPEC and AUTOMATION_RUNTIME were read before monitoring.
- Concrete claim passed canonical identity and Tier A gate and has Gmail Sent readback plus event archive.
- No source or identity failures remained unresolved.
