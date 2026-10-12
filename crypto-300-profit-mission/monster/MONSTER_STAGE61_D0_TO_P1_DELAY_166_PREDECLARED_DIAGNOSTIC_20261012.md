# Monster Stage61：第一次D0 WATCH到P1首次点火等待期的全166真实历史诊断

日期：2026-10-12 Asia/Bangkok。本研究只做Monster，不接入其他价格监控、Frank、Gmail、NFT、持仓或自动交易。

## 目标与数据冻结

以Git既有Stage51因果规则明确的每3分钟tick作为时钟：原P1首次合格 at_UTC 减去 (polls_until_eligible-1)*3分钟，精确还原该次首次D0 WATCH的UTC时间。原P1第一次点火46条（delay=0），随后持续观察到P1的120条（delay>0），是待实证检查的事实一致性条件。

全部166条不可删样、不挑未来赢家；来源Stage55 CSV Git blob dca780246adb28e045ed77f0f96eb4bd034fb2e7 与Stage60历史24h全166未来路径Git blob c76b9b73c11924cb3fdc36fb852074ff9b49b3b8，源必须SHA锁定并经Stage61 CI重新校验。

只做事后描述，不确定将哪些delay范围当未来预测信号：
- 固定对照：首次D0立即升级 / 延迟升级、delay>60min、delay>360min、delay>1440min、原127已发 / 39被排除、全部166、后见日历2×与普通组。
- 每组：完整样本数、等待分钟最小/中位/最大、首次WATCH收盘到P1合格前最新已闭合1m收盘涨幅中位数、原P1信号后24h终点收盘代理涨幅中位数、该24h正收益数量、该24h HIGH从信号代理价再次达到2×数量。
- **信号后收益**严格使用Stage60已校验官方USD-M价格代理，不是用户实际入场、现货利润或新策略准确率；历史D0→P1涨幅来自Stage55原当时可见特征（非未来价格）。
- 所有时钟限定为原冻结UTC06起的七日扫描窗。不能因P1很晚就假定时间限制一定有利；任何新TTL或分级都需另冻结未使用日期及全市场回测，不能调旧P1的失败验收阈值。
- 完成后应形成“保持D0早期WATCH；评估后续迟到升级”和完整产品/技术决策证据。数据分析自身并不能放行Mac部署、Gmail或实盘。

状态：PREDECLARED_HISTORICAL_DIAGNOSTIC；NOT_A_HOLDOUT；NOT_A_NEW_STRATEGY；ORDER_NOTIONAL_UNSPECIFIED；MONSTER_NO_GO。