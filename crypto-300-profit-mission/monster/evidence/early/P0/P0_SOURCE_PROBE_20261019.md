# Monster P0 — 免费历史源实测：BSC V2工厂存储枚举方案（2026-10-19）

## 2026-10-20：Factory存储索引跨三个月份历史日期可读，原始V2来源取得增量证据

**本轮是P0来源能力的有限、前台只读验证，冻结30币及交易金额均未变。**复用以前V3来源核查事前选定的三个独立UTC日期**2025-05-01、2025-07-01、2025-09-01**，针对PancakeSwap V2 Factory（`0xca143ce32fe78f1f7019d7d551a6402fc5350c73`）通过Alchemy免费BNB主网历史`eth_call(allPairsLength)`分别比较每个日期**首块之前**与**最后一块**的Factory计数；两个跨月日期的UTC边界以区块头timestamp二分定位。历史V2新Pair数分别为**455 / 785 / 798**，三个不连续日期合计**2038个新Pair索引**。这些只是Factory累计状态差，不等于2038个独立Token/有流动性的池/真实可卖币，也不声称连续覆盖五月至九月的所有日期。

**抽样验证真实链事件，避免把Factory计数差当成虚构数据**：对三天各用`allPairs`精确读取当日**首个与末个**新索引（共6对），再读各Pool的token0/token1及同日末历史储备。对5月与9月的首个索引用历史Factory计数二分找出创建区块，分别是**48,876,497**与**59,582,029**；在各自**单区块**读取原`PairCreated`并证明Pool地址、两边Token、Factory单调一基序号一致。5月首池为`0xf14395e78c2a037570b05eb657672af36ffd380c`，对应tx `0xada1424a9a94ade33995776b311a204735328f227898563bdb9208a9076d7287`；9月首池为`0x14f7c8c33487e16677eaa72ddb253912b9bba1c0`，tx `0x6c4665cc9d50acf290ed9c203d7f8d060a188ecc8e5198ac9b0ab2ee7a51e70d`。7月首池原P0已独立验证过，此次Pool索引与既有rank1一致，无须再审。

**两种真实业务反例**：在创建块和紧接下一块，5月首池WBNB侧`3 WBNB`、另一侧`0.98` Token单位（18位假设不可自动成立，原始token储备为`980000000000000000`），有同创建交易`Sync/Mint`，但该两块**无Swap**；9月首池这两块**0/0储备、0条Pool事件**。因此即使Factory索引可以早期发现真实Pair，**不能据此下结论已经可买，更不能认定可按相同名义金额卖出**。同日末的6池储备仅供历史状态反例，绝不能倒填为建池即刻可用储备。

**证据和门禁**：原P0 JSON键`bsc_v2_p0_three_preregistered_dates_factory_storage_index_source_capability_20261020`保存UTC区块边界、3个累计差值、6个Pool身份及储备、两例真实Factory交易哈希和早期状态。所有结果为现有**单一Alchemy规范化RPC**，未取得原HTTP字节SHA或第二来源交叉核查；也**没有逐条枚举2038个Pool、取得完整Token母体或证明2025真实`available_at`**。这只实证了跨日期**V2 Factory存储索引源的一条能力**，并未解决V3、launchpad、历史实时PIT或统一研究金额的买卖/费后退出。P0`INSUFFICIENT_COVERAGE`、P1`BLOCKED`、G4`UNKNOWN`、G6`NO_GO`保持。不跑连续历史日志、不付费、不启用Mac后台采集或Frank、Stage99、Gmail、交易，不做模型训练。

## 2026-10-20：原冻结BSC V2 30币恢复29笔真实合约直接部署交易，24个达标池均已关联部署回执

**这次取得新的部署链上证据，且没有选择未来赢家。** 以原用户Mac前台归档的2025-07-01冻结30币及26币「相邻块无代码→有代码」为确定性输入，复用用户已有的**Alchemy免费BNB主网只读连接**，仅对每个已知首代码块读取**该Token地址在该单块的事件**，再用实际`eth_getTransactionReceipt`核对。`29/30`条创建交易同时满足 **status=0x1、receipt.contractAddress=冻结CA、receipt.to=null、receipt.blockNumber=已确认首代码块**，链上证据支持「ERC20代币合约的直接部署交易」；准确的29条txhash/CA/区块逐行记在原P0 JSON键`bsc_v2_p0_29_direct_creation_tx_receipt_recovery_20261020`。其中#1/#8/#15先在当日以前的块对`eth_getCode`有界二分确认代码出现边界，再取创建回执。所有原30币继续保留分母。

**业务交叉结果**：此前可观察到报价侧储备达到冻结最低档位的24个池，**24/24均已关联成功代币部署回执与原PoolCreated身份**。这是已证链上历史身份和部署的覆盖，**不是P0正式24/30 PIT门槛通过**。原来2025年真实公众首次可读取的`available_at`对30/30仍为UNKNOWN，当时的交易可入场先后顺序不可被2026年回查替代。对这些24池，已归档的后续真实BUY/SELL、初始和次区块流动性事实维持原口径；**正式18/30同一冻结研究金额、双向含费可卖出能力仍NOT_SCORABLE**，没有自设交易金额，也没有查询5×/10×未来收益。

**唯一仍未取得准确创建txhash的#5**：代币`0x6d75721984a6678dabe2c5e34ed872f9cc2d5a65`在区块**45,677,195**没有代码，**45,677,196**首次有代码，明显早于2025-07-01 V2池创建；但在该单块对代币地址`eth_getLogs`返回0条，不能据此认定没有部署。该块共有192笔交易；Alchemy免费`trace_filter`明确拒绝（需付费），因此**没有去付费、没有猜测部署txhash、没有为凑30无界逐笔扫描**。该币仍保留在完整30币分母，部署交易标`UNVERIFIED`，此前「无已确认报价侧最低流动性」也继续标UNKNOWN。

**证据等级与止损**：这29笔链上回执来自单一Alchemy连接器的规范化只读RPC结果，**未取得29笔HTTP原字节或独立来源SHA，不构成独立双源验收**；此前Mac原始归档与连接器结果的范围不可混称。未改母体、参数、schema、历史标签、旧批准内容、Frank、Stage99或研究金额。本轮没有新源码、代码测试、CI、Mac后台、Gmail、购买API、部署、合并或任何下单。BSC V3全天和launchpad来源依然不可用，P0 `INSUFFICIENT_COVERAGE`、P1 `BLOCKED`、G4 `UNKNOWN`、G6 `NO_GO`维持。下一个最高价值缺口是**证明当时可观测时点以及真实同量双向退出**；不因部署来源提升而跳进模型开发。

## 2026-10-20：V2工厂计数可不依赖历史getLogs发现新增池，3个真实新池无储备，严格限制为只读可行性

为避免V3历史日志源失败后反复寻找免费节点，本轮只在**已有Alchemy连接**内短暂核查PancakeSwap V2 Factory合约的历史`allPairsLength()`与`allPairs(index)`：块`128722337`工厂总数**3,509,484**；前120块增**13**对、前600块增**35**对、前2400块增**148**对，增量是**Pair数不是通过流动性准入的新Token数**。对前120块新增索引按顺序先取**第一个、中间一个、最后一个**，三个`allPairs(index)`分别返回`0x1c4725bee3de56b09b8f022101d8bae61e0ffe97`、`0x7dab56bc4e9e8351599e94ae9d47cf6daaabd8ff`、`0xedc3964b993983d44fa05dc39169edaa18defe80`，其`token0/token1`均有一侧WBNB，但在同一固定块通过`getReserves()`都返回**0/0**，**这是池身份有效、尚无真实池深的反例**；不能发WATCH/BUY，也不证明它们将来始终没流动性。

以第一个索引`3509471`为历史目标，对`allPairsLength`二分7个只读历史块，找到了该索引首次可用的块`128722229`（前一块工厂长度3509471，当块3509472）。再对**该块一个**Pancake V2 Factory `eth_getLogs(PairCreated)`实际读取，出现成功真实事件tx`0x26eb11e27d6fdb75315c74e9f1b312d746ce654d6188a6ae819f9c628044e2af`、`logIndex=0x1c9`、区块头时间`2026-10-20T09:28:43Z`、Pair编号3509472、Pair地址与`allPairs(3509471)`相同。证明**Factory存储索引可作为不依赖连续大范围getLogs的V2新池候选发现通道**；仍需另行确认首次公开接收时钟及流动性/交易真实执行，PairCreated != real liquidity、Pool count != distinct token count。

**权限与研究止损**：本次只读临时探针，无自动定时/手动任务创建、无新脚本、无Mac部署/CI、无旧Stage99重启、无Frank改动、不固定金额；不可拿2026-10-20事后历史读数填充2025-07-01的真实`available_at`或V3/launchpad母体；只作为以后单独获授权时前台采集工具的局部技术依据。原P0主线Source stop、30币正式24/30 PIT及18/30统一订单额、P1 BLOCKED、G6 NO_GO都未通过。逐块数量、三个Pair的raw uint值与首Pair真实事件独立匹配在原P0 JSON键`bsc_v2_p0_forward_only_factory_counter_logless_discovery_readonly_pilot_20261020`。

## 2026-10-20：P0原30币一页业务缺口/停止决策——不再追同类RPC边界

**固定分母与来源**：2025-07-01 BSC PancakeSwap V2先到的30个不同Token，全部保留，绝非全BSC或V3、launchpad。根据旧P0真实日志、Alchemy历史交易回执、Mac卖出原档审核、24池次区块储备及30币字节码资料，**零新链上查询**做了30/30确定性逐币来源Join，分成完全互斥的4组（合计30，不改变母体）：

| 可核验历史阶段 | 个数 | 冻结rank及业务含义 |
|---|---:|---|
| 池深达标，后续真实BUY及在达标报价侧池深下成功SELL | 18 | #1/3/4/7/9/11/12/13/16/17/19/21/23/24/25/27/29/30。只是历史有买卖：7完整同Token接收者退回原买入数量，2同接收者仅部分回池，9其他地址卖；**不等于18个普通人可同金额退出**。 |
| 池深曾达标且后续真实BUY，但观察到的首笔索引SELL处于极薄池深 | 4 | #2/6/10/22。四笔SELL**确实成功**，但SELL前原WBNB池储备分别为`0.000189964162160741`、`0.000289304051072299`、`0.000601943052925702`、`0.000628508265191285` BNB，远低于预冻结2 BNB观察门槛；**不能据此说市场其他时刻必然不可卖**。 |
| 已有池深达标，缺少达标后独立实际BUY证据 | 2 | #14/#26。无买入回执不等于没人买、未来不能买。 |
| 尚未证实达到预冻结最低报价池深 | 6 | #5/#8/#15/#18/#20/#28。保持`UNKNOWN`、不能标死亡币或负例。 |

**主要阶段证据按层次，绝不升格**：30/30工厂历史池身份与代码存在；25/30原建池同交易Mint/Sync；24/30首次达标和次区块储备持续符合报价观察档位；22/30独立后续BUY，18/30选中高池深SELL。代币**准确部署交易**依然未在原30币逐一取得/验证，真正2025实时公开接收的`available_at`也全体未证；次区块闭状态、曾发生过的未来买卖和最近Sync时间戳不等于入场点。**正式24/30部署+初池PIT门槛NOT_SCORABLE**，而不是“24/30合格”。原18例中的7/2/9是交易参与地址关系，并非同钱包盈利18例；**正式18/30统一研究名义额下双向可卖门槛NOT_SCORABLE**，不是“18例已通过”。

**实际止损原因及下一动作**：完整BSC母体必须有V2+V3+关键launchpad；现在V3全天事件来源未形成（Alchemy免费10块上限，全日需要11520次只扫Factory；Graph目标/对照403；PublicNode两档403；OnFinality两档429；BNB官方公用节点禁用getLogs）。因此停止无证据节点轮换、重复批准旧receipt和“硬凑胜率”。源缺失不可算0个代币或0%赚钱。用户明确不希望交易工具预设买入金额；研究用同一名义额也**尚未有授权冻结**，不自行设置并把它当交易计划。若未来真要开展可执行费后收益研究，须单独获得研究Notional参数的明确批准，且要证明历史两向实际可执行并保留失败币；否则止于P0，不写预测模型。原试验停止日期2026-11-02仍保留；届时无足够源/时点证据则提出保留的**前向只读观察**为另一项独立需同意的研究方案，不暗中上线。P0`INSUFFICIENT_COVERAGE`、P1`BLOCKED`、G6`NO_GO`。

逐币一行的23个来源字段/状态等完整机器表在此P0 JSON的 `bsc_v2_p0_frozen30_one_page_source_pit_trade_gap_decision_20261020`；本轮没有新网络、代码、CI、付款、交易、部署、任务或生产改动。

## 2026-10-20：OnFinality公共BNB历史日志前台实测2档HTTP429，V3计划A暂时止损

用户已执行我们给的**仅3请求**（若链ID通过）Mac标准库前台只读探针到`https://bnb.api.onfinality.io/public`。`eth_chainId`返回`0x38`，原响应的用户报告SHA256=`ce50ba55ecf1a9410c6f5503d09da66974203165305ff8f5a2b520f49a705c07`；`eth_getLogs`同一V3 Factory+topic的2025-07-01区间**52440287–52442286（2000块）HTTP 429**、**52440287–52440296（10块）HTTP 429**。用户Mac归档相对目录`monster-p0-readonly-raw/v3-onfinality-check/20261020T090040103009Z`，脚本仅在正常200响应时保存原始JSON；因此**两次429的HTTP body/header及SHA不存在**，不能据此声称服务器拒绝理由是明确的次数上限、没有历史日志或不支持V3。链ID的SHA只来自用户提供，不是助手读取文件后重算。7秒间隔仍得到429，但不进行反复重试，不尝试绕过限速。

