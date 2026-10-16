# 交给Codex / Claude的完全独立、固定SHA二审：Monster零quote V2 P1/P2补丁

仓库：https://github.com/lxxlx2/ChatGPT_mission_record 。原Draft PR #30：https://github.com/lxxlx2/ChatGPT_mission_record/pull/30 。

**唯一审核源码+测试/CI固定SHA：`ef30be7bc67588b39efe552b39ab240843253846`。** 上轮独立Codex`REQUEST_CHANGES`：`dfceade891909bf374ce3e790f3aef33746f2938`。请detached checkout固定新版；后续Git HEAD推送真实机器摘要、文档可能不同，**不得把HEAD偷换为代码核验版本**。审核准确底层模型身份没有可独立验证凭据则标`UNVERIFIED`。

请先读Monster AGENTS及开发规则、[主线开发节奏](MONSTER_MANUAL_COLLECTION_AND_DEVELOPMENT_CADENCE_20261014.md)、[本轮代码修改之前的两个缺陷事前冻结协议](MONSTER_ZEROQUOTE_V2_CODEX_SQLITE_MASK_AND_DEADLINE_P1_P2_FIX_FREEZE_20261016.md)和[实际修复报告](MONSTER_ZEROQUOTE_V2_CODEX_P1_P2_DURABLE_MASK_DEADLINE_FIX_REAL32_CI_20261016.md)。

**目标严格只有原2个缺陷**：P1临时mask被原production内`with db`提前commit，而外层异常rollback掉恢复导致真实SQLite关闭/重开后原retry_after_ms被永久覆盖；P2候选已经有`last_evaluated_bar_ms`成功原D1评价但now==deadline遇合法quote0时误记SOURCE_UNSUPPORTED。保持**原生产`monster_v4_shadow.py`、原共享核`monster_v4_shared_spot_d0_d1_original_core.py`源Git blob完全不改**；这版依然是实验V2 D1，不等于原D1获批/原交易策略。

源码：
- `crypto-300-profit-mission/local-agent/scripts/monster_v4_shared_d1_zeroquote_research_v2.py`
- `crypto-300-profit-mission/local-agent/scripts/test_monster_v4_shared_d1_zeroquote_research_v2.py`
- `.github/workflows/monster-v4-445-first32-zeroquote-research-v2.yml`

必须审代码不仅看绿灯，并在隔离真实 SQLite 上做**独立**反例：
1. 原 production `process_queue`未经mock替换；插入至少9个按first_seen,id排序的真实PENDING，AA合法零quote需临时mask，BB拥有合法 source；SQLite触发`RAISE(ABORT,'INJECTED_SQL_FAILURE')`在BB真实UPDATE，原异常必须外抛；数据库**关闭并从文件重开**，AA原retry=0，第9个候选原retry=0，不得残留`now+1`，其它已提交生产结果不能凭旧finally被回滚。再独立做先AB成功commit之后AC原source_reader抛真实`RuntimeError`的探针，`close/reopen`应原值。留完整可复查复现脚本与真实readback（不要改受审核源码）。
2. 跨deadline`deadline-1ms / deadline / deadline+1ms` × `last_evaluated_bar_ms NULL / non-NULL` 共6类（以及有无之前WAIT_ERROR）；只要原已有效D1评价过，到期无SETUP应`EVALUATED/NO_SETUP_WITHIN_WINDOW`而不是SOURCE_UNSUPPORTED或假LATE。未评价但有真实zeroquote WAIT，到期限必须`SOURCE_UNSUPPORTED_D1_ZERO_QUOTE`；没有任何quote0前提而原未评价超期仍由原production记真LATE。带真实close/reopen查。
3. 检查新修复的SQLite细节：只在sourcezero存在时使用原FIFO前8掩码，单独提交mask -> 原production内提交/异常 -> 显式rollback遗留开放事务 -> 独立**提交**恢复 -> SELECT readback；确认`store.in_transaction`预检、部分mask失败、恢复失败、异常路径传播、SQL trigger影响范围、副作用是否造成另一个P1/P2。至少一个9同刻zeroquote案例第9不能借出第1占用的slot；原生产一次`process_queue`处理有效候选而非逐个重复处理；无zeroquote时events、queue rows、execution_counts都精确与原已审D1相同。
4. 来源损坏：当原HIGH=0/NaN/坏开放时钟/负报价仍整研究fail-closed；合法quote0不改为正数/不生成SETUP；`production.process_queue`函数对象在成功及异常之后恢复（局部单线程patch，不能声明跨线程安全）。
5. 运行`cd crypto-300-profit-mission/local-agent/scripts && python3 -m py_compile monster_v4_shared_d1_zeroquote_research_v2.py test_monster_v4_shared_d1_zeroquote_research_v2.py && python3 -m unittest -v test_monster_v4_shared_d1_zeroquote_research_v2.py`（预期`11/11`），若有不通过必须说明。
6. 真[GitHub CI #38862965003](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38862965003) 触发SHA应精确一致，4/4 Jobs成功，Linux & macOS各11项OK和py_compile，真实source32 ZIP Artifact IDs `12021352471`及`12021445690`均源于先前发行者同host ZIP+CHECKSUM归档，独立复验32原source成员SHA（如未实际下载请标未独立下载，不要夸大已重下320份Binance ZIP）；与原固定`dfceade...`机器数据比较仅`trigger_commit_sha`和`d1_zeroquote_research_sha256`预期改变，其它字段（含全部events和queue）完全一致。当前机器归档路径`crypto-300-profit-mission/monster/evidence/monster_feb445_first32_zeroquote_D1_research_v2_actual.json`，固定新版机器Git blob `693af9848a9e55a24ec0dca6bcb0e5e3ce84fce1`。
7. 事实边界：真实32币共同D0 29 WATCH、旧Stage26同源逐币29、同刻最多7、实验D1 EVALUATED27/SOURCE_UNSUPPORTED2都ACAUSDT/LATE0/SETUP13/INVALIDATED7、累计selected134 deferred105，**没有**达到8上限的历史真实拥塞。原758历史分母 445曾complete、313缺源；这轮32/445 complete（另413没跑），与Stage28原98同时WATCH91 LATE注入历史不同，不能声称真正445、盈利、PIT listing、OOS、真实可成交净收益或Gmail/部署过。
8. 审核者不能修改被审源码/生产文件，也不得合并PR、Mac部署、发真实邮件、交易或启动Stage99。

报告明确写：审核者身份、底层精确模型标识（无独立证据`UNVERIFIED`）、唯一固定SHA、新旧对照、实际执行命令和证据等级、两个原问题逐一`CLOSED / OPEN`及新P0/P1/P2反例、是否真实下载源artifact与运行SQLite重新打开探针、`APPROVE / REQUEST_CHANGES / BLOCKED`。仍`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`、`G4 UNKNOWN/G6 NO_GO`。

若同一失败触发器同时污染其它库sidecar或mask恢复，新结论应`REQUEST_CHANGES`并留下明确可重现证据；不要因为原32历史源结果未变化就默许异常恢复缺陷。
