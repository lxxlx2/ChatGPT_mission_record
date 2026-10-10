# Airdrop / TGE Monitor State
Updated: 2026-10-10 15:52:38 Asia/Bangkok
Timezone: Asia/Bangkok
- expected_schedule: hourly :50 (unchanged)
- latest_actual_scheduler_run: 2026-10-10 15:51:53 Asia/Bangkok
- latest_actual_run_status: partial
- latest_authoritative_success: 2026-10-10 07:52:16 Asia/Bangkok
- latest_run_path: airdrop-tge-monitor/runs/2026-10-10/155238-final-retry.md
- latest_attempt_path: airdrop-tge-monitor/runs/2026-10-10/155153-attempt.md
- latest_scheduled_shard: 3
- latest_executed_shard: 3
- latest_candidate_count: 3
- latest_triggered_events: 0
- latest_identity_failures: 0
- latest_source_failures: 1
- latest_notification_decision: NO_ACTION
- latest_notification_status: silent

## Durable known-events
See state/known-events.md: already delivered CT/HEEBOO/MetaMask/Cambria original actions are deduped; UNICRED completed; humans& closed and refunded; Abstract user-suppressed; independent Loopscale TGE retired.

## Pending and health
- Concrete additional allocation: UNVERIFIED_CANDIDATE, first-party Foundation portal inaccessible; no verified open/user entitlement delta. No resend.
- Cambria opt-in extension: expired or not currently verified; unchanged original reminder already delivered. No resend.
- MEXC CT promotion: not evidence of new user entitlement; out of mapped rights scope. No ACTION.
- Forecast whitelist, Neutrl redemption identity conflict and other prior unverified candidates remain unresolved, not eligible for notification until Tier A/B and current user-rights gates pass.
- 2026-10-10 14:45:44 run only produced `144544-attempt.md`, no final/final-retry observed: RUN_INTEGRITY_GAP. Do not invent backdated completion.
- 2026-10-10 15:52:38 bounded existing run has durable `155238-final-retry.md`; one first-party source gap; 0 confirmed ACTION, no Gmail. Primary final write blocked; fallback succeeded.
- Overall health: DEGRADED_PARTIAL. The earlier 07:52 authoritative full success is still last fully successful run, not replaced by partial.
- Existing hourly :50 task, title, scope and recipient unchanged; no new monitor or daily TGE email created.
