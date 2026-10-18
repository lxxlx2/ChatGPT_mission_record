# Monster — 已存研究机会读取：先保留全窗口，再按研究状态显示，冻结需求（2026-10-18）

## 当前实际代码/业务缺陷（在任何代码改动前冻结）

现有已获Codex限范围APPROVE的`local-agent/scripts/monster_v4_opportunity_snapshot.py`（原SHA`d38999df6db63192ad3e3d11e793e2e6c4df05db`）只读真实Monster SQLite，正确按事件ID识别 WATCH/D1/ D2、过期、失效、单币quote时效，`NO_BUY`。然而SQLite查询`candidate_queue WHERE first_seen_ms BETWEEN ... ORDER BY first_seen_ms DESC,id DESC LIMIT ?` **先按新旧切掉窗口中其余行**，其后才解析`INVALIDATED/EXPIRED/SETUP/WATCH`。因此最近25个都已经失效、但更早仍有效的研究WATCH/SETUP会**完全被分页隐藏**，默认返回还宣称“shown 25”，不披露该窗口有多少被丢弃的研究回合或有效信号。这对用户「现在有何关注机会」比静态盘口小数点差更有影响。

不得修改已冻结D0/D1/Fair8/Stage163真实采集和资金、上游Shadow写入、Frank、后台服务、发送及任何自动交易。这里的“当前”只代表**查询时已存SQLite的研究状态**，不是当前实时HTTP交易所行情；不将失效事件改写为交易建议。

## 冻结最小规格

1. 在同一`mode=ro/query_only`连接内查询**完整请求时间窗口**队列候选；保持一行一Episode，维持严格`event_key`、`deadline`和单币`latest_poll`/quotes新鲜度的原有状态优先级。禁止`LIMIT`在状态判定之前截断。
2. 先对全部回合完成状态推导、统计`counts_by_signal`和总数，再按**唯一展示优先级**排序：(`SETUP_RESEARCH_ONLY` Spot) > (`WATCH_RESEARCH_ONLY`) > (`FUTURES_ONLY_SETUP`) > (其余被阻断/过期/失效/陈旧的诊断)。每级仍按`first_seen_ms DESC,id DESC`确保同类时间越近越前，不挑选后验赢家/代币市值/历史盈利。仅在此后应用`--limit`默认25，保留`window_total`,`hidden_by_display_limit`,`counts_by_signal_full_window`和明确语义。禁止提供BUY按钮/自动提醒。对Futures单列低于Spot优先级，不能冒充Spot。
3. 原`--asof-ms`维持只在已存数据库上评价时间年龄，不改写历史PIT状态；仅在基于生产Shadow本身注入的一次合成SQLite写入测试覆盖：至少20个更近的失效WATCH + 1个更早仍有效的WATCH/SETUP，`limit=3`应优先返回仍可研究的那条，全部21个计数/隐藏18可信；非活跃状态依然保留于完整研究历史；另保持10个旧测试继续绿灯。
4. 此需求只改善**已经真实存在SQLite数据库时的operator可见性**，不会创造新SETUP、新实时市场数据或提高历史模拟胜率；没有独立Mac验收和真钱执行。设计接受标准：全窗口统计、无遮挡仍有效研究信号、无BUY、SQLite读不写、测试真实Shadow函数与真实SQLite schema。若用户没有现存Mac Monster DB，不假称目前有可跟机会。

## 后续操作门禁

需先提交本冻结合同，再实现源代码、真实运行CI，同一PR#30完整记录实际失败/成功；其他AI需对新源SHA做**局部独立审核**且确认为APPROVE后才能记工程验证通过。当前Stage162 Fair8仍新增SETUP=0，历史Stage30、Stage152负经济代理及未来163全套OOS未通过；G4 UNKNOWN、G6 NO_GO、NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE，不恢复Stage99也不更改Frank。
