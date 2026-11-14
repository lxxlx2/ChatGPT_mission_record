# BSC P4-B 龙虾审查修复：追加链上原始证据与范围更正

日期：2026-10-16（曼谷）。对原目标固定 SHA `e2895bc8fc0a5c73754201504439d738ab1aa992` 收到独立其他 AI 的 **`REQUEST_CHANGES`（审核部分完成）**。其本地 Python 391 项测试通过，但未能独立访问 BNB RPC。本开发回合经已连接 Alchemy BNB Mainnet **重新读取**必要区块和日志，不把其审核结果自动升级为 APPROVE。此文档记录对错误的追加更正；旧链上 JSON 字节**不覆盖、不回溯修改**。

## H1：真实卖家属于原样本（必须更正「独立」）

独立原地址签名（`TokenSale.account` 等于原交易 `from`）只能证明是**不同 EOA**，不能证明市场参与者对原模型样本独立、资金独立或操作者独立。冻结来源 `BSC_MEME_23_EOA_19_CA_EVIDENCE_COMPLETENESS_OVERLAY_V21_2026-10-12.json`，Git blob `3761b9140d0c64b1ffd8d8d243d63a2a1a4fc690`：

| 83636000 真实卖家 EOA | 是否冻结 23 钱包 | 对应钱包索引 | 龙虾 CA 原代币入／出事件数 |
|---|---|---:|---:|
| `0x5c48a7c2113aa044d9c1381588b9c7b3c352387c` | **是** | 20 | 3 / 6 |
| `0x9d1240b262d91ec3a4ea24bfec5e3b21c2eca35c` | **是** | 22 | 1 / 28 |
| `0xbb99a969db5df28f032e2023058ce64c14a46a9b` | 否 | — | — |

原冻结 overlay 的这两个完整 CA 格原本 `trade_signer=UNVERIFIED_FROM_ERC20_ONLY`：**只能将本轮单独重取的两笔卖出签名升级为已验证**，不能将原计数中的 6/28 笔转出均解释为本人卖出，更不能把历史全钱包盈亏闭合。由于 overlay 只保存计数、未保存逐笔哈希，不能确认这两笔是否已经包含在计数中。当前这三个 EOA 都是**已经暴露的案例**；不可作为 P5 untouched holdout。

## H2：毫秒时间原始头部（此次 Alchemy 重取并归档）

| BSC block | 实际 `milliTimestamp`（十六进制 RPC 字段） | 对应 UTC |
|---|---|---|
| 83635777 | `0x19c9e489428` | 2026-02-27T08:48:02.600Z |
| 83636000 | `0x19c9e4a1c26` | 2026-02-27T08:49:42.950Z |
| 83636127 | `0x19c9e4afb64` | 2026-02-27T08:50:40.100Z |
| 83636128 | `0x19c9e4afd26` | 2026-02-27T08:50:40.550Z |

原 DDAC 83635776 已归档 `milliTimestamp=0x19c9e489266`。8356* 这里**不是**推测秒小数；归档分别有真实 `eth_getBlockByNumber` 的区块号、区块 hash、原始 `timestamp` 与 `milliTimestamp` 字段。原调用结果因响应大小截断，标记 `source_response_truncated=true`，但上述字段位于可读段。两块时间差 `100800 ms` 是**区块头时间差**，并不等于第三方真实收到链上消息或订单提交延迟。

## H3：完整单个区块（不是整个窗口）事件

对固定 TokenManager2 `0x5c952063c7fc8610ffdb798152d69f0b9550762b` 在 **83636000 单区块**以 `TokenSale` topic 精确读取全部 **4** 条事件：龙虾 exact CA `0xeccbb861c0dda7efd964010085488b69317e4444` 是 **3** 条，另 **1** 条为**其他 CA**。对龙虾 exact CA 同一单区块以 ERC-20 `Transfer` topic 读取全部 **5** 条：3 条 `seller→TokenManager2`、2 条 `TokenManager2→other EOA`（买入方向转账）。三笔原签名人、`TokenSale.account`、原 transaction hash 和匹配数量，均与冻结的较早样本保存的一致。新增 append-only JSON 归档**全部 4+5 条原始 log**及查询范围/结果和对应三笔回执状态 `0x1`。那额外一条其他 CA 的 `TokenSale` 不是龙虾。两个 manager→买家 Transfer 不在没有匹配 TokenPurchase 证据时被计成已经证明买入 PnL。只主张**该一个抽样区块**的 3 个龙虾卖出，不主张 **83635777–83636127 整个窗口的事件总量**。

