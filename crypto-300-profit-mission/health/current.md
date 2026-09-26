# Crypto Mission Monitor Health

Updated: 2026-09-26 12:05 Asia/Bangkok
Timezone: Asia/Bangkok

## Configuration
- main_automation_id: 6ab46906a0cc8191880f1922dbef954a
- expected_schedule: hourly at minute 29
- timing_mode: exact_schedule
- monster_lane_merged_into_main: true
- separate_monster_daily_automation_enabled: false
- BSC_cluster_lane: excluded

## Notification contract
- ACTION: Gmail + ChatGPT
- changed WATCH: Gmail + ChatGPT
- unchanged WATCH: silent
- NO_ACTION: silent
- monitor health failure: Gmail + ChatGPT
- 19:29 monster summary: user-visible daily summary

## Runtime diagnosis before this repair
- 09:30 automatic run created a skeleton audit but never finalized it.
- later scheduler metadata advanced, while 10:29 and 11:29 produced no durable Mission audit.
- therefore scheduler triggering itself is working, while the prior Mission execution payload was too heavy / insufficiently bounded to reliably reach finalization.
- the abandoned 09:30 skeleton is classified as failed_abandoned_after_skeleton.

## Repair applied
- MISSION_SPEC compacted so the hourly run does not ingest duplicated historical/detail blocks.
- RUNBOOK changed to phased execution:
  - Phase A critical positions first;
  - Phase B upstream-research + bulk-screen discovery;
  - Phase C medium lane only every 3h;
  - bounded candidate deep checks;
  - best-effort finalization even on partial failures.
- closed/historical files are no longer bulk-read every hour.
- Monster V2.1 keeps full-universe screening through bulk data, with detailed calls only for a shortlist.
- launch/NFT/FOMO keep functional coverage via fresh Crypto Daily research plus fallback discovery.
- no new automation was created.

## Current validation status
- GitHub write path: verified.
- Gmail path: verified.
- TGE task: independently producing successful finalized runs.
- Mission automatic post-repair validation: pending next :29 execution.
- until a new finalized automatic Mission audit appears, do not mark Mission scheduler healthy.

## Success definition
A Mission run is healthy only when the same automatic cycle:
1. creates a skeleton;
2. records Phase A lane statuses;
3. records discovery lane statuses;
4. updates state/health;
5. finalizes the same audit.

Scheduler metadata alone is insufficient.
