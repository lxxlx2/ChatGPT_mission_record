# Frank / CA 精准研究与多人物钱包扩展 — 技术方案 V1

- 日期：2026-10-13（Asia/Bangkok）
- 状态：`DESIGN_PROPOSED / TODO_FROZEN / CODE_NOT_CHANGED / INDEPENDENT_REVIEW_NOT_DONE / MAC_NOT_DEPLOYED`
- 只读冻结基线：main `17a71c863b44c67f7a1a47639fd482958e56ee4b`。实施时必须重新读取 main 与真实 Mac 部署指纹；该 SHA 不是未来的默认部署 pin。
- 上位约束：`../MISSION_SPEC.md`、`ca-analysis-unified-accuracy-acceptance.md`、`WALLET_CLUSTER_ANALYSIS_SPEC.md`、`frank-wallet-monitor-dashboard-v2-design-2026-10-11.md`、`FRANK_LOCAL_SIGNAL_V1_POLICY.md`、`../local-agent/config/follow_policy_v1.approved.json`。
- 执行清单及证据门槛：`FRANK_CA_MULTI_PERSON_IMPLEMENTATION_TODO_20261013.md`。
- 本提交只有技术方案和 TODO；不等于独立 Review、代码完成、Mac 安装、链上最新值验证或交易许可。

## 1. 目标、排除事项与“已经修复”的严格定义

要一次性完成此前确定的四条产品主线：

1. **Frank 跟单判断准确性**：顶端“当前跟单机会”只放经过策略判定、仍在有效期、满足最新主动买卖/仓位/报价证据的 `BUY / SMALL_BUY`；`WAIT / NO_BUY / SELL / EXIT / CLOSED / QUOTE_STALE` 进入观察、退出或历史区，不得仅因为本地模型 `OPEN` 就占据首屏。没有合格机会时清晰显示零机会。既有冻结策略**不因前端过滤而改变**。
2. **真实多钱包账本与仓位**：可审核地说明“人物持有哪些钱包、各钱包有哪些 token account、确认交易与被动转账、当前余额/市值、可核实成本与 PnL”。模型 `OPEN` 不代表实时链上持仓；一笔转出不直接等于卖出；余额 0 不直接等于已卖出。
3. **通用 CA 统一尽调**：一个 CA、一次查询，由系统先给有来源的项目名称/叙事和市场信息，再逐步追溯持有人、LP/vault、资金来源、共同控制/公共基础设施、Dev 与历史首笔交易，准确给出完成度。取消面向用户的 quick/standard/deep 精度选项。**取消通用 CA 默认 $30 Jupiter 报价**，但不得改 Frank 已冻结跟单报价金额。
4. **老安全修复正确集成**：复核 PR31/32/33/35/39/41 已入 main 的内容，PR28/37/38 未合并内容，以及旧研究分支 H-5/H-6/M-8/M-9/M-10/M-11/M-12/M-13；只把经独立复核、适用于最新 main 的实际缺陷修复并入新的后续 PR，绝不把通过过期基线 CI 当成当前生产 PASS。

**强制架构约束：为多人物 / 一人多钱包 / 日后跨链适配预留稳定接口。** 当前唯一允许运行生产实时信号及本地/Gmail 投递的 `person_id=frank`；第二个人或第二个钱包即使在研究索引中启用，也**不得自动拥有信号、投递、买卖和定时任务权限**。本人资产钱包、被追踪人物钱包、第三方 token 持有人三类身份不得混用。

**排除**：不修改 Frank V1 冻结 ACCUMULATION/MULTIPLE/REENTRY 决策与 Writer；不调参、不自动交易/签名、不重写既有 Gmail 投递或历史状态、不启用多人 `TOKEN_CONSENSUS`、不新增 LaunchAgent 或自动通知、不依赖付费 GMGN/充值、不修改 Monster/NFT/CORE 的运行许可。`PRODUCTION_TRADING=NO_GO`。

“修复”的最低标准是 **真实数据复现 → 算法/接口证据 → 其他 AI 独立 Review → 红绿测试 → 当前 main 集成回归 → 安全 Mac 只读验收 → 用户独立授权的受控部署 → Mac 实际页面/数据复测**，而非 UI 文案变化或 pytest 数字增大。

## 2. 现状定位、代码耦合与不可直接复用的旧成果

冻结 main 上确认：

