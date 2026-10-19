# Monster — 以真实赚钱价值为目标的阶段决策和下一次有证据的验证（2026-10-18）

## 2026-10-19：新方向唯一入口（旧正文冻结归档）

**从本索引提交之后，本文件停止追加新研发方案、Stage报告或单点修复结论。** 下方历史报告、2026-10-19旧总体提议及其源证据保持原文，供审计和回看，不作为当前可执行模型或付费/部署授权。只有以下三个新版对象作为之后Monster早期链上研究设计的入口：

- [MONSTER_EARLY_ARCHITECTURE_CONTRACT_V1.md](MONSTER_EARLY_ARCHITECTURE_CONTRACT_V1.md) — BSC优先、数据源Plan A/B/C、证据归档、可卖出10x、as-of时钟、止损、复用与Phase验收的总体架构；状态`ARCHITECTURE_REVIEW_BASELINE`。
- [schemas/monster_early_records_v1.schema.json](schemas/monster_early_records_v1.schema.json) — tokens、events、eligibility、outcomes四个机器schema。**尚未形成实际P0真实数据/测试通过声明**。
- [adr/ADR-001-research-budget-power-and-decision-governance-20261019.md](adr/ADR-001-research-budget-power-and-decision-governance-20261019.md) — 研究预算零付费（Plan C须用户另行明确授权）、15个10x独立正例仅为必要非充分功效下限、合同变更只走编号ADR。后续变更用新ADR supersede，不在此处继续堆正文。

原 [30例已冻结源探针](MONSTER_EARLY_VENUE_30_PIT_SOURCE_PROBE_BUDGET_AND_STOP_20261019.md) 是P0既有研究边界，不修改其原样本和2026-11-02截止及2次CI预算。**本次只完成架构/数据契约，不意味着用户批准10周自动运行或已经获得可用BSC来源。** `NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`不变。

---



## 当前产品研发总纲（2026-10-19，PROPOSED，不覆盖原历史冻结合同）

**适用范围：仅 Monster 妖币早期发现 PR #30，不是 BSC 钱包跟单 PR #40，也不是449钱包资产审计 PR #97。** 这段是用户转交Claude十周重设计方案后的项目级可行性、复用和门禁审查；目的是先统一整个产品，不先动代码、合并、Mac安装、通知、定时或交易。待用户明确接受后才能把它变更为新的正式Phase参数冻结。其余本文现存历史原文、已冻结样本、审核结论和2025-07-01 Base覆盖探针**保持不变**。

### 产品目的与三项分立可行性判断

- **产品目的**：在代币的首次真实可交易窗口，以当时公众可取得的链上、场所、合约权限和资金分布证据，对所有符合事前PIT准入的项目排序，发现未来可能出现5x/10x而且有真实卖出机会的少数代币；不是事后挑出赢家、不是保证发现每个10x、更不是把旧CEX的WATCH数量做高。
- **SOURCE_FEASIBLE_CONDITIONAL**：EVM官方链事件理论上可重建部署/池/Swap，但免费公网历史RPC `eth_getLogs`、存档节点完整性、Binance Alpha历史上架/下架档案、V3历史状态和死币覆盖**并未验证**。BNB Chain官方文档公开说明列出的mainnet公共RPC禁用eth_getLogs；已连Alchemy Base免费实测2000块拒绝、每次10块。Mac公网有网本身不能证明BSC完整历史日志可取。须按原30例探针先拿出真实数据路径，不强行开六个月采集。
- **EARLY_SIGNAL_UNKNOWN**：暂无新策略对未来10x可成交项目的样本外分离力证据，先验不承诺精确率、频率或期待回报。若独立正例太少，结果`INSUFFICIENT_POSITIVE_EVENTS`而不是虚称lift显著通过/失败。
- **EXECUTABLE_RETURN_UNPROVEN**：Stage30/162及初期518轮各自历史不同假设的代理账本表现负面，仅能证伪旧规则在那些假设下的有利性，不能证明所有新链上策略必败。必须把最高价格/池瞬时math/真实双向容量、手续费与实际fill严格分级。

### 产品架构（集中到一个早期研究包，不再新增Stage一次性脚本）

