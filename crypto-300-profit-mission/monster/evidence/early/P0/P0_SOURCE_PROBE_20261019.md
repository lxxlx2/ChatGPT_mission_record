# Monster P0 — 免费历史源实测：BSC V2工厂存储枚举方案（2026-10-19）


## 2026-10-20 固定SHA本机验收回执：归档重放已通过（P0业务门槛未通过）

2026-10-20用户回传第二轮**实际Mac终端输出**：`git pull --ff-only`成功、`git rev-parse HEAD=c1cf218093b2ca9a99a90037dd20ee4b6d83527e`；原PIT测试**12/12 PASS**，新增原始归档验证器所在测试**14/14 PASS**，合计**26/26 PASS**。已有私有归档离线执行`--mode audit`得到：

| 实际离线审计输出字段 | 本机回执 | 可以得出的结论 |
|---|---|---|
| `status` | `LOCAL_FROZEN_30_CREATION_REPLAY_PASS` | 固定30样本的建池证据与本地存档成功重放；仅限Pancake V2这一Factory |
| `fully_replayed_creation_count` | 30 | 30个冻结身份全部有相容的Factory创建原响应 |
| `same_tx_initial_lp_count` | 25 | 同建池交易LP初次Sync/Mint存在 |
| `created_without_same_tx_initial_lp` | 5 | 这5个必须继续留在分母，并非样本剔除或证明永远无LP |
| `original_response_files_audited` | 88 | 本地原始JSON-RPC响应字节在运行时被重读并计算SHA；本对话**未接触**原始字节及其完整manifest |
| `unknown_ranks` | [] | 当前本地建池重放程序没有未解析身份；不能推导出所有样本已可买卖 |
| `twentyfour_of_thirty_complete_pit_gate` | `NOT_SCORABLE` | 代币**部署首时点**与公众可用时点仍未完成 |
| `eighteen_of_thirty_sellable_gate` | `NOT_SCORABLE` | 原买入后代币真实转账/税/授权/双向滑点/出售不能由Factory日志推出 |