- `config/frank_local_registry.json` **已有** `persons[]` 和 `wallets[]`，是扩展起点，不应再创造一套相互冲突的注册表；目前只有 Frank PRIMARY Solana 钱包。
- `mission_control/frank.py::FrankReader(production_root, person_id="frank")` 虽支持 person_id 参数，但 `service.py` 直接 `FrankReader(self.production_root)`，`wallet_watch.py` 固定 `PERSON = "frank"`，`server.py` 构造单 FrankReader；不能声称已有端到端多人接口。
- `mission_control/frank.py::candidates()` 的筛选服务冻结信号模型，而非全资产账本。`static/app.js` 将全部非 `CLOSED` 的候选显示于“当前跟单机会”，包含 `NO_BUY`；PR35 只改页面顺序，PR39 只修正文案/历史资金语义。
- `wallet_watch.py`、`wallet_inventory.py`、`wallet_reconciliation.py` 及 ATA/backfill 已具部分只读复用能力，但显式存在 LOCAL_INDEX_ONLY、非原子 32-mint 链上样本、余额/美元价值/成本不完整；不能将该层替换成单纯的新 `person_id` 参数并宣称 PnL 已闭合。
- `mission_control/server.py` 有 `CLUSTER_PRESETS`，deep 仍为最多 20 owner × 100 token 签名 + 50 funding；`meme/cluster.py` 以 `getTokenLargestAccounts` 前 20 token **accounts** 起步，并不是足够的 LP 排除后前 10 **owners** 或完整链史。
- `server.py` 通用 CA 工具在 BASE_READY 和最终报告请求 `execution_quote_30_usdc`；`app.js` 报价 30 秒后过期；`app.js` 外部叙事块仍写“未接入 X/FOMO 外部叙事检索”，`market.name / market.symbol` 直接并列，可能形成“Agency Agency”重复。
- main `server.py` 投递状态仍以旧 `MANUAL_REVIEW/SENDING/SENT_UNVERIFIED` 查询且没有全部研究版异常保护；部署脚本仍 pin 历史产品，不得拿其直接覆盖最新 PR39/41 已合并的版本。
- 2026-10-13 GitHub PR 核查：#31/#32/#33/#35/#39/#41 **已合并**；#28/#37/#38 **未合并**。#30 属 Monster、不在本方案。任何旧 PR 必须对最新 main 做三方 diff/语义验证，不能直接重复合并。
- 目前只有截图和历史本地取证证据，没有本轮独立的新 Mac 读盘或现时链上全量核对；“绿色 Frank 监控正常”**只表示服务运行信号**。

历史具体问题映射及单任务 ID 见 TODO；不得用另一个老状态文件的 `IMPLEMENTED` 覆盖这份最新代码差异证据。

## 3. 多人物 / 多钱包架构（核心前置设计）

### 3.1 分层与权限

`
注册表 Registry (person_id, wallet binding, chain, valid interval, permissions)
  ↓ 受控、只读读取
Chain Adapter (Solana first, other chains interface only; finalized source)
  ↓
Raw Wallet Evidence (wallet + signature + instruction/leg + slot + hash)
  ↓
Economic Ledger (active swap / passive transfer / routing / fee / ATA)
  ↓
Wallet Inventory / Cost Lots / Completeness (wallet + mint + as_of)
  ↓ many-to-person aggregation with bindings and dedup
Person Portfolio & Person Research View (person + mint + source coverage)
  ├─ Research-only Watch / CA study / comparison
  └─ Frozen Frank V1 Reader -> Existing Decision -> Existing Outbox
                                  (Frank only; separate explicit authority)
`

**身份**：
- `person_id` 是稳定不可回收的内部身份标识；`display_name` 仅展示；`chain_id` 使用标准链命名并由 Adapter 声明；`wallet_id` 唯一定位链+地址+有效归属绑定；可有一个人多钱包、同钱包在不同时段归属不同 person 的严格审计关系。
- `source_wallet` 必须属于一个具体 person 的已证实 `person_wallet_binding`，绑定有 `valid_from_slot/time`、`valid_to_slot/time`、来源、角色、批准状态；不能把社区猜测钱包直接并进 Frank 资产或盈亏。关系尚不确定时属于 `WATCH_RESEARCH`，不是已授予钱包权限。
- 钱包地址**只在注册表/证据中出现**，不在 SQL/Python/UI 写死；保留 Frank 现有 canonical 地址和历史 `person_id=frank`，不可凭换名迁移/删除历史主键。已有 `persons[]/wallets[]` 以版本兼容方式扩展，例如新增钱包级 `wallet_id`、`source_status`、`valid_from`、`permissions` 等可选字段，先对旧结构实现兼容解析。
- `permissions` 最小化且默认拒绝：`research_read=true` 可单独审批；`signal_evaluation=false`、`delivery=false`、`trading=false` 对所有新增 person/wallet 默认固定。生产 Frank 权限仅由现有经 SHA 校验的冻结策略与显式 operator release 决定；外部传入 `person_id` 不能打开投递能力。

