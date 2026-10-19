# Monster P0 — 免费历史源实测：BSC V2工厂存储枚举方案（2026-10-19）


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
