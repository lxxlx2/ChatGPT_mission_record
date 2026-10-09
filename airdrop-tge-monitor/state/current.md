# Airdrop / TGE Monitor State
Updated: 2026-10-09 19:53:50 Asia/Bangkok (latest terminal partial)
Timezone: Asia/Bangkok

- architecture: urgent_plus_4_shards_with_stale_recovery
- expected_schedule: hourly at minute 50
- latest_actual_scheduler_run: 2026-10-09 19:53:50 Asia/Bangkok
- latest_actual_run_status: partial
- latest_authoritative_success: 2026-10-08 05:47:29 Asia/Bangkok
- latest_run_path: airdrop-tge-monitor/runs/2026-10-09/195225-final.md
- latest_scheduled_shard: 3
- latest_executed_shard: 3
- latest_stale_shard_recovery: true
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

## Pending and health
- Cambria: current official whitelist/mint content exists but no independently verified NEW user-specific opt-in eligibility, deadline extension or unfinished individual right. Previously delivered RSGP opt-in is not repeated. 2026-10-09 18:49 status UNVERIFIED_CANDIDATE/NO_ACTION.
- Concrete Additional USDC allocation: UNVERIFIED_PENDING. Canonical foundation page inaccessible; Tier A/B eligibility/action delta not established. Existing CT claim-open already delivered.
- Identity: Space @intodotspace distinct from Spacecoin @spacecoin. No ambiguous account treated as user-rights evidence.
- Latest terminal audit: 2026-10-09 18:49:28, runs/2026-10-09/184928-final.md. Run partial: 15 unique projects, 2 candidates, 0 ACTION, 0 identity failures, 2 source failures; final persisted but attempt write blocked by tool safety checks.
- Last fully successful monitoring run remains 2026-10-08 05:47:29. Recent finals are partial; do not claim fully healthy. Continue existing :50 schedule and stale-shard recovery.
- No new verified event meets first-party/current/unresolved-rights ACTION_GATE. No Gmail sent or needed from last partial.
- Historical attempt-only and source gaps remain audit issues; see immutable run artifacts.
- No task, scope, title, or schedule changes.

- 2026-10-09 19:53:50 Asia/Bangkok: terminal 195225-final.md persisted; scheduled/executed stale Shard 3, urgent plus 13 unique projects, 2 unverified candidates (Concrete Additional USDC allocation and Cambria Genesis whitelist), 0 ACTION, 2 source gaps, no Gmail/ChatGPT. Attempt write blocked by safety checks; final is authoritative. Last fully successful run remains 2026-10-08 05:47:29. No task/scope/schedule changes.