回执归属`USER_PASTED_MAC_TERMINAL_STDOUT`。该CLI依其代码不发RPC进行离线审计；但**不能把当次重算的SHA冒充采集当时独立提供商签发哈希，也不能将30/30原建池身份称作30/30全PIT可交易**。前次新审计代码`NOT_RUN`状态现已由用户本机26/26实际测试替代。保留`P0_PARTIAL / G4_UNKNOWN / G6_NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。

**主线下一步**：不再请求用户重复生成30样本或重发1471次RPC。按同一冻结30排名优先从已存`*.later.rpc.json`和冻结历史Sync/Swap证据确定每币在当时是否发生可判方向的真实Token→报价币Swap、是否有可重放的储备/转账/税费来源；不以`getAmountsOut`无税数学结果冒充真实可卖。随后才针对仍缺历史读取的部署交易、不可在本地归档中验证的卖出限制进行**最少量有界免费只读外部查证**。P0覆盖门槛满足前不建预测器、不读事后赢家和30/90天价格标签。

---

## 2026-10-20 用户Mac前台实际来源调用及离线归档验收入口

**用户在本对话直接粘贴实际Mac终端输出**：新Git clone后两组已有离线测试分别12/12 PASS，总共24/24；BSC V2 UTC 2025-07-01历史Factory枚举实得**785个当日新池**、检查前34池并复得冻结**30个CA**，枚举共162个RPC调用。之后六批（排名1–5、6–10、11–15、16–20、21–25、26–30）实际read-only bootstrap回执依次报**5、5、4、2、5、4**个同建池交易Mint/Sync，共**25/30**，六批合计**1309**个RPC调用，加枚举总**1471**个RPC调用。与之前30冻结样本的25/30创建同Tx事实一致。原始Mac终端流已记录在同一JSON中的`bsc_v2_p0_user_mac_local_run_20261020`，来源分类为`USER_PASTED_MAC_TERMINAL_STDOUT`，不可冒充本会话远程读取Mac文件或第二来源的独立审核。用户Mac当次具体Git SHA、原始文件字节与SHA尚未由本会话回读，仍然不能将24/30部署/PIT或18/30真实双向可卖门槛升级为PASS。

**发现并修复一个真实可用性问题**：旧CLI每批会覆盖同一`v2_bootstrap_status.json`，因此六批的状态文件只留最后一批。按Factory index分开的原JSON RPC文件不会因这个状态文件覆盖而直接丢失。现有CLI在保留历史兼容`v2_bootstrap_status.json`的同时，新增不覆盖的`v2_bootstrap_rank_<first>_<last>.json`，供**今后执行**保留各批摘要；此次用户已经完成的六批不会被追溯伪造为具有六份状态文件。

**离线原字节验证入口已写现有CLI**：`--chain bsc-v2 --day 2025-07-01 --mode audit --out-dir ~/monster-p0-readonly-raw`，只读取既有Mac私有目录，不连接RPC、不读钱包、不交易，按已冻结30身份重放每例Factory创建证据及同交易Mint/Sync，对原始已存JSON结果计算SHA256并核对之前单独保存在本地的三份ABI响应SHA；结果落在原目录`bsc-v2-2025-07-01/v2_p0_offline_audit_status.json`，以明确`prior_independent_response_sha256=null`区分审计时重算的哈希与取得时独立回执。缺文件、越范围、内容与历史冻结事实不一致均为`NOT_SCORABLE`。未尝试宣称HTTP headers、独立提供商、公众接收时点、延迟LP全部验收、税/黑名单或真实买卖通过。

**状态分级**：上面24/24测试成功只针对**用户已经运行的旧checkout**；本轮新加的离线`audit`与保留批次文件相关测试已写Git，**新固定HEAD在Mac/CI实际运行仍NOT_DONE**。建议下一步单次本机重新运行此两组单测与离线`audit`，无需重复发1471个RPC请求或再次下载已取得的历史原始资料。保留`P0_PARTIAL/G4_UNKNOWN/G6_NO_GO/NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`。

---

## 2026-10-20 P0 增量核算：首次LP储备覆盖与连续AMM数学参考（仅研究）

本次按冻结的30个BSC V2身份逐项回读同份P0 JSON中事先固定的历史Mint/Sync源，并添加`bsc_v2_p0_reference_sequential_amm_20261020`机器节。**30/30保留在分母，27/30能够从本仓库已存的历史正规化事件重建两资产储备向量**：25个建池同交易LP，加上#14与#26两个延迟首次LP时点的完整Sync。#16/#17仍受连接器完整同块响应截断影响；#18截至7月1日末无Sync，尚余3个储备向量UNKNOWN。**27/30仅是已存事件的数学输入覆盖，绝不能升级为24/30完整部署/PIT或18/30历史真实可交易通过。**

发现原四次Router静态反向报价是对*未改变*的池储备重复读取；它不能代表先买后卖的真实连续价格。新纯函数`v2_reference_sequential_roundtrip`按同一事件储备、买入后池储备更新、每笔0.25% AMM费率计算**完全条件性的无税AMM参考值**，保持无税假定与可执行证据分离：

| 排名 | 原实验输入 | 历史静态反向Router view | 买入后状态更新的无税参考反向 | 范围 |
|---|---|---|---|---|
| #1 | 10 USDT | 9.930276362283922020 | 9.950112138733759041 | 首Mint块52,440,324 |
| #2 | 0.01 WBNB | 0.009926233485230985 | 0.009950122293529727 | 首Mint块52,440,617 |
| #5 | 1 USDT | 0.395408042268688956 | 0.997158206422518356 | 首Mint块52,441,107 |
| #14 | 0.01 WBNB | 0.009938414057573645 | 0.009950091711211336 | **延迟首Mint块52,446,013** |

**#26来源纠错（直接重新取得的历史事件）**：块52,446,701的Pool `0x47009c98b5e2d234724b1f8a9fb43da6fbe882f2`，分别按Pool+单块+Sync/Mint主题查询连接的Alchemy历史BSC节点，两次完整正规化响应各1条，二者交易哈希一致：`0xe722f3db159d390decd678fc7b1a5a7f863599a52d07b737e5be6be0b101d112`，Sync logIndex `0x141` 在 Mint `0x142` 之前、事件data逐字匹配；储备0=`98000000000000000000000000` token原始单位，储备1=`15000000000000000000` WBNB原始单位。原来源节误记的63字符交易哈希已在JSON中保留为`original_incomplete_tx_hash_superseded`，不再当作有效哈希引用。**这补全了#26的历史流动性数学输入及同Tx事件证明，但仍没有HTTP原字节/独立RPC、部署时间、公共T_entry或真实买卖/卖出税验证。**

#5静态反向报价只有约0.3954 USDT，主要因它复用了买入前的薄池状态，**不能据此声称实际连续买卖损失约60%**。#5创建初始报价储备仅约1.314 USDT，深度风险仍非常大；该参考假设买入后资产全额收到、无人抢跑、钱包允许卖出、无转账税/黑名单、无Gas、无滑点外冲击与其他Swap，也未经真正fork交易模拟。结果保持`SELLABLE_AT_NOTIONAL=UNVERIFIED`、`RULE_EXIT_PAPER=NOT_SCORABLE`，不产生BUY信号。

研发仅在既有`mission_agent/early/bsc_v2_pit.py`加一项纯函数及在原测试文件加定向回归，并纠正旧30例单测错误地断言每例创建当笔均有Mint/Sync（真实为25/30）。**仅完成隔离环境等价数学的2项Python单测PASS，Git checkout全部Python单测/CI/外部独立Review与用户Mac历史原RPC/HTTP字节SHA均尚未完成；不要当作整仓测试通过。** 新证据仅复算已存历史事件，未向用户申请交易金额、未改变原冻结初始流动性准入门槛/样本/标签、无真实交易、无额外付费、无监控、无Mac部署。接下来的核心任务仍是完整30样本的来源原字节及实际税/Router双向交易路径，优先解决仅影响链路的阻断，不再用旧静态报价误推可卖性。

---

## 2026-10-20 P0 当前优先结论（旧日期下方进度为历史快照，不覆盖本节）

**本节是当前唯一决策摘要。** 原冻结2025-07-01 UTC历史Pancake V2母体30个候选，`30/30 PairCreated`原交易及池序号已证明；`25/30`在创建同交易有Mint+Sync，`20/30`创建时达到2 WBNB/1000 USDT的历史研究阈值。**这不是24/30完整PIT，更不是18/30双向交易门禁通过。** 全部身份及交易来源仍来自Alchemy已连接免费历史查询的正规化RPC返回；用户Mac原始HTTP存档/哈希、第二独立数据源、部署准确时刻、实际可观测T_entry与税费/禁售验证尚未完成。

创建时没有同交易LP的5个（#14、#16、#17、#18、#26）也始终保留在30币分母中：
- **#14**：00:41建池，01:11:34 UTC（块52,446,013）首次可核Mint+Sync，报价侧17 WBNB。故不能以创建时间充当入场时间。
- **#26**：随后块**52,446,701**找到完全匹配的Mint+Sync，同笔交易`0xe722f3db159d390decd678fc7b1a5a7f863599a52d07b737e5be0b101d112`，报价侧**15 WBNB**；是第二个延迟加池证实案例。
- **#16/#17**：建池时getReserves为0，块52,444,232有Mint且历史getReserves报价侧分别约9.6000及20.2000 WBNB；但当前连接器的同块Sync列表超过约8KB被截断，**不得声称同Tx Sync完整匹配**，先记`MINT_PLUS_NONZERO_POOL_STATE_SYNC_UNRESOLVED`。
- **#18**：创建时和当日末的pair `getReserves()` 仍为0/0，`blockTimestampLast=0`；按标准Pancake V2代码意味着**当日末前尚未执行Sync**，但不能推论次日永远不加池，也不可直接从母体剔除。

**开始了可交易性来源核验，但未证明普通用户的实际可卖出能力。**

在2025-07-01历史区块执行[PancakeSwap V2 Router](https://github.com/pancakeswap/pancakeswap-ai/blob/main/packages/plugins/pancakeswap-driver/skills/swap-integration/SKILL.md) `getAmountsOut`（**view only**）；每项先读`quote→token`，再以第一步原始token报价对**同一未改变的历史池**读`token→quote`。费率据[PancakeSwap官方文档](https://docs.pancakeswap.finance/trade/pancakeswap-exchange/trade)为每次0.25%。两次静态quote结果和整数V2 AMM公式均逐字一致，不能把第二次读操作误称为实际连续回合卖出/利润：

| 冻结候选 | 固定历史区块 | 只读买入输入 | 在同一未变动池上再独立查询的token反向报价 | 解释 |
| --- | --- | --- | --- | --- |
| #1 | 52,440,324 | 10 USDT | 9.930276362283922020 USDT | 静态报价，不保证token可转账 |
| #2 | 52,440,617 | 0.01 WBNB | 0.009926233485230985 WBNB | 同上 |
| #5 | 52,441,107 | 1 USDT | 0.395408042268688956 USDT | 仅有约1.314 USDT初始池报价储备，容量极浅 |
| #14 | 52,446,013（延迟首Mint） | 0.01 WBNB | 0.009938414057573645 WBNB | 不能把创建时空池当作已有报价 |

这些notional是**试验金额**，不同quote资产的金额不能直接横向衡量胜率、不能取代未来P1前冻结的相同研究金额。报价没有计算historical token税费、账户限制、MEV、真实持币到账、真实连续下单后的更新池状态，也**不代表**`SELLABLE_at_notional`标签通过。

**真实Swap方向也已从原事件拆出并与ERC20 Transfer原日志互证：**
- #1在块52,440,351发生`QUOTE_TO_TOKEN`，Swap报告池收约**88 USDT**，token由池子转给接收方，Transfer与Swap`tokenOut=13922587526690708956`精确一致。
- #2在块52,440,642发生`QUOTE_TO_TOKEN`，Swap报告池收约**0.0937 WBNB**，token Transfer与Swap`tokenOut=51223471067359749457487212`一致。
- **#5在块52,441,377确实发生`TOKEN_TO_QUOTE`真实卖出**，有转入池的token Transfer，`tokenIn=69914887641473879`和Swap完全一致，池付`quoteOut=99632794358189979`（约**0.099632794358189979 USDT**）。这只是**一笔已观察到的小额卖出事实**，不能由此推论其他地址、更大订单或未来时点能卖，更不等于净利润。

上述静态买卖报价、三笔Swap与Transfer互证、合约部署时运行字节码初检及5个空池后续状态已统一写入同份[P0来源JSON](P0_SOURCE_PROBE_20261019.json)的`bsc_v2_p0_execution_source_pilot_20261020`和`bsc_v2_p0_late_lp_source_pilot_20261020`，不新增Stage文件。代码在原`mission_agent/early/bsc_v2_pit.py`加入只读V2 0.25%整数quote、Swap方向分类并有真实Router数值回归。**仅临时Python隔离镜像8项定向纯函数测试实际PASS；Git源码完整测试、Mac原HTTP字节及独立审查尚未通过**，此版本不得标APPROVE。

**下一步主线门禁**：再以事前确定研究notional和完整税/blacklist/Router转账路径检验出场，获取有原始SHA的当时可观察事件和跨时间真实流动性，达到P0所列`24/30`及`18/30`的审查条件才进入P1。未通过时固定标`SOURCE_PARTIAL / EXECUTION_NOT_VERIFIED / P5_NO_GO / NO_TRADE`。不能用已观察1笔成功卖出、4组静态报价或30个建池事件充当30币回测或可盈利证明。

---



## 2026-10-20 本轮最新实际进展（以下早期章节为历史研究快照）

**本轮继续原P0，没有建新Stage、没有修改30个身份筛选规则，没有查看后验价格/未来赢家名单，也未执行Mac/后台/实盘交易。** 依赖原唯一固定2025-07-01 UTC PancakeSwap V2 Factory；此处`30/30`指**30个池的创建源**，不是P0终验、Binance Alpha可见性或全BSC代币母体完整性。

| 任务 | 实际查证事实 | 计数 |
| --- | --- | ---: |
| 原Factory时间序号+真实 `PairCreated` | 从历史`allPairsLength`逐序号二分首创建区块，再逐一查Factory事件交易哈希、Pair地址和序号，30/30互异token CA保留 | **30/30** |
| 建池同交易 `Mint/Sync` | 有匹配的原事件、数量和事务；另5个建池时没有同交易加池，但不删除 | **25/30** |
| 当下初始报价侧余额达到冻结粗门槛 | 2 WBNB或1000 USDT，是有界**研究门槛而非用户实际订单额度** | **20/30** |
| 同交易加池但不足门槛 | `#5/#8/#15/#20/#28`，全部保留原母体 | **5/30** |
| 创建时空池/未找到同Tx初始Mint | `#14/#16/#17/#18/#26`，不把建池空池直接当死亡、也不回填未来流动性 | **5/30** |
| 延迟加池 `Mint+Sync` 真实证据 | `#14`，创建00:41:00 UTC，01:11:34 UTC才有首个可验证Mint/Sync，报价侧 **17 WBNB**；严禁把17 WBNB提前到00:41的`T_entry` | **1个另证** |
| 延迟Mint但相关Sync不完整 | `#16/#17`：首次储备更新区块均定位，Mint确有原事件，但本会话Alchemy连接器在同块Sync日志约8KB截断；`SOURCE_TRUNCATED/NOT_SCORABLE`，不得强行把Mint数据当确认的完整双向成交 | **2个部分** |
| 暂未补足延迟流动性 | `#18/#26`，状态保留`UNKNOWN` | **2个待查** |

