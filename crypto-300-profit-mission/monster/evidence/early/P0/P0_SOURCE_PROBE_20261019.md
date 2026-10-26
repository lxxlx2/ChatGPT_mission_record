## 2026-10-26：AWS BNB区块Parquet真实Footer可读；交易文件超8MiB元数据限制，修复为有界Schema前缀探针

**用户Mac前台实际输出（USER_PASTED_MAC_TERMINAL_STDOUT）**：指定日期blocks对象原文件长度147077458字节，ETag "c04114ca2a9e3002cb478423dad7eb26-3"，8字节尾标符合Parquet，实际取得其973289字节完整Footer，SHA256为5d04b0f7be64590ec7df61ae97c296b2f01fd3d08022e7d23980899b936cddd4。声明num_rows=115196、row_groups=185。115196与先前冻结高度52440287..52555482含两端的理论块数恰好一致，但**未读取行值，尚未证明每个高度确有一条、无重复或真实区块哈希对应一致**。块Schema显示number/hash/parent_hash/logs_bloom/receipts_root/timestamp/transaction_count/gas等；**logs_bloom和receipts_root是摘要/承诺，无法代替可解码原生EVM日志或回执**。timestamp是区块时间，不是2025同时代真实客户端接收回执，不升级PIT_VERIFIED。

同日transactions对象长度4826591204字节，在旧固定源码中返回 SourceError:FOOTER_TOO_LARGE_OR_INVALID。该错误将footer长度超出人为8MiB上限和文件无效混在一起；**现有Mac输出无法区分，更不能据此宣告S3对象坏了**。transactions Schema、该日期交易行数、原生log/receipt列仍UNVERIFIED。

**只修复当前数据门禁阻断，没有新建阶段或模型**：在既有aws_bnb_parquet_footer_probe.py加入>8MiB Footer的限额Schema前缀路径，先从末尾8字节获取声明的真实Footer长度，再从Footer开头只读取最多256KiB；要求HTTP 206、Content-Range、Size与ETag配对，且仅在Thrift CompactProtocol的前三个标准顺序字段真实可解析时报告Schema路径和声明num_rows。此分支不读取RowGroup详情、不宣称完整Footer SHA：显式footer_fully_verified=false、row_groups_declared=null、footer_sha256=null、scope=OVERSIZED_FOOTER_SCHEMA_PREFIX_ONLY。若字段结构不匹配/前缀过短，保持source失败并停止，不下载4.83GB正文。<=8MiB路径维持原完整Footer检验及SHA。

**离线验证与Git边界**：本地等价源码+原5个测试+新增3个边界测试，共8/8 PASS（超长Footer仅有限前缀、损坏前缀拒绝、非法Footer长度立即拒绝）。提交新代码1df6462908e19c078ba0bc9fcae467f9c93efc79、测试077d3ee3870ba9805c29c31749c93e5957041a15；本会话GitHub读回验证已写入同一Monster分支。**远端具体提交版本尚未运行新的Mac网络探针/CI，8项本地测试针对等价实现，不能冒充已执行远端逐字节测试**。

下一步只看这份指定日期transactions真实Schema是否含eth_getLogs可复原的topics/address/data/logIndex、逐交易receipt及gas字段。若字段缺失，则AWS计划B最多用作辅助块/普通交易锚点，不为补缺继续下载多GB文件；其余日志/PIT和同研究金额双向真实卖出证据必须由其他已有合法免费源提供。P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO不变；2026-11-02来源止损不变。不付费、不运行Mac后台、不改Frank/Gmail/交易及冻结样本。

---

## 2026-10-26：AWS BNB两份指定日期Parquet对象实际存在，Schema及原生日志仍待核实

**Mac实际运行输出（USER_PASTED_MAC_TERMINAL_STDOUT）**：对冻结的2025-07-01 UTC，通过先前已Git固定的匿名S3目录探针查询成功，blocks/date=2025-07-01/blocks.parquet=147077458字节；transactions/date=2025-07-01/transactions.parquet=4826591204字节。两个对象date_objects_observed=true，目录查询无错误，均有具体完整Key及Size；四种预探日期命名中仅date=YYYY-MM-DD/路径命中。两个顶层列举均truncated=true，仅说明其列出的10个子目录不是整个历史月份全集。**首次证实这一日期分区两类文件存在**，先前SOURCE_CANDIDATE_ONLY升级为OBJECTS_LISTED_CONFIRMED，而不是SOURCE_FULL_COVERAGE_PASS。

**未能证实**：Parquet列字段、完整block高度覆盖、原生logs/receipts、同刻Sync/Swap、2025-07-01 public receive-time；目录无logs/子目录并不证明transactions文件中也没有嵌套日志。即使Parquet行总数较大，仍不能认定数据无漏，也不能用block_timestamp补出真实公众available_at。P0的24/30 PIT和18/30同名义额可卖均继续NOT_SCORABLE。

**本轮实际代码交付**：在同一PR #30下新增local-agent/mission_agent/early/aws_bnb_parquet_footer_probe.py，固定两Key和上述对象长度，通过每对象仅两次HTTPS匿名Range GET读取尾8字节及Apache Parquet CompactProtocol footer（单对象≤8MiB元数据），强制HTTP 206及Content-Range完全匹配，并对两个请求校验ETag/Size一致；只输出Schema路径、文件元数据声明的行数、RowGroups、命中日志/回执候选字段、footer SHA256及错误状态。完全不下载147MB/4.8GB主体，不写文件，不部署，不涉及钱包、RPC或云端付费计算。Schema字段名不等于实际日志可用性，更不等于PIT。提交代码 9f5febbb4d1c5468602c7536837f8b3626a451cb；离线回归 9757f20b407890e5144c47e197bc4c803d60abf8。GitHub读回确认两个文件确实存在，Blob分别为45ba8845d2a0bba599bcba8e4bcb5463d10bda5d、eeb490757991d547334a63738b2150269509ce32。

**测试边界**：同等功能本地草稿经真实Python离线5/5 PASS并用Thrift CompactProtocol合法结构进行了独立合成元数据解析核查；已提交的两个文件仍未通过真实CI或Mac上的命令执行，不把草稿测试冒充已推送源码的完整端到端测试。待Mac首次运行真实SourceProbe输出后决定是否需要只取最小列块/receipt；若Schema明确缺乏事件日志，本AWS Plan B只能作为blocks/transactions辅助事实，不升级PIT。2026-11-02来源止损保持。

---

## 2026-10-26：用户Mac确认AWS BNB第一层目录；零下载有界日期核验器已提交（P0 SOURCE_CANDIDATE_ONLY）

**用户Mac终端输出（USER_PASTED_MAC_TERMINAL_STDOUT，非本会话独立读取S3对象）**：对AWS官方公开桶 aws-public-blockchain.s3.us-east-2.amazonaws.com 使用匿名 ListObjectsV2，prefix=v1.1/bnb/、delimiter=/、max-keys=100，返回 Prefixes=['v1.1/bnb/blocks/','v1.1/bnb/transactions/']，Objects=[]。Objects=[] 仅代表此层没有直接列出文件；delimiter分组后的两个子目录可有大量对象，不能据此记0条交易。该枚举只显示两个第一层子前缀，**日志/receipt是否嵌套、是否包含2025-07-01历史数据完全未确认**。

**本轮完成离线代码和测试**：原 local-agent/mission_agent/early/ 增加 aws_bnb_public_source_probe.py，测试在原 local-agent/tests/test_aws_bnb_public_source_probe.py。匿名最多10个ListObjectsV2请求，每次最多10项、限制XML响应128KiB；枚举blocks/transactions各自第一层与2025-07-01四种常见分区前缀（date=YYYY-MM-DD、YYYY-MM-DD、YYYY/MM/DD、year=YYYY/month=MM/day=DD）。仅打印JSON stdout，无文件写入、无Parquet下载、无RPC/密钥/云资源/交易。结果严格将目录发现与Parquet列验证、历史公众可见时间、PIT、G4可卖性分离。空列举不证明数据不存在，错误保留为错误。

**实际离线验证**：Python标准库离线4/4 PASS，分别涵盖XML命名空间/上限、prefix伪装拒绝、来源错误保留、出现日期对象仍不能虚报日志和PIT。经过Git Blob SHA比对，本会话测试过的源码与GitHub已提交源码逐字相同。两个代码提交分别为 bc784de3413793f4ffb3244cd5231b1e017ffbc2、883f40776934f34a3930360a6cf3b9599e684b2d。**本轮未在Mac或CI运行新探针，也未取得AWS任何Parquet内容、日志/receipt、schema、原始日期分片字节/哈希；独立AI审核未做**。本会话容器对AWS依然DNS解析失败。

**唯一有效下一数据门禁**：Mac前台运行已提交的匿名目录探针；先看确切历史日期对象与命名结构。之后如有数据才检查文件实际字段和Factory日志/receipt能力，并用固定30例交叉核验。即使块时间可回溯仍不等于2025当时公众真实接收时间。继续 P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO；24/30 PIT、18/30统一名义额可卖都未达到正式通过，2026-11-02止损不变。

---

## 2026-10-26：AWS官方公开BNB数据桶，2025年P0完整日志覆盖待查（SOURCE_CANDIDATE_ONLY）

新增**官方可核实候选源**：AWS Registry of Open Data 官方当前明确列出由BNB Chain维护的匿名公开S3前缀 `s3://aws-public-blockchain/v1.1/bnb/`（区域us-east-2），官方登记允许`aws s3 ls --no-sign-request`，公开数据不要求AWS账户或订阅。来源：https://registry.opendata.aws/aws-public-blockchain/ 及 https://aws.amazon.com/marketplace/pp/prodview-w2rxwj7aw6mt6 。它可能提供免付费历史原始数据的另一条Plan B路线，避免继续对Alchemy支付才有的历史debug trace消耗预算。

**实际证据边界**：本轮尝试在当前隔离运行环境匿名列出该前缀，但网络DNS解析失败；网页浏览接口也无法列出S3对象。**没有读到任何真实S3对象、Parquet列、2025-07-01分区、块号范围、日志/receipt行、对象SHA或下载字节。** 因此只能记`PLAN_B_AWS_PUBLIC_BNB_CANDIDATE / DIRECTORY_NOT_READ / HISTORICAL_2025_COVERAGE_UNVERIFIED`，**绝不计为可用来源、PIT当时可见时间、V3/Four.meme全量或P0 PASS**；AWS登记的“daily update”不能推出历史全量或观察时钟。原无账户读取允许但AWS Athena/Glue付费计算未授权，不创建云资源、不下载数据、不启动Mac或新增CI。

单次最小后续验证入口：能够访问公开S3目录时，首先只列`v1.1/bnb/`的子前缀与`2025-07-01`分区；只有找到实际历史Parquet对象后，再核对字段是否包含原Factory/launchpad全部事件、真实来源时钟、行数和无分页截断，再进入最多一个有界日期范围的独立交叉验证。若该源只有链上`block_time`，仍不符合历史`available_at`的`PIT_VERIFIED`，不升级当前24/30、18/30门禁。2026-11-02原历史来源止损日期不变。

## 2026-10-26：22笔历史SELL的真实交易路由与最低输出保护核查（P0执行质量）

为了直接检验“曾经卖出”是否代表普通投资者可**合理受保护地卖出**，本轮按原冻结30个CA中已存的20+2笔代表性历史SELL交易hash，经用户既有Alchemy BNB mainnet**只读`eth_getTransactionByHash`完整读取22/22历史交易的实际`to/from/input/selector`**；不补取未来赢家、不改变选择规则或原代码。对可以按PancakeSwap V2标准ABI解释的交易，只以真实函数选择器和 ABI 字节精确解析`path / amountOutMin / deadline`，并核对全部标准路径均为**对应冻结Token CA→对应WBNB/USDT报价资产**、2个地址、原V2 Router目标地址，未以token Symbol猜测身份。

| 被抽查的原始实际SELL路由 | 数量 | 价格保护（实际入参） |
| --- | ---: | --- |
| 标准 V2 `swapExactTokensForETH`（`0x18cbafe5`） | 13 | **13/13 `amountOutMin=0`** |
| V2 `swapExactTokensForETHSupportingFeeOnTransferTokens`（`0x5c11d795`） | 2 | **2/2 `amountOutMin=0`** |
| V2 `swapExactTokensForTokens`（`0x38ed1739`） | 1 | **rank1存在正数`amountOutMin`**，实际报价资产为USDT |
| 自定义合约/其它选择器（`0xfe061fbb`、`0xe9ae5c53`、`0x3593564c`） | 6 | **保护参数不可从标准V2 ABI推断，标为UNKNOWN** |

因此，**16笔能完整解释为标准V2 Router的历史SELL中，15笔没有设置正数最低输出；不能将另外6笔UNKNOWN也记为零保护**。16笔标准调用里另有11笔的实际`deadline`按合约Unix秒语义在交易发生后仍超过24小时（9笔13位数、2笔11位数）；其余5笔期限在当天，其中rank1距离该交易块时间约1193秒。由此只能断言单笔交易的保护参数及实际期限，不能推断发起者的故意程度或交易所、钱包的通用安全性。

**直接影响P0业务口径**：此前22笔成功卖出的真实回执、18个达标报价深度样本都继续保留为历史**特定成交**。但卖出成功对“普通用户有保护、固定下单金额可重复成交、可净获利”的支撑明显受限；极端99%报价储备耗尽的7笔均属于上述`amountOutMin=0`标准Router，包含rank9/19/27三笔部署者自身卖出。rank1确有非零minOut，也**不是普通投资者完整买入再退出**的实证，不能升级为单例策略PASS。

对应可复算摘要及22个rank逐笔路径分类追加到**原P0 JSON**的`bsc_v2_p0_22_sell_transaction_route_price_protection_20261026`，原引用的交易hash、池及CA没有改动。所有读取来自同一Alchemy规范化RPC，未得到原始HTTP响应SHA、独立供应商证明或2025当时公众收到事件时点。无需继续逐个增加相同来源的交易案例；真正阻断主线的是**完整历史来源/PIT、预冻结统一名义金额、双向税费与最终钱包净到账**。仍为`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`，2026-11-02原历史源止损日期不变。本轮无新Python unittest、CI、独立Review、Mac执行、部署、邮件或交易。

## 2026-10-26：22笔真实SELL的同交易Sync核验与储备耗尽风险（历史执行证据，非PIT或用户净收益）

