# Monster Stage162 — 同8槽首次有效5m评价优先，真实445币 A/B 结果（2026-10-18）

## 来源、固定可验证对象

设计先冻结于 `MONSTER_445_STAGE162_FIRST_VALID_D1_FAIRNESS_RESEARCH_PREREGISTRATION_20261017.md` 与 `MONSTER_STAGE162_FAIR_8_TECHNICAL_IMPLEMENTATION_CONTRACT_20261018.md`。实验**不修改**原 `monster_v4_shadow.py` / 原共享core / 研究zeroquote V2，用隔离 SQLite 的临时掩码让原V2一次只处理当前计划中8个候选，恢复所有未选中候选的原持久`retry_after_ms`。对照：原真实FIFO8 Stage161源SHA、相同445/28ZIP/3360 tick；非真实PIT、非独立OOS，原758还有313币source删失。

真实一次性 [GitHub Actions #39068290868](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39068290868) **2/2 SUCCESS**，唯一请求触发SHA `46f637c7aa2a833915c754b271ec413b67442c5f`；实际4个阶段所有source检查均通过：原445 full JSON SHA `370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf`，已获Claude Stage161审核的full trace SHA `8d7ac8d9a0a78a0daa1164d0aee7783b0a51f29ef099437590b103bad0bab76d`，18个官方历史来源Artifact、28份原ZIP、4450份publisher日SHA，D0 WATCH全269和每个queue episode来源ID全部逐字段相等，容量每tick≤8。源shard0原整体run failure但其中publisher源Job success，旧D1坏quote导致原run fail，已在 `MONSTER_STAGE161_CLAUDE_APPROVE_SHARD00_DISCLOSURE_20261018.md`披露；这份真实来源audit报告中**只有shard0为例外**，不能写死两个。

新Stage162完整结果 GHA Artifact ID **`12113719899`**（`monster162-real445-first-valid-5m-fair8-ab-once-v4`，到期2026-12-16T20:52:18Z），内部`monster162_actual_445_fair8_ab.json` SHA256 **`c30c8b6467b0017b36efc33fadfa2c7853f29f9c7e32993249774269ba4e2ae2`**，以及原`monster162_official_source_audit.json`和小型summary。Git小证据`evidence/monster_feb445_stage162_fair8_ab_real_v4_actual.json` Git blob **`76dd05127bf42f01df784c880bda2819006a6d4c`**。该结果由本对话获取真实Artifact ZIP再从原JSON独立算；它不是独立其他AI审核，不能写新代码review已批准。

## 实际结果，不夸大为盈利

| 精确指标 | 原真实FIFO8（同源V2） | Stage162 FAIR8隔离研究 |
|---|---:|---:|
| 全球poll（3分钟，445源共用） | 3360 | 3360 |
| WATCH_EARLY（同源、同事件ID） | 269 | 269 |
| D1总selected槽 | 753 | 753 |
| 其各首次/重复selected | 269/484 | 269/484 |
| **PEAK_98 WATCH后有效首次5m评价** | **7** | **32** |
| PEAK_98最终LATE | 91 | 66 |
| OTHER_171有效首次评价 | 165 | 167 |
| OTHER_171最终LATE | 2 | 0 |
| **SETUP_ACTIVE事件总数** | **120** | **120** |
| 丢失旧SETUP事件ID | — | **0** |
| 新SETUP事件ID | — | **0** |
| PEAK_98原SETUP | **0** | **0** |
| OTHER_171原SETUP | **120** | **120** |
| 全局重复选中游标未推进 | 190 | 206 |
| 全局重复选中游标推进 | 294 | 278 |

补充全原始 `candidate_outcomes` + `raw_alternative_events` 与原445`events`独立逐条对账：**此前已经获得有效首次评价的172名（PEAK7 + OTHER165）一个也没有失去评价，且首次有效评价时间戳全部不变**；新增获得评价的27名=PEAK25 + OTHER2（GPSUSDT、LUNAUSDT），但是**27个中没有产生新的SETUP**。原120个SETUP的完整event_id集合、`observed_ms`时间戳 **120/120完全相同**，既未损失也未提前/延迟。这是有效性和安全性重要边界，不得仅以SETUP数量不变代替时间不变。正常OTHER组p99由6m变为15m，是**新增两名历史此前完全LATE的样本进入分母**，不能误写为原165人的评价变慢。

新B方案在同一天历史样本实现了先前已冻结的理论峰值容量 **32=+6/+9/+12/+15m四轮×8槽**，相对7增加25个历史真实5m评价；**27个新增已评价不等于27个新币可买或获利**，本次真正新增SETUP是0。实质因果诊断表明原FIFO下旧候选`retry_after_ms+60s`较3m扫描周期短，曾重复占满8槽；B方案可改变这一服务机会分配。B不是证明历史最优，更没有证明对未来市场普适有效。

**原始报告归因失败修复历史**：初次单次CI `#39067400745`在shard 0/1整体run失败例外数量写死2，实际只有shard0，研究fail-closed；`#39067516375`全真实445执行到最终报告因`baseline`局部变量重绑定失败，没出具结果；`#39067850479`实际A/B成功但按同币名而不是`event_key(venue,symbol,"SETUP_ACTIVE",queue_id)`来分组，将另外回合的9个SETUP误算到PEAK，此旧摘要**不可引用为准确峰值SETUP分组**；修复为原生产精确queueID事件哈希，真实dup-symbol负对照与三组候选回归后才由最终 `#39068290868`正式归档。旧成功版原始source字节并未删除，错误报告需保留审计，不要偷偷覆盖。

## 决策与下一研发步骤

**历史机制可行性：YES；生产信号改善/盈利验证：NOT_YET。** 原先120个SETUP在这一天全部被保留且不延迟，是正面结果。但唯一已观察峰值是事后source-complete、非PIT上市池，未产生任何新增SETUP，无法断言策略实际帮助投资。重复槽中未推进5m评价游标的次数反而190→206，说明提高初评覆盖不等于消灭重试占槽，不应以重复槽降低作为唯一优化目标。

下一步优先补**另一独立时间窗口/更真实PIT上市池证据**与原D1可执行成本、BBO/L2盘口买卖深度、手续费/滑点、早报到达时延，确保真正SETUP/可操作数量净增加之前不要部署。Stage162本轮为新调度代码和真实A/B源证据完成，**其它AI对Stage162新模型审查仍NOT_DONE**，严格区别前Stage161批准。G4 UNKNOWN/G6 NO_GO，NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE、PR#30 Draft，禁止新/重启任何Mac/Frank/Gmail、schedule/launchd/cron/ChatGPT Automation或资金动作。
