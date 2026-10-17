# Stage161 真实445首服务/重复占槽追踪 — 独立Gemini/Codex审核包

**唯一审核固定SHA `33f17c7b629fbfc8a8df85f13ecfd3546c0377f4`**，基线为上轮Gemini已APPROVE的Stage160固定SHA `ccd879a890e57b02e3538add4d603a158df170da`。PR #30 分支 `research/monster-v4-local-discovery-20261010`，Open/Draft/未合并；当前HEAD在pin之后追加的内容属于cadence/Stage162设计文档，不允许用新HEAD代替固定源码。用户当前只有Gemini可用，请优先审查真实业务有效性和是否导致错误结论，不要靠增加不相关边界测试延迟主线。

## 固定真实来源与输出

- 原始445同SQLite V2 full JSON：GHA run [#38898752712](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38898752712)、Artifact ID `12044872933`，原完整JSON SHA256 `370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf`；18份早期Artifact/28份ZIP来源proof在PR树，来源事后445/原758中313缺历史数据仍CENSORED。
- Stage161一次性真实CI [#39012150858](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39012150858) **2/2 SUCCESS**，trigger SHA `f5c2fd8ad9b5ee9e85fb9835cab3bb85525785ea`。全量真实trace Artifact ID **`12093253053`**，原`monster445_first_service_trace_full.json` SHA256 `44fb0bec7ac0df9b86eebbc923e9e589eb0d07c523dd311758ccec44bf67928f`。Git小摘要 `crypto-300-profit-mission/monster/evidence/monster_feb445_real_first_service_trace_actual.json` Git blob `c54f677f3dcd8c045f03add14795eb87dceae9e9`。
- 代码 `crypto-300-profit-mission/local-agent/scripts/monster_v4_445_first_service_trace_replay.py`，测试 `test_monster_v4_445_first_service_trace_replay.py`，一次性源触发workflow `.github/workflows/monster-v4-445-first-service-trace-one-shot.yml`；前置冻结设计和已复算的实际业务数据见 `MONSTER_445_STAGE161_FIRST_SERVICE_TRACE_DESIGN_FREEZE_20261017.md` 与 `MONSTER_445_STAGE161_REAL_FIRST_SERVICE_CAUSAL_FINDINGS_20261017.md`。
- 研究V2本身（零quote隔离）不是生产D1；此前所有原D0/D1/V2文件SHA必须与基线完全一致。真实SQL observer只能读取D1处理前后的queue，没有往DB写候选、不分配新槽、不改变重试/截止时间。

## 独立审查重点（需负例与真实完整JSON而非仅摘要）

1. **对原模型严格等价**：独立把reference raw JSON里的`execution_counts, event_type_counts, queue_status_counts, queue_rows, events`与Stage161的重放core输出比较；Stage161 runner通过`run_all(...research_zeroquote_v2=True)`临时patch `zeroq.run_v2`与原研究handler，只允许外层观察真正相同的单次调用。检查patch恢复、不污染产线、不把临时MagicMock冒充独立原产线D1。
2. **真实原因数据**：检查全3360轮、753个选中槽与269个首次selected、484次重复selected；533/534忙轮？以**原JSON的534**为准独立算。每候选唯一id及全部269首次selected关联、来自98峰值的7在+0m、91在+18至+51m才首次selected、附近两币+48m才首次selected。原生产`attempts`都为0不等于未处理。
3. **高峰99人FIFO饥饿**：原`process_queue` `WHERE PENDING AND retry_after_ms<=tick ORDER BY first_seen_ms,id LIMIT 8`，真实高峰+0轮8槽为1旧+7新，+3/+6/+9/+12/+15五轮同一老8反复服务、不允许任何其他峰值币抢到slot。+6首次有效后验5m（7个）；+15老8终止，+18新的8首次选中已逾deadline，此后至+51m，总91峰值LATE从未有效期内获得D1评估。前6轮48槽只有7个峰值币首次selected、另外41重复；注释不可说“41浪费”或“91笔有盈利的币”。
4. **实际并非公平性策略已通过**：Stage161只是观察与证明原baseline FIFO拥塞；没有改变候选规则，不能宣称未来创新方案能提高真实盈利。Stage162已冻结的FIRST_VALID_5M_ONCE_PRIORITY_8仅为方案，代码与回测NOT_DONE；旧原445已接触，不能用它优化赢家后宣称新OOS。
5. **trace数据质量**：从raw `slot_trace`逐条按`tick_ms,id`和269原queue身份对账、观察起始与after字段、是否每轮8槽内、统计首次与重复是否准确、每次selected是否只调用原handler一次。合成真实SQLite测试至少覆盖9人竞争8槽、一个候选重试选中两次、初次有效D1识别、原模型字段不一致拒绝输出、原Reference SHA错误拒绝；请自行制造至少一个非法`selected`数、模型事件篡改或超过8槽反例并验证fail closed。
6. **源与权限**：所用28 ZIP/官方issuer收据仍是历史事后source complete subset，2026-02-04非PIT/OOS；无Frank/Gmail/交易/Mac/新的ChatGPT Automation、LaunchAgent、cron/schedule；两个研究Job都success并将trace保留为Artifact，Git摘要不可覆盖。需检查 `gh run` 原日志与本地改动范围。
7. **业务门禁**：还缺真实未来PIT上市池、真实盘口BBO/L2和买卖可成交量、手续费/滑点、送达延迟和净PnL，既有0 SETUP高峰不代表91根本没有交易机会；`G4 UNKNOWN/G6 NO_GO`和所有生产禁令持续。

## 复现方法与审查格式

独立 checkout commit `33f17c7b629fbfc8a8df85f13ecfd3546c0377f4`，Git差异基线 `ccd879a890e57b02e3538add4d603a158df170da`。在 `crypto-300-profit-mission/local-agent/scripts` 运行 `python3 -m unittest -v test_monster_v4_445_first_service_trace_replay test_monster_v4_shared_d1_zeroquote_research_v2 test_monster_v4_shared_445_source_shards`，记录真实退出码。下载 run #39012150858 Artifact `12093253053`，验证SHA `44fb0bec7...`、逐个slot/tick复算269/484/753、全部93个LATE首次在期限之后，取原full JSON对照事件和最终queue。需要独立复跑全445时按CI原workflow只读重做；若没有权限下载和原字节，明确`RAW_REPLAY_UNVERIFIED`，不能只看Git摘要就声称独立复算。原始完整ZIP用户当前对话中可提供，不必分享密钥。

输出审核者身份/准确底层版本（无法核验写UNVERIFIED）、固定SHA及基线、实际执行命令与退出码、原始Artifact/hash、关键模型等价性与是否无未来泄漏、带真实反例的P0/P1/P2/P3问题及文件行号、最终 `APPROVE / REQUEST_CHANGES / BLOCKED`。**即使APPROVE只针对Stage161旁路研究插桩，不批准Stage162模型、盈利、Mac/Frank/Gmail或真实交易。保持NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE。**

**本文件生成时OTHER_AI_REVIEW=NOT_DONE**，不得把作者CI称为Gemini已审核成功。
