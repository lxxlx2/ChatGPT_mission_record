# Crypto Daily Automatic Runtime

Updated: 2026-09-26 21:05 Asia/Bangkok
Timezone: Asia/Bangkok
Mode: FACTUAL_NEWS_COLLECTOR

Authority for the existing hourly Crypto Daily task.

## Audit

The only mandatory persistence artifact is:
`crypto-daily/runs/YYYY-MM-DD/HHMMSS-final.md`.

Do not require or attempt a start file in the automatic path. Older start files remain valid historical artifacts.

The final audit must include run time, automation id, lane status, research path, source/tool warnings and final run status.

## Ordinary hour
1. core BTC/ETH/SOL + liquid-outlier + major security/exchange/protocol factual scan;
2. one Bangkok-hour rotating shard;
3. write at most 8 material candidates to research;
4. create final audit.

Use supported per-symbol market calls when a multi-symbol endpoint rejects the request. Do not repeat a known-invalid request shape.

## 09:00 / 10:00 / 11:00
09:00 delivery first. 10:00 and 11:00 recovery first.
Read REPORT_SPEC.md and DELIVERY_RUNBOOK.md only in these windows.
Deduplicate before Gmail.

## Status classification
- no material update = healthy;
- an initial request/write error that is fully recovered with equivalent coverage becomes recovered_warning;
- recovered_warning does not downgrade a complete run;
- partial_success / partial_failure only when a real data, persistence or delivery gap remains;
- temporary failures never disable or pause the task;
- no Chinese-language websites as evidence.


## Final persistence fallback

The ordinary-hour research file is durable evidence that collection occurred, but the run still attempts a final audit.

After research is written:
1. try `runs/YYYY-MM-DD/HHMMSS-final.md`;
2. if create fails, fetch that exact path;
3. if the path exists, update it using the fresh SHA;
4. if it does not exist or update is blocked, create one compact retry file:
   `HHMMSS-final-retry.md`.

Do not perform optional work after research write and before final persistence.

A successful research write plus successful final/final-retry = success.
If research exists but both final writes fail, the next run records the previous cycle as `audit_gap_recovered` and continues.


## Notification behavior

Read `docs/MONITORING/NOTIFICATION_POLICY.md` only when deciding whether a user/email notification is required.

Ordinary hourly collection is internal:
- persist research;
- persist final audit;
- return an empty user-visible response.

Do not notify merely because Bitget, ZEC, SOL relative strength, or another already-known item remains material.

A new monitor-health incident is different: send one deduplicated Gmail + ChatGPT alert according to the notification policy.

09:00 formal daily delivery remains governed by REPORT_SPEC / DELIVERY_RUNBOOK.
