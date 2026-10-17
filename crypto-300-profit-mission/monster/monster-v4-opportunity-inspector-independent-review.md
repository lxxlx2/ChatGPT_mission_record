# Monster V4 只读机会查询器独立代码与业务安全审核包

更新：2026-10-18。仅用于现有PR #30的研究代码审核；用户Mac、Frank、Gmail、交易均未变更。

## 精确审核对象

- 仓库：https://github.com/lxxlx2/ChatGPT_mission_record
- Draft PR：https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
- 分支：`research/monster-v4-local-discovery-20261010`
- **唯一审核固定SHA**：`7cee9f13f01f8601ba5759466b8befc55e8dec14`
- **唯一比较基线**：`51fcf066ef144d1526146a952e6b190961092a3a`
- 已复核Git compare：ahead 7、behind 0。核心实现3文件：新增`crypto-300-profit-mission/local-agent/scripts/monster_v4_opportunity_snapshot.py`、新增`crypto-300-profit-mission/local-agent/tests/test_monster_v4_opportunity_snapshot.py`、在`.github/workflows/monster-v4-research-baseline.yml`添加触发路径和测试步骤（7行新增，无删除）。同一compare还包含2个Monster文档变更（Stage163研究计划及本审核包前版），审查时须识别为文档范围，不能误写为只有3文件diff。
- 实际CI：https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39075820114 ， `historical-baseline` job success，全部22/22步骤完成；新增8/8 unittest PASS（log原始`Ran 8 tests in 0.095s / OK`）；旧Shadow/D2回归也pass。
- Stage162已由Codex独立APPROVE的固定SHA `b85dee96ec6f567e1f0b90f0d50cc5b19c79018b` 不属本轮修改，不必重复同代码审核。本轮新增功能未经其他AI Review，状态 `NOT_DONE`。

## 研究问题与不许升级状态

此前D0/D1/D2事件入SQLite，但`monster_v4_shadow.py status`仅输出健康计数。操作人员看不到明确的币、首次WATCH时间、是否过期、SETUP强度及对应D2检查状态。新工具只读已存在的Monster研究SQLite，输出带时间戳的机会清单，解释WATCH当时触发窗口、涨幅与24h成交背景，并附D2实际记录的价差/往返成本代理/费用假设；正确处理不同queue episode、场所、15m deadline、过期、无源或degraded、D2的用户未知真实费率，不产生BUY/交易/通知。没有部署Mac。

真实市场业务负证据：旧Stage30六日期已曝光样本430笔可评价WATCH后24h价代理133赢297亏，单交易无上限独立PnL+17.575264U但用户资金约束300U十槽乐观未知退出仍-79.489406U；它是历史代理非实际订单。Stage162已曝光同一445源Fair8新增有效首评27、净新增SETUP=0；来源不能冒充真PIT与新盈利验证。Stage163 2026-10-17T22:04:40.094Z Binance Spot官方原HTTP T0 已有511活跃USDT对，但未来7日（10月18~25日曼谷）未完成，没有动态真实入出场L2。G4 `UNKNOWN`、G6 `NO_GO`、`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`保持不变。

## 发给独立Claude/Codex的完整审核提示词

你是独立代码与业务安全审核者，请**实际获取GitHub固定提交的源码和逐文件Diff**，不要仅评论PR文字。

目标GitHub仓库：https://github.com/lxxlx2/ChatGPT_mission_record 。审核Draft PR #30，research分支 `research/monster-v4-local-discovery-20261010`；审核固定SHA `7cee9f13f01f8601ba5759466b8befc55e8dec14`，唯一比较基线 `51fcf066ef144d1526146a952e6b190961092a3a`。本轮重点审核以下3个代码/CI文件，另2个文档差异只需核对信息真实性和门禁，不必重审历史模型：
1. `crypto-300-profit-mission/local-agent/scripts/monster_v4_opportunity_snapshot.py`
2. `crypto-300-profit-mission/local-agent/tests/test_monster_v4_opportunity_snapshot.py`
3. `.github/workflows/monster-v4-research-baseline.yml`

