# Monster Stage127：首次 D0 时间前推优先级模型，一次性冻结方案

状态：`PRE_REGISTERED_BEFORE_MODEL_CALCULATION`，2026-10-14 Asia/Bangkok。原 [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)。研究工作，不调用新的自动采集、通知、订单、Mac 任务或生产 Frank。原 Stage118 18/28、Stage100、Stage111、Stage117 否决结论均不修改。

## 业务假设与显式失败条件

原 Stage118 需绝对 quote15 / trades15 和 ret60 硬阈值，在已曝光 519 D0 上只保留 18/28 个历史重大早报。Stage92 原 Stage79 D1 虽在已 WATCH 子样本有 27/28 早报，但 305/42 天平均 7.26，单日峰值 52，违反通知注意力负担。尝试**不硬过滤普通 D0**的顺序型早期优先级模型：只从第一次 D0 当时已闭合的过去 61 分钟价格和成交构造统计分数，依靠过去日期自动学习，而不用固定 ≥8% 的先涨确认门槛。所有原 D0 519 保留，不在高分之外删除 WATCH；分数只能形成 `RESEARCH_D1_PRIORITY`，永远不代表 `BUY` 或可以发送 Gmail。

**唯一候选**：六特征 L2 正则 logistic 回归，固定全批次算法和训练日期前推口径。若旧日期无 >=6 个真实早5分钟机会则不训练，在前瞻评分上记 `WARMUP_NO_MODEL`，不将未来日期标签回流到本折训练。使用更晚暴露历史窗口进行 walk-forward 诊断，但这些窗口**早被其他 Monster Stage 用过，绝不是新的 OOS**。

历史研究门槛：
- 有效训练折日期严格早于评估折日期，至少 6 个已知训练正样本、至少 30 个训练事件及至少 10 个训练负样本。
- 已曝光研究折（实际能打分的窗口）重要 D0 >=5m 早于 2x 的机会，需要入选率 >=80%；与既定 G3 一致，所有评估日期完整 7天 UTC06 桶平均升优先级 <=5/天、峰值 <=12/天。不能把前面 `WARMUP` 没有打分的日期算作模型通过；每个窗口分别报告和统计因训练不够未能服务的早报机会。
- 只要实际早5分钟保留 <80% 或负载超标，模型记 `REJECTED_EXPOSED_HISTORICAL`；历史折过线也只能 `HISTORICAL_DIAGNOSTIC_NOT_OOS`，G0–G6 仍不可放行。模型不准依据观察到的错币/收益结果改特征、日期、系数正则、阈值或折划分后称同一候选成功。

## 原始可信历史输入，全部币保留

- `monster/evidence/monster_stage64_all519_D0_asof61m_official_1m_taker_trades_SHA.jsonl`，Git blob `8ebe53acfdfe10413ac1e6f03457d6ace25d9d5a`；全 519 已有 Binance 官方一分钟来源/发布者 SHA 审计、首次 D0 UTC 当时可见已闭合 61m 特征。
- `monster/evidence/monster_stage83_all519_source_and_D1_result.jsonl`，Git blob `c76b3a137c8dbe56feed3a79a63adcc0752f5e2e`；按 `(date,symbol)` 完整 519 严格一对一匹配，唯一标签 `D0_at_least_5m_before_2x` 为旧已曝**事后评价**，不能作为输入特征。完整 6 个锚点按时间排序：2025-01-30、2025-06-02、2025-08-01、2025-10-02、2026-06-21、2026-07-28，样本分别 161、34、54、75、100、95，旧评估早报机会 0、0、6、13、2、7（总 28）。完整未来全市场 `no WATCH` 的赢家分母缺失，因而仅报告 **原519已WATCH的条件优先保留率**，不当作全币 2x 召回。

## 唯一冻结特征/数学/日期规则

使用 Stage64 `features_ASOF_ONLY`，严格禁止 `post_D0_24h_close_return_pct_EVALUATION_ONLY`、`original_7day_calendar_2x_EVALUATION_ONLY`、Stage83 未来标签及 `D1_FIRST_UTC` 进入模型特征：
1. `ret60_pct / 20`（保留符号）；2. `log1p(max(quote15_USDT,0))`；3. `log1p(max(trade_count15,0))`；4. `log1p(max(quote15_normalized_prev45,0))`；5. `taker_buy_share15`；6. `taker_buy_share15-taker_buy_share60`。
各字段要求数值有限且原始业务定义有效，失败则 `SOURCE_UNSCORABLE` 并保留原 D0。只使用该折训练旧日期计算每维均值和总体标准差（小于 1e-9 则取1）；标准化后的每维截断到 [-6,6]。训练时当时已知的历史标签为 `D0_at_least_5m_before_2x`，只进训练目标。
- 标准二分类 logistic，初始化所有权重=0，偏置 `log((positive+1)/(negative+1))`，全量 batch GD 固定 400 轮、学习率 0.2，特征权重 L2 梯度 `0.05*w`，偏置不惩罚。无任何测试日期参与归一化或训练。
- 使用旧训练集每条事件的拟合分数选择一个**固定的历史负载阈值**：对旧训练集中分数的所有唯一阈值候选，从最宽松到最严格递增，取第一个严格 `score > threshold` 使得旧训练完整 7日 UTC06 天桶 `平均 <=5/天且峰值 <=12/天`；若没有则 `NO_VALID_CALIBRATION`。这属于旧训练样本负载校准，可发生乐观偏差，不能拿历史训练达标冒充测试负载达标。无每日 top N 截断或排队丢弃。
- 每个被评价的新历史锚点只用其**之前所有完整旧锚点**训练；完整7日锚点运行，而非随机 train_test_split。已曝光原 D0 记录本身可能晚于锚点开始，仍属于该锚点整体测试，禁止共享标签。每个 7日小时桶起始 `anchor UTC06:00`，每日一桶，所有 7 天计入含零信号桶。
- 记录全部 519 行 `venue-symbol-anchor`、有效/无模型/缺证据、固定阈值、预测 score、是否研究优先、原历史 2x 标签仅用于评价。若历史窗口无训练模型，输出 `WARMUP_NO_MODEL`，不把未观测涨幅当负收益。
- 报告每个窗口、全体、有模型窗口的样本总量、历史正例、早报保留、平均/峰值真实负担，并保留每个漏掉的历史标的。不得选替代阈值、换赢家或挑对自己有利的日期。

## 工程与放行

纯离线 Python 无外部模型包、无网络调用；Source Git blob 哈希校验（CI 用 `git hash-object`），固定 Python 单元测试及 Ubuntu/macOS 对真实519双源回放，完整机器逐事件和汇总留档 Git/CI。仅对历史已曝光群体给出 `REJECTED` 或 `HISTORICAL_DIAGNOSTIC`。独立其他AI Review必须另行完成；真正新 OOS 仍需官方全市场 source-authenticated 新完整窗口。不会影响 Stage99 三个已停止的 Mac 任务、Spot、Frank、真实 Gmail 或实盘。

`STAGE127_STRATEGY=FROZEN_BEFORE_REPLAY`; `OLD_EXPOSED=519`; `UNSEEN_OOS=NOT_DONE`; `G0=PARTIAL`; `G4=UNKNOWN`; `INDEPENDENT_OTHER_AI_REVIEW=NOT_DONE`; `MONSTER_DEPLOY=NO_GO`.
