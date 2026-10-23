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

## 6A. 2026-10-23 官方资料补充：优先候选为 WebSocket 推送+小窗口回补（非运行实测）

**实际核查来源**：
- [Alchemy BNB 网络页](https://www.alchemy.com/rpc/bnb)明确区分无钥的公开HTTP `https://bnb-mainnet.g.alchemy.com/public` 和**需要API Key**的应用专有 `wss://bnb-mainnet.g.alchemy.com/v2/<api-key>`。之前Mac上的12次成功读取仅使用前者，并**没有**验证后者握手、订阅、延迟、流量或可靠性。
- [Alchemy BNB API目录](https://www.alchemy.com/docs/bnb-smart-chain/bnb-smart-chain-api-overview)列有`eth_subscribe`；[Alchemy订阅类型说明](https://www.alchemy.com/docs/reference/subscription-api-endpoints)列出`newHeads`和按address/topics过滤的`logs`，并明确订阅按**传输数据量计费/计量**；[日志订阅语义](https://www.alchemy.com/docs/reference/logs)说明reorg后旧链日志可能以`removed=true`重发，不可拿首次通知当最终确定。
- [Alchemy BNB eth_getLogs](https://www.alchemy.com/docs/chains/bnb-smart-chain/bnb-smart-chain-api-endpoints/eth-get-logs)当前对Free层公布**每请求10块窗口**、60 CUs/次。BNB官方[公共RPC说明](https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/)说官方列出的mainnet公网节点禁用`eth_getLogs`，但**不等于**Alchemy专有、符合免费层限制的节点也全面禁用。现有此前10块零星历史成功不等于前向连续`logs`可用。
- 对于每约3秒一个块的粗略情景，24h可能接近28,800块；**单工厂**如果完全依赖10块窗口回补至少需约2,880次查询（乘以Alchemy文档每次60CU约172,800CU，另有headers、index、liquidity等查询）。这是容量预算计算**不是实际链上测量或当前账户收费保证**，因此应优先推送、仅对明确缺口小段回补，禁止先开启无上限抓取。

**候选工程设计**：一个带连接状态与区块连续游标的单进程（未来审批后才运行），按**明确预登记的工厂地址和事件topic**订阅`logs`与必要的`newHeads`，本地/被批准的远端即时落原字节和接收UTC/单调时钟；重组日志做`removed`失效且不删除历史raw；断开后使用只读HTTP的**10块分段**恢复block+日志并单独标记`BACKFILLED_NOT_LIVE_OBSERVED`，不能在恢复后把历史数据算作当时真实接收。V2所有索引用`allPairsLength`有限抽检和Factory序号核对；V3/launchpad必须分别有自己的真实源证明。真实终端上是否能订阅这些具体BSC Factory地址、是否准确无漏仍为`NOT_TESTED`。

**运行位置和授权关键缺口**：用户Mac当前负载任务多，不接受未经批准的常驻负载；用户已消费的一次性无钥HTTP授权**不包含**应用专有WebSocket、凭据提取、在远端存钥、后台服务或连续运行。用户现有Alchemy app的`BNB_MAINNET`能力和当月显示$0不等于证实可免费持续收`logs`；无现成获批且保证零新增成本的非Mac计算宿主。必须先有独立额度上限、可撤销权限、凭据储存/清理、流量速率、终止机制和场所源覆盖计划，才能请求单独的D1短时验证批准；不自行安装或试运行。


## 6B. 2026-10-23 官方来源/现有账户核查后的路线排名：Webhook→Workers→D1 优先（更新6A的推荐顺序）

**新排名**（本节只更新设计优先级，不 supersede 原Source/覆盖/PIT合同，未授权创建服务）：

| 路线 | 真正免费/常驻性边界 | 结论 |
| --- | --- | --- |
| **A 优先：Alchemy BNB Custom Webhook → Cloudflare Workers Free HTTP入口 → D1 Free** | Alchemy官方[Webhook产品](https://www.alchemy.com/webhooks)将BNB列为支持网络；[Custom Webhook](https://www.alchemy.com/docs/reference/custom-webhook)提供按contract address/topic的GraphQL原事件过滤；接收端是按需触发的Cloudflare Worker，**不要求Mac/VPS/WebSocket连接常驻**。Workers Free官方[10万入站请求/日、10ms CPU/次](https://developers.cloudflare.com/workers/platform/limits/)，D1 Free[读500万行/日、写10万行/日、总5GB](https://developers.cloudflare.com/d1/platform/pricing/)且[单数据库最大500MB](https://developers.cloudflare.com/d1/platform/limits/)。供应商公开能力为`DOCUMENTED_FEASIBLE`，**BNB Custom具体产品/账户权限/实发事件/签名+持久化/末端源覆盖仍`NOT_TESTED`**；账户/服务均不创建。 | **先验证此源**，如真实可用再申请D1短时运行许可 |
| B 备用：Alchemy BNB`eth_subscribe logs` + 合规免费持续VM | 可订阅目标日志，且免费层有WebSocket；但要求独立24h宿主+安全保存API Key，**无已确认获批的非Mac VM**。[OCI Always Free](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm)与[Google e2-micro](https://cloud.google.com/free)可作为开户/区域/余额/存储与流量逐项核准的备选，不假定可获得容量或免费运行。 | 条件候选，次于按事件启动的Webhook |
| C Cloudflare Cron + HTTP按10块窗口全扫 | Workers Free[10ms CPU、每次最多50个子请求](https://developers.cloudflare.com/workers/platform/limits/)，适合低频健康检查；但每分钟约133块、一个venue至少14次`eth_getLogs`，三venue至少42次，还不含区块完整性与身份/存储。单次cron读到的事件是**延迟查询**，不得写成事件当时的`LIVE_OBSERVED`。 | 不做主早期发现，若获批准只补有限缺口 |
| D GitHub-hosted Actions | GitHub-hosted job[最大6小时](https://docs.github.com/en/actions/reference/limits)；私有仓库免费额度GitHub Free为[2000分钟/月](https://docs.github.com/en/billing/concepts/product-billing/github-actions)，24小时=1440分钟（未计其他CI）、7天=10080分钟，且持久状态不可靠。公开仓库分钟免费也不解决6h单job限制。 | **REJECT**，不得动原两个手动CI预算 |
| E Render Free Web Service | [15分钟无入站请求/消息会休眠、临时磁盘重启清空](https://render.com/docs/free)，免费后台worker不存在；外呼也可能因高流量暂停。 | **REJECT**，不是无漏持续监听 |
| F Cloudflare Worker直接做出站长WebSocket | 官方[Protocols](https://developers.cloudflare.com/workers/reference/protocols/)未列标准可用的出站WebSocket能力，且无持续保活资源保证；不能当作已证明的免费非Mac WebSocket客户端。 | **NOT_PROVEN**，不作为优先方案 |

**经官方资料修正的BSC区块频率与费用上界示例**：[BNB Chain Fermi](https://www.bnbchain.org/en/blog/osaka-mendel-hard-fork-strengthening-bnb-chain-after-sub-second-speed-gains) 2026年已约`0.45s/block`（不是前节按3秒假设）。由此按86400秒/日，**理论目标**约192,000块/日，不是采样实测的固定精确出块数；完全用10块切分查询，**每venue**约19,200次`eth_getLogs`/日。若[Alchemy BNB日志](https://www.alchemy.com/docs/chains/bnb-smart-chain/bnb-smart-chain-api-endpoints/eth-get-logs)按Free 10块/次与60CU/次，约`1,152,000 CU/venue/day`，三venue约`3,456,000 CU/day`，30天约`103.68M CU`，已高于[Alchemy Free 30M CU/月](https://support.alchemy.com/articles/5827006872-what-is-included-in-the-free-tier)（还没计区块头、池解析和确认）。前节基于3秒/块的粗估**已被更近真实资料取代**，不得用于容量批准。

Alchemy Webhooks/WebSockets官方[0.04 CU/交付字节](https://support.alchemy.com/articles/1890990699-how-are-webhooks-priced)。若网络级`newHeads`按约192,000条/天、**假设每条1KB**，即约`7.68M CU/day`或`230.4M/30日`，不适合免费连续全链订阅；按工厂地址+精确事件topic过滤，**只对实际匹配事件计有效推送成本**，费用是否落入免费额度需用真实事件数和实际payload字节进行预算，不能用理论优惠当账单保证。无花费上限机制不能自动升级到PAYG。

**已查现有账户（只读、无泄密）**：已连接Alchemy应用`h6m5pairkgzet7vz`具`BNB_MAINNET`能力；实际`list_webhooks(app_id=...)`的`data=[]`，即此app当前有**0个Webhook**（不是整个团队配额）。团队2026-10账期读数81,352 CU、USD 0.00，source freshness 2026-10-23 04:59Z；官方通用Free套餐有5 Webhooks，但**没有读到该团队真实计划、是否能在该应用创建BNB Custom Webhook、可计费/关停方式或Cloudflare账户已存在的证据**。本轮不读取或导出私有App API key、Webhook管理auth、签名key，也不执行`create_webhook`或启动Workers。

**最小安全数据链合同**（仅待验证）：
1. Alchemy仅订阅经官方地址确认的BSC V2`PairCreated`，再分别验证V3`PoolCreated`和Four.meme全创建事件；不能混用token符号或`Swap`声称每token全部事件。
2. Worker接收时即时写下UTC`received_at`、请求原正文字节SHA256、请求长度、`webhook_event_id`、`webhookId`、source`blockHash/txHash/logIndex`、签名是否通过，**在数据库事务成功后才回复200**；未经[Alchemy HMAC SHA256验签](https://support.alchemy.com/articles/1337366997-what-is-alchemy-signature-and-where-to-find-the-auth-token)的请求直接拒绝，签名key放Cloudflare秘密存储，不入Git或客户端。
3. 对重复推送/顺序变化需按`webhook_event_id`和链日志自然键幂等、重组标无效但保留raw摘要；Webhook自带重试**不能**证明全链无漏。官方[失败重试有时间边界](https://www.alchemy.com/docs/reference/notify-api-quickstart)，且未经持续`allPairsLength`审计时**只能声明已收到的事件完整**，不得声称`ALL_BSC_COMPLETE`；审计/缺块回补要另获授权，不因无推送就判0个新池。
4. D1每个venue/接收区间保留可重放的计数/水位/丢失状态，先在**本地离线模拟**签名、重复、错误/超限、时钟和schema，再请求任何远端服务开通。Webhook`createdAt`不是区块首次公众可见时间；Worker的`received_at`只证明**此接收者最迟收到**，不推出普通投资者可成交、首次流动性或0.45秒发现能力。
5. 正式动用Cloudflare/Alchemy提供商账户及任何API/webhook/Worker/数据库/定时健康检查，须**单独获得用户部署和经常性运行授权**，并冻结`24h`或其他时窗、停止/删除手段、零收费硬限制、每日最大消息/写入量、私有源和数据备份策略。原先的Mac一次性采样授权**已经用完**，本文件没有权限续跑。

**D0本轮结论**：`ZERO_MAC_CONTINUOUS_INFRASTRUCTURE_CANDIDATE_FOUND_DOCUMENTED`；**仍非**`BNB_CUSTOM_WEBHOOK_ACTUAL_PASS`或`VENUE_COHORT_COMPLETE`。与前节仅有WebSocket+VM的判断相比，已找到真正可按事件触发、非Mac/非常驻的**有条件$0候选**，因此应先核验提供商精确产品可用性与安全架构，而不是直接宣告整个研究前向来源永久BLOCKED。若BNB Custom Webhook不支持或无法证明免费硬上限，再回到VPS是否实际可用的门禁，不为满足研发计划自动上云。

## 7. 当前明确决议与最小下一步

本ADR仅获准作为**研究设计草案**提交Git，下一次有意义工作是基于实际可用的免费来源与目标venue，给出**是否存在合理的非Mac常驻、全来源无漏的获取路径**的成本/覆盖评估；若无合规零付费方案，则明确`FORWARD_CONTINUOUS_SOURCE_BLOCKED`并停止扩充采样器代码。是否同意实际运行任何D1/D2、接受V2单源范围缩减、研究notional及生产部署，全部**未批准**，不可推定。

保留`NO_MERGE / NO_DEPLOY / NO_SCHEDULE / NO_GMAIL / NO_TRADE / G6_NO_GO`；不进行任何真实网络采样、注册账号、CI触发或Mac/云端安装。
