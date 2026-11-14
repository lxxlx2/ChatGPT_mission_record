# BSC P4-C — 8E6B 历史代币「4」两组真实 BNB 正负回合独立抽核

时间：2026-10-15 Bangkok。仓库 `lxxlx2/ChatGPT_mission_record`，原 [Draft PR #40](https://github.com/lxxlx2/ChatGPT_mission_record/pull/40)，研究只读。**此报告不是当前 BSC 信号推荐，也不是 2026 年初始市场可执行机会。**

## 样本为什么要保留、不能误用

严格复用 P2 冻结 23 EOA × 19 exact CA 中 8E6B `0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0` 与代币「4」`0x0a43fc31a73013089df59194872ecae4cae14444` 的两组原始库存回合（P2 #16 / #17），**一亏一赚**，共 **19 笔**原始签名成功收据：回合 #16 1 买 1 卖；#17 1 买 16 卖。正负对照与五笔独立抽查位置在新 RPC 前写入 `bsc-meme-address-model-v1-p4c-8e6b-token4-two-rounds19-precommit-2026-10-15.json`。

**历史年份门禁：经 BNB mainnet 区块 header `timestamp`/blockHash 原始读取，本组实际开始于 `2025-10-01T04:08:45Z`（区块 63056884），最终卖出于 `2025-10-13T08:13:21Z`（区块 64458294）。** 原始整区块 RPC 约 8 KB 后返回截断，但开头区块高度、hash、timestamp 字段可核实；详情在 `bsc-meme-address-model-v1-p4c-8e6b-token4-2025-blocktime-header-2026-10-15.json`，来源 blob 由对抗回归固定。**这是 2025 历史正负控制；不能作为 2026 Meme 新发机会的已验证样本。**

## 原始历史钱包经济结果，不是跟单收益

| 来源 P2 回合 | 已确认本人买入/卖出 | 原始 BNB 买入本金（不含 Gas） | 实际退出 WBNB 总额 | 本人实际付 Gas | 观察到的退出路由金额差 | 最终钱包 BNB 净变化 |
| --- | --- | --- | --- | --- | --- | --- |
| #16（负） | 1 / 1 | 0.5 BNB | 0.392489121020047983 WBNB | 0.006541656 BNB | 0.003924891210200479 BNB | **−0.117977426190152496 BNB** |
| #17（正） | 1 / 16 | 0.3 BNB | 13.612008635725316651 WBNB | 0.023925089273120164 BNB | 0.005118666658977376 BNB | **+13.282964879793219111 BNB** |

**原始整数核算**：每笔卖出的本人 BNB 余额变化 `WBNB_Withdraw - paid_Gas - observed_route_difference`；买入余额变化 `-tx.value - paid_Gas`；原 19 笔固定账户变动总额 **+13.164987453603066615 BNB**。19/19 过去已有实际链上完整交易回执及本人签名证明；仓库中 Stage24、原始对账、19 回执身份源经**逐笔哈希/区块、原始库存、WBNB/BNB、实际 Gas 和账户净变动**重新离线对齐，19/19 一致、原始两回合 token 库存均归零。

**独立新查询的范围必须准确披露**：仅新查询**预冻结的五笔**（第 1 回合买/卖；第 2 回合买、首卖、末卖）；并非本次另行实时抓取全部 19 笔。五笔独立 read-only `eth_getTransactionByHash` 确认 EOA+chainId=56+block，**5/5 完整成功回执**、Gas、历史账户 `N−1/N` 差和 WBNB Deposit/Transfer 或 WBNB Transfer/Withdraw 数量，全部吻合旧完整来源。源：`bsc-meme-address-model-v1-p4c-8e6b-token4-independent-five-part1-2026-10-15.json`、`...-part2-2026-10-15.json`，其 SHA 和历史源 SHA 都由新重放器固定。

**不能凭空命名费用**：两笔独立新查买入分别付 **0.500 BNB、0.300 BNB**，但真实 WBNB Deposit + Transfer 给交易池分别只有 **0.495 WBNB、0.297 WBNB**，买入本金与实际报价资产存入差额分别为 **0.005 BNB、0.003 BNB**。这些是已核实差额（恰好为付款金额的 1%），不是已确认的手续费受益人或税的最终归属。卖出端另有前表严格观测到的路由差额，其具体收款方不能仅用 EOA 余额和 WBNB log 推断。

规范化源：`bsc-meme-address-model-v1-p4c-8e6b-token4-19tx-five-independent-source-reconciliation-2026-10-15.json`。
确定性原始字节 Git blob SHA 重放：`bsc_meme_address_model_v1_p4c_8e6b_token4_19tx.py`。
对抗回归：`test_bsc_meme_address_model_v1_p4c_8e6b_token4_19tx.py`（源 SHA 漂移、证据内容与原收据不一致、重复/缺失、假造 Gas/WBNB、假造 N−1/N、忽略负回合、错误身份和2025时间门禁）。

## P4-C、P4-B、P5 严格门禁

- 这份两回合原生现金流是 **8E6B / 「4」历史样本**，同一个钱包同一个 exact CA，有正有负；**最多对应 1 个 23×19 的 wallet×CA cell**，不能把 2 回合当作 2 个赚钱钱包，也不能据此估算 2026 新币命中概率。
- 当前 **独立其他 AI 审核尚未覆盖本次 SHA**，因此本阶段新增的 8E6B/「4」应先作为 **`HISTORIC_NATIVE_SETTLEMENT_REPLAYED_REVIEW_PENDING` 候选高等级证据**。旧发布/审核口径的 23×19=437 的正式统计仍为 **5 个已来源复核原生 BNB 回合、4 个 wallet×CA cells、433 个未按同口径审核的 cells**；在新 SHA 通过独立复核前，不得擅自把这里额外两回合当作审核通过的 2026 样本，也不能把旧 5 和新 2 当作模型交易信号。
- 继续优先寻找**不同钱包且真正发生在 2026 的**重大 Meme 正负成交案例，并查资本金和市场首次观察者可跟入点 U；P5 需历史可得 1/5/15 分钟真实买入/退出，含池子深度、价格冲击、交易税、Gas、容量和失败样本。当前这些仍然缺失。
- [PR #40](https://github.com/lxxlx2/ChatGPT_mission_record/pull/40) 必须维持 Draft；无合并、无部署、无后台采集、无 Gmail、无自动交易、无对 Frank/Monster/网页修改。P4-C **PARTIAL**、P4-B 首次可执行 U **UNKNOWN**、P5 **BLOCKED**、production **NO_GO**。
