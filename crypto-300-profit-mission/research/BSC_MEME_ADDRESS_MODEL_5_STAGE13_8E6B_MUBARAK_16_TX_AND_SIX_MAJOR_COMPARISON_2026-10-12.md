# BSC 地址分析建模 5：Stage 13 / MUBARAK 16 笔完整回执与多重大 Meme 横向经济对照

日期：2026-10-12（Asia/Bangkok）；BNB Chain 主网。仅研究，不修改生产、监控、钱包或实际交易。**OBSERVE_ONLY / NO_GO**。

## 1. 主线进度与审计边界

仓库权威 V19 冻结样本：**23 个钱包 × 19 个 CA = 437/437 组合完成双方向正值 ERC20 Transfer 全游标**。观察到实际转账的组合 **148 个**，无正值转账 **289 个**；独立原始代币数量与链上余额核对已 **109/148**，仍有 **39/148** 未闭合。此处“完整”仅指固定 CA 的 ERC20 正值转账，不等于每笔交易的买卖、资金成本、退出价格或钱包 PnL 已经核实。不会用 balanceOf 快照取代全量转账数量复算。

本阶段把研究重点放到原始经济因果链，尤其检验 **8E6B** 是否真实、反复抓住重大 BSC Meme 上涨机会，同时纳入失败样本，不因为“多币种有活动”就直接做盈利榜。

## 2. 8E6B / MUBARAK：16 笔同一钱包原始交易回执独立交叉核验

钱包 `0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0`，固定合约 `0x5c85d6c6825ab4032337f11ee92a72df936b46f6`。

重新从链上直接读取 **16/16 原始 receipt**，核查 tx hash、本人 `from`、成功状态 `0x1`、`gasUsed × effectiveGasPrice`，和此前冻结的交易、BNB 区块余额差额独立对照，全部符合。**5 笔买入、11 笔卖出相关交易**，5 笔 `msg.value` 共 **3.333 BNB**，16 笔 Gas 合计 **0.02151212 BNB**。这 16 个准确区块钱包 BNB 历史余额差额相加为 **+5.299103329471661818 BNB**。

针对这 16 个区块的 `external` 原生 BNB 转账分别以钱包为发送方和接收方完整分页核查，**16/16 个区块各仅一笔该钱包本人发起的原始交易，其他直接 native 转出为 0，直接 native 入账为 0**。链上 `internal` 类别或 `debug_traceTransaction` 在当前免费数据源不可用，因此依然不能确认没有同区块隐藏内部 BNB 变动，也不能将 +5.2991 BNB 直接升级成完全因果归因的实际已实现利润。

结算路径细分：
- 11 笔卖出相关交易中，**10 笔包含成功回执里的 WBNB Transfer + Withdrawal**，所记载的 WBNB 提现事件合计 **7.557105239505843199 WBNB**。对应十个区块钱包 BNB 余额变动加 Gas（未排除内部效应）低于 WBNB 提现金额 **0.066502526107651415 BNB**；这是“原始提现额与钱包可见收款额的差异”，**不是已审核的协议费率或税费**。
- 第一笔卖出相关原始成功回执**没有 WBNB Transfer/Withdrawal**；该区块原生 BNB 净增 **1.157564561073470034 BNB**，不能假装是 WBNB 卖出，只能标记为不同路由待验证。
- 5 笔买入区块的 BNB 差额与 `-msg.value - Gas` 存在合计 **+0.00396 BNB** 的残差（分笔 +0.0006/+0.0012/+0.0006/+0.0012/+0.00036）。这些是已验证的算术差异，并非直接交易利润，也不应擅自定义为返佣、内部转入或协议补贴。

结论级别：`MATERIAL_POSITIVE_NATIVE_BLOCK_SCOPE; ORIGINAL_OWNER_AND_RECEIPTS_VERIFIED; DIRECT_EXTERNAL_EXCLUDED; INTERNAL_CAUSAL_PNL_UNVERIFIED`。

## 3. 8E6B 在六个重大代币上的正负样本，不以活动次数替代利润

对仓库已有四大机会证据，以及上面 MUBARAK 新审计，统一按原始哈希和区块交叉对照。六个币种各自冻结的历史区块和唯一交易哈希之间没有重复：**6 组、15 个跨组配对，重复交易哈希与重叠区块均为 0**。因此这六组 *原生 BNB 区块差额* 在对应样本窗口没有按同一钱包交易区块重复统计的问题，但**不是六次可跟随的独立完整获利周期**。

| 代币 | 样本原始交易数量 | 历史相关区块 BNB 净变化（BNB） | 交易回执状态 |
| --- | ---: | ---: | --- |
| 4 | 19 | 13.164987 | 19 SUCCESS |
| GIGGLE | 16 | 5.715926 | 16 SUCCESS prior |
| MUBARAK | 16 | 5.299103 | 16 SUCCESS independently rechecked |
| HAJIMI | 13 | 1.242899 | 13 SUCCESS / 0 UNKNOWN (headers truncated) |
| 龙虾 | 13 | 4.794002 | 11 SUCCESS / 2 UNKNOWN (headers truncated) |
| 我踏马来了 | 6 | -0.599024 | 6 SUCCESS prior |

