# Active Crypto Automations

Updated: 2026-09-26
Timezone: Asia/Bangkok

## Active

### Crypto 每小时情报采集
- Schedule: every hour at :00
- Purpose: lightweight rolling research only
- GitHub: `crypto-daily/research/` + `crypto-daily/runs/`
- Gmail: never

### Crypto 09:00 日报发布
- Schedule: 09:10 / 10:10 / 11:10
- Purpose: formal 13-section report + recovery
- 09:10 primary; later runs dedupe and repair only
- Gmail-first, GitHub-second

### 全项目空投与TGE监控
- Schedule: every hour at :14
- Purpose: urgent set + one registry shard
- Full registry refresh target: <= 4 hours
- Daily summary: first run after 00:00 for previous natural day

### $300 Crypto盈利监控
- Schedule: every hour at :29
- Purpose: capital / position / opportunity decision layer
- Monster squeeze V2.1 is embedded here
- 19:29 run emits the monster daily summary

## Disabled legacy / superseded

- 妖币每日汇总: disabled; merged into $300 Mission.
- ETH期权到期交易检查: completed/disabled; ETH now lives in Mission.
- Crypto 日报滚动素材池: disabled; replaced by Crypto 每小时情报采集.
- 历史报告回填修复: disabled one-off tool.

## Health expectations

A scheduler trigger is not considered healthy unless the expected GitHub audit exists.

- Collector: one run audit per hourly trigger.
- TGE: one run audit per hourly trigger.
- Mission: one finalized run audit + state/health updates per trigger.
- Daily publisher: audit on every actual publish/recovery attempt.

Missing audits are operational failures even if the scheduler UI says the task ran.
