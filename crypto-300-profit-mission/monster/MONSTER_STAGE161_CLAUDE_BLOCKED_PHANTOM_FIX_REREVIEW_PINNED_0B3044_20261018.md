# Monster Stage161 — Claude BLOCKED/REQUEST_CHANGES 修复、真实445再验证、重新复审包

**唯一代码与研究证据复审固定 SHA：`0b3044daa9eeef14ac968c6d0f36a430b6b9ca23`**

- 上一轮Claude审查SHA `a1977cecea3bc6a99b70d86e672df9c23280058b`，模型窗口宣称Claude Haiku 5.5，底层模型无法独立核查，`UNVERIFIED`。Claude给 **`BLOCKED` 总结论（没有收到原Artifact）和 `REQUEST_CHANGES` 代码结论**，该状态持续直至另一AI真的独立复审，不能以作者CI替代。审核范围仅Stage161研究观测器/证据，不含Stage162 A/B调度模型或盈利结论。
- 仓库：https://github.com/lxxlx2/ChatGPT_mission_record；Draft PR：https://github.com/lxxlx2/ChatGPT_mission_record/pull/30 。当前pin以后仅允许后续研究说明/审核文档commit；此文件本身**在固定pin之后创建**，这是Git SHA不能把自身未来文档包含在同一不可变commit的正常现象。请以完整分支路径在当前HEAD读取本说明，**实际审核执行checkout固定pin**，不要要求说明文档必须事先存在于那个SHA。
- 所有生产`monster_v4_shadow.py`、原shared core、原zeroquote研究V2均字节不变；未动Frank、Mac、真实交易/Gmail，不新增计划任务、cron/launchd/schedule/ChatGPT Automation，保留`NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`，`G4 UNKNOWN/G6 NO_GO`。历史445属于758中事后来源完整集，313删失，非PIT上市/独立OOS/可执行净PnL。

## 审核反馈逐项修复与防误导说明

**P2（blocking）“幻影第8槽”**：
- 上一版`monster_v4_445_first_service_trace_replay.py`检查原handler `selected`数量和非预计前8行未被改，但未要求预计8行真的已被服务；Claude真实SQLite探针`7/8修改但selected=8`和`0/8修改但selected=8`能绕过。
- 当前在`FirstServiceObserver.instrument()`里，**处理前后读取完整`candidate_queue`所有行**：ID集合一致、任何非预计前8行完全不变、**所有预计选中行每行至少一个持久字段发生变化**。不满足任何一条fail-closed；有误不得生成成功trace。正向不可将选中前后整行相等当做有真实服务凭证。
- **新增三组真正SQLite独立反例**：`test_09`只修改前7行但宣称选8，`test_10`完全没更新队列但宣称选8，`test_11`使用自定义7分钟/30分钟候选`deadline_ms`，确认早到晚到与`first_seen+15min`硬编码不同。
- 原`test_06`之前模拟改写第9行时故意仅更新了前7行，新正向不变式先捕捉`selected_candidate_no_state_change`，使测试原预期的`nonselected_candidate_mutated`名称不再吻合。**真实第一次CI #39064319960在单测步骤FAIL，full replay正确SKIPPED；保留失败日志**。修复测试为更新真实前8行又非法更新第9行，结果必须命中`nonselected_candidate_mutated`；幻影测试独立由test09/test10覆盖，避免用弱化观测器的方式让CI通过。

**P2截止/时间**：函数`selected_within_queue_deadline()`直接读取每个候选实际 `deadline_ms`，test11以7分钟过期/30分钟延长的真实谓词边界验证。不是仅在CI里检查deadline≥first_seen。98峰值在+6/+9/+12/+15四轮才具备有效5m首评容量，因此**32最多理论有效首次评价槽、额外25是理想极限，不是保证机会/SETUP/盈利**。原六轮×8=48仅是“被选中”最大槽位，不是合法有效评价上限。

**190次未推进5m游标的正确表达**：真实研究V2单库slot trace 753 selected =269首次+484重复，重复中**190占槽但没有推进有效5m评价游标**、294有推进。190分类：68次`AWAIT_POST_WATCH_CLOSED_5M`、93次`NO_SETUP_YET`（这161可能包括对同一已知窗口的重复检查）、15次研究V2零quote保护、14次15m窗口期结束的合法队列终态服务。不能把190都当无价值请求、或强行说没有新行情。最终原93个LATE第一次被选中均已超过各自实际deadline；**不是93个可获利交易机会**。Stage162独立A/B研究仍NOT_DONE，不能借本次修复承诺SETUP召回增加。

