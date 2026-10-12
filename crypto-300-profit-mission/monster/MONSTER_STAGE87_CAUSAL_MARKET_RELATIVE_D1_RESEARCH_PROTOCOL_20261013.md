# Monster Stage87：妖币D1自身异动与同时刻市场背景分离的只读研究协议

日期：2026-10-13 Asia/Bangkok | 原 PR #30 | `NO_NEW_SIGNAL_THRESHOLDS`。

## 为什么必须先做这一步

Stage83在6个旧窗口的519条 D0 中形成305个D1，2×提前留存27/28；注意力负载平均7.26/日、峰值52/日，原策略不合格。Stage85全部305个D1的**升级当时**量价已按Binance官方SHA校验完成。Stage86在同日期27个提前2×与277个普通未达锚点2×对照后，发现单独的60m涨幅、quote15、笔数、归一量比的宏平均AUC均接近0.5。此时在同批已曝光标签上继续提高单特征阈值属于容易过拟合的路径。

下一项唯一必要的数据补充是同一分钟的市场背景：判断D1的涨幅或放量是不是同时全市场普遍发生。**BTC和ETH仅是用来归一化目标妖币的市场参照，绝不进入Monster候选、持仓监控或新增价格提醒。** 本期只增加这两个现有官方USD-M参照，以控制开发边界。

## 先冻结的研究量（无策略阈值或赢家筛选）

- 固定人群：Stage85全部305条真实D1 Git blob `622299fec16400e189cb8fa668ecbc8bc31ec630`。保留所有519 D0在Stage83原表，正负样本只有**描述性事后分组**，禁止读取2×赢家标签来确定取数范围、参数或临界值。
- 每个D1时刻 `t` 对参考 `BTCUSDT`、`ETHUSDT` 均用Binance USD-M官方日1m ZIP及发布方 `.CHECKSUM` 取**真实已闭合** `[t-61m,t)` 61根数据；出现跨日须两天连续核验。观测时钟与目标币 D1 完全相同，不拿其它日期收盘价代替，不使用未来15分钟HIGH。
- 基准60分钟涨幅：`market_ret60 = (btc_ret60 + eth_ret60)/2`，全部按Decimal；`monster_excess_ret60 = monster_ret60 - market_ret60`。另分别保存减去BTC和减去ETH的两个相对涨幅，禁止只报告事后“最好看的一个”。
- 当下成交活跃的背景：相同两参照都用`quote15_normalized_prev45`计算 `market_quote_ratio_mean`，`monster_excess_quote_accel = monster_quote_ratio - market_quote_ratio_mean`。若任何一个行情被删失，标 `MARKET_BENCHMARK_SOURCE_UNKNOWN`，保留D1不能被计算为非2×或自动降级。
- 对 Stage86 原始明确的27个“D1至少早5分钟预测到锚点2×”和277个锚点非2×，完整保存所有原始及市场相对特征，以**同日期等权 pairwise AUC**和按日期完整AUC对照；只进行分析，绝不就此更改Stage79阈值、打开邮件或部署。
- Git结果应保存305条全量指标、BTC/ETH已验证发布者SHA列表、按旧日期统计，以及相对市场基准的6个日期内AUC及失败/源缺档。绝不能从六个已见窗口挑好日期宣称新OOS通过。

本阶段 `STAGE87=DESCRIPTIVE_ASOF_ONLY`; `OOS_NOT_DONE`; `D1_ORIGINAL_G3=REJECTED`; `REAL_NET_PROFIT_UNKNOWN`; `OTHER_AI_REVIEW_NOT_DONE`; `MONSTER_DEPLOY_NO_GO`; `GMAIL_OFF`; `AUTOTRADE_NO_GO`; `FRANK_UNCHANGED`。
