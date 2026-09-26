# Airdrop / TGE Monitor State

Updated: 2026-09-26 15:10:00 Asia/Bangkok
Timezone: Asia/Bangkok

- architecture: urgent_plus_4_shards
- expected_schedule: hourly at minute 14, exact_schedule
- last_run: 2026-09-26T14:14:47+07:00
- last_run_status: failed_missing_persisted_run
- last_success: 2026-09-26T13:13:21+07:00
- last_shard_0: 2026-09-26T12:12:53+07:00
- last_shard_1: 2026-09-26T13:13:21+07:00
- last_shard_2: 2026-09-26T10:16:44+07:00
- last_shard_3: 2026-09-26T11:11:39+07:00
- consecutive_full_failures: 1
- consecutive_partial_runs: 0
- daily_summary_last_date: 2026-09-25
- daily_summary_backfilled_dates:
  - 2026-09-24
  - 2026-09-25
- open_urgent_events: []
- last_candidate_count: 0
- last_triggered_events: 0
- last_identity_failures: 0
- last_source_failure_projects: []
- note: 13:13 run is repaired/finalized as success. Scheduler triggered again at 14:14:47 but persisted no automatic audit/state update; recorded as missing run. Runtime now uses append-only start/final audit files. Last verified success remains 13:13:21.