**最重要的业务判断**：Pancake V2的历史池身份及真实创建时点在这30个抽样记录里已经可核对，但`30/30 PairCreated`绝不能晋升`24/30完整Token部署+公众时间可用性PIT`。当前`token creation`、历史独立可见性、税/黑名单/买卖权限、当时真正bidirectional固定金额深度以及纸面退出手续费均不足，所以**24/30和18/30正式验收均`NOT_SCORABLE`，预测模型不启动**。原始完整提供商HTTP JSON-RPC字节与header未能由本会话Alchemy连接器归档，Git只保存原RPC**标准化原事件字段**和每条事实的来源范围；不能把Git里标准化结果伪装成完整raw SHA归档。

**避免重复做无效单点工作**：新早期研究纯包`mission_agent/early/bsc_v2_pit.py`新增`verify_delayed_mint_sync`，判断是否确实后来才加池；原只读CLI `monster_early_venue_factory_rpc_roster_probe.py`的 `--mode bootstrap --bootstrap-start-rank 1..30 --bootstrap-limit 1..5` 可有界处理任意冻结排名段，避免原只能处理前五名的业务阻断；待用户Mac实际联网与授权执行才会留下带SHA的完整RPC bytes。原始`--mode enumerate`须先成功且同源，同日固定名单不可更改。测试已添加整30例历史标准化事件确定性回放和#14延迟加池反例；**本会话在隔离Python镜像实际跑过4项纯函数unittest，全部通过；这不是远端完整测试/CI/Mac联调通过，新增30例回放仍待仓库环境执行**。PR依旧Draft，不授权`MERGE / DEPLOY / GMAIL / TRADE`。

