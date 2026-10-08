# Airdrop / TGE Monitor State
Updated: 2026-10-08 22:53 Asia/Bangkok
Timezone: Asia/Bangkok

- architecture: urgent_plus_4_shards_with_stale_recovery
- expected_schedule: hourly at minute 50
- latest_actual_scheduler_run: 2026-10-08 22:52:06 Asia/Bangkok
- latest_actual_run_status: partial
- latest_authoritative_success: 2026-10-08 05:47:29 Asia/Bangkok
- latest_run_path: airdrop-tge-monitor/runs/2026-10-08/225206-final-retry.md
- latest_scheduled_shard: 2
- latest_executed_shard: 0
- latest_stale_shard_recovery: true
- latest_candidate_count: 2
- latest_triggered_events: 0
- latest_identity_failures: 0
- latest_source_failures: 1
- latest_notification_decision: NO_ACTION
- latest_notification_status: silent

## Durable known events
- UNICRED #230: COMPLETED_NO_REMAINING_ACTION
- Concrete CT claim-open: delivered once, unchanged suppressed
- HEEBOO claim-open: delivered, unchanged suppressed
- Reflect USDC+ recovery: delivered, unchanged suppressed
- Surf Season 1 referral claim: delivered, unchanged suppressed
- MetaMask Money Sweepstakes: delivered, unchanged suppressed
- Cambria RSGP opt-in: delivered 2026-09-27, unchanged suppressed
- humans& via Echo/Alpen Capital: CLOSED_FULLY_REFUNDED
- Abstract / ABS: USER_SUPPRESSED
- Loopscale independent TGE discovery: SUPPRESSED per registry

## Pending / health
- Cambria 2026-09-30 Foundation post claiming Oct 8 extension: UNVERIFIED_PENDING, current first-party action readback unavailable. Do not resend without new Tier A/B evidence.
- Neutrl redemption: candidate identity mismatch (@Neutrl vs registry @neutrl_labs); no ACTION.
- Autheo THEO: unrelated to Theo Network; rejected identity collision.
- Earlier attempts without terminal finals remain historical gaps; 2026-10-08 18:45 attempt also lacks observed terminal.
- 2026-10-08 19:54 attempt plus 19:57 terminal final-retry persisted.
- 2026-10-08 20:50 invocation: partial; terminal 205001-final.md persisted; historical source gap Cambria.
- Last fully successful run remains 2026-10-08 05:47:29 Asia/Bangkok; partial run is not success.
- 2026-10-08 22:52 invocation: attempt 225206-attempt.md and terminal 225206-final-retry.md persisted. Scheduled Shard 2, executed stale Shard 0; 14 unique projects checked; 2 candidates, 0 ACTION, 1 Cambria source gap. Primary final blocked; fallback terminal successful. No Gmail or user notification.\n- 2026-10-08 21:50 attempt remains without observed terminal final; historical health gap.\n- No new Tier A/B material ACTION; Gmail not attempted; ChatGPT silent.
