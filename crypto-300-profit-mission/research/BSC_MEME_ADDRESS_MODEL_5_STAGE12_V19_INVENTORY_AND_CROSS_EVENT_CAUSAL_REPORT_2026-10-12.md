# BSC 地址分析建模 5：Stage 12 / V19 原始数量闭合与跨 Meme 经济归因

日期：2026-10-12，Asia/Bangkok。BSC / BNB mainnet。严格按 Mission 2026-10-10 冻结候选的 23 个 EOA 与 19 个代币 CA。**RESEARCH / OBSERVE_ONLY / PRODUCTION=NO_GO**。

## 结果先行

| 检查项目 | Stage 11 V18 | Stage 12 V19 |
| --- | ---: | ---: |
| 全量 ERC20 正值 Transfer 双方向游标完成 | 437/437 | **437/437** |
| 冻结样本内有 ERC20 转账的组合 | 148 | **148** |
| 有转账且完成独立原始数量闭合的组合 | 106 | **109** |
| 仍缺独立数量闭合的有转账组合 | 42 | **39** |
| 在冻结样本内完全覆盖 19 CA 的钱包 | 23/23 | **23/23** |

当前对 V18 原 42 个尚未独立闭合的组合，已在统一 BSC 区块 `0x79549a0` 全部重新执行 ERC20 `balanceOf(wallet)`：**42/42 RPC 查询成功，42/42 原始余额非零**。这些快照不单独完成转账流量闭合。5 个余额只有 1 或 2 个代币最小整数单位，可能是尘埃，不得称为一个完整显示单位代币，更不得未经市场价格和 decimals 证明就计入有价值的持仓。

随后针对三个有意义的源组合继续重新跑完双向正值 ERC20 历史游标，`uniqueId` 去重，独立 `balanceOf` 同区块原始整数金额验证闭合：

| 钱包 | 代币 | 完整 in/out 日志 | 同区块原始余额 | 利润状态 |
| --- | --- | ---: | ---: | --- |
| `8E6B` | TUT | 6 / 4 | `28050472618166057283` | 未确认 |
| `877AF` | GIGGLE | 2 / 0 | `538193267724672920` | 未确认 |
| `A83B` | BULLA | 1 / 0 | `149450289467938143498` | 未确认 |

三项已计入 V19 的 109，39 项仍待独立数量对账。非零余额也不意味着可交易、有利润或真实经济价值。

## 跨币种归因：8E6B 已有可关注的重复经济活动，但最终盈利尚不应排名

`0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0`

**4：** 先前已保存 19 个 owner-signed / success 交易与两轮完整 token 数量退出，BNB 区块范围净余额 **+13.164987453603066615 BNB**。两轮分别为 **-0.117977426190152496 BNB** 和 **+13.282964879793219111 BNB**。两轮一亏一赚，单一较大盈利回合驱动最终数额。缺少完全独立的 internal native trace，仍不得等价于最终已实现净利润。

**GIGGLE：** 已有 16 笔原始本人交易和 16 个 native 区块的历史核对。新一轮读取 6 笔 USDT 入账、1 笔 USDT 出账，按相同原始交易哈希和 USDT 合约 `0x55d398326f99059ff775485246999027b3197955` 分别重新在相应区块查询，7/7 原始整数金额完全一致：

- GIGGLE 相关 16 区块范围 BNB 钱包余额净变化 **+5.715925819273344974 BNB**；
- USDT 原始净变化 **+4061.629806775951927704 USDT**；
- BNB 资产范围里另有 **0.0006 BNB** 异常非交易残差，尚待进一步归因；
- USDT 与 BNB 不能按数字相加，也不能直接作为已确定美元利润。内部转账、费率及机会资格必须继续核验。

综合两币，8E6B 值得保持为 `PRIORITY_FOR_CAUSAL_CROSS_TOKEN_ECONOMIC_AUDIT`，**不授予 verified profitable repeater 或 copyable trader 标签**。

## 877AF / MARSCOIN：首次部分卖出存在正收益条件估算，但不能机械当成已实现 PnL

`0x877af245c61289b24f0c619a4346cdbc68f1aaac`

原始记录显示首次卖出前 7 笔本人发起的 MARS 买单，原始支付 **0.61 BNB**。历史 4 个买入区块钱包原生 BNB 合计流出 **0.61142653456 BNB**（包含 gas / 其他区块效应）。首个卖单卖掉前 7 笔买入 token 数量的 **64.1093%**。

**实质性负向控制**：卖单区块另有该钱包原始发起的两笔交易，一笔向其他地址发送 **0.0001 BNB**，两笔成功回执合计 Gas **0.0000419976 BNB**。因此该卖单区块原记录 **+0.508198463321432886 BNB** 不能直接标为该笔卖出净所得。仅在这两笔是当区块其余相关原生钱包经济变化、且无未知内部转账的条件下，卖单 after-gas 原生收款测算为 **0.508340460921432886 BNB**。当区块已经独立查询到对应原始卖单向经理合约转入 **0.513786330627709985 WBNB**。假设 1% 经理费时，反推单独卖单 Gas **0.0003080064 BNB** 能实现精确算术对齐；经理费未能从完整原始回执独立确认，不能升级该假设。