**下一步关键阻断仅两件**：①取得Mac上的历史RPC原始JSON和SHA完整归档，并正式跑完整代码/三十例回归及必要独立审查；②按冻结名单验证当时的真实可买**且可卖**路径/代币限制与费用，不要继续只靠AMM储备数学模拟判可卖、更不能从本次历史创建事实倒推以后十倍。原2025-07-01 Base30探针属于另一套冻结研究，不能混成这30个BSC V2结果；BSC V3/Four.meme/Alpha分母也尚未覆盖。保留11月2日源预算停止规则。

---



状态：`BSC_V2_30_IDENTITY_ROSTER_VERIFIED_AS_HISTORICAL_SCALARS / PIT_NOT_SCORABLE / NO_MODEL / NO_TRADE`。本文件是本Phase唯一当前报告，不新增Stage文档，不更改2025-07-01 Base30原冻结探针，未使用任何付费RPC、钱包、Mac后台服务或两次P0 CI预算。本轮真实连接器读取的机器可核数字和前12个池地址在同目录[源结果JSON](P0_SOURCE_PROBE_20261019.json)；**原始提供商HTTP正文/响应header没有通过当前连接器归档，因此SHA256字段为null，尚不满足最终PIT和审计门禁**。

## 1. 先拿到真正的链上事实

