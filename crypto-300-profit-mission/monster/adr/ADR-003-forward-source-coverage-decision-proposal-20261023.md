# ADR-003 — Monster 下一阶段前向来源覆盖与可卖出验证：审批前设计

- 日期：2026-10-23，Asia/Bangkok
- 状态：`DESIGN_PREPARED_ONLY / SOURCE_COHORT_UNVERIFIED / NOT_AUTHORIZED_TO_RUN`
- 适用范围：Monster Draft PR #30（不属于 Frank、BSC 449 钱包或地址建模）
- 前置事实：[架构合同](../MONSTER_EARLY_ARCHITECTURE_CONTRACT_V1.md)、[ADR-001](ADR-001-research-budget-power-and-decision-governance-20261019.md)、[ADR-002](ADR-002-forward-only-observation-pilot-20261022.md)、[原P0实证](../evidence/early/P0/P0_SOURCE_PROBE_20261019.md)
- 没有 supersede 现有冻结合同，不把本文件的候选时间盒/准入指标当成用户已经批准的新研究参数。本次仅“继续设计与记录”，不续用已经消耗的一次真实Mac授权。

## 1. 结论：真实采样链路已证明，市场来源与策略尚未证明

2026-10-23 用户 Mac 在固定 `c646d438ebdd33183e047e47323315d78aab2869` 运行源码上，只运行**一次**真实无密钥BSC主网前台采样，得12次只读RPC；Factory两次计数 `3535217 -> 3535217`，固定块 `129259581 -> 129259583`，1.039858708秒计数收包间隔，包含祖先验证；用户现场重新验算12/12原始正文SHA。授权已经消耗，没有再次实跑，Git仅保留脱敏摘要。此结果支持 `ONE_SHOT_TRANSPORT_AND_RECEIPT_PIPELINE_PASS`，**不**支持新Pair首次观察覆盖、V3、Four.meme全量、当时全网首次可见时点、可执行买卖或5x/10x。零增长只对本次V2短窗口成立。

2025历史样本（V2按时间冻结30个、Four.meme 538个）和历史来源 `available_at=UNKNOWN` 均不修改；2026-11-02原P0来源截止日照旧，届时必须按既定合同独立结项，不能用2026年实时采集成功来给2025历史来源追认PASS。当前`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`。

## 2. 拟研究的三个独立问题（先A后B后C）

**A：在给定实际接收时点之前，究竟有多少原生事件可见、多少漏掉？** 以冻结的合约/工厂/索引为入口，保留创建但0流动性、未迁池、RUG、死币及缺失数据；先输出venue分母、block连续性和coverage，不看后来涨幅。某场所因不具备完整来源能力，必须写`VENUE_NOT_COVERED`，不能把0个结果当成0个事件。

**B：其中有多少可在首次“收到证据时”被普通用户实际买入和卖出？** `POOL_CREATED`只说明池身份，`MINT/SYNC`仅说明储备，`SWAP`只是历史成交；均不能单独证明冻结名义额的往返可执行性。应另收最初实时可见池状态、quote side、税/交易限制和费用证据，不能以事后最高OHLC或迁池成功定义`T_entry`。

**C：如A和B真正通过，才讨论30/90天后可卖出5×/10×分离力及同限制随机/朴素基线，冻结研究名义额与退出规则须**另行用户审批**；不能默认给出买入金额或从未成熟样本打正负标签。

## 3. 来源能力矩阵：一次采样成功只覆盖V2计数

| 观察venue | 能复用的真实能力 | 前向母体技术门槛 | 当前判定 |
| --- | --- | --- | --- |
| PancakeSwap V2 Factory | `allPairsLength()`在固定BSC块读取已实际通过；`allPairs(index)`和`token0/token1`有离线回归，真实新池个案尚未由此次前向窗口触发 | 记录所有新增index、每个对应Pair和token地址、index/区块hash绑定、每次RPC接收完成时间；跨重组与断线逐段计缺；及时获得首次Mint/Sync/Swap与报价侧交易证据 | `COUNTER_LIVE_PASS / IDENTITY_LIVE_NOT_YET_OBSERVED / COHORT_NOT_PROVEN` |
| PancakeSwap V3 Factory | 历史10块短窗日志仅有有限探针成功，免费公共`eth_getLogs`可受限；V2 `allPairsLength()`方案不可复制到V3 | 必须实际证明每个连续区块的`PoolCreated`完整日志或等价可审计索引、tick/liquidity/Swap；缺日志不能声称V3完整 | `LIVE_SOURCE_UNVERIFIED` |
| Four.meme TokenManager2 | 2025单日538个索引历史状态真实有界读取，5个迁池是**事后胜者子集**；不代表2026年实时TokenCreated事件被连续捕获 | 实时证明index增长或完整创建事件、原始token身份和未迁池个案、迁池前后token与池映射、观察时间以及无法解出的索引分母 | `LIVE_SOURCE_UNVERIFIED` |
| Alpha / USD-M / Spot | 只能作辅助当时公告/开盘证据；不能用今日存活名单倒推历史空缺 | 官方当时发布/接收时间和同CA身份必须独立证明；并非主DEX全量抽样框 | `AUXILIARY_NOT_COMPLETE_DENOMINATOR` |

正式称`BSC_ALL_RELEVANT_VENUES`前，至少须有预冻结范围的V2、V3及选定launchpad证据；否则只能发布`SCOPED_V2_ONLY`的有缺口研究，不得用V2部分数据宣称全市场成功率。

