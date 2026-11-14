# BSC Meme 23 钱包经济证据横向普查：审计覆盖，不是盈利排行榜（2026-10-17）

**固定范围：23 个原冻结 EOA × 19 个原冻结 exact CA = 437 个唯一格。** 本报告对应同一 Mission Draft PR #40 研究分支，基于 [P1 原始 437 格](./bsc-meme-address-model-v1-baseline-2026-10-13.json) blob `e3c8815630878dddc03b7a6e11b8f0d2d89cbf6a`、[P2 50 个精选本人签名闭合回合](./bsc-meme-address-model-v1-p2-evidence-ledger-2026-10-13.json) blob `2a19dbd88c2971efff60a15894d952d0d05e64d9`、以及 Stage23 两重大 Meme 选定结算证据（原 SHA `6227e69fabd6c0d991add0d7ff5c6e406babd40b`）。此处**没有新的主网扫描、没有新钱包、没有后验成功样本替换**。该 50 回合是精选研究样本，不是 437 格的全部本人交易，也不是全链机会的无偏分母。

## 上轮独立审批与本轮不同

另一 AI 已在固定 `b2fb255dd486a2bd6502e21dbd14eaa6ef557c2e` 相对 `520eb0dd0851b1bb15728d4f57c50abc0917474c` **APPROVE**：审核核对 10/10 原始 Git blob、10 原交易、ADFF 原始单块 owner-out 空标准 ERC20 转出及 internal RPC 不支持、2ADF 截断、21/21 焦点测试、488/488 BSC 和两系统 CI。**这批准仅对上轮代码/来源有效**。本次新增全样本普查程序与快照需新 SHA 其他 AI 独立复审，不能把旧批准转移为自动通过，也不允许 merge/deploy。

## 经济证据分母，不能再混写成胜率

- 冻结的 **437** 钱包×CA：**148** 存在某方向 ERC20 转账，**289** 在冻结确切 CA 里无该 ERC20 转账。无转账 **不代表** 错过机会、没做其他路由、亏损。
- 在 437 格之外按 wallet×CA 关联到原始 P2 **50 个精选独立 token 库存闭合且本人签名的回合**，来自 **7 个钱包**。剩余 **16 个钱包**没有纳入这批精选经济回合，状态是 `NO_CURATED_ROUND_DOES_NOT_MEAN_NO_TRADE_OR_LOSS`，绝非 16 个失败钱包或冷钱包。
- 50 个精选回合的来源类别为 **44** `SIGNED_NATIVE_BLOCK_SCOPE`、**4** `SETTLED_NATIVE_DIRECT_WBNB_GAS`、**2** `MIXED_BNB_USDT_SPOT_REFERENCE`。方向是 **30** 原生账户选定区块净正、**18** 选定区块净负、**2** 混合报价正向参考；**这不是 30 笔可归因赚钱/18 笔亏钱/2 笔平手的实际胜率**。混合报价没有与 BNB 相加。
- 在较强的 4 个 WBNB/Gas 选定回合中，8E6B 的 **HAJIMI 首回合**、**龙虾第二回合**有两个不同 exact CA 的 2026 年正向结算选定来源；另两个是 2025 年 `4` 的正负对照，不能伪装为 2026 的正向机会。**只有 8E6B 有“本精选源内两种不同 2026 重大 CA 的已匹配 WBNB/Gas 正向回合”证据；这不是全历史可归因盈利、统计胜率、他人可跟单性或最终高手资格。**
- ADFF 原始 Dragon `msg.value=0`，原区块未发现标准 indexed ERC20 from-owner 转出，但取得代币的其他地址代付、内部路由与前期资金均未审计；`ADFF_ACQUISITION_SOURCE_AMBIGUOUS`，不能把原生余额正向视为盈利。2ADF 一笔中间退出 Withdrawal 被截断为未知，不能把未知按 0。

## 23/23 钱包对等证据表

表格「正/负/混合」**只指已经精选本人签名库存闭合回合的来源等级和选定账户区块符号**，不代表钱包总盈利、亏损或交易信号。**没有精选回合**不等于历史没有实际交易。地址完整值以 [确定性程序输出](./bsc_meme_address_model_v1_p4c_23wallet_economic_census.py) 的 `wallets` 字段及 P1 原始文件为准。