已使用用户原本连接的免费Alchemy All Chains应用在BNB Chain主网（chainId56）读取2025年的历史区块、PancakeSwap V2官方Factory `0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73` 的只读历史状态与`eth_getLogs`：
- 2025-09-29 22:31:02 UTC，区块 **62,914,693** 的真实`PairCreated`，哈希`0xb63846e92b19018da4d0e24cec8aab69d979c14059130b7b76dbfe972e5e1418`，Pair `0xb2dc7c7f5b67b2d604603fbc56530ba7832648a8`，token0 `0x1c88e86556b815f4b140ec14297ada7863bc97c8` / token1 WBNB。相邻历史`allPairsLength()`由1,985,116到1,985,117；`PairCreated`日志的`allPairs.length`和同一历史区块的`allPairs(1985116)`都严格相符。这是实际链上存储/日志的独立函数交叉验证（同一Alchemy来源，**非第二提供商独立证明**）。
- 在2025-08-09 14:01 UTC与2026-03-06 11:21 UTC，另两个不同月份的10区块窗口，`eth_getLogs`都为0，同时历史Factory计数delta均为0；只代表**各自10区块**没有创建，不表示整天或样本币为零。
- 请求一个2,000区块的BSC`eth_getLogs`明确被当前Alchemy免费计划拒绝：`Under the Free tier plan ... up to a 10 block range`。不能用此调用方式在合理请求预算内连续爬半年，也不能据此判断其他免费RPC全部不可用。BNB Chain官方列出的公共主网节点禁用eth_getLogs，参见 [BNB官方说明](https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/)。

