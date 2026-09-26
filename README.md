# ChatGPT Mission Record

本仓库是长期自动化任务的可审计状态仓库。原则：沿用现有自动化，配置、运行记录、通知与正式报告分离。除非用户明确要求，不因为修复、QA 或拆流程额外创建监控任务。

## 当前目录

| 目录 | 用途 | 运行形态 |
| --- | --- | --- |
| `crypto-daily/` | Crypto 小时素材 + 09:00 正式日报 | 同一个现有任务 |
| `crypto-300-profit-mission/` | 实盘/机会 Mission，含 ETH、XRP、PONS、JUMP、NFT、Monster V2.1 等 | 每小时决策层 |
| `airdrop-tge-monitor/` | 空投、TGE、Claim、KYC、allocation 等 | 每小时 urgent + shard |
| `us-stock-daily/` | 美股晨报 | 独立对话维护 |
| `eth-trading-monitor/` | 旧 ETH 专项历史记录 | 已并入 Crypto Mission |
| `x-revenue/` | X 内容候选与人工审批 | 独立流程 |
| `audits/` | 跨任务审计 | 按需 |
| `docs/` | 架构与运维说明 | 文档 |

## Crypto 时间轴

Asia/Bangkok：

- 每小时 `:00`：`Crypto 每日情报`
  - 核心市场/安全扫描每小时执行
  - 发现类内容采用 3 小时 rotating shard，保证连续成功 3 轮覆盖全部 discovery 类别
  - 09:00 同一任务优先交付正式日报
  - 10:00 / 11:00 同一任务优先修复缺报
- 每小时 `:14`：`全项目空投与TGE监控`
  - urgent set + 一个 registry shard
  - 4 小时覆盖完整 registry
- 每小时 `:29`：`$300 Crypto盈利监控`
  - Phase A 先检查真实资金与活动仓位风险
  - Phase B 用 Crypto Daily 最新研究 + bulk market screening 做机会发现
  - Phase C 每 3 小时检查慢速仓位
- 每天 `19:29`：仍由同一个 $300 Mission 输出 Monster V2.1 日汇总

详细设计：`docs/CRYPTO_AUTOMATION_ARCHITECTURE.md`

## 运行可靠性

每次自动化第一项持久化动作必须先创建：

```text
<task>/runs/YYYY-MM-DD/HHMMSS.md
run_status: in_progress
```

结束时必须 finalize 为：
- success
- partial_success
- partial_failure
- failed

不得故意留下 `in_progress`。

scheduler UI 的 last_run_time 只说明触发过，不能证明功能成功。没有 finalized GitHub audit 的触发视为 missing_audit。

单一来源、GitHub、Gmail 或某一个 lane 失败时，能继续的部分必须继续；临时故障不得自动 disable/pause 现有任务。

## 通知

- NO_ACTION、重复信号、低质量候选静默
- Mission 的 ACTION / changed WATCH 按 Mission spec 发 Gmail + ChatGPT
- TGE 只在官方证据确认且需要用户行动时通知
- Crypto 普通小时不发 Gmail
- Crypto 正式日报先 Gmail，后 GitHub；Gmail 已成功时禁止因 GitHub 后续失败重复发送

## 数据真实性

- 禁止使用中文网站作为 Crypto / TGE / Mission 的确认来源
- 官方、一手链上、交易所原始数据优先
- 钱包实时值优先于历史快照
- 私有交易场所未连接时只能保留 USER_CONFIRMED + 时间戳
- 未识别资产不计入 NAV
