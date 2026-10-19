# Monster P0 — 免费历史源实测：BSC V2工厂存储枚举方案（2026-10-19）

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
