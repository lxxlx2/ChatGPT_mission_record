# BSC 地址分析建模 5 — Stage 16：跨钱包交易合约费用事件与双向经济资金闭环

日期：2026-10-12（Asia/Bangkok）。固定研究仓库 `lxxlx2/ChatGPT_mission_record`；研究链 `bnb-mainnet`。**仅限链上研究 / PRODUCTION_TRADING = NO_GO**。没有使用 GMGN 付费 API，也没有执行部署或下单。

## 1. 数据阶段的冻结事实

V21 权威基线：23/23 钱包，19 个固定 CA，437/437 钱包×CA 的正值 ERC20 双向历史查询游标结束。148/148 有转账组合完整原始整数数量对账并与匹配历史区块 `balanceOf` 核实，289 个组合没有正值 ERC20 转账。**以上仅证明代币库存数量，不说明实际买卖、盈亏、资金来源、交易资格与可跟单性。** 不再将重复分页作为地址建模的新进度。

## 2. 新发现：管理合约相同事件可在 3 个钱包 / 3 个代币 / 8 笔原始交易中独立复核

管理合约 `0x1de460f363af910f51726def188f9004276bf4bc`，原生报价 WBNB 合约 `0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c`。

对原始交易逐个检查 `ethGetTransactionByHash` 的本人 EOA `from`、管理合约 `to`；再以固定 BSC 区块、管理合约、固定 `topic0=0x205442d60b70af1203d43cab62352c3b69b94f091be32fe683198057282b5c92`、**原始 EOA 索引 topic** 精确查询事件，按 `transactionHash` 过滤；另对 WBNB Transfer 和 `Withdrawal` 通过原始合约日志核对。

独立证据覆盖 DDAC/MARSCOIN 买二卖二、2ADF/BOB 买一卖一、A83B/BROCCOLI714 买一卖一，总计 **8/8 笔唯一原始交易**：

- 每笔**买入**的管理合约事件第一个 32-byte 整数恰为 `floor(msg.value × 1%)`；经理合约向真实池转出 WBNB `msg.value - 事件金额`，两端能精确相减对平。
- 每笔**卖出**的对应事件金额恰为 `floor(池给管理合约的 WBNB × 1%)`；DDAC 两笔出售另外以 WBNB `Withdrawal` 官方事件证实 gross，其他两笔已有原始 WBNB ERC20 记录。
- 这构成对同一管理合约费用机制的强烈、可重复的链上交叉证据，但**事件 ABI 语义名尚未被独立核对**，所以当前严谨标签是 `MANAGER_FEE_LIKE_EVENT_EXACT_1PCT`，不能升级为“官方规定永远固定 1%”。

**纠错：** 旧的 2ADF/BOB 买入原始研究文件曾把 `managerEventRaw=0x11c37937e080000`（0.08 BNB）保存为未绑定 EOA 的相关 manager event 参考。此次经过 `topic0 + indexed EOA + transactionHash` 过滤，实际该笔交易匹配的费用性质事件为 **0.005 BNB**。旧的 `0.08` 不应继续用作本钱包手续费计算。保留历史文件，新增经来源绑定的更正证明。

## 3. DDAC/MARSCOIN：同一卖出区块两笔原始 EOA 操作的成本拆分

`DDAC = 0xddac928a240bdace3994c2cc0783d4e29a002127`。前两笔本人买入各支付 `0.5 BNB`，对应管理事件各 `0.005 BNB`，各自真正传给交易池的 WBNB 为 **0.495 BNB**。两笔买单的独立钱包原生区块净支出分别为 **0.500059367840 BNB**、**0.500059380680 BNB**；减去 `msg.value` 后所推导的 Gas 分别为 `494732` / `494839` Gas 单位，均符合对应原始 gasPrice/gasLimit。

两笔对应卖出均存在**另一笔成功的本人原始零 BNB 合约操作**，该操作 Gas 均已通过完整回执独立确认为 `0.000005878080 BNB`。扣除这笔额外 Gas，原始钱包区块增加与 WBNB 提现、管理合约事件、主卖出推导 Gas 的关系如下：

| 来源 | 第一次卖出 | 第二次卖出 |
|---|---:|---:|
| 收回的 WBNB 总额 | 0.557192882040803636 | 0.496481881346340937 |
| 管理合约对应事件 | 0.005571928820408036 | 0.004964818813463409 |
| 同区块另外一笔成功交易的 Gas | 0.000005878080000000 | 0.000005878080000000 |
| 主卖单推导 Gas | 0.000059460840000000 | 0.000060756600000000 |
| 钱包该区块 BNB 净增加 | 0.551555614300395600 | 0.491450427852877528 |
| 推导主卖单 GasUsed | 495507 | 506305 |

上表所有金额单位为 **BNB/WBNB，18 位小数原始整数精确计算**。两行各自都严格满足 `WBNB 提现 − 管理事件 − 主单推导 Gas − 额外交易 Gas = 钱包区块 BNB 净增`。这项**算术闭合并不等于取得缺失的原始交易完整回执**：后两笔主卖单的完整回执依然被接口约 8098 字节的截断影响，主卖单 GasUsed 为根据独立区块余额计算的**条件性推导值**；BSC 当前免费源不支持原生内部调用 trace，无法完全排除无其他外部原生交易但仍存在内部资产变化的情况。