## 2. 关键发现：V2可不依赖历史长跨度event日志，按Factory不可变序号恢复候选分母

[PancakeSwap官方合约源码](https://github.com/pancakeswap/pancake-swap-core/blob/master/contracts/PancakeFactory.sol)同时暴露`allPairsLength()`（selector `0x574f2ba3`）和`allPairs(uint256)`（selector `0x1e3dd18b`）；Factory数组追加新pair，历史状态读数包含当时前N个池，**不因为之后token死亡/退市/价格变动而删除旧pair地址**。此结论只适用于此已核实的V2合约存储模型，不自动扩展V3、launchpad或全BSC代币母体。

固定日期 **2025-07-01 UTC**，已从历史块时间二分定位区块闭区间 **52,440,287—52,555,482**。实际Factory历史计数：
- 前一块52,440,286：**1,874,173**
- 7月1日最后一块52,555,482：**1,874,958**
- 所以当天V2新pair数**785**（工厂数组长度差，非全日志已复核数量）。
- 已依次查询zero-based Factory index **1,874,173—1,874,206** 共34个pair地址，并按序分别读取其历史`token0/token1`；**34/34成功**，其中4个不满足事前WBNB/USDT配对条件，**30个不同CA合格为初始历史池身份候选**。前12个池的11/12报价配对只是这一批的先导结果。完整34池（含4不满足事先条件的负控制）与30个按顺序获选CA地址、精确工厂序号均保留在[机器JSON](P0_SOURCE_PROBE_20261019.json)，没有查看后续利润/幸存与否，也没有静默删除不匹配的池。
- 不能凭7月1日末的池身份数据把建池时点或初始流动性、真实第一笔Swap倒填到当日早晨。这30个是**先于任何5x/10x结果冻结的源身份名单**，不是已经取得全部`PairCreated`原交易哈希的30个PIT事件，更不是`T_entry`、真实可交易、流动性合格或盈利名单。

**方法判决：BSC_V2_FIRST30_CHRONOLOGICAL_POOL_IDENTITIES_RECONSTRUCTED。** 不依赖事后热门币名单的前30池身份已取得（工厂前缀34/785），但尚未取得对应原交易、真正初次进入流动性、税、可卖出报价或退出证据。若未来补充第二提供商/交易原文发现与本次数据不一致，应冻结并复核，而不是悄悄换掉死亡币。V3 PoolCreated需继续经可完整获取的旧日志或独立索引建立母体，不能假设与V2有`allPairs`接口。Alpha/launchpad/Pancake Infinity分母更不自动被V2代表。

## 3. 同一代码中实现可重复只读入口，不造新Stage脚本

已在原`local-agent/scripts/monster_early_venue_factory_rpc_roster_probe.py`中追加`bsc-v3`官方V3 Factory地址及`--mode enumerate`限BSC V2；可在已批准的用户Mac研究目录中运行：按固定UTC日边界计算V2起止序号，单调按序获取`allPairs(index)`和同历史块的`token0/token1`，每个index的原始RPC文本、SHA256和source fingerprint保存本地，断点重新读取时验证原文本SHA和endpoint一致性；只有得到真实前30个符合事前报价条件的**互异CA**才报`CHRONOLOGICAL_FIRST30_V2_POOL_IDENTITIES_ONLY`。不读CEX后续价格、不调用交易方法/钱包、不运行Gmail/launchd，也不把这30项直接晋升为5事件PIT验证。

`--mode probe`仍只做2000/10块能力检查；`--mode scan`仍做连续Factory原事件扫描。新增单测涵盖V3/v2不同事件ABI、V2序号增量与恶意删行、保留原始响应的枚举/续跑/源SHA/零地址拒绝等。**当前只完成了代码提交和小范围链上独立验证；本分支新改动尚未执行完整Python unittest/CI或拿到其他AI独立代码审查结论，不应宣称测试绿。** PR30保持Draft。

## 3A. 继续真实查证：3个事前固定候选的建池及首笔流动性（2026-10-19）

本轮没有再从赢家名单反推选择。直接使用[JSON已冻结的30个CA](P0_SOURCE_PROBE_20261019.json)中的排名**1、2、5**，从**历史工厂序号**对 `allPairsLength(block)` 做首次成立区块二分，然后查询该块真实 `PairCreated` 和对应Pair同一笔交易的 `Sync`、`Mint` 日志，另用历史 `eth_call getReserves()` 在同一块复核。

| 原30名单位置 | 首次创建的BSC区块（UTC） | 原始交易 | 首次`Sync`的报价侧储备 | 预设初始报价流动性下限 |
| --- | --- | --- | --- | --- |
| 1 | 52,440,324（07-01 00:00:27） | `0x26396c2954f8f1ff36449d76454f0706c9cf1564da89b2a4a3f0fdfbac6744dc` | **10,000 USDT** | 满足1,000 USDT粗门槛 |
| 2 | 52,440,617（07-01 00:04:07） | `0x51d6219287049c10e7e61b039aee60222bd37e8ae2b3c20f52860fc30b79fd33` | **8.3 WBNB** | 满足2 WBNB粗门槛 |
| 5 | 52,441,107（07-01 00:10:15） | `0x84be9a910e2786682d7130b8fa6e5471aa75c36d352f9d8550021ed0c4da9a86` | **约1.314 USDT** | 不满足1,000 USDT粗门槛 |

三笔都实际具备独立Factory `PairCreated` 和**同交易Pair `Sync+Mint`**；日志初始 `reserve0/reserve1` 与创建块 `getReserves()` 原始整数完全相符。已将每个样本Factory及Pair对应交易的**完整正规化链上事件字段（地址/主题/data/tx/block/logIndex/时间）**追加到同一份P0 JSON，避免只保存文本结论。它们是原链读取结果，不是包含节点HTTP头部的完整原始供应商回执：`raw_http_sha256=null`，独立提供商重取还未通过。

**真实首笔后续Swap已找到，但仍不是可卖出/盈利证明。** 在每个Pair建池之后的前10个区块内未见Swap；这只是窗口受限的初步观察。随后利用 `getReserves()` 的历史 `blockTimestampLast` 单调更新，对各池二分定位创建后的首次**后续储备更新区块**，并查到同一块真实 `Swap` 日志：
- **#1**：52,440,351，2025-07-01 00:00:48 UTC，距离建池21秒；原交易 `0x2d0361e427bc0feaf9e316f6a79b3a9f935777043d13cb4084c9adfeed2f9ae7`。
- **#2**：52,440,642，00:04:26 UTC，距离建池19秒；原交易 `0x459ad9b0a8601b3502077ce5e26a65af7b461429958c4ff8d9e269ee48324547`。
- **#5**：52,441,377，00:13:37 UTC，距离建池3分22秒；原交易 `0xddf4631429c9faf6bb2a117516a2fff39debe9fd207d19c274808ca99a16f348`。

以上3条后续Swap的真实 `Sync/Swap` 标准化事件及历史reserve时间查证已并入同一P0 JSON；**这证明这些池有链上Swap交易，但不是某一资金量可以当时立即买入再卖出的证据**。历史区块时间不等于观察者当时实际接收时间，是否允许卖出、税费、滑点、launchpad迁移、持仓容量仍是`UNRESOLVED`。特别是批量工具中曾错误写入V2 Swap主题，已通过这三条真实交易核对纠正为链上实际 `0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822`，并为此添加回归约束。

**交易性仍未证明**：目前仅`INITIAL_LIQUIDITY_CONFIRMED / FIRST_SUBSEQUENT_POOL_SWAP_ONCHAIN_CONFIRMED / T_ENTRY_EXECUTABLE_UNKNOWN / SELL_PATH_UNKNOWN`。其中1号、2号当天结束时储备的报价侧已分别变成约0.002406 USDT、0.00001804 WBNB，报价储备剧变是事实，但**不能仅凭余额下降推断撤池、跑路或投资收益**；必须另查 `Swap/Burn` 及可归因资金路径。本轮不看后续5×/10×标签。

**P0进度：3/30真实原`PairCreated`+初始`Mint/Sync`且后续真实`Swap`得到链上交叉核实，其中2/3达到事前最低初始报价额；但3/30的完整部署时间、公众首次可见时刻、策略初次满足全部可交易条件时刻与双向同额可卖性仍不成立。** 所以24/30“部署及首池完整PIT”、18/30“真实双向可交易”严格验收**仍然NOT_SCORABLE**，绝不能拿这3例初始流动性当作3笔已验证盈利交易。

为避免人工重复针对单钱包和每币撰写Stage，本轮同步在 `local-agent/mission_agent/early/bsc_v2_pit.py` 建立唯一纯函数验证内核：`first_creation_block`二分、`verify_bootstrap`逐一核Factory事件和同Tx `Sync/Mint`，缺源立即UNKNOWN而不伪造Swap；旧Factory脚本继续承担有界RPC和本地原字节归档。配套测试包括历史冻结三例反例重放，不涉及生产。 批量CLI新增 `--mode bootstrap --bootstrap-limit N`，先要求同一数据源已固定 `--mode enumerate` 的30个身份列表，之后最多逐次验证5个原序候选、保存factory/pair/首笔储备更新原始RPC文本SHA；不自动启动、未实测Mac。纯函数镜像在独立本地Python环境的**3项合成单元测试实际通过**；Git中扩展的三例回归及原脚本完整测试仍须正式在该固定SHA运行，不能提前说CI通过。下一个动作必须是**批量使用该唯一验证器**，不是再增加一个按币命名的脚本或Stage。

## 4. Plan A/B/C实际状态及P0结论

| 路线 | 本轮实际可核事实 | 判定 |
| --- | --- | --- |
| A1：当前Alchemy免费历史`eth_getLogs` | 三个窗口各最多10块可读、成功校验1条正事件，2,000块请求被限 | `SMALL_RANGE_PASS; FULL_DAY_FAIL_THIS_PLAN` |
| A2：Alchemy BSC V2历史Factory状态 | 2025-07-01按工厂计数发现785新池；按序34个池恢复全部token0/token1，冻结30个不同CA配对候选 | `FIRST30_POOL_IDENTITIES_CONFIRMED_SCALAR; ORIGINAL_HTTP_AND_FIRST_SWAP_NOT_VERIFIED` |
| A3：用户Mac上其他真正开放历史logs的免费RPC | 当前会话容器DNS不可用；Mac未有本项目真实探针输出 | `NOT_TESTED` |
| B：符合合法导出与成本条件的BSC历史索引 | 已核公开数据列表和权限，未取得全量旧日志授权导出 | `NOT_VERIFIED` |
| C：商业/充值RPC | 合同默认0美元、无需请求用户资金 | `NOT_AUTHORIZED` |

**P0整体：`SOURCE_PARTIALLY_FEASIBLE_NOT_GATE_PASS`**。现已取得V2前30个历史池身份，但仍未取得30/30`PairCreated`原事件和准确首次出现/可交易时间证据，也未做24/30部署/首池与18/30首次双向可卖模拟覆盖，故原`COVERAGE_RATE=NOT_SCORABLE`、`G4 UNKNOWN / G6 NO_GO`保持。既不因为小规模正面源证据就直接启动十周建模，也不因为HTTP网络条件把链上源永久判死。

**下一次有意义交付**只接受：在实际Mac前台、免费、可限额/可中断的read-only枚举中复现既定30个顺序候选并留原始SHA归档；随后对随机预定样本查原创建交易、首次真实Swap/流动性（包含失效样本），达到24/30与18/30才进入P1。对V3和launchpad缺失需在同一P0结果中明确范围，不能偷换成“全BSC完整母体”。
