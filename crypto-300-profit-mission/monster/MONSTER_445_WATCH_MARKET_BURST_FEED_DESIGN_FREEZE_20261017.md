# Monster Stage160 — 基于真实445的突发WATCH可读输出合同（先冻结后实现）

**审核/数据身份。** 第三轮Claude独立审核对固定SHA `68f2b9516fd89fdad5197a68bb9657e4c639a7ff` 的研究代码修复结论 `APPROVE`（Claude底层准确版本UNVERIFIED）。**原始full JSON在Claude环境没有拿到，独立对原始数字的P1-2仍BLOCKED。** 这不阻止作者从原Artifact只读开展下一阶段实验，但任何用户可见数字都应注明由当前对话本地计算、不是Claude对raw JSON的独立背书。PR #30 Draft/open/unmerged，G4 UNKNOWN/G6 NO_GO。

**冻结数据范围。** 原445同日source-complete币共用单SQLite3360次全球poll，原始2026-02-04历史source-complete cohort（非PIT上市池、不是OOS），原758中313删失，full result Artifact ID 12044872933，原JSON SHA256 `370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf`，用户当前对话内有 `monster445_full_replay_20261016.zip`。本研究只允许读取已归档`WATCH_EARLY`事件里的首次观察字段（event_id、symbol、venue、observed_ms、trigger窗口、观察时点涨幅、24h quote代理），构建**历史展示预览**；每个候选原事件及字段必须保留，不能用后验D1 status、SETUP、LATE、未来OHLC作为当时排序或推荐。

**预先固定的可解释分组规则（非调仓、非D1调度、不依赖后验盈利）：**

- 每次`observed_ms`完全相同（3分钟poll周期）的一组WATCH是一个展示批次；若**同轮WATCH数>原D1槽位上限8**，在研究展示中改为一张`MARKET_BURST_WATCH`卡，卡片链接到全量成员；否则逐币展示。阈值9来自既有单tick8槽**容量合同**，不是在Feb445数据上调出来的获利最优参数；以后变更必须新预注册、不能回写本次。
- 同一市场批次不意味着98币属于同一个产业或存在因果同涨。多币显示顺序可按WATCH时点拥有的quote24 USDT历史重建代理值降序，其余按symbol/eventID稳定排序，**仅用于展示顺序**，不当做可执行深度、盈利率或交易优先级。分组不得删除、屏蔽、改变D0/D1/outbox持久事件。
- 输出分为两个物理上隔离字段：`point_in_time_display_preview`（只读WATCH当时已知字段，所有**269个WATCH**逐币保留，任何后验状态字段不得进入）与`hindsight_diagnostic_not_for_live_display`（对照过去研究V2真实最终状态，含同刻98中91LATE+7EVALUATED、是否产生SETUP、容量峰值等）。历史重建的quote24 proxy绝不能宣传成当时官方24h PIT ticker；没有实时再核验和盘口成本，`can_follow_now=UNKNOWN`，`BUY=FORBIDDEN`。
- 无历史邮件量记录，`standalone_watch_cards`仅属于“如果一WATCH一张卡”的静态对比模拟，不冒充真实发送量；本规则最多把同轮的超过8个个别历史WATCH显示为1张集成卡。禁止发送邮件、通知、启动浏览器后台任务或实时监控。
- 必须从raw复算：历史269 WATCH共多少unique tick，超过8槽有多少batch及覆盖多少候选，分组后`display_cards_count`、被分组逐币仍可检索数量，旧研究队列的hindsight终态以及SETUP以冻结生产event_key验证，全部校验失败即不输出“成功”。

**否决标准与未来验证**：如果任何WATCH丢失/被覆盖、出现后验标签或未来价格泄露至当时预览、代码触发任何生产副作用、隐瞒原313删失，则NO_GO；如果分组后发现用户仍可能把市场事件等同交易推荐，改文案而非增加不必要的模型规则。后续单独研究“首见公平性+重试公平队列”才会碰D1策略对照，必须在独立前瞻/PIT样本上计漏报、首见时延、有效SETUP及可执行价差、流动性/手续费/滑点；Feb445已观察样本不能被当成OOS或验证收益。所有试验仍NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE，不创建任何定时任务。
