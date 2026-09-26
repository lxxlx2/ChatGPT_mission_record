# ChatGPT Mission Record

本仓库是长期自动化任务的可审计状态仓库。核心原则是：**沿用现有自动化，配置、运行记录、通知与正式报告分离；除非用户明确要求，不因为修复流程额外创建新的监控任务。**

## 当前目录

| 目录 | 用途 | 运行形态 |
| --- | --- | --- |
| `crypto-daily/` | Crypto 每小时情报采集 + 09:00 正式日报 | 同一个现有任务按小时切换模式 |
| `crypto-300-profit-mission/` | 实盘/机会 Mission，含 ETH、XRP、PONS、JUMP、NFT、妖币 V2.1 等 | 每小时决策层 |
| `airdrop-tge-monitor/` | 空投、TGE、Claim、KYC、allocation、分发权益监控 | 每小时 urgent + shard |
| `us-stock-daily/` | 美股晨报 | 由独立对话维护 |
| `eth-trading-monitor/` | 旧 ETH 专项历史记录 | 已并入 Crypto Mission |
| `x-revenue/` | X 内容候选与人工审批 | 独立流程 |
| `audits/` | 跨任务审计 | 按需 |
| `docs/` | 跨任务架构与运维说明 | 文档 |

## Crypto 自动化时间轴（Asia/Bangkok）

- 每小时 `:00`：现有 `Crypto 每日情报` 运行。
  - 普通小时：只做滚动素材与 run audit。
  - 09:00：同一任务额外生成并发送正式日报。
  - 10:00 / 11:00：同一任务只在当天正式日报缺失时执行恢复/补发。
- 每小时 `:14`：现有空投/TGE 监控，执行 urgent 项目 + 一个 registry shard，4 小时覆盖完整白名单。
- 每小时 `:29`：现有 $300 Crypto Mission，读取最新情报、仓位、链上状态和妖币 V2.1。
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

单一数据源失败不得让整个任务“消失”。能降级时继续执行，并标记 `partial_success` 或 `partial_failure`。

## 通知原则

- NO_ACTION、重复信号、低质量候选保持静默。
- Mission 的 ACTION / WATCH 按当前 Mission spec 发送。
- TGE 只在官方证据确认且需要用户动作时发送。
- Crypto 普通小时采集不发 Gmail；09:00 正式日报及 10:00/11:00 缺报恢复由同一个 `Crypto 每日情报` 任务完成。
- Gmail 已成功后 GitHub 失败，不重复发邮件，后续运行只补 GitHub。

## 自动化管理原则

- 修复既有监控时优先修改原任务。
- 除非用户明确要求“新增任务/新增监控”，不得因为 QA、恢复、拆流程而创建新的 automation。
- 可通过仓库 Runbook 拆分逻辑，但 scheduler 任务数量保持最小化。

## 数据源原则

- 禁止使用中文网站作为 Crypto / TGE / Mission 的确认来源。
- 官方、一手链上、交易所原始市场数据优先。
- X / Reddit 可以做发现和情绪证据，不能单独替代一手事实。
