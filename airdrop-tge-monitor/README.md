# Airdrop / TGE Monitor

监控空投、TGE、Claim、KYC、allocation、investor distribution、Clay Shares 等需要用户动作的权益事件。

## 当前执行模式

为保证运行成功率，采用：

```text
每小时 urgent set + 一个 registry shard
4 小时完整覆盖全白名单
```

详细项目表：`REGISTRY.md`
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