本轮继续原P0主线，**不换30个冻结CA母体、不读未来5×/10×结果或事后赢家名单**。数据直接使用原P0 JSON中已存20组`case_results`及rank16/17另2组真实后续BUY/SELL；每笔只按原冻结rank+CA+Pool匹配。对**全部22笔历史卖出**通过现有免费Alchemy BNB只读`eth_getTransactionReceipt`实际重新读取，不使用用户Mac、不执行交易。全部22/22 receipt `status=0x1`，对应Pool在原卖出交易中**恰好1条Sync**；按旧冻结Factory token0/token1确认报价资产方向，由这笔真实回执的**Sync成交后Quote储备＋已有真实Quote池侧输出＝已存卖出前Quote储备**，22/22按最小原始整数单位精确一致。对其中最极端7笔另核验WBNB Transfer自池流出与原Swap输出精确一致。实际RPC返回为Alchemy规范化回执，**没有原始HTTP字节SHA或第二独立节点**，本结论仅是指定历史交易/单池执行证据。

**直接观察到的退出规模风险**：22笔特殊挑选的实际历史卖出中，7/22笔（rank2、6、9、10、19、22、27）一笔取走卖出前池内超过99%的报价储备。4笔（2、6、10、22）卖出前储备本就低于冻结报价侧深度门槛；另外3笔（9、19、27）**卖出前满足原冻结深度门槛**，各从约15.48/15.52/15.82 WBNB储备取走超过99.9990%（按原始整数分数精算，见新增机器证据表），且这些rank的卖出代币发送地址恰好为对应代币部署交易发送地址。这说明**单凭历史“有成功卖出”和“卖出前池储备达到下限”，无法证明普通投资者在统一研究额度下能以合理价格退出**。不推断这些交易的意图、是否恶意或实际受益所有人；部署地址不同同样不能保证项目彼此独立。

为量化费用压力，按原研究Pancake V2 25bps参考池手续费，在单池理想恒定乘积、无税/MEV/其它路由/整数dust的假设下，特定卖单相对卖出前池中间价的**理论平均卖出折价**为`25 + 9975 × QuoteOut/QuoteReserveBefore`（单位bps）；22笔中**15笔超过100bps**，18个卖出前有合格储备的池中**11笔超过100bps**。100bps及99%仅为**事后诊断敏感性阈值**，不属于预冻结研究资金或真实交易准入规则。这是历史选中特定卖出交易的`AMM_MATH_ONLY`分析，**不能作为普通投资者现实卖单净成交价格或策略费后收益**；原22笔并非全链完整、随机交易、最高价附近事件或22个独立正常交易者，不能推广为全体失败率。

机器证据以**单条追加记录**写入原P0 JSON的`bsc_v2_p0_22_actual_sell_pool_quote_depletion_20261026`，22条逐币保存原tx hash、Pool、预/后Quote储备、池输出、Quote取走bps和参考AMM折价，支持未来审计或算法中的`LARGE_EXIT_CAPACITY_RISK`解释；**未改变当前策略或实际风险提醒**。真正同一冻结名义金额、完整税费/Gas、合理最低成交保护和独立于发行方的真实双向退出仍未解决。2025实时`available_at=UNKNOWN`、BSC V3/Four.meme全母体无漏证明仍欠缺；`24/30 PIT`及`18/30同量级可卖`均继续`NOT_SCORABLE`，`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`，2026-11-02历史源止损日期不变。此次无新Python测试/CI/独立Review，不启动服务/付费API/邮件/交易/新RPC配置。

## 2026-10-26：29份历史部署者只读补证与已存20笔BUY/SELL参与者交叉匹配

**新增真实来源**：利用用户已连接的Alchemy BNB只读接口，对原冻结30例中已有确切创建交易哈希的29例补查发送方。20个通过完整`eth_getTransactionReceipt`直接读取及身份匹配，另9个通过完整`eth_getTransactionByHash`读取创建交易的`from/to=null/txHash/区块`并与原先保存的合约创建回执关联；以上不再依据当前钱包持仓或未来赢家名单抽样。新机器记录追加在同一份P0 JSON的`bsc_v2_p0_29_deployer_sender_identity_readback_20261026`，各rank地址与原创建交易hash/块可复核。**29/29发送者地址不同；rank5仍无确切创建交易，保持UNKNOWN。** 这些只是部署交易的发送地址，不等于实益所有者、同一团队的独立性或真实市场参与者身份。

**对先前保留的20笔实际买入及其各自首条已索引卖出做跨表关联**（另有rank16/17两笔后续BUY不在这20行内，不能把20冒充22）：这20笔的Token BUY接收地址只有**14个不同地址**，Token SELL转入池子的发送地址也只有**14个不同地址**。重叠BUY接收地址包括rank `2/6/10/22`（同地址）、`3/13/23`（同一自定义合约）、`7/19`（同地址）；重复SELL发送地址包括`2/6/10/22`、`3/13/23`、`25/30`。历史卖出结果本来就是特定交易案例，不能把池数直接换算成独立买卖参与者数量。

与29个部署者关联得到**五条可定位的地址角色重合**：
- rank **1** 的已存BUY代币接收者，正是**rank1自己合约的部署交易发送者**。
- rank **9、19、27** 的已存首条索引SELL代币发送者，各是该rank代币的部署交易发送者。
- rank **4** 的已存BUY接收地址，同时是另一冻结样本 **rank24** 合约部署交易发送者，属于跨代币角色重合。

以上匹配只说明**公开链上地址字面相等**，无法据此认定实际控制人相同、刷量、内幕交易或利益冲突；卖出证据仍是历史具体数量/路径成功，且`first indexed SELL`不等于已完整扫描未来全部SELL。此前相同runtime代码组A的9个CA由9个不同发送地址部署，组B的4个CA也由4个不同地址部署；两种事实需同时保留，既不能把相同bytecode硬合并成一项目，也不能凭不同部署地址宣称九个独立项目。

**补齐完整22笔历史BUY的同一地址口径**：原本另行留存的rank16与rank17两笔独立于初始Mint的BUY，在2026-10-26再经Alchemy只读重新查询其后续SELL的真实交易回执，分别严格验证ERC20 `Transfer`实际发送地址、原池接收地址和原始token数量与冻结机器档案一致。合并原20组＋这2组，保留22个CA/22笔特定BUY及各自已观察SELL，得到**16个不同的BUY Token接收地址、16个不同的SELL Token发送地址，13/22为同rank BUY接收地址与SELL发送地址相同**。上述特定金额历史成交不能算16名独立投资人、完整退出或统一金额可实现利润。新增2例未与已核实29个部署地址重合；原五条部署者角色关系未变。对应机器可复算记录为原P0 JSON的`historical_22_buy_sell_participant_reconciliation`字段；两笔新回执同属原Alchemy提供商，未取得完整原始HTTP响应字节，仍不能声称跨供应商独立复核。

**研究影响**：此前的22笔BUY与18个达标池SELL应继续作为**交易可行性实证**留存；不能当成22名独立自然人或18个彼此独立的可获利投资者。后续若进入P2，需要按地址、字节码、资金关联作稳健性分组，并额外区分发行/部署关联方交易与普通用户条件；当前既没有证明资金关系，也没有为此筛掉任何冻结30例或回溯挑选赢家。新读取来自同一个Alchemy提供商的规范化输出，**无原始HTTP响应字节归档、无第二供应商验证、无2025年实时`available_at`**，正式`24/30 PIT`、`18/30统一金额双向净卖出`仍为`NOT_SCORABLE`，`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`。本轮没有启动Mac、定时任务、交易、邮件、模型训练或新的CI，冻结2026-11-02停止日期不变。

## 2026-10-26：冻结30例跨证据表一致性与相同运行时代码集中度（离线派生，无源门禁升级）

来源仅为已保存的原P0机器JSON blob `978f437788689eef265b47511fa963490c3e9c96`，使用GitHub连接器按完整字节读取后在隔离JavaScript运算中联结既有冻结身份表、最终缺口矩阵、29笔部署回执摘要及18例时间顺序表。**跨表核对完全离线，没有调用新的数据源计算这些统计。** 另尝试对rank 5的历史部署区块做少量只读Alchemy补证：`alchemy_getTransactionReceipts`在BNB网络返回`Unsupported method`；`eth_getBlockByNumber(fullTransactions=true)`只返回截断正文，未取得rank 5的创建交易，也没有将该失败记为0部署。无Mac运行、模型开发、交易或Python unittest/CI；代码及原实验阈值不变。

- 30/30 frozen rank、CA及池唯一；30/30身份、池、建池区块在两张既有独立派生表逐rank一致；29/30已保存成功部署交易且部署区块不晚于建池；18/18已保存时间顺序表的达标深度区块严格早于历史BUY，历史BUY严格早于实际SELL；未发现所检查的跨表身份/区块/卖出阳性冲突。
- 源证据区分：24/30首次已证达到原报价侧储备下限，22/30后续实际BUY，18/30有原达标池后的成功SELL，7/30有同一token接收地址买回原数量的往返；**7包含在18内，不能加总**。其余样本是证据缺失/未观察到，不得记作实际失败交易或0收益。
- 已存历史合约运行时代码映射中，`EXACT_RUNTIME_BYTES_GROUP_A_1346`为9个CA（rank 7,9,11,12,19,21,25,27,30），其中9/9在18个实际成功SELL集合；`EXACT_RUNTIME_BYTES_GROUP_B_3553`为4个CA（rank 2,3,6,10），其中1/4有成功SELL。其余12个CA仅证明不等于A/B，**组内是否相同未知**；5个CA因提供商字节码返回上限无法完整分类。**相同bytecode并不证明同一项目、独立交易者或共同控制关系**，但说明未来不得将这些高度相似的池/交易视为独立10x盈利正例；独立性须以身份与发行来源进一步验证。
- 本轮只做旧原始机器记录之间的派生一致性检查，没有重下载2025年完整HTTP原字节，也没有重新证明链上receipts的独立供应商来源。2025年同时代公众`available_at`仍为UNKNOWN；一致性并不解决完整V3/Four.meme原生日志覆盖、税费/路由/最终钱包净到账、统一用户研究名义额的双向容量。正式`24/30 PIT_VERIFIED`和`18/30 same-notional sellable`仍为`NOT_SCORABLE`，`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`，原2026-11-02止损日期不变。

## 2026-10-23：P0历史来源完整性审计及免费V3扫描预算决策（NO_SCAN）

固定基线：PR #30 OPEN/Draft，审计前HEAD `ddacb786e843c0e3d8bf4d3d4d9cd2629de121e6`；本次只对现有原证据JSON blob `978f437788689eef265b47511fa963490c3e9c96`做来源可达性、完整覆盖、时钟与计算资源分类，**没有重新扫描历史V2买卖、未触碰已有30例身份或538个Four.meme索引，也未变更前向批准范围**。

### 1. 真实已得证据与真正欠缺

| 预冻结来源 | 已有真实性与采样范围 | 尚缺什么（严禁自动PASS） | 本轮结论 |
| --- | --- | --- | --- |
| Pancake V2 Factory | 2025-07-01 UTC 首30对CA/Pair；29笔准确部署receipt、24份独立完整区块后合格储备、22笔独立后真实买入、18个合格池实际卖出；2026-10-23 Mac唯一已授权一次性前向短窗口12次RPC且Pair计数0增长 | 历史2025 contemporaneous `available_at`与完整BSC多场所分母、同统一预冻结研究名义额完整双向净执行 | `V2_HISTORICAL_SCOPED_ONLY`，PIT `NOT_SCORABLE` |
| Pancake V3 Factory | **预登记三日、各首10块**（2025-05-01、07-01、09-01）Alchemy `eth_getLogs` 3/3响应成功，其中仅五月窗口有1个`PoolCreated`，明确与历史receipt及getPool交叉；2025-07-01第一窗口事件0 | 三日**其余区块全覆盖**、所有V3原事件无漏分母、统一集中流动性真实in-range报价与买卖能力、当年真实可见回执 | `BOUNDED_10_BLOCK_WINDOWS_ONLY`，`FULL_DAY_NOT_COVERED`；不能把7月首10块0推成全日0 |
| Four.meme TokenManager2 | 2025-07-01合约索引差为538，后续Multicall3逐个读出538/538唯一非零Token地址，及538份**日末**TokenInfo储存状态；3个真实创建事件锚点；日末已迁池的5个另有局部Mint/Swap实证 | 每一TokenCreate确切事件的**原始全日日志覆盖**、creation时点真实接收、曲线实时准入、税费与全币种可卖能力 | `538_INDEXED_END_DAY_STATE_COMPLETE_IN_SCOPE`，`CREATE_EVENT_COVERAGE_UNVERIFIED`；不能用迁池5例作无偏总体 |
| 现有第二供应商 | The Graph V3用户Mac受限首次查询此前实得`HTTP_403`；OnFinality 2025历史2000与10区块`eth_getLogs`此前均`HTTP_429`；公共BSC RPC官方列出endpoint明确禁用logs | 可合法免费导出、完整且可重放的独立BSC历史原生事件/索引 | `SECOND_SOURCE_NOT_QUALIFIED` |

**本轮独立连接器试验（不涉及付费）**：既有Blockscout MCP连接初始化后，对预冻结五月V3阳性锚点tx `0xdc17cf044b461178d0ba629239e9935c3a9c9d941e88848fab9c654479d7c2a4`调用只读`get_transaction_info(chain_id=56)`，服务明确响应`Chain ID '56' is not supported by the Blockscout API`；其`get_chains_list(query='BNB')`仅返回Matchain (Chain 698)，不包含BSC。**只证明此时此连接方式不可读取BSC，不能外推为Blockscout网站或所有索引永远不支持BSC。**其当前服务提示2026-10-08起要求PRO授权；没有添加/购买密钥、没有尝试绕过限额、没有转入其他计费计划。官方文档：https://mcp.blockscout.com/ 。

### 2. 免费V3单日完整扫描的可量化最低成本与防误判

原冻结2025-07-01 UTC链高度`52440287..52555482`（含两端115196块），Alchemy官方现行**BNB Free eth_getLogs 每次至多10块、每调用60CU**。仅扫描一个固定V3 Factory `PoolCreated` topic、**不计**首末区块校验、重复/失败重试、Pair状态、V3 ticks/Swap、Four.meme或其它场所，最低需要：

- `ceil(115196/10)=11520`次日志查询；
- `11520×60=691200 CU`；这占供应商公开Free每月30M额度的约2.304%，**不是现有用户实际订阅、剩余额度、月账单或成功率确认**；
- 官网当前标示单应用最多500CU/秒，则仅这些请求的纯吞吐数学下界为`691200/500=1382.4秒`，约23.04分钟，未计任何网络等待、退避/429、归档、跨源校验；原每扫描日≤30分钟只是性能目标，无法预先声称通过。

