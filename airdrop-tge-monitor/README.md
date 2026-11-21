# Airdrop / TGE Monitor

监控仍在活跃名单中、可能影响用户实际权益的空投、TGE、Claim、KYC、投资分配与退款事项。已领/无资格/用户明确删除的历史项目只留审计，不做周期性扫描。

## 当前执行模式

为保证运行成功率，采用：

```text
每小时动态 urgent（允许 0 项） + 一个 active registry shard
4 小时轮到全部 28 个剩余活跃项目/投资权益，若原始数据不可读则仍须标 PARTIAL
```

详细项目表：`REGISTRY.md`；2026-11-21 已取消全部五个固定 Urgent，剔除已结束的 StandX、Cambria 及用户明确排除的 Neutrl 等项目。Echo/01 的 $1,000 是独立投资权益，用户没有 01/N1 积分。
执行规范：`MONITOR_SPEC.md`
运行状态：`state/current.md`

不再要求每小时逐个穷尽整个白名单，因为历史运行已证明会造成大量 partial / missing audit。

## 通知

默认静默。

只有新的、一手官方证据确认、需要用户现在或在明确期限前行动的事件才通知。

通知必须满足：
- canonical identity；
- two-anchor；
- 无 unresolved same-name / ticker / chain / domain conflict；
- QA 通过。

Space (@intodotspace) 与 Spacecoin (@spacecoin) 永久视为不同项目。

## GitHub

- `runs/`：每小时 audit
- `reports/events/`：正式提醒事件
- `reports/daily/`：前一自然日运行汇总
- `incidents/`：历史事故和回归规则

Grass 与 Backpack 明确排除。
