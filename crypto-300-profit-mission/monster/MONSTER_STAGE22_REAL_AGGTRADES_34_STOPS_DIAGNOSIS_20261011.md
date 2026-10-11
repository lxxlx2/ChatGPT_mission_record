# Monster Stage22：34笔真实历史止损的官方AggTrades根因核查

日期：2026-10-11（Asia/Bangkok）。研究仍位于原 [PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)，未接入生产。

## 已完成的真实证据流程

首先复核 Stage21 十个历史日期的每个官方1m归档和77个首笔D1；其中65笔通过Stage20质量过滤，62笔6h退出有价格代理（34 STOP、8 TAKE_PROFIT、20 TIMEOUT_6H），3笔因流动性/无成交截尾。此前交易脚本和风控均无改动。

在读取新的逐笔成交之前，先提交并冻结 [Stage22研究合同](evidence/monster_stage22_aggressor_flow_stop_rootcause_prereg_20261011.json)：commit \`c6710f13a1db52de739d337a27424b53fe0dfe09\`，精确锁定之前65笔合格D1的日期/代币/首次SETUP时间，键集SHA256 \`89f62d524a23b82429ec6d19db63972766db13de82f2b6877ad99b37e1dfa3d8\`，并规定**新特征仅能使用D1确认前真实产生的交易**。不得只挑34个止损，不得按未来止损定义模型输入，不得把缺档当作主动买盘为零。

随后新增[官方Spot AggTrades根因代码](../local-agent/scripts/monster_v4_stage22_aggtrade_flow.py)、六项因果/校验测试及十日期矩阵CI。官方文档：[Binance Public Data](https://github.com/binance/binance-public-data/blob/master/README.md)。从 \`data/spot/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-{DATE}.zip\` 下载CSV与对应 \`.CHECKSUM\`，按SHA256验证，再从真实时间戳过滤SETUP前最近5/15/60分钟的成交。Binance原始字段 \`m=true\` 表示buyer is maker，即**卖方主动成交**；\`m=false\` 表示买方主动成交。量按成交价乘成交币数量换算为USDT。2025年起Spot时间戳按微秒解析后归一化为毫秒；SETUP时间及以后记录全部排除。AggTrades为聚合成交，不等于每一笔独立原始Fill，更不能还原历史L2盘口。

[真实CI #38133070166](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38133070166)：**10/10矩阵Job全部Success，6/6离线测试PASS，每一个质量合格D1都找到可校验的官方AggTrades，65/65归档验证成功、0缺失/损坏**。最初CI #38133037982 因测试将六位小数输出按七位精度检查而失败，测试修复后重跑成功，失败记录保留。十个实际ZIP及解压JSON SHA256、原始Artifact ID与分组统计保存在 [Stage22永久证据](evidence/monster_stage22_actual_official_aggtrades_65_d1_20261011.json)。复核原始ZIP和JSON后，本次统计使用的65个样本身份与Stage21一致。

## 真实结果：信号前的主动买卖方向，没有明显区分34笔止损

| D1后结果 | 原始样本 | 最近5m主动买入quote占比中位 | 最近15m主动买入quote占比中位 | 最近60m主动买入quote占比中位 | 最近15m真实quote额中位 |
|---|---:|---:|---:|---:|---:|
| STOP（实际模拟-8%风控） | 34 | 53.22% | **54.38%** | 55.30% | 197.79万USDT |
| TAKE_PROFIT（模拟+18%风控） | 8 | 53.00% | **54.95%** | 56.09% | 67.01万USDT |
| TIMEOUT_6H | 20 | 54.80% | **53.95%** | 54.66% | 123.85万USDT |
| 退出截尾，单列 | 3 | 52.75% | 48.49% | 54.80% | 14.56万USDT |

对有完整模拟退出的**34笔STOP vs 另外28笔（8TP+20TIMEOUT）**计算无需阈值的组间配对秩AUC，只是已暴露历史样本的描述性鉴别能力，不能视为预测模型样本外AUC：

| SETUP之前已经可得的指标 | 用指标数值较高识别STOP的描述性AUC |
|---|---:|
| AggTrades最近5m主动买入quote占比 | **0.4685** |
| AggTrades最近15m主动买入quote占比 | **0.5189** |
| AggTrades最近60m主动买入quote占比 | **0.5315** |
| AggTrades最近15m实际USDT成交量 | 0.6134 |
| 已有Stage20质量指标：60m币价相对BTC额外涨幅 | **0.7920** |
| 已有Stage20质量指标：币价最近60m绝对涨幅 | **0.7574** |

靠近0.5的秩AUC与随机区分相近。AggTrades的真实方向性研究**不支持**在现有65个信号中使用主动买盘比例作为直接止损过滤器；也没有观察到“止损币在D1前普遍由卖盘主导”的模式。此前以买盘强弱作为止损原因的直觉未获得数据支持。不得基于少量例外选择新方向百分比阈值。

相反，原本就有的SETUP前60m相对BTC上涨幅度，在STOP组的中位值约**15.38个百分点**，在TAKE_PROFIT组约**7.62个百分点**，在TIMEOUT组约**7.65个百分点**；组间AUC约0.7920，存在研究价值。它**依然属于原Stage21已曝光赢家/输家样本**，不是验证通过；某个研究日期有很多行情相关信号，不能把62笔视作62个独立市场阶段，无法据此断言以后涨超一定比例必然回撤。

## 下一步方案与研发闸门

- 反证方向：不针对主动买卖quote占比单独设计生产止损过滤器。它目前未显示稳定信号；65个已暴露D1的方向特征仅作为永久负面证据。
- 研究方向：固定一项**事前过度延伸风险门槛**，只对原V4 D1做买入资格过滤，**不更改原D0 WATCH或原始D1**。必须在新的未观察过的日历日期、全758币、官方连续1m、原Stage20执行模型中与完全相同的D1基准同时回测。用新日期上的交易数量、漏掉的真正赢家、真实费用情景、相同交易配对、一个30U资金槽位的盈亏决定是否有净价值；亏损仍必须按原合同保存，不得在新数据后临时挑阈值。
- 执行限制：Binance AggTrades可核实历史成交方向、成交价和量，但**不能还原真实bid/ask报价、L2档位/队列、可实际成交的卖出报价和订单撮合**。即使能看出过度拉升，价格代理结果也不能当作真实盈亏。

当前：\`STAGE22=DIAGNOSTIC_DONE\`；\`TICK_AGGRESSOR_SHARE_STANDALONE=NOT_SUPPORTED\`；\`RELATIVE_OVEREXTENSION=UNVALIDATED_HYPOTHESIS\`；\`MONSTER_DEPLOYMENT=NO_GO\`；\`INDEPENDENT_OTHER_AI_REVIEW=NOT_DONE\`；\`REAL_GMAIL=OFF\`；\`TRADING=NO_GO\`；Frank原服务不变。