业务目标：把既有Monster Shadow研究SQLite中持久化D0 WATCH、D1 SETUP、D2盘口审查输出为**真正只读、不含BUY误导**的机会摘要，正确显示首次观察时间、真实持久WATCH触发理由/涨幅/源证据、source可用性、15分钟窗口/过期、futures-only、不同queue episode、独立D2实际保存的spread/cost与费用假设。严禁更改已冻结D0/D1/Fair8、历史回测、Frank生产、Gmail、launchd、GitHub schedule、ChatGPT Automation、真实交易。不得把历史代理收益、旧30U D2场景或当前HTTP报价冒充真实可成交交易/净收益。

独立验证原始提交Diff及目标代码完整性；复现新增8项SQLite单测，并自行构造至少这些真正会影响用户的反例：
- 一个币旧SETUP已过期、新WATCH刚产生，能否避免用旧SETUP或旧D2标记新回合；
- `d2_reviews=CHECKED`但盘口/费率来自旧固定金额或有缺口，是否会错误宣称BUY/真实可成交；
- source缺失/DEGRADED、最新poll没有所有官方eligible交易对、时间戳倒流/过期，是否错误显示为可跟进；
- SETUP在期内或多次重复WATCH时，event_key与queue_id是否精确映射；SPOT与USD-M是否隔离；
- sqlite`mode=ro/query_only`是否确实不变更原库、丢文件时是否禁止创建假库，是否有意外联网、定时启动、发邮件、交易代码；
- `--asof-ms`仅为已保存现态评价钟，是否仍可能被误认为历史PIT回放；测试与CLI说明是否充分。
着重指出真正影响完整功能性和可用性的P0/P1/P2，避免仅审美或极端低价值边界建议。检查原`monster_v4_shadow.py`事件ID与D2字段契约，不能只根据新增测试假定一致。核查实际GitHub Actions #39075820114的触发HEAD/原始日志，不只看报告摘要。

请按固定结构返回：`APPROVE | REQUEST_CHANGES | BLOCKED`；准确审核SHA及比较基线；每个P0/P1/P2的代码行号、实际复现步骤、结果、修复方向；检查是否会改变WATCH、D2/BUY解释、Frank隔离或G0–G6放行；明确剩余真实源/样本外/手续费与可成交缺口以及`NO_MERGE / NO_DEPLOY`是否仍生效。不能访问固定源码或运行测试请标`UNVERIFIED/BLOCKED`，禁止凭文字自称完成独立审核。

## Codex 定向复审最终结果：APPROVE（2026-10-18）

**本节为本次用户转交的独立Codex报告的归档；该报告中本地 `/tmp` 探针文件不是本会话从GitHub重新取得的证据。** 本会话另外独立核对原固定SHA的GitHub Actions成功与代码源保持不变。审核者报告的底层精确模型为 `UNVERIFIED`。

