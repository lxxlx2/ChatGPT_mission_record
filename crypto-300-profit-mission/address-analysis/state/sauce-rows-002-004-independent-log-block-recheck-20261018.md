# 独立历史校验：Batch 001 sauce #002/#004 的代币日志与区块 BNB 现金流

日期：2026-10-18 Asia/Bangkok
状态：`NEW_INDEPENDENT_CHAIN_FACTS / TOKEN_FLOW_CLOSED / NATIVE_TX_ATTRIBUTION_UNRESOLVED / NO_GO`

## 本轮新增的真实链上证据

原先 Alchemy 对6笔 sauce 路由成交返回的完整 receipt 被截断（每笔8098字符，status=0x1 仅可在截断前缀读取）；但历史 **eth_getLogs 允许用代币合约、Transfer 主题、钱包 from/to 索引与精确区块过滤**。据此对原始来源 #002、#004 分别核查：

- 原始买入两个高度 `0x6f9e4df`、`0x6f9e4e1`：两个钱包各独立收到一笔 `sauce` 转账，tx hash 对上原先保存的两个 router buy。
- 原始卖出高度 `0x7a0db98`：每个钱包分别有**同一卖出 tx 内两条向外的 Transfer**，总转出量与两笔买入合计严格相等。漏掉第二条 Transfer 会严重低估卖出代币数量。
- 用相反方向的精确 topic 过滤核查：买入两高度无钱包 sauce 转出，卖出高度无钱包 sauce 转入；共6组反向查询，均返回空数组。
- 使用 `eth_call(balanceOf)` 在买入前、首次买入后、第二次买入后、出售前和出售后分别对每钱包重新读取5次，结果一致：0 → 首次买入量 → 两次合计 → 出售前不变 → 0。
- 对每钱包分别读取历史 BNB `eth_getBalance` 6 个快照及对应 `eth_getTransactionCount` 6 个快照，买入两区块 nonce +1、卖出区块 nonce +2（批准授权交易也算）。这些快照的 BNB 净差与旧来源的两次买入成本及卖出高度净增加完全一致。
- 通过 `ethGetTransactionByHash` 复读全部6笔路由 tx sender、to、block、method、原生 `value`；实际 tx 均与冻结地址、固定路由及预期交易哈希一致。6笔对应的 receipt 前缀均标示 `status=0x1`，但是完整 receipt **仍未取得**。

[原始日志数量、topics、data、BNB余额、token余额、nonce及边界](../evidence/batch001-sauce-rows002-004-narrow-transfer-native-block-20261018.json) 已结构化入库，研究范围只有这两个钱包和一个代币。

| 来源行 | 买入代币 raw 合计 | 卖出代币 raw 合计 | 三个区块 BNB 净差合计（wei） |
| ---: | ---: | ---: | ---: |
| #002 | 63699915473588833872341 | 63699915473588833872341 | +156828105278687674 |
| #004 | 63523412284240094966004 | 63523412284240094966004 | +154215798043203099 |

这里的 BNB 数字是三个**完整区块前后地址余额之差**的算术汇总，不是隔离每笔交易的内部 BNB 收款证明。按旧证据和新事实，原有收益闭环的数据一致性增强；但仍没有证据排除卖出区块中被动 BNB 入账，因而不能无条件认定这些金额全由所列路由交易产生，也不能升格为**完整钱包 PnL**。

## 可复核程序与测试

新增只读 [保存来源核对程序](../tools/verify_block_roundtrip.py) 和 [12项离线反例测试](../tests/test_verify_block_roundtrip.py)。隔离 Python 标准库环境下 `python -m unittest discover -s tests -p test_verify_block_roundtrip.py -v` 通过12/12，git blob 与已测试版本一致：

- 程序：`7e9c329feea37d54660b4fc68dd681a7b081caf6`
- 测试：`7f2310884344d2fdaf2902b33a7e893949cacfc8`

程序读取冻结449地址来源及本轮链上结构化快照，不自动访问RPC；逐行核对固定钱包身份、同区块转账日志、代币期末库存、BNB区块变化、nonce、交易哈希及第二条卖出 Transfer。身份、方向、金额、来源或反向查询有缺口时返回 `PNL_UNRESOLVED` 而非构造收益。12项测试为本地合成反例；**尚未声称该Python CLI已用原始Git 449清单和本轮JSON执行端到端**。

## 下一个功能性门禁

为了把`区块级 BNB 差额`升级为可靠的**逐笔交易经济结果**，仍需取得完整交易执行轨迹或可证明没有其他 BNB 来源的等价资料，并完成全时段资产流、其它 token、Gas 与链间成本核算。当前 Alchemy 免费权限不允许 `trace_transaction` / `debug_traceTransaction` BSC 追踪。应将**缺乏逐交易原生收入归因**视为 PNL_UNRESOLVED 的具体原因，不要改写为已获审计通过或通过自动跟单资格。

原有总状态：449地址、三链已筛查120，完整钱包30日和长期 PnL 都 **0/449**；旧三笔正收益单币历史来源不增加计数。PR #97 继续 Draft，`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。
