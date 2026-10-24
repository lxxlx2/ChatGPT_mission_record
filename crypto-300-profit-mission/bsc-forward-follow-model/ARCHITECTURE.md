# BSC 前向钱包跟单研究：架构 v1、复用边界、验收与终止合同

> Status: `ARCHITECTURE_V1_REVIEW_REVISION / PENDING_OTHER_AI_REVIEW / RESEARCH_ONLY / PRODUCTION_TRADING_NO_GO`  
> Date: 2026-10-19 (Asia/Bangkok)  
> Scope: **新建独立 BSC 前向研究模块的设计文件**；本 PR 仅文档，无采集代码、无在线运行、无交易、无通知。  
> Authority: [MISSION_SPEC](../MISSION_SPEC.md)、[仓库结构规则](../../docs/REPOSITORY_STRUCTURE.md)、[PR #40 冻结需求（固定提交）](https://github.com/lxxlx2/ChatGPT_mission_record/blob/431c02d1fcbe4babe8a2223e4e6fb1b0c0ac3a2c/crypto-300-profit-mission/research/bsc-meme-address-model-v1-requirements-2026-10-13.md)（commit `431c02d1fcbe4babe8a2223e4e6fb1b0c0ac3a2c`、blob `ca9229c32daee9e4b548436d1789e77f808dd9eb`，**未合并、当前分支无此文件、不依赖 PR #40 合并**）。历史冻结合同原样保留。

## 0. 问题、成功含义、决策权限

最终投资问题：**过去多次较早参与重要 Meme 的公开钱包，在未来首次被本观察器识别到新买入后，第三方按统一延迟、规模、退出条件，扣除可证明/保守假设的费用，是否能相对事前定义的对照组取得稳定的纸面净收益？**

分别设三个不互相冒充的结论：
- **L1_CAPTURE**：是否及时、完整地记录本人签名买入？依据独立复查分母、捕获率、确认与观察延迟、断线缺口。
- **L2_EXECUTION**：观察时是否存在可报价、可按事先设定条件纸面执行与退出的路径？依据报价覆盖、陈旧率、不可成交率、保守费用敏感性。
- **L3_L4_ALPHA**：事前筛选是否优于对照组？依据事先冻结规则、簇级收益及不确定性。

`PASS` 仅批准**下一步只读/纸面研究**。永不自动推出实际盈利或资金使用许可。保持 `NO_TRADE / NO_GMAIL / NO_ALERT / NO_PRODUCTION_DEPLOY / NO_NEW_AUTOMATION / NO_MERGE`，实际本机长时间运行也须另行获得用户批准。

## 1. 旧仓库数据复用与隔离

| 来源/组件 | 用途 | 不允许推论 |
|---|---|---|
| [PR #40](https://github.com/lxxlx2/ChatGPT_mission_record/pull/40) 的 23 EOA × 19 CA、原始交易及 P2–P4c | BSC 候选、正负样本、原始证据、解析回归用例 | 冻结研究集并非全市场；历史正向余额不等于可跟收益；**不得**覆盖原 G0/P0–P7 |
| [PR #97](https://github.com/lxxlx2/ChatGPT_mission_record/pull/97) 的 449 EVM 钱包/237 有签名活动候选 | 只读接入其中经过链及 EOA 校验的 **BSC** 候选；保留第三方标签和初始选择偏差 | 237 的 BSC/ETH/Base 并集不等于 237 个 BSC 活跃 Meme 钱包；**不得**终止其独立的 30d/长期盈利亏损任务 |
| 21 行历史回合草稿（PR40 Bulk16 16 条 + PR97 闭合 5 条） | schema/回归与数据质量验证；源 blob 分别为 `51a41aebe7931c242910470a6907e4c93d217568` 与 `e1e1e1eea4f8c5aa998d3278eb18bc9c6b20c623` | 13 个过 PR40 本人签名门禁、8 个暂定 UTC 日期簇**均非**真实公众跟单成交；不能当作干净 holdout |
| `receipt_probe.py`、`transaction_ledger.py`、`verify_block_roundtrip.py`、`lineage_gate.py`、`closed_token_index.py` | **复核接口及测试后**选择性包装为适配器；FIFO 主要供标签抽检，不能阻塞实时热路径 | 未经接口、性能、schema 兼容和依赖审查，不宣称“原样可运行” |
| P4b `public_observer_ingress_gate.py` | 复用“历史自报观察时间不足以证明公众可见”的证据思想和可通过的独立测试 | 不宣称单采集器首次看见 = 全网最早可见 |
| BSC Follow V1、Frank/Monster 实验 | 历史模拟器/规则留作隔离对照 | 模拟收益不等于成交；不得直接引入 Solana 运行时和 Frank 规则 |

数据集与代码**可共享只读适配器**，但 PR #40 和 #97 的冻结范围、审核结论、任务结果、历史指标均独立；不写回两条旧分支。旧历史补证默认封存；若有决定性的 P0/P1 障碍，单案例最多 12 次**免费**只读 RPC、明确终态，不自动开第二轮。

## 2. 五层独立契约（所有记录都有 schema_version、source_ref、ingested_at）

### L0: 观察名单

主键 `(chain_id, wallet_lower, source_id, version)`，字段：
`chain_id, wallet, source_id, source_blob_sha, original_label, selection_bias_note, added_at, status, exclusion_reason, version`。

来源枚举：`PR40_23`、`PR97_449_BSC_CANDIDATE`、`CONTROL_RANDOM`、`CONTROL_SAME_TOKEN`。L0 仅表示**候选名单**，不存事后累计盈利、事后挑币分数或“已证明聪明钱”标签。

不得将 449 个 EVM 钱包无区别地投入 BSC 监控；先去重、检查链范围、钱包类型（需以目标区块 `eth_getCode==0x` 或等价证据确认 EOA，单凭 PR #97 nonce 不足）、已知 Router/CEX/基础设施身份及来源。保留排除与不确定状态。早期候选历史偏差显式记录。

### L1: 交易捕获、买卖确认及时间语义

原始消息（append-only）与解析事件分表；推荐逻辑事件键 `chain_id | wallet | tx_hash | target_ca | side`，同一笔交易多条 Transfer 归并时仍保留原始 log_index 关系。字段：
`event_id, chain_id, wallet, target_ca, side(BUY/SELL/UNKNOWN), trade_tx, block, block_hash, block_time_utc, tx_from, tx_to, tx_value_wei, quote_asset, quote_paid_raw, quote_received_raw, token_in_raw, token_out_raw, receipt_status, confirmations_observed, finality_rule_version, evidence_level, event_state, failure_reason, source_ref`。

独立捕获时钟字段：
`t_first_received_utc, t_first_received_monotonic_ns, t_buy_detected_utc, t_sell_detected_utc, signal_detection_reason, clock_offset_ms, collector_id, ingest_path(WS/POLL/BACKFILL), t_rpc_response_utc, t_receipt_success_utc, t_receipt_confirmed_utc, observation_provenance, gap_id, trial, reorg_state`。

- `t_first_received_utc` 仅为本机第一次看到 tx/hash 的时间；**hash 本身不代表当时能识别 BUY**。`t_buy_detected_utc`/`t_sell_detected_utc` 分别为采集器在当时可得信息中首次识别交易方向和 CA 的时间，才是跟单策略时间起点。不可事后以哈希首见时间或区块时间回填 BUY 信号。以上均不冒充全网最早公开时间。
- 区块时间与观察时间不同；用它们的差不能直接证明节点传播延迟。时间源记录 NTP/时钟漂移与采集方式；可独立交叉验证时另记多观察者证据。
- `E0_SEEN`：见到原始哈希/通知，不代表已知方向；`E1_CONFIRMED`：成功 receipt + `tx.from == wallet` + 满足 F1 冻结最终性门禁；`E2_TRADE_ATTESTED`：E1 + BUY 的目标 CA 入账及可归因的报价付出，或 SELL 的目标 CA 出账及可归因的报价实收。单纯同笔交易出现不相关 Transfer、仅原生 `tx.value > 0` 均不足以升级；`E3_LIVE_CAPTURE_ATTESTED`：E2 + 前向当时实测的 BUY/SELL 方向与 CA 首次识别时间，且未因 BACKFILL 或时钟缺失污染。E3 证明本采集器观察事实，是否可执行另由 L2 评价。
- E0–E3 是追加保存的证据里程碑，**不是永不撤销的真实状态**。F1 须定义可用的 BSC finality 语义或固定 N 确认深度、观察频率及不少于 N 的重组监测窗口；记录首次成功 receipt 与达到最终性门禁的两个独立 UTC 时间；重组按 block_hash 复核并把原等级标记 INVALIDATED。候选的实时报价可以先于 E1 最终性确认，失败/重组事后撤销正式标签，但不删除历史原始报价。
- 事件业务状态 `SEEN -> CONFIRMED -> ATTESTED -> LABELED -> CLOSED`；可以带原因进入 `REJECTED / INVALIDATED / GAP_UNRECOVERABLE`。失败事件保留并进入相关分母。
- 历史 21 行最多可**逐条验证到 E0/E1/E2**，绝不能因为历史补录取得 E3；原 bulk16 的 13 条 owner-signed 不能在未验证买入报价因果前一律标 E2。

**分母双层**：`N_chain_expected` = 从**独立于在线采集器逻辑**的链上签名交易回查/receipt/Token 流向复核得到的可检范围内买入集合；`N_live_captured` = 在窗口内成功实时首次观察的对应集合。每日按钱包+交易哈希交集/差集回溯，记录分页、回查覆盖、供应商缺口、无法解析，以及随机复核。仅以 nonce 增量或 Transfer 首页**不能**形成真实买入分母；发现率分母无法闭合时为 `UNRESOLVED`，不报 95% PASS。

### L2: 报价与纸面可执行性

每 `event_id x scenario_id` 一行：
`decision_time, quote_requested_at, quote_received_at, quote_age_ms, router_or_pool, quote_source, entry_amount_in, entry_amount_out_quote, gas_estimate, price_impact, tax_evidence, exit_rule, exit_observed_at, exit_quote, fee_model_version, exec_evidence, unfillable, unfillable_reason, paper_net_return, evidence_ref`。

`decision_time = t_buy_detected_utc + delta`。`delta` 采用原研究重点 60/300/900 秒作为拟冻结的离线情景；**不**替用户设定实际下单金额。情景规模必须在 F1 列出，并在正式冻结前审核；每一情景测算双向深度、可达路由及退出。

成交证据：
- `QUOTED`：**当时实际发出请求、当时返回**的 Router/池报价，完整存证请求/返回 UTC、参数和响应；仅价格发现，无成交承诺。事后 RPC 储备复原是 `SIMULATED_ARCHIVE_QUOTE`，不可冒充实时 QUOTED。
- `PAPER`：事前规则在当时报价上扣预设 Gas、价格冲击/滑点、税费、无法成交情景后的研究估计；**无实际成交**。
- `REAL`：通过真实签名和链上成功 receipt 复核的自主成交；**本研究禁止生成**。

F0 可以测得采集延迟、RPC 失败和报价不可得比例；**没有实盘单就不能测实际成交失败率、真实抢跑成本或实际滑点分布**。PAPER 的这些部分必须使用固定的保守区间/敏感性情景，不可伪称“实测”。缺失税率或卖出能力证据须按已冻结规则保守 `UNFILLABLE/UNKNOWN`，不得随意置零；报价 TTL、失败恢复及钱包卖出信号被看到后的退出延迟要入模型。

必须同时报告 `QUOTED -> PAPER` 折损。无报价、过期报价、撤池、交易已不可跟等属于**不成交结果**，不得从 L4 统计中无声删除。

### L3: as-of 特征/钱包规则基线

函数 `score(wallet, as_of, data_snapshot)` 只能读取在 `as_of` **之前已公开且已实际进入研究数据可用范围**的字段；禁止当前候选事件自身的后验交易、未来闭合净收益、未来加入的名单及后来补写的结果。要求来源记录 `event_time` 与 `first_available_at` 两种时间。

先用可审计、仅当时可知的简单基线进行数据可用性验收；L4 必须并列报告**含历史候选先验**与**从 F3 第一天起仅滚动使用前向观测的 cold-start 变体**，明确原始候选来源偏差。拟评估的三组特征：滚动**当时已闭合并确认**的回合数/盈利比例、首买距已证市场可交易时间的时长、截至事件当时已知的其他名单钱包参与数。跨多个来源标签只是候选信息，不能直接当盈利率。

CI 必须做**未来扰动测试**：插入/修改 `as_of` 之后的任何记录不能改变过去的特征/分数；输入乱序和延迟到达亦须可复现。同簇共振只能使用当时已被采集且确认的买入，不能回看最终行情簇成员。

### L4: 一次性评估

对每一场景以**实际样本纳入流程**为依据报：
1. 总链上应发现买入数、在线捕获数、E0/E1/E2/E3 数及拒绝/回填/无报价/未平仓事件数；
2. 簇数量、token/wallet/时间分布、非独立度；
3. `QUOTED` 覆盖、`PAPER` 覆盖、不可报价率、不可成交率、净收益（绝对/百分比、均值/中位数）、precision@k、最大回撤、单币利润集中度；
4. 配对对照组增量与按簇重抽样置信区间，同时补充按**Token 整组**剔除的稳健性检验；市场时段/同钱包相关性作敏感性分析；
5. 基准数据缺失或样本太少时诚实判 `INSUFFICIENT_DATA`。

随机参照按相同链、预先定义周窗口、Router、买入规模档位筛选**普通签名买入 EOA**，不要求同 CA；匹配过程不得使用未来盈利、最终买入表现或信号以后的可用数据。**实时发现并前向随机抽样普通 Router 签名买入**是 F0/F2 必须验证的独立数据源能力，候选外普通钱包需进入与主组完全相同的实时报价管线；拿不到时不能凭事后匹配补造实时对照。另设同 CA 参照，仅回答“入场时机”，其结论与钱包筛选对照分开。

样本足够进入探索评估的最低门槛**暂拟** `>=30` 个簇；不等于统计显著，不等于自动 PASS。正式 P/F/INSUFFICIENT_DATA 的利润、相对基线、置信界、集中度、最大回撤及覆盖质量阈值须在 **F1** 事先定义并提交复核，F2 仅因基础设施测量错误作带版本复审的修改，且必须在 F3 第一条正式事件之前固定。显著性检验按簇配对且保存原始输出；不得事后重选有利 bootstrap 配置。


### 关键执行合同：审查修订项（PR #113 R2，优先于抽象定义）

**A. 定时 QUOTED 与对照组证据对称（原 P0-2）**

1. E0 的纯哈希可能不足以确定 Token；**首次确认其为 BUY 候选及 exact CA 的实时识别时刻** `t_buy_detected_utc` 才能触发该事件的 L2 三档请求。`t_first_received_utc` 只记原始哈希接收，禁止不具备买入信息时反推“用户早可跟”。
2. F3 对全部符合前向抽样合同的主组与实时随机对照，使用**同一个**在识别 BUY 候选后立即安排的 `+60/+300/+900s` 单调时钟调度器，保存 `scheduled_deadline / quote_requested_at / quote_received_at / queue_delay_ms / quote_source / raw_blob_sha / pool_state_block`。分别报告准点/迟到/失败；超时、数据缺失不能由后来回查补成 QUOTED。E1/E2 最终通过前可预先保留 `PROVISIONAL_QUOTE`，最终不合格时只保留原始事实并标 REJECTED。
3. 对照必须**实时**来自候选名单之外的普通 Router 本人买入流，按事前随机种子和当时已知 chain/week/router/size-bin 条件选择，不能使用事后最终收益、Token 涨幅或未来交易。其 BUY 识别、finality、报价、费用、缺失和时间戳标准与主组一致。没有这种数据源则 F0 阻断策略比较；事后控制组只能是 `CONTROL_ARCHIVE_SIMULATED` 附录。
4. 候选未能在某个截止时间前识别、获取报价或返回有效报价，写 `MISSED_DEADLINE` / `NO_QUOTE` / `STALE_QUOTE`；保留在总分母，不能事后重新锚定 `t_observed`。

**B. E2 买卖机械规则（原 P1-1、P1-2）**

1. `side=BUY`：`receipt.status=1`、本人签名、目标 exact CA 净入账，且通过冻结的 Router/路径因果核查。原生 BNB 情况：`tx.value>0`、`tx.to` 为 F1 已验证的 Router/入口地址且同 tx 的 Swap/路由日志可证明报价投入与目标 Token 入账有关；ERC20 路径：exact quote CA 的 `Transfer(from=wallet)`（含正确的真实 payer 路径）与实际 Swap/路由和 Token 入账对应。**不能只凭 tx.value 或同 tx 独立 Transfer 自动宣称 E2**。
2. `side=SELL`：本人签名、目标 exact CA 净流出及可归因的 WBNB/USDT/USDC 或原生 BNB 实收；SELL 也有 E0–E3 和首次本机识别时刻。未能追溯出金时标 `SELL_QUOTE_UNRESOLVED`，不把卖出区块时间当成第三方可见时刻。
3. 多跳、聚合路由、转税、Router 白名单以外的路径走 `QUARANTINED / QUOTE_PATH_UNRESOLVED`，不得为了提高统计数量而事后扩大 E2。F1 按签名 calldata、Router address、官方报价合约 CA 和事件日志建立可机械判定的白名单及负例测试。

**C. 发现分母独立性（原 P1-4）**

每日独立回查使用**与实时 WS/资产转账 API 不同的方法**：固定区块/交易索引构造完整候选 EOA 签名交易集合（或等价可审计完整索引）→ receipt → 目标 Token 入出/quote 因果。优先不同服务商，并留存两路来源/具体限制及差集；同一 Alchemy 账号不同接口并不等于完全独立，需暴露同源故障风险。无足够权限/分页/区块交易索引支持时报告 `DENOMINATOR_UNRESOLVED`，不算捕获率 PASS。

**D. UNKNOWN 与盈亏分母（原 P1-6，主判决口径）**

- **进入前不可执行**：报价缺失/过期/税未知且冻结策略禁止买入，记 `ENTRY_NOT_EXECUTED`，**资本没有支出，不能当作实际 -100% 亏损**，仍算漏失/不可执行机会，纸面组合现金未变化。
- **纸面已投入后退出无法证明**：主判决采用最保守压力计算，假定剩余投入全部亏损（`ASSUMED_WORST_CASE`，记额外已确定 Gas/成本），对照组实行同政策；标明这是**假设下界**而非链上实亏。并报条件结果（剔除 UNKNOWN）与覆盖率/缺失率，防止任何一边有选择性缺样。
- **UNKNOWN 不可默认为 0**；若系统不能区分“没买”与“买后无法卖”，保留 `UNRESOLVED` 并视为整体证据不足，不能给出盈利模型 PASS。精确参数和通过阈值在 F1 冻结。

**E. 合同验收与数据泄漏（原 P1-3、P1-5 及 P2）**

F1 必须冻结 finality 标准或 N 确认及 reorg 窗口、Router/quote 配置、退出卖出判定、样本外绩效与 L4 阈值；F2 不得看到正式收益后优化。F3 的视图只露 L1 非收益字段，禁止从实时 QUOTED 或 “可跟”状态间接暴露收益。F0 来源分层抽样不宣称代表所有钱包；L4 并列报告“含历史候选先验”与“仅 F3 前向滚动”评分，并必报整 token 聚合稳健性。所有**策略/数据语义跨越**进入真实 F0 前必须独立 Review。

## 3. 市场行情 episode 与两类时间用途

正式评价 `cluster_id = chain_id | exact_ca | episode_index`。拟初值：对**同一 CA** 按首买可见事件顺序切分，连续两次买入之间间隔 **大于 6h** 时开启新 episode，跨 UTC 午夜不切簇。无买入 6h 规则在 F1 冻结；池储备波动只作辅助分层/敏感性分析，**不强制同时超过某阈值**，否则出现超长混合行情和来源稀疏带来的不稳定。

注意两种用途必须隔离：L4 可以用完整观察期对事件**事后归簇以正确计算依赖性**；L3 的共振特征只能使用事件时刻已知的簇前缀、已确认名单钱包，不能读取未来簇成员。

**L4 必报**将整只 token 合成一个大簇的敏感性结果、按 Token 整组剔除、按时间周/月剔除及按钱包聚合结果，以说明 30 簇是否实际上只有少数 Token/大行情支撑。

## 4. 冻结及实验泄漏合同

- **TRIAL**：F0/F2 调试和候选数据源选型阶段，所有记录 `trial=true`，不得进入正式 OOS 样本；期间允许更换采集器技术方案与修复缺陷。
- **ARCHITECTURE_V1**：本文件先在独立 Draft PR 审核。不是已经完成的 F1 策略冻结，不预先把候选阈值宣称为已验收。
- **INFRA_FREEZE**：F2 结束并通过独立源回放与实际运行验收后记录代码 SHA、schema SHA、来源和缺口版本；正式期仅 P0/P1 紧急修复，形成新 infra SHA、变更影响窗口与 `gap_report`，保留旧事件。
- **STRATEGY_FREEZE**：在 F3 第一个正式事件**之前**冻结名单 snapshot/blob、对照组抽样规则、delta、规模情景、退出、税/Gas/滑点保守参数、共振规则、cluster 初值、评分和终止条件为 `FREEZE.json` + SHA。正式观察期无策略调参；任何策略更改属于**新实验**，旧版本与失败结果永久保留。
- **收益盲化**：F3 每周报告只允许 L1 发现率、延迟、失败/缺口、时钟、Quote 覆盖和监控资源成本；**不得披露价格路径、逐事件报价、可跟状态、盈亏、胜率、盈利钱包排行或区间回报**。原始报价可按最小权限保存用于 F4 解盲。完整收益标签可以按冻结逻辑盲态落盘，但 F4 才解盲评价。F3 非正式问题修复不得读未来收益挑修复条件。

## 5. 阶段门禁、交付与停止

| 阶段 | 界限/输入 | 实际交付物 | PASS/FAIL/不足 |
|---|---|---|---|
| **F0 可行性原型** | 按 L0 来源分层抽样 10–20 个 BSC 钱包（冻结随机种子）；24–48h 技术试运行；免费 WS/POLL/混合源、**实时随机对照流及另一套回查方法** | `F0_REPORT`：技术可用、请求额度/错误/费用、成功与失败的原始事件、首见延迟、WS 断线、缺口、独立复查分母能力、对照组来源是否可获 | 若观察窗口无足够真买入，**不宣称达标**；用保存的正负交易作功能回放，`DATA_INSUFFICIENT` 时延长技术验证须另行批准；数据源不可承担观察成本则 `FAIL` |
| **F1 架构、名单与情景合同** | F0 报告及独立架构 Review | 审核后的 `ARCHITECTURE.md`、L0/L1/L2/L3/L4 schemas、候选 `FREEZE.json`、对照组可行性、目标预算 | 缺失关键 L1/L2 数据路径不得进入 F2 |
| **F2 集成验收** | 已审核接口及有界本地测试许可 | 源到事件到报价到只读视图 V 的端到端验证；故障、重组、回放、幂等、分页、缺口；建议连续 7 天运行抽检及覆盖率报告；`INFRA_FREEZE` | 捕获率目标初拟 >=95%，但须有可审计充分分母；不能仅凭 nonce 变化声称“无漏”；严重缺口阻断，低频真实事件为不足 |
| **F3 前向观察** | 经过独立审核的 `STRATEGY_FREEZE` 及已获批准的本机**只读**运行 | 第一窗 6–8 周；时间、原始事实、缺口和报价存证；每周只报告采集质量 | 少于 30 个有效独立簇/对照不足/持续严重缺口则 `INSUFFICIENT_DATA`；不擅自延长/改规则 |
| **F4 纸面收益评估** | 固定观察账本 SHA | 对冻结规则与两类对照**一次**计算并出具 L4 报告；保守费用敏感性及置信区间 | 不在原正式样本上换配置重跑 |
| **F5 独立审查与判决** | 固定 F4 SHA 与全部源 blobs | 另一 AI 的 `APPROVE / REQUEST_CHANGES / BLOCKED_INSUFFICIENT_EVIDENCE`；业务判决 `PASS / FAIL / INSUFFICIENT_DATA` | 审核批准仅表示证据和流程可靠，不准实盘；下一轮需独立计划 |

F0 的 `>=95%` 是**有足够覆盖时**的初拟技术线；24–48h 10–20 钱包无真实机会时不能得出“采集器完美”结论。F2 需加入独立的链上已确认交易回查覆盖证据，而不只看每小时无服务故障。

### 产品验收 V（研究只读）

**F0/F2 试运行**可展示 `wallet | CA | 首次识别时间 | 区块/确认 | evidence | 最新报价时间/有效期 | PAPER状态 | 证据链接 | 缺失原因` 验证功能；**F3 正式观察仅展示 L1** 的钱包/CA/捕获与确认时间/等级/缺失原因，隐藏报价、价格、可跟状态与任何可反推收益的信息；**F4 解盲后**才展示 PAPER 与 QUOTED 结果。**“可跟”一词必须明确是 PAPER/QUOTE 级别，不构成交易建议。** 历史21条用合成/封存展示验证即可，不混为实时机会。研究 UI 不发送信号，不启动邮件，不连接钱包签名。

## 6. CI 与开发治理

1. 每个 PR/任务标注对应 `L0/L1/L2/L3/L4/V`、业务增量、接受准则、最大调查成本及旧模块不受影响的证据；无主线增量不得开“Stage N”细枝。
2. 采用 Git 固定 source blob、代码及测试 SHA；源不完整、null 与零分离；负向事件、丢包、过期 Quote 和回填留在结果分母；历史21条 schema 回归。
3. 建立契约/负例测试：误把 Token Transfer 当 swap、tx.from 不同、receipt fail、同区块多次 Transfer、WBNB 转移非本人出资、quote 缺失、重复/乱序、时钟回拨、WS 断线、BACKFILL E3 误升级、重组失效、未来标签泄漏、同币簇跨午夜、共振“未来钱包”计入、PAPER 冒充 REAL。
4. CI 对禁止交易/邮件/通知/生产路径进行结构和导入检查，并提供可复查的 denylist/allowlist；**静态扫描不是绝对安全保证**。运行密钥与任何账号敏感值不得进 Git。
5. 一阶段一个有界 Draft PR，至少有真实运行/离线测试、原始证据、F0/F2 的资源用量及可核对的固定 SHA；阶段间其他 AI 独立审核。不要先开全部未来 Stage PR。
6. 必须遵守仓库实际命名与结构规则。开发顺序：核查事实/选数据源 → 架构/设计 → 实现 → 他 AI Review → 测试 → 经授权的本机只读验收 → 修复复验。审核不是自动合并/部署/交易授权。
7. PR #40、PR #97 独立 Draft；新实验不改它们的数据、冻结字段、指标、原目标和已有历史结论。新研究目录归属 Mission 下独立研究模块；F1 阶段评估 `docs/REPOSITORY_STRUCTURE.md` 是否需要补充目录映射，禁止修改旧监控路径。

## 7. 待 F0/F1 以真实证据填充的空位

- 免费 BSC 数据源及配额、WS 是否及时、历史完整回查是否可做、**实时普通 Router 签名买入对照流、相同时间三档报价任务、独立区块/完整签名交易回查方法**；无法免费实现即在 F0 失败或申请新方案，**禁止付费 API/充值门槛代替批准**。
- **F1 必须固定并审核**：正式金额规模列表、Router/quote exact CA 白名单及 E2 机械验证规则、E1 finality N 与重组窗口、Token 排除与合约风险规则、报价 TTL、退出规则（跟目标卖出时第三方延迟识别/24h 等）、不可卖情景、税费缺失时默认处理、目标流动性最低值和超额收益的明确统计门槛。
- 完整性指标各自分母：链上复查事件分母、被观察可识别事件分母、可报价/纸面执行分母、策略筛选分母；确保 **0/缺失/未查询** 分开。
- 6–8 周是第一观察窗而非保证通过的时间。样本不足须书面结项，再决定是否另行规划，不持续无限延期。
- 已存在的 21 条源行 schema 验证资料只作回归输入，不直接证明真实下单/跟单效益。

## 8. 正式开工门槛

**本次文档提交只建立待审设计；尚未批准 F0、未创建或运行采集服务、未将任何监控设为后台常驻。**

架构经另一 AI 独立审核通过、与原冻结需求的差异被明确接受后，才允许按 F0 合同启动**有限期**免费只读技术探测。F0 未通过不创建 F1/F2 的无意义规模化代码。最终策略评价至少达到 `INSUFFICIENT_DATA` 也必须在期限内给出可追溯结论，不以“再查一个历史回合”替代。
