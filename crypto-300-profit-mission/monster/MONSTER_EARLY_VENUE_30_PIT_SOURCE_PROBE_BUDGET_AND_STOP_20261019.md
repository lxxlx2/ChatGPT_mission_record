# Monster：早期交易入口PIT覆盖度探针（30例、源门禁、预算与真实试探记录）

状态：**SOURCE_DISCOVERY_BLOCKED / COHORT_NOT_YET_FORMED / NO_MODEL_DEVELOPMENT**。创建时间2026-10-19 Asia/Bangkok。沿用原PR #30 / `MONSTER_MODULE_DEVELOPMENT_RULES.md`、Stage77风控；不是新Stage、不是Alpha/DEX生产授权，也不是30个负例研究结论。

## 0. 目标与反例母体，而非事后赢家

本轮唯一任务：先证明能够在**一个预定历史时点**从不依赖后验涨幅或当前存活名单的完整来源抽取30个不同的真实token CA，再独立证明五个生命周期时点的历史证据可查程度，并重点检查DEX最初“创建池子≠充入流动性≠能在可用报价双向Swap”的D2区别。成功前**不开发预测模型**，不扩大为昂贵的18个月全链溯源。

样本来源选择：Base（chainId 8453）、Uniswap V3官方Factory `0x33128a8fC17869897dcE68Ed026d694621f6FDfD`，官方[Base部署地址](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-base-deployments)；截至本次是可连接的技术探针，不表示Base是后续投资范围或对用户要求的BSC/Solana的替代已获认可。

**预冻结样本选择，不偷看未来涨幅：** 若可以查询完整按日志顺序的2025-07-01T00:00:00Z至2025-07-02T00:00:00Z的该Factory `PoolCreated(address indexed token0,address indexed token1,uint24 fee,int24 tickSpacing,address pool)`链上原事件，则按(blockNumber,transactionIndex,logIndex)升序；仅保留当时有WETH/USDC作为一侧的池、另一侧为不同代币CA，事先排除基础资产与事先已知稳定币（必须预先提供冻结排除表，不可根据未来涨幅排除）；同一CA多费档池只取第一次；选前30个。**绝不因后来没有涨、退市、归零、当前合约不可用而删例，不能挑30个已经知道没涨的“负例”。** 30只是源可用性小样本，不可当12–18个月投币市场准确率估计；未来12–18月正式母体要覆盖更多工厂、链、月份、死币。若工厂无法完整扫描指定区间，**本样本的抽样过程本身无效**，不得用现在的热门币列表代替。

## 1. 五个严格PIT时间点与明确未知的分类

每一例应有统一`chain_id/token_CA/first_anchor`以及原始证据URI、来源hash/txhash、block height/txindex/logindex或发布时钟、`observed_at`、`available_at`与可用性边界。五类分别为：

1. **智能合约部署**：creation交易、部署区块与时间、部署合约本身地址。代币如为代理、映射/同名不确定则`IDENTITY_UNRESOLVED`。
2. **DEX首次交易入口**：原`PoolCreated`事件＋当时第一次真实注入流动性的`Mint/Sync`（依AMM模型）和首真实`Swap`日志/方向、能还原的双向报价及交易时段；**池存在不代表能交易，更不代表实际能以固定金额卖出**。V3 tick/流动性须按历史状态求报价，不准拿2026年现存储备回填2025年深度。
3. **Binance Alpha**：当时公开的上币/交易公告和真实首可交易时点，或有独立覆盖完全的无上市记录证明。今天Alpha token list当前listingTime本身不是独立历史公告发表时间。
4. **Binance USD-M合约**：当时官方开通公告及同合约真实成交/身份倍数映射；期货价格不作为DEX或Spot的买入价。
5. **Binance普通Spot**：当时官方开通/交易状态公告及已收盘成交来源；历史后缀USDT同名不代表就是链上CA。

逐字段值只允许`PIT_VERIFIED`（原事件/文本/sha在所研究历史时点已公开）、`PIT_EVENT_ABSENT_PROVEN`（必须证明完整官方事件索引覆盖，否则禁用）、`SOURCE_NOT_ACCESSIBLE`、`IDENTITY_UNRESOLVED`、`NOT_SCORABLE`。在没有完整原来源时，不得将`UNKNOWN`当成无上市，**所有抽到的30例都保留在分母**。不同场所的“没有上币”不意味着来源无覆盖；计算可用性必须区分“该事件后来未发生”与“源数据无法评价”。未来盈利标签单独建立，在本次源验证前不读取。

## 2. 先冻结停止条件 / 最多两次一次性CI，最长到2026-11-02

**硬预算**：覆盖度探针最多**2次仅手动push触发的一次性GitHub Actions运行**（并不要求必须发起CI），以及到2026-11-02为止最多14天的源和字段可用性核验；**不创建计划任务**，不购买API额度，不为凑30改母体、再造Stage或多轮其他AI评论。当前阶段可直接只读连接器检查；仅确认了获取路径可行之后才允许花一次CI额度构造30例和做检查。

