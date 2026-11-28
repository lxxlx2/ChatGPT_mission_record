# 正负Token交易成交报价核验：WBNB事件哈希匹配（2026-10-19）

执行 [盈利主线纠偏计划](../state/pnl-mainline-recovery-plan-20261019.md) P1。不再以单一钱包区块余额差冒充成交；本轮通过**真实WBNB合约** `0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c` 上的 `Deposit / Withdrawal` 事件，按准确买/卖交易hash进行匹配，提供新的**Token成交路径中WBNB报价**证据。此处在同一事件中分开买卖/Wrap+Unwrap，不能把一次wrap+unwrap算两笔交易。

**重要结果：#227 BOARDSEAT 正向，#227 BTCLIFE 负向，#400 BOARDSEAT 负向**，现在两套相互独立的链上数据（真实WBNB合约报价事件、钱包原生BNB执行区块变化）在三笔中方向全部一致。

| 原始钱包 | Token | 买入时WBNB事件 (BNB) | 卖出时WBNB事件 (BNB) | WBNB报价差(未扣费用，不是最终钱包收益) | 钱包买卖执行区块BNB余额净差 | 钱包净差 − WBNB报价差 |
|---:|---|---:|---:|---:|---:|---:|
| #227 | BOARDSEAT | 0.330000000000000000 | 0.483663976630184592 | **0.153663976630184592** | **0.139871398530549414** | -0.013792578099635178 |
| #227 | BTCLIFE | 0.330000000000000000 | 0.149944555963376124 | **-0.180055444036623876** | **-0.190058157929590970** | -0.010002713892967094 |
| #400 | BOARDSEAT | 0.990000000000000000 | 0.668967157750727214 | **-0.321032842249272786** | **-0.337858120186780058** | -0.016825277937507272 |

**这三个差额用途不同：** WBNB报价差是买卖交易哈希上观察的Wrap/Unwrap数量差，直接证明路由兑换阶段的**粗略价差方向**；它不表示该数全部转入或转出用户钱包。BNB钱包区块差涵盖买卖调用及相应Gas，也可能含区块内其它Native收付。两者差异可能由Router税/中介费、Gas与其它区块活动造成，不能倒过来将差值全记作手续费。

- **#227 BOARDSEAT**：买 `0x83166b427a3b57463e1a3de9f8162ae8b1e9a68b9211ce339f72ab982e0e4e02` WBNB Deposit `330000000000000000` Wei，卖 `0x9349a04cf35c7846c77dfd1c28e0e64f761747b5686adec5d47318fbf30d96cc` WBNB Withdrawal `483663976630184592` Wei，均属于Router执行交易哈希。
- **#227 BTCLIFE**：买 `0x9db45eb50fd726266111d3f6903dfe85d63799f973d746faf37289c697e65766` 同笔WBNB Deposit+Withdrawal皆 `330000000000000000` Wei，卖 `0xf8ad3230681af452306ee6219e92c724bd935d347b4d9740f68cafb8e1bdb394` 同笔WBNB Deposit+Withdrawal皆 `149944555963376124` Wei，**同一交易的封装/解除封装不能重复计数**。
- **#400 BOARDSEAT**：买 `0x099de44e8175bdb1bd25ec08c223c5d10cccc4d53752b95d2a2e62e0beadf5db` 真实WBNB Deposit `990000000000000000` Wei（另有0 Wei日志忽略），卖 `0x4a6c126269c92cef7a2fd2397e70bbe72011d1a399229a3baa877b471f7d4d2e` Withdrawal `668967157750727214` Wei。两笔Boardseat同exact CA但是不同独立钱包、不同交易hash。WBNB Router事件报价的获利方向正负相反，不能拿Token名称代替策略或交易时间。

历史其它门禁：这三个回合已经在之前证据中做过本人签名、完整Token CA原始数量入/出闭合和买前卖后零库存核验。最新材料补充对应交易的**WBNB原生合约报价路径**。BNB免费节点内部trace目前不可用；因为Router可能在转给EOA前再次抽税或交给别的合约，**当前证据等级提升为`HASH_MATCHED_WBNB_QUOTE_EVENT_AND_CLOSED_TOKEN`，仍不是`AUDITED_REALIZED_NET_PNL`**。

**结论计数：**新增3笔完整Token回合（1报价正向、2报价负向）hash匹配WBNB事件，3笔均与钱包BNB余额方向一致；**新增已核定最终逐笔净利润0笔**，完整30日钱包PNL0/449，长期0/449。下一步优先寻找直接以ERC20 WBNB、USDC等报价交付钱包的案例，届时能以`Transfer`原始日志精确结算而不依赖内部Native资金追踪。不得无限循环同一router问题。

底层数字和逐笔hash见 [机器证据](../evidence/pnl-mainline-wbnb-event-quotes-20261019.json)。只读研究，不合并、不部署、不交易。
