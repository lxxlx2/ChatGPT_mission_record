# Airdrop / TGE Monitor State

Updated: 2026-09-29 23:09:51 Asia/Bangkok
Timezone: Asia/Bangkok

- architecture: urgent_plus_4_shards_with_stale_recovery
- expected_schedule: hourly at minute 14, exact_schedule
- latest_actual_scheduler_run: 2026-09-29 23:09:22 Asia/Bangkok
- latest_actual_run_status: success
- latest_authoritative_success: 2026-09-29 23:09:22 Asia/Bangkok
- latest_scheduled_shard: 3
- latest_stale_shard_recovery: false
- latest_candidate_count: 0
- latest_triggered_events: 0
- latest_unverified_candidates: 0
- latest_identity_failures: 0
- latest_source_failures: 0
- latest_notification_decision: NO_ACTION
- latest_notification_status: silent
- regression_baseline: 16/16 preserved
- delivery_proof_policy: Gmail Sent message id + readback + event archive

## Open urgent events

- project: Cambria
  event: RSGP Genesis Event Opt-In
  deadline: 2026-09-30T10:00:00+07:00
  delivery_status: recovered_2026-09-27
  gmail_message_id: 1a0e149fa6d9718a

## Recovered rights event

- project: Crusoe
  event: Series F valuation change
  official_date: 2026-09-17
  financing: 3.9B USD
  post_money_valuation: 30.9B USD
  immediate_user_action: none_confirmed
  delivery_status: recovered_2026-09-28
  gmail_message_id: 1a0e801b313706a0

## Latest successful run

- run_path: airdrop-tge-monitor/runs/2026-09-29/230922-final.md
- scheduled_shard: 3
- urgent_checked: Concrete, MetaMask, Claynosaurz, HEEBOO, Space (@intodotspace)
- shard_projects_checked: Cambria, Crusoe, Apptronik, Thalassa Robotics / Thalassa Inc., Fortytwo, Space (@intodotspace), 1X, Aalo Atomics, rTTOK / RepublicX / Republic
- closed_scope_skipped: humans& via Echo/Alpen Capital
- result: no fresh Tier A or registry-mapped Tier B material delta requiring user action
- gmail_attempted: false
- gmail_sent: false

## Health

- 2026-09-29 23:09 run completed successfully with final state persisted.
- ACTION_GATE, known-events, REGISTRY, MONITOR_SPEC and runtime rules were read successfully.
- No source failures or identity failures were recorded in the latest successful run.
- Historical future-dated invalid artifacts remain non-authoritative and are ignored for coverage.
- Pending ACTION delivery survives later NO_ACTION runs until delivery proof exists.
