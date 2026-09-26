# ChatGPT Mission Record

本仓库是长期自动化任务的可审计状态仓库。核心原则是：**任务配置、运行记录、通知与正式报告分离**，每条自动化都必须能从 GitHub 看出“应该做什么、实际做了什么、是否成功”。

## 当前目录

| 目录 | 用途 | 运行形态 |
| --- | --- | --- |
| `crypto-daily/` | Crypto 每小时情报采集 + 09:00 正式日报 | 采集与发布拆分 |
| `crypto-300-profit-mission/` | 实盘/机会 Mission，含 ETH、XRP、PONS、JUMP、NFT、妖币 V2.1 等 | 每小时决策层 |
| `airdrop-tge-monitor/` | 空投、TGE、Claim、KYC、allocation、分发权益监控 | 每小时分片 + 每日汇总 |
| `us-stock-daily/` | 美股晨报 | 由独立对话维护 |
| `eth-trading-monitor/` | 旧 ETH 专项历史记录 | 已并入 Crypto Mission |
| `x-revenue/` | X 内容候选与人工审批 | 独立流程 |
| `audits/` | 跨任务审计 | 按需 |
| `docs/` | 跨任务架构与运维说明 | 文档 |

## Crypto 自动化时间轴（Asia/Bangkok）

- 每小时 `:00`：Crypto 小时情报采集，只做滚动素材与 run audit。
- 每小时 `:14`：空投/TGE 增量监控，每轮“紧急项目 + 一个 registry shard”，4 小时覆盖完整白名单。
- 每小时 `:29`：$300 Crypto Mission 决策层，读取最新情报、仓位、链上状态和妖币 V2.1。
- 每天 `09:10`：Crypto 正式日报首次发布尝试。
- 每天 `10:10`、`11:10`：仅在当天正式日报尚未送达时自动恢复/补发。
- 每天 `19:29`：由 $300 Mission 同一轮输出妖币 V2.1 日汇总。
- 每日第一次 00:00 之后的 TGE 轮次：生成前一自然日 TGE daily summary。

详细设计：`docs/CRYPTO_AUTOMATION_ARCHITECTURE.md`。

## 运行记录要求

每次真正触发的自动化必须优先留下最小可审计记录：

```text
<task>/runs/YYYY-MM-DD/HHMMSS.md
```

至少包含：

- run_time / timezone；
- automation_id；
- run_mode；
- run_status；
- 已执行 lane / shard；
- 关键数据源状态；
- 是否触发用户动作；
- Gmail / ChatGPT 通知状态；
- GitHub 写入状态；
- 失败原因。

单一数据源失败不得自动让整个任务消失。能降级时继续执行，并标记 `partial_success` 或 `partial_failure`。

## 通知原则

- NO_ACTION、重复信号、低质量候选保持静默。
- Mission 的 ACTION / WATCH 按当前 Mission spec 发送。
- TGE 只在官方证据确认且需要用户动作时发送。
- Crypto 小时采集从不发 Gmail；正式日报由独立发布任务负责。
- Gmail 发送成功后 GitHub 失败，不撤销已经送达的邮件，下一次恢复轮次补 GitHub。

## 数据源原则

- 禁止使用中文网站作为 Crypto / TGE / Mission 的确认来源。
- 官方、一手链上、交易所原始市场数据优先。
- X / Reddit 可以做发现和情绪证据，不能单独替代一手事实。
