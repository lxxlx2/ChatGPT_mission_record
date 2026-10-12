# BSC 地址分析建模 5：Stage 15 / V21 全冻结样本 ERC20 库存闭合与经济账本推进

日期：2026-10-12（Asia/Bangkok）。BNB mainnet；研究范围严格采用已冻结的 23 个钱包和 19 个 exact CA。**OBSERVE_ONLY / NO_GMGN_PAID_API / NO_PRODUCTION_DEPLOYMENT / NO_GO**。

## 一、结果与证据等级

| 指标 | Stage 14 V20 | Stage 15 V21 |
|---|---:|---:|
| 冻结钱包完整 CA 分页 | 23/23 | **23/23** |
| 地址×代币合约 ERC20 双向游标完整 | 437/437 | **437/437** |
| 有正值 ERC20 Transfer 的组合 | 148 | **148** |
| 独立原始数量守恒、同历史区块余额核验 | 117/148 | **148/148** |
| 仍缺 token 原始数量对账 | 31 | **0** |
| 无正值 Transfer 且游标完整的组合 | 289 | **289** |

**注意：这次完成的工作是特定 19 个合约上正值 ERC20 Transfer 的完整原始数量闭合，绝不是 148 次买入卖出、148 个赚钱的仓位或 148 次可跟单机会。** 旧的 `CLOSED_TOKEN_QUANTITY`、新的 `RAW_TOKEN_BALANCE_ZERO_RECONCILED`、`RAW_TOKEN_BALANCE_NONZERO_RECONCILED` 兼容保留，各钱包 `closed_token_quantities === observed_cells` 均通过校验。历史 V11–V20 未覆盖，V21 指向 16 份新证据文件及 SHA。

本轮 31 个新增原始数量闭合均在 BSC **固定区块 `0x79549a0`**：双方向 exact CA 逐页读取直到无 `pageKey`、原始事件 `uniqueId` 去重、将每笔 ERC20 原始整数 `in - out` 与同区块 `eth_call(balanceOf(wallet))` 对比。**原有 117 个组合沿用以前已验证的各自证据区块/核验路径，不能谎称全部 148 都在同一个区块重新扫描过。**

主要的高活动新样本：
- `877AF / 牛来`：124 in / 115 out，独立余额 `138878417262324072549`（原始单位）。
- `877AF / MARSCOIN`：73 in / 97 out，余额 `68700271596483656647`（原始单位）。
- `DDAC / MARSCOIN`：17 in / 23 out，余额 `3050660512775076744`（原始单位）。旧研究的前缀记录误显为 0 次流入、19 次流出；完整原始分页查明该口径不能表示真实全量，不可据旧前缀称钱包曾“凭空卖币”。
- `5C0C / BROCCOLI714`：34 in / 61 out，余额仅原始整数 `1`，应视作潜在尘埃，未经 decimals 和价格折算不计经济持仓。
- `DDAC / GIGGLE`：71 in / 0 out，证明有来源转账，但不能仅凭 71 次入账推断付费买入、账户盈利或流动性退出。

## 二、经济账本：DDAC / MARSCOIN 新的独立正负样本

钱包 `0xddac928a240bdace3994c2cc0783d4e29a002127`。从完整的 17 in / 23 out ERC20 源账本，按预先存在的时序选择前两个买入与其后对应的两笔卖出交易，查准确区块的历史 BNB 钱包余额 `block_N - block_(N-1)`、原始该钱包 external 发起交易和收款、相关回执。

**第一买卖回合（原始 token 数量全部退出）**：
- 区块 `112441920`，钱包本人原始交易 `0xfd87fa6d…b63824`，`msg.value = 0.5 BNB`；区块钱包 BNB 净流出 **0.500059367840 BNB**。
- 区块 `112442886`，钱包本人卖出相关交易 `0x8f538619…647b35c`，该笔 token 转出同时包含合约扣税/路由转移；合并两条 ERC20 out 日志的原始 token 数量与首次入账完全一致。卖出区块钱包 BNB 净增加 **0.551555614300395600 BNB**。
- **两区块 BNB 净变化 +0.051496246460395600 BNB**，对买入区块原生总支出约 **+10.30%**。该卖出区块还有另一笔钱包原始零 BNB 合约调用（回执成功，Gas **0.00000587808 BNB**），已包括于区块净变动，不得把所有区块入账单独归给卖出交易。
- 两个区块检查到该钱包原始 external 交易分别 **1 / 2 笔**，直接 native external 入账均为 **0**。大宗交易的完整回执因返回长度约 8098 字节被截断，无法独立核实所有 Gas、路由及内部转账，**因此这一正向收益仍为经签名及原生区块核对的回合现金流候选，非 verified causal realized PnL**。

**第二买卖回合（仅部分退出）**：
- 区块 `112635735`，本人再次以 `0.5 BNB` 发起买单，买入区块原生 BNB 净变化 **-0.500059380680 BNB**。
- 区块 `112639419`，第一次对应卖出消耗该次买入代币的一部分，钱包 BNB 增加 **0.491450427852877528 BNB**。这两个区块差额 **-0.008608952827122472 BNB**，但尚有当次买入数量 `103244712934056473168717` 原始单位**未在这笔卖出中退出**，加上后续还有其他转账。故该负值**不是该次完整交易的已实现亏损**，更不是整个地址的 MARSCOIN 最终盈利。
- 两个回合四个不同区块合计原生净变化约 **+0.042887293633273128 BNB**。不能直接当全仓已实现利润或全部 17/23 条日志组成的全年交易结果。