## 4. 跨钱包的正负对照：不能以一次卖出推断长期高手

把上述一套严格 **EOA 原始签名 + 原始代币全量配对 + WBNB 真实结算 + 区块余额 + Gas + 同区块其他交易** 方法，用于已经提前冻结的三个初次完整数量匹配回合：

| 代币 | 钱包 | 首次完整配对的区块 BNB 净变化 | 对初始区块支出的收益率 | 原始回执 |
| --- | --- | ---: | ---: | --- |
| MARSCOIN | `0xddac928a…` | 0.051496246460395600 | 10.30% | MAIN_SWAP_RECEIPT_TRUNCATED; GAS_IMPLIED_FROM_INDEPENDENT_FEE_EVENT_CONSERVATION |
| BOB | `0x2adf961b…` | 0.009515610472872943 | 1.90% | ORIGINAL_SWAP_RECEIPTS_SUCCESS_AND_GAS_CONFIRMED |
| BROCCOLI714 | `0xa83b73f5…` | -0.239887492433116024 | -4.80% | ORIGINAL_SWAP_RECEIPTS_SUCCESS_AND_GAS_CONFIRMED |

DDAC/MARSCOIN 第一笔买入至对应第一次卖出的 raw token 数量正好全部匹配，区块净增 `+0.051496246460395600 BNB`，对首次总投入含 Gas 为 **+10.30%**。随后第二次买入、第一次部分卖出虽然两个区块净变化为 `-0.008608952827122472 BNB`，该轮代币仍有剩余，**不能算已实现完整亏损**。2ADF/BOB 首轮约 **+1.90%**，A83B/BROCCOLI714 首轮约 **-4.80%**，保证研究包含确凿的负收益对照。

三个完整数量配对样本仅为经济归因方法的**正负单元案例**，**不是“3 次机会、2 次赢＝66.7% 胜率”**。三钱包在全部重大机会上的资金与可参与资格、未参与机会、普通代币转账、隐藏路由和链上回报仍需单独验证。未给任何地址 `VERIFIED_PROFITABLE_REPEATER` 或 `PRODUCTION_ELIGIBLE`。

## 5. 主线后续的优先工作与验收标准

1. 在真实重大 Meme 机会上，把原始独立 owner-signed swap、普通 token transfer、分发/税费、同区块额外签名操作明确分类，按本轮验证的“**钱包索引事件 + 原始交易哈希 + WBNB 真实合约资产流**”逐笔归因；不得无条件复用 1% 规则到不同历史路由或合约。
2. 对 8E6B、877AF、DDAC、A83B、ADFF、2ADF 和 5C0C 固定**跨项目正负机会清单**，保留未参与、晚买、持仓未平的真实分母。报价本位 BNB/WBNB/USDT 不能未按时点汇率转换就叠加到同一净利润。
3. 在收支与真实重复盈利模型充分审查后再设计 5/15/30 分钟延迟跟随、真实滑点、池流动性以及小资金能否成交的独立历史回放。后续代码须经过其他 AI Review、测试、隔离验收；**生产始终 NO_GO**，没有部署。

## 6. 已远端保存并绑定 SHA 的原始证据

- `BSC_MEME_23_EOA_19_CA_EVIDENCE_COMPLETENESS_OVERLAY_V21_2026-10-12.json`（Git blob `3761b9140d0c64b1ffd8d8d243d63a2a1a4fc690`）
- `BSC_MEME_STAGE16_DDAC_MARS_TWO_BUYS_WBNB_MANAGER_FEE_GAS_QA_2026-10-12.json`（Git blob `a626ae870cb99dea3af751495a005a4a547ed43a`）
- `BSC_MEME_STAGE16_DDAC_MARS_SELL1_WBNB_FEE_GAS_RECONCILIATION_2026-10-12.json`（Git blob `59cd93c8182aa40ee8b58b3cd1a4edce6d270124`）
- `BSC_MEME_STAGE16_DDAC_MARS_SELL2_WBNB_FEE_GAS_RECONCILIATION_2026-10-12.json`（Git blob `d0ef9ad02fe1a268522af9c02976a97674c3bbcd`）
- `BSC_MEME_STAGE16_MANAGER_ONE_PERCENT_FEE_EVENT_CROSS_WALLET_QA_2026-10-12.json`（Git blob `91037563adfe7ec84b308b92d60685512400de21`）
- `BSC_MEME_STAGE16_3_EOA_ROUTER_FEE_AND_SIGNED_ROUNDTRIP_QA_2026-10-12.json`（Git blob `a537350f66060efa38440d2c1c462641b7015c97`）
- `BSC_MEME_STAGE15_DDAC_MARSCOIN_FIRST_FULL_AND_SECOND_PARTIAL_NATIVE_ECONOMIC_QA_2026-10-12.json`（Git blob `1eec74ae2fc7091dfb1fab0e4ab76741c0282f46`）

所有原始数据来源于当前 BNB Chain 只读 RPC 或仓库既有原始交易证据。无付费 GMGN、无用户本地执行命令、无自动监控/交易部署。
