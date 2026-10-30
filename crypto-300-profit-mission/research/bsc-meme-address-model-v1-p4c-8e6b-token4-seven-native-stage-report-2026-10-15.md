# BSC 地址建模 P4-C — 8E6B「4」原始 19 笔独立复核、7 回合 / 5 单元经济矩阵

**研究日期：2026-10-15 Asia/Bangkok。** 此阶段用户明确放弃先前 BSC 页面设计，继续 BSC 原始地址分析和可跟单收益证据主线。原 [Mission Draft PR #40](https://github.com/lxxlx2/ChatGPT_mission_record/pull/40)，只读研究；未部署、未发通知或交易、未合并 PR。

## 结果 — 历史 EOA 本人结果，不是跟单策略结果

冻结原样本 23 个 EOA × 19 个 exact CA = **437** 个钱包×代币研究单元。上一阶段已高等级验证的 5 个原钱包 BNB 经济回合（3 正 / 2 负）覆盖 **4** 个钱包×CA 单元，本阶段在原 19 CA 内补入 Stage24 早已冻结的 8E6B「4」两个历史本人真实经济回合：

| 冻结历史原钱包 | 代币 | 冻结 P2 回合 | 买卖交易数 | 原钱包 BNB 净额（含原始 Gas、实际差额） | 历史发生时间 | 分级 |
| --- | --- | --- | --- | --- | --- | --- |
| `0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0` | `4` CA `0x0a43fc31a73013089df59194872ecae4cae14444` | #16、episode 1 | 1 买、1 卖 | **−0.117977426190152496 BNB** | **2025 年** | 原钱包本人负收益 |
| 同钱包同 CA | `4` | #17、episode 2 | 1 买、16 卖 | **+13.282964879793219111 BNB** | **2025 年** | 原钱包本人正收益 |

- 两回合 ERC20 原始 token 库存数量完全闭合为 0。冻结 19/19 原钱包本人签名成功交易，19 笔原始报价/WBNB 退出、实际 Gas、钱包 BNB N−1/N 区块变化与路由成本差额逐项整数闭合。相关资产是原钱包 **原生 BNB**，不是用今日市场价格估算。
- 在新读链前**冻结 5 笔独立核对交易**（负向：买入与卖出；正向：买入、首笔卖出、最终卖出）。5/5 重新读取 BNB Chain 主网 signer/chainId/块号、**完整成功回执**、WBNB Deposit/Withdraw 和 ERC20 Transfer 成对金额、receipt gasUsed×effectiveGasPrice、原钱包 N−1/N 余额，全部与最初的 Stage24 原始历史固定整数吻合。剩余 14 笔仍以旧的完整来源和原始 receipt verification 的 Git 字节证明为基础，**不能将 5/5 spot 当成 19/19 全部重新读取**。
- 此外，对之前**预冻结 19 个原始交易区块**，从 BNB 主网 Alchemy 原生外部转账索引重新双向查询：**19/19 外发来源完整、各仅一笔预选 EOA 自发原始交易；19/19 未发现其他外部 BNB 进入该钱包；0 分页未完成、0 provider 截断**。这排除“额外外部 BNB 同块转账污染”，但**不等价于验证全部内部 trace，无法独立归属完整协议收费人**。
- 「4」的正负回合发生在 **2025 年**，不能写成 2026 年发现的信号；这仅补强覆盖冻结的历史重大 CA 与钱包结果，不能替代 2026 新机会因果验证。

## 严格按回合和不同钱包×CA 单元分别计算

加到此前 5 个原钱包真实经济回合之后：

| 统计维度 | 阶段数值 | 语义 |
| --- | ---: | --- |
| 原始不同钱包 | 23 | 冻结研究钱包总分母，非“盈利钱包数” |
| 冻结重大 exact CA | 19 | 不允许把更多未来钱包硬写死为仅 23 |
| 钱包×CA 组合 | 437 | `23×19` |
| 已核对真实历史 EOA BNB 经济**回合** | **7** | 4 正、3 负，包括本轮 token4 一正一负 |
| 已覆盖的不同钱包×CA 经济**单元** | **5** | 8E6B/HAJIMI、8E6B/龙虾、8E6B/4、DDAC/龙虾、239E/龙虾 |
| 尚未同等级审计的经济单元 | **432** | 含此前 ADFF、A83B、877AF 原始数量闭合但报价/Gas 不足的单元 |
| 至少一次原始 EOA 正向且高等级已审钱包 | **2** | 8E6B 与 239E；239E 龙虾及 8E6B「4」均有历史负回合 |
| 具有 3 个不同重大 CA 历史正向闭合回合的钱包 | **1** | 仅 8E6B：HAJIMI、龙虾和 **2025 年**「4」 |
| 已通过 P4-B U + P5 延迟跟单完整验证的可执行信号 | **0** | 不得根据钱包历史净收益建议买入、仓位或预期收入 |

本批次是原 P2 选择性抽样和高度聚焦钱包，并**非**整个 23×19 437 格的无偏估计，更不能据此计算“策略胜率”、当前 Meme 推荐或真实 1/5/15 分钟跟单收益。

## 证据追溯、代码和 CI

- 先前冻结的 19 original token4 交易、两个正负样本、5 笔现场复核抽样：`bsc-meme-address-model-v1-p4c-8e6b-token4-two-rounds19-precommit-2026-10-15.json`。
- 两份 5 笔新读主网完整交易/回执/历史余额：`bsc-meme-address-model-v1-p4c-8e6b-token4-independent-five-part1-2026-10-15.json`、`bsc-meme-address-model-v1-p4c-8e6b-token4-independent-five-part2-2026-10-15.json`。
- Stage24 原始旧证据继续只读 Git 原件：`BSC_MEME_STAGE24_8E6B_TOKEN4_TWO_ROUNDS_THREE_MAJOR_POSITIVE_COHORT_2026-10-13.json`、`BSC_MEME_8E6B_4_EXACT_SETTLEMENT_RECONCILIATION_2026-10-11.json`、`BSC_MEME_8E6B_4_ORIGIN_RECEIPT_VERIFICATION_2026-10-11.json` 和 `BSC_MEME_8E6B_4_NATIVE_BLOCK_AUDIT_2026-10-11.json`。
- 每一字节输入的真实 Git blob SHA 存在 `bsc-meme-address-model-v1-p4c-8e6b-token4-two-settled-source-audit-2026-10-15.json` manifest；离线复算 `bsc_meme_address_model_v1_p4c_8e6b_token4_two_native.py`；对抗 `test_bsc_meme_address_model_v1_p4c_8e6b_token4_two_native.py`。
- 后补**原始全部 19 区块外部 native 污染排除**：`bsc-meme-address-model-v1-p4c-8e6b-token4-19external-precommit-2026-10-15.json`，4 份 `bsc-meme-address-model-v1-p4c-8e6b-token4-19external-part{1..4}-2026-10-15.json`，标准化 `bsc-meme-address-model-v1-p4c-8e6b-token4-all19-external-exclusivity-2026-10-15.json`，独立来源固定 SHA 复算 `bsc_meme_address_model_v1_p4c_8e6b_external19.py` 及对抗测试。
- **整表追加而非覆盖历史版本**：`bsc-meme-address-model-v1-p4c-23x19-seven-native-mixed4-2026-10-15.json`，确定性 `bsc_meme_address_model_v1_p4c_seven_rounds23x19.py` 及单元测试。
- 初版外部核查 replayer 在旧标准化 P4-C 经济结果的 `NO_GO` 读取字段位置不一致处出现 `KeyError`；修复为兼容原 source `summary.production`，不修改原始链上来源。最新 BSC 主模型 CI 与 3 个专项工作流已通过（固定 SHA / Actions 链接在后续计划更新中核对）。

## 模型门禁与下一步

- **本阶段经济口径需要新的其他 AI 独立审查**，因为扩充了原生钱包盈利/亏损总回合和「8E6B 三 CA 正向」结论。历史其他 AI `APPROVE` 仅涵盖旧 SHA `ea6684a3478d301534ff9d26b5984367eb7530f3`，不覆盖此代码、资料、经济结论。按 BSC 开发规则给用户提供固定最新 HEAD 完整审核提示词、精确源/CI 链接，报告当前 `PENDING_OTHER_AI_REVIEW`。
- 此后别继续围绕 8E6B / 「4」反复刷同区块调用。回到**不同 EOA、2026 年重大 Meme** 的真实可比盈利/亏损对照；对免费来源无法完整获取 receipt、quote、Gas 的记录保留 `UNRESOLVED` 和样本分母，不能当作盈利钱包。
- P4-B 还需证明全球观察者首次可见且真实可买卖的历史机会 U（特别是 launchpad、V2、V3、USDT 非同源资金）；P5 仍需考虑 1/5/15 分钟实际延迟、容量/滑点/税费、Gas、失败、卖出路径和真实退出，不能由高收益原钱包成绩推断可跟单。
- **P4-C PARTIAL / P4-B U UNRESOLVED / P5 BLOCKED / PENDING_OTHER_AI_REVIEW / NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE**。未修改前端、Frank、Monster、Mac 服务、真实钱包或通知。
