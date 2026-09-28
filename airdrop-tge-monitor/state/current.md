# Airdrop / TGE Monitor State

Updated: 2026-09-28 19:34:00 Asia/Bangkok
Timezone: Asia/Bangkok

- architecture: urgent_plus_4_shards_with_stale_recovery
- expected_schedule: hourly at minute 14, exact_schedule
- latest_actual_scheduler_run: 2026-09-28 ~19:19 Asia/Bangkok
- latest_actual_run_status: incomplete_provisional
- latest_authoritative_success_before_that: 2026-09-28 17:12 Asia/Bangkok
- clock_integrity_incident: confirmed_2026-09-28
- invalid_future_timestamp_files:
  - 201500-final-retry.md
  - 221500-final.md
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

## Health

- The previous state cache was stale at 2026-09-27 and could not be used as reliable shard freshness authority.
- The 2026-09-28 19:19 run persisted only a provisional final and did not complete.
- Future-dated artifacts are ignored for coverage.
- Pending ACTION delivery now survives later NO_ACTION runs until delivery proof exists.
