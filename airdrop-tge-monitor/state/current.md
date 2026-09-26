# Airdrop / TGE Monitor State

Updated: 2026-09-26 15:16:00 Asia/Bangkok
Timezone: Asia/Bangkok

- architecture: urgent_plus_4_shards
- expected_schedule: hourly at minute 14, exact_schedule
- last_run: 2026-09-26T15:13:59+07:00
- last_run_status: success_functional_cache_write_failed
- last_success: 2026-09-26T15:13:59+07:00
- last_shard_0: 2026-09-26T12:12:53+07:00
- last_shard_1: 2026-09-26T13:13:21+07:00
- last_shard_2: 2026-09-26T10:16:44+07:00
- last_shard_3: 2026-09-26T15:13:59+07:00
- consecutive_full_failures: 0
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
- note: 15:13:59 automatic run completed urgent + shard 3 with 0 candidates, 0 identity failures and 0 source failures. Its own state/current cache update was blocked by connector safety checks, but the append-only final audit persisted. From now on final audits are canonical and this mutable file is optional cache only.
