# ChatGPT Mission Record

这是长期自动化任务与 Crypto 研究的可审计仓库。

仓库分成两层：
1. **运行层**：保存当前 runtime、state、health、alerts、delivery 与 audit。
2. **研究层**：按项目 / token / Meme / NFT 组织可复用研究。

完整结构规则：
- `docs/REPOSITORY_STRUCTURE.md`
- `docs/X_TECHNICAL_POST_WRITING_GUIDE.md`

## 内容导航

| 类别 | 位置 | 用途 |
| --- | --- | --- |
| 监控任务 | `crypto-daily/`, `airdrop-tge-monitor/`, `crypto-300-profit-mission/`, `docs/MONITORING/` | runtime、state、health、alerts、audit |
| 项目分析 / 项目记录 | `research/projects/` | 项目尽调、公售、协议、产品、时间线 |
| 代币 / 二级 / 合约 / 妖币分析 | `research/tokens/` | tokenomics、现货/永续、funding/OI、回购、挤空模型 |
| Meme 分析 | `research/memes/` | Meme 叙事、社区传播、launchpad、筹码和交易研究 |
| NFT 分析 | `research/nfts/` | mint、collection、creator、rarity、二级和出售研究 |

## 当前自动化 / runtime 状态 — 2026-10-04

### Crypto 每日情报
- **ACTIVE**
- 当前任务采用 08:10 prebuild、09:10 primary、10:10/11:10 recovery，并保留其他 bounded collection 时点。
- Runtime authority: `crypto-daily/` 下最新 spec/runbook。

### 全项目空投与 TGE 监控
- **ACTIVE**
- 当前 schedule: 每小时 `:50` Asia/Bangkok。
- Runtime authority: `airdrop-tge-monitor/AUTOMATION_RUNTIME.md` 及其最新 gate/state 文件。

### $300-3000 Crypto Mission

当前 canonical 状态：
- `crypto-300-profit-mission/STATUS_SCOPE_2026-10-04.md`
- `crypto-300-profit-mission/MISSION_SPEC.md`

当前模块：
- Frank local deterministic signal: **LIVE**；ACCUMULATION 本地通知 LIVE；MULTIPLE 本地通知 + Gmail LIVE；GPT signal authority 已移除。
- NFT opportunity radar: **SPEC_PRESENT / RUNTIME_PAUSED**。
- MONSTER / 妖币: **V3 TRAIN PASS，但 2024 validation 未通过；RESEARCH_FROZEN**。
- CORE PRICE / “整体走势”: **PAUSED**。
- `$300-3000` umbrella GPT task: **PAUSED 2026-10-04**，因为没有剩余实质授权 lane。
- legacy `$300 Crypto资产状态监控`: **DISABLED**。
- production trading: **NO_GO**。

Frank 当前不依赖 ChatGPT scheduler；它由本地 deterministic runtime 独立运行。

### 美股每日晨报
- **ACTIVE**
- 属于独立任务，不受 `$300-3000` Mission task 暂停影响。

详细任务导航可继续参考：
- `docs/MONITORING/README.md`
- `docs/CRYPTO_AUTOMATION_ARCHITECTURE.md`

如果这些历史导航与最新 canonical runtime/status 冲突，以各模块最新 `MISSION_SPEC` / `AUTOMATION_RUNTIME` / dated status 为准。

## 自动运行 audit

新自动运行采用 append-only：

```text
<task>/runs/YYYY-MM-DD/HHMMSS-start.md
<task>/runs/YYYY-MM-DD/HHMMSS-final.md
```

旧的 `HHMMSS.md` / `HHMMSS.json` 是 immutable historical audit，不批量改名。

`scheduler last_run_time` 只表示触发过；是否成功必须看 durable final audit、delivery receipt 和对应 lane 的真实结果。

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

Dated status/scope snapshot 使用已有稳定格式，例如：
- `STATUS_SCOPE_2026-10-04.md`

自动 audit 保持机器稳定命名，不为了美观批量重命名。

## 重构安全规则

整理仓库不能破坏监控。

普通整理禁止直接移动：
- `crypto-daily/`
- `airdrop-tge-monitor/`
- `crypto-300-profit-mission/`

这些 current pointers 保持路径稳定：
- `portfolio/current.md`
- `performance/current.md`
- `state/latest.md`
- `health/current.md`

任何被 runtime 使用的文件如需迁移：
1. 先创建新 canonical 文件；
2. 更新已知引用；
3. 保留旧 compatibility path；
4. 等真实 runtime 验证通过；
5. 再决定是否删除 legacy alias。

除非用户明确要求，仓库整理、修复和 QA 不创建新 automation。

## 数据真实性

- 禁止使用中文网站作为 Crypto / TGE / Mission 的确认来源；
- 官方、一手链上、交易所原始数据优先；
- 钱包实时值优先于历史快照；
- 私有交易场所未连接时只能使用 `USER_CONFIRMED` + freshness；
- provider failure 不等于余额为 0；
- 未识别 / 垃圾资产不计入 NAV；
- 钱包余额变化不能自动当成 PnL；
- paused module 不得伪装成正在提供 coverage。
