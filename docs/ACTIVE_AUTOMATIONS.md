# Active Crypto Automations

Updated: 2026-09-26
Timezone: Asia/Bangkok

This document lists actual current automation state, not historical designs.

## Active

### Crypto 每日情报
- automation_id: `6a8600b9d12481919bc43ebc800c9916`
- schedule: hourly at :00
- ordinary hours: factual rolling research
- 09:00: formal Crypto Daily delivery
- 10:00 / 11:00: delivery recovery if needed
- runtime: `crypto-daily/AUTOMATION_RUNTIME.md`

### 全项目空投与TGE监控
- automation_id: `6a85fff710e0819190ffcf8c1145a170`
- schedule: hourly at :14
- purpose: urgent set + one registry shard
- runtime: `airdrop-tge-monitor/AUTOMATION_RUNTIME.md`

### $300 Crypto资产状态监控
- automation_id: `6ab46906a0cc8191880f1922dbef954a`
- schedule: hourly at :29
- purpose: factual wallet/position/threshold/opportunity-state telemetry
- Monster V2.1 remains embedded
- 19:29 same task performs Monster factual daily summary
- runtime: `crypto-300-profit-mission/AUTOMATION_RUNTIME.md`

## Disabled / superseded

- `Crypto 09:00 日报发布`: disabled; publication/recovery is handled by the active Crypto 每日情报 task.
- `妖币每日汇总`: disabled; Monster is merged into $300 Mission.
- `ETH期权到期交易检查`: completed/disabled.
- `Crypto 日报滚动素材池`: disabled; replaced by Crypto 每日情报.
- `历史报告回填修复`: disabled one-off.

## Health proof

A scheduler trigger alone is insufficient.

Current expected automatic audit pattern:
- `HHMMSS-start.md`
- `HHMMSS-final.md`

A run can still be valid if a start-marker write is blocked but the factual lanes complete and a final audit is durably written with the warning recorded.

No repository cleanup may create a replacement automation merely to solve naming or organization issues.
