# Airdrop / TGE Monitor State
Updated: 2026-10-09 14:53 Asia/Bangkok
Timezone: Asia/Bangkok

- architecture: urgent_plus_4_shards_with_stale_recovery
- expected_schedule: hourly at minute 50
- latest_actual_scheduler_run: 2026-10-09 14:52:30 Asia/Bangkok
- latest_actual_run_status: partial
- latest_authoritative_success: 2026-10-08 05:47:29 Asia/Bangkok
- latest_run_path: airdrop-tge-monitor/runs/2026-10-09/145147-final-retry.md
- latest_scheduled_shard: 2
- latest_executed_shard: 2
- latest_stale_shard_recovery: false
- latest_candidate_count: 2
- latest_triggered_events: 0
- latest_identity_failures: 0
- latest_source_failures: 2
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

- 2026-10-08 23:53 invocation: terminal 235356-final.md persisted, partial, Shard 3, Cambria source gap; state cache previously stale.
- 2026-10-09 00:53 invocation: attempt 005337-attempt.md and terminal 005337-final-retry.md persisted. Scheduled Shard 0; executed stale Shard 2. 13 unique projects checked; 3 candidates; 0 ACTION; 2 identity rejections; 1 Cambria source gap. Primary final write blocked; compact fallback successful. No Gmail or user notification.
- Shard freshness from observed terminals: shard 0 2026-10-08 22:53 partial; shard 1 2026-10-08 19:57 partial; shard 2 2026-10-09 00:54 partial; shard 3 2026-10-08 23:54 partial. Last fully successful run unchanged at 2026-10-08 05:47:29.

- 2026-10-09 02:55 Asia/Bangkok invocation: 025407-final-retry.md persisted (commit bf96d3c748c3e8c2f08c2cbed29fcd90a76d8da1). Scheduled shard 2, executed stale shard 1; urgent + shard 1 checked, no verified Tier A/B new ACTION; triggered_events: 0, Gmail not attempted, user silent. Attempt and primary final writes blocked by safety checks. Cambria extension remains unverified/current-action source gap. Partial; latest fully successful run remains 2026-10-08 05:47:29. Earlier 014623-attempt.md lacks observed terminal.

- 2026-10-09 03:47:34 invocation: 034734-final.md persisted (commit 30e64bc370038d72f0c2b3c77309f0504cbd6498). Scheduled and executed Shard 3, urgent + 13 unique projects in scope; 2 Cambria unverified candidates, 0 ACTION, 1 Cambria source gap, no Gmail or user notification. Attempt write blocked by tool safety checks. Latest fully successful run remains 2026-10-08 05:47:29; current partial. Shard 3 last partial coverage 2026-10-09 03:47:34. Earlier attempt-only windows remain historical gaps.

- 2026-10-09 04:55:51 invocation: attempt 045459-attempt.md persisted; primary final blocked by safety checks; terminal 045459-final-retry.md persisted (commit c80f2905a392852b1306b803a29caeac7b7d7448). Scheduled Shard 0, executed stale Shard 1; urgent plus 13 unique in-scope projects; 4 candidates, 0 ACTION, 1 Neutrl handle identity drift, 2 source gaps (Concrete Additional USDC allocation and Cambria opt-in extension). Gmail not attempted, user silent. Partial, latest fully successful run unchanged. Historical attempt-only gaps remain. 

- 2026-10-09 07:59:37 invocation: 075906-attempt.md and terminal 075937-final-retry.md persisted. Scheduled shard 3, recovered oldest stale shard 0; urgent + 15 unique projects, 2 unverified candidates (Concrete Additional USDC and Cambria RSGP extension), 0 ACTION, 0 identity failures, 2 first-party source gaps. Gmail not attempted, user silent. Primary final blocked by safety checks, fallback terminal persisted; partial. Latest fully successful run unchanged. Shard 0 latest partial coverage 2026-10-09 07:59:37. No task or schedule changes.

- 2026-10-09T12:48:36+07:00 invocation: attempt 124733-attempt.md and terminal 124733-final.md persisted. Scheduled Shard 0, executed stale Shard 3; 13 unique projects checked, 3 candidates, 0 Tier A/B ACTION, 2 official current-state gaps (Concrete Additional USDC and Cambria RSGP opt-in). No Gmail or user notification. Partial. Latest fully successful run remains 2026-10-08 05:47:29. Historical attempt-only gaps remain; no new task/scope/schedule changes.

- 2026-10-09 14:52 Asia/Bangkok: 145147-attempt.md and terminal 145147-final-retry.md persisted (commit f6e47bd549637dc88ab7122d625ed24725c9d615). Scheduled/executed Shard 2; urgent plus 14 unique projects checked, 2 unverified candidates (Concrete Additional USDC allocation, Cambria RSGP opt-in extension), 0 Tier A/B ACTION, 2 source gaps. Primary final write blocked by safety checks, fallback terminal persisted. Gmail not attempted, user silent. Partial; last full success unchanged at 2026-10-08 05:47:29. No task/scope/schedule changes.
