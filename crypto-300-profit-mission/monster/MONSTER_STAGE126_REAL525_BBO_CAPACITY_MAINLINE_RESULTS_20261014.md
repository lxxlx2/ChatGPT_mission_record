# Monster Stage126：原始525全市场真实 BBO 容量与执行证据缺口，历史模型保持 NO_GO

日期：2026-10-14 Asia/Bangkok。原 [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。研究数据时间 **2026-10-14T09:48:24.840Z**（Stage123 旧有归档），**不是本报告提交时新的当前行情**。本次无新公开 Binance 采集、无定时任务、无交易、无 Mac 部署、无 Gmail、Frank 未改。

## A. 本轮的先后证据

1. 冻结规则：[Stage126 先验容量分析协议](MONSTER_STAGE126_FROZEN_FULL525_ASOF_BBO_DISPLAYED_CAPACITY_PROTOCOL_20261014.md)，在计算前提交 Git SHA `f608882b2efcca04604f3b4516b4109041df4578`。
2. 原始数据：此前 Git 中 [Stage123 八源清单](evidence/monster_stage123_20261014T094824Z_manifest.json)，全部 5 个 exchangeInfo 分片以及 ticker、best bid/ask、mark 文件；阶段 Stage124 `load()` 再核 927 全部市场条目和 525 个 TRADING+PERPETUAL+USDT 合约，完整币种和 Unicode 不删除。
3. 本轮已提交离线纯程序 `../local-agent/scripts/monster_v4_stage126_full_market_bbo_capacity.py`，包含原始同 symbol 的买一卖一价格数量、同时可见的较小双边量、价差、时钟和删失状态；没有固定交易金额、没有盈利筛币门槛、更没有 D1 新权重。
4. 七项专用回归测试及原始八源实际加载测试均已实现。`2026-10-14` 首次 [CI #38554847452](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38554847452) 为 **FAILURE**：人工合成 stale 时间例子写成了负 epoch，程序正确地将其分类为 `INVALID_BBO_TIME`，测试错误地预期 stale。修改测试成 **正 epoch 且 >60s** 的真实可表达场景，未调整盘口经济公式、源数据、阈值或原模型；修复 commit `3b840dd2137848bc9a30396a215d28e0aab19324`。
5. 修复后真实 [CI #38554960854](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38554960854) **SUCCESS**：Ubuntu job `115821703000`、macOS job `115821702452` 均完成 Python 7 测试、全量 927/525 源读回和完整机器结果上传。两个 OS stdout JSON 的所有指标经独立逐字段字符串比对 **完全一致**，并将永久汇总写到 [实际525源结果 JSON](evidence/monster_stage126_20261014T094824Z_actual_full525_bbo_capacity_summary.json)。完整 525 行 JSON 也作为两个 CI artifact 保存（GitHub Actions artifact 有保留期，可随时从 Git 原始八源通过代码重现）。

## B. 525 全市场实际盘口统计（Binance 结构化连接器已存档源）

| 全市场源统计 / 容量分布 | 实际结果 |
| --- | ---: |
| 所有合约 exchangeInfo | 927 |
| 活跃 USD-M USDT 永续固定分母 | 525 |
| 本次有新鲜、两边均为正量的 BBO | **525 / 525** |
| 其他 source missing / stale / invalid / zero qty | **0**（仅此批） |
| 买一卖一价差，bps 中位 / p25 / p75 | **3.864734 / 2.001641 / 5.947071** |
| 买一显示挂单 quote 名义金额代理，中位 | **103.6689300 USDT** |
| 卖一显示挂单 quote 名义金额代理，中位 | **197.7544800 USDT** |
| 双边共同数量按卖一价换算的 quote 容量代理，p25 | **22.2940200 USDT** |
| 双边共同容量，中位 | **67.0187700 USDT** |
| 双边共同容量，p75 / p90 | **197.2525700 / 668.3234820 USDT** |
| 当时已发生的过去24h涨幅 ≥10% 的币 | **9**；其双边共同容量中位 **89.7385800 USDT** |
| 当时已发生的过去24h跌幅 ≤-10% 的币 | **13**；其双边共同容量中位 **57.63350400 USDT** |
| 其余原始市场合约 | **503**；容量中位 **67.0187700 USDT** |

计算公式：`two_sided_common_contract_qty=min(bidQty,askQty)`；`visible_roundtrip_buy_quote_ceiling=askPrice*two_sided_common_contract_qty`。此值对应**在同一瞬时 L1 报价下同时有显示挂量的最大共同数量报价代理**。其币种是否与 Spot 的原生 token 相同、是否存在非一倍合约单位、是否可以用真实市场委托吃到这档、是否还存在第二档、交易费用以及退出时盘口均未证明。若瞬间挂单撤单，连这一档也不能按该价保证成交。

核心业务结论：**即使前24h成交额巨大，在单一观察时刻买一或卖一仍可能很薄；滚动成交额不能代替当前可见双边深度，更不能代替信号后入场和退出的实际净收益。** 当前 525 个合约的 L1 名义容量 p50 只有约 67.02 USDT，分析对象仅为本批交易所 USD-M 合约，不能外推全球市场或任意时刻的深度。此报告不据此创建仓位默认金额，也不临时筛掉这些合约。

## C. 与原目标的关系和下一主线

- 真实源：Stage123 八份源和完整 symbol 统计复算成功，但连接器提供结构化数据，尚未取得原 Stage97 成对 HTTPS 原始字节证明；BBO、ticker 和 mark 亦非同一原子时间。报告不能补认原 2026-10-14 06:00 UTC 已失败的 Stage99 窗口。
- 历史策略：Stage118 在已曝光 519 D0 中仅早期保留 18/28 个重要2×，`REJECTED`。本轮**没有**将已见的九个涨≥10%合约选作新策略验证成功，也没有更动历史 D0/D1 判定。
- G0：当前 USD-M BBO 合约源可以对账，但币种发行资产身份、Spot/合约单位及 D0/D1 的真实时点交易资格仍为 `PARTIAL`；Stage125 同名现货映射只有结构化候选，不能当作资产层真实对应关系。
- G4：需要 **当时 D0 的真实多档深度、有效报价数量单位、明确用户交易金额、双边适用费率、后续退出真实报价与成交** 才能算可执行净值。525 个纯 L1 快照有效 ≠ 至少30个双边入场/退出成交；`G4=UNKNOWN`。
- G1/G2/G3：没有未经曝光的完整 7 日独立 forward 时间路径，不能从 24h 过去涨幅或单张 BBO 推断早期发现率。下一阶段应沿着 **完整 D0/D1 全市场时间线与实际 D2 同时点证据的连接** 继续，不继续在暴露 519 上调阈值；手动新批次仍由用户主动发消息触发。
- 仍需真正其他 AI 独立 Review、失败修复与复验、完整源验证，并在全部关口通过后另行申请 Mac 隔离部署授权。

`STAGE126_SOURCE_FULL_MARKET=DONE`; `STAGE126_CODE_AND_7_TESTS=DONE`; `STAGE126_UBUNTU_MACOS_REAL525=PASS`; `STAGE126_MACHINE_SUMMARY_SAVED_GIT=DONE`; `STAGE118_MODEL=REJECTED`; `G0=PARTIAL`; `G1_G2_G3=NOT_SCORABLE_NEW_OOS`; `G4=UNKNOWN`; `INDEPENDENT_OTHER_AI_REVIEW=NOT_DONE`; `MONSTER_DEPLOYMENT=NO_GO`; `PRODUCTION_TRADING=NO_GO`; `GMAIL=OFF`; `FRANK=UNCHANGED`; `NO_NEW_SCHEDULES`.
