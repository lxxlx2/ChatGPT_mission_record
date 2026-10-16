# Monster 零quote研究V2：Codex REQUEST_CHANGES的 P1/P2 修复、真实SQLite故障实测、原32币CI回放与二审冻结（2026-10-16）

## 审核范围及先前独立缺陷

审核者Codex，底层精确模型`UNVERIFIED`，原唯一`REQUEST_CHANGES`固定SHA`dfceade891909bf374ce3e790f3aef33746f2938`。本报告不是第三方对新修复的APPROVE。之前旧production`monster_v4_shadow.py`及独立获批shared原core`monster_v4_shared_spot_d0_d1_original_core.py`无改动，原[CodeReview包](MONSTER_FIRST32_ZEROQUOTE_V2_INDEPENDENT_REVIEW_PINNED_DFCEADE_20261016.md)和[新修复事前冻结](MONSTER_ZEROQUOTE_V2_CODEX_SQLITE_MASK_AND_DEADLINE_P1_P2_FIX_FREEZE_20261016.md)仍有效。

- **P1 实际缺陷**：原研究变体临时把zeroquote候选AA和第9位溢出候选的`retry_after_ms`改`now+1`，外`with store`内调用原production`process_queue()`，原producer自身内`with db`会提交这些临时值。对正常AB的UPDATE触发SQL`RAISE(ABORT)`后finally里的恢复写入被外层rollback抛弃，数据库关了重新开AA仍保持`now+1`，历史队列半污染。
- **P2 实际缺陷**：在now恰好deadline时零quote，原变体不区分`last_evaluated_bar_ms`非空/空，把已经完成合法D1评价、到期没有SETUP的候选误标`SOURCE_UNSUPPORTED_D1_ZERO_QUOTE`；当now超过deadline则原production已正确标`EVALUATED/NO_SETUP_WITHIN_WINDOW`，边界自相矛盾。

## 本轮实现细节（只改实验V2及其tests）

1. **不要将嵌套数据库context当嵌套事务**：只在需zeroquote分支，对原FIFO前8（第9及之后不得提前得到槽）建立被mask身份与各个original`retry_after_ms`映射。明确拒绝caller已有待提交事务（避免擅自commit）。提交研究临时mask作为单独阶段，然后原冻结`production.process_queue`只对余下真实可评分候选执行至多8槽，可能内部提交/抛SQLite或source错误。**无论正常或异常**，在离开本函数之前先`rollback()`清除任何unfinished transaction，在**独立`with store`事务**恢复所有原retry并真实commit，最后SELECT逐身份回读确认，失败则`ZEROQUOTE_RESEARCH_MASK_RESTORE_FAILED`中止整个研究。这样不会出现先前`finally`执行了但后来一并被rollback的问题；原production对已经成功处理候选的提交不撤回。
2. **仅研究分类语义P2**：当已入选的zeroquote或以往zeroquote等待的候选达到期限，`last_evaluated_bar_ms IS NOT NULL`时只能`EVALUATED/NO_SETUP_WITHIN_WINDOW`且按`completed`计一次，既不`SOURCE_UNSUPPORTED`也不`LATE`；若确实从未成功评价且一直被真实zeroquote阻止，标`SOURCE_UNSUPPORTED_D1_ZERO_QUOTE`而非LATE/SETUP。不曾遭遇quote0、只是超期且无曾经评价的老候选由未改`production.process_queue`正常判断LATE。合法quote0仍消耗原8槽，不补假成交量；非法HIGH0、NaN、时间坏source仍致命整研究失败。
3. 保持`true_full_445_replayed=False`、`only_original_production_D0_and_D1_called=False`、`G4 UNKNOWN/G6 NO_GO`。冻结原D0信号、真实历史分钟来源SHA、Stage26 758/445/313人口不变、生产旧core unchanged。

## 实际回归和CI