归纳V3历史PoolCreated完整来源：Alchemy已确认部分10区块`eth_getLogs`并发现真实5月1日V3池；免费单请求≤10块，UTC 2025-07-01从`52440287`至`52555482`共**115196块**，如10块连续扫描至少**11520次**，与当前时间/免费资源预算不符，**本轮未执行该扫描**；Graph Gateway两不同子图403；PublicNode 2000块及10块均403；OnFinality两档429；BNB官方公共节点禁用`eth_getLogs`。上面都是**本会话实际尝试或明确文档限制**，没有一个源提供V3完整2025-07-01全天连续日志及受控可复验缺页证明。暂停无证据的免费RPC轮换和整日V3扫描，不寻找随机公共节点刷满速率；除非以后发现一个可信、合法免费、可连续回溯且有原始归档能力的来源才重开。**这只是当前源门禁阻断，不证明BSC V3市场空或任何历史没有可交易Token。**

按Monster既有Source stop，V3及launchpad母体为`UNKNOWN / COHORT_NOT_FORMED`。保留原冻结V2 30/30 identity、P0已有回执及相关UNKNOWN，不换赢家名单补齐。不提前固定用户交易金额、不启动P1/P2模型、G6继续NO_GO。后续有价值的主线仅限**原V2 30的PIT/双向执行来源和真实未达标原因整理**，而非为赚任务进度无限制造附属边界。P0`INSUFFICIENT_COVERAGE`，P1`BLOCKED`。

## 2026-10-20：Mac BSC V3 PublicNode 免费源探针59次调用，2,000/10块eth_getLogs均HTTP 403；停用该来源

用户在原分支固定SHA`b6219785e4f5b88222da7104648fd62e544c93e7`的现有`monster_early_venue_factory_rpc_roster_probe.py`前台运行`--chain bsc-v3 --day 2025-07-01 --mode probe --max-requests 80 --delay 0.4`，结果`chain=bsc-v3`，RPC Host `bsc-rpc.publicnode.com`，RPC源URL摘要`474b7939233328340174d2967470a6a2e6951f51e119471ff7e51ea7eca54ee1`；全日UTC历史区块准确定位`52440287–52555482`，总59个RPC请求。Factory历史`PoolCreated`查日志两档都失败：块`52440287–52442286`的2000区块、块`52440287–52440296`的10区块均得到**`RPC_HTTP_403`**。这是RPC访问失败，不是零新池、零流动性或没有V3；HTTP 403未提供服务端body，不能断言源不支持方法的全部原因。继续同一来源重试或开始11万区块扫描没有收益，`V3_FULL_DAY=UNKNOWN`、`P0=INSUFFICIENT_COVERAGE`和`P1=BLOCKED`不变。

公开查询2026-10-20服务商文档得到另一个潜在合法免费源**OnFinality BNB public RPC `https://bnb.api.onfinality.io/public`**，服务商明确声称支持`eth_getLogs`和历史Archive，并列公共限流10请求/分钟，官方BNB文档亦提示其自身公用节点禁用`eth_getLogs`。这仅是**服务商文档证明，尚未Mac网络实际查询**，不能提前承诺支持2025-07-01历史日志或2000区块范围。优先在Mac直接对冻结历史块`52440287–52442286`和10区块短段分别发**一次小额前台只读RPC检查**，前置一次`eth_chainId=0x38`，避免再次用59次RPC重做日期二分。失败即停，不启动自动扫描、不购买API/套餐、不设钱包或交易，不修改原V2候选和研究金额。

## 2026-10-20：BSC V3三日期预登记小窗来源能力实际通过，首次原日志得到May1真实V3池

在独立固定Git登记 `36dab85ad9146f3cab3fe929de85d62527a7000d` 之后，使用现有Alchemy BNB-mainnet免费只读连接，定位三日UTC零点历史区块和上一块时间，严格只查询已登记每个日期起首10个连续块的V3 Factory `PoolCreated`：**2025-05-01块48876398–48876407：1条；2025-07-01块52440287–52440296：0条；2025-09-01块59581791–59581800：0条**，全部`eth_getLogs`返回成功且topic、地址正确。零仅证明该10块无事件，**绝不意味着该日不存在新V3池/能形成整日完整母体**，不能再以这种稀疏结果推进P1。2025-03-18公开已知的另外两笔V3 PoolCreated交易receipt与单区块logs一致，仅作**事后source正对照**，严禁与预登记三日期同分母混算。

新获得的预冻结时段链上May1事件：块`48876404`，Factory`0x0bfbcf9fa4f9c56b0f40a671ad40e0805a091865`，tx`0xdc17cf044b461178d0ba629239e9935c3a9c9d941e88848fab9c654479d7c2a4`，token0`0x6eb23a077490759e17a7e59fe1aee03f201814dd`，token1为WBNB，feeTier=10000（1%），tickSpacing=200，pool`0x96d37ca7626818c5a9e2a22d46606a3c5445578c`。在创建块以factory `getPool(token0,token1,10000)`独立读取Storage返回该pool，池同一tx真实事件 **Initialize、Mint**，pool `liquidity()`历史状态数值85730557630176831、`slot0()`历史价格状态可读；pool在该10块的所有log仅2个（Initialize/Mint），**没有Swap**。池部署/初始化/首加池和当时可双向卖出是不同层级，V3 `liquidity()`不能直接换成2 WBNB/1000 USDT的报价储备或真实用户可卖容量。本次Factory交易receipt因连接器约8KB输出上限截断，开头success和PoolCreated可见但完整receipt原字节未获得；所有调用仍由单一Alchemy规范化响应，无独立网络时间recv、无原HTTP SHA。两笔事后案例不能视为三日期的样本。

原脚本`local-agent/scripts/monster_early_venue_factory_rpc_roster_probe.py`**早已有`bsc-v3`配置及离线测试**，没有重复开发/新Stage/新付费服务。V3全天窗口预计远超30区块，当前免费Alchemy每次10块，单三个小窗不能计为V3全母体，也不能替代真正连续+缺页校验；Graph Gateway双子图403依然BLOCKED。本轮未采任何未来币价或钱包收益标签。实际结果逐块/逐事件保存在原P0 JSON `bsc_v3_p0_three_date_preregistered_alchemy_factory_log_pilot_results_20261020`；原V2冻结30未改、正式PIT和同一notional双向门槛仍NOT_SCORABLE。P0`INSUFFICIENT_COVERAGE`、P1`BLOCKED`、G6`NO_GO`不变。

## 2026-10-20：事前登记BSC V3来源检验三日期，避免选择性样本

先于本轮三日期V3目标日志读取，冻结UTC历史日期`2025-05-01`、`2025-07-01`、`2025-09-01`。对每一天以历史区块`timestamp`定位当天最初完整区块，**只读首10个连续区块**的PancakeSwap BSC V3 Factory `PoolCreated`事件（Factory `0x0bfbcf9fa4f9c56b0f40a671ad40e0805a091865`）；不读未来币价、不挑已知赢家，使用现有免费Alchemy 10区块上限。该任务仅确认三个预登记时点的来源读写/真实日志返回能力，不声明全日V3母体或零事件；数据与结果必须另一个commit记录，日期不得因结果难看而修改。已通过公开BscScan线索定位两笔2025-03-18 BSC V3 PoolCreated回执（后验**仅为Source positive control**），但与三日期随机母体不可混淆。现有`monster_early_venue_factory_rpc_roster_probe.py`源代码已经含`bsc-v3`选项，不创建重复脚本。P0、P1/G6门槛不变。

## 2026-10-20：用户Mac BNB官方公共RPC原响应与Alchemy原异常交易独立交叉核对通过（仅#7）

用户在Mac前台通过 `https://bsc-dataseed.bnbchain.org` 原生只读JSON-RPC分别请求`eth_chainId`、`eth_getTransactionReceipt`、`eth_getTransactionByHash`，贴回简要结果并保留**三份原始字节文件及SHA256**在私有目录`monster-p0-readonly-raw/bnb-official-check/20261020T082832Z-de07fa`。官方回报chainId`0x38`，交易`0xabd855e35df0feaeaa5c2df0edd964efb9ca8eda4b449749bc72fd08ccef827f`，区块`0x32033b0`，receipt status`0x1`，gasUsed`0xb53e`（46398），`effectiveGasPrice=0x0`，transaction `gasPrice=0x0`，Approval事件`data=0x00000000000000000000000010ed43c718714eb63d5aa57b78b54704e256024e`。**这些字段逐项与之前Alchemy现读一致**。三份用户报告的SHA：chainId `ce50ba55ecf1a9410c6f5503d09da66974203165305ff8f5a2b520f49a705c07`、receipt `aef83b6df4f891bf0b9398d7ffcc45d30c00ad08cae07197ed347edda6fd9dbd`、tx `19d10677d8c4e4d11494e9d85fb86cfc0a8799cddbe055308aa16ebe9233dd2a`。**原文件仅位于用户Mac，助手未读到其原始字节，也未独立重新计算SHA；三份hash属于用户提供的待复核来源证明**。

这**排除本例相关字段是Alchemy单一RPC解析错误**，确认同一Token合约Approval日志data编码Router地址而非calldata指定的max uint256；之前通过历史`allowance`验证过0→MAX。不能仅按标准ERC20的Approval事件金额重建此模板的allowance，正式功能要使用状态/交易输入进行判断并标记非标准事件。官方及Alchemy对**本例Approval**均返回0 effectiveGasPrice，按链上回执字段，该笔交易gasUsed×effectiveGasPrice=**0 wei**；这修正了“本例zero gas字段只是Alchemy源异常不能采信”的先前不确定性。**并未独立核实其余三笔Approval的官方返回、四币BUY/SELL真实全部费用、外部赞助/其他成本、钱包净PnL或用户可获得的网络时点**。#7此前池侧毛差为负这一事实仍成立，不能把零授权Gas推断为整体盈利。相同1346字节模板9币不能由一笔事件假定所有成员或所有日期一致，也不是同一控制者证明。

仅更新原P0一份JSON与一份MD，不新增Stage/新策略/盲目补边界。源交叉检查为一笔交易、非完整P0来源覆盖：`P0=INSUFFICIENT_COVERAGE`、完整PIT及统一金额双向`NOT_SCORABLE`、`P1=BLOCKED`、`G6=NO_GO`。无需付费、合并、部署、交易或改生产。

## 2026-10-20：原30币历史runtime字节码完整度25/30、至少两组完全相同的合约模板

本轮从**冻结的原2025-07-01 BSC PancakeSwap V2首30币**逐rank读取历史`eth_getCode`，先使用已在4笔Approval案例中的同一1346字节Token源码作**准确整串字节比对**：rank **7/9/11/12/19/21/25/27/30共9币完全相同**（模板A）；另外rank **2/3/6/10共4币**拥有完全相同3553字节runtime（模板B），与模板A不同。另12币均不同于A/B，**未断言这12币互不相同**。rank **8/18/20/26/28**因Alchemy连接器向当前对话截断`eth_getCode`长输出（约8000字符）无法核对完整字节码，属于`UNREADABLE`而不是合约代码不存在。30个Token身份仍逐一保留、没有事后剔币。完整rank、合约地址、历史完整块、高度、返回字节数及证据等级在**原单一P0 JSON**键`bsc_v2_p0_all30_historical_runtime_bytecode_family_exploration_20261020`。

尤其之前的**4笔同钱包Router BUY→Approval→SELL案例rank7/12/21/30全部同属模板A**。此前四笔Approval日志的data与其approve calldata最大值不一致，可能与这一共同runtime实现相关；但没有独立提供商确认交易或解析代码，**不得声称已经证明是哪一行合约代码导致，也不能声称Alchemy一定造假**。该4例只证明相同代码族曾出现的历史交易，不能据此得出4种独立代币卖出机制均已通过；字节码一致也**不等于同一实际控制者/一个项目/一个人/重复同一收益事件**。后续统计的15个独立可卖出10x正例仍需另外依据研究规则核实，并非当前合约族数量。

独立免费验证仍未达成：BscScan tx页面本环境403；Blockscout连接器提示2026-10-08起需要PRO key，不按用户禁止付费约束继续；公开搜索对#7 token能得到部分当前合约元数据，**不能当2025年原RPC收据交叉验证**。本轮没有现金支出、没有后验标签、没有改研究金额/池深/成功门槛，也没有新增Stage、新模型、部署、邮件或交易。P0 `INSUFFICIENT_COVERAGE`、P1 `BLOCKED`、G6`NO_GO`不变。

## 2026-10-20：四例真实Approval交易已定位，3笔Gas保本界限更新

本轮继续此前**已选定**的四个真实同钱包Router成功买卖样本#7/#12/#21/#30。对每个 Token/owner/router 在原买入与历史卖出前之间使用Alchemy BNB-mainnet历史`eth_call allowance`二分定位**相邻区块授权状态从0变uint256.max的边界**，再读取该单块Token事件日志并以实际`eth_getTransactionByHash`和`eth_getTransactionReceipt`核对。四笔均为同原持有人向原Token发出`0x095ea7b3 approve(router,uint256.max)`，状态`0x1`，GasUsed均**46,398**。只读验证不做批准/发交易。区块内真实Approval事件topic的owner/spender准确，但**四笔事件data均编码Router地址数值，和approve calldata最大额度冲突**。这是链上提供的数据源实际显示的冲突，依赖相邻块历史allowance变更与调用输入来确认授权结果；不得用此事件data宣称标准金额。也不能因为邻接块转变就断言这是钱包历史首次Approval，允许此前非单调授权变更。

#7 approval block 52442032, tx 0xabd855e35df0feaeaa5c2df0edd964efb9ca8eda4b449749bc72fd08ccef827f, approve-to-sell 3 blocks / 3s, 3tx GasUsed 328992, equal-gas break-even NO_POSITIVE_GROSS_POOL_QUOTE_MARGIN Gwei
#12 approval block 52443729, tx 0x3969503d3fba3cde5b973b10d60cdcfafda032028ce425c0a150eee409ee5f8b, approve-to-sell 2 blocks / 2s, 3tx GasUsed 328992, equal-gas break-even NO_POSITIVE_GROSS_POOL_QUOTE_MARGIN Gwei
#21 approval block 52445408, tx 0x34f6f9dec322597cd95a025840b10edb806294ff5c3973e26eaffd1defe312ca, approve-to-sell 28 blocks / 21s, 3tx GasUsed 328956, equal-gas break-even 14.364842 Gwei
#30 approval block 52448418, tx 0xe792353ad47ed0391be0b1890a66bc8b9198d8e1174d90ddd7be5bbaaa471c2d, approve-to-sell 3 blocks / 2s, 3tx GasUsed 328968, equal-gas break-even 14.254785 Gwei

