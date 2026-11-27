# BSC Meme 地址模型 V1 — P1 23 钱包跨重大机会证据基线核验（2026-10-13）

**Mode:** `RESEARCH_ONLY` / `NO_GO`; 仅研究优先队列，**绝非收益排行**。

## 0. V1 冻结输入

- 用户目标与门禁：`bsc-meme-address-model-v1-requirements-2026-10-13.md`；
- 开发和审查阶段：`bsc-meme-address-model-v1-implementation-plan-2026-10-13.md`；
- 唯一 P1 冻结输入：`BSC_MEME_23_EOA_19_CA_EVIDENCE_COMPLETENESS_OVERLAY_V21_2026-10-12.json`，Git blob **`3761b9140d0c64b1ffd8d8d243d63a2a1a4fc690`**；
- 确定性、无网读取：`bsc_meme_address_model_v1.py`；
- 单元回归：`test_bsc_meme_address_model_v1.py`；PR 只读 CI `.github/workflows/bsc-meme-address-model-v1-tests.yml`；
- P1 机器产物：`bsc-meme-address-model-v1-baseline-2026-10-13.json`。

## 1. 全部 23 钱包的同口径证据初始对照

P1 强制验证：**23 钱包 ×19 exact CA =437 cells，其中 148 存在转账，289 不存在正值转账**。最初冻结的四个 **2026 年重大 Meme 优先线索**为「我踏马来了、龙虾、牛来、MARSCOIN」。**后续新增重大币需要单独 V1.1 版本并在读取回报前冻结**，以免事后更改机会池。

以下是 **按 2026 年这四币是否有 ERC20 Transfer、其次按其它 19 币转账广度排序的研究核查顺序**。*只表明哪些地址更值得优先查原签名和回款，不说明活跃盈利、选币能力或最近30天交易*。

| 研究检查顺序 | 原地址 | 2026 四币有转账 | 19 币有转账 | 本人签名买卖 | 可归因真实 PnL | 最近 30 天真实 Swap |
|---:|---|---:|---:|---|---|---|
| 1 | `0xa83b73f5644cde337b61da79589f10ea15548811` | 4/4 | 17/19 | 未确认 | 未确认 | 未确认 |
| 2 | `0xadffbebbd2d9141cff80f8a905846ba8f9e3946d` | 4/4 | 14/19 | 未确认 | 未确认 | 未确认 |
| 3 | `0x8e6b3c9c72ca592bbab470f761fa869c174e9ea0` | 4/4 | 13/19 | 未确认 | 未确认 | 未确认 |
| 4 | `0x2adf961b40951736bcff3b36b7fb1cd5775475ba` | 4/4 | 12/19 | 未确认 | 未确认 | 未确认 |
| 5 | `0x0abb84c976d07b97c1e23b7bfa88bc1f3d9f1fd8` | 4/4 | 10/19 | 未确认 | 未确认 | 未确认 |
| 6 | `0xddac928a240bdace3994c2cc0783d4e29a002127` | 4/4 | 6/19 | 未确认 | 未确认 | 未确认 |
| 7 | `0x877af245c61289b24f0c619a4346cdbc68f1aaac` | 3/4 | 12/19 | 未确认 | 未确认 | 未确认 |
| 8 | `0x8d8c031fd095b15f6e7ce1b27c1318015723ae25` | 3/4 | 6/19 | 未确认 | 未确认 | 未确认 |
| 9 | `0x239e74bfbd02d71cdc70fecc2d505dc13acfb337` | 3/4 | 3/19 | 未确认 | 未确认 | 未确认 |
| 10 | `0x498528e32b04bdaa73d5c8943a09aeffd15bd99a` | 2/4 | 7/19 | 未确认 | 未确认 | 未确认 |
| 11 | `0x9d1240b262d91ec3a4ea24bfec5e3b21c2eca35c` | 2/4 | 4/19 | 未确认 | 未确认 | 未确认 |
| 12 | `0x5c48a7c2113aa044d9c1381588b9c7b3c352387c` | 2/4 | 3/19 | 未确认 | 未确认 | 未确认 |
| 13 | `0xcceea39c8a5b5306a4eabaaca82a2777a39d8037` | 1/4 | 5/19 | 未确认 | 未确认 | 未确认 |
| 14 | `0x11a7327957ed5d370d2e009ec250ab0da2ab98d8` | 0/4 | 8/19 | 未确认 | 未确认 | 未确认 |
| 15 | `0x5c0c5d788661dde7437842fb7f0bbff7f1607583` | 0/4 | 7/19 | 未确认 | 未确认 | 未确认 |
| 16 | `0x2b40f892a5b8aefdf9868317330ca0f956f70d2b` | 0/4 | 5/19 | 未确认 | 未确认 | 未确认 |
| 17 | `0xd70ce47ec32625420640da206f0b3525c2bec678` | 0/4 | 4/19 | 未确认 | 未确认 | 未确认 |
| 18 | `0x3638cd44e7d8449a1adfc423cbc39e06942bc203` | 0/4 | 2/19 | 未确认 | 未确认 | 未确认 |
| 19 | `0x4789f192df5deb559af2bd9185781fda995856d5` | 0/4 | 2/19 | 未确认 | 未确认 | 未确认 |
| 20 | `0x47b87148e6ddff25fe765a0ac23aaa4c19f1b429` | 0/4 | 2/19 | 未确认 | 未确认 | 未确认 |
| 21 | `0x57c98bc732f0e9ed7156d21f74c17bee4bb0cbf4` | 0/4 | 2/19 | 未确认 | 未确认 | 未确认 |
| 22 | `0xbeb713cced9ef608cd349cc14971c32d4e6e2ffc` | 0/4 | 2/19 | 未确认 | 未确认 | 未确认 |
| 23 | `0xe54bdcaff91ed27e53a19bb1203b10bc5e2dc568` | 0/4 | 2/19 | 未确认 | 未确认 | 未确认 |

