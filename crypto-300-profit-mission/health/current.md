# Crypto Mission Monitor Health

Updated: 2026-09-26
Timezone: Asia/Bangkok

## Configuration
- main_automation_id: 6ab46906a0cc8191880f1922dbef954a
- expected_schedule: hourly at minute 29
- architecture: RUNBOOK + MISSION_SPEC
- monster_lane_merged_into_main: true
- separate_monster_daily_automation_enabled: false
- eth_lane_merged_into_main: true
- BSC_cluster_lane: excluded

## Notification contract
- ACTION: Gmail + ChatGPT
- WATCH: Gmail + ChatGPT
- unchanged WATCH: silent
- NO_ACTION: silent
- monitor health failure: Gmail + ChatGPT
- 19:29 monster summary: user-visible daily summary

## Runtime health
- last_scheduler_trigger_seen_before_repair: 2026-09-26T07:12:06+07:00
- last_verified_automatic_run_audit: none_after_repair
- last_manual_integration_qa: 2026-09-26T07:59:00+07:00
- current_status: awaiting_first_post_repair_scheduler_validation
- github_write_path_test: passed manually
- gmail_delivery_path_test: passed manually
- note: prior health file incorrectly said WATCH was ChatGPT-only; corrected here.

## Mandatory lanes
- wallet/gas
- PONS
- XRP/Variational
- ETH conditional
- BTC regime
- JUMP
- launch/NFT radar
- active-position security
- monster squeeze V2.1
- Robinhood/FOMO execution-flow

## Success definition
A scheduler run is successful only after:
1. a run audit exists;
2. every mandatory lane is checked or explicitly failed;
3. state/latest.md is updated;
4. health/current.md is updated;
5. the run audit is finalized.

Scheduler metadata alone is not proof of success.