## 真实GitHub测试与原字节文件

- 修复运行 [**CI #39064416945**](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39064416945)，固定触发源码SHA`a57b44716a01f8f929e47969045e654eaaf85d1c`，**两个Jobs success**。stage1`py_compile`通过；`python -m unittest -v test_monster_v4_445_first_service_trace_replay`真实11/11通过(exit0)，source/zeroquote组合18/18通过(exit0)，**合计29项**。原full JSON先做SHA校验成功；重新收集历史18 artifacts、28 ZIP/publisher SHA源校验成功；同一SQLite 445币3360 tick全量原V2，再执行严格每行变更校验，所有`execution_counts/event_type_counts/queue_status_counts/queue_rows/events`与原445模型完全一致。
- Git小型事实证据 `crypto-300-profit-mission/monster/evidence/monster_feb445_real_first_service_trace_review_v4_actual.json`，Git blob `60d574de8b59b6d95eceefbff17db0bb9f7dd60c`，不覆盖旧V1/V2；完整GHA Artifact ID **`12113086240`**，名称 `monster445-real-first-D1-service-phantom-fix-28shards-v4`，到期2026-12-16T19:59:16Z。
- **完整trace原JSON的实际SHA256与旧版本一致**：`8d7ac8d9a0a78a0daa1164d0aee7783b0a51f29ef099437590b103bad0bab76d`，原因是新增严格观察不改变任何被记录的处理字段。此原始ZIP在当前ChatGPT会话的可下载文件为`monster445_stage161_phantom_review_v4_20261018.zip`，用户必须作为真实附件上传Claude聊天窗口（不是把下载链接文字发过去），不需要任何GitHub token。
- 作者再次独立在本会话解压原GHA ZIP，直接从753个`slot_trace`计算269首次、484重复、294重复推进有效5m标记、190没有推进、534忙轮；190分类`NO_SETUP_YET 93 / AWAIT 68 / SOURCE_ZERO_QUOTE 15 / END_WINDOW 14`；269个candidate中93 LATE首次selected时间均在其实际`deadline_ms`后。**这仍不能冒充Claude已经获取原ZIP完成独立复算**，Claude原BLOCKED需其收到文件后解除。
- V4执行日志可读证据：`freeze_and_offline` stage 11 tests in 0.113s OK + 18 tests in 9.769s OK，`actual_full445_eight_slot_trace` source SHA check OK，原28来源核查行 `MONSTER445_FIRST_SERVICE_REAL_ALL_28_ORIGINAL_SOURCE_SHARDS_ATTESTED`，原V2一致行 `MONSTER445_FIRST_SERVICE_ALL445_REAL_TRACE_MATCHED_ORIGINAL_V2`，Git seal 行 `MONSTER445_FIRST_SERVICE_REVIEW_V4_RESEARCH_EVIDENCE_IMMUTABLE_GIT_ARCHIVED`，两个Job均SUCCESS。Claude环境API限流不是此次CI失败。

## 给另一AI的准确审核动作

Checkout SHA`0b3044daa9eeef14ac968c6d0f36a430b6b9ca23`，对比原拒绝审查SHA`a1977cecea3bc6a99b70d86e672df9c23280058b`；核对Stage161两个Python文件+一次性workflow+新evidence，其他原产线代码不能变。运行`python3 -m unittest -v test_monster_v4_445_first_service_trace_replay test_monster_v4_shared_d1_zeroquote_research_v2 test_monster_v4_shared_445_source_shards`，给退出码。自行复现同数量8但仅更新7个 / 完全不更新 / 更新8个又非法改第9个，对照每个异常名称，确保失败可归因。检查旧Review V3的失败日志没有被抹除。用实际附件ZIP先校验内`monster445_first_service_trace_full.json`SHA256`8d7ac8d9...`再从原始`slot_trace`独立重算753/269/484/190/294、93个LATE均未在实际截止时间前首次选中。若得不到原字节必须写`RAW_REPLAY_BLOCKED`，不可仅从本说明/Git小摘要“推定”独立确认。审核范围Stage161旁路观测器和统计，不含Stage162/盈利/生产。

输出审核者身份与底层模型（不可核实写UNVERIFIED）、固定SHA、基线、实际运行命令、各P1/P2/P3 CLOSED/OPEN/PARTIAL/BLOCKED以及真实反例、最终`APPROVE/REQUEST_CHANGES/BLOCKED`，保留所有生产禁令。

**当前实际审核状态：上一Claude `BLOCKED/REQUEST_CHANGES`，作者代码修复和真实CI通过，独立其他AI复审未发生。**