在之前买+卖两笔GasUsed之外加入确证的Approval GasUsed，#21三笔合计328,956、#30三笔合计328,968。**只有假设三笔使用相等、非零但未知的GasPrice且无其他费/税时**，#21池侧正差的保本上界从约16.723649调整为`14.364842` Gwei，#30从16.595421调整为`14.254785` Gwei；#7/#12池侧差在任何非负手续费前已为负，不能变为正。四笔Approval交易GasPrice/effectiveGasPrice与旧八笔买卖一样都被同Alchemy接口报告为`0x0`，**实际支付Gas依然未核实**，不得记为免手续费。授权与卖出的链上时间差仅2、3、21、2秒，是历史块timestamp差，非当时用户可执行公共观察窗口。第三方BscScan网页版在本运行环境不可访问，尚无独立第二来源校验。逐笔txhash、原始十六进制状态、Gas和派生界限在**原有**P0 JSON键`bsc_v2_p0_four_actual_approval_transactions_and_three_tx_gas_break_even_20261020`。

本轮未冻结名义额，未做模型、没有真实交易、部署、邮件、持续监控、新脚本或重审历史测试；本轮只做业务链路的缺失审批取证及既有成本字段更新。P0`INSUFFICIENT_COVERAGE`，24/30 PIT、18/30同名义额双向门槛仍`NOT_SCORABLE`，P1`BLOCKED`，G6`NO_GO`。

## 2026-10-20：9 个原买入地址的真实历史余额、转回Pair模拟与Router授权来源核查

在原冻结30例中只选旧有回执证明存在“Token接收地址后来将Token卖回同池”的9例（7笔原接收金额整笔回池，2笔仅部分卖回）。使用既有已授权的Alchemy BNB mainnet连接，在对应**买入区块结束时**读取`balanceOf(owner)`、以当时余额和历史观察卖出Token数量做单次非持久`eth_call transfer(pair,amount)`，以及`allowance(owner,PancakeV2Router)`。之后对旧证据中4例明确经Pancake Router真实卖出的钱包，在对应卖出区块前一完整区块另查询allowance。共**31次成功的真实历史只读eth_call**：9/9余额足额、9/9直接Token转池的模拟返回ABI bool true（无状态改变）、9/9买入块末Router授权为0、4/4确证后续Router卖出的案例在卖出前一块已有max uint256足够额度。旧4例排名#7/#12/#21/#30。严格区分`transfer`和Router内部`transferFrom`，**成功的直接转账模拟不证明当时已可通过Router退出**；买后allowance 0意味着走标准Router卖出还需要授权状态发生变化，其Approval交易、Gas、等待时间没有查询。不能由后续交易成功反推该交易当时提前可执行。

8/9历史buy块末余额与该笔买入收到的Token相等，**#17买后余额277369498906744234958525580**，明显高于单笔买入`9567924680128822181663051`，说明地址已有其他同币头寸或当区块另有来源，随后部分卖出无法精确归属于这笔BUY。此点必须保留在同一钱包收益归因的边界。

所有返回是同一Alchemy提供商正规化RPC，不含独立原始HTTP来源哈希/当时公开网络recv；真实无链上交易发生。模拟不包含配对Pool的实际Swap、Router规则、Token转账税扣量、Gas费用、抢跑/MEV，也没有跨币统一研究订单金额或证明普通用户在信号时点可卖出。逐项地址、raw数量、买卖区块及不确定性已追加原P0 JSON单一键`bsc_v2_p0_nine_historic_holder_balance_transfer_and_router_allowance_20261020`。本次仅事实来源增量，未新增脚本或修改旧参数，P0 `INSUFFICIENT_COVERAGE`、P1 `BLOCKED`、G6 `NO_GO`均不变。

## 2026-10-20：4笔真实同EOA历史买卖的池侧WBNB回转及Gas保本上限，首次量化执行成本阻断

未额外查询链上，也未自定研究订单金额。仅从已有并交叉过字段的4例同一个EOA通过Pancake V2 Router真实买入、随后同一EOA卖出（Token原接收数额整笔回池）的历史回执，逐币按BigInt计算**原池报价资产流入(买)与流出(卖)差额**，以及两笔交易的GasUsed之和。四例的固定原始交易金额不同，仅属于历史个人成交，不是Monster研究的统一下单金额。所用WBNB“卖出回池释放”的报价不一定就是同EOA钱包最终可支配的BNB，不包括Router拆分、其他资金动作，故这只是**池侧资金流约束**，不宣称钱包真实盈利。

- #7 买0.012 WBNB，卖方池释放0.011940359843178181 WBNB，**池侧差−0.000059640156821819 WBNB**；两笔GasUsed合计282594，扣除任何非负Gas/额外费用后不可能将这一池侧负差变为正数（但不是完整钱包PnL审计）。
- #12 买0.25 WBNB，卖方池释放0.249547777402681631，**池侧差−0.000452222597318369 WBNB**；GasUsed合计282594，同样池侧负差。
- #21 买0.005 WBNB，卖方池释放0.009725401038080023，**池侧正差+0.004725401038080023 WBNB**；GasUsed合计282558，若两笔GasPrice完全相同且不存在其他费用，则用这两笔Gas保本的**假设GasPrice上限约16.723649 Gwei**。
- #30 买0.3 WBNB，卖方池释放0.304689368200754634，**池侧正差+0.004689368200754634 WBNB**；GasUsed合计282570，同样前提的**假设GasPrice上限约16.595421 Gwei**。

**真实Gas费用尚无法核实：**已有Alchemy规范化字段在这四个样本的8笔交易都报告`0x0` GasPrice，仓库已将此记录为源异常，不可按真实零费用或盈利证明处理；上限仅是一元敏感性不等式`buyGasUsed*buyGasPriceWei + sellGasUsed*sellGasPriceWei < grossPoolQuoteDiffWei`的演算，且忽略了额外Approval/TransferTax/其他钱包路径。逐笔原始整数、txhash、GasUsed、计算及所有UNKNOWN在原P0 JSON键 `bsc_v2_p0_four_actual_router_roundtrip_pool_quote_gas_budget_20261020`。验证目的为说明为何P0必须有准确Gas和同订单名义额；没有读未来收益标签、没有改冻结母体、没有模型和策略声称。P0正式门槛仍是24/30 PIT NOT_SCORABLE与18/30同金额双向 NOT_SCORABLE，P1 BLOCKED。

## 2026-10-20：P0历史买卖链路18例严格先后顺序再核对（无新RPC）

从24例首次池深达标后下一个完整区块仍具备双边储备的真实Alchemy回读，与先前已归档的后续BUY/SELL交易比对：冻结30样本中的**18个**满足`next_block_end < distinct BUY block < later successful SELL block`，并且原先的SELL回执池深达到冻结门槛。按Token实际接收/回池关系：**7个**同接收地址且原买入Token数量完整回池，**2个**同地址但只是观察到部分数量卖回（#16/#17），其余**9个**卖出来源并非相应买入Token接收方。这18例只说明历史真实交易的时间先后和存在的卖方，绝不可认定相同投资者18例都能获利退出。#3、#13的实际BUY距观察到的下一个区块状态只有一个区块的间隔；没有同期实际公共`available_at`，不能声称实时可跟入。

逐rank证据见原P0 JSON新键`bsc_v2_p0_next_block_to_later_real_buy_sell_chronology_20261020`。本次为原有证据确定性Join，**没有新RPC、代码、测试或费用**。P0 24/30完整PIT和18/30同一研究名义额双向买卖仍`NOT_SCORABLE`，P1`BLOCKED`。继续以首次真实可观察时点和用户可执行统一金额为未来验证标准。

## 2026-10-20：冻结V2样本的24个首次达标池，下一完整区块储备24/24仍达标（新真实只读核验）

本次采用已连接的免费Alchemy BNB mainnet，只读`eth_call`向**已冻结且曾观察到首次池深达标**的24个原PancakeSwap V2 Pair，在对应首次确认门槛区块`block+1`读取`getReserves()`（selector `0x0902f1ac`）。分4批、每批6个，**24/24 均成功**、池中Token储备大于零且报价侧储备仍达到原冻结阈值（2 WBNB或1000 USDT）。其中20个首次达标位于建池区块，4个是后来区块#14/#16/#17/#26。本次原始`reserve0/reserve1/blockTimestampLast`的报价侧/Token储备、池地址、查询块及当时阈值已逐项记录到同一P0 JSON键 `bsc_v2_p0_all24_next_block_reserve_source_read_20261020`，可复核原值。**注意getReserves第三值是最近一次Sync的blockTimestampLast，不是区块时间戳，也不能充当公开available_at。**

其余6个排名 **#5/#8/#15/#18/#20/#28** 没有此前确认的首次达标事件，故本轮不做“首达标+1块”检查，并保持在原30个样本分母；没有将它们定性为永远无池深或无法卖出。24个成功只能证明对应**下一完整区块末的历史池状态**，不能证明用户在当时接收过信息、可在指定订单名义额买卖、Token没有转账税、反卖限制、MEV/Gas以及真实净收益。返回来源为Alchemy连接器规范化RPC，不是本次取得独立原HTTP bytes，不能冒充新SHA归档或第二服务商一致性证明。

**P0正式24/30完整PIT仍NOT_SCORABLE，18/30统一名义额双向可卖仍NOT_SCORABLE，P1 BLOCKED，研究预算0美元。** 这项24/24不推动Phase验收，下一工作应检验事前冻结订单金额及历史Buy/Sell容量是否可独立证明，优先保留最小完整样本链，不重复已审交易回执。

## 2026-10-20：Graph 对照子图同样403，停止无证据的重复查询；Alchemy重核原V2样本

本次用户 Mac 前台手动运行原Branch HEAD `45e598d4`：11/11定向Python测试 **PASS**，仅出现模拟HTTPError资源释放`ResourceWarning`；随后独立 Graph Network 参考子图 `DZz4kDTdmzWLWsV373w2bSmoar3umKKH9y82SUKr5qmp` 唯一真实请求返回 `CONTROL_HTTP_DENIED`、**HTTP 403**。此前 Pancake V3 同一个Key也返回403；Security截图已确认任意Subgraph/Domain均允许。两次403的真实服务端 body 未保存，因此无法区分 Key本身、账户状态、Gateway政策或其他认证故障。The Graph Free官方文档提供每月100000次免费查询，不需要因此推断必须升级；当前Plan B Graph实际状态 `BLOCKED_HTTP403`。暂停以相同凭据重试相同请求，直到获得新根因证据。

转而使用已连接的 **Alchemy ChatGPT Crypto Monitor All Chains**，真实调用 `eth_getTransactionReceipt`、network `bnb-mainnet`，获得成功回执 `0x26396c2954f8f1ff36449d76454f0706c9cf1564da89b2a4a3f0fdfbac6744dc`。区块 52440324 的日志同时包含 Pancake V2 Factory `PairCreated`、对应 Pair `0x021d84d4d9f88518f74935c61e2cf4b70713bc16` 的 `Sync/Mint` 和真实 Token Transfer，证明历史交易原始链事实可以再次通过现有免费只读连接核查。但该交易属于原30币rank1，已在旧证据中记录，本次**仅交叉回读，无新增样本、无提升PIT、可卖覆盖或模型标签**。连接器返回的是标准化回执结果，不生成原HTTP bytes SHA256，不能冒充Mac raw归档。

下一步优先在已冻结30币内核实真实首次可观察时间的重建可行性、统一名义额双向历史执行成本及失败币保留，按原24/30和18/30门槛停止。V3全量母体依然未知，Graph免费权限未通过，P0 `INSUFFICIENT_COVERAGE`、P1 `BLOCKED`、G6 NO_GO，零付费、未部署、未交易。

## 2026-10-20：API Key Security 无白名单限制，提供一次性独立参考子图对照

用户 Graph Studio Security 截图直接显示 **Authorized Subgraphs: Any Subgraph** 与 **Authorized Domains: Any Domain**。因此可排除这两类当前配置的 whitelist 导致目标 Graph Gateway 403；Key 状态与 Free 账户授权仍未知。The Graph 官方文档明确支持 `Authorization: Bearer` 及现有 Gateway URL，无需盲目重建 Key 或转为 URL 内嵌 Key。目标 Pancake V3 子图 Explorer 显示久未更新，**但不能由此推断 403 具体原因**。

在同一个 `local-agent/mission_agent/early/graph_v3_source_probe.py` 新增手动 `--diagnose-control`：只对 Graph Network Arbitrum 官方参考子图 `DZz4kDTdmzWLWsV373w2bSmoar3umKKH9y82SUKr5qmp` 发**一次 POST `_meta`**，使用现有 Bearer Key，打印固定分类、成功时的区块高度及原响应 SHA256，不打印请求 URL、Key 或服务端失败 body。该参考子图 Explorer 近期更新，适合区分“同Key完全不能查询公开参考子图”和“仅目标BSC V3出错”。成功参考子图不会使 BSC V3 或 PIT 通过，任何失败也不能直接宣称 Key 无效。

原有目标 V3 `--live-one-query` 保持单请求原限制；未创建后台任务或重复扫描。新模式隔离环境以等价代码做了9个离线测试通过（含3个参考探针用例），**新远端提交的完整测试、Mac参考子图请求尚未执行**。最终P0仍 `INSUFFICIENT_COVERAGE`，P1 `BLOCKED`，零付费，NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE。

## 2026-10-20 Mac 复验：8/8 通过，真实 The Graph Gateway 返回 HTTP 403（源仍 BLOCKED）

用户提供的最新 Mac 终端截图（Python 3.14.7）：修订后的 Graph 探针 **8/8 单元测试 PASS**，测试输出包含由 mock HTTPError 清理产生的 ResourceWarning，不代表真实 Gateway 响应。随后唯一手动真实 Graph 请求返回 `GRAPH_HTTP_403_KEY_OR_ACCESS_DENIED`，HTTP 层确认收到拒绝答复；没有成功取得 `_meta` 或历史 V3 池，无法从 403 单独断言 API Key 无效、账户未开通、子图不可用或具体计费故障。当前代码在失败时丢弃原 HTTP body，故根因 **UNRESOLVED**。

