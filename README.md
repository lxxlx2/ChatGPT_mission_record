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
| EVM 钱包地址盈利研究（独立新模块） | [地址分析 Draft PR #97](https://github.com/lxxlx2/ChatGPT_mission_record/pull/97)，目标目录 `crypto-300-profit-mission/address-analysis/` | 449 地址固定源清单、每批 20 个、23 批、长期与近 30 天盈利/亏损及 CA 证据；**当前在 PR 分支、未合入 main** |

## 当前自动化 / runtime 状态（各任务以最新权威文件为准）

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
- `crypto-300-profit-mission/MISSION_SPEC.md`（长期政策，包括逐项资产 >=$1 计入口径）
- `crypto-300-profit-mission/state/latest.md`（最新模块状态）
- `crypto-300-profit-mission/portfolio/current.md`（最新钱包及 CEX 来源时间）
- `crypto-300-profit-mission/performance/current.md`（初始 $300 + 原六个 Credits 的收益归因）
- `crypto-300-profit-mission/STATUS_SCOPE_2026-10-04.md`（2026-10-04 历史范围快照）

当前模块：
- Frank local deterministic signal: **LIVE**；ACCUMULATION 本地通知 LIVE；MULTIPLE 本地通知 + Gmail LIVE；GPT signal authority 已移除。
- NFT opportunity radar: **SPEC_PRESENT / RUNTIME_PAUSED**。
- MONSTER / 妖币: **V3 2024 验证未通过；V4 在 Draft PR #30 进行研究，尚未批准实盘监控、邮件或交易**。
- CORE PRICE / “整体走势”: **PAUSED**。
- `$300-3000` umbrella GPT task: **PAUSED 2026-10-04**，因为没有剩余实质授权 lane。
- legacy `$300 Crypto资产状态监控`: **DISABLED**。
- production trading: **NO_GO**。
- EVM 地址分析（[Draft PR #97](https://github.com/lxxlx2/ChatGPT_mission_record/pull/97)）：**RESEARCH_ONLY / UNMERGED / Batch 001 PARTIAL**。BSC 20 地址签名活跃度筛查已做，单币 RTX5090 一轮买卖闭合；所有钱包长期/近 30 天全量盈亏尚未完成。此模块不会自动成为 Frank、Monster 的信号源。

Frank 当前不依赖 ChatGPT scheduler；它由本地 deterministic runtime 独立运行。2026-10-10 PR #29 已合并，用户 Mac 上先前授权的 Loop/Dashboard 部署曾通过 7 项只读验收；实际后续运行以本地健康检查为准。

### 美股每日晨报
- **ACTIVE**
- 属于独立任务，不受 `$300-3000` Mission task 暂停影响。

详细任务导航可继续参考：
- `docs/MONITORING/README.md`
- `docs/CRYPTO_AUTOMATION_ARCHITECTURE.md`

如果这些历史导航与最新 canonical runtime/status 冲突，以各模块最新 `MISSION_SPEC` / `AUTOMATION_RUNTIME` / dated status 为准。

## Mission 核心规则与研究交接

**长期权威入口：** [Mission Spec](crypto-300-profit-mission/MISSION_SPEC.md) → [current state](crypto-300-profit-mission/state/latest.md) → [current asset ledger](crypto-300-profit-mission/portfolio/current.md) / [performance ledger](crypto-300-profit-mission/performance/current.md)。专题以对应子模块 README、冻结规则、实际 Git HEAD 及带时间的链上证据为准；旧报告和旧聊天只表示当时状态。主 README 的模块状态为有日期的索引，不保证本地 Mac、Gmail 或链上状态实时更新。

- **事实与来源：** 原始链上交易/RPC/官方 API 优先；官方声称、推断与预测明确分级。来源不可用、分页不完整、价格缺失写 `UNAVAILABLE / UNRESOLVED`，不能当成零或补造数值；不能用中文网站作为 Crypto 项目核实来源。
- **钱包与资产：** 已识别且有可信实时美元估值的每一笔资产 **≥$1** 才计入展示总额；低于 $1 的逐项排除，未标价资产保留待核实。Binance 投资资金计入，**Bybit 整户只记录为生活/房租资金并排除**。转账、退款、解锁、余额增加以及出售毛收入不能直接等同交易利润，不能重复加总。
- **交易盈亏：** 长期与滚动 30 天独立核算，回溯开仓成本、成功买卖交易、gas、代币税、历史兑换价格、剩余仓位和跨钱包资金。单币闭环 `TOKEN_ROUNDTRIP_VERIFIED` 不代表钱包完整 `30D_PNL_COMPLETE`，只筛出近期签名交易也不等于确认盈利。亏损样本与盈利样本同等保留。
- **地址分析固定研究队列：** [PR #97](https://github.com/lxxlx2/ChatGPT_mission_record/pull/97) 冻结 449 个原始地址，按源文件顺序每批 20 个、共 23 批；先筛活跃钱包，再做具体代币、长期/近期盈亏。第一批仅 **BSC 活跃度 20/20、1 个代币闭环**，尚无整批钱包盈利审计完成。未解决的地址进入持久 `DEFERRED`，不得遗漏或只报赢家。**PR 未合并，不可宣称 main 已包含模块。**
- **开发与上线隔离：** 研究、试验及 Draft PR 不能自动升级成生产交易信号。原有 `NO_GO`、暂停监控和用户已冻结的价格/妖币模型规则不因新增研究而改变。未经明确授权不新增/恢复/替换 automation、Gmail 提醒、launchd 或实际交易。
- **Git 与完成判定：** 写入后必须检查真实 Git commit SHA 和远端文件；Draft PR、代码审核通过、回测结果与用户 Mac 实测验收彼此独立。按任务规格需要的 `HHMMSS-final.md` 或 `final-retry.md` 才是任务完成证据，trigger/临时文件不是。失败应原样记录，不能报成功。

完整研究方法：[项目框架](crypto-300-profit-mission/PROJECT_ANALYSIS_FRAMEWORK.md)、[证据流程](crypto-300-profit-mission/PROJECT_ANALYSIS_EVIDENCE_WORKFLOW.md)、[代币原则](crypto-300-profit-mission/token_trading_principles.md)、[Meme 原则](crypto-300-profit-mission/meme_trading_principles.md)。旧模块命名与兼容性清单：[命名审计](docs/mission-legacy-naming-audit-2026-10-18.md)。

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

历史稳定路径及已被代码或审核引用的 uppercase policy、阶段报告、自动证据文件属于兼容性例外。不得为统一外观批量改名。旧人工文档标题不清晰时，优先保留原路径修正 H1 和导航，需迁移时先建立新入口、审计引用并保留兼容性。新建未审核 Draft PR 的文件名暂不作旧资产改名处理。

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
- 钱包实时值优先于历史快照；资产展示逐项独立核实 **>=1 USD 才计入已标价资产**，低于 $1 不计入展示合计，未定价/未查全保留 UNRESOLVED；
- 私有交易场所未连接时只能使用 `USER_CONFIRMED` + freshness；
- provider failure 不等于余额为 0；
- 未识别 / 垃圾资产不计入 NAV；
- 钱包余额变化不能自动当成 PnL；
- paused module 不得伪装成正在提供 coverage。
