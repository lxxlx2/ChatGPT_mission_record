# Monster Stage48 — 全市场936条原D0 WATCH真实闭合分钟量价、首次/重复事件对照

日期：2026-10-12（Asia/Bangkok）；唯一[Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。严格遵守[模块规则](MONSTER_MODULE_DEVELOPMENT_RULES.md)：此阶段仅事实分析，不训练/优化新P1，不回写原V4、Frank、Gmail或Mac，不模拟可成交利润。

## 冻结原输入和真实来源

- 在取回本轮官方行情以前，先提交[Stage48固定437币日期、936条原始WATCH的事实分析协议](evidence/monster_stage48_all437_watch_minute_feature_observations_prereg_20261012.json)，commit `52226bf4361eb2857a7dcb83c86207d8a6d48191`。原冻结数据必须是[Stage45的全部5400币日期真实原V4回放结果](evidence/monster_stage45_blind_all5400_originalV4_P1v02_cases.jsonl) Git blob `fbc8eb844d3b34c0532f2da4d4bdfad30d84f214`。不得只挑未来2×赢家，未触发WATCH或源缺币日期也必须保留完整身份与分母。
- [Stage48事件来源代码](../local-agent/scripts/monster_v4_stage48_all437_asof_second_watch_features.py)对六日期各900冻结USD-M历史符号共5400币日期，实际只为**437个有原始WATCH的完整币日期**重新读取需要的Binance官方日度1m ZIP及`.CHECKSUM`，源SHA必须与Stage45保留的官方原发布者SHA**逐日字节对齐**。每次观察时间t只读取开盘UTC `t-61min…t-1min` 的61根连续、已经闭合的真1m K线；不得从t以后拿价格或quote。成交额来自官方K线quoteVolume、成交数来自num_trades；60m涨幅、15m成交额、先前45m成交额及三倍相对比皆为as-of特征。
- [真实Stage48全部原源36个分片CI #38216755205](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38216755205) **36/36 SUCCESS**。
- [Stage48独立下载全部36份原Artifact ZIP重新算SHA、与Stage45第一次P1v0.2原60m回报+两段quote输入完全一致、与Stage47第二次提前越线计数一致CI #38217076927](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38217076927) **SUCCESS**。所有聚合器源码：[36源SHA复核与全市场量价分组](../local-agent/scripts/monster_v4_stage48_original36_shas_936_asof_features_aggregate.py)。
- 长期Git原始事实：[36源SHA、全部分组统计与BULLA逐时刻量价](evidence/monster_stage48_original36_SHA_all936_true_asof_minute_features_summary.json)、[所有936条实际WATCH的量价与后来越线时间的事后组标签](evidence/monster_stage48_full936_real_closed1m_original_D0_event_features.jsonl)、[所有5400币日期状态/437有WATCH真实SHA回执](evidence/monster_stage48_all5400_source_and_437_watch_case_inventory.jsonl)。聚合Artifact ID `11732544493`，ZIP SHA256 `24cd757b82c76727d9520b38f6e38f50e83ad8f0353a70bee5da39c4ccf605f2`。

## 事实：首次WATCH无法靠「放量速度」简单区分赢家

| as-of指标中位数 | 真正未来2×的首次早报40条 | 事后未达到固定窗口2×的首次WATCH 397条 |
|---|---:|---:|
| 首次D0时最近60m已闭合K线价格涨幅 | +11.0727% | +9.1903% |
| 首次D0时最近15m官方quote成交额 | 2,627,119 USDT | 1,622,985 USDT |
| 首次D0时近15m相对先前45m的标准化成交额加速比 | **6.109×** | **7.350×** |
| 首次D0时最近15m真实成交笔数 | 26,722.5 | 17,536 |

这说明赢家样本**当前绝对成交量更高，但两组首次量加速都很强，赢家的相对加速中位数反而更低**。因此单看第一次WATCH的quote加速比，不能将未来两倍与普通波动干净分开；Stage45的P1v0.2升级359、普通未2×高达323一事有数据层面解释。因同名symbol跨日期、市场背景、固定窗口2×标签及因果回看方式限制，不能将上述中位数直接当盈利预测阈值。

## 事实：二次及后续WATCH量价和上涨持续性更有区分空间

| 特征中位数 | 2×首次真正越线之前的重复WATCH **56条事件** | 普通未2×币日期的重复WATCH **310条事件** |
|---|---:|---:|
| 最近60m闭合K线回报 | +10.2933% | +7.1070% |
| 最近15m官方quote成交额 | 5,342,212 USDT | 2,362,746 USDT |
| 15m相对先前45m成交额比 | 3.206× | 3.167× |
| 当前价相比第一次WATCH时最后已闭合价 | **+22.2396%** | **−1.0266%** |
| 与上一次D0 WATCH间隔 | 979.5分钟 | 1015.5分钟 |
| 最近15m成交笔数 | 47,482.5 | 33,679.5 |

**重要分母：** 56是31个未来2×币日期在真2×前再次报警的所有重复事件，不是56种独立币；310是138个非2×币日期的重复事件。两组事件数/次数权重不同，且普通组观察全部168h而赢家组只截真2×首次之前，因此它们只能支持二次点火特征方向，**不能把中位数差异当新模型Precision或盈利率**。所有2×越线后追加的133条重复WATCH单列 `2X_REPEAT_AFTER_OR_AT_2X`，不得冒充有效提前发现。

## BULLA 10×实际时间与as-of真实价格条件

- [完整源SHA机器行](evidence/monster_stage48_original36_SHA_all936_true_asof_minute_features_summary.json)已复核：2026-01-28 11:33 UTC第一次D0 WATCH时，60m闭合涨幅 `2.1597633%`、最近15m quote `272,526.72 U`、最后闭合价 `0.0345300`，未满足已弃用P1v0.2。
- 2026-01-29 **05:42 UTC**，距真第一次2×分钟HIGH仍早**137分钟**，第二次真实原D0 WATCH时60m闭合涨幅 `41.5071770%`、最近15m quote `2,418,786.71 U`、quote相对先前45m归一比 `71.0944×`、最后闭合价 `0.0473200`，相对首次WATCH时高 **37.04%**。
- 这仅证明**同一原D0币可以在首次WATCH没满足优先条件后，真实生成可重评的新观察时刻**。不能根据已知道BULLA最后10×而声称设置某阈值即能赚钱。并非所有2×币都能在翻倍前给第二次早报。

## 按长期规则推进下一步

1. 将第一次D0的RAW观察完整持久化，**不删、不延迟**。研究额外的**持续观察/再点火状态**：每次已闭合真实行情的更新可重新评价（并非只在第一条D0判断一次），但URGENT通知必须有真实时效与拥挤容量，不得把全部936原D0事件发成急件。当前没有合格新P1。
2. **先验冻结下一候选及其未使用日期，再读新行情**。新规则应在历史全市场正常币与暴涨币中同时检验至少5分钟提前机会保留、全部5×/10×漏失、全天最大事件拥挤、成本、当时合约交易资格；不得因为BULLA第二次涨41.5%而直接把阈值定成针对它。
3. 真正币安期货原生产同源回放仍是**研究发现层**。历史真实订单簿/价差/滑点、已退市/合约乘数/RWA、全币共享D1队列、未来新品种、新日期、独立其他AI Review和Frank隔离Mac测试都没完成。因此`EXECUTABLE_PROFIT=UNVERIFIED`、`RESEARCH_NEW_PRIORITY=NOT_VALIDATED`、`MONSTER_DEPLOYMENT=NO_GO`、`FRANK=UNCHANGED`、`GMAIL=OFF`、`AUTO_TRADE=NO_GO`。
