# Monster Stage161 — Claude REQUEST_CHANGES 修复 / 下一次独立复审（固定 SHA）

本文件属于**提交后复审交接文档**，不扩大原研究代码的审核范围。

## 身份、冻结版本、范围

- 仓库：https://github.com/lxxlx2/ChatGPT_mission_record；Draft PR：https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
- 上一轮真实独立审核人：Claude聊天窗口，自述Claude Haiku 5.5，底层身份无法第三方核验 `UNVERIFIED`；原审核结论 **REQUEST_CHANGES**，审核SHA `33f17c7b629fbfc8a8df85f13ecfd3546c0377f4`，比较基线 `ccd879a890e57b02e3538add4d603a158df170da`。
- **本次唯一修复代码+真实V2证据复审固定 SHA `a1977cecea3bc6a99b70d86e672df9c23280058b`**。此前审核状态尚未改判；`OTHER_AI_RE_REVIEW=NOT_DONE`。此pin以后的cadence/审核文档变更不改变批准代码身份。
- 生产 `monster_v4_shadow.py` / shared original core / zeroquote V2 字节未修改；本轮只改Stage161旁路观测器、SQLite反例测试、单次研究CI、解释文档、Stage162未实现的预注册方案，原历史V1 trace和所有来源proof**不覆盖**。
- 严禁 `NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`，G4 `UNKNOWN`、G6 `NO_GO`；无任何新schedule/launchd/cron/ChatGPT Automation、Mac或Frank生产操作。

## Claude提出的每一项问题与作者本轮修复

### P1-1：有效D1首次评价容量，不能拿48错充32

`MONSTER_445_STAGE161_REAL_FIRST_SERVICE_CAUSAL_FINDINGS_20261017.md`新增明确区分：

- 原峰值2026-02-06 00:36UTC同刻98 WATCH，+0/+3m尚无WATCH后真正闭合的5m K线；**首次有效评价只可能在+6/+9/+12/+15m四个poll**，在假定其它旧候选及正常重试均不竞争的最宽松边界下 **4×8=32**。
- 原实证只有7个峰值币得到有效评价，所以最多*理论额外*25个 **有效评价**；远不是可保证挽救25个SETUP，更不是91个潜在盈利机会。此前六轮×8=48仍是“首次被selected”的空闲理想上界，不是“首次有效评价”上界。32不一定能实际达到。
- Stage162**预注册补注**以上边界；保持原研究B与生产8槽/15m条件，不用同一天峰值结果选择赢家排序参数。

### P1-2：根因不只是FIFO排序，需实际区分无新5m游标推进的重复选中

真实 `monster_v4_shadow.py` 在 `AWAIT_POST_WATCH_CLOSED_5M` 或 `NO_SETUP_YET` 时都把 `retry_after_ms=now+60000`，下一个全局poll在3分钟后，旧PENDING候选早就重新有资格。按`first_seen_ms,id`的原FIFO再选同一旧8，造成晚来候选饥饿；改变“尚无新已闭合5m候选的重试资格”和改变优先排序是两种**不同的实验**，本轮没有实施任何策略变更。

新版 `monster_v4_445_first_service_trace_replay.py` 按逐槽读取 `last_evaluated_bar_ms_before/after` 派生 `valid_5m_evaluation_marker_advanced` 与两个互补计数。旧stage161原始Artifact和新原始445 rerun交叉检查后一致：

- 共753选中 = 269首次 + 484重复。
- **重复且没有推进有效5m评价游标=190**（peak98:14，other171:176），重复且有推进=294（peak98:21，other171:273）。
- 未推进的190条按处理后error分组：`AWAIT_POST_WATCH_CLOSED_5M=68`、`NO_SETUP_YET=93`、`SOURCE_UNSUPPORTED_ZERO_QUOTE=15`、`NO_SETUP_WITHIN_WINDOW=14`。
- 这些值是**有效评价游标没有向前移动**的证据，不是断言没有任何市场新K线、或者能够无害删除190次服务；若删除掉有意义的重试，原120个SETUP可能受损。

### P2-1：同数量、不同ID不能误归因

新版observer在调用真正冻结zeroquote研究handler的**前后分别读取candidate_queue全部真实SQLite行**，比对ID集合相等，并逐行检查未在真实FIFO预测前8候选里的每个ID的全部SQLite字段完全不变；如果有非预测ID变动、或新增/删除候选，则 `MONSTER445_TRACE_nonselected_candidate_mutated` / `candidate_row_set_changed` fail closed，且不会输出成功trace。与此同时保留真实`outcome.selected==predicted_count`核验。V2可能在handler内部暂时mask旧队列非selected的`retry_after_ms`，完成时已恢复，终态对账不允许污染。

