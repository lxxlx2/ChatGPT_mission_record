# Airdrop / TGE Monitor

监控已有用户参与项目的真实进度与兑现机会，包含 Crypto TGE / Claim / 上币、股权 IPO / 上市 / 并购退出、重大影响投资价值的融资、份额交付、证券票据结算、退款、解锁和必须操作的截止日期。名称沿用 TGE 监控，28 个既有项目仍按原分片扫描，不因资产非加密代币就排除。已领/无资格或用户明确关闭的历史项目留审计，不做周期性扫描。

## 当前执行模式

为保证运行成功率，采用：

```text
每小时动态 urgent（允许 0 项） + 一个 active registry shard
4 小时轮到全部 28 个原有活跃项目/投资权益，核实官方里程碑与最近一次已证实状态的差异；原始证据不可读仍须标 PARTIAL
```

详细项目表：`REGISTRY.md`。固定 Urgent 0；Galxe 用户已发现并尝试领取，历史补发已完成，停止特殊动态监控；只追踪 28 个既有项目实际 TGE/IPO/资金兑现进展。Echo 是参与平台，01/N1 是发行方项目身份，用户有 $1,000 原 01 投资且无 01/N1 积分。
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
