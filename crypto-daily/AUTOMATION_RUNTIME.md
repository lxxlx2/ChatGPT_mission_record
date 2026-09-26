# Crypto Daily Automatic Runtime

Updated: 2026-09-26 15:10 Asia/Bangkok
Timezone: Asia/Bangkok
Mode: FACTUAL_NEWS_COLLECTOR

This is the authority for the existing hourly Crypto Daily scheduler.

## Durable audit model

Do not update the start marker.

At run start create:
`crypto-daily/runs/YYYY-MM-DD/HHMMSS-start.md`

Fields:
- run_time
- automation_id
- mode: FACTUAL_NEWS_COLLECTOR
- run_status: started

At the end create a new file:
`crypto-daily/runs/YYYY-MM-DD/HHMMSS-final.md`

Fields:
- run_time
- automation_id
- run_status: success | partial_success | partial_failure | failed
- research_path
- core_scan
- discovery_shard
- source_failures
- tool_errors
- delivery_status when relevant

A run is complete only when the final file exists. This append-only pattern avoids SHA/update conflicts.

## Ordinary hours

1. Create start marker.
2. Core factual scan: BTC/ETH/SOL, liquid outliers, major security/exchange/protocol headlines.
3. Run one rotating discovery shard by Bangkok hour % 3:
   - 0: English X + Reddit + NFT/digital-art
   - 1: TGE/ICO/ecosystem/RWA/stablecoin/AI-Crypto/DePIN/prediction markets
   - 2: flows/derivatives/cross-chain/macro/security depth
4. Save at most 8 material candidates to:
   `crypto-daily/research/YYYY-MM-DD/HHMMSS.md`
5. Create final audit.

Healthy no-news states are `checked_no_update`, not failures.

## 09:00

Delivery first.

After start marker:
1. check Gmail Sent and today's official GitHub report;
2. if missing, read prior 24h research and only a small fresh verification set;
3. read `REPORT_SPEC.md` and `DELIVERY_RUNBOOK.md`;
4. generate/QA/send Gmail first;
5. read back Gmail;
6. archive/read back GitHub;
7. optional hourly research only after delivery;
8. create final audit.

## 10:00 / 11:00

Recovery first:
- repair only the missing Gmail/GitHub side;
- never duplicate an already sent official Gmail;
- after recovery, do ordinary hourly collection if time permits;
- create final audit.

## Failure rules

- one source failure does not abort the run;
- research write failure gets one compact retry;
- if research still fails, create final audit as partial_failure;
- temporary failure never disables or pauses the task;
- Chinese-language websites are not evidence sources.