**多钱包计算**：
- 原始链事件唯一键优先 `(chain, signature, instruction_index, inner_index, token_account, leg_index)`，保留 finality/slot/hash；一个签名触及两个被跟踪钱包不得重复记一次链上总买卖或重复算利润。
- 钱包层各自核对 owner 对应 token accounts + SOL/USDC/WSOL 资金腿；人物层按**经核实的归属钱包集合**聚合净头寸；同人钱包间转账只做内部转移，不是 Person realized PnL；不同人钱包间转账要各自识别，不能凭链上直接关系宣布同一控制人。
- `person_id + chain + mint/token_id + time/slot` 定位人物持仓快照；钱包/ATA、余额、成本批次、价格来源、核对时刻各自保存，不以 `current_raw` 或模型 OPEN 覆盖链上数量。跨钱包、多链价格统一成 USD 仅在被验证的同时间窗行情与成本可用时提供。
- `token_account_owner`、`funder`、`beneficial_owner/person` 分开存：链上的 owner 解析不等于该现实人物的控制权。受益归因必须保留证据强度和公共 CEX/router/fee-payer 排除。

**可扩展但不擅自启用**：未来 `WalletFactsProvider`、`ChainAdapter`、`PersonRegistry`、`WalletLedger`、`PortfolioAggregator`、`SignalProvider` 接口分离；Solana adapter 首先实现。未来 EVM 支持须独立实现 log/trace/receipt/decimals/chain-specific finality 测试，不因类型枚举接受 EVM 地址就宣称已支持。

### 3.2 提议的数据契约及版本兼容

数据/接口 **V2 命名空间** 不破坏现存 V1 `signals`、`v1_states`、`decision_events`、`decision_outbox` 的已有主键、邮件去重 ID 或受审内容。优先 Sidecar 本地 SQLite + 只读生产数据库视图，待独立 Review 后决定真实迁移：

| 表/实体候选 | 主键/必备约束 | 数据来源及意义 |
| --- | --- | --- |
| `person_registry_version` / `person_wallet_binding` | person_id, wallet_id, chain_id, 有效时间/slot, 证据 hash | 已批准研究身份/钱包角色，不是任意地址控制证明 |
| `wallet_source_cursor` / `wallet_raw_evidence` | chain, wallet, signature/instruction, raw hash, finality, slot | 可恢复分页、去重、缺口、原始证据 |
| `wallet_economic_leg` | chain, tx, wallet, mint, leg; direction/type | active market BUY/SELL 与 passive transfer/ATA/fee 分开 |
| `wallet_balance_snapshot` / `token_account_owner_snapshot` | chain, wallet, mint, token_account, as_of_slot | 同链尽量同一 slot，逐账户数量完整性与冲突 |
| `wallet_cost_lot` / `wallet_position_snapshot` | wallet, mint, acquisition lot, evidence status | 成本不明绝不能以零成本计算 PnL |
| `person_position_snapshot` | person_id, chain, mint, snapshot_id | 仅聚合已确认归属钱包，内转去重，显示可核实剩余量 |
| `watch_item` / `watch_transition` | person_id, chain, mint, transition seq | 独立观察状态与冻结 follow signal 分离 |
| `ca_research_job` / `ca_evidence_source` | job_id, exact CA, source_id, observed_at, hash | 单模式研究分页/进度/超时/缓存/可重复读回 |
| `holder_role_evidence` / `cluster_edge` / `narrative_source` | wallet/edge, type, provenance | LP/公共设施/资助/关系/官方叙事证据，禁止臆测共同控制 |

所有价格/金额以 raw 整数及 Decimal 派生，任何“已核实”必须带 `provider, source_url_or_signature, observed_at, slot_or_block, sample_coverage, parser_version, as_of`；历史真实值不会被较新的错误或空响应清零。限流/数据库锁错误不导致返回 `balance=0`。