本轮**代码+test+workflow唯一固定SHA `ef30be7bc67588b39efe552b39ab240843253846`**（V2源码修复commit`f5039d9724d08edb2295a66031854491489f0f30`，扩展四个新测试commit`ef30be7bc67588b39efe552b39ab240843253846`）。真实[GitHub Actions #38862965003](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38862965003)，触发SHA严格相同，`4/4 completed/success`。Ubuntu24.04 & macOS **各11/11测试OK**且py_compile通过，实际Job Logs中以下四新增测试均出现`ok`：
- `test_08_sql_update_abort_restores_mask_after_true_producer_inner_commit`：真实暂存SQLite建9条FIFO队列，AA zeroquote临时mask，未mock原生产队列，SQL trigger AB UPDATE `RAISE(ABORT)`，断言原`sqlite3.IntegrityError`传播、AA与AI的original retry=0内存恢复，并**关闭重新打开真实SQLite**逐条对账仍0，`PRAGMA integrity_check=ok`。
- `test_09_source_reader_error_after_committed_producer_restores_both_masks`：原真实producer已经评价AB并提交后AC官方source reader人为抛`RuntimeError`，AA及第9 AI掩码必须真实恢复且**关闭再打开SQLite依旧=0**，没有伪造模型通过。
- `test_10_six_deadline_boundaries_preserve_prior_valid_D1_ownership`：deadline`-1/0/+1ms` × `last_evaluated_bar_ms is None / non-None`六组实际SQLite，对所有临界情况核对分类和完成/迟到计数，先前有合法评价必须到期限`EVALUATED/NO_SETUP_WITHIN_WINDOW`，完全未评价且此前quote0才`SOURCE_UNSUPPORTED`。
- `test_11_no_prior_quote_failure_reverts_to_original_real_late`：真正没遭遇quote0也没有D1完成而超期的候选依然走原production产生1条真LATE，不因修复一律删除LATE语义。
- 原7项仍全通过，包括无zeroquote时与冻结原producer事件/queue/count精确相同、9个候选第1个zeroquote时第9不能获利借用槽位、坏HIGH0源不能冒充quote0、原待到期不误报。

真实CI再次下载了之前已封存的两份Stage26 publisher daily ZIP+CHECKSUM历史源GitHub Artifact ID`12021352471`和`12021445690`（此轮是归档原生source二次验证**不是重新下载320个Binance原日ZIP**）；重新SHA核对并在**同一SQLite**以2026-02真实32币源执行3360个3min轮次完整研究变体D0+D1；机器[evidence/monster_feb445_first32_zeroquote_D1_research_v2_actual.json](evidence/monster_feb445_first32_zeroquote_D1_research_v2_actual.json)触发SHA准确固定`ef30be...`、Git blob`693af9848a9e55a24ec0dca6bcb0e5e3ce84fce1`。

核心结果源SHA更新前后比较**所有原指标/事件/queue/来源字段值精确相同**，变更字段仅预期`trigger_commit_sha`和`d1_zeroquote_research_sha256`：
- 32真正共享D0 `WATCH=29`，与同源原Stage26逐币`WATCH=29`各币 UTC严格相同；原2026-02-06 00:36Z 7币同时WATCH，仍未超过D1 limit8。
- V2 D1 `EVALUATED=27`、`SOURCE_UNSUPPORTED_D1_ZERO_QUOTE=2`（均ACAUSDT），`LATE=0`、`SETUP_ACTIVE=13`、`INVALIDATED=7`。累计处理次数`selected/deferred=134/105`（不是134或105个不同币）、10个重复zeroquote slots、最大同tick selected=7。
- **32/445 source-complete子集**、413完整源未本轮共池重放，另313原来源缺失不填零；尚未444? 不等于445全源/758 PIT/盈利/OOS/交易/净成本/告警送达。

## 二审与剩余风险

**本次只是作者代码修复+多系统真实CI与新故障回归通过，其他AI固定新版独立复审** `NOT_DONE`。需特别重新用Codex旧/tmp探针等价故障确认异常后的sourceSQLite可关闭重开、真AB UPDATE ABORT、AC reader失败后不遗留mask、6组boundary分类、无新P1/P2，防止本轮修复其他candidate stale/retry事件副作用。之后才考虑把剩余来源完整币加入28份原一分钟源分片，**全445共池仅来源28/28才有意义**。

原`MONSTER_STAGE151`收益预估与本V2无关。保持`G0 PARTIAL / G1 NOT_SCORABLE / G2/G3 NOT_PASSED / G4 UNKNOWN / G5_RELEASE NOT_PASSED / G6 NO_GO`和`NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`；PR#30保持open Draft、Frank/Stage99不改。