当前官方来源（2026-10-23已读）：
- https://www.alchemy.com/docs/chains/bnb-smart-chain/bnb-smart-chain-api-endpoints/eth-get-logs
- https://support.alchemy.com/articles/5827006872-what-is-included-in-the-free-tier
- https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/
- https://thegraph.com/docs/en/subgraphs/querying/introduction/ 需有效API key，已有用户Mac授权受限查询返回403，其根因尚未被实际证明。
- https://mcp.blockscout.com/ 当前连接接口Chain 56不支持，不能作独立BSC交叉源。

结论并非“历史V3扫描在金额上不可能”，而是**仅证明标称CU量低于供应商宣传月度Free总额**，不证明旧块的完整响应、全局来源一致性和原始HTTP归档；更重要的是，2026年今日回读2025年事件**无法补造2025年当时的公众收包时间**。若预期输出仍是原合同24/30 `PIT_VERIFIED`，批量读取11,520个窗口不能独自清除PIT障碍。避免为了表面“扩数据规模”去消耗请求配额后仍无法过门。

### 3. 原路线与具体执行决定

**本轮决定`NO_BULK_V3_SCAN`、`NO_GRAPH_RETRY`、`NO_PROVIDER_CHURN`**。它们是基于未解的PIT与账户访问缺口暂缓大规模无价值调用，**不是判定V3永远不存在免费源，更不是用户拒绝未来前向方案**。不新增Stage脚本、隐藏定时、用户Mac读/后台持续读取或新API账号；没有读取私人API key。沿架构合同三步回答：

1. **来源与时钟**：BSC V2仅限历史冻结样本; V3限三个真实10块窗口; Four.meme限538个日末索引状态。每个场所独立`SOURCE_SCOPE`和`PIT_STATUS`，不能拼成“全BSC高覆盖率”。历史真实`available_at=UNKNOWN`仍必须fail closed；采用未来冻结延迟时也只能标`PIT_RECONSTRUCTED_ONLY`。
2. **真实双向交易**：已证实际历史部分买卖；统一研究金额、税、V3区间流动性、曲线与卖单保护均欠缺，不给缺失样本赋0盈利/0成本；不要从上述5个已毕业Four.meme池或V2七组回售得出策略信号。
3. **停损与后续**：原2026-11-02历史P0源止损时间保持；截止前仅在有**新的、可实际验证**的合法免费完整事件源或历史收包档案时重新评估历史方向。若无则按架构停止历史P0，`P1 BLOCKED/G6 NO_GO`，未来若用户**另行明确授权**前向观察的执行环境、时间、配额、存储与成本，可独立评估ADR-003的D1来源覆盖试验；**不得用前向结果倒签2025的历史PIT PASS**。

权限/审查：本轮仅Git合同内既有P0 MD追加、既有远端数据与只读供应商能力确认，无真实交易、部署/调度、邮件、Mac进程、付费源、全面历史扫描。未执行新增Python单测/全仓CI/独立Review，本次不声称Phase门禁提升。维持`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`。

## 2026-10-23：七组已冻结历史同接收地址买卖的真实链上回执再次核验

固定证据来源：既有P0机器JSON Git blob `978f437788689eef265b47511fa963490c3e9c96`，只使用原冻结2025-07-01 UTC BSC V2 **30个CA**中早先找到的#3/#7/#12/#13/#21/#23/#30，不增删样本、不按胜者筛选新母体。本轮重新通过**用户既有Alchemy BNB mainnet app**只读取得上述七组买入、卖出的14份真实`eth_getTransactionReceipt`规范化响应，核对成功status、同一代币的Transfer方向与数量、Pair的Swap方向及数量、先买后卖的区块顺序。实际**14/14 receipt成功、14/14 Swap与Token Transfer对应、7/7买入后同一接收地址向同一池卖回精确相同Token原始数量**。原先来源包含单供应商规范化结果；**本次只是再读相同Alchemy供应商，不是跨节点独立证明，不保存原始完整HTTP响应或2025年实时观察回执。**

七组不是七名独立正常交易者：#3/#13/#23由同一自定义合约`0x7347a30460516c8451687d9b1fc61efec6f8dae6`接收并回售Token，另外#7/#12/#21/#30为四个不同EOA、经PancakeSwap V2 Router调用。已按原始`eth_getTransactionByHash`再次核实后四组**8笔调用**，买入selector `0x7ff36ab5`、卖出selector `0x18cbafe5`，8/8动态ABI定长参数与早先保存的`amountOutMin`和`deadline`完全一致。**4/4卖出amountOutMin=0**，即零最低到账限制；4/4卖出deadline为**13位数值**，合约解释为Unix秒时显著远在2025年区块时间以后，实质缺少短期有效期保护。此四笔成功卖出**不应当被模型升级为有合理用户价格保护的安全卖出路径**。实际交易成功不代表反例下不会遭受恶意滑点、夹子或无法卖出的风险。

同四笔EOA卖出，链上receipt中WBNB `Withdrawal`事件**4/4均有且值逐wei与Pair的WBNB卖出输出匹配**，证明池的WBNB出流进入Router后成功发生相应WBNB解除包装；这是更强的实际兑换路径证据，但**尚不是逐交易追踪的最终EOA原生BNB净到账**。既有历史EOA区块前后余额变动一致仅限区块级，可能受到同块其他资金事件影响。尝试仅针对#21卖出区块通过既有Alchemy的`getAssetTransfers(category=internal)`补证，明确返回`The 'internal' category is not supported for this network`；**是接口能力缺失，不是零内部转账，也未升级付费trace**。

| 原冻结rank | 接收路径 | 历史实际池侧买入WBNB | 历史卖出池侧WBNB | 池侧毛差额WBNB | 本轮source复验 |
|---|---|---:|---:|---:|---|
| 3 | 共享自定义合约 | 0.001100 | 0.001347005 | +0.000247005 | 双向Transfer/Swap严格匹配 |
| 7 | EOA+Router | 0.012000 | 0.011940360 | -0.000059640 | 双向匹配，0最小输出，Withdrawal匹配 |
| 12 | EOA+Router | 0.250000 | 0.249547777 | -0.000452223 | 同上 |
| 13 | 共享自定义合约 | 0.001100 | 0.001383378 | +0.000283378 | 双向Transfer/Swap严格匹配 |
| 21 | EOA+Router | 0.005000 | 0.009725401 | +0.004725401 | 双向匹配，0最小输出，Withdrawal匹配 |
| 23 | 共享自定义合约 | 0.001100 | 0.001376363 | +0.000276363 | 双向Transfer/Swap严格匹配 |
| 30 | EOA+Router | 0.300000 | 0.304689368 | +0.004689368 | 双向匹配，0最小输出，Withdrawal匹配 |

注意毛差额仅为每组已观察原池的Quote in/out差值，虽为真实成功交易，**仍不是最终钱包净收益**。4组EOA的8笔`effectiveGasPrice=0x0`也由本轮receipt再次观察到，不能单凭零字段推定用户能免费执行；3组自定义合约交易有非零Gas字段，但代付、合约内部转出与最终受益人未知。七组观察到的Transfer/Swap精确配对只证明**这些特定金额与当时地址路径**的实际执行，不保证任意金额/任意买家/其它时刻的代币税、最大可卖容量或保护程度。

**P0门禁不升级：**原30币中29份精确部署receipt、24份合格历史储备、22笔合格后历史BUY、18个历史达标池SELL继续分别保持已有source-grade；本轮七组包含在前述18例以内，**不可重复算新增7例**。公开实时`available_at(2025)`仍UNKNOWN、跨V3/Four.meme完整母体未证、统一研究名义额与税费及可执行退出验证欠缺。正式`24/30 PIT`与`18/30统一名义额双向可卖`均`NOT_SCORABLE`，`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`，原`2026-11-02`历史源决策截止不变。本轮未改源码、无新测试/CI或独立Review声明，无交易、部署、持续监控、邮件、付费源或用户Mac操作。

## 2026-10-23：冻结30例中22笔真实历史BUY的入场价格冲击

**本轮实际进展**：GitHub远端固定P0原证据JSON blob `978f437788689eef265b47511fa963490c3e9c96` 已重新读取，保留冻结30个CA/Pair，精确匹配先前有真实receipt的20笔后续BUY与#16/#17两笔独立后续BUY，总计22/30。20+2都在已归档的首次达标储备区块**之后的独立区块**，对应token/pool/rank无冲突；余8例记`NOT_SCORABLE`而非零成本/无买入。全部是真实历史交易的精选证据，未证明“首次公开可买时刻”，不可当成随机全市场样本。

采用已获官方文档支持的PancakeSwap V2固定0.25%池费、交易前Quote储备与所选真实BUY的入池Quote数量，计算真实所选BUY的**理论平均成交价格相对交易前池中间价的溢价**（fee-inclusive effective execution price premium）。实现采用正整数精确有理式、向上取整到micro-bps；`100bps`仅为**本轮诊断示例**，不等于已获批用户研究金额、买入规则、模型参数或统一入场费率上限。当前冻结真实数据得到：
- 22笔所选BUY中位`115.930127bps`（约1.159%），最小`25.125157bps`，最大`387.353275bps`；
- `14/22`理论池层入场价格溢价大于`100bps`；其中`2/22`大于`200bps`。
- 成本表示交易前储备和真实池输入量的AMM理论平均冲击；单币转账税、第三方路由、Gas/MEV、持币能否卖出、买卖钱包经济利益、交易选择偏差均未证明，不能当实际净损益或投资指令。

**口径纠正**：最初临时计算值`13/22`及`114.6007555bps`对应相对理论无摩擦兑换数量的**输出折减**，与成交价格溢价略有不同。原先写成“平均成交价格冲击”的表述不够精确；正式此节采用价格溢价口径，诊断阈值与计数按14/22重算。两种量纲不可混用，也不能把诊断阈值升级为策略冻结参数。

**可复验代码与实际离线测试**：`local-agent/mission_agent/early/entry_impact.py` Git blob `57a10563d90776c68ae3181e5e96e47e3bec9484`，`local-agent/tests/test_monster_p0_entry_impact.py` Git blob `453051a7eb259b6f0b3afc022a4bf46d81629c8c`。本轮隔离Python实际执行该两文件逐字节一致源的**5/5 unittest PASS**（模拟fixture，包括30分母、8缺失、错误池、重复rank、未来时序、失败receipt、参数坏值和未来标签注入）。并在GitHub连接器环境对完整真实JSON以同一整数公式复算22笔，得到以上金额无关的诊断汇总，但**尚未在Python测试环境读入整份1MB远端真实JSON**；不可宣称Mac复算/完整仓库CI/独立AI Review通过。没有额外实际RPC、原始字节采样、付款、邮件、定时服务、真实交易或模型。

**状态保持**：历史2025`available_at=UNKNOWN`，且V3/launchpad完整分母、统一研究金额/税/双向可卖性未证实，`24/30 PIT`、`18/30可卖`均`NOT_SCORABLE`；`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`，2026-11-02源止损截止不变。该分析只为强调价格冲击是实际收益/交易性验证不可跳过的一环，不替代完整来源和真实退出证据。

## 2026-10-23：原冻结V2三十例的历史池容量上界（AMM_MATH_ONLY，价格溢价公式已复核）

**业务口径修正（P0成本关键路径）**：此模块旧实现将“相对理想兑换量的输出折减”（quantity shortfall）按“相对交易前中间价的成交价格溢价”（effective execution price premium）命名，导致后续容量上界被高估约1.348%（以修正后值为分母）。本次统一采用后者，与`entry_impact.py`的22笔BUY诊断一致；真实来源/实验对象和100bps诊断示例均不改变。该修正影响**静态数学容量口径**而非链上已成交事实，不能视为P0验收通过。

本轮从Git远端已存P0 JSON blob `978f437788689eef265b47511fa963490c3e9c96`，以精确CA/Pair/rank核对完整30例与24份下一完整区块末端储备：30个唯一身份、24个有历史储备、6个无足够储备证据（保留`NOT_SCORABLE`）。复核既有29个准确部署receipt、22个达标后历史买入、18个储备达标的真实历史卖出，集合身份/子集关系没有发现冲突。此为既有规范化证据离线重新计算，并未新增链上RPC或独立原始HTTP字节。

为在**不预设用户下单金额**的前提下量化静态池大小，使用只针对PancakeSwap V2恒定乘积的整数数学上界：假设一侧输入收取25bps AMM费，在历史`getReserves`快照上，将相对池中间价的平均成交价格影响（包括该AMM费）限制在100bps，则`max_input_raw = floor(reserve_in_raw × [100 × (10000 - 25) - 25 × 10000] / [10000 × (10000 - 25)])`。这是`effective_execution_price / pretrade_mid - 1 <= 100bps`的连续AMM数学上界；整数Swap向下舍入可能造成dust输出为0，因此不是链上真实可成交额度。100bps是**敏感性演示参数**，不是获批研究入场阈值、投资建议、历史实际成交，也不改变已有合同或固定入场判定。

| 冻结历史报价资产 | 有储备快照的池 | 单池最大AMM数学买入量（原报价资产，100bps含池费） |
| --- | ---: | --- |
| WBNB | 23 | 最低约0.018734 WBNB；中位约0.112406 WBNB；最高约0.450298 WBNB |
| BSC-USDT | 1 | 约74.937343 USDT |

正反方向独立给出理论输入容量，但**不能**把历史同一瞬间的买侧与卖侧上界拼成可执行往返；缺失币的容量留空，不填0。代币手续费/转账税、路由约束、Gas、MEV、交易时点前向变化及历史公众`available_at`仍然UNKNOWN。因此正式`24/30 PIT`与`18/30同研究金额双向可交易`均`NOT_SCORABLE`，`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G6 NO_GO`不变。

实现复算逻辑复用同一个`local-agent/mission_agent/early/quote_capacity.py`包文件，从原30条冻结身份精确关联历史24条储备并保留其余6条UNKNOWN，另有`local-agent/tests/test_monster_p0_quote_capacity.py`。两份远端blob与本次隔离执行过的Python源文件逐字节一致，分别`94b7f789e7210749c4c287f6c4c50be17c294268`和`706f91f7254daa6cbc8d5399a86b55cc52dd23e3`。隔离Python使用Git exact-blob对应源码执行该模块**9项离线unittest，9 PASS、0 FAIL**，新增与`entry_impact.py`的数学边界一致性测试；没有声称整个仓库测试已通过、Mac运行、CI或其他AI独立Review。模块没有网络、默认投资名义额、订单或监控。