* **Source stop（优先立即生效）**：若无法按历史事件时间顺序重建原Factory完整候选分母、取得足够至少30个CA以及去重证据，立刻记`COHORT_NOT_FORMED_SOURCE_BLOCKED`，**不得开始新模型代码、不得把0例除以30当成0%成功率**。禁止为补这条源链盲目重复付费/分页或换成当前幸存代币。
* **Coverage stop（只有真正冻结30例后才计算）**：必须30/30保留身份与原`PoolCreated`哈希/区块，至少24/30（80%）能证明代币部署和首次池创建这两个基础时点的PIT，至少18/30（60%）能取得首实际流动性和成交且能支持**至少一笔可按数量与手续费模拟双向的同刻成交条件**；Alpha/USD-M/Spot分别给出可核证有/无/未知及来源覆盖分母，不能因某币历史从未在Binance上市便机械判五列失败。若达不到门槛，则本候选早期来源路线`REJECT_INSUFFICIENT_PIT_COVERAGE`，不写预测器。
* **模型止损**：即便Coverage通过，下一真正时间隔离OOS无法比原CEX动量基线及同期间等额随机候选在费用后可执行净回报上改善，则`REJECT_STRATEGY`，不得依赖少量已曝光赢家微调规则。D2无历史双向可执行证据时G4继续UNKNOWN，不许宣布回报PASS。

## 3. 2026-10-19真实源探针：未得到30份样本，不编造覆盖率

| 查找途径 | 实际调用/观测 | 判断 |
| --- | --- | --- |
| 已连接Blockscout BSC | `get_transactions_by_address(chain_id=56, factory=0xcA143Ce..., 2025-07-01 00:00–01:00Z)` 返回`Chain ID '56' is not supported`；`get_chains_list('BNB')`仅匹配Matchain,不含BNB Smart Chain | `BSC_SOURCE_UNAVAILABLE_IN_CONNECTED_BLOCKSCOUT`，不把BSC当真实0池 |
| 已连接Blockscout Base | 解锁会话后对官方Uniswap V3 Factory地址按`2025-07-01 00:00–01:00Z`访问`get_transactions_by_address`返回`PRO API credits exhausted (HTTP 402)`，工具明确提示等待额度重置或充值；本次**不购买、不无意义重试** | `BASE_INDEXER_SOURCE_BLOCKED_BY_PROVIDER` |
| 用户已有免费Alchemy app（选中已既定的All Chains app） | 实际读取Base历史区块成功；对BNB链Factory尝试大范围`eth_getLogs`收到免费层`max 10-block range`限制（应改为至多10区块）；Base Uniswap Factory在2025-07-01附近的五段10区块日志探针，5段均无事件（样本50区块、时间**非连续**）；不能推出当日0池或首次30币缺失 | `CHAIN_ACCESS_PARTIAL / CONTIGUOUS_FACTORY_EVENT_ROSTER_NOT_BUILT` |
| 通用公网程序运行环境 | 对Base Blockscout、GeckoTerminal和Binance公开域名尝试HTTPS时DNS不可解析（当前容器网络受限），并非网站本身停服 | `RUNTIME_DIRECT_PUBLIC_HTTP_UNAVAILABLE` |
| Binance Alpha官方开发者市场数据接口 | [官方文档](https://developers.binance.com/en/docs/catalog/advanced-trading-alpha-trading/api/rest-api/market-data)公布`agg-trades`和`token/list`接口，但**未形成旧代币完整下架前名单/公告PIT原本**；不能用现在列表声明历史全人口 | `HISTORICAL_ALPHA_COMPLETE_ROSTER_UNVERIFIED` |

来自官方的[Uniswap V3 Factory源码](https://github.com/Uniswap/v3-core/blob/main/contracts/UniswapV3Factory.sol)确认`PoolCreated`是池子**创建**事件，不等于`Swap`。本次Base历史区块二分探针成功定位2025-07-01附近块号约`32269xxx`；这些查询仅验证历史区块可读，**没有完成完整24h/30CA工厂日志扫描**，没有做DEX深度或5种历史时点验证。

**真实项目计数：COHORT_CREATED = 0；COHORT_ELIGIBLE_RANDOM_SAMPLED = NOT_SCORABLE；30_CASE_COVERAGE_RATE = NOT_SCORABLE；已核验30币 = 0；失败取源不能记为30个负例。** 这只是**数据路径初验被阻断**，并非证明未来任何高倍项目不可预测、也非证明所有区块浏览器都不可用。

## 4. 本轮最终执行决定

在当前免费/已连接来源约束下，**首个Source stop已触发**。暂停这条链上30例样本生成和后续预测开发，保留冻结合同与实际失败记录。重新继续的唯一合格条件是先取得一个真实可复现、无需当前结果倒推的历史Factory `PoolCreated`全量事件来源，能审计连续区块、原交易哈希及重建前30个目标代币；否则不再打着“继续”名义只补日志边界。切换另一个公开索引提供商之前，必须检验它是允许连续历史数据及可取SHA/区块凭证的**合法免费方案**，不能要求用户购买API。

原Spot511冻结七日窗口仍保持独立研究对照，不拿它的亏损证明新链上模型也亏损。生产Monster、Frank、Gmail/launchd均不改；`G0 PARTIAL / G4 UNKNOWN / G6 NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`保持。
