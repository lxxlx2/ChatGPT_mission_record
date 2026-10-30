# P4-B 2026：239E 持仓期间真实外部 1,000 USDT 买单（USDT→WBNB→龙虾）

日期 2026-10-18。Mission Draft PR #40，原冻结 23 钱包 × 19 exact CA = 437 个组合，研究母数不变。该外部签名人 `0x5e600e259e3cff0757e3736223685958665866c6` **不属于这次原主人 239E 回合**，是既有资金池真实外部行为的一次有界、非无偏研究，而非增加一条已盈利模型推荐。

## 1. 从历史信号在仓到完整买入事实

原钱包 239E 在龙虾第二轮真实签名买入区块 **85,959,961**，随后直到其真实卖出 **85,961,371**。本批先冻结四组原始 Pair Swap 观察窗口和 `balanceOf(239E)`；四个区块末实际持币调用均成功，均在指定时点证实原主人仍有非零龙虾。在 Alchemy 免费版，12/13 块 `eth_getLogs` 被「最多 10 块」拒绝；重新明确冻结 10 块窗口后 4/4 都因工具最多返回 8,098 字符而**不完整**。原始失败分别追加记录，没有声称空交易或偷偷换赢家。

最后明确限制只检查原主人两轮各自买入后的**唯一第一个区块**，R1 返回仍截断，R2 真实区块 **85,959,962** 返回完整 JSON：**4 条 Pancake V2 Swap，涉及 2 笔原交易**。第一笔 WBNB→龙虾 Swap 哈希 `0x2b93cfb6ae16ab4943f5f209fff1820f98368fd357cbdcb4f624708440bf8f47`；第二笔含 3 条龙虾→WBNB Swap，但其签名原文因复杂授权数据截断，没有认定卖家的实际签名钱包、利润或是这第一笔买家。

通过另一次明确预冻结的 `ethGetTransactionByHash`，第一笔确认为**外部签名成功的 Router `swapExactTokensForTokens`**，签名人 `0x5e600e…c6c6` 而非 239E。它和 239E 买入是相邻区块，但两个区块的秒级共识 `blockTimestamp` 相同，因此不能证明它是看到 239E 后才行动，更不代表首次公开可交易 U。

## 2. 买入者真正支付的是 USDT，而非池内 WBNB

开始仅能观察到 Pair 的 **1.562236003910333182 WBNB** 入池，不能据此把它视为买家 WBNB 支出。专项核实该签名人买前和买后 WBNB 完全不变，并且同一区块不存在该签名人的 WBNB `Transfer(from=owner)` 事件。对同一笔真实交易完整解码 calldata 后，确定路径为：

`BSC USDT 0x55d398…97955 → WBNB 0xbb4c…095c → 龙虾 0xeccb…4444`

方法 `swapExactTokensForTokens`，`amountIn=1,000 USDT`（18 位），`amountOutMin=43,745.625824946640280067 龙虾`，实际池内 WBNB 1.562236003910333182，实际龙虾到账 48,454.704178311452125501。

进一步有界真实链上核验：

| 项目 | 实际结果 |
|---|---:|
| 钱包买前 USDT | 10,946.711670407384671180 |
| 钱包买后 USDT | 9,946.711670407384671180 |
| **真实钱包 USDT 净支出** | **1,000.000000000000000000** |
| 同笔 ERC20 USDT Transfer(from=本人) | **1,000 USDT**，真实 hash 一致 |
| 买前龙虾持币 | 335,173.813691889308361853 |
| 同笔 ERC20 龙虾 Transfer(to=本人) | **48,454.704178311452125501** |
| 买后龙虾持币 | 383,628.517870200760487354 |
| 买单 status | **0x1 success** |
| 实际 receipt gasUsed | **156,632** |
| 实际 gasPrice | **0.5 gwei** |
| **真实买入 Gas 费** | **0.000078316 BNB** |

完整 receipt 在本次工具读取时可解析（7,310 字符），但 Git **只保存了经过核对的字段和来源信息，没有保存提供商网络层完整原始回执字节**。USDT 和龙虾事件数组则经单块 topic 过滤完整获得并归档。交易 input 路径可从固定签名字段复算，所有 token 数量均按最小单位严格核对，不能把 1.562 WBNB 中间资产二次当作个人本金。

## 3. 该真实买家仍不能纳入盈利胜率

最重要的反例是：买入之前，这个买家**已持有约 335,174 枚龙虾**。新的一笔 1,000 USDT 是原有仓位**加仓**，不是从零开始的首次发现或一笔独立完整 round。直到 239E 最终卖出的历史区块 85,961,371，该买家余额仍为 **383,628.517870200760487354 枚**，没有在当前来源内证明它已卖出、收到资金回款或实现收益。新买单真实本金与 Gas 已确认；**后续出售、交易净利润以及 DDAC/239E 公共跟单因果性仍 UNRESOLVED**。不能拿这次真实买入或别人的后验赚钱数据冒充 P5。

复算来源与结果：

- [连续历史 Pair Swap 审查，包括 R1 截断和 R2 全 4 条日志](./bsc-meme-address-model-v1-p4b-239e-single-block-r1-clipped-r2-four-real-v2-swap-events-2026-10-18.json)
- [外部 signer 与卖方复杂签名源的不同证据等级](./bsc-meme-address-model-v1-p4b-239e-r2-one-real-external-buy-signer-other-sell-truncated-2026-10-18.json)
- [买家龙虾历史四余额和 ERC20 Transfer](./bsc-meme-address-model-v1-p4b-239e-r2-external-wallet-real-incremental-buy-erc20-transfer-readback-2026-10-18.json)
- [没有由钱包直接扣除 WBNB 的链上证据](./bsc-meme-address-model-v1-p4b-239e-r2-external-buyer-wbnb-not-direct-debit-readback-2026-10-18.json)
- [源签名 Router 完整 USDT→WBNB→龙虾 calldata](./bsc-meme-address-model-v1-p4b-239e-r2-real-external-1000usdt-three-token-route-signed-calldata-2026-10-18.json)
- [真实 1,000 USDT 原钱包扣款、成功 receipt 与买入 Gas](./bsc-meme-address-model-v1-p4b-239e-r2-external-5e60-real-usdt-debit-gas-and-dragon-readback-2026-10-18.json)
- [独立 SHA 固定复算程序](./bsc_meme_address_model_v1_p4b_real_external_1000usdt_buy.py) 和 [12 项防假阳性测试](./test_bsc_meme_address_model_v1_p4b_real_external_1000usdt_buy.py)

下一阶段应使用**同一资金来源 + 原主仍持币 + 实际带观测/接收时间 + 同一外部真实买卖 closed PnL**的正负对照，而非继续无上限拆 RPC 窗口。对只实际买入未退出或已有仓位加仓的样本保留在观察表，禁止填入可跟单成功分母。

当前 `P4-B=PARTIAL / PUBLIC_EXECUTABLE_U=UNRESOLVED / P5=BLOCKED / PRODUCTION=NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。无实盘交易、部署、邮件或付费接口。