新增两项**真实SQLite负例**：故意声明selected=8，但仅修改前7个预测行同时改写候选ID9（相同数量、不同集合）必须失败；故意插入新ID候选但声称8 selected也必须失败。再新增一项无新有效5m游标进展的重复8槽指标正例。原5项测试扩成8项；真实CI #39043696721 Ubuntu stage1 **8+7+11=26项**相关单测exit 0。

### P2-2：时间截止使用队列实际字段

`LATE_selected_before_deadline` 从`first_seen+15*MIN`改为比较候选行中`deadline_ms`，并在每个`candidate_first_service`输出真实字段。原历史两者一致但源不同，以防未来研究deadline合同漂移。

### P3：解释文本

- Stage161因果报告非峰值状态的正确汇总为“171=162 EVALUATED+4 INVALIDATED+3 零报价研究终态+2 LATE”，不再写“其它169合计171”。
- 峰值+51m这一次共选中5个：**峰值91个LATE中的最后3个**、以及峰值后+3m才WATCH的GPSUSDT/LUNAUSDT这**2个非峰值币**。这2个的首次延迟是**各自WATCH后48分钟**，相对于峰值时间是**+51分钟**，不能混淆两个时间基准。
- 明确本基线是**原V2研究队列handler + 冻结生产D0/D1代码**，不是原生产D1对含0 quote全445完成回放。

## 本轮实际 CI 与不可伪造数据身份

- 单次显式request `MONSTER445_FIRST_SERVICE_TRACE_ONESHOT_REQUEST_V2`，源码trigger commit `516531c74dade32c602b5974915f258d70521717`，CI [#39043696721](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39043696721) **2/2 jobs SUCCESS**。
- 全445真实历史回放先验证历史full JSON artifact `12044872933`，原sha256 `370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf`，然后重下18原Artifact/28片source proof并在同库3360 tick重跑；核心V2全部`execution_counts`、`queue_status_counts`、`event_type_counts`、`queue_rows`、`events`均与旧full源**逐字段相等**。
- 新完整Artifact ID **`12105470474`**（`monster445-real-first-D1-service-review-fixes-28shards-once-v2`，预计到期2026-12-16T15:11:52Z）。里面 `monster445_first_service_trace_full.json` 字节SHA256 **`8d7ac8d9a0a78a0daa1164d0aee7783b0a51f29ef099437590b103bad0bab76d`**；本会话从下载的这个原始ZIP再次独立复算确认 753/269/484、190/294、四类状态划分和93 LATE期限字段。
- Git小型归档：`crypto-300-profit-mission/monster/evidence/monster_feb445_real_first_service_trace_review_v2_actual.json`，Git blob `f6a2ac8d27316ac4c3bcf2c72462a801722aa964`。旧V1 evidence/Artifact均保留，绝不覆写。

## 复审命令/判定规则

请使用新的固定SHA `a1977cecea3bc6a99b70d86e672df9c23280058b`，基线原审核SHA `33f17c7b629fbfc8a8df85f13ecfd3546c0377f4`。在 `crypto-300-profit-mission/local-agent/scripts` 实际运行

`python3 -m unittest -v test_monster_v4_445_first_service_trace_replay test_monster_v4_shared_445_source_shards test_monster_v4_shared_d1_zeroquote_research_v2`

特别自己构造`selected=8`但写了非预测ID9的SQL负例，核查`candidate_row_set_changed`也fail-closed；检查全部269原queue的`deadline_ms`是否已用于LATE计算。需要收到**新真实Artifact ZIP**（当前对话已可直接下载并上传Claude）并校验full JSON SHA `8d7ac8d9...`之后，才能独立从原`slot_trace`复算190/294及93个LATE的时间。没有原字节必须将`REAL_TRACE_RECOMPUTE`写`BLOCKED`，不得把Git摘要或作者CI当作独立数据复核。

请对原 P1-1/P1-2/P2-1/P2-2/P3 逐条标 `CLOSED / PARTIAL / OPEN / BLOCKED`，写真实AI身份（底层不可核写UNVERIFIED）、固定SHA与baseline、实际命令退出码、文件及行号、反例，最后给出 `APPROVE / REQUEST_CHANGES / BLOCKED`。APPROVE仅可覆盖**Stage161研究旁路观测与审计修复**，并非Stage162公平调度模型、盈利/执行可行性、Mac/Frank/Gmail/交易授权。所有现有生产禁令继续有效。

**该报告目前仅由作者准备；OTHER_AI_RE_REVIEW=NOT_DONE。**
