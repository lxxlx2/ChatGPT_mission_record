# Monster Stage161 — 445真实D1逐轮首次服务与占槽轨迹（先冻结再实现）

## 本轮核心产品问题

Stage160显示层268/269的数据显示没有解决真实D1能力问题：2026-02-06T00:36:00Z的98同刻WATCH中91最终LATE，仅7为EVALUATED；不能以0 SETUP证明没有机会。Stage161目标是回答：**真实研究V2同一SQLite执行期间，哪些WATCH首次进入8槽、首次被真实评估、何时延期、多少旧候选重复占8槽、以及91 LATE到底有没有处理过？**

当前实测原445全结果 SHA256 `370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf`，Artifact `12044872933`，run #38898752712；原SHA内269 queue_rows的attempts都为0，但 execution_counts 已真实存在 D1_selected=753，D1_deferred=488，D1_completed=169，D1_late=93；`attempts=0`只能证明**没有走相应Error增加尝试计数的分支**，不是没被选中或评价。仅历史最终状态**没有逐轮首次处理时间**，不能事后填造首次尝试时间；需要对相同28原始来源单库再跑一次**旁路插桩**，验证全量原结果不变。

## 技术边界：旁路观察，不改原算法

- 原 `monster_v4_shadow.py`、`monster_v4_shared_spot_d0_d1_original_core.py`、`monster_v4_shared_d1_zeroquote_research_v2.py` 文件字节Git blob固定不变。新`monster_v4_shared_445_first_service_trace.py`可在**隔离研究进程内**对已有`experimental_queue_handler`增加临时外层只读观察回调：在同一次 `run_v2` 中以`patch.object(zq,'experimental_queue_handler')`方式封装，真实内部仍调用原处理函数一次；绝不自行重复选币或改回放队列策略，不写入DB、不修改候选优先级、retry_after、8槽上限、15分钟有效期。原V2也仅是研究处理器，不等于原生产零quote真实处理行为。
- 新脚本从18个固定GHA原始Artifact ID、28份ZIP/Git原proof直接复制来源到本次临时沙箱，并完整调用已有 `shards.read_archive(proof=...)`、`shared.prepare_symbol`。原758中313仍CENSORED、不追加、不替换、不假零。
- 单个全局tick记录处理前`pending`、可选中总数、实际选中原FIFO前8的 ID、`first_seen_ms`、原status、上次last_evaluated_bar_ms、retry等待数；处理后读取相同候选的`status`、`retry_after_ms`、`last_evaluated_bar_ms`、`last_error`，并按候选ID构建`first_selected_tick`、`first_successful_evaluation_tick`、重复选中次数、是否逐轮延期。SQL只读且单一SQLite连接/进程；若event含敏感令牌/地址，不导出。
- 新追踪结果的原始Model输出必须逐字段比对*另一份已冻结445正式V2回放*的`execution_counts, event_type_counts, queue_status_counts, queue_rows, events`，有一个字节级语义漂移就fail-closed且不写最终成功证据。仅允许timestamp/run provenance/log和独立研究扩展不同；如不一致先修仪表而不回写旧证据。
- 出具有界 `slot_trace` per tick非空服务、`candidate_first_service`269全员、来源审计、tick摘要（3,360轮），以及小型Git result summary。必须有独立原source SHA/28proof校验、原445 full JSON SHA对照；禁止用纯合成trace代替。
- Metrics在观测前冻结：总269 WATCH，98高峰与171非高峰分别报告首服务覆盖率、0/3/6/9/12/15m首服务、排队初次服务延迟p50/p90/p99、全局重服务占槽与first-selected占槽、哪种`DEFERRED`是正常尚无新的收盘K线/正常无SETUP、哪种是研究零quote、不把全部DEFERRED算作错误、最终91个LATE中首次选中/未选中人数及其分布。必要时如无全部逐条因果信息，明确UNKNOWN，不发盈利建议。
- 只允许使用当时存在的排序信息做将来的候选策略离线比较，绝不以已看见的98/91/SETUP作为未来调度排名目标；先实际采集本轮后再设计公平队列反事实，不能为快速减少LATE而直接提高生产D1容量或更改阈值。
- 发布禁令：无新ChatGPT Automation、GitHub schedule、launchd/cron、Mac/Gmail/Frank/交易操作；G4 UNKNOWN/G6 NO_GO、NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE，Draft PR#30继续。

## 最终验收

必须由一次**显式、仅研究request JSON的push触发** GitHub Actions执行真实28来源回放，单元测试在执行前通过；原V2终态逐字段与历史冻结结果一致；提交全量trace Artifact 与小型Git summary，以新固定SHA送独立另AI审批。CI成功≠模型盈利。不能在没有trace时宣称已经掌握首次处理时延或可执行净利润。
