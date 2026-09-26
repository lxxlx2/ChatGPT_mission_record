# Crypto Daily Automatic Runtime

Updated: 2026-09-26 16:33 Asia/Bangkok
Timezone: Asia/Bangkok
Mode: FACTUAL_NEWS_COLLECTOR

Authority for the existing hourly Crypto Daily task.

## Audit
Create crypto-daily/runs/YYYY-MM-DD/HHMMSS-start.md first and never update it.
At completion create matching HHMMSS-final.md.
A final audit is proof of completion.

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