Schema/迁移：先定义兼容读取旧 Frank `persons[]` 的单人一钱包 fixture；增加二钱包同人、二人物同币、相同地址错误归属、同人转账的 fixture；Sidecar 升级具备 schema_version、独立备份、只读 dry-run、迁移事务与回滚；生产 SQLite 写入只允许另行授权。

### 3.3 API 与前端（契约提案，非已实现）

建议版本化端点，所有接口只读或只读研究任务；`person_id` 必须来自注册表的 allowlist，不能根据任意 URL 自动加入订阅或投递：

- `GET /api/v2/people`：研究可见人物、钱包列表（允许脱敏显示）、钱包认证/时效状态、研究覆盖；只返回获准显示人物，不携带交易授权。
- `GET /api/v2/people/{person_id}/positions?as_of=...`：wallet→person 聚合余额、市值/成本是否可计算、每个来源 slot、模型 vs 链上差异、冲突和漏扫；不能将旧缓存伪装实时。
- `GET /api/v2/people/{person_id}/activity?window=24h|7d|30d|all&cursor=...`：市场主动买/卖、被动收/发、路由未解、异常与覆盖缺口单列；时间范围明确。
- `GET /api/v2/people/{person_id}/watchlist?scope=...`：完整研究观察池、历史退出、手动收藏；**与** `GET /api/v2/people/{person_id}/follow-opportunities` 分开。生产 follow 结果只能对获许可 Frank 用现存 V1 `/api/candidates` 派生做**纯显示过滤**，不产生新决策或投递。
- `POST /api/v2/ca/research` 输入 `{chain:"solana", mint}`，与人物及跟单信号无关；`GET /api/v2/ca/research/{job_id}` 查询 `QUEUED/FETCHING/PARTIAL/INCOMPLETE_EVIDENCE/COMPLETE/ERROR`，`GET .../{job_id}/evidence` 只读详细来源。独立 `GET /api/v2/ca/quote?mint&amount_usdc=...` **只有用户明确提供金额时调用**，无默认 $30。
- 分页、source cursor、报告 ID、schema_version、captured_at、freshness/coverage/status/reasons 为必要字段；客户端不得使用 missing→0；老端点在过渡期只读保持一致，新增界面不应混用两个不兼容版本的计数或历史状态。

## 4. Frank 跟单机会/观察/退出：业务状态机（不改底层策略）

- **行动**：只有 `decision∈{BUY, SMALL_BUY}`、记录为当前有效 `source_signal_id/episode`、符合冻结策略内的 freshness/quote/position gate、最近动作不为 `SELL/EXIT/SELL_POSITION_UNRESOLVED`，且当前没有更新的 `NO_BUY/WAIT` 反证，才可置顶“候选可跟”。最终仍以现存 Decision 为准；UI 不推导新的 BUY。
- **观察**：`WAIT`、`REENTRY_WATCH`、钱包模型 OPEN 但 `chain inventory` 不完整的研究观察，以及尚需证据的资产；单独面板，不能带“推荐买入”措辞、不能自动发送。
- **不跟**：`NO_BUY` 或退出/过期/信号失效，在当前机会区完全不显示；保留可检索历史/审计链路，不删除数据库或邮件历史。当前列表为空时应真正显示 0 个当前可跟机会。
- **仓位**：“Frank 模型状态”和“链上验证余额”是两列；展示可追踪的核实时刻/slot；当无法确认余额，应明确哪个 owner/ATA/token program 未覆盖并由任务继续查证，不能以“仓位不明”作为合格候选入首屏。已可证实余额为零，只能标记 `NO_INVENTORY_VERIFIED`，不能由此推导“已市场卖出”。
- UI 顺序：当前可跟（只列 actionable） → 最新真实活动/重要持仓变化 → 人物仓位摘要 → 精选持续观察（可折叠） → 历史退出和审计；数据健康独立显示 `writer/loop health` 与 `ledger coverage`。PR38 折叠 UI 是候选设计，不应替代数据验证。
- 首屏卡片的模型买入价、历史支付、最新卖出、跟单预期价必须区别时间/金额/资金腿口径；任何价格都记录观测时点，过期交易报价不得作为即时建议。

## 5. CA 单模式完整研究流水线

