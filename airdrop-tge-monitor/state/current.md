# Airdrop / TGE Monitor State

Updated: 2026-09-27 12:23:00 Asia/Bangkok
Timezone: Asia/Bangkok

- architecture: urgent_plus_4_shards_with_stale_recovery
- expected_schedule: hourly at minute 14, exact_schedule
- last_run: 2026-09-27T12:12:00+07:00
- last_run_status: success
- last_success: 2026-09-27T12:12:00+07:00
- last_shard_0: 2026-09-27T12:12:00+07:00
- last_shard_1: stale; no current-morning final found
- last_shard_2: 2026-09-27T10:13:11+07:00
- last_shard_3: 2026-09-27T11:15:45+07:00
- consecutive_full_failures: 0
- delivery_proof_policy: Gmail Sent message id + readback + event archive
- open_urgent_events:
  - project: Cambria
    event: RSGP Genesis Event Opt-In
    deadline: 2026-09-30T10:00:00+07:00
    delivery_status: recovered_2026-09-27
    gmail_message_id: 1a0e149fa6d9718a
- last_candidate_count: 0
- last_triggered_events: 0
- last_identity_failures: 0
- last_source_failure_projects: []

## Health notes
- Latest final audit at 12:12 is healthy.
- Shard 1 coverage is stale because several scheduled cycles produced no final audit.
- Runtime now substitutes the oldest >6h stale shard for the scheduled shard, one shard per run.
- Cambria alert delivery gap was repaired at 12:15 with Gmail readback and event archive.
- The Sep-14 Space cross-project alert remains RETRACTED. A formal correction email was delivered on 2026-09-27, message id 1a0e149f1f9d03be.