正向回合与未平的部分回合均被保留，杜绝只挑选盈利案例。

## 三、对照组与钱包优先级

| 钱包 / 代币 | 已验证的经济事实范围 | 仍不可确认的事情 |
|---|---|---|
| 8E6B / MUBARAK | 16/16 原始本人成功回执，买单 `3.333 BNB`，原生相关区块合计 `+5.299103329471661818 BNB`，16 个区块排除其他 direct external native 流入流出 | internal native trace、跨路由费率、最终交易因果 PnL |
| 8E6B / 4、GIGGLE、HAJIMI、龙虾、我踏马来了 | 六币固定交易哈希、区块 15 个两两比较无重复；有显著正向区块净变化，同时我踏马来了负向 | 真正“重复获利率”和可跟单成交、全部亏损机会资格 |
| 877AF / MARSCOIN | 前七笔本人买单、64.1% 首次部分退出的 FIFO/加权成本条件估算为正；本轮全 73/97 ERC20 库存闭合 | 其余全部交易的净回款、税费、原始信号可跟性 |
| A83B / BROCCOLI714 | 首次本人签名、token 数量配对的回合买卖相关区块约 `-0.239887492433116024 BNB` | internal trace 与后来入币资金成本 |
| DDAC / MARSCOIN | 本轮新增首次 token 完全退出的原生区块净变化 `+0.051496246460395600 BNB`，随后部分退出不能视作最终亏损 | 完整回执费项及原生内部转账、整个项目累计 PnL |

这些是**研究审计优先级**，没有任何地址在本阶段被授予 `VERIFIED_PROFITABLE_REPEATER`、`COPYABLE_TRADER` 或 `PRODUCTION_ELIGIBLE` 标签。

## 四、接下来的研发顺序

冻结 19 CA 的 transfer 和 token inventory 数据阶段现在完成，**不再用重复扫日志充当建模进度**。研究主线转向：1）将每个重大代币的原始 owner-signed 买卖和普通 transfer / protocol tax 区分；2）实际报价资产 BNB/WBNB/USDT/USDC 等的收支与 Gas、代币税、路由额外交易按独立事件对齐；3）在仍然没有完整 internal trace 的前提下保留 `CONDITIONAL` 或 `ECONOMIC_UNRESOLVED`；4）固定重大机会资格和缺席/亏损分母，判断 8E6B、877AF、DDAC、A83B、ADFF、2ADF 等钱包是否长期抓住了大机会；5）再做跟随延迟/价格/流动性回测及其他 AI review、测试和本地验收。

本轮**仅写研究 Git 文件，未修改策略、监控、交易账户或部署任何生产运行时，NO_GO**。

## 五、证据链接

- `BSC_MEME_23_EOA_19_CA_EVIDENCE_COMPLETENESS_OVERLAY_V21_2026-10-12.json`（SHA `3761b9140d0c64b1ffd8d8d243d63a2a1a4fc690`）
- `BSC_MEME_STAGE15_DDAC_MARSCOIN_FIRST_FULL_AND_SECOND_PARTIAL_NATIVE_ECONOMIC_QA_2026-10-12.json`（SHA `1eec74ae2fc7091dfb1fab0e4ab76741c0282f46`）
- `BSC_MEME_STAGE15_877AF_MARSCOIN_FULL_QUANTITY_QA_2026-10-12.json`（SHA `504cba93088c07453d79460f9a1064c32a93cea3`）
- `BSC_MEME_STAGE15_877AF_NIULAI_FULL_QUANTITY_QA_2026-10-12.json`（SHA `7254f30ecd0de523bc070d6b46f745d58f2b6f03`）
- `BSC_MEME_8E6B_SIX_MAJOR_EVENT_DISJOINT_NATIVE_SCOPE_AND_NEGATIVE_CONTROL_2026-10-12.json`（SHA `91daf8cd87297ac4f2d71be83e3ee03f761b6159`）
- `BSC_MEME_A83B_BROCCOLI714_FIRST_OWNER_ROUNDTRIP_BNB_GAS_SETTLEMENT_QA_2026-10-12.json`（SHA `54440542e014b02fb69ac3262b9258da930ed6f0`）
- `BSC_MEME_877AF_MARS_FIRST_PARTIAL_EXIT_COST_BASIS_SENSITIVITY_2026-10-12.json`（SHA `f24029e3cc935fc8190a32bf72642d463dbb428f`）

V21 `source_blobs` 还记录本轮 16 个新文件的 exact blob SHA，回合原生 BNB 核对原始数据见 `BSC_MEME_STAGE15_DDAC_MARSCOIN_FIRST_FULL_AND_SECOND_PARTIAL_NATIVE_ECONOMIC_QA_2026-10-12.json`。
