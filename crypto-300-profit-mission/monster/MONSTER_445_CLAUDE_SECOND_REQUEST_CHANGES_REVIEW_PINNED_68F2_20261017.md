# Monster 445：Claude 第二轮 REQUEST_CHANGES 的有界修复与第三次独立复审交接

本文件为**只读复审交接文档**，不代表完成独立复审；由于两条额外Git提交为文档，代码审核请严格用本次固定SHA **`68f2b9516fd89fdad5197a68bb9657e4c639a7ff`**；比较基线为上一Claude固定SHA **`02c49c2533776a564c94bcc8d9b6d8faf1605171`**。Mission Draft PR [#30](https://github.com/lxxlx2/ChatGPT_mission_record/pull/30)；原生产 `monster_v4_shadow.py`、`monster_v4_shared_spot_d0_d1_original_core.py`、Stage80、零quote V2历史研究实现没有修改，历史28来源ZIP和已有269候选完整回放JSON均没有覆写。本轮审查者 Claude Anthropic具体底层版本 UNVERIFIED；**上一审查结论REQUEST_CHANGES持续有效，OTHER_AI_REREVIEW=NOT_DONE**。

## 对最新Claude报告逐项回应（作者自检，必须由别的AI复核）

- **P1-1/N1 生产vs回放零成交额行为**：报告先前“原产线D1 fail-closed”的措辞不精确。真实`monster_v4_shadow.process_queue()`直接捕获 `evaluate_closed_5m` 的 `ValueError(INVALID_CLOSED_QUOTE)`，保持候选 PENDING、`attempts`递增、设置 `retry_after_ms`并追加failure，后续若无可评估K线且截止会LATE；若未来恢复有效K线，则可能合法重新评估，不能预言全部零quote一定LATE。而冻结历史**回放来源回调**在`monster_v4_shared_spot_d0_d1_original_core.py`把不支持源转为`RuntimeError`，原生产D1回放因此整体失败；445完整研究V2独立把3个候选标为旧字段`SOURCE_UNSUPPORTED_D1_ZERO_QUOTE`。三者**不能互换**。新文件 `test_monster_v4_shared_445_claude_review_fixes.py`真正用SQLite和原生产process_queue验证早期8根中首根0quote -> deferred(PENDING/attempts=1) -> 无恢复时LATE且事件按queue.id锚点匹配，未修改原生产代码。
- **N2 旧审计的literal True伪验证**：`monster_v4_shared_445_burst_audit.py`移除5条“市场确实是零成交/生产8根判定已由回放数据验证”等硬编码True；现在从**原full JSON队列**计算3个旧零quote终态的实际币种`ACAUSDT:2`、`GUSDT:1`，无法从events本身证明究竟“市场零quote/缺源”的字段直接标注`NOT_DETERMINABLE_FROM_EVENTS_ALONE`；生产8根条件来自**独立冻结生产源码及单测**，不是269 WATCH统计的推导。历史source/manifest证明与纯队列事件来源的论断严格分级，不篡改旧证据。
- **N3 LATE生产两条路径**：原生产新增WATCH时回收已过期旧队列会记`LATE_REVIEW`并带`reason=OVERDUE_WHEN_REARMING_WATCH`，而正常`process_queue`跨过deadline则在payload携带`first_seen_ms`与`deadline_ms`且无reason。新`classify_late_production_path`以真实事件payload判别，反查queue ID/符号/截止时间，不认识的原因拒绝统计。对原始实数 [#38950459044](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38950459044) 已重新算得 **269 WATCH、120 SETUP（精确锚点）、93 LATE，其中`D1_PROCESS_QUEUE_DEADLINE_EXPIRED=93`、`WATCH_REARM_OVERDUE_PRIOR_CANDIDATE=0`**。同轮98个WATCH/其中91个LATE、其余2个LATE仍不变。不能把这份**特定历史样本**的93个超时分类推断成所有未来直播数据。
- **P2-3 test shard01正例和真实Bash覆写守卫**：`test_monster_v4_shared_445_archive_replay_runner.py`补上(1,) + 源Job成功的正例和错误源Job失败负例，继续只限(0,)/(1,)单源例外；新增`test_08`**执行**5条遗留工作流真正的bash拒绝覆写片段、分别测试原目标不存在(exit 0)和文件已存在(exit !=0)且内容未变，而非仅验证guard字符串。4条保留push监听的workflow只对各自明确单次request JSON触发，普通代码push不能二次触发；其它源码函数没有cron/schedule任务。
- **N4 数据读取校验加入时间**：445历史模型的最早触发SHA `9b32f8debe6a4246f91f56a84aa7539884f5f857` 当时`official_source_shards.py`尚无逐币source proof对ZIP内manifest的额外比较，因此那一**已发生的模型执行不能反向宣称执行过新校验**。新校验是后续代码新增，且在本次 [#38950459044](https://github.com/lxxlx2/ChatGPT_mission_record/actions/runs/38950459044) 用18个旧原始Artifact/28片ZIP真实**重新读取并重新执行新逐币收据核对**；验证445币、4,450份原发行方日SHA、每币12960 1m条。**该工作并未重跑旧生产D0/D1，也不能宣称是新445盈利回测。**
- **P1-2 Claude外部访问阻断**：本对话存在经验证原始ZIP `monster445_full_replay_20261016.zip`（约54KB，解压出全JSON约478KB、summary和源audit），原JSON精确SHA256 `370c34fbe8c2e914de54d87068b329405fc94c9d2624f7e3d8701155b10d67cf`。**用户需把这份ZIP作为实际附件上传Claude审查环境**，不必分享GitHub token、不依赖它的匿名403访问。Claude没拿到字节以前P1-2对Claude仍 BLOCKED；作者在本会话使用ZIP成功复算不能代替独立审查者。
- **研究边界**：历史2026-02-04单日445为758中事后来源完整样本（313 CENSORED），不可称历史PIT完整上市池或未来独立OOS；真实BBO/L2、买卖成本/滑点、通知延迟、可执行净PnL、分市场币种召回未获证实。研究`SOURCE_UNSUPPORTED_D1_ZERO_QUOTE`旧字段名称具有误导性，**仅对旧已归档V2终态说明**，并没有重写冻结历史状态或声称原实盘引擎可用。保持`G4 UNKNOWN/G6 NO_GO/NO_MERGE/NO_DEPLOY/NO_GMAIL/NO_TRADE`。

## 当前新CI与可审计来源

- 真正GitHub研究CI run **#38950459044**，trigger `edc883aef91a93c3db1b462ac269ccf9febc13d4`，`completed/success`。在Ubuntu真实执行 **32项test**（包括旧原6根/8根、复审新增零quote实盘延期路径、5条遗留workflow覆写守卫、shard01正例） + 下载原full JSON SHA核验 + 18/28份官方归档ZIP重验 + 审计回写和Artifact二次封存。
- V2原事件审计新版：`evidence/monster_feb445_true_burst_causal_audit_review_n1_n3_actual.json`，Git blob `e6b3e75a2317bf60bdae8e88b6ebc231bc5096ba`；审计schema `MONSTER_FEB445_ACTUAL_D0_BURST_QUEUE_CAUSAL_AUDIT_V2`、分组后93/0原因、ACA2/GUS1、不再写无法证明的市场来源结论。
- 原始Source publisher manifest第二轮：`evidence/monster_feb445_original28_publisher_sha_proof_manifest_review_n3_actual.json`，Git blob `24603b09ec66a2ba84b25491c6806d4b8897c5c0`；同旧verified来源报告bytes一致是正常复核。
- 新结果GitHub Artifact ID `12068321724`（60天，预计2026-12-15T18:51:57Z失效）。历史问题归档均继续留存：第一审audit旧格式非法JSON、旧shard01重采事故、原生产445零quote实验的失败运行。

## 发给 Claude/Codex 的复审指令（固定代码版本）

请独立在仓库SHA `68f2b9516fd89fdad5197a68bb9657e4c639a7ff` 而非任意后续HEAD，比较前版 `02c49c2533776a564c94bcc8d9b6d8faf1605171`，复核上轮REQUEST_CHANGES的 P1-1（live与offline回调不同）、N2（不再对源市场状态硬编码真值）、N3（payload两类LATE与93条实际归类）、P2-3（分片01正例和5条旧Bash守卫真实行为测试）、N4（445原始运行的历史时间次序与后续28片复核）以及本轮是否出现新P1/P2。

必须独立取得附带真实ZIP（由用户上传）并对完整`monster_feb445_all445_one_sqlite_full_result.json`校验 SHA256 `370c34...`，自己从raw `events` 与 `queue_rows` 计算269/120/93、同tick 98、峰值91、93条全为`D1_PROCESS_QUEUE_DEADLINE_EXPIRED`且WATCH_REARM=0、逐个 SETUP 与 LATE 的生产`event_key`候选锚点；没有拿到文件就不得把该项写为独立通过，只能 `UNVERIFIED`。另外自己运行相关tests并记录**真实命令/退出码**、尝试至少一份篡改未知`LATE_REVIEW.reason`的反例，重点查是否只凭作者JSON布尔字段就自证生产没有修改。对历史435/445等数字不得创作不存在的来源。若找到问题，给出位置和反例；否则明确是否可以批准本次研究代码范围内的修复。

反馈格式：身份、准确底层模型版本（无法核验写UNVERIFIED）、唯一审核SHA、比较基线、实际执行命令/日志、逐P1/P2项 CLOSED/PARTIAL/OPEN/BLOCKED 与新问题、最终 `APPROVE/REQUEST_CHANGES/BLOCKED`。即使 APPROVE，G4 UNKNOWN / G6 NO_GO 和全部生产禁令保持，**不批准交易策略、盈利模型或生产发布**。当前独立复审仍未执行。
