# Monster Stage5: first-WATCH 前态特征复核（预定研究规则）

Date: 2026-10-10. Status: EXPOSED_HISTORICAL_DIAGNOSTIC_ONLY.

## 为什么进行此项复核

Stage3 的30条普通强信号 +30条已知历史5x预命中强信号已经固定，不再挑例子、不再按未来的回报来筛选样本。本批研究直接调用 Binance 官方历史 1h OHLCV，检验首次 WATCH 之前24个已经完成的1h价格/成交路径在两个群体中是否有差异。此处不得把已知上涨赢家的差异误写成能预测下一批赢家，也不得拿它替代尚未进行的 1m–5m early forward study。

## 锁定的样本与输入

- 来源：evidence/monster_stage3_combined_60case_360_scenario_20261010.csv，固定取 model=NOW 共60行，每个 cohort 各30行；不能按研究结果剔除“难看”案例。
- Binance 官方对应 venue 的 1h Kline：startTime=watch_utc-24h，endTime=watch_utc-1ms（不含 watch 之后的任何行情），应有连续24根已闭合 K 线。BTCUSDT 使用**同 venue / 同时间段**，仅用于相对收益。
- 对退市、缺档、交易量为零、请求失败或原数据不满足24根连贯性，记录异常状态，不填零、不借未来数据补齐。
- 已知 ALPACA 零成交的24h实际退出属于 CENSORED，仍保留样本但不算可执行结果；BABY/BIFI等单根极端 high 不应视为可交易 5x。

## 事先定义的同刻可观测指标

1. ret1_pct：最新已完成1h close / 上一小时 close - 1。
2. ret4_pct：最新已完成1h close / 4小时前 close - 1。
3. btc_ret1_pct、btc_ret4_pct：同venue BTC对应指标；relative1_pct、relative4_pct 是两者百分点差。
4. quote_last_hour_usdt：最后完成小时的 quote turnover；vol_ratio_prev23 为最后1h quote / 先前23小时非零 quote 中位数。
5. quote_last4_share_pct：最后4个小时 quote 总量在24小时内占比，不得说成未来成交量。
6. positive_steps_last4：最近四次小时 close > 上小时 close 的计数。
7. breakout_prev23_pct：最后小时 close / 前23小时 high 最大值 - 1。
8. upper_wick_range_pct：最后小时的 (high-close)/(high-low)，分母为0则标 unknown。

不通过事后 GT 标签构造上述特征；outcome/proxy、known_gt_maxhigh/maxclose 只在分析阶段使用，不得进入实时排序逻辑。

## 预定比较与审查

对所有有效行以及独立 spot/futures 分别统计：样本覆盖率、中位数、四分位/尾部分布、量能变化、相对BTC、强连续性和近期波动结构；对异常小时及可能的历史合约/杠杆产品单独标记。观察结果只决定哪些候选特征进入未来评估，不从这60个已曝光事件中选定盈利阈值。30条普通样本有分组抽样设计，不能当成总体无偏负例，不能计算“V4胜率”。

允许逐批写同一 CSV 并在 Git 里保留批次提交；输出必须包含成功及失败逐事件记录、时间窗、数据源、失效原因；对异常不做静默删除。

## 生产边界

Frank 不动，Monster 不安装、不创建 Gmail/automation、不进行交易；Shadow = DRY_RUN_ONLY，真实通知时效和实际可执行收益仍 UNKNOWN。
