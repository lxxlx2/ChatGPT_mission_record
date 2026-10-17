# Mission Monster Stage162 — 新公平8槽调度器 A/B 独立审核包（固定SHA）

## 只审核新的Stage162，不要无限重审已批准Stage161

- Repo https://github.com/lxxlx2/ChatGPT_mission_record
- Draft PR https://github.com/lxxlx2/ChatGPT_mission_record/pull/30
- 研究分支 `research/monster-v4-local-discovery-20261010`
- **Stage162 唯一新源码+成功真实A/B证据固定审核SHA：`b85dee96ec6f567e1f0b90f0d50cc5b19c79018b`**
- Stage161已获Claude独立`APPROVE_RESEARCH_ONLY`的基线SHA `0b3044daa9eeef14ac968c6d0f36a430b6b9ca23`，但该批准**不**覆盖本Stage162新排序逻辑；审查者具体底层版本无法独立核验就写UNVERIFIED。
- 当前审核包与Stage162结论Markdown在上述固定SHA**之后**单独提交；请在PR branch HEAD读取审核包后checkout固定SHA运行代码测试，不能因为文档不位于固定SHA而拒审业务源码。
- 源冻结：`monster/MONSTER_445_STAGE162_FIRST_VALID_D1_FAIRNESS_RESEARCH_PREREGISTRATION_20261017.md` 和 `monster/MONSTER_STAGE162_FAIR_8_TECHNICAL_IMPLEMENTATION_CONTRACT_20261018.md`。主要新增代码 `local-agent/scripts/monster_v4_445_stage162_first_valid_fair8_research.py`；对应 SQLite tests `test_monster_v4_445_stage162_first_valid_fair8_research.py`；一次性工作流 `.github/workflows/monster-v4-stage162-fair8-445-replay-once.yml`，唯一请求JSON `monster/source-batches/monster_feb445_stage162_first_valid_fair8_request.json`；实际Git证据 `monster/evidence/monster_feb445_stage162_fair8_ab_real_v4_actual.json` blob `76dd05127bf42f01df784c880bda2819006a6d4c`。Stage161及冻结生产三文件blob必须字节不变。

## 实际源与复算材料

