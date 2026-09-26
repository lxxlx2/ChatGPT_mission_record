# Crypto Monitoring Tasks

Updated: 2026-09-26

This page is the human-readable index for the three active Crypto monitoring systems.

## Crypto Daily

Task: `Crypto 每日情报`

Schedule:
- hourly at :00 Asia/Bangkok;
- 09:00 formal daily delivery is handled by the same task;
- 10:00 / 11:00 are recovery windows when needed.

Operational root:
- `crypto-daily/`

Runtime authority:
- `crypto-daily/AUTOMATION_RUNTIME.md`

Primary outputs:
- `crypto-daily/research/`
- `crypto-daily/reports/`
- `crypto-daily/runs/`

## Airdrop / TGE

Task: `全项目空投与TGE监控`

Schedule:
- hourly at :14 Asia/Bangkok.

Operational root:
- `airdrop-tge-monitor/`

Runtime authority:
- `airdrop-tge-monitor/AUTOMATION_RUNTIME.md`

Primary outputs:
- urgent + registry shard checks;
- event reports only when action is verified;
- `airdrop-tge-monitor/runs/` append-only audit.

## $300 Crypto Mission

Task: `$300 Crypto资产状态监控`

Schedule:
- hourly at :29 Asia/Bangkok;
- 19:29 same task also produces the Monster factual daily summary.

Operational root:
- `crypto-300-profit-mission/`

Runtime authority:
- `crypto-300-profit-mission/AUTOMATION_RUNTIME.md`

Primary current-state files:
- `portfolio/current.md`
- `performance/current.md`
- `state/latest.md`
- `health/current.md`
- `positions/`
- `watchlists/`
- `runs/`

## Reliability rule

A scheduler timestamp alone is not success.

Current audit convention:
- mandatory: `HHMMSS-final.md`
- historical/best-effort: `HHMMSS-start.md`

The automatic path no longer requires a start marker because that write was an unnecessary failure point.

A successful final audit is the canonical proof that the run completed.

No repository cleanup may silently move these authority/runtime paths.


## Notification policy

Canonical notification/silence rules:
- `docs/MONITORING/NOTIFICATION_POLICY.md`

Healthy hourly runs are silent. Actual monitor-health incidents use deduplicated Gmail + ChatGPT alerts.