## 2026-10-23 已授权唯一一次 Mac 前台真实采样

MANUAL_FORWARD_READONLY_PILOT_PASS。授权评论6357433481。本次真实执行恰好1次，无重试。旧隔离目录HEAD为6403be09，故旧脚本目标c646校验失败；未reset或删除，改用全新detached worktree精确c646。运行源码blob及Python模块实际导入位置全部匹配批准checkout。Mac Python3.14.7 / arm64；load4.41/3.30/2.73，memory_pressure可用85%，磁盘437GiB，私有父目录原为空且0700。未接触私钥或私人API key，使用已批准公开无密钥端点，仅对子进程传环境变量。

12次RPC，Chain56，两计数均3535217；区块129259581→129259583，中间129259582 hash/parent连续，固定块前后及首尾anchor回读通过。NEW_FACTORY_PAIRS=0，身份读0，未读0；只代表这两个Factory快照之间零增长。实际计数完成间隔1.039858708秒；capture2.934009458秒（到manifest写入前）。UTC调用起点04:40:46.573513Z，最后响应完成04:40:49.506294Z；本地日期2026-10-23 Asia/Bangkok。12份正文SHA256逐份读取字节重算全部通过，目录0700、原始文件及manifest0600，无failure.json。原始正文仅保存在Mac私有目录，未上传Git。

单提供商本地收包不是全网首次公开时间/独立认证，未证明finality、V3/launchpad完整分母或任何交易容量/税费/可买可卖/收益。历史available_at UNKNOWN、P0 INSUFFICIENT_COVERAGE、P1 BLOCKED、2026-11-02截止不变。技术采集链路值得保留，但零增长短窗口不足以支持扩大研究或模型；任何额外采样/长期观察均需新授权。本次授权已经消耗，不自动复跑。无部署/调度/邮件/交易/生产变更。

脱敏可核摘要（不含完整HTTP归档或私人端点）：

```json
{
  "snapshots": [
    {
      "all_pairs_length": 3535217,
      "block": {
        "chain_timestamp_seconds": 1792730446,
        "hash": "0x819a2aea91f319460fab3706242514762cc4a0662c8b02a3826fc00855f76c74",
        "number": 129259581,
        "parent_hash": "0xc63e4635aa5b54adf08fb580cf9a7b87ecc0909c16c05de659f68531a7396996"
      },
      "count_observed_at_utc": "2026-10-23T04:40:47.452511+00:00",
      "count_response_monotonic_offset_ns": 879018125
    },
    {
      "all_pairs_length": 3535217,
      "block": {
        "chain_timestamp_seconds": 1792730447,
        "hash": "0x78c2d2a858edcfd0457724103e9f8d8b444aced4ee148aa874a25927230a5089",
        "number": 129259583,
        "parent_hash": "0xb38361313dba5a8a876307a1560a86abc6a2d05c1784b1c5ac7d717a29274171"
      },
      "count_observed_at_utc": "2026-10-23T04:40:48.492376+00:00",
      "count_response_monotonic_offset_ns": 1918876833
    }
  ],
  "rpc_attempt_count": 12,
  "new_factory_pair_index_count": 0,
  "new_pairs_read": [],
  "unread_new_pair_count": 0,
  "count_response_interval_monotonic_ns": 1039858708,
  "capture_elapsed_monotonic_ns": 2934009458,
  "capture_started_at_utc": "2026-10-23T04:40:46.573308+00:00",
  "capture_completed_at_utc": "2026-10-23T04:40:49.507512+00:00",
  "status": "MANUAL_FORWARD_READONLY_PILOT_PASS",
  "runtime_commit": "c646d438ebdd33183e047e47323315d78aab2869",
  "runtime_blob": "5e41458eb199599a861498260bda895f525fb1b6",
  "authorization": "6357433481",
  "execution_count": 1,
  "raw_sha256_recomputed_pass": 12,
  "archive": "~/Library/Application Support/MonsterResearch/forward-observation/authorization-6357433481-once",
  "manifest_sha256": "7c56cdb160815d0e01440ceb08517ca8dc4a7cc4c5a7f44d89926ed55eb4d5d0",
  "permissions_verified": true
}
```

## 2026-10-23 Mac验收关闭代码遗留问题

固定c646d438本轮实际115/115测试通过，新增9项全部通过，独立子agent二审实际完成：APPROVE_OFFLINE_CODE。RPC环境变量未配置，MANUAL_FORWARD_READONLY_PILOT_BLOCKED。完整命令、日志和边界见 local-agent/tests/evidence/monster_forward_review_20261022/acceptance-c646-review.md。本轮无源码修复、无真实RPC。以下为此前历史记录。

## 2026-10-23 独立 Mac 离线审核与修复（待完整负例复验）

基线 `89868fa08c90f91d8983cebce850631faa9f05ba`，远端初查相同。真实 Mac Darwin arm64 / Python 3.14.7，隔离 checkout `/private/tmp/monster-forward-review-20261022`，独立 venv，无真实 RPC。主工作区 x-revenue 脏文件未动。

基线结论 REQUEST_CHANGES：P1 实际计数窗口可达40秒仍成功、跨RPC UTC回拨、socket timeout并非总deadline、Content-Length截断被接受；P2 query凭据回显/默认文件权限、跳块祖先未验证、重复池未拒绝。独立审阅由本会话三个子agent实际完成基线负例；修复后二审因额度中断，不能宣称已完成。

本次最小修复位于 forward_observation.py：专用只读 transport、20秒整个请求deadline、HTTP长度核验、凭据回显拦截、0700/0600；实际count完成间隔最多3秒、整capture耗时独立记录、本地UTC/monotonic一致性、跳块祖先核对并在20次内动态减少身份覆盖、重复池拒绝、ABI计数word核验。历史shared transport、PIT定义、冻结样本和ADR均未修改。

实际命令在 local-agent 目录：`/private/tmp/monster-forward-review-env-20261022/bin/python -m unittest discover -s tests -p PATTERN -v`。PATTERN及结果：基线 test_monster_forward_observation.py 15 PASS；test_monster_pit_asof.py 24 PASS；test_fourmeme_index_source_probe.py 11 PASS；test_monster_early*.py 38 PASS；修复后 test_monster_forward*.py 33 PASS，0 skip。测试仅fake/in-memory/127.0.0.1，未接外部RPC。原始输出在 local-agent/tests/evidence/monster_forward_review_20261022。初次修复后transport fixture缺status导致21 errors，补齐真实HTTP fixture字段后33通过，保留最终输出。尚未完成修复后新增时窗/时钟/祖先全部独立负例回归，因此最终 REQUEST_CHANGES，不能以33项通过替代未覆盖项。

环境：当前进程 MONSTER_BSC_ARCHIVE_RPC_URL 未设置，主checkout根目录和local-agent均无.env；连接器已有免费应用不代表Mac CLI已配置，免费额度未联网核实。已建私有目录 `/Users/jerson/Library/Application Support/MonsterResearch/forward-observation`，权限0700，无采样数据。最多20次RPC，单次总deadline20秒，无重试，真实运行需独立授权且仅一次前台。16核Mac初查load 2.69/2.24/2.34，空闲盘437GiB；这是瞬时快照，真实运行前须重新查看CPU/内存，不停止任何现有进程。没有安装launchd/cron或修改生产服务。

最终：REQUEST_CHANGES / MANUAL_FORWARD_READONLY_PILOT_BLOCKED。剩余阻断为修复后时钟/祖先/实际窗口负例复验与独立二审，以及Mac RPC安全配置。历史2025 available_at仍UNKNOWN；本机收包时刻不是全网首次公开时间，Factory增长不证明流动性、税、可买可卖、固定金额容量或利润。NO_MERGE / NO_DEPLOY / NO_TRADE / NO_GMAIL，P1仍BLOCKED。

# Monster P0 — 免费历史源实测：BSC V2工厂存储枚举方案（2026-10-19）

## 2026-10-22：前向本地时钟证据试验——离线原型已入Git，未运行Mac

依据用户同意继续**准备**前向只读验证、未授权后台运行/生产部署的范围，提交新[ADR-002](../../../adr/ADR-002-forward-only-observation-pilot-20261022.md)，**只为此项新增研究路径记录边界**，不取代ADR-001或历史P0冻结24/30、18/30门槛。原2025-07-01 BSC V2 30例、Four.meme 538例、当前source-stop`2026-11-02`仍未修改。新工具不是新Stage、自动买币信号或P1模型。

**真正实现**：`local-agent/mission_agent/early/forward_observation.py`，复用已存在的`fourmeme_index_source_probe.JsonRPC`（HTTPS/无重定向、禁回显秘钥、限制响应大小），一次`--manual-once`调用只采两个BSC主网`eth_blockNumber`快照与对应区块头、同块`PancakeSwap V2 Factory allPairsLength`；若Factory索引增长，至多验证3个`allPairs(index)`池地址、`token0/token1`。请求白名单仅`eth_chainId/eth_blockNumber/eth_getBlockByNumber/eth_call`，最多20个RPC，快照间隔0–3秒；相邻父hash、重读原区块hash与索引单调性失败即生成`failure.json`并拒绝标`manifest.json`成功。新目录仅写一次，逐次保存原始RPC响应体字节、SHA256、调用开始UTC、处理完成UTC与单调耗时；输出不含完整RPC URL/API key，不生成交易、不调钱包、不设购买名义额。

**核心证明限制**：`local_response_completed_at_utc`只是**本地处理完此RPC返回的UTC时间**，不是全网首次公开时间，也不是可交易的`T_entry`或经过第三方可信签名的时间。旧2025`available_at=UNKNOWN`不会自动填补。BSC V2 Factory index增长并不等于新代币数量、有效流动性、买入/卖出或可达5x；若零增长，只能说这两个观察区块的Factory计数无增加；超出3个身份时必须保留`PARTIAL`。只适用于V2，不假装覆盖V3、Four.meme全部launchpad或整个BSC。

**实际执行与复核**：独立Python 3.13.5离线运行`python3 -m unittest discover -s tests -p test_monster_forward_observation.py -v`：**15/15 PASS，0 skip/error/fail**，覆盖2次完整快照、原始SHA、20次调用上限、过载部分覆盖、错链、同高计数矛盾、链头倒退、Factory倒退、重组、无效地址、输出不覆盖、原响应矛盾和时钟声明。GitHub远端`forward_observation.py` blob SHA=`696846648e12fc6308857b3fad8d0d39df87736f`，测试文件blob SHA=`dedd847cb33e7758dbbea10795a89767025db4f9`，两者均与独立本地执行时`git hash-object`一致（大小分别10,988与9,063字节）。**未运行旧Monster全套测试、独立第二AI审核或用户Mac真实前台采样**，测试结果仅说明固定源码的离线行为。

**现有免费连接器真实小范围技术检查**：2026-10-22，已选定的原Alchemy免费`bnb-mainnet`应用实际返回`eth_chainId=0x38`及链头`0x7b2afc1`；在相同高度只读调用Factory `0x574f2ba3` 得`0x35e3aa=3,531,690` 个历来创建的池索引。**这只是连接器实测Factory计数，不是上述Mac采集器的实际运行、不是一次真实检测到新Pair，也不是公开可观察时间的独立可信来源**。

**门禁保持**`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`。没有Mac部署、定时任务、CI Action、GMGN、付费RPC、交易、邮件或合并。下一次合格工作是先独立代码/源协议审查，再单独取得用户对**一次性Mac前台调用**的明确授权、核实原响应完整性和系统时钟可信度；绝不能自动升级为常驻监听。

## 2026-10-22：独立BSC历史源复核的真实能力结论（未通过）

**本次只复核P0来源门禁，不更改冻结样本或开始P1/模型。**目标是找一条独立于现有Alchemy免费BNB主网RPC、可以对**已冻结2025-07-01**历史交易或PoolCreated原事件完成真实读取的第二通道。结论绑定本轮PR固定前置SHA `f5a0ae21d13fb44bd09bfff904ba871ac7623678`；查询均为只读，未使用账号充值、付费API、私钥或链上写入。

| 路径 | 本轮实际行为 | 结果 / 不能推断 |
| --- | --- | --- |
| BNB Chain官方公共主网RPC | 官网核对ChainID 56和RPC限制（https://docs.bnbchain.org/bnb-smart-chain/developers/json_rpc/json-rpc-endpoint/） | 官方列明公共节点**禁用eth_getLogs**；即使单笔`eth_getTransactionReceipt`将来能返回，也不支持本研究的完整Factory事件分母；本轮在可用容器网络尝试官方RPC域名DNS失败，因此**没有拿到第二来源的真实2025收据** |
| Blockscout已连接数据插件 | 新session实际`get_chains_list("BNB")`仅返回Matchain ChainID 698；`get_chains_list("BSC")`为空；用2025-07-01实际交易`0xf3891e0391d6704401e2788ee6f09dc75b2b1e2e722fe86be74f437fa0823e0c`直接调用`get_transaction_info(chain_id="56")` | 明确返回`Chain ID '56' is not supported by the Blockscout API.`。**UNSUPPORTED_CHAIN**，不能误记BSC主网已二次验证 |
| BscScan和BSCTrace浏览器交易页、bnbscan.com交易页 | 对上述已冻结交易tx访问页面 | web工具均返回网页不可访问，不是「未上链」「0笔交易」或已复核 |
| Binplorer独立BNB索引 | 检索其公开API合同（https://github.com/amilabs/Binplorer/wiki/Binplorer-API），尝试同笔实际历史tx的免费`getTxInfo/{hash}?apiKey=freekey` HTTPS GET | 官方文档有接口及免费开发key，但其公共`freekey`限定请求速率和`Max allowed timestamp age: 30 days`；**2025年历史覆盖未经证实**。本轮web连接器对具体请求返回不可访问，`NOT_TESTED_HISTORIC_ACCESS`，不宣称有历史收据/完整Factory扫描，更不通过绕限额多号/付费方式验证 |
| Alchemy现有单提供商 | 复核冻结P0原记录：30/30原V2 Pool身份、29份独立部署交易、24份报价侧深度证据、22笔后续BUY、18笔SELL；另538 Four.meme索引的5个事后已迁池池 | 有**单提供商的历史链上存在性**与部分买卖事实；无原始完整HTTP bytes/独立RPC复核，**2025公众`available_at`仍全未知**，没有事前固定同名义金额的真实费后可卖出收益 |

