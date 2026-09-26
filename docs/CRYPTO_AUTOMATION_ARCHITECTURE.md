# Crypto Automation Architecture

Updated: 2026-09-26
Timezone: Asia/Bangkok

## 目标

解决此前三个共同问题：

1. 单轮任务负载过大，搜索完成后在 GitHub 写入或发布阶段失败。
2. 正式日报与小时研究耦合，09:00 任一步骤失败会导致整天漏报。
3. scheduler 有触发记录，但缺少 GitHub heartbeat，无法确认功能真的执行。

## 三层架构

### Layer A: Collection

任务：Crypto 每小时情报采集。

时间：每小时 :00。

职责仅包括：
- 快速市场与事件扫描；
- 最多保留 8 个 material candidates；
- 只写简短、脱敏、转述后的 research；
- 写 run audit；
- 不发 Gmail，不承担正式日报。

禁止在本层：
- 生成 13 章日报；
- 做大量历史回填；
- 保存长篇网页原文、长 URL dump、攻击利用步骤；
- 因单一来源失败停止整轮。

### Layer B: Specialist monitors

#### TGE
每小时 :14。

每轮：
- 所有 urgent 项目；
- REGISTRY 的一个 shard；
- 4 小时覆盖全 registry；
- 正式 trigger 才通知；
- 第一次跨过 00:00 的 run 生成上一日 summary。

#### Mission
每小时 :29。

职责：
- 真实仓位、资金、gas；
- ETH / XRP / PONS / JUMP；
- launch / NFT；
- 妖币 squeeze V2.1；
- opportunity ACTION/WATCH；
- 风险和安全事件。

Mission 是“决策层”，不重复做 Crypto Daily 的全网长篇研究。

### Layer C: Formal delivery

任务：Crypto 09:00 日报发布。

运行：09:10 / 10:10 / 11:10。

行为：
1. 先检查当天 official report 与 Gmail Sent。
2. 已送达则静默退出。
3. 未送达则读过去 24h research，补一次 fresh verification。
4. 生成最终 13 章正文。
5. QA。
6. Gmail first。
7. GitHub archive second。
8. Gmail 成功、GitHub 失败时标记 partial_success，后续重试只补 GitHub，不重复邮件。

## GitHub 目录职责

```text
crypto-daily/
  REPORT_SPEC.md            正式日报内容规范
  COLLECTOR_SPEC.md         小时采集规范
  DELIVERY_RUNBOOK.md       09:10/10:10/11:10 发布与恢复
  research/YYYY-MM-DD/      小时素材
  reports/daily/            正式日报
  runs/YYYY-MM-DD/          每次采集/发布 audit

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
  state/current.md          shard/urgent/delivery 状态
  reports/events/           正式触发事件
  reports/daily/            每日汇总
  runs/                     每小时 audit
```

## 失败降级标准

### GitHub research write 被 safety check 拦截

先把 research 内容压缩为：
- topic；
- 1-3 句 paraphrase；
- source domains / source names；
- market numbers；
- confidence；
- no raw exploit steps；
- no large copied text。

再次写入。仍失败时：
- run audit 记录 `research_write_failed:true`；
- 继续其它 lane；
- 下一轮不得假称上一轮 research 已成功。

### 外部数据源失败

- 单一 source 失败：继续其它来源。
- mandatory market source 全部失败：该 lane partial_failure。
- 其它 lane 继续。
- 同一 mandatory lane 连续两轮失败：触发 monitor health alert。

### Gmail 失败

- 正式日报：后续恢复轮次继续尝试。
- Mission/TGE action alert：ChatGPT 通知仍需产生，GitHub 记录 Gmail error。

## 成功判定

scheduler 触发本身不等于 success。

只有对应 run audit 已写入，且本轮必须 lane 有可审计状态，才算真实运行。