1. 原历史baseline（同一445币/28片官方历史source，原758其余313仍CENSORED）：Run #38898752712 Artifact `12044872933`，full JSON SHA `370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf`。
2. 同源基线真实D1按轮观察：Run #39064416945 Artifact `12113086240`，内部Stage161 full trace SHA `8d7ac8d9a0a78a0daa1164d0aee7783b0a51f29ef099437590b103bad0bab76d`，并非模拟 FIFO。
3. Stage162最终来源和对照：**[GHA #39068290868](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/39068290868)**、trigger `46f637c7aa2a833915c754b271ec413b67442c5f`、两个jobs completed/success，Artifact ID **`12113719899`** `monster162-real445-first-valid-5m-fair8-ab-once-v4`，到期2026-12-16T20:52:18Z。实际完整`monster162_actual_445_fair8_ab.json` SHA256 **`c30c8b6467b0017b36efc33fadfa2c7853f29f9c7e32993249774269ba4e2ae2`**。GHA实际重新验证18历史Artifact/28 source ZIP、4450 publisher days SHA；源shard0原整体run failure而source publisher Job success的例外已在专门审计文档披露，真正来源校验绝不能凭run整体failure否定publisher已验成功。
4. 用户可把`monster_stage162_real445_fair8_ab_20261018.zip`**实际文件附件**上传另AI，无需私有GitHub Token；若没收到原ZIP、无法读原Artifact，请明确 RAW_RECOMPUTE=BLOCKED，不能把作者Git小摘要当作真正独立计算。

## 重点审查业务因果及真实可用性

- **没有未来信息泄漏**：scheduler每轮仅凭当前SQLite真实`status=PENDING / retry_after<=now`、`first_seen_ms`、`deadline_ms`、已评估的`last_evaluated_bar_ms`，以及最新5m按时钟已经闭合，优先安排当前真正有后WATCH闭合5m但从未有效评价的候选；不得读未来市场价格、未来LATE/SETUP状态、盈利结果或对98币事后硬编码白名单。其它剩余8槽保留原FIFO。source缺源/零成交仍交给原V2，不改原5m特征模型。
- **掩码安全/原生产不修改**：观察先选8，临时掩蔽其余eligible的`retry_after_ms`至`now+1`，调原zeroquote V2 handler**仅一次**、该handler再调冻结`production.process_queue`，随后在独立transaction完整恢复并读回；若异常要恢复/不可虚构收益。每轮selected<=8，原3360 tick，D0 269 WATCH事件ID+原queue episode (id, symbol, first_seen, deadline)与baseline逐字段相等。自行制造限额>8、错误source bar时钟、retry gate尚未成熟、状态漂移和掩码恢复反例。
- **SETUP事件跨回合身份**：比较必须按`production.event_key(venue,symbol,'SETUP_ACTIVE',persistent_queue_id)`精确关联；仅按symbol关联是危险缺陷。请独立复现`test_10_duplicate_symbol_across_episodes_uses_queue_id_not_name`，否则可能把别的episode的9个SETUP错误算到高峰。真实完整原始数据验证 baseline与新总SETUP=120，**同一个120个event_id全部保留、0lost/0new，并且120个`observed_ms`时间戳逐一不变**。PEAK98原SETUP0，新SETUP0；OTHER171 120→120。旧V3虽然总计数正确但按币名的分组错误，必须以V4作为准确审核材料。
- **主要业务结果不许夸大**：PEAK98有效首次评价7→32，LATE91→66；OTHER171有效首次评价165→167，LATE2→0；原172个已经获得有效评价的candidate其首次评价时刻**全部不变**，新增27个有效评价=25峰值+2其它，无任何新增SETUP。全753 D1 selected未增加，初次269、重复484也不变；只是时序/顺序变化。重复且有效评价游标未推进由190→206，不能称减少了所有无信息占槽。上述真实回放源来自2026年2月4日起已看过的445/758事后subset，并非独立未来OOS，也非真实PIT listing/盘口BBO/费用/滑点/可成交净利润；不能宣称25/27个盈利交易或模型已经成功可部署。
- **真实失败史必须保留**：`#39067400745`来源审计假设shard0和shard1两个整体run failure，真实仅shard0而失败；`#39067516375`真实full replay后结论函数`baseline`覆盖导致TypeError而失败；`#39067850479`真实调度和120个SETUP源本身正确，但分组按照symbol错误把另外回合9个SETUP算给peak，只有修复后的`#39068290868`可以作为正式峰值分组证据。作者无隐藏失败或重写旧Artifact。
- **影响现有正常业务**：独立检查是否存在同SETUP不同时间的延迟，以及正常171币原先162 EVALUATED、4 INVALIDATED、3ZEROQUOTE、2LATE如何变动。第一轮仅机制历史优化、不批准新生产D1；下一步必须是独立窗口(PIT/OOS)和交易可执行成本，且有真实SETUP改善才能考虑Shadow（也须用户明确同意）。

## 独立审核操作和结论

checkout固定SHA `b85dee96ec6f567e1f0b90f0d50cc5b19c79018b`，比较 `0b3044daa9eeef14ac968c6d0f36a430b6b9ca23` 及相关合约。 在 `crypto-300-profit-mission/local-agent/scripts` 真正执行：
`python3 -m unittest -v test_monster_v4_445_stage162_first_valid_fair8_research test_monster_v4_shared_445_source_shards test_monster_v4_shared_d1_zeroquote_research_v2`；实际10+7+11=28项测试的真实退出码与源码反例结果（不要照抄作者值），核对GHA原来源/原全量JSON、新full A/B结果文件真实SHA、候选269和SETUP120事件身份。每项问题记 P0/P1/P2/P3、文件行号、复现输入、是否真实改变WATCH/SETUP、是否未来信息泄漏；输出**APPROVE / REQUEST_CHANGES / BLOCKED**，明确是限定Stage162研究代码或原数据是否已独立复算。**不批准盈利模型、Mac、Frank、Gmail或交易**。维持`G4 UNKNOWN / G6 NO_GO / NO_MERGE / NO_DEPLOY / NO_GMAIL / NO_TRADE`、PR#30 Draft、禁止任何新定时任务。

**截至本包交付：OTHER_AI_STAGE162_REVIEW=NOT_DONE**，作者CI success不是别的AI独立审查。
