# P4-B：2026 年五轮本人签名交易的历史信号生命周期复盘

日期：2026-10-18。原冻结 23 钱包 × 19 exact CA = 437 格不变。本批仅检查 3 个原钱包、2 个代币、5 轮已经由旧来源冻结的签名真实交易；没有增加新钱包或追逐新赢家，也不计算策略胜率。

## 五轮真实正负和“信号是否还在”

| 钱包/代币 | 原签名交易区块 | 本人选定经济回合 BNB 净变化 | 研究结论 |
|---|---|---:|---|
| DDAC/龙虾 | 83635776 买入 → 83635800 全部退出 | −0.092169615514614272 | 旧买入信号在本人真实退出后失效；D503 在 83636000 才买入 |
| 239E/龙虾第 1 轮 | 85954137 买入 → 85954824 **加仓** → 85957578 退出 | −0.015332805033002259 | 同一仓位第二笔买入，不是新的独立盈利机会 |
| 239E/龙虾第 2 轮 | 85959961 **重新入场** → 85961371 退出 | +0.022647938898252522 | 旧仓位清空后相隔 2383 块产生新一轮买卖，不能恢复旧信号 |
| 8E6B/HAJIMI | 74741352 买入 → 74741573 **部分卖出** → 74741587 卖光 | +0.268592992917629933 | 第一次卖出后剩余 64629048195327088600524 raw，不应误判已清仓 |
| 8E6B/龙虾 | 93584281 买入 → 94208823 退出 | +0.253300282319389315 | 真实正向原钱包回合，不是早期公开可跟单证明 |

同一 239E 钱包同一龙虾 CA 两轮正负相反，选定 BNB 净变化相加仅 +0.007315133865250263 BNB；不是全钱包历史利润。同样，三正两负是**事后精选样本**，绝不能报成 60% 策略胜率。

## 新模型能识别的历史状态

已先将五轮事件、对应查询检查点及来源 Git blob SHA 固定在 [预冻结文件](./bsc-meme-address-model-v1-p4b-5owner-rounds-signal-lifecycle-precommit-2026-10-18.json)。

[复算程序](./bsc_meme_address_model_v1_p4b_original_owner_signal_lifecycle.py) 用原签名交易的确切 token 数量按块顺序生成下列**已归档事件内的状态**：首次买入、已有仓位加仓、部分退出仍持有、完全退出、完全退出后重新买入、当前样本之前尚没有签名交易可判定。239E 两次加仓和两轮正负结果均原样保留；HAJIMI 半仓退出按逐 raw 数量结算，不能见到任何 SELL 就标记仓位清零。

所用来源均未改动：[DDAC 龙虾负向结算](./bsc-meme-address-model-v1-p4c-dragon-ddac-closed-native-loss-2026-10-15.json)、[239E 龙虾两轮真实结算](./bsc-meme-address-model-v1-p4c-239e-dragon-two-owner-native-settlements-2026-10-15.json)、[8E6B HAJIMI 和龙虾 WBNB/Gas 正向回合](./bsc-meme-address-model-v1-p4c-8e6b-hajimi-dragon-two-verified-native-positive-2026-10-15.json)、[原 23×19 市场矩阵](./bsc-meme-address-model-v1-p4c-23x19-crosswallet-native-verified-matrix-2026-10-15.json) 与 [D503 较晚真实买入](./bsc-meme-address-model-v1-p4b-dragon-postowner-original-seven-txs-2026-10-16.json)。[14 项正负用例](./test_bsc_meme_address_model_v1_p4b_original_owner_signal_lifecycle.py) 包括 239E 加仓不重复计数、清仓后重新入场、HAJIMI 部分卖出非全部退出、DDAC 先卖后 D503 入场等。

**证据硬边界：** 这些信号状态只指所选本人已归档成功签名交易的重建，不是在历史任意区块读取全部真实 ERC20 余额；同块别的交易、区间外赠币转出、实时余额没有覆盖。尚未核实第三方真正收到信号的时间、公网首次可执行 U、固定延迟 1／5／15 分钟入场的真实成交、费用与完整退出净收益。区块高度差不等于分钟。

**业务下一步：** 真正生成面向用户的信号之前，应先把旧钱包 CA 的最新持币事实与当前新买单关联，并以本人确切退出为旧信号作废条件、部分退出为风险降低条件、退出后重入为新的独立回合。以上只是待多市场测试的设计假设，不升级为生产规则。

状态保持：P4-B=PARTIAL / PUBLIC_EXECUTABLE_U=UNRESOLVED / P5=BLOCKED / PRODUCTION=NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE。
