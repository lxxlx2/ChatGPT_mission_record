# 地址分析 / 收据与交易类型只读验证 V1（2026-10-18）

状态：`REAL_4_RECEIPT_FACTS_READ / OFFLINE_17_TESTS_PASS / SWAP_PNL_UNRESOLVED`

## 本次直接完成

- `tools/receipt_probe.py`：只读 EVM JSON-RPC `eth_getTransactionByHash`、`eth_getTransactionReceipt`；允许用两份本地 JSON 离线复验，或者通过指定环境变量取得 HTTPS RPC URL。凭证不进入仓库，程序不签名、不提交交易、不调用交易工具。
- 强制冻结449源文件 SHA、原始行号/钱包地址匹配；校验 chainId、交易哈希、区块哈希及高度、调用发起地址、回执执行成功、ERC-20 `Transfer` 日志、`Approval` 和实际 `gasUsed × effectiveGasPrice`。输出仅为 `RECEIPT_FACTS_ONLY`，不自动填入 FIFO 的 `receipt_success` 或 `quote_flow_verified` 证明标志。
- 解析 ERC-20 到钱包的流入、从钱包的流出及同地址自转账；能够识别授权不算交易、普通代币/原生币转账不证明 DEX 成交。原生币内部回款标为 `UNRESOLVED_INTERNAL_TRACE`，因为标准以太坊交易收据没有内部原生币转账明细。
- 17 项真实运行的离线单元测试通过，覆盖失败回执、错误链/哈希/发起地址/区块、截断及畸形日志、Gas 价格优先级、同钱包转账与 ERC-20 金额和原始钱包身份约束。隔离 Python 标准库环境执行 `python3 -m unittest discover -s tests -v`（该运行只针对本工具的单元测试目录）；实际软件代码与测试文件的 Git blob SHA 在创建时已经与已测本地文件逐字节比对。

## 四个真实主网收据：实际经 Alchemy 获取完整记录

[完整可解析的交易与回执字段](../fixtures/complete-rpc-receipts-four-transactions.json)；[独立复核交易身份与资产净流出/Gas 的证据](../evidence/receipt-probe-four-real-rpc-check-20261018.json)。

| 源行 | 链 | 链上交易事实 | Gas（原生币 wei） |
|---:|---|---|---:|
| 002 | BSC | sauce `approve`，没有确认的 DEX 买卖 | `5878080000000` |
| 044 | BSC | WBNB `transfer` 净转出 `12684915159767001` raw | `4680600000000` |
| 045 | Base | USDC `transfer` 净转出 `500000000` raw | `382277850000` |
| 050 | Ethereum | 原生 ETH 直接转账，没有 ERC-20 Transfer | `1972263426000` |

四笔交易的源行钱包与冻结名单相同，查询回执 `status=0x1`，链身份、哈希/区块及 ERC20 Transfer topics 核查一致。**真实历史到账、转出与 Gas 是事实，不等于交易盈亏**。这些地址的其它交易及成本未审。

## 必须保持的限制

1. 曾尝试独立查询 `sauce` 原买入交易2笔、卖出交易1笔的完整 receipt；当前 Alchemy 连接层对三笔回执均截断到 **8098 字符**，JSON 无法完整解析。因此本轮没有重新验证这三笔历史成交，也**不能**将以前的 3 组单币正收益升级为实时独立 RPC 全流程批准。
2. `receipt_probe.py` 使用完整回执时才能计算日志事实；若 RPC 超时、失败、格式错误或用户数据不完整，返回/退出 `PNL_UNRESOLVED`，不将缺失结果当零。
3. 没有执行 Python 程序通过真实远端 URL 的在线端到端测试，也没有用户 Mac 实测；四份主网历史收据通过已连接 Alchemy 工具读取并使用独立 JavaScript 交叉验证，不能冒充 Python CLI 的网络验收。
4. 没有证明钱包全量的 Token/原生币内部现金流、所有交易历史、费用税率、桥接、前期库存成本或真实亏损；依然不计算完整钱包盈利排名。
5. 若未来需把本工具的资产收付转换为 FIFO BUY/SELL 事件，必须额外证明交易目的、确切 quote/net 转移、代币税、窗口前后持仓和历史成本，再送独立审核。现阶段两程序没有无证据自动拼接入口。

## 下一研发里程碑

**优先**在能完整保留 RPC 返回的来源中取得低频地址真实路由交易全部 receipt、交易时点区块和历史 token 余额；实现有上限的成功交易聚合与跨 quote Gas 计算，查出可独立复算的**真实亏损**案例。随后将上游确切事实转换成 FIFO 输入并验证审计反例。Batch007 签名扫描保持独立队列，不占用这项关键验收。

`RESEARCH_ONLY / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。