## M1：DDAC 买入支付残差严格保持未知

龙虾原始 DDAC 买入 `0x35793699fbf006cfb07d5775991f50c106af64ea840db10a2f580b4661a0df12`：
- 交易 `value`：`800000000000000000 wei`
- 归档曲线购买 cost：`784158415841584155 wei`
- 归档 `TokenPurchase` 协议 base fee：`7841584158415841 wei`
- 差额 **`8000000000000004 wei`**（约 0.008 BNB）：**`UNRESOLVED`**，不能直接记路由费、额外 AntiSniper 税、退款或收益。

Four.meme 当前官方 [交易接入说明](https://github.com/four-meme-community/fourmeme-docs/blob/main/docs/trade-guide.md) 规定 V2 `TokenPurchase.fee` 为 baseFee，某些模式还存在未计入事件该字段的 `extraFee`，但这不证明本样本的残差受益人。原 83635770 已观测到更早的龙虾 Token Transfer，DDAC 不能被称为全球首位买家，该 Transfer 也不能单凭日志认定为同签买入。

## M2 / M3 / M4 / L1–L4：真实证据门禁和 Git CI

修复 `bsc_meme_address_model_v1_p4b_lonxia_observer_gate.py` 新增加固定 `PINS` 的第三份追加纠错 JSON，并强制验证：头部毫秒与 UNIX 秒一致、真实 N+1→卖出块间隔、3 个卖家钱包归属、三笔原交易签名及精确 Token Transfer、该单区块 4 个 manager TokenSale/5 个龙虾 Transfer、每笔 receipt `status=0x1`/blockHash、DDAC 买入 residual 不归属，以及 83636127 的真实 `Disabled` revert payload。买入模拟 `eth_call` 返回 `0x` **没有返回代币数量**；原预计代币数量来自不同方法 `Helper3.tryBuy`，且 `minAmount=0` 不是安全保护。**U/真实 PnL 仍为 `UNRESOLVED`**。新增十一项对抗回归覆盖上述误判，原 BSC 工作流严格钉死 `github.event.pull_request.head.sha` checkout 并自检 `git rev-parse HEAD`。三套老 P4-C CI 的成功只算旧范围，**不替代本轮证据复核**。

## M5：三个来源等级不得混作同一口径

| 来源阶段 / 证据等级 | selected 原钱包回合 | 唯一 wallet×exact CA 格 | 同一等级未审核格 | 使用限制 |
|---|---:|---:|---:|---|
| 老 `crosswallet` 样本选定口径 | 3（2 正/1 负） | 3 | 434 | 历史最低冻结批次，不是全钱包利润完成度 |
| `five_baseline` source-native | 5（3 正/2 负） | 4 | 433 | 新的原生交易五回合版本 |
| `seven_expanded_review_pending` source-native | 7（4 正/3 负） | 5 | 432 | 扩展来源，**已经包含** 8E6B/token4 负正两回合 |

每个数字都限定于**自己的样本批次与证据标准**。三个来源没有被删除或改写；不能相加，不能把 432 未到此审核等级的格子说成 432 个确认没有交易的机会，也不能因为七回合 JSON 字段写“source_verified”就断言独立 AI 已批准其经济表现。最终 P4-C、P4-B 和 P5 仍未通过。

## 纠错来源与下一步

[原始来源不变，追加更正证据](./bsc-meme-address-model-v1-p4b-lonxia-independent-review-errata-2026-10-16.json) 固定原始 JSON 的 Git blob、冻结 V21 overlay、历史 DDAC 买入 source，存储所有新读取结果。除该文件外，旧交易归档保持字节不变。原研究报告有过时的“独立卖家”用语，以本纠错说明及对应字段为准。

审查门禁仍需**新固定 SHA 的其他 AI 再审**。仅证实经过抽样的历史技术性 buy 和不同地址的后续卖出，不证实同一第三方既能买又能以可计算税费净值卖出；不证实真实传播时间、完整期间机会排序或 1/5/15 分钟收益。 `P4_B=PARTIAL`、`U=UNRESOLVED`、`P4_C=PARTIAL`、`P5=BLOCKED`、`NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。