**必须分离3个成功条件**：①能拿到某个2025年交易的独立`txHash/blockHash/receipt`（本轮**未完成**）；②能连续枚举BSC V2/V3以及预定launchpad的**完整历史母体，无漏页/缺块**（本轮**未完成**）；③当时公众**可观察的接收时间`available_at`**和普通用户在该时点的可执行买卖路径（**未完成**）。①即使以后通过也**不能替代**②③。现在切换RPC或继续研究5个被事后筛出的迁池成功案例，不能合理提高P0正式通过率。

**执行上的止损**：严格沿用既有一页P0决策`bsc_v2_p0_frozen30_one_page_source_pit_trade_gap_decision_20261020`的`STOP_FURTHER_FREE_RPC_ENDPOINT_CHURN_AND_P0_REPORT_LOOPS`；不继续按所谓免费provider挨个盲试、不触发本研究仅有的2次手动CI预算，也不部署Mac/生产shadow。仅有**真实新增、可核验、合法免费、覆盖原冻结日期且有原字节的来源**才允许重新审查该阻断。原`2026-11-02`source stop日不变。若到期仍不可证，依旧P0`INSUFFICIENT_COVERAGE`、P1`BLOCKED`、G4`UNKNOWN`、G6`NO_GO`；任何独立forward-only观察需要另外决定，不能默认授权开启。

## 2026-10-22：独立PIT代码复核——阻止链下公告携带未来链上时钟

本轮没有扩展事后筛出的5个Four.meme迁池样本，没有重复计算同一30例历史收益，也没有把新源码视为P1通行证。固定原`monster_early_records_v1.schema.json`的`chain_event_at` **可为null**及公共来源分级合同，发现新增的离线`pit_asof.py`存在两项真正影响主线的缺陷：

1. **链下公告的正常缺失时钟：**Alpha/Spot/USD-M的`ANNOUNCED/LISTED`类事件，允许仅有可验证的公告`published_at/available_at`而没有链上事件时间。旧实现无条件解析`chain_event_at`导致输入null时报错。新版为上述明确的链下事件保留null，同时要求真正链上部署、建池、Swap类事件有链上时钟，否则不评分。
2. **提前公告中的未来链上时间泄漏：**旧实现对`ALPHA_ANNOUNCED`等允许`available_at < chain_event_at`，但仍会将尚未发生的`chain_event_at`字段放进历史`asof`输出。新版只允许返回`chain_event_at <= decision_at`的事件；未来可见时间也会被过滤。必要的`available_at < chain_event_at`链上时间矛盾仍抛错，不得因新过滤逻辑吞掉源数据不一致。

**实际执行，不仅是Git提交：**本次在独立本地Python 3.13.5环境，按GitHub源码逐字建立隔离文件（不连接RPC）；本地`git hash-object`与新远端源码Blob **`8cbf3a0fbde612e6457960a93785ac73cf184666`**相符，测试Blob **`10f8301e46d66d9136f0846b35aa79b8f1f8582c`**相符。运行`python3 -m unittest discover -s /tmp/monster_p0_verify/tests -p 'test_monster_pit_asof.py' -v`：**Ran 24 tests, OK，24/24 PASS，0 FAIL/ERROR/SKIP**。新增4项验证链下null时钟、未来链上事件时间不泄漏、链上事件null不可评分及无链上时钟不可通过历史假设补造。还保留原20项中的不一致来源时钟必须拒绝测试。测试只证明这两份源码在离线mock输入下表现，不证明外部`PIT_VERIFIED`输入标签真实性或P0数据源满足要求；`p1_gate_passed=false`始终维持。

**独立外部来源替代排查（免费且只读）：**Blockscout连接器当前可用链目录用`BNB Smart Chain`精确检索无匹配，服务明确提示2026-10开始PRO API授权限制，不把它视为有效的第二BSC RPC来源，也没有购买key。BscScan两个已有实际交易哈希在本会话网络读取路径不可访问，**没有**把网页访问失败记作源数据无交易或第二提供商验证通过。官方2025年公开到达时间/原HTTP字节、完整V3与其他launchpad分母、事前统一研究金额和实际用户卖出费后结果仍未解决。

**阶段与权限仍为**`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`；原研究stop日`2026-11-02`不变。没有CI Actions、Mac后台、付费查询、生产部署、签名、交易或邮件；未修改冻结研究合约、母体及名义额。下次主要应直接验证可得的真实来源/开放时钟证据或诚实止损，不进行新的微小建池事件追逐。

## 2026-10-22：历史PIT的离线asof严格门禁与20/20回归

**本轮不再扩大已知5个迁池币的短窗交易查询，也不选获利赢家。**依据原架构`MONSTER_EARLY_ARCHITECTURE_CONTRACT_V1.md`第5节与`monster_early_records_v1.schema.json`的`events`时间/来源字段，增加**一份纯离线P0证据as-of裁剪实现**：
- `local-agent/mission_agent/early/pit_asof.py`：`asof(token_key, decision_at, information_policy, *, events, historical_delay_ms=None, historical_delay_policy_sha256=None)`。只返回对应token_key、决策时点前合格的经过字段白名单裁剪的事件，不直接向下游暴露未来成交量、持仓、Alpha、未来收益标签；同事件重复回放幂等、同ID相互矛盾fail-closed。
- `LIVE_OBSERVED`只接受明确`PIT_VERIFIED`且按`ACTUAL_LIVE_OBSERVER_RECEIPT`或`ACTUAL_HISTORICAL_PUBLICATION`**有时间字段声称**的输入；没有`available_at`直接不进入视图。程序本身**并不能审验原始签名/第三方历史来源真实性**，因此所有返回结果固定`source_provenance_independently_verified=false`、`p1_gate_passed=false`。这里的`PIT_VERIFIED`仅是输入证据声明经过时间一致性筛选，**不得误当独立来源认证或批准P1**。
- `RECONSTRUCTED_CONSERVATIVE`额外允许预先明确给定`historical_delay_ms>0`及`historical_delay_policy_sha256`的延迟假设，任何该模式输出的汇总等级**最高`PIT_RECONSTRUCTED_ONLY`**；SHA只是被记录的引用，不证明假设本身得到审批。此阶段**未冻结具体延迟值**、未设置默认值；不会用此前5例链上750ms出块间隔伪装普通用户收到通知的延迟。
- `NO_VERIFIABLE_ASOF`永远返回`NOT_SCORABLE`且无事件，未来数据、未知来源及时间异常fail-closed。所有模式只用于P0源码防泄漏负例验证，**未接入生产交易、训练、日常监控、邮件或Mac后台服务**。

**真实执行的离线测试与字节核对**：独立本地Python运行`python3 -m unittest discover -s /tmp/monster_p0_offline/tests -p test_monster_pit_asof.py -v`，**20/20 PASS，0 SKIP、0 ERROR、0 FAIL**。本机两份镜像文件的`git blob` SHA1分别为`884973b93bef0fbe1483d04176d22fd53020c2e4`（模块，6694字节）和`882115e5e887b129b4c571a2c9e493539ad7e583`（测试，8967字节），与GitHub最终所写入内容blob一一相等。测试内容包括时区/毫秒时钟边界、未来事件与未来结果污染反例、未知来源/时间、跨CA的同名混淆、矛盾重复事件、强制预冻结延迟参数及P1默认拒绝。**没有调用真实网络、运行Mac、运行完整Monster旧套件、启动CI或取得独立AI源码审查**，故结论仅限固定代码的该20项测试。

**P0真实业务差距仍未消失：**原冻结BSC V2 30个身份已核对30/30，已有29份独立代币部署交易、24个样本有报价侧资金门槛证据、22个样本有独立后续买入交易、18个有后续卖出活动；这些计数各自代表不同业务事实，不是可按相同名义订单即时双向成交的18/30。原538 Four.meme历史索引有5个日末完成迁池样本、5个N+1块真实卖出，但这是**事后筛出的已迁池子集**，也没有证明2025同期`available_at`。**以仓库现有资料，没有任何一个上述样本可以因这个新增纯函数便升级为真正的`PIT_VERIFIED+可执行收益`；新工具不生成任何真实观测证据或训练标签**。真正阻断仍是完整历史来源/原始字节与验证、足够场所覆盖、公开可见时点、统一事前研究名义额的真实买卖及费用。不能以输入字符串自称`PIT_VERIFIED`就绕过源审查。

**研发决策**：维持`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`。历史重建敏感性只能在事前冻结参数与独立审查后作为独立`RECONSTRUCTED`研究，不能替换2025同期实测回执。维持原2026-11-02来源终止判断日期，未批准任何新预算、CI、部署、交易、邮件或自动化。

## 2026-10-22：Five个Four.meme迁池池的下一块真实SELL和750毫秒链头时间

使用已冻结2025-07-01 UTC、Four.meme一日538个索引中的**全部5个经TokenManager2状态3+Helper3证实迁池的代币**，在前次已确认的Pancake V2 PairCreated/Mint/Sync创建区块后，单独读取**紧接着的第一个区块**的原池`Swap`和`Sync`单主题日志，逐个按V2的4个Swap金额字解码买入/卖出方向，并与同交易Sync、区块末getReserves及两侧历史区块头交叉核验。

| Four.meme index | 原V2建池块→紧邻下一块 | 下一块真实BUY/SELL | 下一块真实SELL获得WBNB | 卖出前池中WBNB储备 |
| --- | --- | --- | ---: | ---: |
| 247622 | 52449009→52449010 | 0 / 1 | 0.146394754236798148 | 23.519999999451199994 |
| 247633 | 52474140→52474141 | 2 / 1 | 0.300070460751183867 | 26.519999999451199994 |
| 247672 | 52470447→52470448 | 3 / 1 | 0.198424069571668611 | 24.569999999451199994 |
| 247708 | 52511487→52511488 | 3 / 1 | 29.941403750398179781 | 54.436916362204566290 |
| 247733 | 52480580→52480581 | 0 / 1 | 0.246482939595807014 | 24.019999999451199994 |

**SELL交易入口的关键限制：**对上述5笔真实SELL原交易额外核验`from`、`to`、calldata selector及合约在历史区块的代码。**5个SELL中只有2笔为标准Router调用**（`0x10ed43c718714eb63d5aa57b78b54704e256024e`，`swapExactTokensForETH`），并且两笔均由**同一个外部地址**`0x5361d8af3d841e1e858abafb4643a7bbe3c1b5a7`发送；两笔都实际编码了该币→WBNB两跳路径、`amountOutMin>0`与卖出方自身收款地址。另3笔SELL调用了3个当时链上存在字节码的自定义合约，尚未证明其是普通钱包可复用的标准交易路径，也未能核实实际策略、外部控制人及钱包税费净额。这**不构成五个相互独立的散户完成标准买卖**。自定义合约之中2个返回的整段bytecode被Alchemy连接器8KB截断，只有非空代码前缀可证。机器证据及对应tx哈希写在本节所引原P0 JSON的五个rank行内。\n\n**5/5具有真实下一块WBNB流出SELL、8笔BUY、5笔SELL，总计13条同一区块范围内的Swap证据。**每个卖出前储备均超越原冻结2 WBNB报价侧观察档位；这些是历史真实池中交易，并不意味着是同一钱包从迁池前买入再卖出，不代表统一预冻结研究名义金额的可执行买卖或净利润，也不证明接收后普通投资者来得及下单。

新增时钟约束：5组BSC原始区块头的`milliTimestamp`显示PairCreated块到后一块间隔**均为750ms**；其中常规秒级`timestamp`有两组差值为0秒，因此统一使用此来源实际返回的毫秒区块字段，不能用秒级字段推导负时延或交易员真实响应。**区块头时间不是2025年网络`available_at`、不是邮件抵达、签名/广播/确认总延迟。**历史PIT和同研究金额买卖覆盖门槛维持`NOT_SCORABLE`。此外无法由这一块的日志保证某币以后任意时刻可卖，也不保证最低利润。

所有5条选定SELL的`txHash/logIndex`、对应报价流出、卖出前quote储备、建池/下一块准确block hash及milliTimestamp已写入原P0 JSON键`bsc_fourmeme_p0_five_migration_next_block_buy_sell_750ms_20261022`。来源仅为已有Alchemy免费只读单提供商的**标准化返回**，未取得原始无改写HTTP回包字节/SHA或独立节点复核。完整block JSON返回经连接器截断，时钟字段从未截断的区块头前部按blockNumber/hash读取；不能称完整JSON解析通过。仍需验证可观察PIT、网络延迟、税/金额/退路以及完整V3/其他发射场所母体。P0`INSUFFICIENT_COVERAGE`，P1`BLOCKED`，G6`NO_GO`。2026-11-02历史来源截止不变。无新源码或单测、未启动Mac服务、无交易、付费、邮件或合并。

## 2026-10-22：五个Four.meme迁池代币的真实首池Mint和第一批BUY交易

**新增业务证据（未启用模型）：**沿用冻结2025-07-01 UTC、同日538个Four.meme TokenManager2索引里的**全部5个日末状态3且Helper3证实`liquidityAdded=true`**代币，不重选获利赢家。读取Pancake V2 Factory在目标日首/末状态，再对5个固定`token_ca+WBNB`历史`getPair()`二分确定首次非零区块；同一块逐个核Factory `PairCreated`、对应Pair的`Sync/Mint/Swap`事件及`getReserves()`最终储备。5/5准确的Factory事件/池地址/创建交易/同交易`Mint+Sync`成立，5/5首次注入WBNB为**23.519999999451199994 WBNB**，均高于原冻结的2 WBNB观察门槛。最后一条同块`Sync`与该块末`getReserves`各自严格相符，不能把后续Swap后的块末储备当初始储备。

| Four.meme Index | 精确V2池创建区块 | 创建同区块的真实Swap | 方向（WBNB报价腿） |
| --- | ---: | ---: | --- |
| 247622 | 52,449,009 | 0 | 未在**该区块**观察到Swap，后续未知 |
| 247633 | 52,474,140 | 2 | BUY、BUY（2.5 + 0.5 WBNB流入） |
| 247672 | 52,470,447 | 1 | BUY（0.5 WBNB流入） |
| 247708 | 52,511,487 | 1 | BUY（0.5 WBNB流入） |
| 247733 | 52,480,580 | 1 | BUY（0.5 WBNB流入） |

**重要交易边界：**以上5笔真实Swap是**4/5池在创建同一块内、但与最初Mint不同交易**的WBNB流入买单，**没有证明一个卖出腿**。不能从同区块内交易先后推定普通用户收到新区块后还能追上；不能将其计为4个公开可反应的`T_entry`、或5次已经实现的双向买卖。初始23.52 WBNB是迁池的标准化历史池储备事实，不能推导转账税/Router fill、用户持币净额或统一研究名义额收益。日末五池储备已记录在上节，是不同时点的状态，不能作为建池时的可卖出量。

