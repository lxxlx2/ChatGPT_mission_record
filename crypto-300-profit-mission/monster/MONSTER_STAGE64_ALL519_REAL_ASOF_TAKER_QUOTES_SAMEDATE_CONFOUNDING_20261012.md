# Monster Stage64：首次D0的519条真实as-of成交量/笔数/主动买入特征与同日期消除行情偏差诊断

日期：2026-10-12 Asia/Bangkok。只改原Monster PR #30。Stage64采集前已在 [预先冻结的数据研究合同](MONSTER_STAGE64_ALL519_ASOF_61M_REAL_TAKER_TRADES_PRIOR_FROZEN_PROTOCOL_20261012.md) 固定全部519条候选、时间窗及来源，禁止筛赢家调阈值。后续Stage64b仅是研究诊断，不是新交易策略验收。

## 原始真实数据、代码与CI

1. [Stage64全部519原D0信号as-of只读研究脚本](../local-agent/scripts/monster_v4_stage64_all519_first_d0_asof61m_official_taker.py) 创建commit ba4eec8d5280964936a130661c3dfa6a40337aa3。[CI #38264106669](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38264106669) SUCCESS：519/519在D0第一次WATCH **发生前**闭合的61根1m USD-M实际行情，按Binance官方日ZIP及发布者.CHECKSUM真实校验，并与原Stage52这些日源的SHA逐值核对。46条首次D0=首次P1的独立Stage56历史特征及publisher SHA收据全部完全一致。旧未来分钟污染/缺分钟自测通过。
2. [机器全519逐币as-of特征与原官方来源SHA](evidence/monster_stage64_all519_D0_asof61m_official_1m_taker_trades_SHA.jsonl) Git blob 8ebe53acfdfe10413ac1e6f03457d6ace25d9d5a；[完整分日期数据汇总](evidence/monster_stage64_all519_asof61m_quote_taker_tradecount_summary.json) Git blob e72d678e548e182c7edc8ab43191515c13b7f4ad。
3. [Stage64b不可拟合新阈值的全519分日期比较代码](../local-agent/scripts/monster_v4_stage64b_exposed519_venue_asof_within_date_rank_diagnostic.py) 创建commit b683a5a9dc3c08c111356fb225a4620a8572012d；[CI #38264631332](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38264631332) SUCCESS，使用所有519原候选的冻结blob，未来固定日历2×只是事后**评估标签**。全市场正组29、普通490，共计14,210个跨日期成对比较和2,001个同日期成对比较。所有计算值通过单元自测且Git来源锁定。
4. [Stage64b机器评分与各日期的分子/分母](evidence/monster_stage64b_all519_global_vs_within_date_asof_feature_pairwise_evaluation.json) Git blob 26de4ecd25f1c8faea700eeb84fa42acb9d6049e。

数据时钟：D0信号发生在UTC t，统计仅使用 t-61分钟close与 t-60..t-1分钟的全部已收盘行情，严格禁止把t这根尚未闭合1m当成可观察信息。没有利用事后标签选择抓取标的。

## 两类真正不同的历史事实

### 519条候选首次WATCH时实际数据

| 信号前真实字段，中位数 | 后来七日固定calendar HIGH≥2×的29条 | 其余490条 |
|---|---:|---:|
| 过去1小时收盘价涨幅 | +10.31% | +7.11% |
| 最近15分钟USD-M成交额 | 353.3万USDT | 255.5万USDT |
| 最近15分钟主动买入quote占比 | 54.65% | 52.68% |
| 最近60分钟成交笔数 | 65,624 | 47,171 |
| 最近15分钟相对于先前45分钟的成交额归一比例 | 3.795 | 3.511 |

简单的全样本中位数差距并不等于对未来的预测能力。不同交易日期的整体暴涨/暴跌、币种上市和事件环境可能同时影响所有上述指标。

### 同日期正反样本成对排序揭露的混杂

这里将一个历史2×候选的预先可见特征与另一个普通候选比较，正组特征更高算1分，相等0.5分；分数除以全部比较对数就是**历史pairwise rank concordance**（AUC-like历史排序统计），并非模型样本外ROC，也不是买入胜率。

| 信号当时指标 | 跨所有不同日期混合14,210对 | 同一日期内2,001对 |
|---|---:|---:|
| 过去60分钟涨幅 | 0.691 | **0.543** |
| 最近15分钟主动买入占比 | 0.630 | **0.512** |
| 最近15分钟成交额 | 0.540 | 0.611 |
| 最近60分钟成交笔数 | 0.566 | 0.610 |
| 最近15分钟量能归一比 | 0.514 | **0.417** |

其中“动量”和“主动买入占比”在合并日期时看似具有识别优势，但日期内区分度接近随机；不能以合并日期统计直接设动量/taker告警阈值。成交额与交易笔数日期内排序约0.61，只属于已曝光历史上的弱至中等候选线索，未来实际表现尚未验证，不能新建买入或URGENT规则。

特别提醒：六日期中，**2025-01-30**共有161个D0 WATCH，该窗口24h价格代理涨幅中位+20.57%（Stage63），但这些币D0发生前60m价格动量中位-11.75%、主动买入占比中位低于50%；说明简化的“正动量、高主动买盘才允许WATCH”可能把重要市场反弹区间的早期观察机会静默排除。本阶段不作买卖推断。

## 对正式模型研发的决策约束

1. 完整D0覆盖519个被确认有WATCH的原始币日期，Stage63首次WATCH的24h期货收盘代理中位+2.56%，但5/6日期为负；**无法证明可执行净盈利或稳定预测力**。
2. Stage64前61m原始成交特征现在519/519俱全，可以设计以各日期/同时段全市场作正常基线的绝对流动性、活跃度与相对变化评估，但**不能从这519已经曝光样本挑最优阈值**。
3. 应坚持完整全市场的原始D0 WATCH保留和即时可见；真正URGENT排序是独立层，不能让日配额被动删除首次WATCH事实；区分历史“已发出来”与“真正用户投递”，避免过期补发。
4. 下一阶段先冻结具有可证伪指标、运行成本上限、时钟/数据缺口处理、独立新历史日期的策略与技术方案，再使用**原同一生产代码重放全市场**。若新日期欠缺，拒绝把Stage64b排序数字宣传成胜率。
5. 用户Monster单笔交易金额仍未指定。历史USD-M成交额/交易笔数是期货市场事实，不能代替实时Spot/Alpha/DEX可执行盘口，收益UNKNOWN。

当前Monster阶段：Stage63完整519真实数据与旧166精确对账通过；Stage64全部519完整taker与quote来源SHA + 46独立回归通过；Stage64b分析复核通过；P1v0.3仍REJECTED；新策略独立样本外与Other AI review均NOT_DONE；Monster部署NO_GO、通知与生产自动交易保持关闭。
