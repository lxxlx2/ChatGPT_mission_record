# ChatGPT Mission Record

这是长期自动化任务与 Crypto 研究的可审计仓库。

仓库现在明确分成两层：

1. **运行层**：保证现有自动化稳定执行。
2. **研究层**：按内容类型组织，方便人工浏览和后续复用。

完整规则：
- `docs/REPOSITORY_STRUCTURE.md`

## 五类内容导航

| 类别 | 位置 | 用途 |
| --- | --- | --- |
| 监控任务 | `crypto-daily/`, `airdrop-tge-monitor/`, `crypto-300-profit-mission/`, `docs/MONITORING/` | runtime、state、health、alerts、audit |
| 项目分析 / 项目记录 | `research/projects/` | 项目尽调、公售、协议、产品、时间线 |
| 代币 / 二级 / 合约 / 妖币分析 | `research/tokens/` | tokenomics、现货/永续、funding/OI、回购、挤空模型 |
| Meme 分析 | `research/memes/` | Meme 叙事、社区传播、launchpad、筹码和交易研究 |
| NFT 分析 | `research/nfts/` | mint、collection、creator、rarity、二级和出售研究 |

## 三个现有 Crypto 监控

### Crypto 每日情报
- Schedule: 每小时 :00 Asia/Bangkok
- 09:00 同一个任务负责正式日报
- 10:00 / 11:00 同一个任务负责缺报恢复
- Runtime: `crypto-daily/AUTOMATION_RUNTIME.md`

### 全项目空投与TGE监控
- Schedule: 每小时 :14
- Runtime: `airdrop-tge-monitor/AUTOMATION_RUNTIME.md`

### $300 Crypto资产状态监控
- Schedule: 每小时 :29
- 19:29 同一任务包含 Monster factual daily summary
- Runtime: `crypto-300-profit-mission/AUTOMATION_RUNTIME.md`

详细导航：
- `docs/MONITORING/README.md`
- `docs/CRYPTO_AUTOMATION_ARCHITECTURE.md`

## 自动运行 audit

新自动运行采用 append-only：

```text
<task>/runs/YYYY-MM-DD/HHMMSS-start.md
<task>/runs/YYYY-MM-DD/HHMMSS-final.md
```

旧的 `HHMMSS.md` / `HHMMSS.json` 是历史 immutable audit，不批量改名。

scheduler 的 `last_run_time` 只代表触发过。
是否成功以实际 final audit 和 lane 结果为准。

## 命名规则

人工研究文件：

```text
<entity>-<purpose>.md
```

H1 必须同时写清：
- 对象是什么；
- 这份文件在做什么。

例如：
- `# JUMP / Jumper Legion 公售参与计划与项目跟踪`
- `# Jack / Visualize Value Credits NFT 持仓、稀有度与挂单记录`
- `# PONS 二级市场、回购机制与合约持仓记录`

自动 audit 保持机器稳定命名，不为了美观批量重命名。

## 重构安全规则

整理仓库不能破坏监控。

普通整理禁止直接移动：
- `crypto-daily/`
- `airdrop-tge-monitor/`
- `crypto-300-profit-mission/`

这些 current pointers 也保持路径稳定：
- `portfolio/current.md`
- `performance/current.md`
- `state/latest.md`
- `health/current.md`

任何被 automation 使用的文件如需迁移：
1. 先创建新 canonical 文件；
2. 更新已知引用；
3. 保留旧 compatibility path；
4. 等真实自动运行验证通过；
5. 再决定是否删除 legacy alias。

除非用户明确要求，仓库整理、修复和 QA 不创建新 automation。

## 数据真实性

- 禁止使用中文网站作为 Crypto / TGE / Mission 的确认来源
- 官方、一手链上、交易所原始数据优先
- 钱包实时值优先于历史快照
- 私有交易场所未连接时只能使用 USER_CONFIRMED + 时间戳
- 未识别 / 垃圾资产不计入 NAV