## 4. 提议分阶段验证，而非重做短窗口

**D0 — 本轮，只冻结设计，不运行。** 读入当前一次性manifest的非秘密摘要，确认最小契约与真实缺口；列出每个场所可获得的源、权限和数据费用。源费用仍按ADR-001默认`$0`。提交本ADR，不部署任何软件、不申请有偿服务、不创建定时任务。

**D1 — 若未来获单独批准，拟做至多24小时有界来源覆盖试验。** 此`24小时`只是待审批的工程**上限提议**，不是已批准的运行时间、频率和配额。必须先有适合承载的**非用户Mac常驻**运行环境及合法免费数据源（需要另审具体提供者、流量配额、存储成本及安全）；不允许擅自用GitHub Actions/已冻结2次手动CI预算、Mac launchd/cron、私有主机或Git定时任务当现成方案。计时/逐块证据采用 `chain_block_at` 与 `local_received_at` 两套时钟；包括没有Pair、超时、429、回退和断网的所有区段。必要时只保留短的有界手动窗口，并明确这些窗口**不构成24h完整覆盖**。

**D2 — 只有D1来源指标实测支持，另行审批提议至多7天的前向venue母体观察。** 提议`7天`是来源样本增长/断档指标的观察窗口，**不是**10x结果验证窗口；新增与未毕业项目均保留。任何新策略正例仍需至少30/90天标签成熟，90天成熟可能晚于历史P0的2026-11-02止损日，不得把11月2日当天强行宣布盈利或亏损结论。

**D3 — 只有完整母体与首次可交易证据证明后，才进行同研究名义额的可卖出结果重算、样本外验证。** 原`15个彼此足够独立、90天成熟的可卖出10x正例`功效必要条件不变。新研究不能跳过这些门槛直接做训练/买入提醒/部署。

## 5. 前向source必须生成的最小可审计表（设计口径）

对每个观察interval/每个场所：`chain_id`、`venue`、`factory/program`、`observer_session_id`、`run_commit`、`endpoint_identity_hash`、`block_start/end`和hash/parent链、`rpc_call_started_utc`、`rpc_response_completed_utc`、`duration_monotonic_ns`、`raw_file_sha256`、`request_count`、`factory_count_start/end`、`new_index_count`、`resolved_index_count`、`unresolved_index_count`、`missing_block_ranges`、`clock_check_status`、`provider_errors`、`source_coverage_state`。

对每个候选Pair/token：`first_seen_by_this_observer_utc`，对应`source_block/hash/index`，`identity_status`，`first_liquidity_evidence_utc`，`first_swap_evidence_utc`，`two_way_at_research_notional_status`，`venue_state`。完整来源回补时必须分列`HISTORICAL_BACKFILL_RECEIVED_AT`；**不能**把历史回补读取时间或block timestamp当成事件发生时的实时用户可见时刻。不可见/未读到保留`UNKNOWN/NOT_SCORABLE`，不能偷换为无事件或失败收益。

验收指标必须如实给出：有界窗口中可证连续区块数/缺口范围、V2索引差额与已解索引数、请求成功率/429、原始文件SHA验真率、每个venue独立可评率、接收时延分布、实收死亡/0流动性候选数、不可评估占比；**不定义虚假的全BSC覆盖率分母**。当本次窗口无新增索引时，应写`0 NEW_PAIR_IN_OBSERVED_DELTA`，不得除以0得出0%来源漏报。

## 6. 进入下阶段必须先回答的验收问题和明确止损

- **历史源门禁与前向研究严格分账**：11-02前仍不能证历史同时代 `available_at` 的，历史P0按原合同`INSUFFICIENT_COVERAGE/SOURCE_BLOCKED`结项；继续前向观察不追认旧数据。
- **来源完整性**：未证明V3/launchpad可持续取得无遗漏原生事件/索引，就不可声称“全BSC/全部妖币”；可否仅限V2继续，必须在审阅实际覆盖成本后另做范围审批，不能默默降低研究目标。
- **缺失处理**：遇到RPC限流、非连续区块或超过预算后，应标`PARTIAL/SOURCE_NOT_ACCESSIBLE`，停止扩大；事后回补只能修复历史身份覆盖，不补造原`observed_at`。
- **资源/授权**：任何连续观测必须单独批准运行时间、环境/提供商、存储位置、请求频率/总预算、关闭和撤销方法；不能将一次`--manual-once`执行授权视作新的7天授权。默认零付费、不强占用户高负载Mac、不进入Frank/交易/邮件/生产。
- **产品价值**：若数据只能证明V2计数，长期也拿不到可交易/退出容量，则停止收益方向代码，不再反复追同一Factory的短窗口或补造“已发现10×”示例。

## 7. 当前明确决议与最小下一步

本ADR仅获准作为**研究设计草案**提交Git，下一次有意义工作是基于实际可用的免费来源与目标venue，给出**是否存在合理的非Mac常驻、全来源无漏的获取路径**的成本/覆盖评估；若无合规零付费方案，则明确`FORWARD_CONTINUOUS_SOURCE_BLOCKED`并停止扩充采样器代码。是否同意实际运行任何D1/D2、接受V2单源范围缩减、研究notional及生产部署，全部**未批准**，不可推定。

保留`NO_MERGE / NO_DEPLOY / NO_SCHEDULE / NO_GMAIL / NO_TRADE / G6_NO_GO`；不进行任何真实网络采样、注册账号、CI触发或Mac/云端安装。
