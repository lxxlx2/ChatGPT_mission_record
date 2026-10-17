# Stage160 269 WATCH展示分组研究 — 独立Claude/Codex审核包（固定SHA）

**只准审核研究数据及只读展示投影，不批准盈利模型或生产UI。**
- 仓库：https://github.com/lxxlx2/ChatGPT_mission_record
- Draft PR：https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
- branch：research/monster-v4-local-discovery-20261010
- **唯一代码+数据审核固定SHA：ccd879a890e57b02e3538add4d603a158df170da**
- 新研究范围相较已审Stage159代码SHA 68f2b9516fd89fdad5197a68bb9657e4c639a7ff（上一Claude对该SHA的研究代码范围意见APPROVE，原raw ZIP独立访问仍BLOCKED）。本新代码未获外部AI审核：`STAGE160_REVIEW=NOT_DONE`。
- 设计前置冻结：`MONSTER_445_WATCH_MARKET_BURST_FEED_DESIGN_FREEZE_20261017.md`，固定8槽来自原D1，触发是同轮WATCH数 **>8**，不以最终是否盈利/迟到排序或回填。
- 代码：`local-agent/scripts/monster_v4_445_burst_watch_feed_research.py`，测试 `local-agent/scripts/test_monster_v4_445_burst_watch_feed_research.py`，工作流 `.github/workflows/monster-v4-445-watch-burst-preview-one-shot.yml`，请求 `monster/source-batches/monster_feb445_watch_burst_preview_request.json`，真实Git摘要 `monster/evidence/monster_feb445_269_watch_burst_display_actual.json`。

## 必须独立取得的原始数据与真实执行

原始来源由先前同一SQLite全445历史研究V2执行（非原生产全D1，原历史PIT上市资格未核实）产生：真实 #38898752712 Artifact ID 12044872933；完整原JSON SHA256 `370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf`。如果Claude浏览器不能下载，**要求用户把当前对话中的 `monster445_full_replay_20261016.zip` 作为真实附件上传**，不能使用作者Git摘要冒充独立source复核；无需分享任何GitHub token。

新模型展示研究CI [#39009734600](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39009734600)，trigger `392c27e7c8c7a34aa435b0442e5ff789f12f0592`，实际completed/success；其输出Artifact ID **12092496953**（名`monster445-269-complete-watch-burst-display-study`，有效期至2026-12-16T06:23:42Z，包含完整269个逐币WATCH显示JSON和小型summary）；完整投影JSON SHA256 `fc4586fe19371042b182583ab95a4e15921edba9d45f59cf1979a3d09946f36e`。Git小摘要 blob `b67bac68294da771c5cce2d7f96a13e52e4338ac`。报告值：原269个WATCH，159个不同时刻，只有一次同刻98个超过8，研究显示卡从269变172、减少97；所有269原WATCH的`event_id`仍唯一且保留，98个成员可下钻；该98最终91 LATE/7 EVALUATED/0 SETUP仅存在**事后诊断区**，不能进入当时WATCH展区。**172是离线卡片假设，不是历史发出172封邮件或实际盈利能力**。

## 完整中文复审指令（可原样复制）

你是独立审核者。checkout固定SHA ccd879a890e57b02e3538add4d603a158df170da，对比前代码基线68f2b9516fd89fdad5197a68bb9657e4c639a7ff，不审核浮动PR HEAD。先读AGENTS、MONSTER_MODULE_DEVELOPMENT_RULES、Stage160冻结方案及此审核包。重点独立证伪以下业务错误：

1. **未来信息泄漏**：任何在`point_in_time_display_preview`中出现SETUP、LATE、最终队列status、盈利或后验优先排名；必须从原raw的WATCH_EARLY事件/自身payload构造而非从queue_rows后验列拿展示字段。历史Quote24是由分钟数据重构的proxy，**不能冒充官方当时PIT 24h ticker或真实BBO**。feed`can_follow_now`必须UNKNOWN，`BUY`必须FORBIDDEN。
2. **269完整性与群组归属**：从真实原ZIP复算269个WATCH身份哈希（生产`event_key`）、159个时间轮、同轮8容量门槛。98成员仅分成一张集成卡，但所有98个event_id仍逐一保留、可点击下钻，其他171独立卡无新增丢失/重复；概念显示总卡172，仅1个市场群组，绝不可称实发邮件数量。
3. **基线与计算时序**：8-slot阈值由已冻结生产代码决定，并非优化已看过的Feb445历史。组内展示仅按WATCH事件当时的历史quote24 proxy排序，不等于交易推荐，不应让99个涨币重复推动买入建议。检查同时间戳+场所确定性、重复WATCH和反例、无未来状态影响`display_preview`的独立负例。
4. **CI与权限隔离**：查看CI原始run #39009734600及Artifact与Git raw证明；工作流仅对唯一显式请求JSON push启动、没有schedule/cron/launchd/Automations；未动Frank、Mac或Gmail；没有发交易/通知；Git结果拒绝覆写并在rebase后验证源码及请求没有漂移。
5. **原始验证状态**：Claude上一审仅对Stage159修复APPROVE，不能借用它批准新Stage160。新raw JSON如果没有真实字节，269/98/172只能标UNVERIFIED，不能把Git自报看成独立复算。当前样本只有事后source-complete445/原758、313缺源，非PIT/OOS，G4 UNKNOWN G6 NO_GO。
6. **目标对齐**：审核此次究竟提高了用户理解“市场冲击 vs 某单币WATCH”的能力，还是只做漂亮UI；有无完整候选检索/源时间戳和状态鲜度；不允许把此输出作为提高D1早报或已验证盈利的证据。下一阶段若要研究首见公平性，必须另行先冻结目标、保留原8-slot FIFO基线和真实D1首服务轨迹。

请你独立复跑Python 3.12 `python -m unittest -v test_monster_v4_445_burst_watch_feed_research`，并下载或直接读取用户提供的原ZIP后独立运行`python monster_v4_445_burst_watch_feed_research.py --full <full.json> --summary <summary.json> --out <unused.json>`；逐字节核对原JSON SHA、输出数量和未来信息泄漏反例。如果网络不能访问GitHub Artifact且没有收到ZIP，明确`RAW_DATA_RECOMPUTE=BLOCKED`，不要补造模型结果。

反馈要求：真实审核者身份/准确可核验模型版本（否则UNVERIFIED）、唯一SHA/比较基线、实际命令及退出码、文件与行号、P0/P1/P2/P3问题的复现输入与修复建议，明确**APPROVE/REQUEST_CHANGES/BLOCKED**，严格限定为**Stage160只读投影研究**。NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE，原生产妖币盈利模型G4 UNKNOWN、G6 NO_GO继续。
