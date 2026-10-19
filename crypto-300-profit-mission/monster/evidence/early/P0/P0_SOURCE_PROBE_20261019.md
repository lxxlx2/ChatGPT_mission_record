# Monster P0 — 免费历史源实测：BSC V2工厂存储枚举方案（2026-10-19）

状态：`SOURCE_PATH_PARTIALLY_PROVEN / FIRST30_NOT_READY / NO_MODEL / NO_TRADE`。本文件是本Phase唯一当前报告，不新增Stage文档，不更改2025-07-01 Base30原冻结探针，未使用任何付费RPC、钱包、Mac后台服务或两次P0 CI预算。本轮真实连接器读取的机器可核数字和前12个池地址在同目录[源结果JSON](P0_SOURCE_PROBE_20261019.json)；**原始提供商HTTP正文/响应header没有通过当前连接器归档，因此SHA256字段为null，尚不满足最终PIT和审计门禁**。

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
- 已依次查询zero-based Factory index **1,874,173—1,874,184** 共12个pair地址，12/12成功读到历史`token0/token1`，其中**11/12**恰好一侧为事前指定WBNB或USDT报价币。十二个池的地址、两个token CA、精确序号和非报价池保留在[机器JSON](P0_SOURCE_PROBE_20261019.json)，**没有按当前存活或涨幅选择**。
- 不能凭7月1日末的池身份数据把建池时点或初始流动性、真实第一笔Swap倒填到当日早晨。这12个不是正式`T_entry`、不是最终30CA名单、更不是可交易盈利记录。

**方法判决：BSC_V2_APPEND_ONLY_HISTORICAL_ROSTER_PATH_CONFIRMED。** 这仅打通原链历史候选池的可枚举性。真实35–100个池能否通过报价匹配、过去初次创建时间、真实进入流动性和退出时价仍需另证。V3 PoolCreated需继续经可完整获取的旧日志或独立索引建立母体，不能假设与V2有`allPairs`接口。Alpha/launchpad/Pancake Infinity分母更不自动被V2代表。

## 3. 同一代码中实现可重复只读入口，不造新Stage脚本

已在原`local-agent/scripts/monster_early_venue_factory_rpc_roster_probe.py`中追加`bsc-v3`官方V3 Factory地址及`--mode enumerate`限BSC V2；可在已批准的用户Mac研究目录中运行：按固定UTC日边界计算V2起止序号，单调按序获取`allPairs(index)`和同历史块的`token0/token1`，每个index的原始RPC文本、SHA256和source fingerprint保存本地，断点重新读取时验证原文本SHA和endpoint一致性；只有得到真实前30个符合事前报价条件的**互异CA**才报`CHRONOLOGICAL_FIRST30_V2_POOL_IDENTITIES_ONLY`。不读CEX后续价格、不调用交易方法/钱包、不运行Gmail/launchd，也不把这30项直接晋升为5事件PIT验证。

`--mode probe`仍只做2000/10块能力检查；`--mode scan`仍做连续Factory原事件扫描。新增单测涵盖V3/v2不同事件ABI、V2序号增量与恶意删行、保留原始响应的枚举/续跑/源SHA/零地址拒绝等。**当前只完成了代码提交和小范围链上独立验证；本分支新改动尚未执行完整Python unittest/CI或拿到其他AI独立代码审查结论，不应宣称测试绿。** PR30保持Draft。

## 4. Plan A/B/C实际状态及P0结论

| 路线 | 本轮实际可核事实 | 判定 |
| --- | --- | --- |
| A1：当前Alchemy免费历史`eth_getLogs` | 三个窗口各最多10块可读、成功校验1条正事件，2,000块请求被限 | `SMALL_RANGE_PASS; FULL_DAY_FAIL_THIS_PLAN` |
| A2：Alchemy BSC V2历史Factory状态 | 2025-07-01按工厂计数发现785新池，12个按原序号成功还原Pair+token两侧 | `V2_ROSTER_FEASIBLE_PARTIAL; RAW_AND_FIRST30_NOT_YET_ARCHIVED` |
| A3：用户Mac上其他真正开放历史logs的免费RPC | 当前会话容器DNS不可用；Mac未有本项目真实探针输出 | `NOT_TESTED` |
| B：符合合法导出与成本条件的BSC历史索引 | 已核公开数据列表和权限，未取得全量旧日志授权导出 | `NOT_VERIFIED` |
| C：商业/充值RPC | 合同默认0美元、无需请求用户资金 | `NOT_AUTHORIZED` |

**P0整体：`SOURCE_PARTIALLY_FEASIBLE_NOT_GATE_PASS`**。还未取得30/30历史事件完整证据，也未做24/30部署/首池与18/30首次双向可卖模拟覆盖，故原`COVERAGE_RATE=NOT_SCORABLE`、`G4 UNKNOWN / G6 NO_GO`保持。既不因为小规模正面源证据就直接启动十周建模，也不因为HTTP网络条件把链上源永久判死。

**下一次有意义交付**只接受：在实际Mac前台、免费、可限额/可中断的read-only枚举运行中拿到原始SHA归档和至少30个顺序候选；随后对随机预定样本查原创建交易、首次真实Swap/流动性（包含失效样本），达到24/30与18/30才进入P1。对V3和launchpad缺失需在同一P0结果中明确范围，不能偷换成“全BSC完整母体”。
