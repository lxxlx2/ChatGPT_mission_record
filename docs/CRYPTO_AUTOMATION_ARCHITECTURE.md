# Crypto Automation Architecture

Updated: 2026-09-26 12:05 Asia/Bangkok
Timezone: Asia/Bangkok

The system deliberately uses the existing automations only. Repair and QA must not create additional monitors unless the user explicitly asks.

## Schedule

- :00 Crypto 每日情报
- :14 全项目空投与TGE监控
- :29 $300 Crypto盈利监控
- 19:29 the same $300 Mission run also produces the monster daily summary

The legacy separate monster task stays disabled.

## Reliability principle

Each run starts with a durable skeleton audit before expensive work.

A scheduler timestamp alone is not success.

A run should finish as success, partial_success, partial_failure or failed. It should never intentionally remain in_progress.

Temporary tool/source/GitHub/Gmail problems must not automatically pause or disable an existing automation.

## Crypto Daily

One existing hourly automation.

Ordinary hours:
- core market/security scan every hour;
- one rotating discovery shard;
- compact research;
- finalized audit;
- no Gmail.

09:00:
- delivery first;
- use prior 24h stored research plus short fresh verification;
- Gmail first, readback, GitHub archive;
- optional new research only after delivery.

10:00 / 11:00:
- recovery first;
- dedupe Gmail + GitHub;
- repair only the missing side;
- then ordinary collection.

## TGE

Every hour :14:
- skeleton first;
- urgent set;
- one registry shard;
- four-hour full registry coverage;
- checked_no_update is healthy;
- only real access/tool failures count as source failures;
- ACTION only triggers Gmail + ChatGPT.

## $300 Mission

Every hour :29.

Phase A, always first:
- live wallet/gas;
- PONS;
- XRP/Variational;
- ETH;
- BTC regime;
- JUMP/deadline;
- active-position security.

Phase B:
- read at most two recent Crypto Daily research files;
- one bulk derivatives universe screen;
- deep-check only shortlisted monster candidates;
- deep launch/NFT/FOMO verification only for actual candidates or stale-upstream fallback.

Phase C:
- UNICRED / Credits and slower data every 3h or when material.

This preserves the monitoring scope while avoiding duplicate full-web crawls in both Crypto Daily and Mission.

## Repository authority

`crypto-daily/`
- COLLECTOR_SPEC.md: hourly research runtime
- REPORT_SPEC.md: formal daily content
- DELIVERY_RUNBOOK.md: delivery/recovery
- research/: rolling inputs
- reports/daily/: official report
- runs/: immutable audits

`crypto-300-profit-mission/`
- MISSION_SPEC.md: compact global policy
- RUNBOOK.md: execution contract
- portfolio/current.md: live capital state
- performance/current.md: PnL accounting
- state/latest.md: current Mission state
- health/current.md: scheduler health
- positions/: per-position rules
- watchlists/: model-specific rules
- runs/: immutable audits

`airdrop-tge-monitor/`
- REGISTRY.md
- MONITOR_SPEC.md
- state/current.md
- reports/
- runs/

## Data truth

Fresh wallet/RPC reads outrank old snapshots.

Private venue state remains USER_CONFIRMED until directly connected or refreshed by the user.

Unknown tokens are excluded from NAV until identified.

No successful alert/report may be claimed without the required Gmail/GitHub readback specified by its runbook.
