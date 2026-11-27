# Mission — BSC重复盈利钱包跟踪：可行性判决、复用边界、产品架构、研发主线（2026-10-19）

状态：DESIGN_PROPOSAL / NOT_A_STRATEGY_FREEZE / NO_NEW_RUNTIME / NO_GO。
原任务入口：Draft PR #40（BSC钱包发现、公开可复制性）；PR #97（449地址活动与盈亏审计）只提供经确认的数据/工具；PR #30（Monster高倍币发现）保持独立，不改任何现行目标/参数。本文是原V1 G0冻结需求的**建议性V2产品设计**，不是未经授权替换已有开发计划、创建第三个生产监控、新分支或已通过独立审查。

## 1. 立即可得的可行性判决

- TECHNICALLY_PLAUSIBLE：BSC钱包签名交易、交易收据、DEX池和区块可作为只读事件取证输入；但公共RPC不一定支持历史eth_getLogs或WS，必须**实测一条可用免费/已有数据源**，不能把存在接口等同部署可用。BNB官方公共节点列表对eth_getLogs禁用，免费Alchemy有窗口/返回截断约束。
- SIGNAL_DELIVERY_NOT_YET_DEMONSTRATED：目前**尚无**真实运行的用户观察器、observer first received UTC、完整性/网络延迟或实时双向报价回执，不能宣称有及时可使用的BUY/跟单提醒。
- ECONOMIC_ALPHA_UNPROVEN：PR #40 最新5钱包4币6历史选定回合中，0/6 verified public observer executable U，0/6能审核后宣布有效G5；原钱包买入之后+60s时已有2/6退出、+300s时3/6退出、+900s时5/6退出。历史重点样本选择偏差严重，不能当自然胜率；旧无公开观察者时戳的回放永远不能补造。
- SECONDARY_ROSTER_NOT_RANK：PR #97 固定449/449已查三链签名变化，237曾有任一查询链签名活动，212对应三链历史窗口没有签名变化；已完成237/237选定链出账首页，不等于237个BSC最近主动DEX买卖；完整钱包30天/长期PnL依旧0/449。原PR97是分批钱包盈亏审计，不能为了本方案改变其目标、删掉原始次序或合并代码仓位。
- DECISION：**值得启动小规模、最短链路的只读观察/报价技术验证；不值得仅凭历史研究投入八周无中途验收的全量开发**。前向研究能测可行性，不能预先承诺盈利。

## 2. 唯一用户目标和验收主链路

用户看到的是：明确的钱包本人在何链、何Token、何时首次被本观察器看到买入 -> 当时是否仍有可安全且双向卖出的真实DEX场所 -> 经过实际采集延迟后手动能否利用 -> 真实不盯事后赢家的费后纸面收益/亏损与失败原因。任何收益金额只是研究场景，**没有用户授权的交易名义本金/仓位**，也不涉及自动交易或买入金额建议。

两个分开、共享底层来源事实的研究目标：
A. WALLET_FOLLOW（原PR #40）：已冻结候选EOA发生新的本人成功买入信号时，衡量观察者可见时点以后的独立可跟表现。
B. EARLY_TOKEN_DISCOVERY（原PR #30）：Token首次可交易、流动性变化、跨DEX/Alpha/合约/Spot身份的早期发现；**不得因为本项目跑通而宣布Monster策略获利或自动接入Frank**。
PR #97仍独立回答用户原始449钱包的近期和长期真实PnL。钱包名单可跨模块**只读引用**，但原23+449不能在不查链、去重、确认近期主动swap及样本选择偏差的情况下直接合成“盈利地址名单”。

必须是端到端完整功能，而非只通过某一审计关口：
准确候选 -> 第一收到的真实事件 -> 当时实际可用DEX双向报价 -> 研究型进入/退出记录 -> 人可读解释和失败原因 -> 同期间对照 -> 样本外评估 -> 决策。
没有任何环节可以把未知替代为0或成功。