**来源/纠错：**标准化Alchemy免费BSC历史RPC单提供商`getPair`状态、1块`PairCreated`、Pair日志、`token0`与`getReserves`交叉读取。一次手动复制#247708 CA时误少一位，产生了错误的候选块查询；发现长度41不满足42字符CA约束后从冻结JSON重新读取完整地址，重新二分并以真实Factory事件纠正为**52,511,487**，错误临时值未写入Git。所有5个准确行的token/pair/初始储备、事件tx和logIndex、每笔Swap报价方向和哈希在原P0 JSON键`bsc_fourmeme_p0_five_graduated_pairs_historical_mint_swap_20261022`。仍缺连接器原始完整HTTP响应字节、原样SHA和独立节点，2025年当时公众`available_at`均未知。不得把完整10区块查询的**截断回包**当日志零条/证明整段无交易。

**门禁不变：**这是Four.meme的**事后限定来源5个已迁池样本**，不是538币全部可交易资格，也不修改原30个Pancake V2冻结技术候选。P0`INSUFFICIENT_COVERAGE` / P1`BLOCKED` / G4`UNKNOWN` / G6`NO_GO`，2026-11-02原来源决策日继续有效。未运行Mac原始HTTP归档，未用真实或默认研究交易金额、未付费、未部署、未交易、未发送邮件。

## 2026-10-22：Four.meme 538个历史日末曲线状态全量复查，以及5个真实迁池样本

本轮以原冻结 **2025-07-01 UTC**、原日终BSC区块 **52,555,482**、既有538个地址母体作只读来源测试，没有增加/删去原有Pancake V2 30币，亦不改变用户未设定交易金额的规则。直接对Four.meme TokenManager2（`0x5c952063c7fc8610ffdb798152d69f0b9550762b`）的历史`_tokenInfos(address)`（selector `0xe684626b`），通过当日已部署的Multicall3 `aggregate3` **最多7个地址一批，共77次历史RPC** 取得 **538/538条、每条13字段**。按原index→CA逐条核查无重复、无跳号、字段长度准确和子调用成功，规范化结果全部保存在同一P0 JSON键`bsc_fourmeme_p0_all538_frozen_day_end_curve_state_20261022`。中途一次RPC断开未提交新数据，缩小批次后只补剩余区间，最后远端完成538/538。

**来源分层，绝非538个可盈利新币：**

| 历史日末曲线计价资产 | 一日发行索引数量 | `funds>0` 账面状态 | `funds=0` 账面状态 |
| --- | ---: | ---: | ---: |
| BNB原生报价（`quote=0x0`） | 463 | 294 | 169 |
| USD1（`0x8d0d000ee44948fc98c9b98a4fa4921476f08b0d`） | 74 | 69 | 5 |
| BSC-USDT（`0x55d398326f99059ff775485246999027b3197955`） | 1 | 1 | 0 |
| **合计** | **538** | **364** | **174** |

USD1和BSC-USDT两合约均通过**2025当日历史`decimals()`调用**验证为18位小数。原生BNB组`funds`账面合计 **162.489358576115452492 BNB**，USD1组 **4,346.346267470955042275 USD1**，USDT组 **1.510590016007912637 USDT**；**这些是各代币独立曲线内部统计字段的数学求和，不是钱包/LP可提现资产合计、不是当天成交量/利润，且不能把不同报价资产相加。**正余额中很多极小值：BNB正余额组中位数仅`0.000289542551425689 BNB`，USD1正余额组中位数`0.000000000084528062 USD1`。因此`funds>0`只表示日末净曲线状态，不证明有当时可成交额度或存在正收益。相反`funds=0`也**不能**证明历史上完全没有过买卖（可能发生了完整的买卖往返）。绝不能用364/538当作`18/30`双向执行验收。