按前 7 笔总买入区块花费分配已卖部分的成本，获得两个条件性数值：

| 成本分配法 | 分配到首次卖出数量的成本（BNB） | 条件性收益（BNB） |
| --- | ---: | ---: |
| 加权平均成本 | 0.391981483096472565 | +0.116358977824960321 |
| FIFO（首笔入量足以覆盖首次卖量） | 0.388772987925825305 | +0.119567472995607581 |

以上均是 `CONDITIONAL_SCOPED_PNL_SENSITIVITY`，不计为 `VERIFIED_REALIZED_PNL`。第一次卖出后余下买入数量及后续所有交易仍待单独经济账本；不得使用整个卖出区块原生变化忽略同区块另外两笔交易。

## 877AF / GIGGLE：重要的“有转账不代表抓住机会”负向控制

同一钱包历史只有 **两笔正值 GIGGLE 转入，无转出**，数量已于 V19 完整闭合。逐笔查询原始 transaction `from`：

1. `0xb91fcc8bfa951eb473941128fa79759a9e7906bb9d3bd9d66f9ed8ec32d975b9`：原始发起人 `0x679d8a9a2bb243ca42d0c3a7a49d46203b5a0632`，**并非钱包本人**。同区块没有钱包直接发起的 native external 交易及钱包 ERC20 支付日志。
2. `0x41d1b44d7f17218ed671609bab4cbd6dbe9eb613ed79540ff9d0be0d905fd230`：确实是钱包本人原始发起，原生 `msg.value=0`，同区块没有钱包 ERC20 支付日志。合约调用 `0x84da2c7b` 的经济来源尚未独立解码，可能还涉及内部协议结算。

GIGGLE 在该地址的“转账覆盖币种”指标应保留，但“原始本人付费买入并获利”的确认数量仍为 **零**。第一笔不能算钱包主动买入，第二笔不能凭本人签名就当免费领取或 DEX 买入。A83B / BULLA 同样是单笔入账、未见本人原始 native external 或 ERC20 支付，原始签名因服务端长回执截断未确认，保持 unresolved。

## 继续研究与生产边界

下阶段先分批把 39 个剩余有转账组合按同区块双向历史总额完成数量闭合；然后聚焦 8E6B、877AF、A83B、ADFF、2ADF 的 **owner signer + 真实入场付款 + 买卖收款 + 多报价资产 + gas/税费 + 全部有效 major events**，保留亏损案例。关键成果是形成可审查的每钱包跨大机会“真实、条件性、未确认”三栏经济矩阵。证据允许后才进行 5/15/30 分钟延迟成交验证与其他 AI review。

不创建生产监控，不接入 Gmail，不部署跟单，不修改现有 production 策略；**NO_GO**。

## 主要原始 Git 证据

- `BSC_MEME_23_EOA_19_CA_EVIDENCE_COMPLETENESS_OVERLAY_V19_2026-10-12.json`（blob `cb061d017474e369352801d93278b91aab29c021`）
- `BSC_MEME_V18_UNCLOSED42_FIXED_BLOCK_BALANCE_GLOBAL_QA_2026-10-12.json`（blob `5e911ab27e2a5c6d12639ea450c37f5cb211382a`）
- `BSC_MEME_877AF_MARS_FIRST_PARTIAL_EXIT_COST_BASIS_SENSITIVITY_2026-10-12.json`（blob `f24029e3cc935fc8190a32bf72642d463dbb428f`）
- `BSC_MEME_8E6B_GIGGLE_7_USDT_QUOTE_REVALIDATED_VS_4_EPISODES_2026-10-12.json`（blob `98b344555b8be48deac728a316af4c8a4c056e11`）
- `BSC_MEME_877AF_GIGGLE_TWO_INBOUND_OWNER_SIGNER_NEGATIVE_CONTROL_2026-10-12.json`（blob `362f20ad6d435f97d9036e96f34a765e89639ff6`）
- `BSC_MEME_8E6B_TUT_BIDIRECTIONAL_RAW_INVENTORY_BALANCE_QA_2026-10-12.json`（blob `602c6e037de6fa0503833125c1201f604c2e3ef9`）
- `BSC_MEME_877AF_GIGGLE_BIDIRECTIONAL_RAW_INVENTORY_BALANCE_QA_2026-10-12.json`（blob `8e2ff31436baf14c9a53567d2eb2234f3056a692`）
- `BSC_MEME_A83B_BULLA_BIDIRECTIONAL_RAW_INVENTORY_BALANCE_QA_2026-10-12.json`（blob `dcde8221582f83e671c22b1a83af9c0e03a38539`）