## 3. 复用清单与明确禁止复用

| 资产/原位置 | 决策 | 原因和边界 |
| --- | --- | --- |
| PR #97 tools/receipt_probe.py + tests | REUSE_AFTER_PORT_AND_TEST | 收据基础事实取证；需检查HTTP截断、event logs+native内部返款。不可直接当钱包盈利 |
| PR #97 tools/transaction_ledger.py、closed_token_index.py、lineage_gate.py、verify_block_roundtrip.py | REUSE_OFFLINE_FACT_ENGINE | FIFO/库存/来源门禁/原区块复验；无交易所现价、无观察者first_received。跨分支代码必须固定SHA移植，并保留原单测 |
| PR #40 bsc_meme_address_model_v1_p4b_public_observer_ingress_gate.py | REUSE_CONCEPT_AND_FAIL_CLOSED | 观察者时间不许以tx.block.timestamp或事后作者自报代替；必须在真实接收时存不变事件 |
| PR #40 原23 EOA×19 exact CA 和已封存6案例 | HISTORICAL_DIAGNOSTIC_ONLY | 旧数据已曝光且样本事后选择；只验证身份/时间/数量边界，不能训练并再称样本外 |
| PR #97 449源和237签名活跃证据 | CANDIDATE_POOL_ONLY | 未验证BSC主动DEX、近期反复盈利；独立保留449原始索引，不改PR #97 |
| BSC Follow V1历史池数学结果 | SCENARIO_BASELINE_ONLY | 没有真实观察者到达时间、可税后卖出与深度证据，不可标REAL_QUOTE或FILLED |
| Frank Solana解释器/ACC MULT、Monster CEX D0 | ONLY_REFER_IF_SCOPE_EXPANDS | Frank生产独立、不可私自挪用阈值或读写live DB；Monster历史策略未验证正收益；Solana另设协议和资料接入 |
| GMGN受限/需充值API、事后最佳赢家优化、无限补171队列、逐wei重复旧账 | DO_NOT_USE_IN_MAINLINE | 用户拒绝付费路径；无法改进实时发现与可执行收益；原报告只归档，不追着边界反复改 |

## 4. 五层契约与严格时间轴（不得把历史数据冒充实时）

L0 roster：chain_id、EOA、provenance、added_to_observer_at、active_signed_swap_confirmed_at、eligibility、source_hash、roster_version；允许静态候选无评分、不允许从2026当前赢家名单回填已往表现。

L1 raw observation：observer_id、subscription/connection_state、RPC source、raw_block/tx/receipt/log/event hash、source_node_timestamp、**observer_received_at**（实际本机UTC接收）、monotonic_sequence、clock_skew、observed_confirmations、reorg_status、observability_latency；不宣称这是全网络GLOBAL public_first_seen。若为历史数据，字段为HISTORICAL_NO_OBSERVER_RECEIPT，不能补造时间。

L2 normalized wallet event / opportunity identity：wallet、exact CA+chain、signed_tx hash、真实路由swap方向、quote_asset/raw_token/raw_quote、gas、venue/pool、evidence_level、first_seen_monotonic、event_id=(chain,txhash,logindex,monitored_EOA)，**机会episode_id按链/CA/可交易区间/冷却窗口生成，不强制UTC日当作真实独立簇**；相关钱包/关联资金及同池、同币时点在统计时分组，cluster_id只用于有证据的聚合，未经证明不得当同控。

L3 quote/simulation snapshot：真实在observer_received_at后请求，且与同venue pool/block/token/方向一致，存原始返回body SHA、收到UTC、卖出同量假设、池储备或集中流动性、税费/gas与quote有效期；区别LIVE_EXECUTABLE_QUOTE（仍非真实成交）、AMM_MATH_ONLY、SYNTHETIC_STRESS、NO_ROUTE、UNKNOWN。真正FILL_VERIFIED仅限用户实际授权的独立真实订单，当前不能出现。双向可买/卖及router兼容先于盈利讨论。