**重要发现：** 不只 8E6B，`A83B`、`ADFF`、`2ADF`、`0ABB`、`DDAC` 均覆盖这四个 CA 的正值转账；其中 `A83B` 的 19 CA 转账广度 **17/19**，`ADFF` 为 **14/19**，`8E6B` 为 **13/19**。这证实 P2 需要先做同口径跨钱包比较，不能默认 8E6B 排第 1。

这些地址可能包含空投、朋友转币、跨合约被动收益或损失；此表**不是**前排盈利地址清单。拥有这四币中的 4/4 ERC20 Transfer **绝不等于 4/4 主动买入、更不等于 4/4 赚钱**。

## 2. 独立发现的 V21 来源例外：8 个“有转账但完整笔数字段为 null”

模型首次校验读取时发现，**8E6B** 的 MUBARAK、SIREN、BULLA、4、GIGGLE、我踏马来了、龙虾、HAJIMI **共 8 个已分类 COMPLETE_OBSERVED 单元**，其旧 V21 汇总对象的 `complete_in_events` 和 `complete_out_events` 均为 `null`。

这不改变 V21 的 437 个游标完成与 148 个正值转账数量核对**总体声明**，但**不能从 V21 汇总对象取得这 8 个单元的最终进出笔数**。重要的是其 `original_in/out_events` 是旧阶段计数，可能小于真实最终补齐数量：例如后来审计的 8E6B/4 为 **2 入17 出**，而旧汇总包含 **2 入5 出**；GIGGLE 为 **4 入23 条转出日志**，旧汇总 **4 入15 出**。

V1 模型处理方式：
- `ERC20_presence=PRESENT`，仍按照冻结全覆盖结论；
- `complete_in_events=null`，`complete_out_events=null`，`complete_event_count_state=PRESENT_WITH_NULL_COMPLETE_COUNTS_IN_V21_OVERLAY`；
- **不填零、不使用旧 original_* 采样数、不伪造完整交易笔数**；
- 后续 P2 必须逐项从对应已存在的完整原始交易来源映射真实数量，不修改 V21 历史报告，不重新扫 437 个组合。

这一例外会在 CI 中作为**预期的、必须明确显示的来源事实**进行检查。它不是交易失败，也不是全量来源已经丢失。

## 3. P1 的接受结果与局限

P1 机器输出的所有 437 单元：
- `ERC20_presence` 可判定；
- `owner_signed_buy_state`、`owner_signed_sell_state`、`realized_cashflow_and_profit`、`major_opportunity_eligible_miss`、`followability` **全部 UNRESOLVED**；
- 23 钱包的 `last_confirmed_true_swap_UTC` / `profit_rank` 全为 null；
- `recent_30d_activity_state=UNRESOLVED`，绝不以没有最近数据替代确证不活跃；
- `RESEARCH_PRIORITY_ONLY` 是输入核查次序，不是交易资格判定。

G1/G2 **结构化输入已建立**，G2 的经济证据丰富度尚未完成；原有 Stage16–26 的经审核 PnL 目前**未批量灌入**模型（即 P1 未载入已核经济结果，不意味着 0 个真实赚钱案例）。

## 4. 下一步 P2 必须补齐的三类主线

1. **全 23 钱包经济证据对齐**：按统一 quote/profit tier（真实可归因、混合资产、原生区块账户变化、未知）对照，必须保留亏损。逐个使用已存 Stage16–26 数据，不重复原始转账分页。
2. **2026 年真实主动交易**：先拿 P1 前列钱包的「牛来、MARSCOIN、龙虾、我踏马来了」原始签名、实际入场/退出；检查最近30天完整真实签名（不是 BNB 钱包在动）。
3. **冻结后可执行回测**：延迟 **1/5/15 分钟**、真实池/手续费/税费/失败和不可买、本人下单后才可见信号；严禁把旧 V0/V1 事后价格模拟升级为合格跟单收益。

所有结论还需**其他 AI 独立 Review**、单元/CI 验收后才能考虑只读本地运行；生产 `NO_GO`。
