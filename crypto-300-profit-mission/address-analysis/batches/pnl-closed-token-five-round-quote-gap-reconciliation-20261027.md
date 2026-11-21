# 449 地址盈利主线：5 个 Token 闭合回合与 3 个 WBNB 事件报价交叉核验

Date: 2026-10-27 Asia/Bangkok
Mode: **RESEARCH_ONLY / FROZEN_2026-10-19_EVIDENCE / NO_NEW_RPC / NO_TRADES**
PR: **#97，原有 Draft 分支更新**。这是已有证据的独立整数复算，**不是新成交数据，也不提高可证明净利润样本数量**。

## 1. 两项冻结数据集不是同一维度

- PR #40：23 个 BSC 研究钱包 × 19 个 exact-CA 历史重大代币 = **437 钱包—币种组合**，不是 437 个钱包，也不是 449 个地址。PR #40 的正负闭合回合和跨代币机会分母仍由该独立 Draft 管理，不能混入此处的 449 行号。
- 本 PR #97：固定来源 **449 个独立 EVM 地址**，原顺序 23 批，每批最多 20。BSC/Ethereum/Base 历史冻结窗口已做活动筛查 **449/449**，其中 **237** 有至少一条检查链的签名 nonce 活动，**212** 在三条检查链没有签名增长。**237/237** 的出账事件**第一页**已读，仍有 **171 个活跃候选队列位置存在未完成分页**。这不代表已审交易总覆盖，也不是盈利排名。
- 当前有 **5 条**具体闭合 Token 进出记录，来自 **4 个原始地址**；其中 **3 条**可进一步找到相同交易哈希的 WBNB Router Deposit/Withdrawal 事件。**已批准的单笔交易净 PnL = 0 条；30 日及长期完整钱包 PnL = 0/449**。
- 历史 #016 RTX5090 在另一份原始证据中，**不在这个五回合账本内**；#002/#004 sauce 同币及关联时点，不作为两套独立随机策略。不得用此表的 5 个案例描述全部历史交易。

## 2. 已能精确复算的交易证据

| 源行 / Token | Token 库存 | 买入 WBNB 事件 (BNB) | 卖出 WBNB 事件 (BNB) | WBNB Router 事件差额 (BNB) | 原钱包执行区块 BNB 变化 (BNB) | 两种口径差额 (BNB) | 审核分类 |
|---|---|---:|---:|---:|---:|---:|---|
| #227 BOARDSEAT | 买入量 = 卖出量 | 0.330000000000000000 | 0.483663976630184592 | +0.153663976630184592 | +0.139871398530549414 | **−0.013792578099635178** | 交易哈希匹配的 Router 报价事件；**非净利润** |
| #227 BTCLIFE | 买入量 = 卖出量 | 0.330000000000000000 | 0.149944555963376124 | −0.180055444036623876 | −0.190058157929590970 | **−0.010002713892967094** | 交易哈希匹配的 Router 报价事件；**非净利润** |
| #400 BOARDSEAT | 买入量 = 卖出量 | 0.990000000000000000 | 0.668967157750727214 | −0.321032842249272786 | −0.337858120186780058 | **−0.016825277937507272** | 交易哈希匹配的 Router 报价事件；**非净利润** |
| #002 sauce | 买入量 = 卖出量 | **UNRESOLVED** | **UNRESOLVED** | **UNRESOLVED** | +0.156828105278687674 | 无法归因 | Token 闭合 + 区块余额正向候选 |
| #004 sauce | 买入量 = 卖出量 | **UNRESOLVED** | **UNRESOLVED** | **UNRESOLVED** | +0.154215798043203099 | 无法归因 | Token 闭合 + 区块余额正向候选 |

精确公式：`event_spread_wei = sellWbnbWei - buyWbnbWei`；`gap_wei = nativeBlockDeltaWei - event_spread_wei`。全部使用整数 wei 运算，表内 BNB 为除以 `10^18` 后的定点十进制，不使用浮点估计。

**三个 gap 不等同 Gas**，因为 WBNB 包装/解包装、Router 内部现金流、原生 BNB 直接交易、合约收费、转向其他接收者、授权 Gas 与同区块其它活动尚未形成完整的、唯一归属同一笔 Token 往返的结算闭环。方向一致也不构成费用或利润归因。特别是 #227 既有一个正向、又有一个负向候选，不能只挑 BOARDSEAT 报“盈利地址”。

## 3. 链上证据与固定来源（Git blob）

- `state/pnl-canonical-closed-token-ledger-20261019.json`：blob `e1e1e1eea4f8c5aa998d3278eb18bc9c6b20c623`，5 回合原始 Token 数量、钱包地址、买卖哈希及净 PnL = UNRESOLVED；
- `evidence/pnl-mainline-wbnb-event-quotes-20261019.json`：blob `53f4e00610c5a7540b1f8641d26b23f9870e8194`，3 回合 exact buy/sell 哈希、WBNB Deposit/Withdrawal、原生余额及未经归因的 residual；
- `evidence/activity-candidates-001-449.json`：blob `4727b8b53dcd63b350d9e5f27922cd06db8a2a14`，449 固定行号、原始地址、237/212 活动分类。

离线复算入口：`python3 crypto-300-profit-mission/address-analysis/tools/reconcile_closed_token_quote_gap_offline.py`；它按 Git blob 校验原始文件，再核 exact wallet/source row/CA、完整进出库存、三笔买卖 tx 哈希、事件 quote 与 BNB 差额，输出只含证据等级的 JSON 到标准输出，**不写账本、不调用 RPC**。配套单元测试检查 449 分母、篡改 tx hash、篡改 WBNB 金额、伪造净利润和源 blob 变更。

## 4. 下一步实际盈利交付：不继续循环做“首页已查”

**最优先找到当事钱包直接收付的 WBNB、官方 USDC 或其他可验证报价资产的历史闭合买卖**；同时需要完整本人签名成功收据、真实初始购买成本、实际退出净收入、Gas/手续费和原始数值。来源不能完全归因就保留 `NATIVE_BALANCE_DELTA_ONLY` / `UNRESOLVED_COST`，到有界免费查证上限标 `DEFERRED` 转下一个地址，而不是为了消除3个老 gap 无限重复查询。

交付时依次补：**第一笔真正 `TOKEN_VERIFIED_PNL`（正负均须保存） → 原钱包30天和长期 PnL 的完整交易分母 → 跨代币多次盈利证据 → L1/L2可观察且可成交的未来跟单评估 → L3/L4 对照组**。PR #40 历史重大代币研究与 PR #97 的 449 地址仍保留独立来源，F0 20 主/10 备预选**不能**使用事后利润反向改样本。

**保持 `RESEARCH_ONLY / OPEN_DRAFT / NO_NEW_RPC / NO_DEPLOY / NO_TRADES`；BSC F0 仍 `D1_BLOCKED_AUTHORITY / F0_NOT_PASSED / PRODUCTION_NO_GO`。** 当前文件不批准任何新采样、签名或交易。