The Graph 官方 [Managing API keys](https://thegraph.com/docs/en/subgraphs/providers/subgraph-studio/managing-api-keys/) 和 [Serving Queries](https://thegraph.com/docs/en/gateways/subgraphs/consumer-side/serving-queries/) 均支持 POST+Bearer；API Key 的 Security 可设置**域名白名单及子图访问范围**，均可能导致 403（还未取得用户账户设置证据）。下一步首先检查原 Key 的 Security（是否有限域名、是否只允许指定 Subgraph）、Active 状态及 Free Plan，而非再造 Key、修改正确的认证格式或购买付费额度。此轮只追查源门禁，保留 V2 冻结30池及无全覆盖、无公共 PIT、无统一交易金额的停门状态。P0 `INSUFFICIENT_COVERAGE`、P1 `BLOCKED`、G6 `NO_GO`，无模型训练、部署、邮件及交易。

## 2026-10-20：用户 Mac 首次 Graph 探针失败，已修正静默吞掉 HTTP 诊断问题

用户在本地隔离 worktree HEAD `3f6e2984` 前台执行原始 Graph 单次探针，终端实际返回 `GRAPH_NETWORK_OR_AUTH_FAILURE`；同期 Graph Studio 截图显示 `No queries yet`。旧脚本将 HTTP 401/403/402/404/429/5xx、DNS、TLS 和超时统一捕获成同一个错误，故**真实 HTTP 状态、是否到达 Gateway、是否为凭证错误均未知**，不得将它写成 key 不可用、历史子图不存在或历史无池。

已在固定代码提交 `947b1397234fe745b800d78c276a86828e714ea5` 修改同一来源探针错误分类，只输出不含 URL、body、API Key 的固定 HTTP/网络状态，新增针对 HTTP 拒绝/DNS 的两个离线单测。隔离 Python 环境对同等诊断逻辑的9个独立模拟案例 PASS，但**新提交的完整8个 Python unittest 尚未执行，新代码尚未经用户 Mac 重跑，真实 Graph API 请求未成功**。The Graph 官方文档支持现用的 Authorization: Bearer 格式，无证据要求改变 URL 或添加付费方案。

用户在聊天中粘贴了 Key，应在 Graph Studio 轮换；本 JSON/MD/PR 严禁记录密钥或其部分前缀。账户 Free Plan 有免费查询额度，若后续返回402不得付费重试。既有30个 V2 样本、24/30 PIT和18/30同金额门槛均未更改；P0 `INSUFFICIENT_COVERAGE`、P1 `BLOCKED` 保持。

## 2026-10-20：BSC V3 索引来源单次请求探针代码已提交，真实历史 GraphQL 仍未查询

- 官方 PancakeSwap BSC V3 子图 ID `Hv1GncLY5docZoGtXjo4kwbTvxm3MAhVZqBZE4sUT9eZ`；其官方开源 [lite BSC Factory 源配置](https://github.com/pancakeswap/pancake-subgraph/blob/master/subgraphs/exchange-v3/lite/subgraph.yaml) 起始区块 26956207，源码 [Pool schema](https://github.com/pancakeswap/pancake-subgraph/blob/master/subgraphs/exchange-v3/lite/schema.graphql) 定义创建块、创建时间、token0、token1、feeTier。**线上部署 schema 与 2025 完整索引覆盖尚未经过实际 API 核实。**
- 在既有 `local-agent/mission_agent/early/` 新增 `graph_v3_source_probe.py`，并在既有 tests 中增加 `test_graph_v3_source_probe.py`。由人手动前台执行时只允许 **1 个带环境变量 API Key 的官方 The Graph Gateway HTTPS POST**：读取 `_meta` 和 2025-07-01 UTC 指定区块区间内按创建块排序最多 5 个 pool；保存原响应和 SHA256，零分页、零交易、零部署，不含凭证。无 Key 不调用网络。
- 隔离 Python 环境按远端完整 Git blob 匹配执行离线 **6/6 PASS**，覆盖单 POST、无 Key 零请求、原响应SHA256、索引未到目标、空池、异常/错误响应；**尚未在 Mac 上运行新增代码，真实 The Graph API 请求次数 0**。本次无实际 V3 池身份入库，不宣称索引连续/完整、链上 Factory 回执交叉验证、当时公共可用时间或真实买卖容量。
- 既有 V2 30例及冻结条件原样，24/30 完整PIT = NOT_SCORABLE，18/30统一研究金额双向可交易 = NOT_SCORABLE。P0仍 INSUFFICIENT_COVERAGE，P1 BLOCKED，G6 NO_GO。The Graph Free API Key 需用户自行创建且确认 Free Plan；不得升级付费。没有在本次会话创建帐号或接受付费方案。


## 2026-10-20 P0来源路径再调查：V3存在官方免费查询候选，但当前尚不具备正式来源PASS

**目标**：直接解决`V2-only固定30币`不能代表BSC V3及launchpad的源覆盖问题。没有新建预测器、增加Stage、变更母体或擅自设研究下单额；此处只是`PLAN_B_SOURCE_DISCOVERY`，不是宣称已经拿到2025年V3完整原始数据。

**已查到的官方可复核候选**：
- PancakeSwap官方[Subgraph目录](https://developer.pancakeswap.finance/apis/subgraph)列出**BSC Exchange V3**对应The Graph [`Hv1GncLY5docZoGtXjo4kwbTvxm3MAhVZqBZE4sUT9eZ`](https://thegraph.com/explorer/subgraphs/Hv1GncLY5docZoGtXjo4kwbTvxm3MAhVZqBZE4sUT9eZ?chain=arbitrum-one&view=About)。子图面向Pool/Swap/流动性索引，可望避免在当前Alchemy免费`eth_getLogs`每10块的限制下整日遍历；**但不是原始链上全量日志，也不等于PoolCreated完整列表已验证**。
- The Graph官方[查询指引](https://thegraph.com/docs/en/subgraphs/querying/introduction/)明确**Free Plan 100,000次查询/月**，需在Studio申请API Key；[密钥管理文档](https://thegraph.com/docs/en/subgraphs/providers/subgraph-studio/managing-api-keys/)要求安全保存密钥，不能写入Git。**没有创建用户账户、没有获取授权Key、没有实际执行GraphQL查询、没有付费**，所以不能将免费额度或网页例子写成实际可用的数据出口。
- 该官方BSC V3子图的Explorer网页查询时显示**Indexing约74.5%**（网页进度快照，并非本轮用`_meta.block.number`实测）；历史2025-07-01目标区块是否已完整被索引、子图是否存在历史过滤和完整分页、原数据是否缺失，全部`UNVERIFIED`，不能凭索引进度认定指定旧日必缺失，也不能认为必完整。
- PancakeSwap官方目录给出的**BSC Exchange V2**来源为NodeReal Marketplace，不是上述The Graph V3子图；未经实测账号权限、可用免费额度和历史覆盖，不把其标为`V2_FREE_SOURCE_PASS`。
- [Routescan官方迁移文档](https://routescan.io/docs/getting-started/migrate-from-etherscan)列举支持迁移的Mainnet chainIds未包含BNB的**56**；虽然其[免密钥免费额度](https://routescan.io/docs/plans-and-limits/rate-limits)约为1万次/日，但**不应假定其免费API支持BNB**或基于不支持的chainId直接建适配器。Etherscan/BscScan的BNB历史日志当前免付费许可也未取得单次真实响应确认，不计作Plan A备份来源。

**精确下一次Proof，而不是直接开发采集器**：只有获得可用且`$0`的合法查询权限后，先向上述**固定官方V3子图**发**一次小样本只读GraphQL POST**，至少保存响应原始字节、响应SHA、`_meta.block.number`、实际成功/错误及一页时间过滤的2025-07-01 Pool `id/token0/token1/createdAtBlockNumber/feeTier`。不能把第一页当整日分母；仅当历史区块确实被索引、原CA/pool创建事实可逐Tx与其它RPC交叉核查、分页/缺页机制明确，再考虑有界获取整日候选。若Key不免费、要求开通付费订阅、旧区块缺失、索引/权限不满足，则记录具体`SOURCE_BLOCKED/INSUFFICIENT_COVERAGE`，**不购买、不猜测、不继续开发V3数据模块**。

**V3的不同物理执行模型是业务门槛**：V3使用tick/活跃流动性和feeTier，子图`Pool.liquidity`原始整数**不能当成V2 Pair的报价侧WBNB/USDT reserve**；V3是否真实能买、能按相同订单名义额卖出，必须有真实tick/报价/模拟及当时限制证据，不能把V2的2 WBNB/1000 USDT池深度直接照搬为V3的liquidity门槛，也不能把最近查询的索引数据倒填原`available_at`。研究额需合同审批并在读取未来收益标签前冻结。

**当前Plan判定**：`A=SOURCE_FEASIBLE_SCOPED_TO_FROZEN_V2_RECEIPTS_ONLY`、`B=V3_OFFICIAL_GRAPH_FREE_CANDIDATE_NOT_LIVE_TESTED`、`C=PAID_NOT_AUTHORIZED`、launchpad来源仍`NOT_ESTABLISHED`。不因找到了官网链接提高原24/30 PIT和18/30统一金额卖出Gate：二者仍`NOT_SCORABLE`，P0总体`INSUFFICIENT_COVERAGE`、P1 BLOCKED。机器化候选来源与停止条件见本P0主JSON`bsc_p0_v3_subgraph_free_source_screen_20261020`。

---

## P0 最新一页结论（2026-10-20）：按原验收合同报告可用性，不以刚好达标的数字代替PIT

**适用范围和结论**：原冻结`2025-07-01 UTC` BNB主网PancakeSwap V2 Factory**按原始时间顺序首30个quote池代币**，不包括BSC V3、其它launchpad或全BSC。用户Mac固定SHA `b783d154376b154d54b1e86f3b613300558ac05a`实测**38/38测试PASS**、18份真实卖出原始RPC收据在线19次调用全部核对PASS且本地离线**0 RPC**重放PASS。**子集链上来源可用：`SOURCE_FEASIBLE_SCOPED`；完整P0当前为`INSUFFICIENT_COVERAGE`，P1仍`BLOCKED`。** 这不是对已发现真实卖出的否定，而是坚持事前冻结的完整PIT和统一名义额门槛。

| 固定30币的指标 | 观察值 | 证据级别 | 是否构成原P0门禁通过 |
|---|---:|---|---|
| 固定Factory顺序身份、PairCreated | **30/30** | 旧Mac 88份原始RPC重放；未删浅池/死池 | 身份通过，但不能算完整PIT |
| 代币历史runtime-code非空 | **30/30** | 26例当天首次有代码状态、4例当天前已存在；**创建Tx仍不确定** | **不能**等同部署交易+来源可观察时点 |
| 建池原Tx时流动性同步Mint+Sync | **25/30** | 真实历史链上事件 | 未达标时不排除后续注资 |
| 建池时quote侧≥冻结研究门槛 | **20/30** | 2 WBNB或1000 USDT只是**池深度，不是购买金额** | 仅报价储备事实 |
| 建池后进一步确证越过报价侧门槛 | **4例：#14/#16/#17/#26** | 实际延迟Mint/Sync；#16/#17同Tx原子循环买入不算外部入场 | 仅补充历史深度事实 |
| 至少一次观察达到研究流动性下限 | **24/30** | 20建池+4延迟；其它6例#5/#8/#15/#18/#20/#28仅`UNVERIFIED` | **不是原24/30完整PIT验收** |
| 真实可在注资交易结束后独立买入（已观察） | **22/30** | 原20笔后续块真实买入+ #16/#17后续独立成功买入；不同金额、未验证实时送达 | **不是全母体可在T_entry买** |
| 后续真实`SELL Swap`且卖前深度达门槛 | **18/30** | 所选18笔Mac原始收据、交易内Token入Pool、quote出Pool、Sync+Swap可重放 | **不是原18/30统一订单额双向可执行门禁** |
| 先前历史买入实际收币地址又回流**恰好相同token数量** | **7例、5个不同收币地址** | #3/#7/#12/#13/#21/#23/#30，后验存在性 | 交易额不一致，不能报真实策略胜率/盈利 |
| 24/30部署+首池PIT及可追溯`available_at` | **`NOT_SCORABLE`** | 真实公众收到数据的时钟与准确部署Tx尚缺；不能把事后查询当实时 | **NO** |
| 18/30统一研究`notional`双向卖出容量、税费/真实Gas | **`NOT_SCORABLE`** | 从未在看结果前冻结统一订单额；部分历史Gas字段异常报告0，不代表免费 | **NO** |

**时钟纪律**：每个已观察流动性达到门槛的`chain_event_at=block`可以给出保守的`first_confirmed_block+1`作为**已完成区块状态开始可供后续区块评估的最早参考点**，但只是`NEXT_BLOCK_REFERENCE_ONLY`，**不是当时真实`available_at`、不是已批准的`HISTORICAL_BLOCK_DELAY_ASSUMPTION`、更不是`T_entry`**。本次不生成`PIT_VERIFIED`、不从以后真实交易反选过去的研究订单量，也不重排原Factory前30。逐rank证据矩阵见本P0 JSON顶层`bsc_v2_p0_current_frozen30_p0_gate_matrix_20261020.rows`（含真实CA/Pair/创建块、首次深度块、下一块参考、真实买卖证据及PIT缺失），不用另建Stage或模块。

**Plan A/B/C实测状态**：Plan A对本次**单日/单BSC V2 Factory/所选18笔收据**的本地历史只读重放有效；**尚未完成3个非连续日期的整日无缺页Source、BSC V3和launchpad范围，不等于整个BSC免费历史源已通过**。当前已连接免费Alchemy`eth_getLogs`最多10块的限制，不支持以少量窄窗代替一天约115196个区块的完整日志覆盖；其它Mac RPC可能不同，须以其真实回执为准。Plan B完整BSC历史批量导出免费许可和真实覆盖**未确立**；Plan C**$0、不授权付费采购**。历史第三方来源重放的SHA保证本机文件未篡改，**不能单独证明上游从未漏日志**。

**Plan A当前已证实的资源瓶颈（不是“查询不到市场数据”）**：已冻结BSC 2025-07-01整天区块`[52440287,52555482]`共**115196块**；对目前已连接的Alchemy免费层`eth_getLogs`最多10块/次的已见限制，**一个Factory整日无跳块日志至少需11520次请求**，同日Pancake V2与V3两个Factory至少**23040次**，且尚未包括失败重试、链ID、日志校验、其它launchpad或3个非连续研究日期。原脚本默认每次250请求，仅一个Factory/天的理论最低调用量就为**46.08倍预算**。因此不应在这个免费10块限制的同一提供商上继续无意义的大批量逐块扫描；这是`PLAN_A_CONNECTED_ALCHEMY_CURRENT_BUDGET_INFEASIBLE_FOR_FULL_DAY`，**不否定用户Mac另一个有合法免费大区间日志权限的RPC**，更不能将这一天的Factory V2存储索引成功误写成V3/launchpad历史完整覆盖。机器预算明细见主JSON矩阵的`historical_source_log_budget_limit`。

**止损与当前研发决策**：截至2026-10-20，当前结果是`P0 PARTIAL / OVERALL INSUFFICIENT_COVERAGE`，这不是提前永久停止；仍遵守原2026-11-02来源核查窗口、最多2次一次性CI的限制。下一投入只针对真正改变门禁的事实：①免费连续V2/V3/launchpad历史日志是否存在合规且可在预算内重复取得的实际路径及缺页计数；②完整PIT中`available_at`与部署Tx缺口；③**在预注册统一研究notional后**才能从固定30币进行同额买卖和成本压力试验，否则明确`NOT_SCORABLE`。不能再为了把18变成PASS，继续反复扫描同18笔已通过的卖单；不把6个未证深度币删除分母。`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`，PR保持Draft。

---

## 2026-10-20 Mac实际验收完成：38/38测试，18份真实卖出原RPC回执已落地，0 RPC离线重放通过

**验收代码固定SHA** `b783d154376b154d54b1e86f3b613300558ac05a`。用户在macOS zsh前台执行`git pull --ff-only`从`3e897bf`到上述SHA；两个原测试文件分别 **18/18 PASS** 与 **20/20 PASS**，合计 **38/38 PASS**。其中新增两项真实卖出源验证测试均`ok`，但它们的fixture仍是合成收据；真实历史来源证明来自随后的实际RPC调用及本地raw文件。

同次`--mode sell-archive`明确输出（受限范围`bsc-v2`、固定2025-07-01原始冻结30例中预选的18个**深度达标真实卖出**）：

- `status=HISTORICAL_18_REAL_SELL_RECEIPTS_ARCHIVED_AND_OFFLINE_REPLAYED`；`rank_count=18`；`matched_real_sell_tx=18`，`raw_receipt_hashes_verified=true`，在线`requests_this_invocation=19`（1次chainId + 18笔Tx收据）。
- 紧接着`--mode sell-audit`从Mac已保存**原始JSON-RPC响应**离线运行，仍输出上述相同status与`matched_real_sell_tx=18`、`raw_receipt_hashes_verified=true`，且`requests_this_invocation=0`。
- 观察到**卖出回执报告`effectiveGasPrice=0x0`**的rank是`[7,11,12,21,25,30]`。这一字段为数据源的真实返回值，不代表零Gas、补贴或净收益为正。其他12笔的Gas字段值没有随本次终端摘要传入，不做“确定非零”断言。
- 本验收数据来自**用户粘贴的Mac终端结果**。这证明**用户本机**实际执行了在线采集/完整本地离线核验；聊天内**没有独立读到这18份raw字节或manifest原SHA**，也不知道用户Mac端点和先前Alchemy端点是否独立供应商，因此不写`INDEPENDENT_SECOND_PROVIDER_PASS`。原文在Mac私有`~/monster-p0-readonly-raw/bsc-v2-2025-07-01/v2_p0_real_sell_receipts/`，不能上传包含私有RPC信息的请求/端点URL。

**分层进度判定（防止整数碰巧等于研究门槛而错误晋级）：**

| 判定对象 | 现在可证明 | 还不能证明 |
|---|---|---|
| 原30币中的18笔所选历史卖出收据 | **PASS：18/18有界原RPC归档 + 完整交易/Pool Sync/Swap/Transfer/售前reserve本地重放，38/38代码测试** | 不是其余12币全部历史交易覆盖；不是全市场/全时间事件无漏 |
| 原冻结24/30完整PIT覆盖 | **`NOT_SCORABLE`** | `chain_event_at`不等于当时公网可查询`available_at`；缺连续窗口及其它Venue V3/launchpad实际来源证据 |
| 原冻结18/30统一研究订单金额双向执行 | **`NOT_SCORABLE`** | 18笔实际成交名义金额互不一致；未预冻结同一个notional、历史限制/税费/完整退出规则，不能拿pool depth 2 WBNB/1000 USDT冒充订单金额 |
| 原币种总体研究实用性/P1 | **`P0 PARTIAL / OVERALL INSUFFICIENT_COVERAGE`（当前阶段诊断，非放弃研究）** | 仍需事先冻结时间延迟假设（只能标`RECONSTRUCTED`）、有界同额买卖容量及真实来源完整度；不得从本轮把交易存在性与策略利润混为一谈 |

**研发下一步**：不再重跑这18个卖出回执、不新建Stage；只做预先可评分的研究订单金额/时间与缺失分母说明，审查此BSC V2-only样本能否满足原24/30与18/30，不足则按架构合同正式输出`INSUFFICIENT_COVERAGE`而不是无限补无关边界。冻结母体30例、命名/权限、原有2026-11-02 source probe停止界限均未修改。当前仅向P0结果进度报告记入真实验收，**未改动验收代码、未运行CI、未合并部署和下单**。

---

## 2026-10-20 P0真实卖出来源档案与Gas来源异常：有界18份原HTTP回执，待Mac独立离线验收

**为什么继续这一步**：既有事实已包括30例冻结母体、18例达到历史深度地板的真实token→quote成功卖出，且已有7例与原买入收币地址及数量匹配的完整token退出。但原先18例的转账/Swap/Sync与卖出前报价池储备主要通过同一个Alchemy app标准化历史查询，本次聊天**尚未取得和永久审计原始JSON-RPC字节**。即使18这个整数等于旧覆盖门槛，**不等于P0已过18/30的相同研究名义金额真实可卖出验收**。时钟`available_at`、统一研究订单规模、合约限制和费用继续缺口。

对四个真实同地址EOA Router直连双腿（rank **#7/#12/#21/#30**）用当前连接的Alchemy BNB节点重新分别读`eth_getTransactionByHash`和`eth_getTransactionReceipt`（共8笔）：每例买入`0x7ff36ab5`和卖出`0x18cbafe5`均由原token收币地址发起、状态成功。Gas消耗并非0：
- #7 买入`165146` gas / 卖出`117448`；
- #12 `165066 / 117528`；
- #21 `165134 / 117424`；
- #30 `165054 / 117516`。

但当前响应中这8笔的`eth_getTransactionByHash.gasPrice`和`eth_getTransactionReceipt.effectiveGasPrice`**全部为`0x0`**；这一极端一致字段目前**独立源无法复核**，不能用`gasUsed×0`得出`ZERO_GAS`或据此给出任何费后净利润。既有浏览器读取BscScan具体历史Tx失败，未进行第二数据提供商独立gas交叉。若Mac独立RPC给出非零`effectiveGasPrice`，应以完整原始字节/哈希保存其差异，先解决来源差异，再谈净收益。原完整历史账本还需要授权费用、BNB原生转账和税费，不得只凭Router输入输出计算真实费后结果。

**已提交但尚未Mac实测的最小来源强化代码**：只扩展既有`local-agent/scripts/monster_early_venue_factory_rpc_roster_probe.py`，不创建第二统计框架或新Stage。
- `--mode sell-archive`仅用于预冻结`bsc-v2/2025-07-01`和P0证据JSON中已经归档的**18个不同rank原真实卖出tx**（16个原20候选中深度达标卖出+延迟LP#16/#17），手动显式填历史HTTPS RPC，`eth_chainId`验证+最多18次`eth_getTransactionReceipt`，**单次最多19 RPC请求**；不会调用`eth_getLogs`历史区块扫描，不需要付费API，不查询钱包余额、签名、发邮件、交易或启动后台。
- 严格重算每个Receipt的pool地址、固定token与quote、block+txhash、成功状态、交易内`Sync→Swap`和确切token/quote`Transfer` raw、卖出前池quote reserve与原P0已存记录是否一致。不接受转账到错池、浅池、失败回执、缺源或更改rank、重复rank的乐观PASS。
- 把真实API回应的**原HTTP/RPC字节**保存在Mac原私有`monster-p0-readonly-raw/bsc-v2-2025-07-01/v2_p0_real_sell_receipts/<SHA256_of_endpoint>/rank_N.rpc.json`，不上传Git、不显示含密钥URL。完成18份后才创建本机`v2_p0_real_sell_receipt_manifest.json`（raw长度、SHA256、身份与来源指纹）；
- `--mode sell-audit`**完全离线**复核上述18份原字节/清单哈希、交易回执的Pool Swap+Sync+ERC20 Transfer；源丢失、原文件更改、SHA不一致必须fail closed。不替用户改变原本18/30的模型门禁。
- 新增两个纯合成fixture单元测试，覆盖18固定真实Tx身份与合成成功receipt、错转账/错tx和档案SHA突变；需在Mac执行才能声称PASS。前一个固定SHA`3e897bfe89a54f3945dc51df70076eaa13cbc4b4`的36/36不能自动移植到本次Python改动。未使用/不消耗原仓库最多2次手动CI预算。

**主线止损与结果解释**：若Mac独立历史RPC不支持`eth_getTransactionReceipt`完整原件或真实18例反算不符，必须记录`SOURCE_BLOCKED / INSUFFICIENT_COVERAGE`与具体rank，不为凑18放宽条件；如果18份全部通过，只批准**指定历史真实卖出存在性+原响应可复核**，不批准统一研究订单名义额退出、历史`available_at`或盈利模型。原冻结研究到**2026-11-02**的源探针停止界限、BSC V2-only小样本外推限制、`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`不变。

---

## 2026-10-20 冻结#16/#17已获首次注池之后的真实独立买入与同收币地址部分卖出，历史达标卖出样本由16提升至18

原Mac 36/36离线回放显示#16/#17在块52444232初次流动性注入`Mint`同一TX内分别有65/64次Swap日志；它们**不是可由外部交易者见到注池后响应的129笔买单**。此前仅额外核查随后52444233–52444242十块确为0次Swap，属于特定短窗缺口，不代表之后没交易。

本轮为了找可实际响应的入场路径，仍只用已存在的免费Alchemy BNB-mainnet只读索引，按照**冻结CA+原Pool**，筛该注资块以后的候选token `Transfer(Pool→buyer)`（排序升序、受索引完整性约束），再读取明确TX的原`Swap/Sync/Transfer`收据：

| rank | 原注池/原子交易块 | 外部独立买入块与交易 | 实际quote买入 | 买入前quote reserve | 同收币地址的后续部分卖出 | 卖出前quote reserve |
|---|---:|---|---:|---:|---|---:|
| **#16** | 52444232 | **52444260**, `0x70acb21599d8683113e29a34c1538515a5cd3d878b3a2bef95607514781fee52` | **0.3478 WBNB** | **9.6000278 WBNB** | 块**52445123**，`0x800b881d4fa835eaee2f536ca719e7639721e42d376c9660306d65c36b9c0112`，卖出原买入token数量的约**63.02%**，Pool付出**0.231910983740920204 WBNB** | **10.1938278 WBNB** |
| **#17** | 52444232 | **52444318**, `0x72c611659af9e886bd00b4fbd16473a3c8af0783de6662d1b28b9ccbcd4681a6` | **0.6721 WBNB** | **20.2000287 WBNB** | 块**52444729**，`0x349a4c278ffcee0be6bf34ea7309d0b203dfe3dd85194ec4732b4c3ad150d484`，卖出原买入token数量的约**95.99%**，Pool付出**0.805634283621267362 WBNB** | **23.4122287 WBNB** |

#16真实外部买入token从Pair转到`0x2e3102bef68f6d8ac51ccc19c0df3970201ef88f`，后来该地址把`9178033000000000000000000` raw token实际转回原Pair。#17真实买入收币地址`0x60473ee37f303518c202c98d03afdd1b9baba274`，后续同地址转回`9184589000000000000000000` raw；两例均经成功receipt `status=0x1`、token `Transfer`与Pair `Swap` raw整数逐一对应，并有WBNB实际从原Pool转出。卖出路由涉及其它收款地址，**最终本地钱包实得原生BNB金额、Gas以及税负不可擅自认定**。因只卖出了部分买入token，报价出入金额**不能当完整仓位收益**。

**新P0事实覆盖**：原冻结2025-07-01 30个不同token中，当前已有**18个rank**找到**之后区块真实成功的token→quote卖出，且这一次成交前原Pool quote储备满足冻结2 WBNB/1000 USDT下限**，具体rank #1/#3/#4/#7/#9/#11/#12/#13/#16/#17/#19/#21/#23/#24/#25/#27/#29/#30。其他12例**不标为不能卖**：已知#2/#6/#10/#22首份索引卖出时深度低于阈值；余#5/#8/#14/#15/#18/#20/#26/#28的后续完整历史仍不能评分。**达到18个实际历史卖出“存在性”案例≠原Gate18/30通过**：冻结Gate要求具备首次可公开观察的PIT、当时买入可执行及同一时点量级/费用下可模拟双向条件；本轮买卖是过去发生在不同时间、不同名义金额且并非一致退出时刻的真实交易，不能用恰好18这个整数强行晋级P1。

本轮没有变更Python代码；现存Mac固定SHA`3e897bfe89a54f3945dc51df70076eaa13cbc4b4`的36/36历史测试仍只属于对应代码。新增的是链上只读证据摘要，原HTTP字节未由第三方独立保存/复查，原先已有88份本地归档仍保留。唯一机器结果写回本P0主JSON键`bsc_v2_p0_ranks16_17_post_atomic_distinct_buy_and_partial_sell_pilot_20261020`，无平行Stage、无买卖或部署行为。基线历史PIT`24/30`、统一名义额买卖`18/30`继续为`NOT_SCORABLE`；当前最重要剩余阻断是时间可用性`available_at`和研究订单名义额/费税等价的非后验来源。

---

## 2026-10-20 P0真实同地址历史双向退出核查：7个同额回流案例，仅5个不同收币地址

**主线实证层级提升，不调整冻结准入和买入数量。** 继20例真实后续卖出确证，重新由这20个上传历史买入交易的原`eth_getTransactionReceipt`逐一提取**原始Pool->token实际收币地址与token raw到账量**，对照先前各币首笔索引卖出成功receipt中的`Transfer(Token sender->Pool)`和`Swap(tokenIn,quoteOut)`。原始链上回执都是现有Alchemy BNB只读归一化RPC（`20/20 status=0x1`）；本次**原HTTP响应字节没有保存到Mac私有原始归档**，不能把本报告当独立供应商SHA回放。

| 20个冻结rank中真实首笔索引卖出归属分类 | rank | 数量 | 可以下的结论 |
|---|---|---:|---|
| **原收币地址同一、卖回原池token raw恰好等于观察到的那次原买入到账量** | **3, 7, 12, 13, 21, 23, 30** | **7** | 这7条有真实相同token名义数量的历史两腿正例；并且该次卖出quote储备均达到原冻结深度地板，但**不是统一研究订单名义金额或纸面净利润** |
| **原收币地址同一，但首次索引卖出token数量比本轮观察买入到账量更大** | 2, 6, 10, 22 | 4 | 确认此地址后来曾卖出，但**不能把全笔卖出quoteOut分配为本次买入的收益或同额退出证据**；这4笔卖出当时quote深度也低于原地板 |
| **卖出token转入原池的地址与本次观察买入的实际收币地址不同** | 1, 4, 9, 11, 19, 24, 25, 27, 29 | 9 | 能证实此币有交易者实际卖出，**不能证实本轮买入持币人退出**，也不能据此推断人人可卖 |

7个数量完全吻合的历史报价资产两腿金额对照如下，**是池子quote实际投入与流出之比，不包括Gas、批准交易费用、其它路由/钱包资金流或该地址其它持仓变化**：

| rank | 买入投入WBNB | 卖出时Pool付出的WBNB | quote两腿变化（非净利润） | 已验证金额匹配 |
|---|---:|---:|---:|---|
| #3 | 0.0011 | 0.001347005350 | +22.46% | 收币/卖币/报价收币地址相同，但卖出Tx由第三方合约地址发起 |
| #7 | 0.012 | 0.011940359843 | −0.50% | 同地址Router调用卖出 |
| #12 | 0.25 | 0.249547777403 | −0.18% | 同地址Router调用卖出 |
| #13 | 0.0011 | 0.001383378402 | +25.76% | 收币/卖币/报价收币地址相同，卖出Tx由第三方合约地址发起 |
| #21 | 0.005 | 0.009725401038 | +94.51% | 原同地址Router卖单，`swapExactTokensForETH`的`to`参数为本地址 |
| #23 | 0.0011 | 0.001376362549 | +25.12% | 收币/卖币/报价收币地址相同，卖出Tx由第三方合约地址发起 |
| #30 | 0.3 | 0.304689368201 | +1.56% | 原同地址Router卖单，`swapExactTokensForETH`的`to`参数为本地址 |

**去独立性：上述7个token实验只涉及5个不同的token收币地址**：#3/#13/#23均为`0x7347a30460516c8451687d9b1fc61efec6f8dae6`。这些地址是否为同一人控制、合约代执行还是关联集群不推测，更不能把其中5条报价两腿正收益当5个独立的模型盈利标签。历史用户恰好做过一笔回收并不表示事前公开可观察时点`T_entry`已经满足、可以在当时用同样的订单成交、或特定退出策略能抓住此价。

数据在原P0唯一机器JSON`bsc_v2_p0_uploaded20_actual_buy_and_indexed_real_sell_replay_20261020`的20行`case_results`中增补`historical_buy_receipt_token_transfer_receiver`、`first_indexed_sell_transfer_token_sender`、数量、三档`first_sell_vs_buy_recipient_evidence_class`及去重汇总。**本次不新建Stage/单独指标表/运行时交易模块**。

**停止边界和下一步**：至此已拿到池买入的20笔真实成功交易、20币各1笔真实卖出、16个卖出时已达流动性地板、7个同地址数量完全相同的历史回流；但**30币完整PIT和用户尚未审批的研究统一名义金额，仍不满足24/30和18/30**。应优先使用现有数据说明历史同额能否买卖及来源覆盖，最后**正式作P0的SOURCE_FEASIBLE / INSUFFICIENT_COVERAGE判定**；不能继续不停制造新Stage或把当前事后回顾收益伪装成前向Monster信号。现行`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`继续执行。

---

## 2026-10-20 实际买卖链上证据推进：20例独立候选全部找到后续成功卖出，16例卖出前深度达标

**新增实证来源与重要口径改变。** 用户上传了Mac离线产物`v2_p0_20_later_block_buy_candidates.json`（本轮实际文件原字节SHA256 `c4fc4e30c4e1e670b5a339dc25951cc27831b63c36a68436396967d5fde8a4a5`，5495 bytes）。逐条对照原冻结Pancake V2 Factory30成员、20个唯一rank、20笔唯一买入TX、买入块严格晚于建池块、买入时的原冻结报价侧池深度下限：**20/20身份和时间/流动性标注一致**。全部20个rank的旧短窗阶段前身已经有`Swap+Sync`，但不能把`first_observed`写成全历史首次可公共反应的`T_entry`。

使用用户已连接且可用的免费Alchemy BNB-mainnet只读端点（无需API升级）完成**两个相互补强但非独立供应商**的历史事实查询：

1. 对上传的20个确定买入TX读历史`eth_getTransactionReceipt`：**20/20状态`0x1`**。此前#1/#2/#3以及本次#4/#7/#12/#25另有原池WBNB/USDT实际转入、候选代币从池实际转出、Pair Swap数量逐原始整数匹配的闭环抽查；其他13笔首先确认回执status，不能把所有20笔均写成已逐条核对原ERC20买入Transfer。
2. 对**每个冻结token CA + 对应原Pair地址**，用Alchemy已索引的`getAssetTransfers(category=erc20,toAddress=pair,contractAddresses=[token],fromBlock=买入区块,order=asc,maxCount=2)`取得**买入后至少一笔代币真实转回原池的Tx**，再读取每笔首次索引回流的原始`eth_getTransactionReceipt`。**20/20**有成功`status=0x1`、该Pool真实`Swap`、该候选Token的`Transfer(sender→pair)`、报价Token的`Transfer(pair→router/recipient)`，两种资产的转账raw分别与同笔Swap的`tokenIn/quoteOut`逐整数匹配。并以该笔交易的Pair`Sync`反推**当笔卖出之前**quote reserve，非用事后某个OHLC高点。这**是实际市场中存在的卖出，不是单纯看到有人将代币转入池子**；但被观察到的卖方不一定是上传的买方。
3. 上述**20笔各自第一笔索引后续真实卖出中，16笔卖出前quote reserve达到原冻结的`2 WBNB`（rank#1为`1000 USDT`）研究地板**：#1/#3/#4/#7/#9/#11/#12/#13/#19/#21/#23/#24/#25/#27/#29/#30。**4笔低于门槛**：#2/#6/#10/#22，其中报价余额接近dust，不能与较早达标买入的储备混算或宣布可承受同额退出。研究池门槛不是用户下单金额。各20例的真实买卖Tx、block、原始Token实际入池/quote实际转出数量、当笔卖出前的reserve和是否达门槛均记录在本P0唯一JSON主文件的`bsc_v2_p0_uploaded20_actual_buy_and_indexed_real_sell_replay_20261020.case_results`，未创建平行新Stage/多余成果文件。

**三条同收币地址、同购买Token原始数量实际回流的闭环样例（均卖出前过冻结流动性门槛）**，只计算池quote侧两腿流入与流出，不计Gas、授权、其它资产跨钱包出入及交易服务成本：

| 冻结rank | 买入真实quote | 对应原token全部回流数量 | 成功卖出池quoteOut | 两腿quote变化，非净利润 | 交易细节 |
|---|---:|---|---:|---:|---|
| #3 | 0.0011 WBNB | `122279179504473913187874` raw | 0.001347005349558909 WBNB | **+22.46%（费前金额）** | 买方token收币地址与后续卖出tokenFrom和报价收币地址均`0x7347a30460516c8451687d9b1fc61efec6f8dae6`；实际卖出Tx发起人是**另一地址**，不可冒称同一EOA执行 |
| #7 | 0.012 WBNB | `476518429758317` raw | 0.011940359843178181 WBNB | **−0.50%（费前金额）** | 同一钱包于Router执行后续`swapExactTokensForETH`；WBNB从Pool进Router，最终native输出由成功路由器调用支持 |
| #12 | 0.25 WBNB | `987648209114086` raw | 0.249547777402681631 WBNB | **−0.18%（费前金额）** | 同一钱包直接从Router买入并通过Router `swapExactTokensForETH`卖出，卖出手续费及批准的完整Gas口径未核实 |

#7/#12的卖单函数选择器为`0x18cbafe5`，且成功receipt；#3卖出TX选择器`0xfe061fbb`、由第三方发起，实际原Pair报价Token直接转向同原Token收币地址。以上均为**单笔历史参与者的结果，不得当作策略在当时公众可用时点赚到该收益**。查询来自同一Alchemy供应商的标准化索引+RPC，非第二家独立交叉提供商；本次没有把原HTTP bytes采集为不可变Git原始证据，不能声称已核验源哈希保真。

**P0门禁不升档。** 此轮明显改变了旧结论“已存建池短窗口达标卖出0个”：那只是**非连续短窗口范围**，并非历史事实全貌；现用定向索引查到了20例真实后续卖出和16笔足量报价储备下的实际卖出。然而原冻结`24/30完整PIT`、`18/30统一研究金额的双向可模拟卖出覆盖`仍`NOT_SCORABLE`：离线公开实时`available_at`/税费/卖出Router限额/买入后连续源覆盖/90天完整退出规则/统一事先冻结的研究notional未闭环；另外10个冻结母体成员不能从分母删除。下一阶段优先**确认完整30例在冻结金额条件下的来源与交易容量是否可评分**，真实费后回测再决定P1，而不是继续机械增加买卖TX样本或用这三笔历史交易随意推销盈利能力。PR #30始终Draft，`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`。

---

## 2026-10-20 全量冻结30例独立成交口径确认，锁定20例下一阶段买入样本

用户上传的Mac命令行文本明确确认：固定SHA `3e897bfe89a54f3945dc51df70076eaa13cbc4b4`、原两组离线测试18/18+18/18=**36/36 PASS**；离线复用原88份历史RPC归档，30/30建池身份与25/30原建池同Tx注资验证仍通过。`observed_swap_activity_distinct_transactions_by_rank`对全部30行输出，其中**26个样本在已存有限窗口存在Swap，4例#14/#18/#20/#26未见Swap**（不等于无交易，#18/#20后续窗口缺失）。

| 旧保存窗口实际记录指标 | 结果 | 对业务的含义 |
|---|---:|---|
| 买入Swap日志 | **150次** | 仅是池事件数，含同交易内循环 |
| 不重复的买入Tx（按池+block+txHash） | **23笔** | 23个有买入样本，非23个人 |
| 买入时达到2 WBNB/1000 USDT冻结深度的Tx | **22笔** | 只是该交易深度，不等于用户可买 |
| 上述22笔中，首次满足深度Sync同Tx的买入 | **2笔** | #16/#17各自一笔Mint交易，合计129个Swap，不能作为同一交易内部可响应信号 |
| 上述22笔中，保存窗口内之后不同区块的达标买入 | **20笔，20个rank** | #1/#2/#3/#4/#6/#7/#9/#10/#11/#12/#13/#19/#21/#22/#23/#24/#25/#27/#29/#30。只是**历史买入交易候选**，不是20个`T_entry`已获验证 |
| 卖出Swap日志 | **4次** | #5=1，#8=2，#28=1 |
| 卖出独立Tx | **4笔** | 四笔均在已观察卖出时低于冻结报价储备下限 |
| 达标卖出 | **0笔（仅已存窗口）** | 不可据此推断24h/90d永远不可卖 |

这一分层**不是**购买资金建议，2 WBNB/1000 USDT是已冻结历史研究报价侧池深度门槛。仍未有20例的统一金额闭环、实际任何账户可卖、实时可观察`available_at`或因果经济收益。只要后续链上数据源窗口残缺，应报告`NOT_SCORABLE`，不得把没有看到卖出解释为`FAIL`或价格归零。

为了以交易闭环证据推进而不是继续添加活动量统计，利用现有已连接免费Alchemy只读BNB历史RPC，独立对**rank#3**初期后续区块的一个具体买入进行`Swap + ERC20 Transfer + transactionReceipt`交叉验证：

- 冻结token `0xd19ed19b1fae4f1f502b989745352e7b3a5a58a0`，池 `0x8cbd60ac73398e0a0b03d861274a802de84af9b3`，建池块52440691，真实买入块**52440693**。
- 交易`0xf8220e79c6bb545c6f49f4993c45f87976061e8f3f3508b57962de086e405a00`，receipt `status=0x1`，日志4条，实际`Transfer(WBNB→Pool)`金额`1100000000000000` raw=**0.0011 WBNB**，日志序号0x198；`Transfer(Token←Pool)`金额`122279179504473913187874` raw，日志序号0x199。二者逐整数与该Tx的Swap`amount0In/amount1Out`一致；该池最初quote储备60.09 WBNB，高于2 WBNB阈值。比单纯观察到一个Swap强，但**这仍只是一个成功买入历史个例，不证明税费/普通账户可卖/固定名义额退出或原公众`T_entry`**；RPC回执来自同一提供商规范化响应，完整原HTTP报文未保存到Git。
- 加上此前已核实的#1/#2，目前至少三笔固定候选**具体历史买入有原链上成功receipt与双币Transfer交叉核验**。不将“三笔成功买”写成“30币可交易”或“可赚钱”。

原30例子在此阶段**无需再二分部署区块，也无需把20个交易哈希逐一花无限RPC费用核实**。下一次优先从本机`v2_p0_offline_audit_status.json`现成`rank_results[].archived_pair_swap_evidence.first_observed_qualified_buy_later_block`导出20例买入交易对应的Tx和报价储备，再设计**有界的真实历史转账及统一研究名义额退出检测**。双向可执行的`18/30`和完整PIT`24/30`继续`NOT_SCORABLE`。PR保持Draft，`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`。

---

## 2026-10-20 Mac 36/36验收：65/64次Swap不是65/64笔独立成交；停止误用事件活跃度

用户直接上传Mac命令终端回执，固定代码SHA `9fcc34d025f282bce458cd0800ada77a483f4f12`：`test_monster_early_bsc_v2_pit.py` **18/18 PASS**，`test_monster_early_venue_factory_rpc_roster_probe.py` **18/18 PASS**，共**36/36 PASS**；旧存档**88份RPC响应**离线重放、冻结30/30真实PairCreated、25例创建同笔Mint+Sync、零身份异常继续通过。`24/30完整PIT`和`18/30实际同金额双向买卖`仍`NOT_SCORABLE`。

最重要的PIT/刷量防错证据：仅来自已归档非连续窗口，rank **#16观察到65次买入Swap、去重只有1笔独立transactionHash**；rank **#17观察到64次买入Swap、去重只有1笔独立transactionHash**。这两笔各自均为块**52444232**的首个后续注入`Mint`同一原子交易；Mac独立排序证据：#16第一个达标Sync logIndex736、Mint logIndex737、首笔Swap日志742；#17依次为1076、1077、1082。各自第一次Sync quote reserve 4/6 WBNB，均过2 WBNB研究深度地板；但**129个Swap日志不是129笔独立TX、更不是129个交易用户或129次公开可跟进买入**；其中没有任何已保存的另一笔TX出现在较后区块。首次可公开观察块、可用RPC延迟及可卖性均不因此确认。

为小成本实际查补，在Alchemy现有免费只读BNB端点用精确pool address+Pancake V2 Swap topic分别查#16/#17从**52444233到52444242**共**10个后续区块**：两池都返回**0 Swap**、0交易。这是10块的严格范围内缺事件，并非全天、未来90块或历史后续永久无交易。服务端对尝试的较大90块`eth_getLogs`窗口给出了**Free最多10块**的限制（无调用成功的90块数据），故不再无限追加逐块RPC追此二币；原始provider HTTP bytes不在Git，当前来源是同一既有Alchemy连接器规范化响应。

实用工程调整（未获新的Mac测试）：`summarize_v2_archived_swap_windows`在保持原真实Swap、真实深度、原子Tx边界结果不变的同时，**新增按区块+交易哈希去重的买入/卖出交易数量以及冻结门槛达标买入的独立Tx数**。`--mode audit`在原主结果JSON中列`observed_swap_activity_distinct_transactions_by_rank`（30行），每rank有`buy_swap_events/buy_distinct_txs/above_floor_buy_swap_events/above_floor_buy_distinct_txs/sell_swap_events/sell_distinct_txs/first_qualified_buy_public_reaction_status/qualified_buy_later_block_distinct_txs`。单元测试用**同一Mint交易内多笔Swap**反例确认swap count=2而独立交易=1；原#1/#2/#5真实离线旧归档回归确保其他样本不回退。新代码版本 **NOT_RUN_ON_MAC**，不把原SHA 36/36自动视为新版本通过。

**主线决定：** 接下来先用本机已归档88个真实RPC文件对**整个冻结30币**计算独立交易数，识别有真实独立外部订单的候选。然后只对这些真实候选优先核对代币Transfer、转账税/限制、进入时间和统一研究名义额双向退出能力。明确保留少量交易/死亡/无法退出的代币在母体分母，绝不从先前Binance/Alpha赢家倒推。没有足量卖出交易与完整窗口时必须输出`INSUFFICIENT_COVERAGE`或`NOT_SCORABLE`，不为推进P1制造模型样本。原研究深度2 WBNB/1000 USDT不是用户买多少的指标，禁止把它当建议买入金额。

---

## 2026-10-20 #15/#16/#17首笔归档买入、延迟LP及原子交易边界

用户Mac离线审计`v2_p0_offline_audit_status.json`的原始首笔事件摘要（来源`USER_PASTED_MAC_STDOUT`）：

| 冻结rank | 首个归档买入区块 | 已归档买入Swap数量* | 第一笔归档买入前quote储备 | 旧冻结quote深度门槛 | 第一笔归档买入tx |
|---|---:|---:|---:|---|---|
| #15 USDT | 52443890 | 1 | 1.131902945232507780 USDT | 未达1000 USDT | `0x67bec80a3a1e1568f7715a1a24bee05c43df5c53d42573580df3412531471f9f` |
| #16 WBNB | 52444232 | 65 | 4 WBNB | 达到2 WBNB，但同tx LP注入 | `0x39d28c9d42c174151d6f6ac31df93ee2edf2bc709a3550889c3f69ccf0638f16` |
| #17 WBNB | 52444232 | 64 | 6 WBNB | 达到2 WBNB，但同tx LP注入 | `0x8fbe3ba7e888f1380f2ea660eec643a868436373827a91d57bd36b6946d3fbb2` |

*65/64是原**非连续短窗口内的买入Swap事件数**，不是65/64个用户、65/64笔独立交易、公开交易次数或真实可跟进信号。Mac原始88个HTTP/RPC正文未被ChatGPT容器读取。

本次通过已有只读Alchemy BNB-mainnet RPC定向核实块**52444232**两对池各自恰有一次`Mint`（按**正确**Pancake V2 Pair Mint topic筛选；每池只返回一个；未对全链其他池做断言）。#16 `Mint`在logIndex**737**(0x2e1)，txIndex103；#17在logIndex**1077**(0x435)，txIndex107。各自`Mint`所属tx与上述**首笔归档达标BUY Swap相同**；首次Swap的logIndex分别为**742、1082**，Mint均先于该Swap。Mint WBNB额度**4 / 6 WBNB**，恰等于用户Mac`Sync+Swap`反推的首笔买入前quote reserve。其对应的PairCreated块`52444037/52444121`原始交易未含同Tx初始Mint；后续注入发生在52444232。

更重要的区块结束状态（真实历史Pair`getReserves()`只读`eth_call`，WBNB在两Pair均为token1）：

| 冻结rank | 块52444231结束quote reserve | 块52444232结束quote reserve | 块52444233结束quote reserve |
|---|---:|---:|---:|
| #16 | 0 WBNB | **9.6000278 WBNB** | **9.6000278 WBNB** |
| #17 | 0 WBNB | **20.2000287 WBNB** | **20.2000287 WBNB** |

因此确认：**首次已归档的达标买入是在同一笔`Mint`流动性创建的原子交易内部发生**，不能在回测中将这笔Swap当成“外部参与者见到Mint后可立即买入”的机会；同交易内流动性尚无面向另一独立交易的即时可响应时间。状态从0储备到区块结束仍过门槛，故**下一块52444233是使用已确认区块状态的保守入场候选起点，不是已证明公众观察时点，也不证明下一块钱包买卖可执行**。`24/30`和`18/30`均仍`NOT_SCORABLE`。

为避免继续事后偷看，原`summarize_v2_archived_swap_windows`离线模块现在逐池从完整归档窗口按`(block,txIndex,logIndex)`发现最早的**已保存的**达标`Sync`、最早达标买入`Swap`，标记`SAME_TX_NOT_PUBLICLY_REACTABLE_AFTER_SYNC`/同块不同交易/后续块，以及Mint与首达标买入是否同Tx；统计首次达标Sync所在交易内的BUY个数、独立未来区块BUY个数。这些字段仅适用于已保存窗口，缺页不变成未发生。`--mode audit`重跑**离线**可抽取这两例的原始历史交易边界信息，新代码/测试尚待本机验收，不宣称已PASS。下一阶段应该查**后续区块是否存在符合真实资金约束的独立买入、Token Transfer以及可卖出同额路径**，而不是再二分30份code或制造盈利标签。无交易执行/付费API/自动交易权限。

---

## 2026-10-20 P0真实历史Swap准入快照：用户Mac 35/35与原88份离线回放PASS

用户Mac固定代码版本`91ffecf096af60dda0658744337402a54d0b5aaa`离线单测`17/17+18/18=35/35 PASS`，旧归档共**88份原始RPC响应成功重放**、固定30例创建30/30、创建同Tx Mint+Sync 25/30，`unknown_ranks=[]`。重算**交易前报价资产深度**后，原非连续存档短窗观察到：**23个rank有买入Swap，其中22个在所观察具体买入时达到事先冻结的2 WBNB/1000 USDT门槛，#15买入时低于门槛；3个rank有卖出Swap，但#5/#8/#28在所观察具体卖出时均低于门槛，达标卖出观测数0。** #16/#17两例虽然建池交易时没有同笔Mint+Sync、初始LP不足以评估，但在所存后续`Swap`中反推出交易前报价储备高于事前门槛；**这不能直接写成入场时刻`T_entry`已找到**，因为所存窗口只含建池起初10块及第一后续储备更新块，并不证明哪次注入首次满足门槛，也没有历史公共可读时间。后续窗口缺失仍是#18/#20。

**业务结论**：在这有限窗口中**0个符合事前深度标准的实际卖出样例**，不是“30个币都卖不出去”，不是“卖出胜率0%”，更不是18/30的失败判定。当前数据已不足以给出18/30双向实际卖出可模拟性：`18/30=NOT_SCORABLE`，`24/30 PIT=NOT_SCORABLE`。若免费可连续获得池日志及原ERC20转账/费率/限制数据，下一验证应针对初始达标+延迟达标候选的真实同Tx收发、确定连续区块内首次资格跨越和统一研究名义金额的退出情景；如数据窗口始终不完整则报告`INSUFFICIENT_COVERAGE`并停止扩大模型。本次归档与开发可复验并不授权进P1。

**额外链上实际Transfer闭环**：通过已连接Alchemy BNB-mainnet只读RPC对初始达标的#1、#2在2025-07-01的已知历史买入交易，分别读取成功`status=0x1`的receipt及精确按报价Token->Pair、候选Token Pair->recipient过滤的ERC20 `Transfer`事件。#1：块52440351交易`0x2d0361e427bc0feaf9e316f6a79b3a9f935777043d13cb4084c9adfeed2f9ae7`，**88 USDT**转入原池、`13922587526690708956` token raw转出，逐整数等于Pool Swap。`Swap`前报价储备为10,000 USDT（>=1000 USDT）。#2：块52440642交易`0x459ad9b0a8601b3502077ce5e26a65af7b461429958c4ff8d9e269ee48324547`，**0.0937 WBNB**转入池、`51223471067359749457487212` token raw转出，逐整数与Swap一致；事前池报价储备8.3 WBNB（>=2 WBNB）。#2报价转入可能经路由器，不能以WBNB Transfer.sender冒充买方钱包。对应完整整数、真实转账主体和研究/实际订单区别存入`bsc_v2_p0_historical_buy_transfer_receipts_20261020`机器JSON。**只证明这两笔具体历史买入成功，不推断全钱包买卖、首次可观测T、税费或卖出成功；同一Alchemy供应商，不冒充独立第二源。**

对延迟LP #16/#17（首次后续储备更新与大量Tx集中在块52444232），连接器按池在该块过滤`Sync/Swap`和完整Mint交易receipt响应仍因结果过长被截断；不能把不完整文本当全事件顺序。Mac原离线文件`v2_p0_offline_audit_status.json`已经保存各rank对应所有已归档的`observed_direction_events`；可本机**只读取**#15/#16/#17的实际首个达标Swap的区块/Tx/储备，必要时下一次加固定窄块离线事件排序，不重复全部前史RPC，不调用付费`trace_filter`。

来源等级：`USER_PASTED_MAC_STDOUT`、`ALCHEMY_NORMALIZED_READONLY_CHAIN_EVENT`；Mac归档原始HTTP字节未由本对话读取/签收；不将任何此处成功声明为`SELLABLE_AT_NOTIONAL`/Paper盈利。`G4 UNKNOWN/G6 NO_GO/NO_MERGE/NO_DEPLOY/NO_TRADE/NO_GMAIL`不变。

---

## 2026-10-20 Mac 历史 runtime-code 全30完成；下一主线改为真实 Swap 前流动性

用户Mac五次连续前台只读运行，`--mode deployment`固定rank#6–10、11–15、16–20、21–25、26–30均返回`BOUNDED_CODE_STATE_REPLAY_PASS_NOT_DEPLOY_TX`、每批`requested_count=5`，请求分别**53/57/68/74/74**，合计326；加上已验第一批#1–5的38次，整30例共**364次RPC**。全部冻结30 CA历史 runtime-code 状态已有正常输出：**#1/#5/#8/#15在UTC前一日已有代码，其余26个首次出现于2025-07-01当日已确定块**。本次额外第一见代码块在PairCreated同块的排名为**#14/#16/#17/#18/#26**；严格区分“区块结束时已经有代码”与“同交易已经完成token部署”，也不根据缺初始LP丢弃这些失败/延迟样本。30排名完整对照、5批每批请求数和来源限制均保存于本Phase主JSON键`bsc_v2_p0_mac_deployment_code_full30_20261020`。用户本地已由程序归档RPC正文/同机校验SHA；Git未读取私人原始正文，不把终端复制的数值冒充独立HTTP回执原字节核验。**完整部署交易receipt、当时首次公众可查询available_at和真实可交易PIT仍不成立，24/30 PIT仍`NOT_SCORABLE`，不升P1。**

停止针对30例的纯历史代码区块重复二分，转入可以影响用户资金风险的验证：在原`bsc_v2_pit.py`已有离线窗口`summarize_v2_archived_swap_windows`里，新增`quote_reserve_floor_raw`参数。只在目标池**同交易、在Swap紧邻之前的Pair Sync**可用时，以Sync之后reserve和Swap实际`amountIn/amountOut`逆推该次真实Swap**交易前**的报价侧reserve，并与旧冻结的2 WBNB / 1000 USDT比较；没有紧邻Sync则`UNKNOWN`，数据不自洽则 fail closed。若是Tax/转账导致Swap内部实际入池额不同，按Pair事件真实amountIn计算，不假设币税为零；仍不能推出该用户钱包的代币实际到账或任意名义金额可卖。原离线Factory`--mode audit`因此可从之前Mac保存的88份原始RPC文件直接输出`observed_buy_with_proven_preswap_quote_floor_ranks`、`observed_sell_with_proven_preswap_quote_floor_ranks`、`observed_buy_below_preswap_quote_floor_ranks`、`observed_sell_below_preswap_quote_floor_ranks`和`observed_swap_preswap_depth_unresolved_ranks`。有缺页的非连续窗口仍不能推断全年首次Swap，也不能认定首个符合条件的`T_entry`。

验证设计时已经从Git归档的真实#1/#2/#5 Pool Sync+Swap原始十六进制事件重算，交易前quote储备**#1=10000 USDT、#2=8.3 WBNB、#5≈1.313968230 USDT**，与此前各自原始Mint+Sync创建储备逐整数一致；前二者当笔高于门槛、后者未达到。其余27个真实Mac本地事件结果**待运行新增离线审计，不能提前声明通过或枚举其金额**。新逻辑及回归测试虽然已入branch，但测试结果目前是`NOT_RUN_AFTER_CHANGE`；此前Mac `33/33 PASS`固定SHA`15625f3`仅针对前一版代码，不自动迁移到新提交。

冻结母体不变、基线研究门槛不变、quote深度下限**不是用户下单的名义金额**，不制造`SELLABLE_AT_NOTIONAL`标签和过去可观察时钟。开发优先级从源开关转成“真实Trade时的交易前深度→token/quote真实收发→用户固定名义金额模拟及真实T_entry”顺序；`G0 PARTIAL/G4 UNKNOWN/G6 NO_GO/NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`保持。

---

## 2026-10-20 Mac部署代码状态实测第一批 #1–#5：完整通过

固定SHA `15625f373250cc2356ee05ca92e8a321b1bcd565` 在用户Mac前台 `git pull --ff-only` 成功，离线测试 `test_monster_early_bsc_v2_pit.py` **15/15 PASS**、`test_monster_early_venue_factory_rpc_roster_probe.py` **18/18 PASS**，合计**33/33 PASS**。新`--mode deployment`首次真实BSC历史HTTPS RPC运行（冻结2025-07-01 UTC，rank1–5）**38个RPC请求、5/5正常完成、无来源失败**。rank#1和#5 `RUNTIME_CODE_PREEXISTS_FROZEN_UTC_DAY`（当天之前已有code），rank#2首次代码可见块**52440593**、#3 **52440672**、#4 **52440725**（前一块无code；和之前只读Alchemy结果一致）。本机原始HTTP响应+本机计算SHA预期按代码写入原P0本地归档，**本对话没有读取/独立校验用户Mac文件**；记录为`USER_PASTED_MAC_TERMINAL_STDOUT`而非第三方原始字节证明。用户回执证据详见JSON的`bsc_v2_p0_mac_deployment_code_batch1_20261020`。该固定代码版本本地新单测由NOT_RUN转为PASS。

精确业务边界：5/5成功只证明P0历史 runtime-code 出现/存在区块，**不是5/5部署Tx证明，也不是5/5 public `available_at`、买卖实际可行、策略赚钱**。`24/30` PIT与`18/30`卖出均仍`NOT_SCORABLE`。有界免费链上方法可用性检查：Alchemy连接器的`trace_filter`明确需要付费，`alchemy_getTransactionReceipts`在BNB网络不受支持；标准`eth_getBlockReceipts`能返回结果但当前连接器大结果截断（约8KB），不能作为完整区块所有部署收据。**不升级付费、不把截断数组当完整验证**。若需准确部署Tx，后续仅通过已验证免费历史RPC在指定代码首次非空块读取完整收据或有界交易索引，且对factory内部CREATE与顶层contractAddress作区分，先证实可用才开发；不要无条件跑全天交易收据。

下一次仅需**接着执行rank6–30的五批**，不需要重复rank1–5或既往1471请求；每批独立100次免费RPC上限，故障后停止并保留旧原始归档。完成后即可以代码状态为背景，集中验证实际入场/可卖证据与完整PIT门槛，不增新Stage，不开始P1或模型。

---

## 2026-10-20 P0新实证：冻结30币历史代码存在性、首次代码状态与实际入场分层

不从赢家倒推，**只按冻结V2工厂时间顺序**查2025-07-01的30个token；结合早已冻结的池原始Mint/Sync和2 WBNB / 1000 USDT报价侧下限：**20/30在建池Tx初始流动性已达原冻结档位且30内均出现在历史归档买入Swap+Sync列表中**；其他10个在建池时未达到这一档位，含后续延迟LP样本、零储备及超浅池。**20是条件交集的来源证据而不是已确立完整`T_entry`的买入资格，更不是已可卖出样本；10仍保留母体且可在之后首次满足条件时入场**。23/30买入Swap和3/30卖出Swap均只覆盖保存的非连续短窗口，不能由此推断全天事件全集。

已从现有用户Alchemy免费应用的BNB Mainnet**历史`eth_getCode`**抽查完整30个冻结CA于各自`PairCreated`块的链末状态：**30/30非空bytecode**（#8/#18/#20/#26/#28的提供商文字响应超过连接器上限，只能证明非空前缀，不能宣称完整bytecode已归档）。在冻结日之前块`52440286`检查同30个CA：**#1/#5/#8/#15已有代码**，其余**26个完全无代码**。所以首次有代码落在当日最初块`52440287`至各自PairCreated块闭区间的这26个，只代表**历史块结束时刻的runtime-code状态**，不代表当时公众第一次看见数据，更不代表已知创建Tx；此前存在又自毁再部署的极端历史尚未经receipt排除。

实际只读二分定位四个初始高流动性代表：

| 冻结rank | dayfirst前一块代码 | 首次非空runtime-code所在块 | 前一块无代码 | PairCreated块 | 部署原Tx/精确时刻 |
|---|---|---|---|---|---|
| #2 | 无 | **52440593** | 52440592 | 52440617 | **UNVERIFIED** |
| #3 | 无 | **52440672** | 52440671 | 52440691 | **UNVERIFIED** |
| #4 | 无 | **52440725** | 52440724 | 52440950 | **UNVERIFIED** |
| #6 | 无 | **52441208** | 52441207 | 52441231 | **UNVERIFIED** |

本轮不做数百次无上限连接器循环。在已有`mission_agent/early/bsc_v2_pit.py`新增只读二分`locate_first_runtime_code_block`，在唯一现有Factory CLI新增`--mode deployment`，冻结原30名单和UTC日窗口，不扫描785个建池、不追加Stage。一次前台手动执行最多5个rank并受`--max-requests`严格限制；每个历史`eth_getCode`保留**原始JSON-RPC响应字节与审计时SHA**于Mac现有P0目录，按来源fingerprint隔离，重放缓存时检测篡改。输出首有代码块与前一块无代码的证据状态，**绝不输出部署Tx验证通过、24/30完整PIT通过、可交易或可以盈利**。同时新增无网络合成归档单元测试：四个真实边界、旧日已存在的合同、假响应拒绝、断点复用和原字节篡改。**新增代码当前未运行用户Mac单测/CI，不能提前报PASS**；此前Mac`30/30 PASS`只适用于其固定旧SHA。

后续正路径：对至少24个冻结名单建立真实合约部署receipt、pool和真正`available_at`区分的证据；对20个初始高流动性候选逐个查**相应研究`T_entry`时**原报价储备与买卖双方真实限制/固定名义额成交模拟；税、限制、前60分钟连续数据缺失一律`NOT_SCORABLE`。此前3个成功卖出均在所查初始及卖出后储备小于冻结门槛，不能当24/30、18/30正例。绝不从上线/涨幅之后倒推新CA。

---

## 2026-10-20 第二次用户Mac PASS及三笔真实卖出交易的Token转账闭环

用户再次在原Mac checkout前台快进至精确固定SHA`8c5ed2494f256ab4d172cdf3d986794d9b9d2727`，两组测试**14/14+16/16=30/30 PASS**；本地原始JSON审计**88份、30/30建池重放、25/30同创建Tx Mint+Sync、unknown_ranks=[]**。旧小窗口当中的**23个排名**有报价币→token的实际Pool Swap+同交易Sync，**3个排名#5、#8、#28**有token→报价币Swap+Sync；窗口未观测到上述两方向的是#14/#18/#20/#26，**缺后续更新窗口的是#18/#20**。完整数组已写本Phase的机器JSON：`bsc_v2_p0_mac_first30_swap_window_audit_20261020`。这些数值仅是用户原本保存的非连续小窗口，不能把无Swap视为0、不能把“第一次在所存窗口观察到”冒充全链第一笔、不能把23+3视为26个双向可交易池。

**额外独立于Mac汇总、由已连接免费Alchemy应用历史只读RPC按确定区块复核的三笔卖出如下**。每例历史receipt的`status=0x1`；原token合约`Transfer(holder→pair)`真实传入额=Pool Swap的tokenIn，报价资产的`Transfer(pair→recipient)`额=Swap报价币out，且有同Tx先Sync后Swap。完整32字节Raw事件值及来源限制写入JSON`bsc_v2_p0_actual_sell_receipt_checks_20261020`。这只证明**该账户那笔已发生卖出**，不证明另一个钱包任意时刻/名义额可卖。

| 冻结排名 | 卖出Tx / 区块 | 实际报出报价币（18位精度，仅该笔） | 初始报价池储备 | 卖出Sync之后报价池储备 | 事前冻结最低档位 |
|---|---|---:|---:|---:|---:|
| #5 | `0xddf4631429c9faf6bb2a117516a2fff39debe9fd207d19c274808ca99a16f348` / 52441377 | 约0.099632794 USDT | 约1.313968 USDT | 约1.214335 USDT | 1000 USDT |
| #8 | `0x864245a074f1d48ab773a1c4be9f6cdbb0a4fe3d420c9a28b76e56a70df1e235` / 52442068 | 约0.937879706 USDT | 50 USDT | 约0.191649 USDT | 1000 USDT |
| #28 | `0xe58cfceaec28c06221309f55d413bcced063757cc0c8e84ce9d3d9dfdc3e985b` / 52447990 | 约0.0000392614 WBNB | 约0.002684584 WBNB | 约0.002645322 WBNB | 2 WBNB |

#28首次后续储备更新块52447990经历史`getReserves`更新时间戳二分定位，再在此块完整定向取Swap与两种token Transfer；#8卖出发生在创建后紧接一块。这些数字是实际链上已完成交易而**非用户自定义单笔订单金额**。**关键业务结论：三笔真实卖出所在币在建池初始及该笔卖出后均未达到P0原冻结的2 WBNB/1000 USDT最低报价侧储备**，不能把它们不加条件地变成模型准入后的卖出正例；中途其他时刻是否曾越过门槛并未全时间覆盖，保持UNKNOWN。

本次链上检索仍是**同一Alchemy供应商经连接器归一化的响应**，不是第二供应商交叉确认、不是原HTTP字节SHA/接收UTC、也不是完整可审计receipt文件的Git入库；有大receipt文本截断，字段通过窄`eth_getLogs`及receipt状态分别验证，禁止抬高来源等级。额外抽查#8/#28合约在各自建池区块`eth_getCode`均返回非空bytecode前缀，但响应被连接器截断，**不代表已证明首次部署区块或完整源代码**；不把局部抽查升级为30/30 deployment PASS。

**下一步主线决策**：保留30名单和原失败样本，后续覆盖按“历史首次确实符合事前LP门槛的时点→当时可观察Swap/买卖来源→目标资金量与退出限制”的顺序推进。先以已经可审计的窗口及合同部署来源判PIT是否达到24/30，再选少量符合早期准入的代币查同笔token Transfer和退出可模拟性，未建立免费可连续读的源路径不扩大成全日网络扫描。本轮无需再次执行Mac测试或1471次历史调用，`P0_PARTIAL / 24_OF_30=NOT_SCORABLE / 18_OF_30=NOT_SCORABLE / NO_P1 / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`不变。

---

## 2026-10-20 P0主线增量：已存原始池事件中的真实Swap方向离线重放

不重复RPC、不新增样本也不新建Stage。在已有`mission_agent/early/bsc_v2_pit.py`添加`summarize_v2_archived_swap_windows`，接入已有Factory原归档`--mode audit`。对冻结30个排名，读取先前本地`*.pool.rpc.json`（建池后的最多10块）与有文件时的`*.later.rpc.json`（首次后续储备更新块），以当时已冻结的token0/token1/quote CA判定Pair `Swap`的**实际池子方向**，与同交易、同池、较早`Sync`作一致性核对；记录原块号、Tx、日志序号和Pool原始金额。多个归档窗口重合时，只计相同事件一次，冲突字节拒绝通过。

新增主报告键：`observed_token_to_quote_swap_with_same_tx_sync_ranks`、`observed_quote_to_token_swap_with_same_tx_sync_ranks`、`later_update_source_window_not_archived_ranks`；每排名`archived_pair_swap_evidence`记录全部被观察的方向/来源窗口。**此程序目前只在既有小窗口回放**，中间区块未连贯扫描，任何未观察到Swap的排名不得被叫作卖不出；实际观察到别人成功卖出某笔也不能推出本用户的固定名义额、实际到账转账税、白名单/黑名单状态、任何历史时刻都可以卖，绝不能借此把18/30升级为PASS。LP代币自己发的`Transfer`也不是目标token实际转账，必须看**token合约**收发或真实完整receipt来补证。

已经把Git中三笔独立历史真实Swap（固定排名#1和#2买入方向、#5卖出方向）作为**离线回归夹具**，测试同交易先`Sync`和后`Swap`，另外测试无对应Sync/重叠窗口/冒名池/不合法quote/缺源时不能越级。注意：Git中既存的这三笔正规化观察是历史事实；**本轮新增的针对用户Mac 88份原RPC正文重放还未运行**，新的30排名买入/卖出结果仍未知，不得据此填写比例或声称本地测试已PASS。

下个最小单次命令只要`git pull --ff-only`、两组单元测试、原`--mode audit`。**不需要重新调用此前1471次RPC，不需要授权付费、钱包签名、现货下单、模型/定时任务/生产部署**。本轮仍仅覆盖2025-07-01 BSC Pancake V2，V3/Four.meme/Alpha母体尚未验证，G0/G4/G6维持原冻结状态。

---

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