架构建议（**未创建目录/代码**）：`crypto-300-profit-mission/local-agent/mission_agent/early/`下包含`source/`(EVM及后续Solana/官方CEX/Alpha档案）、`identity/`(chain+CA/venue+product，跨链project_id仅证实后匹配)、`lifecycle/`(事件与PIT可用时间)、`eligibility/`(首次真实流动性与双向卖出可行性)、`features/`(as-of因果特征)、`labels/`(延迟出场价格/5x/10x/归零/删失)、`evaluation/`(分时段验证/随机/CEX对照)、`ledger/`(资金/手续费/容量/损失)，一个`cli.py`含`probe-source`, `build-cohort`, `label`, `evaluate`, `report`。先做最薄source+schema，不预建全部空包，不复制186个旧workflows；若需CI最多一个新研究workflow，旧workflow仅归档、不擅自删除或重新触发。

**身份和因果时间**：基础键`chain_id|token_ca`；场所另有`venue|pool_address|product|official_instrument`。一个代币可多池/多费档/多报价币/代理桥接；同名ticker不得当CA。独立事件按原`block|tx|log_index`或当时已发布官方公告及source-hash确定；所有`observed_at`、`available_at`、`source_hash`、`evidence_grade`要区分历史区块时钟与当时第三方真的已能读到信息。不能用2026已知上市结果认定此前必能看到Alpha公告。基础生命周期是`DEPLOYED → POOL_CREATED → REAL_LIQUIDITY_AND_BUY_SELL_PATH → [ALPHA/USDM/SPOT] → 30D/90D_OUTCOME`；事件可能缺失、乱序或从未发生，不应强制要求所有项目最终上市。

**双层母体**：第一层全集为跨预冻结BSC Pancake V2/V3(必要时含launchpad)连续事件得到的所有CA/原池事件，含0流动性、rug、死币、无法再查询的合约与完整源缺失计数。第二层是**实时实际首次满足并已可观察**事前最低流动性+买卖两侧成交能力的交易可评资格，`T_entry = max(条件真正达到的区块可用时点, 首次可查询时点)`；绝不可在T_pool+1min使用未来一小时累计50笔Swap。未合格/来源缺失的必须保留第一层分母，分别`INELIGIBLE_AT_T` / `NOT_SCORABLE`，不能过滤出幸存币后再分胜负。

**保留原冻结门槛**：现有Base30例探针、24/30部署+池、18/30流动性+双向可模拟的覆盖终止条件，以及Base0.5 WETH/1000 USDC、BSC2 WBNB/1000 USDT研究前置额度是已记载的现行版本。Claude新建议的`20 BNB + 首小时50 swap`**只是候选V2大流动性分层，不自动替换**，因为会直接降低发现更早、更小币的能力及产生一小时lookahead。正式规模/额度按源覆盖验证并在读取未来收益标签前提交独立参数变更。

**标签分层**：主标签可选`T_entry`后90天中首次出现、可以事先冻结的标准名义金额**卖出**的净可得10x（`SELLABLE_10X`），5x和30天是辅助标签；观察时间必须完整跨越90天。最高OHLC、高薄池末笔价格、CEX 1m最高价只能列`THEORETICAL_MAX`，不算可卖出10x。实际交易性价比需同一可观察场所/当时可得历史储备或集中流动性/税/手续费/Gas/容量/先买后卖/退出失败；单侧PoolCreated/单点Reserve不足则`NOT_SCORABLE`或`AMM_MATH_ONLY`，绝不晋升`VERIFIED_FILL`。死亡、迁池、下架、不可退出、未满90天是不同结局或删失，不能全部标成0盈利。

**模型目标分开**：一为全新币中高倍且可卖出项目的识别能力（base rate、precision@k、recall、PR/Top-decile lift与置信区间、每天候选个数）；二为给定冻结资金/仓位/假设手续费/进入观察延迟/明确退出规则的费后**纸面**净收益、最大回撤、无法成交比率和单币收益集中度。高10x标签并不等于成功卖在最高点。比较必须同一PIT母体、同样资金与成本规则的随机基线；旧CEX动量只作另一可比时间/场所的辅助基线，若其上市时点更晚、无共同可买窗口则不能简单作同一个分类器准确率比较。

### 旧仓库代码迁移等级（先迁最少必要功能，不重复审核已封存旧脚本）

| 已有项目/代码 | 处理 | 证据边界 |
| --- | --- | --- |
| 原source SHA、PIT、G0–G6、不可推导则UNKNOWN | KEEP_AS_CONTRACT | 直接沿用不可变原始来源及时间可用性规范 |
| `monster_v4_stage166_spot511_official_1m_intake.py`和`monster_v4_forward_spot511_official_publisher_acquire.py` | ADAPTER_AFTER_EQUIVALENCE_TEST | 已有官方ZIP/CHECKSUM校验作为后期CEX价路或回放对照；非Alpha首次可交易时间/DEX初池证据 |
| `monster_v4_stage139_official_t0_and_saved_contractinfo_evidence.py`和`monster_v4_stage120_exchangeinfo_execution_rules.py` | SELECT_FUNCTIONS_ONLY | 原偏USD-M合约元数据/ASOF；对Alpha公告或DEX税费不直接适用 |
| `monster_v4_mainline_preclosed_300u_cash_ledger.py` | EXTRACT_ECONOMIC_ACCOUNTING_ONLY | 原程序写死300U/30U/10槽、老代理价格与来源；只能移植资金守恒/并发占用/损失记法，不移植实验金额和历史回报 |
| `monster_v4_shadow.py`观察函数和Stage30/162/518证据 | FROZEN_CEX_BASELINE_ONLY | 旧动量WATCH/SETUP、FIFO8、队列/TTL仅适合旧CEX，不进入早期DEX筛选核心 |
| Frank `rpc.py`/`parser.py`/`store.py` | READ_AND_ADAPT_LATER | 当前是Frank生产相关专用解析/库；Solana另需Raydium/pump.fun具体Program事件测试；不能直接把Frank部署/DB接入新研究 |
| 旧Stage一次性脚本和186个workflow | ARCHIVE_IN_PLACE | 不删除过去已审批证据或触发原CI，除正式确认某个模块需要代码等价迁移，否则不做批量审计、修边界或重构 |
| 当前已提交的Mac Factory RPC roster probe | SOURCE_SPIKE_NOT_PRODUCT_MODULE | 尚无实际Mac全天可重复覆盖的证据；首30 Base是源测试，不代表BSC Alpha样本母体 |

### 十周研发提议（总时间盒需用户确认；每阶段一次决定，不开放尾随Stage膨胀）

| Gate / 建议相对周次 | 真正交付 | 放行/停止（未真实通过前不可假报） |
| --- | --- | --- |
| P0，第1周，数据源可用性+设计冻结 | 统一源码版本、BSC V2/V3实际Factory、3个跨不同月份日期及负例的完整事件访问试探、Base30覆盖探针、solana后置价值判断；FROZEN cohort selector/schema/PIT/来源预算 | **SOURCE_BLOCKED**：若不能免费、可复验地取得连续历史原日志或足量实际退出证据，则停止模型/大规模迁移；沿用原Base30探针11-02截止，不为通过门槛伪造样本 |
| P1，第2–4周，BSC历史母体+首可交易 | 预冻结区间真实独立币CA全集（含死币/未上架）、创建/首次注入/首可买卖及Alpha/USDM/Spot资料覆盖度、缺失分母；较长2025上半年档案**仅在源路径真实可用后**才扩展 | 先达到原小探针24/30+18/30硬门槛，再评估是否可建立至少500例具备必要标签与独立负例的母体；500只是探索最低量，10x独立正例太少不能论分离力；失败停止，不缩小到已知热币 |
| P2，第5–7周，1个可解释轻量策略 | 仅用`available_at <= T_entry`信息建立冻结特征表；跨日期训练/内部验证fold的5x/10x precision、lift/PR、源可评比、隐形成本；同时保留同条件随机以及原CEX动量对照 | 在查看最终holdout之前冻结唯一策略及结构；可讨论预注册top-decile lift 3x但应考虑正例数、区间不确定度和每月样本，若统计功效不足明确`INSUFFICIENT_POSITIVES`，不能拿3个赢家承诺显著有效 |
| P3，第8–9周，一次历史holdout +经济 | 对明确未用于训练/阈值重选的时间分割，仅一次预注册评估：同期间无差别随机、相同执行名义额/税费/仓位锁定/退出规则，与CEX旧动量可比区间报告分开；必须有双向历史价格容量 | 若费后纸面净收益不优于同口径随机或<=0、严重集中单币、退出证据不足 -> `REJECT/UNRESOLVED`；旧已曝光2025–26不自动称真正前向，绝不可改holdout重考 |
| P4，第10周，业务判决 | 一个机器结果+一份用户可读报告，核心数据/单币贡献/真实不可卖比例、来源成本、未来shadow需要的连续数据能力，必要的独立其他AI核心结论审阅 | `RESEARCH_SUPPORTS_FURTHER_FORWARD_TEST` / `REJECT_STRATEGY` / `INSUFFICIENT_EVIDENCE` 三选一；即使好也**不是**自动生产GO或利润可复现保证 |

**90天成熟延迟不能压缩**：上述10周（若自2026-10-19计算至2026-12-28）最多对2026-07-19以前进入的历史项目得到完整90日结果；随后新开始的真实前向项目必须到各自T_entry+90日才可打90天标签。使用过去已经曝光的多个大赢家的历史holdout只能称`RETROSPECTIVE_TIME_SPLIT`，不能自称`UNTOUCHED_PROSPECTIVE`。当未来成熟数据不足时报告删失并等明确批准新一期研究，不能为了十周结项偷改为“最高已出现10×”。

### 最少且明确的开发/Review规则

1. **用户价值优先**：每期报告样本CA/可买卖T_entry、来源实际覆盖、5x/10x真实可卖出、入场/退出及费后资金、误报/丢币/死亡、负向、集中度。没有这些的单点代码审计不计主线进度。
2. **只改一个包、一个CLI、一套小回归CI**，源码模块需要迁移时固定Git SHA并做迁移前后等价测试；只有真正重复用到时才抽成包，不为漂亮架构先重写旧库。每Phase一份合同及一份结论，bug记录在commit，不新增Stage文档/逐次审查工作流。
3. **评审分层**：P0来源和PIT冻结需一次针对“无法获得数据或泄漏”的设计评审；探索期普通小改只跑确定性测试；到P2参数冻结和P3经济结论各做必要的独立核心审核，避免每个单点Review循环；不取消仓库要求的交易/发布前独立审核、真实测试、本机只读实测、修复和复验。
4. **硬截止与失败定义**：来源不行`SOURCE_BLOCKED`，母体/正例不足`INSUFFICIENT_DATA`，排除未来泄漏后分离力不显著`NO_DEMONSTRATED_LIFT`，费用后不优于一致随机基线`REJECT_STRATEGY`；都不是`GO`；不因连续数周负面结论去改同一个冻结holdout。
5. **不授权自动行为**：本段未改变原`G0 PARTIAL / G4 UNKNOWN / G6 NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`，不批准Alpha/DEX定时监控、Mac launchd、Frank改动、用户资金、电子邮件或真实订单。原已冻结Spot511七日前瞻比较和原Base30探针原截止/CI次数单独保留，不跨研究混算。

---



## 结论先行

**研究源与代码审计走到这一步，下一次优化不应继续提高历史首评数量，也不应再反复审核已被APPROVE的V3静态报价处理。关键业务障碍是 `WATCH → 可使用的 SETUP → 真正可成交的正收益` 整条链未获验证，且现有历史经济证据显示较强负面风险。**

- **已有研究级完成的项目**：Stage162同8槽排队机制（研究/Code独立APPROVE）与Stage163 V3官方原字节离线报价来源分类、时钟桥及异常盘口审计（独立Codex APPROVE固定证据SHA `15edf022d8b99071701357dfd51d7534f3470409`）；它们并非交易策略/上线批准。
- **今日具体决定**：不将 Fair8 视为已证明能产生更多可交易机会的功能升级；不再为了原445源的某个边界或静态报价单点差价重复自优化，不额外制造未经验证的“更好利润”推送。保留已获批研究代码、测试和归档，待新同场所前瞻机会闭环证据成熟后再决策是否改变正式核心策略。
- **当前用户状态**：没有资格标记某代币`BUY`或“现在还能追”；无现时连续Spot WATCH采集/真实Mac通知，不构成现时观察界面。所有真实交易费率/名义金额、Spot历史/前向同一信号入场和预定退出双边盘口及真实成交未知。`G4 UNKNOWN / G6 NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。

## 可复验源与各自业务含义（严禁跨群体混算）

| 证据及原Git Blob | 真实研究事实 | 对实际用户价值的解释 |
| --- | --- | --- |
| Stage162 Feb445 A/B，`monster_feb445_stage162_fair8_ab_real_v4_actual.json` Blob `76dd05127bf42f01df784c880bda2819006a6d4c` | 同源 WATCH=269、FIFO8和Fair8同753选槽、总SETUP均120；Fair8多27人首次完整5m评价，**新增SETUP=0、丢失SETUP=0**。高峰98币中的评价7→32、最终LATE91→66，但高峰SETUP 0→0 | **只证实减少无法首次评价的历史排队漏处理；没有证实新增可交易机会或盈利**。Fair8不得自动升级生产推荐/改变实盘。 |
| Stage30六历史日期，`monster_stage30_six_new_dates_758x6_real_profit_and_GT_AUDITED_20261011.json` Blob `9b73bb711ed498192c1407286eb2304538876344` | 758×6=4548符号日期尝试，其中2514有连续168h；WATCH760，24h一次性价代理可评价430，赢133亏297（胜率133/430=30.93%），250同币资金重叠，80来源不可评价。历史300U/10槽每笔30U、未知退出本金**乐观全额返还**且20bps单边滑点情景下，选289、资金不足跳过190、槽满跳过31，**乐观资金账本仍净−79.489406U**（最终220.510594U） | **早报33个历史2×中的30个不代表能赚钱**；资金锁定、盈亏不对称、币种缺源及卖出价决定是否实用。历史30U是实验假设，不是用户授权金额；旧已曝光回测不能作为新OOS。 |
| Stage152完全不同305 D1研究，`monster_stage152_original305_integrity_and_economics_summary.json` Blob `518e7aa0d8db83fd1b818513ae7e72b165252806` | 305中回调恢复确认184、无回调113、回调未恢复8；仅184确认样本，24h价格+示例费率代理中位 **−2.835719643955325%**，6h中位 **−2.158127071095925%**。184样本且不把未入场121个计入0盈利。 | 一个D1“确认”并不等于正收益或真实交易；此群体与Stage162及Stage30非同日非同事件，**不合并计算投资胜率或本金盈亏**。 |
| Stage163仅一次旧官方Spot时间锚，`monster_stage163_spot_post_t0_original511_quote_friction_v3_clock_actual.json` Blob `f87ea5342642055af4e8ea8f15dd4efa76e1eb7d` | T0档案511个USDT +TRADING+允许Spot对；BBO实收在T0之后、跨客户端/交易所时钟存在不确定性；旧盘口价差中位11.217050bps，双向正价量511，但**无真实随后退出盘口、交易授权费率或填单回执** | 静态单点价差是市场摩擦特征，不是同一个WATCH当时可成交quote，更不能给Stage30/152历史回填成交价格。已获批的是来源/分类研究而非G4。 |

## 针对用户真要用的产品，下一轮只接受三类新证据

**A. 真正提前、真正有转化**：在相同Binance Spot、时间冻结且未用于模型调参的新窗口，报告**完整人口（至少511个正式T0当时 eligible；后续新增币单列与source缺失分类）**、3m×3360轮的原WATCH、首次有效5m评价、15分钟TTL、过期、SETUP event-key。对Fair8与FIFO8进行同源固定策略配对：原SETUP保留数、新增/损失SETUP、从触发到首次有效观察的延迟、尾部爆发漏报率和源删失。若又是首评+但新增SETUP=0，则明确 **RESEARCH_ONLY / NO_PRODUCT_LIFT**，不发布“优化成功”。

**B. 用户能否在发现之后操作**：每个报告称“可考虑跟进”的候选至少保存当时交易所身份/USDT Spot资格、原始双向bid/ask更新时间或带误差回执、实际当时可获得的完整可成交深度与交易规则、用户明确研究订单名义金额/手续费或只做多个显式成本情景；另外给定的**预先冻结退出时点**双向盘口与不可成交/过期记录。没有同时匹配入场与退出的真实盘口、手续费/滑点证据就`EXECUTABLE_NET_PNL_UNKNOWN`，不得把OHLC最高最低价与过去的T0+几秒快照当买卖成交。

**C. 产品页面极简且不能错报**：真实数据合格时，只保留 `币种/venue`、`发现UTC和年龄`、`WATCH/SETUP/EXPIRED`、`原始触发理由`、`独立有经验钱包方向(若有已核链上源)`、`可跟进证据或缺口`、`具体阻断与最后源时间`；没有新数据/过去15m或quote陈旧则应默认 `观察/不可跟进`。开发已存在的`monster_v4_opportunity_snapshot.py`只读SQLite查询链路用于此输出的基本合同，但其尚无真实Mac部署，不应现在另起漂亮但不可用的研究后台或新交易机器人。

## 真实新样本的时间/来源约束和一个实际停止条件

冻结窗口 `[2026-10-17T22:06Z,2026-10-24T22:06Z)`（曼谷10月18日05:06至25日05:06）截止2026-10-18尚未完整；需要覆盖官方Binance Spot 2026-10-16至10-24已发布的全部1m日ZIP及官方Publisher校验，**发布和SHA都实际拿到以后**才能做历史分钟价代理FIFO8/Fair8。同源1m封闭bar虽能做日期割裂的因果价格代理，但没有当时ticker24/完整listing变化/同一事件L2和实际送达，会标 `OFFICIAL_1M_CAUSAL_PROXY_STRESS`，不能装成完整PIT 7日可执行收益。**历史已曝光Feb445不可因为评审成功而变成未来样本。**

正式商业下一推进原则：
1. **不更改被锁定D0/D1阈值，不重选历史获利代币，不再围绕0.001ms或静态T0问审核者重复兜圈**。
2. 先完整拿到现有官方可用原始前瞻分钟源，按真实源码演练一条完整 WATCH→D1→SETUP/EXPIRED→D2/证据不充分的标准回执，独立区分`已采集`/`缺数据`/`未到发布日期`。
3. 新样本若无法证明**新增有效SETUP**或确认 **真实正收益与完整可交易证据**，接受负结论而不是继续逐个边界调试；真正要转成生产通知/交易前另需独立审核、Mac实测授权和连续shadow验证。

**当前硬门禁不变：** `G4 UNKNOWN / G6 NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`，不主动复活Stage99/Frank、Gmail、自动监控、自动交易。无需用户上传资金/密钥。Stage163源码审计APPROVE与盈利依旧失败或UNKNOWN是两个独立层级，保持分开记录。

## 2026-10-19 产品目标纠偏：停止将 CEX 动量阈值微调作为主要盈利研究

**经过用户转交的Claude主线反思后正式纠偏。** 原来的Binance Spot / USD-M动量D0会在价格已经波动后发现币，无法覆盖同币在DEX首池、Binance Alpha前期或期货上新以前的可交易窗口。原用户目标是尽早识别存在真实净收益可能性的早期大倍数机会，而非得到更多可重放的WATCH或审核APPROVE。此前研发过分投入来源SHA、边界修复、旧模型审阅，是研发优先级错误。

**已核实的停止依据：** Stage30六历史日期 760 WATCH，仅430可评价24h价代理（133盈297亏）、中位-5.638822%、固定300U有限资金乐观返本账本亏79.489406U；Stage162 Feb445 原269 WATCH/120 SETUP的固定300U乐观返本账本分别亏85.59U/73.19U；前瞻第一518轮8 WATCH/8 SETUP的15/60/360分钟净价格代理中位均负。这些是不同冻结人群，不能合并一个“胜率”，也不证明每个未来行情必败。但原CEX动量策略 **PROFITABLE_BUY_THESIS_NOT_SUPPORTED / NO_GO**，不再在已暴露人群上追逐盈利参数或只为了提高首评增设Stage。

**保留有效工程，不冒充盈利：** Codex对固定SHA 94f15a318d6a2a02d6da9e05e54b0c5a75ead79e的APPROVE仅说明1533份官方原档、518轮D0/D1、8+8经济研究及运营查询可独立复现。保留原CEX D0作为异常发现基准，不再当主盈利预测器；旧Spot511七日前瞻样本仍严格保持冻结规则作对照。D2证据核查器已有源码，但历史/前瞻真实同刻买卖盘口尚缺。不得让单次代码审查扩大为盈利或Mac投递资格。

**必须纠正“合约数据一行没有”的绝对说法：** Stage57/58已经核查MYX/AIA/COAI的官方期货及Alpha交易渠道，单用同名Binance普通Spot会漏掉全部三项重大历史机会。Stage75/76还证明H/PIPPIN/TANSSI/TRADOOR等期货原D0以前已有Alpha公告，有部分官方CA。USD-M期货量价和Stage90 D2合约数据证据审计也存在；但是Monster确实没有把链上合约部署、DEX首池/真实Swap、持币结构、流动性迁移与Alpha、CEX PIT上线组成可独立测试的“早期发现且可成交”信号模型。

**新研究先标签和源，再决定是否写策略：**
1. 定义chainId+token CA+venue+product的同一项目身份映射，冻结可验证的部署、首次有流动性可买卖DEX池、Alpha第一次真实上线/公告、USD-M交易开通和Spot交易开通时间。所有event都记录当时信息首次公开/链上块高、获得时间与source hash；不把事后信息提前。
2. 先做12–18个月能覆盖普通币的大样本母体，而不是从未来赢家名单倒推。纳入以后>=10x、>=5x、普通拉升、零流动性或亏损/归零、来源缺失；定义各交易场所独立的入场价/退出流动性，不把Futures high或第一笔极薄DEX spike当成能兑现的10x。缺可用PIT则NOT_SCORABLE。
3. 仅用已曝光MYX/AIA/COAI、H/PIPPIN/TANSSI/TRADOOR作早期交易渠道是否存在的功能案例，同时抽同场所未大涨普通负例，禁止将这几币回测充当OOS。链上RPC/真实池建立和Swap、holder/权限风险，Alpha历史公告、当时USD-M的OI/funding（这是期货合约而非智能合约）分开取证，均不可将当前状态回填为历史特征。
4. 在能证明覆盖、时间因果和普通负例后，预注册一个小策略和未曝光时间段，对首个真实可交易窗口开始的高倍机会召回率、日均误报、通知提前量、同时仓位、费后可退出净收益、回撤作比较。若没有真实两侧价格/交易限额和退出事实，真实利润保留UNKNOWN。
5. 两个明确停止条件：数据无法建立兼有普通币/赢家的时点可交易母体时，停止模型编码而先补最小来源；独立新时间段不能产生可核实的净收益增益时，放弃该规则，不许因为已审核代码多就继续追逐Stage数字。

**研发优先级调整：** 已失败CEX动量策略归档保留发现基线；下一主要任务仅研究跨场所早期生命周期标签与原始可观测来源；随后再决定是否新建最小策略。新标签研究不自动授权Alpha/DEX生产监控、订单、定时工作流、Frank改动或Gmail。原G0 PARTIAL / G4 UNKNOWN / G6 NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE保持不变。原七日10月17至24日研究需等相应官方历史源实际发布，不因方向纠偏回填未来收益。

## 2026-10-19 30例源覆盖探针首次执行结果：SOURCE_STOP_ACTIVATED

为避免继续先造策略再找数据，按照本文件“先母体+标签再模型”的顺序，独立预冻结了[30例PIT覆盖度探针的选择机制、五时点、两个停止条件、预算和实际源失败记录](MONSTER_EARLY_VENUE_30_PIT_SOURCE_PROBE_BUDGET_AND_STOP_20261019.md)。首次工厂来源固定为Base(8453) UniswapV3官方Factory 2025-07-01 00:00至次日00:00 UTC，在完整原始PoolCreated事件按区块/交易/日志顺序抽首30个互异CA；并明确跨场所无上市≠源缺失、创建池≠真实Swap、当前存活列表不能替代历史母体。覆盖门槛：30完整保留、至少24/30真实部署+池PIT、至少18/30当时真实流动性和双向可模拟交易证据；最多2次一次性研究CI/到2026-11-02截止，不成立则停止模型。

**真实尝试发现源阻断：** 已连接Blockscout明确不支持BSC chain 56，Base历史factory交易API返回PRO 402额度耗尽；免费Alchemy虽然能查Base历史区块，但事件日志每次最多10区块，首次五段随机稀疏10区块在factory均无事件，不能凑足全日按序PoolCreated母体。当前公开HTTPS容器DNS不可用。不买付费额度、不改挑热门币、不虚构30个。**实际30样本尚未形成，不能写“0/30覆盖率”**，按预冻结第一Source-stop判`COHORT_NOT_FORMED_SOURCE_BLOCKED`，本分支不启动预测器/生产采集任务；除非以后先有可复现的免费全量历史PoolCreated母体证据。旧Spot511七日及此前独立APPROVE继续作为独立研究事实，不因这项新路线阻断改变交易/部署门禁。

## 2026-10-19 后续纠偏：改为本地前台公共RPC试探，纠正“Source Stop”的范围

原2026-10-19 `COHORT_NOT_FORMED_SOURCE_BLOCKED`结论**仅针对本会话受限连接器及容器直接外网环境**，并非链上历史Pool数据不存在或整项研究永久停止。完整来源停止条件仍在，**正式30例母体目前为0、覆盖率NOT_SCORABLE**。用户转交Claude审核指出Mac本机可按公开RPC原生`eth_getLogs`直接查全区块历史；本轮因此交付同分支 **仅前台手动执行、只读、无密钥**的`local-agent/scripts/monster_early_venue_factory_rpc_roster_probe.py`及6项离线测试。按用户授权之前，脚本未在其Mac运行，不启动任何后台或定时服务，不假定公网端点实际支持历史日志。

本轮真实外部核查显示：已连接Alchemy Base免费应用2,000块`eth_getLogs` **明确拒绝且提示上限10块**；BNB Chain官方2026-08-19文档公开说明列出的BSC公用RPC**禁用`eth_getLogs`**，所以Claude举出的BSC默认节点不能不经探针直接假定成功。Base官方公共RPC支持只读接口但限速，亦不能保证给出全日历史原日志。新程序先`--mode probe`分别试2000/10块，之后**只有供应商真正支持时**才应显式`--mode scan`连续历史源；分段SHA存Mac私有目录、可续跑、有请求次数上限，缺块/拒绝就`NOT_SCORABLE`不凑30币。脚本初版只支持Base V3与BSC V2原Factory技术探针，**真正Binance Alpha高倍项目母体BSC和Solana更重要，Solana须另用Program原交易链做独立数据路由试验**。

正式交易准入先锁只用当时数据的首次1h真实池中Mint/Swap/报价侧最小流动性（Base 0.5 WETH或1000 USDC、BSC 2 WBNB或1000 USDT），仅是未来母体粗准入**并非用户下单金额、实际D2可成交门槛或链间等额**；已归零/不足准入/缺历史原字节的案例保留分母，不因未来赢家调准入X。具体新冻结章节、测试与审核边界见[30例PIT探针](MONSTER_EARLY_VENUE_30_PIT_SOURCE_PROBE_BUDGET_AND_STOP_20261019.md)，新脚本代码范围的其他AI独立审核提示词已写在[审查包](MONSTER_MAC_PUBLIC_RPC_PIT_PROBE_CODEX_REVIEW_REQUEST_20261019.md)，尚未取得其他AI审核结果。最多2次真正来源CI及2026-11-02截止规则不变，**这轮不启动GHA CI、不计入历史样本30个、不改旧CEX/Frank/通知/交易及门禁**。