**真实迁池/DEX路由证据**：538条TokenManager2快照中`status=3`恰有 **5个**，其余533个`status=0`。按[Four.meme公开Helper3贸易文档](https://github.com/four-meme-community/fourmeme-docs/blob/main/docs/trade-guide.md)，状态3是`COMPLETED`，`liquidityAdded=true`表示交易应从曲线转向外部DEX。对这5个token本轮**逐个**在2025历史末块执行`TokenManagerHelper3.getTokenInfo(token)`，5/5返回`version=2`、经理合约及`funds`与原快照一致，`liquidityAdded=true`。另外对3个`status=0`控制代币核查Helper3，均为false。再通过PancakeSwap V2 Factory历史`getPair(token,WBNB)`取得5个确切Pair地址，以历史`token0()`方向和`getReserves()`真实存储值确认五个V2池**日末WBNB报价储备均为正**，且**全都超过本研究原冻结的2 WBNB储备观察门槛**（门槛不是用户订单金额）：

| Four.meme Index | Pancake V2历史池 | 2025-07-01日末WBNB储备 |
| --- | --- | ---: |
| 247622 | `0x1ac2b4e97114b1b9527868cc53ea77312a93bbf7` | 50.485614251043559073 |
| 247633 | `0xbc8d85dcf331db9bde9263c214c9cb05ab370cd2` | 5.257126062980039271 |
| 247672 | `0x6f866815c5143db6a1718469a285a1608d5527d1` | 27.874518494003645776 |
| 247708 | `0xf1e6edf686e9c2bad83891d0125db8ad0e06e4fa` | 30.035378217701950723 |
| 247733 | `0x67922f7079bd77944e7b70e33ff9c782e7831610` | 5.267590176672389017 |

这五条是完整母体上的**日末真实“发射平台已经完成→V2真实有储备”**证据，但并非已经还原了首次流动性到达的**精确时钟**，不等于当时所有用户均能安全买卖、无转账税、能按任何金额退出，亦非5个可卖出10倍标签。源数据跨日期、完整独立流动性事件证明和标准订单成本仍缺。

**实质时钟风险**：538条中**41条`launchTime`早于本冻结日UTC开始**，其中**40条原始数值小于10亿秒**（典型`1751328`，不可能表示2025年Unix秒的实际创建日期）。`launchTime`为发行设置字段，不得当作`TokenCreate.chain_event_at`、真实创建块或2025公众`available_at`；应以实际链事件为锚，再独立核查当时可查询时钟。这个发现不通过增加主观时间窗口来修补。用户目标不变，下一阶段仍是来源完整性和真实T_entry前向可行性。

**验证边界**：538行及五个Pair只来自现有Alchemy单一规范化免费BSC历史RPC，没有保存此次连接器真实HTTP原字节，没有第二独立来源，也没有跑完整538个创建事件日志；不存在已完成Mac真实47RPC原始档案复算的结论。没有新代码或单测/CI/独立Reviewer；本轮没有下载或重试之前拒绝的付费/403/429源，没买卖、部署、发送邮件或修改其它模块。整体仍 `P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`，保留硬源停止日**2026-11-02**。

## 2026-10-21：Four.meme精准Git SHA离线测试11/11与冻结V2同日30币对比

**这次不是“编写测试”而是已对两份真实Git源码的逐字节一致副本执行了完整的离线回归。** 当前PR #30当时固定 HEAD `a35d463d8b5654ace54b3f202bd763ef977ef8a3`；通过GitHub直接读取`local-agent/mission_agent/early/fourmeme_index_source_probe.py`和`local-agent/tests/test_fourmeme_index_source_probe.py`，在隔离Linux（Python **3.13.5**）原样存入对应包目录。源文件14,477字节、本地`git hash-object`为`7ddf0c2bcb4738cc4bc3c5c2df9e0002ed292546`，测试文件10,687字节、Git blob SHA为`b579074872d13792db4d229d23b94c5f1fbd6b4f`，**两个SHA均和远端GitHub同文件blob SHA精确一致**。在隔离运行环境执行：

```sh
python3 -m unittest discover -s /tmp/monster_checkout/local-agent/tests -p 'test_fourmeme_index_source_probe.py' -v
```

真实输出：**Ran 11 tests / OK；11 PASS、0 FAIL、0 ERROR、0 SKIP**。涉及完整538模拟地址、47次RPC模拟与原始JSON-RPC响应可逆base64归档和SHA256、两个真实事件格式、错误链ID、已存在输出目录、索引空洞、重复地址、创建日志错配、HTTP地址限制、请求预算、Multicall3 15条批容量与ABI编码解码异常。**注意测试内网络来源为Mock；不能说真实Mac原HTTP归档已采集，也不是用户Mac上的Python 3.14实测，亦非另一AI独立Review。**不请求CI，也不新增工作流。

**对历史来源的新增业务核对**：从已经完全读取并留在原P0 JSON中的Four.meme单日索引全部**538个非零、唯一CA**，对比**同一2025-07-01 UTC日冻结30个PancakeSwap V2早期样本**，使用精确`token_ca`去重后的集合交集为 **0/30**。这是两个已冻结样本在**相同日期、不同来源定义**下的具体事实；它能证明现有V2 30个候选不能代表当日Four.meme的发行样本，却**不能**据此得出“Four.meme代币从未迁入V2”、“其它日期亦无交集”或“所有BSC发币全集完全互斥”。据此优先补独立发行入口，而不把这538个独立CA静默合入原30币并重新计算原冻结验收百分比。

下一步骤不是追零Gas、不是重跑已拒绝的Graph或HTTP429源，而是保留最小研究权限：已有免费的归档RPC才允许手工做**47次完整原始HTTP正文归档及manifest复算**，没有能访问的免费源则显式保留`RAW_BYTES_MISSING`；并继续核实Pancake V3与剩余发行渠道真正可取得的来源。没有**2025实时可访问`available_at`**、统一研究名义金额下可买可卖/税/费用与全场所分母之前，不能把**11/11工程测试**晋升为**P0整体来源通过、历史10倍正例、生产可用**。保留**2026-11-02**原停止日，`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`。未付费、未部署、未下单、未发邮件，未修改Frank。

## 2026-10-21：Four.meme单日538个历史代币索引已全部读取、去重并验证3个真实创建事件

**决策：真实数据来源取得局部突破，不是整体Monster模型/全链Source PASS。**本轮不再重复之前四个Router钱包Gas细节，转而针对BSC发射平台Four.meme历史数据。此前在2025-07-01 UTC冻结历史区块 `52440286/52555482` 上用`_tokens(uint256)`重建出**247596–248133共538个新增索引位置**，只核实了起始/末端两个真实TokenCreate事件。此后直接以BNB主网历史 `Multicall3`（`0xca11bde05977b3631167028862be2a173976ca11`，`aggregate3`选择器`0x82ad56cb`）批量调用同一个Four.meme TokenManager2（`0x5c952063c7fc8610ffdb798152d69f0b9550762b`）`_tokens(index)`，**36个只读RPC请求、每批最多15个inner calls，成功取回完整538个index→token_CA地址**。链上历史区块每个返回都是非零、每个CA格式有效，**538个地址互不重复、538个index没有缺口**，首末地址均与已核实真实TokenCreate事件匹配。所有538条地址和逐批响应长度保存于原P0 JSON键`bsc_fourmeme_p0_multicall3_frozen_538_index_slot_enumeration_20261021`。这是**2025-07-01当日结束时Four.meme该合约这一索引区间的538个独立CA**，不是所有BSC发币项目，不包含Pancake V3/其他launchpad的分母，也不是538个通过流动性门槛的买入机会。

除了先前的首个`247596`（2025-07-01T00:00:33Z，block`52440331`）、末个`248133`（23:48:34Z，block`52554568`），进一步对**中间索引`247868`**做历史状态区块二分：`52507858`仍返回零地址，`52507859`首次非零`0x2046b70500bfc3ac3a558b697dee9bba89524444`；同块`TokenCreate`真实日志仅1条、token字段恰好一致，交易hash`0xca38b566d04cd53b9782ac23c31abb746dcbab966638e7d6ce228e80c428840c`、log index`0x163`，UTC时间**2025-07-01T14:04:40Z**。这提供了**首/中/末三处真实历史创建事件锚点**；并不等于逐一解码538笔创建事件、完整无缺的当天所有历史日志、原HTTP字节归档或者第二节点交叉验证。

**工程改造与请求预算：**之前写入PR的独立只读原始归档器`local-agent/mission_agent/early/fourmeme_index_source_probe.py`原来单笔读取538次。根据实际已验证的Multicall3查询，现修改为36批、每批≤15条，并保留6次冻结边界、1次chainId、2条真实首末TokenCreate日志及2个成功回执校验；完整手工单次执行预计**47次RPC，硬上限50次**。一次运行只输出本地JSONL形式逐RPC原始HTTP JSON正文的可逆base64、各响应SHA256、完整538地址清单和manifest，异常/空洞/重复/错误chain/失败事件直接拒绝成功manifest；不存用户RPC密钥到Git，不跟踪日志自动运行，不新增Stage工作流或启动本地监控。同步更新`local-agent/tests/test_fourmeme_index_source_probe.py`，**11项离线模拟用例已编写但未对远端这两份源码实际执行pytest/unittest**。助手在独立Python执行环境仅将新ABI编码/解码核心函数抽取测试，通过了2地址往返、15条最大批长度和两种错误回执拒绝等局部检查，**不是完整源码的11项回归PASS，不是独立AI审核**。

**仍存在的真正阻断**：现在538个地址是Alchemy连接器返回的规范化历史`eth_call`数据，可证明“这个合约某日索引状态可低成本重建”，但本轮**无法在助手运行环境保存连接器的原始HTTP响应正文**；Mac端47请求归档器须在真实RPC接口下执行并留下字节级SHA，且需要真实测试。没有当时公众真实`available_at`的2025来源回执；其它发射平台/Pancake V3连续来源也没有完整覆盖；未验证这些538币各自何时达到真实买卖资格、税/流动性/滑点、用户可选任意金额。因此不能用538当作成功交易的分母或启动模型训练、PIT盈利回测。继续遵守冻结日期**2026-11-02**和`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`，没有任何真实下单、部署、邮件、账号付费、额度购买、Frank修改、CI或工作流运行。

## 2026-10-20：Four.meme 历史索引来源突破与有界原始回执采集器

**本轮优先处理缺失的BSC发射平台覆盖，而非继续研究4个Gas为零的旧钱包，也没有扩大或筛掉冻结BSC V2的30币。**此前Pancake V3的公开Graph API、PublicNode、OnFinality的403/429及Alchemy 10块限制已有真实源测试，**不重试已拒绝来源**。本轮新调查的Four.meme为Pancake V2/V3池建立**之前**即可创建并交易的独立平台路径，故历史新币全集不能只用Pancake PairCreated/PoolCreated事件代替。

### 验证到的真正源能力（原始链上只读，不是实时2025接收记录）

1. 来源：BNB mainnet 56，Four.meme TokenManager2 `0x5c952063c7fc8610ffdb798152d69f0b9550762b`；[Four.meme社区集成ABI](https://github.com/four-meme-community/fourmeme-docs/blob/main/abi/TokenManager2.lite.json)真实枚举`_tokens(uint256)`及`TokenCreate(address,address,uint256,string,string,uint256,uint256,uint256)`。对应ABI Git blob为`7506183d10baadd294e529564f772ab330d647bc`，**社区文档不是独立的完整历史来源**，最终以本次链上历史状态和真实事件为准。公开4M TokenManager2代码在2025-07-01历史区块非空。
2. 沿用早已冻结的2025-07-01 UTC BSC历史边界（首块前`52440286`，当日最后`52555482`），只读`eth_call _tokens(index)`定位索引从前日最后非零`247595`/第一个零`247596`推进到日末最后非零`248133`/下一个零`248134`，**增量538个索引位置**。不是把538当成已经完整审计的独立代币数。
3. 对当天第一个新增索引`247596`做合约历史状态二分：`52440330`仍零，`52440331`首个非零`0x1e395d5edb51e7e7c6b1203912d0d0b6f87f4444`。该一块过滤`TokenCreate`真实事件于2025-07-01 00:00:33 UTC出现，token字段完全相同，原交易`0xf21aca5c7b8369cd02b78b1461dd718da0f6a6ab1f6ece27343dd169ae060b9b`，日志序号`0x4`，receipt status`0x1`。
4. 对当天最后一个索引`248133`二分：`52554567`仍零，`52554568`首个非零`0xc4be692236dba677f3db2d2cdb38f998d2f54444`。同块真实`TokenCreate`于2025-07-01 23:48:34 UTC出现，原交易`0xd12b6bab0c732925496f3ac0250a86355251bf54498dc30ef3f97e1da74ef142`，日志序号`0x41`，receipt status`0x1`。中间索引`247597、247868、248132`在当日末均返回非零独立CA，`248134、248500`返回零。
5. **未证明的范围**：538个索引当时确实都存在且互不重复，目前只抽查起始/中间/末端。没有本轮完整当天`TokenCreate`原日志连续导出，没有跨服务商验证、没有2025当时`available_at`、没有Four.meme真实买卖退路/手续费，没有其它发射平台或Pancake V3完整事件来源。因此不宣称发射平台P0源门禁PASS，更不得启动P1、TGE或10x训练。

### 真实下一步与有界工程落地

针对这个**已经通过两个真实事件锚定**的来源，在现有`local-agent/mission_agent/early/`增加一次性手动可运行的`fourmeme_index_source_probe.py`及对应`tests/test_fourmeme_index_source_probe.py`。它并非新Stage、后台服务或交易策略。功能设计：仅在明确`--live-frozen-2025-07-01`后，从用户自行提供的只读HTTPS历史RPC环境变量中查链ID、冻结六个边界、**恰好538个索引**（遇洞或重复即失败）、当天首末两个TokenCreate真实事件及成功回执；硬预算最多**550个只读RPC请求**，不重试429/403，不跨重定向，不回填亏损/盈利或预测。将每个**原HTTP JSON-RPC响应正文**以base64无损储存在Mac本地JSONL，另有SHA256、逐索引CA、缺陷/范围说明的单份manifest；不向Git提交密钥和原始响应。若其中任一步未通过则留不完整原响应，不生成成功manifest；不擅自切换API或付款。这个脚本的代码和**离线模拟测试**已提交到本PR，**本轮未实际运行Mac完整538地址采集，也未执行已写测试、CI或独立AI审查，不把脚本提交等同通过**。

**源验收与资源止损**：后续仅当能在已有免费额度的归档RPC上执行整次采集并本地核对manifest，才可将**Four.meme这一条发射平台一日索引来源**标为部分`SOURCE_FEASIBLE`；Pancake V3/其它Launchpad与整条2025已公开可读时间仍缺，BSC整体`SOURCE_BLOCKED_FOR_FULL_POPULATION`。独立Review及未执行测试完成前不可部署。硬截止日仍是**2026-11-02**，不许自动续期。P0`INSUFFICIENT_COVERAGE` / P1`BLOCKED` / G4`UNKNOWN` / G6`NO_GO`。

## 2026-10-20：零Gas历史交易核实，官方PBS协议可容纳零Gas交易，但不能推定普通用户免费

**这一步核对并纠正原证据里“0 Gas一律只是可疑的RPC数据异常”的过度结论；并未证明这些机器人交易应被当成普通用户交易成本基线。** 本轮从原30币里已有的#7/#12/#21/#30普通外部账户真实卖出回执抽取`transactionIndex`，在**同一历史区块**分别只读查询前后一笔交易（共8笔）`eth_getTransactionByBlockNumberAndIndex`并核对Gas报价字段：**5/8为0 wei、3/8非0**，并存留原transactionHash、区块、序号和Gas原始整数；选择样本不是代表全区块随机抽样。四笔已核实的卖出交易本身`gasPrice=0`，买卖共8笔`gasPrice/effectiveGasPrice=0`，此前查到的原生BNB余额变化也等于买卖的原始币量；这一组事实在单来源内相互自洽，并非单个receipt遗漏价格字段的直接证明。

**BNB Chain官方协议解释**： [BNB Smart Chain Paymaster Overview](https://docs.bnbchain.org/bnb-smart-chain/developers/paymaster/overview/)明确指出Proposer-Builder Separation(PBS)打包可以允许同一Bundle的Gas价不一、包括单笔0 Gas Price的Sponsored Transaction，由另外高Gas价格的赞助交易使全Bundle具有经济激励。该官方描述解释了为什么**0 Gas真实执行在协议上可能**；但**本轮没有查到这8笔交易隶属何种Bundle、具体谁赞助、是否存在额外协议外费用，也没有第二RPC对这8笔原始交易做独立读回**。相邻交易5零3非零，只是“本来就有不同Gas价格混合”的单节点直接证据，不能推断4个目标Tx一定采用某一具体赞助方案。

**当前研究决策不变**：可用证据层次提升的是**历史普通外部账户买卖与BNB实际到账的回溯性可信度**，而非公众可抢到等价填单能力。绝不把“这4笔有0 Gas”推广成一般Monster账户的回测费用，更不能用它替代要求的**统一金额、全链PIT、无漏退出容量、真实税、执行滑点和持续免费源**。官方网页是协议机制来源，**并非针对本轮Tx的独立区块浏览器核实**，故精确交易证据仍只有Alchemy规范化RPC，原字节SHA和第二节点不存在。

**禁止低价值重复调查**：免费Alchemy`trace_transaction`明确被拒绝，官方BSC公网禁用全历史`eth_getLogs`，且历史V3/Launchpad覆盖仍缺口；不为这4笔交易再开账户、转用收费方案、重新全链扫日志或为“最后一个样例”修改研究门槛。**P0的已知剩余实质阻断**仍是“事发时公共数据的真实可访问时间（`available_at`）”和“完整BSC来源+在用户正式明确研究订单额后同金额买入及卖出容量”。在这两条得到*新*可验证免费来源之前，不能启动P1模型/标签训练；至预冻结止损日**2026-11-02**如无法突破，则按架构合同维持来源覆盖失败并形成阶段拒绝结项，不默认续期。原样本30/30、正式门槛`24/30 PIT`/`18/30统一订单卖出`继续`NOT_SCORABLE`，`P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`。

本轮新事实放回唯一P0证据JSON键`bsc_v2_p0_zero_gas_historical_bsc_bundle_compatibility_and_stop_20261020`。没有修改已有交易金额、其它模块、生产、交易、CI、邮件和Mac服务；只修改现有P0 JSON+MD，未运行新源码单测或独立Reviewer。原服务商规范化输出还不是字节级归档。

## 2026-10-20：4笔普通账户实际卖出到账与Router参数防护核实

**结论：在原30币中已经找到的4组“买入原数量、普通账户再全量卖出”案例，原生BNB按历史区块末余额确实增加了与Pool卖出WBNB相同的金额，但4次卖出都没有设置链上最低回款保护。**这能补强退出通道的实际证据，但**不把这些案例当作统一名义金额、普通用户可获得同等执行或最终已验证净利润**。

本轮继续沿上一个P0的**#7/#12/#21/#30**，使用原Alchemy免费BNB主网只读RPC，查询**买入前块、买入块、卖出前块、卖出块**的账户原生BNB余额和Nonce，以及八笔原交易的`eth_getTransactionByHash` calldata。结果如下（原生余额与成交池内金额均按wei做**整数精确比对**）：

| Rank | 原始买入投入BNB | 卖出池WBNB流出 / 账户卖出块余额增加（BNB） | 买前余额→买后余额 | 卖前余额→卖后余额 | 路由卖出最低回款 |
|---|---:|---:|---|---|---|
| #7 | 0.012 | 0.011940359843178181 | 0.012→0 | 0→0.011940359843178181 | **0** |
| #12 | 0.25 | 0.249547777402681631 | 0.25→0 | 0→0.249547777402681631 | **0** |
| #21 | 0.005 | 0.009725401038080023 | 0.005→0 | 0→0.009725401038080023 | **0** |
| #30 | 0.3 | 0.304689368200754634 | 0.3→0 | 0→0.304689368200754634 | **0** |

在八个买卖所在历史区块，各钱包`eth_getTransactionCount`相较前一块**均恰好加1**；已读八笔对应交易txHash、from、to以及Nonce与之相符。这排除了**同一钱包在同一块额外提交第二笔顶层交易**的情况，但不能排除其他账户/内部调用在同块另行转入BNB；因此较严谨的证据是`BLOCK_END_NATIVE_BALANCE_DELTA_MATCHES_EXACT_POOL_WBNB_OUT`，**不是**已经独立追到那一笔Router内部原生转账的交易级Trace。先前的卖出WBNB`Withdrawal`日志和本轮Router calldata收款参数，也都指向原卖方钱包；它们和历史BNB余额形成三层相互一致的同一来源证据。

**新增执行风险**：四笔卖出方法均为`0x18cbafe5`（PancakeSwap V2 Router `swapExactTokensForETH`），卖出`amountIn`与原买入到账的Token原始整数一一相等，`to`均为外部钱包，**但四笔`amountOutMin=0`**。即没有链上最低BNB回款限制，若市场滑点/夹子变差，区块链不会因所得BNB低于最低预期自动回滚。另外，四组买卖共八笔交易传入`deadline`都是**13位数**、远高于2025年约10位的区块Unix秒，疑似以毫秒时间戳填入以秒计的Router字段，**不具备正常短期过期保护**。这两点属于历史交易的具体安全缺口，**不能复制进正式Monster交易逻辑**。这四个Rank的历史真实回款分别不同，也不能从中挑一个金额预设为研究名义金额。

**Gas和来源仍不通过**：8笔`eth_getTransactionByHash.gasPrice`以及相应回执`effectiveGasPrice`均由Alchemy规范化结果报`0x0`，历史区块余额差额也恰与交换的原生币金额相等；但没有第二家真正独立的原始响应，因此**不把“0”作为可泛化的手续费率、不声称普通用户交易可免Gas**。试查`traceTransaction`被现有Alchemy免费套餐明确拒绝（需升级付费），`getAssetTransfers`的BNB内部转账类别不支持；Blockscout插件明确要求PRO授权，**均不付费、不改源**。通过网页直查BscScan这组TX无法访问，所以没有独立来源核对。本轮P0只认链内历史状态/receipt自洽，不声称由不同服务商复核为真实交易真值。

详细固定四Rank/八Tx、余额、Nonce、原始calldata参数、原始wei回款及限制已追加到**原来的单份P0 JSON**键`bsc_v2_p0_four_router_eoa_native_balance_and_unprotected_sell_calldata_20261020`。原先#7/#12的交易本身报价腿就是亏损、#21/#30为正仅属当时实际成交报价腿，不是研究策略成功率或实际用户净收益。30币母体、用户金额和所有验收门禁不动：P0`INSUFFICIENT_COVERAGE`、P1`BLOCKED`、G4`UNKNOWN`、G6`NO_GO`。没有新源码、测试/CI/独立Review、付费、Mac服务、Frank/Stage99修改、邮件、签名、买卖或部署。

## 2026-10-20：7个真实同地址全额卖出案例的执行路径和可核实Gas分级

**本轮直接强化退出可执行性证据，而不改变原30币母体或研究名义金额。** 原20笔BUY+首索引SELL回执中，有**7个Rank（#3/#7/#12/#13/#21/#23/#30）**已证原买入Token接收地址，与后来卖出Token地址相同，且卖出数量**精确等于**原买入收到数量。通过现有Alchemy免费BNB主网`eth_getTransactionReceipt`核对这14笔BUY/SELL交易的**from、to、status、gasUsed、effectiveGasPrice及Transfer/Sync/Swap/Withdrawal事件**，并用历史`eth_getCode`检查接收地址是否有合约代码，发现可重现的两种执行路径：

1. **#3/#13/#23合约交易，属于同一调用方和同一接收合约**。三组的实际tx.from均为`0x7e6cb60fe24b69824a450bda6f9c679955aa55b4`，tx.to、Token买入接收与Token卖出发送均为已有历史代码的合约`0x7347a30460516c8451687d9b1fc61efec6f8dae6`。WBNB买入时从合约发往池、卖出时从池转回合约；**成交报价资产没有直接转到外部调用人的钱包**。这证明该合约路径能做真实双向Swap，但属于受自定义合约实现/权限影响的历史场景，不能当作普通投资者直接Router现货执行通过，也不能把3个币当成3位相互独立的成功投资者。
2. **#7/#12/#21/#30外部账户直接调用PancakeSwap V2 Router**。四组买卖tx.from都与收到、卖出Token的外部账户地址相同，买卖tx.to均为Router `0x10ed43c718714eb63d5aa57b78b54704e256024e`，这些地址在所查历史交易区块`eth_getCode=0x`。卖出时真实WBNB先从Pool进入Router，再发生Router侧`Withdrawal`；**原交易回执不足以直接确认最终BNB已转入该外部账户，亦不足以还原完整Gas/批准费、历史税或钱包总净损益**。

这些**真实历史规模**的Pool报价腿扣减/增加（sell Pool WBNB out 减 buy Pool WBNB in，单位BNB）分别为：#3 **+0.000247005349558909**，#7 **−0.000059640156821819**，#12 **−0.000452222597318369**，#13 **+0.000283378401750402**，#21 **+0.004725401038080023**，#23 **+0.000276362548656745**，#30 **+0.004689368200754634**。特别是**#7/#12已在不计Gas/批准/额外成本时出现负报价腿差额**，不能把“成功卖出”误报为“获利”。

**Gas限制与仅限部分算术**：Alchemy真实回执对#3/#13/#23两笔交易均返回非零`effectiveGasPrice=100002132 wei`，扣除这**仅两笔**买卖Gas后的报价腿差分别为**+0.000222989237546317、+0.000259368289865730、+0.000252346436644153 BNB**。这些只能叫`POOL_QUOTE_LEG_MINUS_TWO_RECEIPT_GAS`，**不能命名为投资者真实净利润**，因为WBNB仍在自定义合约、调用方出Gas，还可能有合约内部资金分配、批准及其他转移/成本。#7/#12/#21/#30的Alchemy`effectiveGasPrice=0x0`与旧记录零值异常一致，保留`GAS_UNVERIFIED`，**严禁把零字段算作免费Gas**。

七个案例是**原有事后找到的交易**，各个历史买入金额不同，不构成用户研究金额的授权或预注册投资额度。它们不提供原2025年实时`available_at`、无漏完整池历史、一般账户当前税/权限、统一额度下先买后卖或完整钱包净收益；因此**24/30 PIT和18/30正式同一额度可卖两个验收门槛继续`NOT_SCORABLE`**。所有逐Rank txhash、调用方、路径、历史Gas字段与安全等级均追加到原P0 JSON键`bsc_v2_p0_seven_same_recipient_full_token_roundtrip_execution_route_20261020`；没有新单独Stage脚本/Workflow，也没有支付、签名、部署、后台启动、邮件或下单。因本轮仅修改证据数据，未运行源码单测、CI或独立Review。单一Alchemy规范化回执无原HTTP字节档案和第二数据源验证，证据等级严格限定。P0`INSUFFICIENT_COVERAGE` / P1`BLOCKED` / G6`NO_GO`保持。

## 2026-10-20：冻结30币早期真实独立交易时间线，22个历史买入均在建池后5分钟内

这是P0真实业务时钟/早期成交能力的**回顾性证据**，不是新参数、实时监控或收益模型。使用原冻结2025-07-01 BSC Pancake V2前30个不同代币的原Pool创建块和UTC，结合已归档的24个报价储备达标块、20笔真实后续BUY回执以及#16/#17在同笔原始加池/大量Swap交易**之后**的另一笔真实BUY交易，再从既有免费Alchemy只读RPC读取**22个对应真实BUY区块头timestamp**和4个延迟达标流动性区块头timestamp。本轮未读取任何后验5×/10×或当日以外输赢标签。

**冻结原30币一例不删，按缺失原因拆分**：

| 历史来源能证的阶段 | 原30币个数 | 精确范围 |
|---|---:|---|
| 建池时最低报价侧流动性达到原门槛 | 20 | Pool创建块闭状态 |
| 首次观察到达标储备推迟到后续区块 | 4 | #14：建池后1834秒；#16：146秒；#17：83秒；#26：163秒 |
| 已证历史池深达标后，**不同的后续区块中**有一笔成功真实BUY | **22** | #1/2/3/4/6/7/9/10/11/12/13/16/17/19/21/22/23/24/25/27/29/30 |
| 达标池深，但还无充分**独立后续**BUY证据 | 2 | #14/#26：不得认定无法交易 |
| 池深未被证明达标 | 6 | #5/#8/#15/#18/#20/#28，UNKNOWN不得判死币 |

上述24个达标池，按**建池块时间与首个已核实达标块时间**对齐后，均在原研究60分钟窗口内达到报价侧最低池深。22个后续真实BUY均发生于**建池后300秒内**，其中10笔在60秒内；精选交易的最短时间差**1秒**、中位数**68.5秒**、最长**253秒**。22笔的历史买入回执已有status成功与Token/Quote Swap转账对账，原交易前报价侧池深满足冻结的WBNB 2 / USDT 1000档位，22笔买入块**严格晚于**各自首次池深达标块。由于#16/#17原最早Mint+Swap为同一个原子交易，本次仅将它们**后续独立块中的真实成交**计入22，未把同一交易内部的65/64个Swap当成65/64次公开抢先交易机会。

**最关键的PIT边界**：这些是事后选出的、在冻结早期池深门槛以上曾经真实成交的链上BUY，**不证明它们是全网第一次Swap，也不证明当时一般人能在1秒至253秒内从公共RPC接收事件、构建交易、拿到Token并最终退出**。2025年`available_at`原始公开接收记录及完整60分钟事件无漏来源仍未获得。不能把22/30表述为正式可交易合格率，不能将此历史回看时差当成实时提醒提前量。也**没有统一研究买入金额、Transfer税/权限、真实退出成本及同额双向报价证据**，正式18/30可卖门槛仍`NOT_SCORABLE`。没有新增历史死亡币胜负标签或模型分离力评估。

逐Rank30行（含未确定字段明确空值、来源、事件时间、精选真实BUY txhash、入场时差及不可升格状态）已在原P0 JSON键`bsc_v2_p0_frozen30_actual_post_depth_buy_60min_chronology_20261020`。仅使用原有规范化Alchemy及Git证据，**无本轮新HTTP原字节SHA/第二Provider交叉**，未改源码、冻结Schema/阈值、旧模型、研究金额、Mac背景任务、Frank、Stage99、CI/Gmail/部署/交易/付费。下一真正高价值验证仍是**客观的历史公开可读取时间/来源完整性与同一冻结研究金额下的现实买卖容量**，当前无此类原始证据时保持阶段停止，不用更多个例历史BUY冒充可盈利策略。P0`INSUFFICIENT_COVERAGE`、P1`BLOCKED`、G6`NO_GO`。

## 2026-10-20：Factory存储索引跨三个月份历史日期可读，原始V2来源取得增量证据

**本轮是P0来源能力的有限、前台只读验证，冻结30币及交易金额均未变。**复用以前V3来源核查事前选定的三个独立UTC日期**2025-05-01、2025-07-01、2025-09-01**，针对PancakeSwap V2 Factory（`0xca143ce32fe78f1f7019d7d551a6402fc5350c73`）通过Alchemy免费BNB主网历史`eth_call(allPairsLength)`分别比较每个日期**首块之前**与**最后一块**的Factory计数；两个跨月日期的UTC边界以区块头timestamp二分定位。历史V2新Pair数分别为**455 / 785 / 798**，三个不连续日期合计**2038个新Pair索引**。这些只是Factory累计状态差，不等于2038个独立Token/有流动性的池/真实可卖币，也不声称连续覆盖五月至九月的所有日期。

**抽样验证真实链事件，避免把Factory计数差当成虚构数据**：对三天各用`allPairs`精确读取当日**首个与末个**新索引（共6对），再读各Pool的token0/token1及同日末历史储备。对5月与9月的首个索引用历史Factory计数二分找出创建区块，分别是**48,876,497**与**59,582,029**；在各自**单区块**读取原`PairCreated`并证明Pool地址、两边Token、Factory单调一基序号一致。5月首池为`0xf14395e78c2a037570b05eb657672af36ffd380c`，对应tx `0xada1424a9a94ade33995776b311a204735328f227898563bdb9208a9076d7287`；9月首池为`0x14f7c8c33487e16677eaa72ddb253912b9bba1c0`，tx `0x6c4665cc9d50acf290ed9c203d7f8d060a188ecc8e5198ac9b0ab2ee7a51e70d`。7月首池原P0已独立验证过，此次Pool索引与既有rank1一致，无须再审。

**两种真实业务反例**：在创建块和紧接下一块，5月首池WBNB侧`3 WBNB`、另一侧Token储备原始整数为`980000000000000000`（未核对代币decimals，不能换算成0.98 Token），有同创建交易`Sync/Mint`，但该两块**无Swap**；9月首池这两块**0/0储备、0条Pool事件**。因此即使Factory索引可以早期发现真实Pair，**不能据此下结论已经可买，更不能认定可按相同名义金额卖出**。同日末的6池储备仅供历史状态反例，绝不能倒填为建池即刻可用储备。

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

## 2026-10-24：冻结 V2 30例 P0 证据的跨表独立一致性核验（无新链上来源）

- 核验 Git blob `978f437788689eef265b47511fa963490c3e9c96` 的完整 JSON（1,056,161 字符）。实际通过 GitHub blob 接口读取，再按 rank/token_ca/pool 关联 `bsc_v2_p0_current_frozen30_p0_gate_matrix_20261020.rows`、`bsc_v2_p0_all24_next_block_reserve_source_read_20261020.rows`、`bsc_v2_p0_uploaded20_actual_buy_and_indexed_real_sell_replay_20261020.case_results`、`bsc_v2_p0_ranks16_17_post_atomic_distinct_buy_and_partial_sell_pilot_20261020.cases`。执行方式为连接器内一次性只读 JS 校验；未执行本机 Python/CI/独立其他 AI Review，也未新增任何 RPC。
- 实际集合结果：**30/30 唯一 CA + 30/30 唯一 Pool；30个历史 runtime code state、24个下一块末尾历史储备、20+2=22个已记录后续历史买入、18个已记录合格深度附近历史卖出、7个精确相同收到Token数量的同接收地址回售**。本轮 30/24/22/18 四组按rank与CA/Pool的交叉关系无冲突，卖出18例均属于买入22例与储备24例；历史精确回售7例已包含在18例内，不能重复相加。
- **具体缺口与下一来源优先级**：未证实达到预冻结报价侧深度的rank为 `[5,8,15,18,20,28]`；已有合格深度但缺少后续独立买入证明的rank为 `[14,26]`；已有历史买入与储备却缺少满足同类门槛的卖出证明的rank为 `[2,6,10,22]`。这些仅表示当前既存证据缺口，不能当成链上永远没流动性/无人买卖/不可卖或四种独立负例。
- **正式门禁**：30例 `first_actual_public_available_at` 全为 `UNKNOWN`；30例 `complete_PIT_gate_credit=false`；30例 `uniform_research_notional_sellability=NOT_SCORABLE`。即便历史交易存在，**24/30同时代PIT和18/30统一研究量级双向执行仍然均未通过**。2025链上时间与2026回溯取得时间不能代替当时接收时间。未补原始HTTP完整body或第二独立来源，未得到历史成交时点真实Gas/税及公平价格保护的可复制保证。
- 上述是**既有证据的独立关联验证，无新增业务观察结果**。遵守ADR-004：不因这次交叉检查继续编写边界修复或自动扩扫描；仅当存在有界、免费、可真正解决PIT或真实退出证据缺口的新来源时再追查对应rank，否则保留原 `2026-11-02` 来源止损。状态维持 `P0 INSUFFICIENT_COVERAGE / P1 BLOCKED / G4 UNKNOWN / G6 NO_GO`。


## 2026-10-25：冻结 BSC V2 三十例多证据关联与交易发生时间口径复核（离线）

本轮复用同一 Git 固定 P0 JSON blob `978f437788689eef265b47511fa963490c3e9c96`，以冻结 rank/精确 CA/Pool/Quote 为身份关联键，实际逐条交叉检查 30 身份、29 准确创建交易回执、24 份后一完整区块储备、30 行历时、20+2 笔已选取独立后续 BUY，以及原 20 条索引 SELL 加上 rank16/17 SELL。检查实际由只读 GitHub 连接器环境中的独立 JavaScript 对原 JSON 进行，未执行新的 Python 测试、GitHub CI、用户 Mac 命令、RPC、交易或外部其他 AI Review；此检查只证明已存规范化记录之间逻辑一致，不是第二节点来源真实性审查。

**逐例联合审计结果：身份/来源交叉键、BUY 交易哈希、原 30 例 BUY/SELL 状态全部匹配，零差异；原 P0 覆盖事实保持 29 创建回执、24 历史合格储备、22 已选取的后续成功 BUY、18 历史合格深度 SELL、7 笔同接收地址同数量完整卖回。** 未有准确部署 receipt 的 rank5；未有历史合格储备的 ranks 5/8/15/18/20/28；未有已选取后续独立 BUY 的 ranks 5/8/14/15/18/20/26/28。这些缺失只代表**保留档案没有足够证据**，绝不标记这些池无买家、不可买或失败币。归档真实 SELL 是被观察到的别人的部分成交，绝非统一金额可退出的18个实例。

对 22 笔已选取成功 BUY 的链上区块时间，**两个起点必须区分**：

| 时间起点与已观测下一笔 BUY 的延迟 | 60 秒内 | 180 秒内 | 300 秒内 |
| --- | ---: | ---: | ---: |
| PairCreated 的建池区块 → 所选后续 BUY | 10/22 | 未作为本次产品时钟指标 | 未作为本次产品时钟指标 |
| 首次已证满足报价侧流动性冻结下限的区块 → 所选后续 BUY | **11/22** | **20/22** | **22/22** |

两种 60 秒数量差异来自 rank16：该池首次确认满足流动性下限比建池晚 146 秒，所选 BUY 相对建池为 167 秒，相对深度确认只有 21 秒。另一个延期注入流动性的 rank17，相对深度确认后 65 秒有买入；不可以把创建时刻当作实际交易准入时刻。180 秒数据仅为已选取交易相对**区块链事件时间**的分布，不代表首笔 Swap、真实 2025 公众 receipt 时间、策略发送提前量或盈利机会分布。这 22 例亦不可代替30例总体、V3/launchpad、失败币和全市场完整母体。

**业务含义**：在这些已观察交易中，3 分钟级 D0 周期可能明显晚于早期真实买入活动；BSC DEX 新池适配应独立证明更早的事件可见性以及可买/可卖时间，不能以现有 CEX 3m tick 机制代替链上秒级观测。尚无 P0 准入合格或实际提早盈利结论。2025 contemporaneous `available_at` 依旧全部 UNKNOWN；历史回溯只能使用获准的保守时钟重建并标 `PIT_RECONSTRUCTED_ONLY`，不得升级正式 `PIT_VERIFIED`。统一研究金额、转账税、Gas 实际支付、退出最小到账、动态合约限制、V3/Four.meme 完整母体均未闭合；**24/30 PIT 与18/30统一金额可卖门禁继续 NOT_SCORABLE，P0 INSUFFICIENT_COVERAGE、P1 BLOCKED、G4 UNKNOWN、G6 NO_GO**。原 2026-11-02 P0 止损日期不变。

本节是现有事实的业务决策核查，不修改源 JSON、原 Python 核心、模型阈值或已有审核结论，也不暗示新的交易、监控、部署、支出权限。
