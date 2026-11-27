**审核后追加更正（覆盖本文相冲突的旧叙述）**：固定 SHA `e2895bc8fc0a5c73754201504439d738ab1aa992` 的独立部分审核为 `REQUEST_CHANGES`。本页原先的“三名独立卖家”只能理解为“三个不同签名地址”；其中 **5C48/9D12 都属于冻结 23 钱包**，仅 BB99 不属于。已补录 N+1 与卖出块原始 `milliTimestamp`（历史头部时间差 100.8 秒）、83636000 **全部 4 条 manager TokenSale（龙虾 3、其他 CA 1）与龙虾 5 条 Transfer（卖出方向 3、买入方向 2）**。DDAC 原 `0.8 BNB` 价值与来源 cost+baseFee 之间 **`8000000000000004 wei`** 未归属。既有“真实卖出”数字只针对**抽样单块**，不代表整段迁移前市场的完整卖出数量；此前 P5 也绝无样本外独立跟单盈利结论。**请优先阅读 [独立审查修复报告](./bsc-meme-address-model-v1-p4b-lonxia-review-correction-2026-10-16.md) 与 [追加只读链上证据](./bsc-meme-address-model-v1-p4b-lonxia-independent-review-errata-2026-10-16.json)**；此前有冲突的语句以新增来源核实内容为准。旧 JSON 原文不可回溯篡改。

# BSC Meme P4-B / 龙虾：从 DDAC 买入后观察者开始的历史买、卖链上证据

