# Current TGE monitor state

## Active configuration (newest scope authority, corrected 2026-11-21)

- fixed_urgent: **NONE**; old Concrete/MetaMask/Claynosaurz/HEEBOO/Space fixed set retired by user
- dynamic_urgent: **derived at run time; may be zero**; closed/ineligible entries excluded
- active_shard_counts: **0=8; 1=6; 2=7; 3=7; total=28** (Neutrl user-excluded)
- active_echo_01_investment: **USD 1,000 user-confirmed; refund/distribution outcome UNKNOWN**, existing Shard 2
- user_01_points: **0**; user_N1_points: **0**; no points/TGE scanning
- user_suppressed_closed_rights: **Concrete, MetaMask, Claynosaurz/Clay Shares, HEEBOO, Space, StandX, Cambria, Neutrl**; retain historical audit only
- original schedule: hourly HH:00 Asia/Bangkok, hour % 4 one shard, unchanged
- neutrl: **USER_DECISION_NO_TGE / PROJECT_COLLAPSED / TGE_CLOSED / PERMANENTLY_EXCLUDED_FROM_TGE_WATCH** (original user analysis dates back to Aug 2026); official incident reserves impaired, operations paused, partial-value redemption. No inference of full investor repayment or an official token-cancellation announcement.
- runtime_reminder: the older last_run metrics below correspond to **before this config correction** and MUST NOT be used as current shard/urgent denominator or counted as a post-fix PASS
- verification_status: **CONFIG_UPDATED_NOT_YET_RUNTIME_VALIDATED**, do not report full recovery until a new authoritative run final with original source receipts actually passes

## Last historical execution record before scope correction
- last_run: 2026-11-21T11:00:18+07:00
- schedule: Asia/Bangkok HH:00 hourly (unchanged)
- latest_final: airdrop-tge-monitor/runs/2026-11-21/110018-final.md
- run_status: PARTIAL_ONLY
- scheduled_shard: 3
- executed_shard: 3
- candidate_count: 0 new qualifying ACTION
- action_gate_pass: 0
- triggered_events: 0
- gmail_sent: false
- app_notification: false
- code_gate: CODE_NOT_EXECUTED
- source_attempted_slots: urgent 5/5; shard3 9/9 (bounded discovery; original rights incomplete)
- event_bound_new_rights_verified: 0/14
- current_rights_complete: 0/14
- source_failures: 14/14 slots not fully verified; see 110018-final.md
- identity_failures: 0 proven
- browser_session: BROWSER_SESSION_UNAVAILABLE
- last_verified_complete_at: 2026-10-10T07:52:16+07:00 (unchanged)

## Last meaningful attempts
- shard0: 2026-11-21 08:00:04 Asia/Bangkok (PARTIAL_ONLY)
- shard1: 2026-11-21 09:04:08 Asia/Bangkok (PARTIAL_ONLY)
- shard2: 2026-11-21 10:03:12 Asia/Bangkok (PARTIAL_ONLY)
- shard3: 2026-11-21 11:00:18 Asia/Bangkok (PARTIAL_ONLY)

## Remaining unresolved within active scope (historical run notes)
- Echo USD 1,000 original 01 investment: settlement/refund/distribution UNKNOWN; no 01/N1 points
- SurfBoard Nov13 expired absent verified extension
- Crusoe mapped investor rights unverified
- Galxe Nov9 sunset + Dec5/Dec15 campaign deadlines already emailed; separate G/Smart Balance/staking asset recovery process NOT YET ANNOUNCED in Nov9 issuer Help Center; claim-center authenticated eligibility SOURCE_GAP
- Exclusions: Forecast, Abstract, Grass, Backpack, Loopscale, humans&, UNICRED; plus Concrete, MetaMask, Claynosaurz, HEEBOO, Space, StandX, Cambria, Neutrl USER_SUPPRESSED
- Space/Spacecoin and Theo/Autheo collision guard