**查询流程**：输入 mint → 验证 exact CA & chain → 预览“是什么/来源/现价/主池/风险”并注明 `PARTIAL` → 决定性链上 RPC、holder + LP 注册/池账户 → 重要钱包历史分页/第一次 acquisition / funding /路由归因 → 转账关系/公共基础设施排除/高疑聚类 → 外部叙事核实与来源链接 → 同定义第二来源核对 → 完整度门禁 → 结论与证据。

- **代币身份**：不要直接把 `market.name + market.symbol` 拼在两行而未判断重复。以链上 mint 地址、token program/metadata/name/symbol 为链上身份锚，DexScreener 多 pair 只作为市场身份交叉验证；如果 pair base/quote mint 与输入不一致，拒绝该行情。名称/符号相同去重展示；冲突时显示来源及 `TOKEN_IDENTITY_CONFLICT`，不能静默选 DexScreener。
- **合约/市场**：Mint/Freeze、Token-2022 敏感扩展及是否活动、update authority、pool 状态；价/MC/FDV/liquidity/volume/买卖数标注 pair、denominator、时刻。外部图表/ATH 来源和时间未查到则不捏造；比较同一 token、同一窗口、同一指标定义的独立市场源。
- **真正持有人**：`getTokenLargestAccounts` 最多前 20 **token accounts**，先映射 owner 和特殊账户；要算 `EX_LP_TOP10`、`EX_SPECIAL_TOP10`、`CLUSTER_ADJUSTED_TOP10` 必须获取足够深的 owner 排名以填补排除 pool/vault 后的十人，并用可复核的全量/分页或合法索引验证。无法获得充分数据时严格数值留空、报告哪些名次缺失，绝不能将“原 Top20 过滤后”输出为完整 Top10。
- **钱包历史/首次买入**：去掉 `100/50` 是“完整”边界的设计。允许按可解释的数据预算渐进分页，重要 owner 的最初 acquisition、资金来源、是否 market buy、关联内部转账、首次确认的主动交易分开；只在碰到可证的创世/首次事件、完成分页或可解释不可克服的来源限制时结束。路由/Token-2022 等异常腿单列，不把余额变化都计为主动成交。
- **关联关系**：分别显示 `CONFIRMED_DIRECT_RELATION`、`PROBABLE_CONTROL`、`PROBABLE_EXECUTION`、`PUBLIC_INFRA_ONLY`、`UNRESOLVED`，每条关系列 signature、金额、时间、资金源、排除证据；32.93% 的相互转账关系不是共同控制 32.93%，13.6204% 未归因不能和“筹码干净”并列；0% 只表示当前证据未建立控制组。
- **叙事**：顶部“项目是什么 / 主题 / 官网或 launchpad 来源 / X 提及与时效 / 是否出现 exact-CA 官方认领 / 社区传播证据”，链接、发帖者、UTC、实际提及 mint、证据级别；与 DexScreener social hints 分开。GMGN/FOMO/OKX 公共视图只能做公开对照，不购买付费 GMGN API，也不绕过站点访问限制。不能证实项目与该 mint 的关联时禁止冒充“官方认可”。
- **报价**：通用 CA 页面删除默认 `execution_quote_30_usdc`、`$30 实际可成交价`、以及 BASE_READY + 最终两次自动报价请求。保留 dated market reference。未来如果用户明确输入交易金额，单独临时 `quote` 请求，在呈现时实时核对 TTL，可刷新/失效，不把 30 秒以前的报价作为实时值。Frank 的 frozen `quote_usdc_amount=30`、策略缓存与通知逻辑一律不碰。
- **证据门禁**：`FETCHING` 仅表示仍在进行；关键字段不足输出 `PARTIAL` / `INCOMPLETE_EVIDENCE`，在一个统一缺口面板记录 `missing fact / materiality / observed attempts / 429 or auth / last good slot / next legal source`；`COMPLETE` 需达到事先固定的各维度可审核门槛。不可达的事实不猜测、不无限请求，但也不得悄悄标记完成。把 N 个“未确认”卡片变为按重要性排序的有限异常摘要；仍保留可展开的原始证据。

## 6. 数据源、可靠性与安全保护