日期：2026-10-16 Asia/Bangkok。Mission [Draft PR #40](https://github.com/lxxlx2/ChatGPT_mission_record/pull/40)，**仅只读研究**。本批依据前一轮固定已批准代码 SHA `47945ca77806d23d942fa2abb681c70244e273a7` 所冻结的 DDAC／龙虾 2026 CA 调查。**本批新增的归档、脚本和工作流不继承此前的独立 APPROVE，新 SHA 仍待独立审查。**

## 2026 年真实公开状态：先证原钱包，后证观察者

龙虾 exact CA `0xeccbb861c0dda7efd964010085488b69317e4444`，Four.meme V2 TokenManager2 `0x5c952063c7fc8610ffdb798152d69f0b9550762b`。已归档原签名人 DDAC 买入 `0x35793699fbf006cfb07d5775991f50c106af64ea840db10a2f580b4661a0df12`，区块 **83635776**；历史区块毫秒时间 **2026-02-27T08:48:02.150Z**。

第三方**不能用 DDAC 交易本身的签名之前价格或 N 区块内其他顺序**假设跟单；本研究只测试**之后 N+1 区块 83635777**，毫秒时间 **2026-02-27T08:48:02.600Z**，说明这里仅相隔约 0.45 秒；不证明公共节点实际向第三方传播 DDAC 交易时间、排队成功、人工下单反应时间或下一笔成交确定性。历史 `eth_call(block=N+1)` 是 **N+1 区块结束时的状态**，并不保证此前 N+1 的第一笔交易前就有完全相同的状态。

## 实际执行的只读合约查询

官方 Four.meme 接入文档 [trade-guide.md](https://github.com/four-meme-community/fourmeme-docs/blob/main/docs/trade-guide.md) 区分 V2 曲线上的 Helper3 查询、`buyTokenAMAP` 买入和 `sellToken` 卖出，后续 `liquidityAdded=true` 转外部 DEX；参考 ABI Git blob：
- `four-meme-community/fourmeme-docs/abi/TokenManagerHelper3.lite.json`: `3b7141fc7265bbd845fcac60b5939e4036599073`
- `four-meme-community/fourmeme-docs/abi/TokenManager2.lite.json`: `7506183d10baadd294e529564f772ab330d647bc`

说明：**这些是本次查询所用的当前官方接口说明；不能仅凭当前文档断言同样的前端、报价 API 或区块订阅体验已在 2026-02-27 对第三方可靠可用。**

在 BNB 主网按历史区块只读 `eth_call`，Helper3 `getTokenInfo(address)` 返回：
| 区块 | 发生意义 | V2 / BNB quote | 剩余 offers（raw） | `liquidityAdded` |
|---|---|---|---:|---|
| 83635775 | DDAC 买之前的一个历史块 | v2 / zero address | 691455696192340590000000000 | false |
| 83635776 | DDAC 买入所在块已结束 | v2 / zero address | 592386442682040597000000000 | false |
| 83635777 | **外部测试区块** | v2 / zero address | 592386442682040597000000000 | false |
| 83636127 | 临近迁移；曲线剩余 0 | v2 / zero address | 0 | false |
| 83636128 | DEX 流动性加入后 | v2 / zero address | 0 | true |

以上 getTokenInfo 的交易协议费为 **100 bps**，但 `feeRate` 不构成包含反夹子、第三方费或动态税的全口径结算证明；真正费用和实际成交仍需要额外链上闭合。

### 外部历史钱包 2ADF 的买入模拟：两种金额成功

选择另一个原冻结钱包 `0x2adf961b40951736bcff3b36b7fb1cd5775475ba` 作为**纯模拟 caller**；在区块 83635777 它有 **2.509326913060654135 BNB**，但**没有**该龙虾代币持仓或对 TokenManager2 的授权。没有用该钱包密钥，没有签名发送交易，也**没有**声称 2ADF 实际跟单。

使用 Helper3 `tryBuy(address,uint256,uint256)`（代币固定，amount=0）、然后 TokenManager2 `buyTokenAMAP(address,uint256,uint256)`（`minAmount=0`，仅用于技术通路测试）的只读历史 `eth_call`：

| 历史模拟投入 | 预计得到龙虾（raw） | 曲线 gross cost（wei） | 协议 fee（wei） | 合约买入 `eth_call` |
|---|---:|---:|---:|---|
| 0.01 BNB | 1121061043083007000000000 | 9900990099009895 | 99009900990098 | 成功，返回 `0x` |
| 0.10 BNB | 11081555505899497000000000 | 99009900990099002 | 990099009900990 | 成功，返回 `0x` |

这些是**不落盘状态变化的模拟调用**；既没有真的转账，也没有产生代币持仓、Gas 已支付数据或可执行的非零滑点保护。特别是 `minAmount=0` 在真实交易里风险很高，此处的成功不应被升级为安全可跟单价格。

### 同区块卖出权限尚不成立，不能把买卖报价相减成利润

在 83635777，DDAC 的原代币余额实际为 `99069253510299993000000000` raw，但对 TokenManager2 `allowance=0`。直接从 DDAC 地址模拟 `sellToken(address,uint256)` 卖出 `1000000000000000000000` raw 时回报 **`ERC20: insufficient allowance`**。因此，卖出需要先授权或采用已经授权的真实其他路径；不证明持币者不能之后授权。

同状态 Helper3 `trySell` 可返回数学估值，例如上面 0.01 BNB 对应的买入预计数量，其 **同一未改变的区块状态** 卖出估值为 `9776645627086865` wei（协议 fee `98753996233200` wei）。**买入和卖出是对同一固定状态的独立调用，不是买后状态的可执行连续交易，不能据此计算真实往返盈利或亏损。**

### 后续真实卖出：来自另外三个链上签名卖家

在区块 **83636000**、UTC **2026-02-27T08:49:42.950Z**，约 DDAC 早期买入后 **100.8 秒**，按 TokenManager2 原始 `TokenSale(address,address,uint256,uint256,uint256,uint256,uint256,uint256)` 事件 topic 精确取到三条**属于龙虾 exact CA** 的成功链上销售事件：

| 原始发送者／卖家 | 原始交易 hash | TokenSale.amount（raw） | TokenSale.cost（BNB gross） |
|---|---|---:|---:|
| `0x5c48a7c2…2387c` | `0x21870257be05a174adfbebf956553dd460c28ed94185b8b5a12b1d17744a0ef5` | 13450048203357820000000000 | 0.487980946775106978 |
| `0x9d1240b2…eca35c` | `0x6e53994782172907d3442e751d1755415a90156a0833dd584a3a00dfeea793cd` | 1237501058717500000000000 | 0.043382453442936750 |
| `0xbb99a969…e9b` | `0x656ed12c323353c91955f0902cfb249f561bd16afff12144826b95a634499998` | 6157730204399673000000000 | 0.212251332962042988 |

三笔均复核原始交易 `from` 等于 `TokenSale.account`，且该笔原代币 `Transfer(from=seller, to=TokenManager2)` 的 raw 数量与 `TokenSale.amount` 精确匹配。这证明当时迁移 Pancake 前，**市场中确有其他地址执行真实卖出**。事件成本是 **gross 曲线报价**；扣除协议、路由、税和 Gas 后钱包收款未完整重建；也没有证明三位卖家是在 DDAC 可观察信号之后买入，或 DDAC/2ADF 的真实跟单往返。

### 可审计原始数据和自动门禁

新增以下 append-only 原证据及两个代码测试文件，均在同一 Draft PR 研究分支：
- [Dragon N+1 历史 Helper3 状态、买入 eth_call 模拟、原持仓及 allowance](./bsc-meme-address-model-v1-p4b-lonxia-observer-nplus1-buy-sim-2026-10-16.json)
- [三个真实 TokenSale 原始日志、原始交易及匹配的 ERC20 Transfer](./bsc-meme-address-model-v1-p4b-lonxia-3-real-market-sells-2026-10-16.json)
- `bsc_meme_address_model_v1_p4b_lonxia_observer_gate.py`：两档买入成功、三笔真实其他钱包卖出、原签名人、同 CA、区块时间顺序及 U 不可升级门禁。
- `test_bsc_meme_address_model_v1_p4b_lonxia_observer_gate.py`：冻结数据正向重放及同区块抢先看、伪造成交、卖家金额/身份改写、删负证据、非法升级 U/P5 等回归。
- 原 BSC GitHub CI 增加离线重放；**CI 不执行 Alchemy RPC**，只重算归档字节和判定。

## 下阶段是否能进入 P5？

**尚不能。** 这次更接近用户最初目标：已从“早期买入交易”推进到“原钱包信号之后区块可技术性买入 + 确认之后其他人真的卖得出”的实证层级；但缺口为：

- 历史节点看到 DDAC 区块后的真实第三方信息到达/排队延迟无法由毫秒区块时间推导。
- 0.01/0.1 BNB `minAmount=0` 模拟不是税后滑点约束、承诺容量或实际成交和支付 Gas。
- 完成一个观察者的“买后状态、先授权、再卖出”真实可行回合、资金成本、真实费用与净收入尚未复算。
- 三名真实卖家是**后续其他地址**，不能当作 2ADF 买后的卖出。
- 已研究龙虾及其他四个样本均已暴露，不得用作 `untouched holdout` 并声称 P5 样本外性能。

**状态：`P4-B U=UNRESOLVED (0/5 validated)`; `P4-C=PARTIAL`; `P5=BLOCKED`; `NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。后续以不超过已预冻结的观察路径做有界 source-grade 研究；独立新 SHA 审核、Mac 只读验收各自是独立门禁，不自动升级。**