L4 prospective features / labels：feature_asof <= decision_at，包括钱包过去已**观察到**的成功和失败、累计表现、此前池历史、代币年龄/权限/分布；未来在退出时点观察并单独生成标签，绝不反向写入features。以固定数据冻结版本及之前审查过的候选名单、时间窗、notional_scenario、延迟、进入/退出和退出失败处理运行；历史样本仅做格式回归。

指标固定分母：raw events、true_signed_buys、observer_received/不可见、distinct token episodes、signal_age、真正同池可买+卖/NO_ROUTE/UNKNOWN、最大观察延迟p50/p95、费后纸面净收益及中位/分布、最大回撤/回撤轨迹、单币集中度、对照组分布、代码与源SHA。至少按交易日/CA/关联钱包聚合稳健误差，**30个簇只是最低探索样本，不是显著盈利证明**。

## 5. 公平对照与参数，不让用户背负未经确认的交易金额

- 对照一：**同场所、同日期和类似流动性/代币年龄**的非跟踪钱包触发事件，不能仅随机同Router任意EOA造成样本分布不同。
- 对照二：同一批可交易token在相同时间约束下无钱包打分的机械候选/随机提醒策略，用完全相同报价、手续费、资金占用、退出及缺源规则评价，禁止故意挑无流动性亏币作负例。
- latency以收到事件后0/30/60/300/900s **观察窗口/报价测量**为研究候选，对应实际能否触达与过期判断；最终用于验收的具体一套延迟/优先级/退出方案，必须在新前瞻评估之前单次冻结。别把“主人退出即同步跟卖”视作唯一退出，也测试事前固定的24h和风险退出规则。
- 不默认0.1 BNB是用户授权名义金额；可使用多档明示的**纯研究标准名义量/深度曲线**，在看到真实前向收益标签之前冻结，另保存用户实际仓位UNKNOWN。
- 加入钱包和币种身份二次核对、危险权限和卖出能力评估；只读合约模拟可能不反映MEV和实际上链税费，承认不确定性。

## 6. 完整研发流程：一个模块、五个交付里程碑，不再Stage数量竞赛

| Gate / 时间范围只是研究观察窗 | 要完成的成品 | 准入/结束判据 | 失败时怎么处理 |
| --- | --- | --- | --- |
| F0 架构和事实，立即 | 目标分层、原PR #40/#97代码复用签名、样本选择偏差、数据契约、完整一条候选到可交易的时序demo合同；选BSC为第一试验链 | 总体文档、可测否定条件、固定source/代码，独立审设计核心，不改变旧G0 | 发现目标冲突则修设计一次，不继续补历史23钱包全量 |
| F1 最小外部数据链路，1–3个自然日观测窗 | 现成免费RPC的WS/HTTP连接、真实BSC交易日志和目标钱包本人swap，时间/回执重放、报价买卖两端、一次性CLI只读输出 | 真实>=1可解释成功事件和>=1失败/不可执行原因；旧block time不被说成observer first; free source可达，失败时NO_GO | 若没有真实事件，区分SOURCE_BLOCKED与NO_WALLET_ACTIVITY；不立即写预测模型 |
| F2 7日受控小样本 | 用户**另行授权**后启动独立、有限期限的只读本地前向采集；恢复/去重、重组、UTC漂移与原始字节；明确每条live quote可用性 | 至少有可核对真实本人swap与对应双向DEX quote及其失败分母；能计延迟p50/p95，未能验证进入/退出就拒绝下一阶段 | 7日事件太少记LOW_SIGNAL_DENSITY，不因缺事例宣称0胜率；可以停止或只调整候选来源后*另开新冻结周期* |
| F3 真正前向样本期（仅F2有业务价值才做，约4–8周观察） | 在完全冻结名单、研究notional、延迟与退出规则下，获得独立episode与全部失败; 对照组并行 | >=30独立episode用于探索性比较，至少20有足够双向quote；高度相关只算1簇；<30为INSUFFICIENT_DATA而非算法FAIL | 未到样本下限→按预定上限停止，不不断延长直到凑到漂亮盈利 |
| F4 一次评估与交付 | 同源主组/两类对照费后收益、可实现比例、最差损失、退出/金额敏感性、时间分层；固定SHA独立审核；最小只读本地UI只在批准后 | 完整经济报告、Review、主线PROCEED / FAIL / INSUFFICIENT_EVIDENCE，只有真实稳定正收益与真实可用性同时有证据才有后续产品许可 | FAIL后归档策略，**不能**在同一holdout上不断重调；不要通过调整测试或补边界凑GO |

