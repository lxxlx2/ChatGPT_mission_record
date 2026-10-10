# Monster Stage 3 — 5m 回踩确认研究协议（取扩展5m结果之前固定，2026-10-10）

**仅作探索性历史压力测试。无策略批准、无生产、无自动交易。本协议在读取本轮 30h K 线后不再按结果改变条件。**

## 固定样本

使用上一轮已经保存的 [30个事件与触发 UTC](evidence/monster_stage2_binance_5m_30case_deterministic_20261010.csv)，分三组各10个 `breakout_only`、`triple`、`new_listing_proxy`；有重复经济实体（如 WCT Spot/Futures），不能当完全独立抽样；样本按先前固定哈希而非未来回报选取。时间均为前一根完整 1h K 线刚完成的 `signal_utc`。

取官方 Binance Spot / USD-M 5m K 线，时段 `[signal_utc, signal_utc+30h)` 360根；所有历史 5m OHLCV 均为事后收集，但每个模拟条件只能读取当刻已完成的 5m K 线。

## 固定比较规则

- `NOW`：`signal_utc` 首根5m open 入场，观察未来4h与24h真实 K 线收盘的价格比；零通知延迟且无手续费/滑点，仅为参照。
- `WAIT30` / `WAIT60`：固定延迟30/60分钟后首根5m open 入场；不使用未来价格做择时；也独立报告可能错过的涨幅。
- `PB03` / `PB05` / `PB08`：在信号之后 **前4h** 逐根检查完成的5m `close`。先用 **已完成的过去/当前 close 的运行峰值** 做基准（峰值必须来自回撤当根之前至少一根已完成bar），当当前收盘 ≤ 此运行峰值×(1−3%、5%、8%) 时设为“已发生回踩”。此后只有在连续两个完整5m bar 的 close 严格上升，才标记 `CONFIRMED`；**必须在确认后下一根5m open 才能尝试入场**。若4h之内没有触发或缺少下一根完整bar，输出 `NO_ENTRY`，不赋0回报也不虚构交易。
- 回踩可以在上市后的第一小时出现；不要求历史24h/30d数据。必须有至少 2 个已完成的5m bar 前史判定两根连续close上涨，确认时钟不得反向。
- 4h/24h 的价格结局一律从各自理论入场开始计时（分别使用入场后第48/288根bar close），同时额外计算从信号开始固定24h结局作为组合可比辅助。 `MIN_LOW` 衡量从入场至终点的最低 low，**不是成交止损结果**；若必要K线缺失，标 `CENSORED`，不归零填补。
- 另设 0.2% 假定round-trip总成本的灵敏度展示（不是 Binance 实际费率）；不声明真实资金费、盘口冲击、成交概率或期货清算收益。实际订单流没有接入。
- 研究只有30组，用 **全部30个样本的成交/无成交覆盖、每组中位、严重回撤比例、4h及24h高层结局** 评价；明确 `NO_ENTRY` 的即刻追入结局以看漏掉的机会。**禁止只计算入场后的赢家并得出“选择策略有效”。**

## 不变输出字段

`group,venue,symbol,watch_utc,model,signal_to_entry_minutes,entry_open,entry_status,4h_close_return_pct,24h_close_return_pct,24h_min_low_return_pct,watch_fixed_24h_close_return_pct,reason`。聚合对照含 **entry_coverage、no-entry 样本的原方案结果、retest 的等待时延、24h ≥20% / ≤−20%、期间 low ≤−20%、样本数量**。

这一阶段明确不实现 V4 的 live BUY/邮件、不同规则自动选优、分钟级盘口执行回测；所有时间点及涨幅后验已暴露，真正独立样本需要未来前向 shadow。