| 钱包短标识 | 已有 ERC20 CA | 精选闭合回合 | 精选正/负/混合 | 强来源等级 |
|---|---:|---:|---:|---|
| `0xa83b73…48811` | 17/19 | 4 | 0/4/0 | 未证实完整利润 |
| `0xadffbe…3946d` | 14/19 | 7 | 6/1/0 | 未证实完整利润 |
| `0x8e6b3c…e9ea0` | 13/19 | 17 | 8/7/2 | 4 个精选回合 |
| `0x2adf96…475ba` | 12/19 | 5 | 4/1/0 | 未证实完整利润 |
| `0x0abb84…f1fd8` | 10/19 | 未入精选账本 | 未审计 | 未证实完整利润 |
| `0xddac92…02127` | 6/19 | 6 | 5/1/0 | 未证实完整利润 |
| `0x877af2…1aaac` | 12/19 | 4 | 2/2/0 | 未证实完整利润 |
| `0x8d8c03…3ae25` | 6/19 | 未入精选账本 | 未审计 | 未证实完整利润 |
| `0x239e74…fb337` | 3/19 | 7 | 5/2/0 | 未证实完整利润 |
| `0x498528…bd99a` | 7/19 | 未入精选账本 | 未审计 | 未证实完整利润 |
| `0x9d1240…ca35c` | 4/19 | 未入精选账本 | 未审计 | 未证实完整利润 |
| `0x5c48a7…2387c` | 3/19 | 未入精选账本 | 未审计 | 未证实完整利润 |
| `0xcceea3…d8037` | 5/19 | 未入精选账本 | 未审计 | 未证实完整利润 |
| `0x11a732…b98d8` | 8/19 | 未入精选账本 | 未审计 | 未证实完整利润 |
| `0x5c0c5d…07583` | 7/19 | 未入精选账本 | 未审计 | 未证实完整利润 |
| `0x2b40f8…70d2b` | 5/19 | 未入精选账本 | 未审计 | 未证实完整利润 |
| `0xd70ce4…ec678` | 4/19 | 未入精选账本 | 未审计 | 未证实完整利润 |
| `0x3638cd…bc203` | 2/19 | 未入精选账本 | 未审计 | 未证实完整利润 |
| `0x4789f1…856d5` | 2/19 | 未入精选账本 | 未审计 | 未证实完整利润 |
| `0x47b871…1b429` | 2/19 | 未入精选账本 | 未审计 | 未证实完整利润 |
| `0x57c98b…0cbf4` | 2/19 | 未入精选账本 | 未审计 | 未证实完整利润 |
| `0xbeb713…e2ffc` | 2/19 | 未入精选账本 | 未审计 | 未证实完整利润 |
| `0xe54bdc…dc568` | 2/19 | 未入精选账本 | 未审计 | 未证实完整利润 |

## 实际经济模型门禁

1. **G2 覆盖**：所有原始钱包和 19 exact CA 各自保留，占满 437 格；对每个 cell 分别标识 `frozen_erc20_presence`、`original_selected_episode_count`、`selected_native_block_positive/negative`、`selected_mixed_quote_reference`、`selected_receipt_gas_scope_count`、`owner_true_all_asset_net_profit=UNRESOLVED`，不能用仅一次转账或正向块余额构建排行榜。
2. **G3 原钱包盈利筛选**：完整全资产投入、有效退出报价、税费、Gas/内部路径和同口径负样本尚未 across-23 独立审计。当前允许研究**已选证据覆盖**，不得给 23 钱包 `profit_rank`、`win_rate`、推荐买入金额或 `GO`。
3. **G4/G5 可跟单性**：市场首次可执行/首次公开可见观察点 `U=UNRESOLVED`；未完成资金容量、真实买入出场与 1/5/15 分钟不可作弊延迟的统一回测。P5 仍 `BLOCKED`。
4. **停止边界修复**：ADFF 零 owner-out 与 2ADF 截断均已经独立审核原始范围，新的 source QA 不应继续无限追同一缺口；下一主线先做固定 19 major CA **逐一可执行市场 U 的横向比较**与各 23 钱包状态，而非继续优化选中赢家的漂亮利润表。

新增[冻结样本/分母声明](./bsc-meme-address-model-v1-p4c-frozen-23wallet-economic-proof-census-scope-2026-10-17.json)、[全 23 钱包只读确定性证据汇总程序](./bsc_meme_address_model_v1_p4c_23wallet_economic_census.py)、[14 项对抗测试](./test_bsc_meme_address_model_v1_p4c_23wallet_economic_census.py)，CI 对 23、19、437、148、289、50、7、16、30、18、2、4、0 盈利排名与 U/P5/NO_GO 门禁做离线验算。**P4-B/P4-C=PARTIAL / U=UNRESOLVED / P5=BLOCKED / PRODUCTION=NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE**。