F1设计验证与F2本机长期运行有不同的用户授权边界：默认只设计/开发离线功能，不创建自动化/后台监控、launchd、schedule或真实通知；即使将来允许只读观察也不自动允许交易。独立AI Review设置在接口/资金模型/来源契约冻结后及上线Gate，非每次低风险文档变更。review提出P0/P1及确定影响结果的P2必须修复；其他缺陷不无限重开同一来源已过审范围。

## 7. 研发规范与禁止再出现的流程

1. **唯一业务看板**，不以commit数、Stage数、SHA复验轮数、首页分页数衡量产品完成度。每次交付固定五项：新增真实可观测买入、可立即双向报价、过期或NO_ROUTE、研究型收益/损失、尚缺哪些源。无新增产品结论则直接报告BLOCKED并转换独立任务。
2. **对外版本固定**：原PR #40主线继续，不另开平行BSC Stage/PR；原PR #97按其449钱包成本亏损分析计划独立跑，必要的共享工具要固定Git SHA移植并跑旧/新双套测试，不改449历史名册、保留两个来源证据。
3. **固定期限单个问题补证**：每例RPC预算可配置并有默认有限值（如12次原证据补查仅针对同一案例），一旦费用/路由/first_seen无法得到即UNRESOLVED，不继续反复让其他AI审查同一小问题；功能主线不因一个钱包被阻断。
4. **价格与利润分级**：OWNER_NATIVE_BALANCE_DELTA_ONLY、OWNER_REALIZED_PNL_VERIFIED、OBSERVER_LIVE_QUOTE、OBSERVER_PAPER_PNL、ACTUAL_TRADE_FILL四类不能互相替代。原钱包盈利 != 跟随者盈利；没有真实下单就不能叫真实fill。
5. **安全门禁**：原PR #40仍Draft、NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE；Frank和Monster生产数据、通知、状态、历史Stage原证据均不修改。任何Mac后台观察、数据传出、通知、研究金额默认都要单独授权。Git仅接受有业务增量的docs、源、代码、测试小批，并先报告已核实SHA和实际CI。
6. **终止优先**：F1证实免费源长期不可获得即SOURCE_BLOCKED；F2即使代码OK但收不到实际及时信号或不能在市场上卖出，停止主策略扩张；F3样本不足则INSUFFICIENT_DATA；样本充足但扣费后不能打败同源对照/依赖单币极端盈利，则REJECT_STRATEGY。不让失败变成无限拉长工程周期。

## 8. 今日边界与下一次执行入口

本文件只交付设计和事实级可行性判决，**未冻结任何可执行交易参数、没有新代码/监控、没有长达8周的自动采集授权、没有外部AI设计审核输出**。已经检查PR #40 HEAD和PR #97 HEAD，不复查旧源以制造新进度。下一次开发前应先完成**F1数据源与真实观察链路的最小能力证明**，然后以具体真实失败与成功标本决定是否投更多时间，保持原模型和研究报告不可改。F1若不能在用户未授权的Mac监控下真实采到事件，只做API探测/离线注入，结果只能是TECNICAL_PROBE_ONLY；不得将它说成真正前向观察。