- **固定审核SHA**：`d38999df6db63192ad3e3d11e793e2e6c4df05db`；比较基线 `7cee9f13f01f8601ba5759466b8befc55e8dec14`。范围仅限机会查询器和测试的两个P2修复，不批准PR其它历史研究/Stage163/交易/生产代码。
- **结论**：`APPROVE`，P0=0/P1=0/P2=0（该固定范围）；原旧SHA的 `REQUEST_CHANGES` 保留历史事实，不反溯批准。
- **P2-1 CLOSED**：用 WATCH 首次 `first_seen_ms` 锚定`INVALIDATED`事件；原EVALUATED的旧SETUP/D2历史保留但显示失效；新WATCH不继承旧失效、SETUP或D2。审核者自述独立调用真实Shadow schema与函数执行 `WATCH→SETUP→D2 CHECKED→INVALIDATED→new WATCH`。
- **P2-2 CLOSED**：场所级poll健康与单币snapshot时戳独立。审核者自述隔离重现AAA在新poll缺席180秒 => `SYMBOL_QUOTE_NOT_SEEN_IN_LATEST_POLL`；缺席540秒 => `SYMBOL_QUOTE_STALE`；场所仍`RECENT_STORED_POLL`。
- **可再验证的原CI**：[run #39076479244](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39076479244)，固定触发SHA `d38999df...`，工作流完成`SUCCESS`，新增query tests 10/10，Shadow 31/31，D2 12/12。审核者另自述本地四类命令通过、逻辑/主DB/WAL SHA只读、未发现网络/邮箱/交易/写库；独立本地日志路径仅存在于审核者的临时环境，不视为持久Git仓库Artifact。
- **仍然`UNVERIFIED`**：真实用户Mac实时持续源、盘口、实际账户费率/成交、告警送达与获利。PR #30保持Draft/open/unmerged；`G4 UNKNOWN / G6 NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`。

**结项**：该两个P2不需要再重新请另一个AI重复审核；后续精力转回增量实际SETUP与可执行成本/净收益验证。只在有新的实质代码变更时为其范围建立新门禁，严格区分其它Stage的独立审核状态。

## 当前状态

`CODE_TEST_CI=PASS`；`FIXED_D38999DF_P2_INDEPENDENT_REVIEW=APPROVE`；`LOCAL_MAC_ACCEPTANCE=NOT_DONE`；`ACTUAL_PROFIT_G4=UNKNOWN`；`G6=NO_GO`。仅研究代码与CI完成，禁止合并/部署/通知/交易。


## 补充：Codex REQUEST_CHANGES 的两项P2闭环修复（2026-10-18）

### 依据、精确身份及修复范围

- **前一独立审核**：用户于2026-10-18转述Codex审查固定SHA `7cee9f13f01f8601ba5759466b8befc55e8dec14`，基线 `51fcf066ef144d1526146a952e6b190961092a3a`；审核者自述Codex，底层模型精确身份`UNVERIFIED`，审核结论 `REQUEST_CHANGES`，两个真实SQLite业务P2，零P0/P1。用户提供的本机 `/tmp` 复现脚本/日志未作为本会话可读取来源冒充重新执行；按审核描述用仓库本身真实生产SQLite函数补齐复现测试。
- **本轮冻结修复代码SHA**：`d38999df6db63192ad3e3d11e793e2e6c4df05db`；仅涉及2个实用性文件：`local-agent/scripts/monster_v4_opportunity_snapshot.py`及`local-agent/tests/test_monster_v4_opportunity_snapshot.py`。相对于 `7cee9f13...` 的Git compare `ahead 4 / behind 0`，差异含之前两处文档整理；任何后续审核务必精确看新旧两版代码。未改冻结D0/D1/Fair8、D2策略与生产。
- **P2-1**：原查询器仅凭候选队列行 `status=INVALIDATED`，而原生产 `observe_snapshot` 只改 `PENDING`；已完成 `SETUP_ACTIVE` 的 `EVALUATED` 行会继续显示正向研究SETUP。修复使用 `event_id(venue,symbol,"INVALIDATED",first_seen_ms)` **精确WATCH回合锚点**查询真实 `events`，并要求 `first_seen_ms <= observed_ms <= now`；历史SETUP与D2仍作证据保存，但当前清单 `signal=INVALIDATED`。不借用 `watch_state.invalidated`，避免新WATCH重置造成跨回合串线。新测试执行 `WATCH→SETUP→D2 CHECKED→PRICE_REVERSED→new WATCH`，验证旧回合 `EVALUATED / INVALIDATED / D2 CHECKED`、新回合仅 `WATCH_RESEARCH_ONLY / NOT_CAPTURED`。
- **P2-2**：原工具只看场所级poll和health，忽略单个币 `snapshots.observed_ms`。修复新增 `symbol_quote_age_seconds`、`symbol_quote_state`、`symbol_seen_in_latest_poll`；如果单币报价缺失，或age>6分钟，或该symbol未出现在当前最新已归档场所poll对应时戳（虽有不超过6分钟旧报价），分别降级`SYMBOL_QUOTE_MISSING`、`SYMBOL_QUOTE_STALE`、`SYMBOL_QUOTE_NOT_SEEN_IN_LATEST_POLL`。场所 `RECENT_STORED_POLL`可独立为真；不得因此证明此symbol依旧属于当时完整可交易人口或当前可执行。新测试在场所BBBUSDT继续成功轮询的情况下，AAA报价先落后3分钟后落后9分钟，分别验证 `NOT_SEEN` 与 `STALE`，并记录540秒 age。
- **状态判断优先级**：本回合失效与队列LATE/过期优先于源陈旧；单币报价不新鲜优先于显示正向WATCH/SETUP；失效或过期保留历史诊断事件，不回写原SQLite、不建立另一套信号源。继续全局`RESEARCH_REVIEW_ONLY_NO_BUY`，`G4 UNKNOWN`、`G6 NO_GO`。

### 真实CI及审查关口

- 正式新的固定SHA GitHub Actions：[#39076479244](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39076479244)；触发修复HEAD `d38999df6db63192ad3e3d11e793e2e6c4df05db`，`historical-baseline` job `SUCCESS`，全部22/22步骤完成。
- 真实日志：新增机会查询器 **10/10 PASS**（原8＋两项真实SQLite生命周期反例），原Shadow **31/31 PASS**，D2 **12/12 PASS**，编译步骤成功。这只证明回归和现有研究接口合同，并非用户Mac持续运行、实时真实盘口或前瞻盈利。
- **作者修复与测试已完成；独立审查未完成。** 新固定SHA需要针对两项P2进行有边界的独立`APPROVE | REQUEST_CHANGES | BLOCKED`复审，旧 `7cee9f13...` 的`REQUEST_CHANGES`不可倒改成APPROVE。Codex已验证的非争议旧契约无须无止境重审。

### 可直接复制给独立Claude/Codex的定向复审提示词

请独立审查 Mission Monster 原 Draft PR #30 里针对上轮Codex两个P2的修复。原审查对象SHA `7cee9f13f01f8601ba5759466b8befc55e8dec14`，结论 `REQUEST_CHANGES`，P2-1是已完成SETUP失效仍显示SETUP，P2-2是场所poll新鲜但单币报价9分钟未更新仍显示WATCH。本轮唯一**修复审核SHA**：`d38999df6db63192ad3e3d11e793e2e6c4df05db`；旧研究分支 `research/monster-v4-local-discovery-20261010`；仓库 `https://github.com/lxxlx2/ChatGPT_mission_record`；PR `https://github.com/lxxlx2/ChatGPT_mission_record/pull/30`。代码比较使用旧审核SHA `7cee9f13f01f8601ba5759466b8befc55e8dec14` 和新SHA，注意两者之间另有文档变化。要审核的源码：`crypto-300-profit-mission/local-agent/scripts/monster_v4_opportunity_snapshot.py`及其同级 `../tests/test_monster_v4_opportunity_snapshot.py`。需要时读取不变生产 `monster_v4_shadow.py` 核对事件ID、 `observe_snapshot` / `process_queue` / `process_d2` 语义。请独立使用真实SQLite schema及生产函数，重做 `WATCH→SETUP→D2 CHECKED→INVALIDATED→新WATCH`，必须核实旧回合EVALUATED即使有D2也被事件锚点覆盖、新回合不继承旧失效/SETUP；再重做AAA报价9分钟未更新但BBB继续全市场poll，检查场所与币级状态独立、3分钟即已从上次poll消失时不会误称正常、缺报价与过去报价不冒充现价。请检查事件时钟、只读安全及所有现有业务P2是否关闭，不引入无关的阈值优化。校验GitHub CI `39076479244` 对应固定SHA、10个机会查询器测试、31个Shadow测试及12个D2测试真实日志。请报告**`APPROVE | REQUEST_CHANGES | BLOCKED`**、固定SHA、P0/P1/P2文件行号/复现步骤/修复建议、已关闭的两项问题及新缺陷，不能运行/取得源码写`UNVERIFIED`。旧Stage162 Fair8历史研究APPROVE与本轮功能查询器审核独立。始终保持`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`、`G4 UNKNOWN`、`G6 NO_GO`，不虚构收益、Mac验收或其他AI批准。
