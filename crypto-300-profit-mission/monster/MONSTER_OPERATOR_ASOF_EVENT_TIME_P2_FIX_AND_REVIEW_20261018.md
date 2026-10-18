# Monster 机会清单：Claude P2-1历史时点未来状态泄露定向修复及独立审核（2026-10-18）

## 当前真实状态

**旧代码定向审核：REQUEST_CHANGES，P2-1。作者修复、真实CI与增量回归已完成；新固定SHA独立其他AI复审：NOT_DONE。** 研究机会查询器曾经由Codex另一次固定SHA批准旧Episode级P2，无法延伸到本次改动。最初`LIMIT`遮挡缺陷在本次Claude聊天独立审核中确认消除，但新发现`--asof-ms`以研究时钟回看已保存SQLite时，`source_state.degraded_since_ms`与`d2_reviews.status`实际存储的是**后续操作覆盖的当前状态**，会将之后的D2 `CHECKED`或来源降级虚假回填到过去。这影响WATCH/SETUP归因及用户是否认为研究信号当时还能跟进，优先修复，不改模型核心。

- 审核方：Claude聊天窗口，自述Claude Haiku 5.5，精确底层模型版本 **UNVERIFIED**；被拒旧固定SHA`731a0dfad0a78e77c53d20dbea3e375aaa9e55e1`，基线`2c37f0979832e2aafc3df94a78cb59660023e3eb`。Claude报告真实运行旧查询器12/12、Shadow31/31、D2 12/12；在原生产函数生成的真实SQLite中重现`asof=08:10:50`仍混入08:11:40 D2已CHECKED及未来SOURCE_DEGRADED。**旧版本结论REQUEST_CHANGES保持原样**，不借本轮作者自测回溯批准。
- **新唯一代码及测试待审核SHA `456111143f5ea1ac2e32103f71ea50dc5a27d078`**，旧审核目标（比较基线）`731a0dfad0a78e77c53d20dbea3e375aaa9e55e1`，本轮源码仅修改`crypto-300-profit-mission/local-agent/scripts/monster_v4_opportunity_snapshot.py`与`crypto-300-profit-mission/local-agent/tests/test_monster_v4_opportunity_snapshot.py`；比较路径中另有之前计划和实现的新增文档，不属于可执行代码变更。已有.github/workflows/monster-v4-research-baseline.yml内容不变，原Shadow/D0/D1/D2核心、Frank、Mac、本地采集/定时、Gmail、资金/买卖均不变。
- **真实固定SHA [GitHub CI #39128008157](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39128008157) SUCCESS，historical-baseline 23/23步骤成功**；实际Github原始日志`Ran 15 tests...OK`（机会查询器）、`Ran 31 tests...OK`（原Shadow）、`Ran 12 tests...OK`（D2）。由于脚本初次单独推送时原测试期待旧queue.status，最初[#39127921607](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39127921607)失败；之后一次只改变测试并补充对因果数据的新回归，终版CI成功。后续外部审查必须复验源固定SHA而不能只相信这份报告。

## 修复范围：以原生产事件作为时点证据

**D2**：原生产`monster_v4_shadow.process_d2()`把 `d2_reviews`的`status`从PENDING原地改为CHECKED/LATE/FUTURES_ONLY，`observed_ms`字段实际为SETUP事件时间，不是D2检查时间；不能仅加`d2_reviews.observed_ms<=asof`来证明检查在asof之前发生。因此查询器按事件SHA（与原生产 `event_key`一致）**只查询**`D2_LIQUIDITY/D2_NOT_SPOT/D2_LATE`中`observed_ms<=asof`的末次真实事件来决定`CHECKED/FUTURES_ONLY/LATE`，之前无终端事件则`NOT_CAPTURED`；费率假设、盘口研究信息只取已知`D2_LIQUIDITY`payload。不可从未来`d2_reviews.status`披露D2“已完成”。真实SETUP没有真实D2时仍可以显示`SETUP_RESEARCH_ONLY`，不能是BUY。

**数据源**：原生产`mark_source_health()`的`source_state`会在恢复时把当前降级清零，所以只检查`degraded_since_ms<=asof`不足以复现降级后又恢复的历史时点。现按venue和`FULL_UNIVERSE`历史事件 `SOURCE_DEGRADED/SOURCE_RECOVERED`，`observed_ms<=asof`的最后转换判断当时是否降级，时间字段取真实事件；不可直接将今天degraded_since显示为昨天。若数据库丢弃过去事件，本查询不会凭现态重构不存在的真实历史；`historical_asof_reconstruction=false`、新`asof_is_only_persisted_event_state_not_full_market_pit=true`，明确历史分钟行情的PIT仍UNKNOWN。

**额外明显时序漏洞**：`candidate_queue.status`同样是可被未来`LATE/EVALUATED/INVALIDATED`原地覆盖的现态。显示的`queue_status`现在由已保存的`SETUP_ACTIVE/INVALIDATED/LATE_REVIEW`事件和已知的deadline推导，无法断定已完整处理的队列返回`UNRESOLVED_ASOF`（对真实现态没有足够过去凭据时，宁可保持研究观察不当作确定的历史完成）；不再使用未来现态在asof之前误把仍有效WATCH标已LATE或已INVALIDATED。已经过期只显示EXPIRED。这个修复不实现真实历史PIT，不重算也不修改业务D0/D1。旧源码中episode事件锚点与quote单币健康评估保持。

**P3（低侵入、提高实际可用性）**：只读连接使用`contextlib.closing`显式close；SQLite`mode=ro/query_only`只限制SQL写入，**实际WAL共享内存辅助文件`-wal/-shm`仍可能因SQLite打开被创建**，文档主动披露，不虚称文件系统逐字节不变。全窗口保护为最多 **50,000**个候选，数据库查询`LIMIT 50001`检测超额后明确`ValueError: MONSTER_OPERATOR_WINDOW_EXCEEDS_SAFE_EPISODE_LIMIT`，绝不把结果截断后冒充完整人口。50k为防资源失控工程阈值，不是模型策略门槛也非本次历史实际事件数。字段`d2_research_liquidity_gate_is_not_fill_proof=true`表明D2只是研究假设，不是成交。

## 实际源与测试

在仓库根目录，下面命令只访问本地SQLite合成测试，不联网，不写生产数据库：

```zsh
python3 -B -m unittest discover -v -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_opportunity_snapshot.py
python3 -B -m unittest discover -v -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_shadow.py
python3 -B -m unittest discover -v -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_d2.py
```

新增回归全部用原`monster_v4_shadow.open_store/observe_snapshot/process_queue/process_d2/mark_source_health`写入真正生产Schema的**隔离合成测试SQLite**，不是编造实盘/未运行的测试。重点：
- 先产生SPOT WATCH→真实SETUP，再在`BASE+720s`才生成D2实际`CHECKED`与源`SOURCE_DEGRADED`，对`BASE+650s`的过去状态回查，期望仍`SETUP_RESEARCH_ONLY`、D2 `NOT_CAPTURED`、`d2_observed_utc=null`、无预算/价差、源仍RECENT；对720s则D2 CHECKED但SOURCE_STALE；900s恢复后反查720s仍应SOURCE_STALE，不受当前source_state已恢复影响。
- 真实WATCH后直到deadline 16m才在未来产生`LATE_REVIEW`，回查旧WATCH刚出现的时间点不能显示`MISSED_D1_DEADLINE`。
- 真实原Shadow产生两个不同回合，临时把本地单次保护上限设为1，验证不静默丢弃后续候选，而是抛出显式`EXCEEDS_SAFE_EPISODE_LIMIT`；恢复正常上限后所有回合完整可读。
- 其余12个既有查询器用例持续验证全窗口先判状态后排序和旧不同时段SETUP/D2身份；原Shadow 31、D2 12真实回归没有被修改。

**当前仅研发证据**：`NEW_CODE_CI=PASS`、`NEW_INDEPENDENT_REVIEW=NOT_DONE`；Mac正式Monster采集服务仍未启动、无真实历史账户盘口/实盘回执，旧Stage30净收益代理为负且Stage162 Fair8新增SETUP=0；`G4 UNKNOWN/G6 NO_GO/NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`持续。绝不因为旧`--asof-ms`显示正确而推广成历史真PIT或盈利模型合格。

## 可直接发给Claude/Codex的固定SHA局部独立复审任务（尚未完成）

> 请独立审核 Mission Monster PR #30 的查询器 `--asof-ms`未来事件泄露问题修复。仓库 `https://github.com/lxxlx2/ChatGPT_mission_record`，当前研究分支`research/monster-v4-local-discovery-20261010`，**唯一新代码审核SHA `456111143f5ea1ac2e32103f71ea50dc5a27d078`、准确比较基线 `731a0dfad0a78e77c53d20dbea3e375aaa9e55e1`**。此前Claude Haiku 5.5聊天独立审基线给出`REQUEST_CHANGES`，确认原`LIMIT`遮挡已修复但P2-1是过去asof时混入将来`d2_reviews.status=CHECKED`和`source_state.degraded_since_ms`；另P3为全窗口巨大表、SQLite连接未显式关闭和WAL可能新建、D2研究流动性字段易误解。真实比较两个固定SHA下`crypto-300-profit-mission/local-agent/scripts/monster_v4_opportunity_snapshot.py`及`crypto-300-profit-mission/local-agent/tests/test_monster_v4_opportunity_snapshot.py`的全部diff；前次一次性文档提交范围不属于代码更改。务必直接核对原生产`monster_v4_shadow.py`的`mark_source_health/process_d2/record_event/event_key`，确认`d2_reviews.observed_ms`其实为SETUP时间，故不能把字段当作D2完成时间。用隔离真实生产schema重放`WATCH→SETUP→延迟D2 CHECKED+SOURCE_DEGRADED→SOURCE_RECOVERED`，在D2发生前和降级后/恢复后各选多个asof，观察早时点D2`NOT_CAPTURED`、无未来payload、源降级不会提前生效且恢复后历史降级仍保留。额外独立反例：未来`LATE_REVIEW`不能把此前仍有效WATCH倒写为LATE；未来INVALIDATED不能回写旧asof；未来恢复不能让过去停机变健康。检查Futures的`D2_NOT_SPOT`时序，历史`D2_LATE`，不同Episode事件ID不串线；无现态队列状态误导，即使当时数据库保存不了历史完整市场行情也要明确`historical_asof_reconstruction=false`。旧SQLite WAL只读连接可能创建sidecars，代码必须不会写主表、通知、交易或修改上游策略。验证全窗口读取超过50k明确报错不冒充完整数据，且已有20或60个失效隐藏1个有效WATCH/SETUP的新排序回归仍通过。真实运行`python3 -B -m unittest discover -v -s crypto-300-profit-mission/local-agent/tests -p test_monster_v4_opportunity_snapshot.py`、原Shadow和D2测试；复查成功GitHub [CI #39128008157](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39128008157)，固定head=4561111、23/23步骤、机会查询器15/15、Shadow31/31、D2 12/12；首次仅源码提交时失败的[#39127921607](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39127921607)记录仍保留。不要重审已获批的Stage163 V3静态报价P2/Stage30经济数据或修改资金分配方案。请返回`APPROVE / REQUEST_CHANGES / BLOCKED`、审核身份与精确底层模型版本（不能独立确认写UNVERIFIED）、固定SHA、P0/P1/P2逐项实际复现、文件行号、测试和CI原始结果，对无法验证事项写UNVERIFIED。批准范围仅是已有SQLite研究机会查看器，不代表自动实盘或收益合格；保持`G4 UNKNOWN/G6 NO_GO/NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`，不部署Mac/Frank或启用自动监控。

## Codex 后续独立审核：新P2残留已由下一代码SHA定向修复（2026-10-18）

用户转交Codex针对本文历史固定SHA `456111143f5ea1ac2e32103f71ea50dc5a27d078` 的真实独立 `REQUEST_CHANGES`：未来 D2／数据源降级、恢复及未来LATE、INVALIDATED **已获独立反例确认修复**，唯一新P2残留是 `candidate_queue.last_error` 无历史发生时间却直接输出为 `d1_last_error`，可使420秒之后D1失败提前泄露到过去JSON。此处旧 `OTHER_AI_INDEPENDENT_REVIEW=NOT_DONE` 是当时状态；当前该SHA独立审结论 **REQUEST_CHANGES**，不能篡改旧审核。已在新代码SHA `6dd74eb05af3b9055575a0996d00925b557bc09b` 定向改为 `d1_last_error=null` + 不可还原来源标记，增真实生产Shadow SQLite + CLI前后相同 as-of 全JSON回归；[CI #39129122383](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39129122383) 16/16查询器、31/31 Shadow、12/12 D2全通过，Job SUCCESS。**新固定SHA独立复审仍NOT_DONE**；见[Codex仅存D1残留P2新审核包](MONSTER_OPERATOR_ASOF_D1_MUTABLE_DIAGNOSTIC_P2_TARGETED_FIX_20261018.md)。
