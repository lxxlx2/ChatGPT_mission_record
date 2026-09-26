# Crypto Automation Architecture

Updated: 2026-09-26
Timezone: Asia/Bangkok

## 目标

解决此前三个共同问题：

1. 单轮任务负载过大，搜索完成后在 GitHub 写入或发布阶段失败。
2. 09:00 发布失败后缺少自动恢复。
3. scheduler 有触发记录，但缺少 GitHub heartbeat，无法确认功能真的执行。

本次修复遵循一个额外约束：**不新增监控任务，沿用已有 Crypto 自动化。**

## Layer A: Crypto 每日情报

同一个现有 automation 每小时 :00 运行，通过当前小时切换模式。

### 普通小时
- 快速市场与事件扫描；
- 最多保留 8 个 material candidates；
- 只写简短、转述后的 research；
- 写 run audit；
- 不发 Gmail。

### 09:00
- 先完成必要的最新采集；
- 检查当天 Gmail Sent 与 GitHub official report；
- 缺失时按 REPORT_SPEC 生成唯一 13 章日报；
- Gmail first；
- GitHub archive second；
- Gmail 成功而 GitHub 失败时记 partial_success。

### 10:00 / 11:00
同一个任务做 missing-delivery recovery：
- 两边都完整：只按普通小时执行；
- Gmail 有、GitHub 缺：只补 GitHub；
- GitHub 有、Gmail 缺：QA 后补 Gmail；
- 两边都缺：重试当日日报。

因此不需要额外的“Crypto 日报发布”scheduler。

## Layer B: Specialist monitors

### TGE
每小时 :14。

每轮：
- 所有 urgent 项目；
- REGISTRY 的一个 shard；
- 4 小时覆盖全 registry；
- 正式 trigger 才通知；
- 第一次跨过 00:00 的 run 生成上一日 summary。

### Mission
每小时 :29。

职责：
- 真实仓位、资金、gas；
- ETH / XRP / PONS / JUMP；
- launch / NFT；
- 妖币 squeeze V2.1；
- opportunity ACTION/WATCH；
- 风险和安全事件。

妖币 V2.1 已并入 Mission，独立妖币任务保持关闭。

## GitHub 目录职责

```text
crypto-daily/
  REPORT_SPEC.md            正式日报内容规范
  COLLECTOR_SPEC.md         普通小时采集规范
  DELIVERY_RUNBOOK.md       09:00/10:00/11:00 同任务发布/恢复规则
  research/YYYY-MM-DD/      小时素材
  reports/daily/            正式日报
  runs/YYYY-MM-DD/          每轮 audit

crypto-300-profit-mission/
  MISSION_SPEC.md           策略与资金权威
  RUNBOOK.md                每小时执行合同
  state/latest.md           最新状态
  health/current.md         scheduler / lane 健康
  positions/                活动仓位
  watchlists/               监控模型
  runs/                     不可变 run audit

airdrop-tge-monitor/
  REGISTRY.md               canonical 白名单与 shard
  MONITOR_SPEC.md           执行规则
  state/current.md          shard/urgent 状态
  reports/events/           正式触发事件
  reports/daily/            每日汇总
  runs/                     每小时 audit
```

## 失败降级标准

### GitHub research write 被 safety check 拦截
先把 research 压缩为：
- topic；
- 1-3 句 paraphrase；
- source domains / source names；
- market numbers；
- confidence；
- no raw exploit steps；
- no large copied text。

再次写入。仍失败时：
- run audit 记录 `research_write_failed:true`；
- 当前轮其它部分继续；
- 下一轮不得假称上一轮 research 已成功。

### 外部数据源失败
- 单一 source 失败：继续其它来源。
- mandatory source 全部失败：该 lane partial_failure。
- 其它 lane 继续。
- 同一 mandatory lane 连续两轮失败：由对应监控触发 health alert。

### Gmail 失败
- Crypto 正式日报：10:00/11:00 同一个任务继续恢复。
- Mission/TGE action alert：ChatGPT 通知仍需产生，GitHub 记录 Gmail error。

## 成功判定

scheduler 触发本身不等于 success。

只有对应 run audit 已写入，且本轮必须 lane 有可审计状态，才算真实运行。
