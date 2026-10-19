# Monster V2 — 早期链上可交易10x研究：总体架构与停止合同 V1

版本：2026-10-19 / `ARCHITECTURE_REVIEW_BASELINE`。仅属于 [Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30) / `research/monster-v4-local-discovery-20261010`。不是新Stage、不是模型已开发、不是Mac后台监控/自动交易授权。原[决策文档](MONSTER_USER_VALUE_AND_NEXT_VALIDATION_DECISION_20261018.md)及[2025-07-01 Base30例历史探针](MONSTER_EARLY_VENUE_30_PIT_SOURCE_PROBE_BUDGET_AND_STOP_20261019.md)是历史冻结证据，冲突时**保留已冻结实验不追改**，新研究的参数须在读取标签前另行冻结。权限始终`G0 PARTIAL / G4 UNKNOWN / G6 NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。

## 1. 唯一研究决策与量化终止

研究对象是按时间第一次达到**已公开可观察**的真实双向交易准入条件的普通链上代币，包含之后5x/10x、失败、迁池、死亡、下架、未上市、来源不完整；**不是**事后获胜的Alpha/Spot名单。答案分离：
- A 数据：完整源名单（包括死币）及`T_entry`可否按当时数据重建？
- B 信号：在`T_entry`仅用当时可见事实，top-k/前10%能否提高未来30/90天**可卖出**5x/10x识别率？
- C 经济：事前固定研究订单名义额、进场延迟、费用、同池实际深度、退出规则、并发资金占用后，策略的**纸面净收益**能否优于同一可评价母体和执行限制下的随机/朴素基线？

10周是研究资源止损时窗，不意味着10周后所有新前向样本的90天标签成熟。任何前期Source/覆盖/PIT失败即提前停止，不为了凑周期继续堆源码。15个**相互足够独立的可卖出10x标签**是最低**探索计数**，达到也必须报告置信区间、分时段和对照，不是统计显著或商业批准。30/90天未成熟统一右删失，不提前计算不存在的负标签。

## 2. 数据源Plan A/B/C：先证免费可用，再扩规模

| Plan | 何时可用/需验证 | 通过证据及止损 | 成本/权限 |
| --- | --- | --- | --- |
| A：真实可读历史日志的第三方BSC RPC | 在Mac前台手动分别测试BSC V2/V3 Factory `eth_getLogs`，至少三处预冻结、不连续日期；标准BSC官方公共endpoint**禁用logs**，不能当成功来源；必须检查节点旧块logs/receipt、速率、窗口、完整响应和分段重试 | 第一小规模覆盖试验记录`chainId/blockHash/txHash/logIndex/logs range`、无间隙连续块、rowcount与原JSON SHA；择一日能在事前操作预算内完成，7天内至少重跑一日相同范围校验且理想情况下另一个独立来源交叉校验。不以单个响应的SHA证明节点未漏事件。吞吐目标≤30min/天是性能目标，**不是来源真实性替代** | 0美元，禁止绕限速/付费API |
| B：受许可的公开历史索引/数据集 | 仅在A失败后检查能实际查询**BSC**全量`bnb.logs`或等价原事件、历史时段、导出限额与费用；Dune官方确认有`bnb.logs`但免费层API为view-only，不能当免费批量导出；Google2026-10-16官方Blockchain Analytics列表未列BSC，不把BigQuery当已验证BSC源 | 原SQL和参数、执行UTC、数据快照/更新滞后、实际导出所有分片的SHA、可核对的总行数、区块范围和至少10条样例tx跨链浏览器/RPC交叉证实；`page/truncation`和未收录工厂显式计缺失 | 只允许真实免费/合规许可；任何账号、额度、导出受限视`BLOCKED` |
| C：商业索引/归档RPC | A与B皆失败时只可写成本和覆盖差距并请求用户另行决定 | **默认拒绝付费：本研究预算 $0，不得使用账号订阅、充值、购买查询额度。** 未取得明确用户授权则`SOURCE_BLOCKED`结项 | USER_EXPLICIT_APPROVAL_REQUIRED，当前NO |

P0每个Plan一行`PASS/FAIL/NOT_TESTED`、source_uri、实际调用、错误/限制、成本和原始回执SHA。不能以“可能支持”算PASS。原2025-07-01 Base 30例是接口覆盖小试验；正式BSC主母体至少覆盖Pancake V2/V3以及预先确认的其他关键launchpad入口，否则必须标`SCOPED_POPULATION_ONLY`，不宣称全链完整。Solana不在本轮BSC母体；最多两天的独立**只读可行性查证**（不写Raydium/pump.fun新解析器），失败照实报告。

Alpha历史档案只作**辅佐事件/部分覆盖**。可用官方公告快照/独立历史归档确认个别曾上市项目；没有完整历史名单时`ALPHA_COMPLETE_DENOMINATOR_UNKNOWN`，**不得报Alpha coverage_pct的假百分比、不得把Alpha上币结果作无偏主标签**。当前list不能倒推历史已下架集合。USD-M/Spot都要按实交易开始时间和exact token身份验明，不能用期货K线当DEX现货退出价。

## 3. 物理存储、来源和可审计等级

- `raw/{chain}/{source}/{utc_date}/part-*.json[.gz]`：Mac本地只读归档原HTTP/RPC bytes，有限大小，附实际原始字节SHA256、取得UTC、API source、block/hash区间、原响应完整性和行数；**不提交Git，不将私人RPC地址/token写日志**。
- `derived/early_v1.sqlite`为首选（标准库可复算、单机够用）；必要时导出Parquet只作为高性能缓存。不能因表缩减删除样本，按事务提交和幂等重跑。只有manifest及结构摘要进入Git；原始文件不能凭Git SHA自动取得，**必须有明确原始数据可用位置、备份/留存期限及完整复现命令**，否则不能声称独立端到端复算通过。
- `evidence/early/P0..P4/`每Phase至多一份主结果JSON和一份人类报告MD（修订覆盖同Phase带版本号），其他中间过程留在归档及Git commit/PR评论；跨源清单在单个manifest中指定SHA、大小、行数、覆盖时间、缺页、SQL/CLI版本、执行SHA。
- `evidence_grade`要**来源等级与计算状态分离**：`RAW_CHAIN_LOG / OFFICIAL_ARCHIVE / THIRD_PARTY_INDEX / WAYBACK_SNAPSHOT`为`origin_kind`；`DIRECT/DERIVED`为`derivation_kind`；PIT独立`PIT_VERIFIED/PIT_RECONSTRUCTED_ONLY/SOURCE_NOT_ACCESSIBLE/NOT_SCORABLE/IDENTITY_UNRESOLVED`。一个计算结果保留输入字段级lineage及最薄弱的*必要*证据，不能把DERIVED当低品质来源/不能把第三方导出的历史时间戳说成当时真的观测到。
- 历史来源`available_at`必须区分：区块确定的`chain_event_at`、当时已可公众查询的`available_at`**证据上界或UNKNOWN**、本次回溯取得的`ingested_at`。无 contemporaneous recv 原文时不允许凭现在读到的历史日志生成`PIT_VERIFIED`实时观测时点。若只需链上新区块公开可见下界，要以明确保守的可用延迟假设作为重建级别，而非伪装真实网络观测。

## 4. schema先于代码：四实体、多维唯一键和版本演进

权威机器合同为[schemas/monster_early_records_v1.schema.json](schemas/monster_early_records_v1.schema.json)，P0先冻结语义、类型、唯一身份、时间字段与允许缺失值，再写数据读取代码：
- `tokens`：(chain_id, normalized_token_ca)唯一；`project_id`可空且未经独立验证不得凭symbol匹配；`first_known_block`不能夸为部署首块。
- `events`：一个代币对应多个实际池、多个场所、公告及复杂生命周期；`event_id`须与链+txhash+logIndex或公告原始ID绑定，有可验证的`venue/pool/quote_asset/product`和lineage；一个池事件不会直接触发可交易身份。
- `eligibility`：**不是一个token一个永久状态**；唯一键需包含token、venue、pool、rule_version、`evaluated_at`。首次合格`t_entry`只能在当时储备/Swap/真实双向能力已知时出现；严格禁止用T+1h总Swap数回填T+0时点。
- `outcomes`：唯一键需包含token、`t_entry`、研究notional、exit rule、30/90天；分别输出`THEORETICAL_MAX/SELLABLE_AT_NOTIONAL/RULE_EXIT_PAPER`及DEAD/FLAT/5X/10X/CENSORED/NOT_SCORABLE。薄池OHLC max不是可卖出的10x；卖出容量/税/成交限制不明则对应sellable空值且有缺失原因，不得用0代替。
- P1-P3只能**向后兼容增加字段**，字段重命名或语义变化必须有`schema_version`新版本+一次迁移等价检查+明确回放差异；不能因禁止变更而强迫在旧错误结构上叠补丁。feature_set在P2探索时可变，但P3 holdout前完整冻结编号/哈希，且不得重新挑holdout。

## 5. 唯一as-of门禁，支持历史与实时两种时钟

唯一研究读取接口`asof(token_key, decision_at, information_policy)`；任何eligible/feature/score的输入只允许带来源和状态的as-of视图，不能直接读当前events、结果标签或2026现有holder/合约权限。规则是`available_at <= decision_at`，但历史`available_at`无法由原数据证明时只能使用预冻结的`HISTORICAL_BLOCK_DELAY_ASSUMPTION`且结果必须标为`RECONSTRUCTED`，不得声称真实观察回执。

最低CI反例：注入未来Pool/Swap、未来充值、下一小时成交量、后来的币安Alpha公告、token当前owner、未来标签之后，同一过去`asof`输出字节相同；未知可用时间fail-closed；跨场所CA撞名不得合并；一天内卖出/迁池后仍要在结果里记录退出失败；重复事件幂等。不允许PIT测试失败还继续计算训练正例。真实网络重组和供给完整性另外测试，不会被asof一个函数全部证明。

## 6. P2统计和对照：尽早冻结功效门槛，不包装胜率

- 同源同期限，主策略对比：(a)同日期/场所/可交易状态匹配的随机top-k（固定随机种子多重复）；(b)基于第一次当时可见报价侧池流动性/交易活动的单特征朴素排序；(c)旧Binance CEX动量只在共同实质可交易范围作对照，若listing时点导致没有共同风险窗口则`NOT_COMPARABLE`。
- `precision@k/recall@k/top-decile lift/PR AUC`同时报真实机会基准率、事件计数、拒绝源/不可卖/删失数量、每日候选噪声、对低流动性独立场所的稳健性；**不只报涨幅最高的一小撮赢家**。top-k的k按实际可处理的名义候选量冻结，不因观察结果调整。
- **功效停止**：小于15个互相可区别的、90天已成熟、在事前固定量级上可卖出的10x项目，`INSUFFICIENT_POSITIVES`，不对lift下结论。达到15个只是探索启动门槛，还必须报不确定性；不能用一月中许多相关币当15个真正独立事件；按月分块bootstrap、月数很少则报告宽区间或改用holdout稳定性，不能强迫宣称置信区间排除1。原Claude建议的`lift>=3`只能列候选业务阈值，正式阈值在看留出集标签前冻结。
- P2内所有探索试验要有append-only`experiments.log`（包括失败尝试、特征集合和阈值、input SHA）。P3 holdout只允许运行**预先冻结的胜出方案一份**，不是“登记表里编号1”（编号与合理选择无关）；可独立重复计算同一冻结方案，但改特征/窗口/起点/报价即污染holdout，不重新调优。

## 7. 研发流程、人机分工、ADR与安全门禁

**新增能力只允许写`mission_agent/early/`源码包 + `cli.py`统一CLI + 同一研究CI**。实验代码如只执行一次可短期停留在Mac研究缓存，长期可复用逻辑必须迁到包并加单测；不再新建`monster_v4_stageN_*.py`、不新建每批一个workflow、不重审已经固定批准的Stage原raw。移植旧官方ZIP、合约规则、现货/期货时间工具、300U账本的通用资金守恒逻辑须先有before/after等价测试；旧已获批模型/Frank运行时只读，禁止串写。

变更机制：
- **CONTRACT_CHANGE**：母体窗口、币准入、入场时点、30/90天定义、notional、基线和成功停止条件。唯一ADR（`adr/ADR-###-*.md`）记录背景/选择/拒绝选项/影响/用户审批状态/取代旧版本。每Phase默认最多2项重大合同变更；超过则本Phase停止并请求明确新任务，且一旦P3 holdout开始绝不能在同一holdout调参。
- **IMPLEMENTATION_CHANGE**：bug、效率、SQL分区、特征工程、schema向后兼容添加，在既有Freeze不变时用Git提交+确定性单测/集成测试。若影响资金/源覆盖/PIT/模型含义，即便表面“bug”也属于研究结论潜在重大影响，需外部独立review或追加ADR，不是一律豁免审核。
- **CLAIM/PHASE_GATE**：只有P0/P1证明源/因果、P2模型冻结、P3经济结论以及任何上线/授权前的必要一次性独立审查；审核重点原始source/hash、样本留存/泄漏、买卖容量、费后结果，单一固定SHA。P0工程测试可先跑，P3结论审查不能用先前的测试PASS取代；P0/P1低风险小改不循环请外部AI重新批同一证据。PR保持Draft、用户无授权不能把代码Review称部署授权。
- **Canonical pointer/index**：本文件是长期稳定架构合同；原历史决策文档今后只加本文件链接索引而不再累计长篇路线版本；新签字决策进入ADR且旧ADR原文永远不重写，只能由后续ADR明确supersede。历史已冻结Base探针和已审批项目继续独立保留。
- Solana本十周最多2天`SOURCE_FEASIBLE/BLOCKED`来源技术spike（不加入母体，不开发新Raydium/pump.fun解析器，不并Frank生产）；只有BSC研究真正有B/C业务改善证据才由用户另立二期。

## 8. P0输入输出——下一阶段机械执行，不重新讨论设计

固定先跑旧Base30技术探针已知冻结条件（截止2026-11-02、两次一次性研究CI预算各自保留），并以**BSC更相关的V2/V3/launchpad**试连续原日志：Plan A实际可用性及三日期来源分片、Plan B真实许可及导出资格、Plan C一律不采购；按Factory原事件和后续实际流动性/Swap例计算含死币母体小样本及24/30、18/30覆盖。P0不得从曾经公开热门币倒推CA，也不得仅凭Base20个币推论BSC。独立review只针对这份schema/源完整性/PIT否决条件，不必重审旧的1533份ZIP。

P0结项必须交一页确定结果：`SOURCE_FEASIBLE / SOURCE_BLOCKED / INSUFFICIENT_COVERAGE`、三通道实际回执、连续缺块/缺页计数、最初30例（如足够）、18/30双向历史估算的**实际类别**、是否正式启动P1，以及没有通过的根因。无原始数据或历史卖出模拟不可证时只能stop/UNKNOWN；不制造任意成功。
