# Monster Stage153：独立 Codex 最终 APPROVE@4553cb6（严格限定P1/P2代码修复）

2026-10-16 Asia/Bangkok。**证据性质**：本文件根据用户粘贴的Codex独立审核结果归档，并以GitHub原始CI/HEAD/固定SHA验证审核对象身份；这**不是**在GitHub上代表Codex发表review，更不是把作者或OpenAI连接器的核查冒称独立Codex审核。审核者报告：Codex；底层精确模型版本 `UNVERIFIED`，没有凭据不编造。原 [Monster Draft PR #30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30) 保持 `Open/Draft`、禁止合并/部署。

## 精确固定审核对象与结果

- **本次唯一代码、测试、未变更workflow固定SHA**：`4553cb6b18c5aaf723072d17a39f9ad92f0629c9`。
- 上次同模块 `REQUEST_CHANGES@80ebab9a6f3533103858de9e321f037384e86fde`：1 P1 SQLite源文件被`--out`覆写为JSON，2 P2 asof未来候选及候选/SETUP/LATE身份核对。
- 用户提供Codex独立review最终 **`APPROVE@4553cb6b18c5aaf723072d17a39f9ad92f0629c9`**，上述原1个P1、2个P2均关闭，本轮新增P0/P1/P2=0。原 Stage152 `APPROVE@71a041405352c9e2210d93dff9c2685149809e52` 的局部范围不变。
- reviewer checkout `/tmp/monster153-review-4553cb6` detached HEAD干净，审核器SHA256 `d33c24160fde670ecde064ca29dc3a4a32860111dc2899037bdc0f889cd89636`。本地`python3 -m unittest -v test_monster_v4_stage153_source_locked_d1_queue_lifecycle.py` `18/18`通过，`python3 -m py_compile`两文件通过。CI [#38789077966](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38789077966) 触发SHA精确相同，`3/3 Jobs SUCCESS`，Ubuntu24.04/macOS各18/18通过，历史原source audit并回写成功。
- 审核员另自己下载原Stage28 6份Artifact ZIP，分别SHA256核对外ZIP和内JSON `6/6 + 6/6`，独立计算与机器归档字节完全一致。它**没有**重新下载原Binance 1421份5m发行者源、没有重新跑全市场共享D0。

## P1安全关闭的准确边界——SHM caveat为必须保留的真实反例

Codex在隔离临时**真实WAL模式SQLite**、**独立进程CLI**上重跑**13种危险输出路径**：数据库本体（直接、相对、符号链接、硬链接）及`-wal/-shm/-journal`（直接、符号链接、硬链接）。全部拒绝并非零退出，错误`STAGE153_OUTPUT_ALIASES_SQLITE_OR_SIDECAR`，主数据库字节不变、WAL与journal未遭输出篡改，`PRAGMA integrity_check=ok`。合法新JSON会独占创建，重复指向已存在的JSON被拒绝且内容不变；最终`open("x")`不会像旧`Path.write_text`截断现存源。

**关键限制：活动SQLite WAL的`-shm`共享内存索引可能因SQLite正常`mode=ro`读取而改变部分字节**，不能写“所有sidecar绝对字节不变”“任何文件都不发生变化”。Codex明确做过**无`--out`只读查询对照**：
- 仅只读查询（无输出）：主库不变、WAL不变、SHM部分字节变化；
- 被拒绝的恶意`--out`：主库不变、WAL不变、SHM出现**同位置同类变化**。
因此已经关闭的是**CLI越权输出覆盖SQLite/sidecar**的P1；SHM可因正常SQLite只读活动更新属于底层共享内存缓存机制，不是本次`--out`覆盖漏洞、不是已证明的生产数据损坏。隔离Mac实验不授权访问或修改用户实际生产SQLite。

## P2 ASOF未来数据与身份对应均已关闭

- Codex独立构造98条`first_seen_ms=asof+1min`的未来pending、未来bar、已开始尚欠1毫秒完成5分钟闭合bar：全部拒绝`STAGE153_ASOF_FUTURE_PENDING_OR_COMPLETED_BAR`。合法98条候选和未来`retry_after_ms`回退等待：正确统计全量backoff，不随意topN截断。
- `snapshot_scope=CURRENT_STORED_PENDING_ONLY_NOT_HISTORICAL_RECONSTRUCTION`是事实：本探针只统计当前已保存PENDING快照，不能用当前状态推断历史任意时点全部PENDING。
- 候选主键`id`及episode分开唯一检查；LATE精确`symbol+payload.first_seen_ms+payload.deadline_ms`匹配并要求`observed_ms>deadline_ms`，不重复消费。原重复主键、时间提前、重复LATE替换另一件、错误SETUP币种/时间窗均拒绝。
- 原Stage28`setups`仅含`symbol+utc`，不存在producer candidate ID；现审计器检查完整SETUP事件到原候选的**单射匹配可行性**，不能冒称知道真实来源。
- 用户提供Codex独立精确确定两个**真实历史不唯一**SETUP：`MBLUSDT` 2025-11-09 08:21 UTC 两个候选ID 211/212，`BERAUSDT` 2026-02-06 18:36 UTC 两个候选ID 145/146。新报告总歧义=2，`setup_source_id_provenance=NOT_IN_ORIGINAL_STAGE28_REGISTER_MATCHING_EXISTS_ONLY`。Codex专门通过“需要重新分配才能合法一一匹配”的正例、三个SETUP争两个候选的`STAGE153_SETUP_NONINJECTIVE_CANDIDATE_OWNERSHIP`负例，验证不是逐件盲选第一个candidate。

## 真正验证的历史证据及未验证业务

Stage28 原GitHub产物六份双SHA验证成功，审计新summary [机器证据](evidence/monster_stage153_stage28_1128_queue_lifecycle_summary.json) Git blob `e4ce8ad5d00b76d56b06616208a6b7dc11541cb0`，原1128行[逐条JSONL](evidence/monster_stage153_stage28_1128_queue_lifecycle_rows.jsonl) blob `beb066d13ed1bf9656a1d9153f003c4363aa849c` 与旧版完全相同。新旧摘要除触发代码SHA、脚本SHA和新增源归属歧义字段外，其余数据严格一致。

冻结六日总量：`1132 WATCH / 1128 candidates / 1005 EVALUATED / 123 LATE / 828 SETUP / 3542 selections / 2414 deferred`。2026-02-06 00:36 UTC 98同轮WATCH → 91 LATE / 7 EVALUATED；123/123 LATE最终`last_evaluated_bar_ms=None`，其中27个`attempts>0`只代表原生产异常重试迹象，**不能推断从未发HTTP，也不是已证实漏掉123笔可盈利买单**。真正单一共享全市场D0、Spot+Futures争用与完整D0撤销历史、首次实际HTTP时刻、端到端通知送达、真实盘口与可成交净收益均未验证，不能提升G4/G6。

## 审核流程关闭和下一真正主线

**Stage153代码审查门禁仅该固定SHA：独立Codex APPROVE，旧1 P1/2 P2关闭，新问题0。** Stage153源码已由CI校验、原历史字节重放保留。后续应该回到已冻的用户目标：构建同一全市场共享D0 WATCH → 持久化队列 → 实际D1已闭合评价的因果时钟和真实高并发负载研究，不再围绕此只读小工具无限修改边界；下一阶段仍需新冻结、CI证据和另外AI review，以及真正用户授权Mac后才能测试本地安装与通知。**不要对Stage153新内容修改源码导致本次固定SHA复审身份失效。**

继续 `G0 PARTIAL / G1 NOT_SCORABLE / G2/G3 NOT_PASSED / G4 UNKNOWN / G5_FULL_RELEASE NOT_PASSED / G6 NO_GO` 和 `NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE / FRANK_UNCHANGED / STAGE99_STOPPED / NO_NEW_SCHEDULE`。本文件只是Git文档，不是向PR发布Codex review，也不代表代码合并/交易盈利验收。
