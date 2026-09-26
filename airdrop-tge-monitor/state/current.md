# Airdrop / TGE Monitor State

Updated: 2026-09-26 09:19:24 Asia/Bangkok
Timezone: Asia/Bangkok

- architecture: urgent_plus_4_shards
- expected_schedule: hourly at minute 14, exact_schedule
- last_run: 2026-09-26T09:19:24+07:00
- last_run_status: partial_failure
- last_success: none_after_2026-09-26_repair
- last_shard_0: unknown_after_repair
- last_shard_1: 2026-09-26T09:19:24+07:00
- last_shard_2: unknown_after_repair
- last_shard_3: unknown_after_repair
- consecutive_full_failures: 0
- consecutive_partial_runs: 1
- daily_summary_last_date: 2026-09-25
- daily_summary_backfilled_dates:
  - 2026-09-24
  - 2026-09-25
- open_urgent_events: []
- last_candidate_count: 0
- last_triggered_events: 0
- last_identity_failures: 0
- last_source_failure_projects:
  - Concrete
  - Claynosaurz
  - HEEBOO
  - Space
  - Surf
  - ForecastFDN
  - Hylo
  - OnRe
  - Loopscale
  - Reflect
  - Tydro
  - Theo
  - Neutrl
- note: 09:19:24 run persisted its audit and completed urgent + shard 1, but the original state update did not land. This state file was repaired from that immutable audit. Next exact :14 run must independently create/finalize an audit and update this state.
