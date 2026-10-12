# Monster Stage41 — P1高优先级研究引擎因果技术方案（DESIGN_ONLY，2026-10-12）

**严格先后关口**：[Stage39全部900×6真实USD-M市场与普通币WATCH量化](MONSTER_STAGE39_FULL900_SIXDATE_ORIGINAL_V4_REAL1M_SHA_MARKET_DISCOVERY_FINAL_20261012.md) = FACTUAL_PASS → [Stage40先提交并冻结的WATCH/P1候选与淘汰门槛](MONSTER_STAGE40_WATCH_PRIORITY_IGNITION_KPI_AND_STRATEGY_PROPOSAL_20261012.md) = STRATEGY_DRAFT → **本Stage41 = TECHNICAL_DESIGN** → Stage42原相同核心规则的全市场历史因果回放/独立保留数据 → 真实其它AI Review → 集成/隔离/本机部署后验收。此稿不构成改动Frank、Monster本地服务、Gmail或交易的许可。

## 输入/时间契约

- 入口仅接收已被**未改动原版V4**产生并已记录 `WATCH_EARLY` 的 `(venue,symbol,watch_closed_utc,first_watch_closed_price,event_id)`，以及来源SHA验证过的相同venue/symbol原始官方1m K线（UTC分钟起点、open/high/low/close、quote volume）。原始D0确定方式和旧WATCH冷却不动。
- 完整且连续的分钟k线必须从至少 `first_watch_closed_utc-60min` 覆盖到 `first_watch_closed_utc+6min`，全部以**已经闭合**bar为输入。不得计算 `now` 以后收盘、将不完整分钟做收盘价、使用未来2×/5×/10×标签控制P1。
- 候选检测流程 `priority_candidate_v01` 作为纯函数不写外部DB、不读预测市场、不调BTC、不发邮箱、不交易：在首次WATCH时计算60m价格收益，≥8%；分别在第一个和第二个后续3m确认点读取最近已收盘close，均≥WATCH close；在第二个确认时刻计算最近15m真实quote成交额≥250,000 USDT，且该15m每分钟均量与更早45m每分钟均量的比值≥1.5。任一所需bar缺失、时间不在一分钟刻度、价格为零、成交额负值或样本点未闭合，返回明确`UNSCORABLE_SOURCE`或`NO_ESCALATION`，不能等价“币没有2×”。
- `P1`升级预期相对于D0第一次WATCH至少经过两个3m确认，因果延迟约6分钟。在真实D0刚好临近暴涨的案例，P1可能太晚——这必须作为模型风险记录到升级后的首次2×时差。P1不能回填到首次WATCH时间骗取提前量；低优先级D0始终完整保留。
- 单币**事件幂等ID**采用 `SHA256('MONSTER_STAGE41|'+venue+'|'+symbol+'|'+original_watch_event_id+'|P1_V01')`，仅用于历史research事件去重。绝不写原Frank SQLite/outbox。后续真实Monster要有独立SQLite/LaunchAgent/端口/队列/日志及真实授权通知回执。

## 研究执行架构

1. 先从 Stage39 的 `monster_stage39_all5400_usdm_real1m_originalV4_cases.jsonl` 无条件读取所有3283个源完整的币日期及原V4 WATCH_UTC；**严格校验483个有WATCH的不同币日期**，其中50未来日历2×且已有WATCH、433未来窗口未达2×，不允许事后只选52个赢家。
2. 对这483个有效WATCH币日期，从**官方USD-M 1m ZIP + .CHECKSUM**仅取必要的首次WATCH及其前60m/后6m归档范围（多数1–2个UTC日文件），计算P1；按原始日期、币、原始WATCH event_id严格一一对应。另52个2×真标签中的一个TRUMPUSDT源删失、一个PENGU无WATCH，不能算P1已覆盖的候选；P1的召回分母必须包含所有有效2×，漏报不能被候选过滤消失。
3. 全部新数据与假设必须在读取新日期前先完成`date_exposure_ledger`，不得把已研究Spot/Monster阶段上百样本简单重新命名为OOS。先只把已经暴露的Stage39用于**代码同样行为验证**，不拿它的阈值跑出高命中就宣称未来可盈利。
4. 输出 `source_verified_P1_candidates.jsonl` 每行包含日期、符号、原始D0 UTC、原始D0价格、P1判定时UTC、两次3m确认真实已闭合K线UTC、前60m涨幅、15m quote、先前45m quote、P1是否升级、为何不升级、SHA证据、未来GT（评分阶段**独立附加**）、与真实首次HIGH越线的严格时间差。
5. 由与源采集隔离的聚合器对全部候选进行source SHA+ZIP CRC复验、原Stage39 D0时间一致性、事件分母及漏报归类，不得把应用异常算作没有P1。实际用户告警压力至少报告P95单日、峰值日、6日期每周原V4 WATCH事件数与新P1事件数。

## 代码与验收需要真实通过的测试

- 时间边界：第1、2个后续闭合3m都不使用未闭合bar，`t+6m`不能由`t+7m`后验补出；
- 形态：中间一分钟缺档、quote为负、open或close≤0、乱序时间必须fail-closed；跨UTC零点用官方前一日/当日，中文年份无关；
- 识别与生存：所有D0原事件记录保留、若P1不升级不能修改原WATCH、后验2×分类仍按Stage39冻结价格；
- 资金与外部系统：本轮完全只读；没有真实盘口时任何P1 `BUY`状态都不可出现，production Mac/Frank/Gmail仍保持NO_GO；
- 不同样本：市场范围要包括所有已暴露的483个WATCH（不是52已知赢家），对5×/10×零或一个正事件返回`INSUFFICIENT_EVENTS`而不假报成功；
- 一套P1候选满足不了Stage40冻结的“保留重要提前事件≥80% + 优先提醒平均≤5/天且单天≤12”等门槛，就弃用/标记`FAIL`，不许循环调阈值直到旧日期变好。

**Stage41技术方案已写入，不是已实现或已测试。状态：`TECH_DESIGN_DRAFT`；`STAGE42_IMPLEMENTATION_NOT_DONE`；`INDEPENDENT_OTHER_AI_REVIEW_NOT_DONE`；`DEPLOYMENT_NO_GO`。**