- 事实优先：Solana finalized RPC（含 mint/account/签名/tx/ATA）、实际 DEX pool/launchpad；参考价 DexScreener 与可访问的第二源；叙事优先项目第一方/X 可访问内容和明确来源；免费第三方工具仅参考、不作为控制人确定依据。
- 限流：可审计的端点选择、`Retry-After`/冷却/分页 cursor 持久化、已读取 hash 与失效时间，限制总体并发避免锁死 Frank 现有监控。来源被限流应列出具体缺口与重试计划；不能在未完整读取时显示 100% 覆盖。
- 统一 `as_of`：链上余额、pool/market、人物归属关系各有独立时效；不同 slot 的样本不得伪装成同一时刻的原子整体。重查核实时可以复用不易变的历史交易，但不能将历史价、历史余额当“当前”。
- 只读研究路径不得写生产 Frank `forward.sqlite`、`v1_states` 或 outbox。任何缓存/Sidecar schema、迁移、可恢复 journal/SQLite backup 都在未来 review 和授权后执行；公共 Git 禁止钱包隐私源数据、邮件、token、用户交易身份、敏感日志。用户另有明确允许的最小化脱敏证据同步须走独立授权/审批及可审计的分支，避免公开批量钱包轨迹。
- 未授权没有新增定时监控、模型决策、交易执行；内部研究接口不能直接接受任意 `person_id` 并升级为实时信号。原生活费 Bybit/个人 Mission NAV 与被追踪人物账本严格隔离。

## 7. 必须先做的真实数据与测试矩阵

以已保留的 Frank 32-mint 历史、J7/BPxx ATA、2026-10-09 三笔活动、Agency 原 exact mint、GOMO 分仓/公开基础设施等已记录样本作为回归基准；**每条已验证结论都必须引用确切交易/slot/时间，不能把截图数字当现在余额**。

必测：同人两钱包内部转账不增 PnL；同人两钱包同 tx 去重；两人同 token 互不污染；空 registry/未经授权 person fail closed；Frank 历史 person id 完全兼容；新增钱包没有通知权限；陈旧/分叉/被动转账/路由/无法查实成本不得给肯定价格或 PnL；最新 SELL 反证下 NO_BUY 必须退出当前机会；多账户池子占 Top20 时 LP 排除后的十人须从 rank>20 获取；前 100 笔只是一小段但不能显示首笔完整；市场 pair mint 冲突；Agency name/symbol 重复；外部帖子非官方 exact-CA 冒名；资金源 CEX 共用不能当共同控制；行情/报价 TTL 已到不能继续宣称实时；RPC 429、SQLite 锁、进程中断/重启保留 cursor 与旧证据；旧服务端+新前端、旧字段不齐均不能报零值或 HTTP 异常。

红灯用旧 main 真复现；绿灯用修复后**同一** fixture；完整 local-agent、真实 Git 回放、JS DOM/浏览器、故障注入与当前 main 合并树。不同 CI SHA 不能互相转嫁 PASS；独立第二 AI Review 必须说明型号/范围/完整 SHA、实际缺陷、修复后再审结果。

## 8. 实施/PR/部署策略

**不做一个巨型无审查 PR**。按依赖建独立、可复核的新 PR：
A. 身份/多钱包 registry 与事实接口（不启用第二人）；
B. 完整账本、持仓核对、观察池与首屏纯展示过滤；
C. CA 来源/链上归因/统一查询和叙事；
D. 历史通知安全修复按当前 main 重建与回滚；
E. UI 聚合、端到端验收与 Mac 受控发布。

分支来自**开工时最新 main**，按仓库命名规范，不强制复用 #28/#37/#38 或早已合并 #31/#32/#33/#35/#39/#41 的分支。阶段交接包含源 SHA、目标文件、数据原始证据、方案、差异、测试、另一 AI 完整 Review、回滚计划与未闭合项。

产品部署 pin 必须取自**最终真实合并树的 immutable product commit+三 product blob**，不能继续使用研究分支或旧 `deploy_frank_dashboard_review_badge.py` 中已过时的目标。Mac 发布分为只读 plan、授权、受控发布、独立进程/HTTP/浏览器/SQLite 复核、回滚验证；已确认的 legacy Loop 运行时历史差异需使用 PR41 设计的专项恢复门禁，不得绕过。

此文档 **设计与排期通过前禁止任何业务改动**。用户本轮仅要求记录技术方案、TODO 和 Git 归档。任何实际生产改动必须后续单独授权；开发阶段不得因本方案自行放行 Gmail、新人物信号、监控或交易。