额外重要资产：GIGGLE 同一范围里链上已独立对账 **6 笔 USDT 转入 + 1 笔 USDT 转出，净 +4061.629806775951927704 USDT**；USDT 的金额不能和 BNB 原生余额差额直接相加，更不能把“净资产流入”直接当完整美元利润。

`4` 的两次完整原始 token 出入周期分别为 **-0.117977426190152496 BNB** 与 **+13.282964879793219111 BNB**，说明这一币种的收益高度集中在第二轮，第一轮本身是亏损。`我踏马来了` 的负向对照约 **-0.599023816844905516 BNB**。龙虾样本有两个原始回执状态受截断影响仍未确认。所有多币种正向结果继续按 **区块账本范围证据** 定级，不升级为 `VERIFIED_PROFITABLE_REPEATER`。

### 结论

8E6B 显示明显的**跨多个重大机会的实际交易及正向资金记录**，比仅靠 ERC20 转账数量的候选地址更值得经济复核；但尚未完成所有 token 报价成本、Gas/税费、内部资金流、回合边界、亏损持仓、同价可成交量和机会资格分母，不具备真实盈利排名或跟单生产资格。

## 4. 保留跨钱包对照，防止成功案例筛选偏差

`A83B / BROCCOLI714` 首个原始本人配对买卖的两区块 BNB 余额变化 **-0.239887492433116024 BNB**；`2ADF / BOB` 的范围为 **+0.009515610472872943 BNB**，都不自动代表完整 wallet 或 token 利润。`877AF / MARSCOIN` 首次部分退出对应 FIFO / 加权平均两种**条件性**分摊收益约 **+0.119567/+0.116359 BNB**，首次卖出区块本身混有另外两笔本人交易，完整内部 trace 不可用。研究继续保留正反对照，避免人为只挑赚钱的 Meme 与钱包。

## 5. 下一阶段的主线与不可越过的边界

- 对 **39 个仍未独立代币数量闭合的正值转账组合**，批量执行源端完整转入/转出原始整数求和及同区块余额核验，不能因快照非零、尘埃或旧的 `OPEN_TOKEN_REMAINDER` 就推断盈利或未卖出。
- 对 8E6B、A83B、ADFF、2ADF、877AF、5C0C 先固定一组 2025/2026 重大 Meme 原始交易回合，逐币拆出 `OWNER_ORIGIN`、`PAYMENT_ASSET`、`TOKEN_INVENTORY`、`ACTUAL_EXIT`、`FEE_GAS` 与 `CAUSAL_LIMITATION`；避免在单一亏损或高额利润上反复纠结，保持多个币种齐头推进。
- 把独立的历史可入场资格、初始钱包资金、延迟 5/15/30 分钟和流动性真实成交作为**后续经济充分审计之后的独立验证**；未经其他 AI Review、测试和用户授权，不开发或部署跟单、邮件或生产策略。研究状态始终 **NO_GO**。

## 6. 已入 Git、可复核的固定源文件

- `BSC_MEME_23_EOA_19_CA_EVIDENCE_COMPLETENESS_OVERLAY_V19_2026-10-12.json`（Git blob `cb061d017474e369352801d93278b91aab29c021`）
- `BSC_MEME_8E6B_MUBARAK_16_OWNER_SIGNED_WBNB_NATIVE_EXTERNAL_QA_2026-10-12.json`（Git blob `220d6a849db54ce9853324033b2db67da3e46336`）
- `BSC_MEME_8E6B_SIX_MAJOR_EVENT_DISJOINT_NATIVE_SCOPE_AND_NEGATIVE_CONTROL_2026-10-12.json`（Git blob `91daf8cd87297ac4f2d71be83e3ee03f761b6159`）
- `BSC_MEME_877AF_MARS_FIRST_PARTIAL_EXIT_COST_BASIS_SENSITIVITY_2026-10-12.json`（Git blob `f24029e3cc935fc8190a32bf72642d463dbb428f`）
- `BSC_MEME_8E6B_GIGGLE_7_USDT_QUOTE_REVALIDATED_VS_4_EPISODES_2026-10-12.json`（Git blob `98b344555b8be48deac728a316af4c8a4c056e11`）
- `BSC_MEME_A83B_BROCCOLI714_FIRST_OWNER_ROUNDTRIP_BNB_GAS_SETTLEMENT_QA_2026-10-12.json`（Git blob `54440542e014b02fb69ac3262b9258da930ed6f0`）

附加原始数据：`BSC_MEME_8E6B_MUBARAK_16_RECEIPTS_BATCH_A/B/C_2026-10-12.json` 和 `BSC_MEME_8E6B_MUBARAK_16_BLOCK_NATIVE_EXTERNAL_EXCLUSION_A/B/C/D_2026-10-12.json`，单笔账本及 SHA 全部记录在汇总 QA JSON 中。

没有修改任何已有阶段历史文件，未调用 GMGN 付费 API、未增加生产依赖，未执行交易或部署。
